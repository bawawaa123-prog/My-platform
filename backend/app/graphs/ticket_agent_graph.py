from __future__ import annotations

from uuid import uuid4

from fastapi import HTTPException, status
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt
from sqlalchemy.orm import Session

from app.graphs.ticket_agent_state import TicketAgentState
from app.schemas.ai import AIReplyDraftRead, AIWorkflowPendingReviewRead, AIWorkflowProcessRead
from app.schemas.ticket import TicketRead
from app.services.rag_service import RagService
from app.services.review_service import ReviewService
from app.services.risk_service import RiskCheckResult, RiskService
from app.services.ticket_service import TicketService
from app.services.ticket_similarity_service import TicketSimilarityService

_CHECKPOINTER = InMemorySaver()


class TicketAgentGraph:
    def __init__(self, db: Session):
        self.db = db
        self.ticket_service = TicketService(db)
        self.rag_service = RagService(db)
        self.review_service = ReviewService(db)
        self.ticket_similarity_service = TicketSimilarityService(db)
        self.risk_service = RiskService()
        self.graph = self._build_graph(include_human_review=False)
        self.interrupt_graph = self._build_graph(include_human_review=True)

    def invoke(self, ticket_id: int) -> TicketAgentState:
        return self.graph.invoke({"ticket_id": ticket_id})

    def start(self, ticket_id: int, *, thread_id: str | None = None) -> AIWorkflowPendingReviewRead:
        # 带 interrupt 的流程会在 human_review 节点停住，
        # 然后把当前审核所需的全部上下文打包返回给前端。
        workflow_id = thread_id or str(uuid4())
        config = self._build_config(workflow_id)
        result = self.interrupt_graph.invoke(
            {
                "ticket_id": ticket_id,
                "run_id": workflow_id,
                "thread_id": workflow_id,
            },
            config,
        )
        if "__interrupt__" not in result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Workflow did not pause at the human review step.",
            )
        return self.get_pending_review(workflow_id)

    def resume(
        self,
        *,
        workflow_id: str,
        ticket_id: int,
        action: str,
        reviewer_user_id: int,
        final_content: str | None = None,
        reject_reason: str | None = None,
    ) -> AIWorkflowProcessRead:
        # resume 的本质是把“审核动作”作为 Command 重新送回 LangGraph checkpoint。
        config = self._build_config(workflow_id)
        snapshot = self.interrupt_graph.get_state(config)
        if not snapshot.next:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No interrupted workflow found for the provided thread_id/run_id.",
            )
        if snapshot.values.get("ticket_id") != ticket_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Workflow thread_id/run_id does not belong to the requested ticket.",
            )

        review_command = {
            "action": action,
            "reviewer_user_id": reviewer_user_id,
            "final_content": final_content,
            "reject_reason": reject_reason,
        }
        state = self.interrupt_graph.invoke(Command(resume=review_command), config)
        final_output = state.get("final_output")
        if not final_output:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Workflow resume did not produce a final output.",
            )
        return AIWorkflowProcessRead.model_validate(final_output)

    def get_pending_review(self, workflow_id: str) -> AIWorkflowPendingReviewRead:
        config = self._build_config(workflow_id)
        snapshot = self.interrupt_graph.get_state(config)
        if not snapshot.next:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No interrupted workflow found for the provided thread_id/run_id.",
            )

        values = snapshot.values or {}
        if "human_review" not in snapshot.next:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Workflow is not waiting at the human review step.",
            )

        ticket = values.get("ticket")
        classification = values.get("classification")
        reply_suggestion = values.get("reply_suggestion")
        risk_check = values.get("risk_check")
        if not ticket or not classification or not reply_suggestion or not risk_check:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Interrupted workflow checkpoint is missing review context.",
            )

        interrupt_id = None
        if snapshot.interrupts:
            interrupt_id = snapshot.interrupts[0].id

        reply_draft = self._ensure_reply_draft(reply_suggestion)
        risk_result = self._ensure_risk_result(risk_check)

        return AIWorkflowPendingReviewRead(
            run_id=workflow_id,
            thread_id=workflow_id,
            status="pending_review",
            pending_node="human_review",
            interrupt_id=interrupt_id,
            ticket=self._serialize_ticket(ticket),
            classification=self._serialize_classification(classification),
            knowledge_hits=self._serialize_knowledge_hits(values.get("knowledge_hits")),
            similar_tickets=self._serialize_similar_tickets(values.get("similar_tickets")),
            draft_reply=reply_draft.model_dump(),
            sources=[
                source.model_dump() if hasattr(source, "model_dump") else dict(source)
                for source in reply_draft.sources_json
            ],
            confidence=reply_draft.confidence,
            risk_check=risk_result.model_dump(),
        )

    @staticmethod
    def _build_config(workflow_id: str) -> dict:
        return {"configurable": {"thread_id": workflow_id}}

    def _build_graph(self, *, include_human_review: bool):
        # 同一份节点逻辑编译成两张图：
        # 一张直接跑完，一张在 human_review 节点支持 interrupt。
        builder = StateGraph(TicketAgentState)
        builder.add_node("load_ticket", self._load_ticket)
        builder.add_node("classify_ticket", self._classify_ticket)
        builder.add_node("retrieve_knowledge", self._retrieve_knowledge)
        builder.add_node("search_similar_tickets", self._search_similar_tickets)
        builder.add_node("generate_reply", self._generate_reply)
        builder.add_node("risk_check", self._risk_check)
        builder.add_node("finalize", self._finalize)
        if include_human_review:
            builder.add_node("human_review", self._human_review)

        builder.add_edge(START, "load_ticket")
        builder.add_edge("load_ticket", "classify_ticket")
        builder.add_edge("classify_ticket", "retrieve_knowledge")
        builder.add_edge("retrieve_knowledge", "search_similar_tickets")
        builder.add_edge("search_similar_tickets", "generate_reply")
        builder.add_edge("generate_reply", "risk_check")
        if include_human_review:
            builder.add_edge("risk_check", "human_review")
            builder.add_edge("human_review", "finalize")
        else:
            builder.add_edge("risk_check", "finalize")
        builder.add_edge("finalize", END)

        if include_human_review:
            return builder.compile(checkpointer=_CHECKPOINTER)
        return builder.compile()

    def _load_ticket(self, state: TicketAgentState) -> TicketAgentState:
        ticket = self.ticket_service.get_ticket(state["ticket_id"])
        return {"ticket": TicketRead.model_validate(ticket).model_dump(mode="json")}

    def _classify_ticket(self, state: TicketAgentState) -> TicketAgentState:
        ticket_id = state["ticket_id"]
        system_user = self.ticket_service.get_system_user()
        classification = self.ticket_service.classify_ticket(ticket_id, system_user)
        ticket = self.ticket_service.get_ticket(ticket_id)
        return {
            "classification": classification.model_dump(mode="json"),
            "ticket": TicketRead.model_validate(ticket).model_dump(mode="json"),
        }

    def _retrieve_knowledge(self, state: TicketAgentState) -> TicketAgentState:
        ticket = self.ticket_service.get_ticket(state["ticket_id"])
        query = "\n".join(
            filter(
                None,
                [
                    ticket.title,
                    ticket.content,
                    ticket.category,
                    ticket.priority,
                    ticket.ai_summary or "",
                ],
            )
        )
        retrieved_context = self.rag_service.retrieve_context(query, top_k=5)
        return {
            "retrieved_context": {
                "chunks": [
                    {
                        "doc_id": chunk.doc_id,
                        "chunk_id": chunk.chunk_id,
                        "chunk_index": chunk.chunk_index,
                        "content_preview": chunk.content_preview,
                        "score": chunk.score,
                        "embedding_id": chunk.embedding_id,
                    }
                    for chunk in retrieved_context.chunks
                ],
                "confidence": retrieved_context.confidence,
                "low_confidence_reason": retrieved_context.low_confidence_reason,
            },
            "knowledge_hits": [
                {
                    "doc_id": chunk.doc_id,
                    "chunk_id": chunk.chunk_id,
                    "chunk_index": chunk.chunk_index,
                    "content_preview": chunk.content_preview,
                    "score": chunk.score,
                    "embedding_id": chunk.embedding_id,
                }
                for chunk in retrieved_context.chunks
            ],
        }

    def _search_similar_tickets(self, state: TicketAgentState) -> TicketAgentState:
        similar_tickets = self.ticket_similarity_service.list_similar_tickets(state["ticket_id"], top_k=5)
        return {"similar_tickets": [ticket.model_dump(mode="json") for ticket in similar_tickets]}

    def _generate_reply(self, state: TicketAgentState) -> TicketAgentState:
        ticket = self.ticket_service.get_ticket(state["ticket_id"])
        suggestion = self.rag_service.generate_ticket_reply(ticket)
        return {"reply_suggestion": suggestion.model_dump(mode="json")}

    def _risk_check(self, state: TicketAgentState) -> TicketAgentState:
        ticket = self.ticket_service.get_ticket(state["ticket_id"])
        risk_result = self.risk_service.evaluate_ticket_reply(
            ticket=ticket,
            reply_suggestion=self._ensure_reply_draft(state["reply_suggestion"]),
        )
        return {"risk_check": risk_result.model_dump(mode="json")}

    def _human_review(self, state: TicketAgentState) -> TicketAgentState:
        # interrupt 会把 suggestion、sources、risk_check 暂停暴露给外部，
        # 等审核动作回来后再真正更新 suggestion 状态。
        reply_suggestion = self._ensure_reply_draft(state["reply_suggestion"])
        risk_result = self._ensure_risk_result(state["risk_check"])
        payload = {
            "ticket_id": state["ticket_id"],
            "suggestion_id": reply_suggestion.id,
            "draft_reply": reply_suggestion.suggested_content,
            "sources": [
                source.model_dump() if hasattr(source, "model_dump") else dict(source)
                for source in reply_suggestion.sources_json
            ],
            "confidence": reply_suggestion.confidence,
            "risk_check": risk_result.model_dump(),
        }
        decision = interrupt(payload)
        reviewed = self.review_service.apply_review_action(
            suggestion_id=reply_suggestion.id,
            action=decision["action"],
            current_user=self.ticket_service.get_user_by_id(decision["reviewer_user_id"]),
            final_content=decision.get("final_content"),
            reject_reason=decision.get("reject_reason"),
        )
        return {
            "human_review_payload": payload,
            "review_decision": {
                "action": decision["action"],
                "reviewer_user_id": decision["reviewer_user_id"],
                "final_content": decision.get("final_content"),
                "reject_reason": decision.get("reject_reason"),
            },
            "reviewed_suggestion": AIReplyDraftRead.model_validate(reviewed).model_dump(mode="json"),
        }

    def _finalize(self, state: TicketAgentState) -> TicketAgentState:
        reviewed_suggestion = state.get("reviewed_suggestion")
        final_output = {
            "ticket": self._serialize_ticket(state["ticket"]),
            "classification": self._serialize_classification(state["classification"]),
            "knowledge_hits": self._serialize_knowledge_hits(state.get("knowledge_hits")),
            "similar_tickets": self._serialize_similar_tickets(state.get("similar_tickets")),
            "reply_suggestion": self._ensure_reply_draft(state["reply_suggestion"]).model_dump(),
            "risk_check": self._ensure_risk_result(state["risk_check"]).model_dump(),
            "review_decision": state.get("review_decision"),
            "reviewed_suggestion": (
                self._ensure_reply_draft(reviewed_suggestion).model_dump()
                if reviewed_suggestion
                else None
            ),
        }
        return {"final_output": final_output}

    @staticmethod
    def _ensure_reply_draft(value: AIReplyDraftRead | dict) -> AIReplyDraftRead:
        if isinstance(value, AIReplyDraftRead):
            return value
        return AIReplyDraftRead.model_validate(value)

    @staticmethod
    def _ensure_risk_result(value: RiskCheckResult | dict) -> RiskCheckResult:
        if isinstance(value, RiskCheckResult):
            return value
        return RiskCheckResult.model_validate(value)

    @staticmethod
    def _serialize_ticket(value: TicketRead | dict) -> dict:
        if isinstance(value, TicketRead):
            return value.model_dump()
        return TicketRead.model_validate(value).model_dump()

    @staticmethod
    def _serialize_classification(value: dict | object) -> dict:
        if hasattr(value, "model_dump"):
            return value.model_dump()
        return dict(value)

    @staticmethod
    def _serialize_knowledge_hits(value: list | None) -> list[dict]:
        if not value:
            return []
        serialized: list[dict] = []
        for item in value:
            if hasattr(item, "__dict__"):
                serialized.append(
                    {
                        "doc_id": item.doc_id,
                        "chunk_id": item.chunk_id,
                        "chunk_index": item.chunk_index,
                        "content_preview": item.content_preview,
                        "score": item.score,
                        "embedding_id": item.embedding_id,
                    }
                )
            else:
                serialized.append(dict(item))
        return serialized

    @staticmethod
    def _serialize_similar_tickets(value: list | None) -> list[dict]:
        if not value:
            return []
        serialized: list[dict] = []
        for item in value:
            if hasattr(item, "model_dump"):
                serialized.append(item.model_dump())
            else:
                serialized.append(dict(item))
        return serialized
