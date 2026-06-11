from __future__ import annotations

from datetime import UTC, datetime
from copy import deepcopy
from uuid import uuid4

from fastapi import HTTPException, status
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt
from sqlalchemy.orm import Session

from app.agents.knowledge_agent import KnowledgeAgent
from app.agents.reply_agent import ReplyAgent
from app.agents.risk_agent import RiskAgent
from app.agents.similar_case_agent import SimilarCaseAgent
from app.agents.supervisor_agent import SupervisorAgent
from app.agents.triage_agent import TriageAgent
from app.agents.workflow_agent import WorkflowAgent
from app.graphs.ticket_multi_agent_state import TicketMultiAgentState
from app.schemas.ai import AIMultiAgentPendingReviewRead, AIReplyDraftRead
from app.schemas.ticket import TicketRead
from app.services.agent_run_service import AgentRunService
from app.services.ticket_service import TicketService
from app.models.ai_suggestion import AISuggestion
from app.models.audit_log import AuditLog
from app.models.ticket import Ticket

_MULTI_AGENT_CHECKPOINTER = InMemorySaver()


class TicketMultiAgentGraph:
    def __init__(self, db: Session):
        self.db = db
        self.ticket_service = TicketService(db)
        self.agent_run_service = AgentRunService(db)
        self.supervisor_agent = SupervisorAgent(db)
        self.triage_agent = TriageAgent(db)
        self.knowledge_agent = KnowledgeAgent(db)
        self.similar_case_agent = SimilarCaseAgent(db)
        self.reply_agent = ReplyAgent(db)
        self.risk_agent = RiskAgent(db)
        self.workflow_agent = WorkflowAgent(db)
        self.graph = self._build_graph()

    def preview(self, ticket_id: int) -> dict:
        # preview 给 MCP dry_run 用：
        # 会真的跑一遍图，但最后把 suggestion、audit_log、ticket 状态等副作用清理掉。
        workflow_id = str(uuid4())
        ticket_before_obj = self.ticket_service.get_ticket(ticket_id)
        ticket_before = deepcopy(self.ticket_service.serialize_ticket(ticket_before_obj))
        suggestion_ids_before = self._get_reply_suggestion_ids(ticket_id)
        audit_log_ids_before = self._get_related_audit_log_ids(ticket_id, suggestion_ids_before)
        result = self.graph.invoke(
            {
                "ticket_id": ticket_id,
                "run_id": workflow_id,
                "thread_id": workflow_id,
            },
            {"configurable": {"thread_id": workflow_id}},
        )
        pending_review = self.get_pending_review(workflow_id)

        self._cleanup_preview_side_effects(
            ticket_id=ticket_id,
            ticket_before=ticket_before,
            suggestion_ids_before=suggestion_ids_before,
            audit_log_ids_before=audit_log_ids_before,
        )

        ticket_after = self.ticket_service.serialize_ticket(self.ticket_service.get_ticket(ticket_id))
        latest_suggestion_id_after = self._get_latest_reply_suggestion_id(ticket_id)
        preview_result = pending_review.model_dump(mode="json")
        preview_result["ticket"] = ticket_before
        reply_suggestion = preview_result.get("reply_result", {}).get("reply_suggestion")
        if reply_suggestion and reply_suggestion.get("id") not in suggestion_ids_before:
            reply_suggestion["id"] = None
            reply_suggestion["status"] = "dry_run"
            reply_suggestion["reviewed_by"] = None
            reply_suggestion["reviewed_at"] = None
            reply_suggestion["final_content"] = None
            reply_suggestion["reject_reason"] = None
        if preview_result.get("workflow_result", {}).get("updated_ticket"):
            preview_result["workflow_result"]["updated_ticket"] = ticket_before

        return {
            "ticket_id": ticket_id,
            "dry_run": True,
            "status": "preview",
            "ticket_before": ticket_before,
            "ticket_after": ticket_after,
            "latest_reply_suggestion_id_after": latest_suggestion_id_after,
            "result": preview_result,
            "audit_trail": preview_result.get("audit_trail", []),
        }

    def start(
        self,
        ticket_id: int,
        *,
        created_by_user_id: int | None = None,
        thread_id: str | None = None,
    ) -> AIMultiAgentPendingReviewRead:
        # 正式 multi-agent 运行除了返回 pending_review 结果，
        # 还会把 output_json 和 audit_trail 持久化到 AgentRunLog。
        workflow_id = thread_id or str(uuid4())
        config = {"configurable": {"thread_id": workflow_id}}
        input_json = {
            "ticket_id": ticket_id,
            "run_id": workflow_id,
            "thread_id": workflow_id,
        }
        try:
            result = self.graph.invoke(input_json, config)
            if "__interrupt__" not in result:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Multi-agent workflow did not pause at the human review step.",
                )
            pending_review = self.get_pending_review(workflow_id)
            self.agent_run_service.upsert_run_log(
                ticket_id=ticket_id,
                run_id=workflow_id,
                run_type="multi_agent",
                status="interrupted",
                input_json=input_json,
                output_json=pending_review.model_dump(mode="json"),
                audit_trail_json=pending_review.audit_trail,
                created_by=created_by_user_id,
            )
            return pending_review
        except HTTPException as exc:
            self.db.rollback()
            self.agent_run_service.upsert_run_log(
                ticket_id=ticket_id,
                run_id=workflow_id,
                run_type="multi_agent",
                status="failed",
                input_json=input_json,
                output_json={},
                audit_trail_json=[],
                created_by=created_by_user_id,
                error_message=str(exc.detail),
            )
            raise
        except Exception as exc:
            self.db.rollback()
            self.agent_run_service.upsert_run_log(
                ticket_id=ticket_id,
                run_id=workflow_id,
                run_type="multi_agent",
                status="failed",
                input_json=input_json,
                output_json={},
                audit_trail_json=[],
                created_by=created_by_user_id,
                error_message=str(exc),
            )
            raise

    def get_pending_review(self, workflow_id: str) -> AIMultiAgentPendingReviewRead:
        # 从 checkpoint 里恢复“暂停时刻”的全部 Agent 输出，
        # 这样前端时间线页不需要自己再拼装多份状态。
        snapshot = self.graph.get_state({"configurable": {"thread_id": workflow_id}})
        if not snapshot.next:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No interrupted multi-agent workflow found for the provided thread_id/run_id.",
            )
        if "human_review" not in snapshot.next:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Multi-agent workflow is not waiting at the human review step.",
            )

        values = snapshot.values or {}
        reply_result = values.get("reply_result")
        if not reply_result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Interrupted multi-agent workflow checkpoint is missing agent outputs.",
            )

        reply_suggestion = AIReplyDraftRead.model_validate(reply_result["reply_suggestion"])
        interrupt_id = snapshot.interrupts[0].id if snapshot.interrupts else None

        return AIMultiAgentPendingReviewRead(
            run_id=workflow_id,
            thread_id=workflow_id,
            status="pending_review",
            pending_node="human_review",
            interrupt_id=interrupt_id,
            ticket=values["ticket"],
            supervisor_result=values["supervisor_result"],
            triage_result=values["triage_result"],
            knowledge_result=values["knowledge_result"],
            similar_case_result=values["similar_case_result"],
            reply_result=reply_result,
            risk_result=values["risk_result"],
            workflow_result=values["workflow_result"],
            draft_reply=reply_suggestion.model_dump(),
            sources=[
                source.model_dump() if hasattr(source, "model_dump") else dict(source)
                for source in reply_suggestion.sources_json
            ],
            confidence=reply_suggestion.confidence,
            audit_trail=values.get("audit_trail", []),
        )

    def _build_graph(self):
        # 当前版本采用固定顺序图，优先保证演示稳定性和输出可解释性。
        builder = StateGraph(TicketMultiAgentState)
        builder.add_node("load_ticket", self._load_ticket)
        builder.add_node("supervisor", self._supervisor)
        builder.add_node("triage", self._triage)
        builder.add_node("knowledge", self._knowledge)
        builder.add_node("similar_case", self._similar_case)
        builder.add_node("reply", self._reply)
        builder.add_node("risk", self._risk)
        builder.add_node("workflow", self._workflow)
        builder.add_node("human_review", self._human_review)
        builder.add_node("finalize", self._finalize)

        builder.add_edge(START, "load_ticket")
        builder.add_edge("load_ticket", "supervisor")
        builder.add_edge("supervisor", "triage")
        builder.add_edge("triage", "knowledge")
        builder.add_edge("knowledge", "similar_case")
        builder.add_edge("similar_case", "reply")
        builder.add_edge("reply", "risk")
        builder.add_edge("risk", "workflow")
        builder.add_edge("workflow", "human_review")
        builder.add_edge("human_review", "finalize")
        builder.add_edge("finalize", END)
        return builder.compile(checkpointer=_MULTI_AGENT_CHECKPOINTER)

    def _get_reply_suggestion_ids(self, ticket_id: int) -> set[int]:
        suggestions = self.reply_agent.rag_service.suggestion_repository.list_reply_suggestions_by_ticket_id(ticket_id)
        return {suggestion.id for suggestion in suggestions}

    def _get_latest_reply_suggestion_id(self, ticket_id: int) -> int | None:
        suggestions = self.reply_agent.rag_service.suggestion_repository.list_reply_suggestions_by_ticket_id(ticket_id)
        return suggestions[0].id if suggestions else None

    def _get_ticket_audit_log_ids(self, ticket_id: int) -> set[int]:
        statement = self.db.query(AuditLog.id).filter(
            AuditLog.target_type == "ticket",
            AuditLog.target_id == ticket_id,
        )
        return {row[0] for row in statement.all()}

    def _get_related_audit_log_ids(self, ticket_id: int, suggestion_ids_before: set[int]) -> set[int]:
        ticket_audit_log_ids = self._get_ticket_audit_log_ids(ticket_id)
        suggestion_audit_log_ids: set[int] = set()
        if suggestion_ids_before:
            statement = self.db.query(AuditLog.id).filter(
                AuditLog.target_type == "ai_suggestion",
                AuditLog.target_id.in_(suggestion_ids_before),
            )
            suggestion_audit_log_ids = {row[0] for row in statement.all()}
        return ticket_audit_log_ids | suggestion_audit_log_ids

    def _cleanup_preview_side_effects(
        self,
        *,
        ticket_id: int,
        ticket_before: dict,
        suggestion_ids_before: set[int],
        audit_log_ids_before: set[int],
    ) -> None:
        new_suggestions = (
            self.db.query(AISuggestion)
            .filter(
                AISuggestion.ticket_id == ticket_id,
                AISuggestion.suggestion_type == "reply",
                ~AISuggestion.id.in_(suggestion_ids_before) if suggestion_ids_before else True,
            )
            .all()
        )
        for suggestion in new_suggestions:
            self.db.delete(suggestion)

        new_ticket_audit_logs = (
            self.db.query(AuditLog)
            .filter(
                AuditLog.id.notin_(audit_log_ids_before) if audit_log_ids_before else True,
                (
                    ((AuditLog.target_type == "ticket") & (AuditLog.target_id == ticket_id))
                    | ((AuditLog.target_type == "ai_suggestion"))
                ),
            )
            .all()
        )
        for audit_log in new_ticket_audit_logs:
            self.db.delete(audit_log)

        remaining_new_audit_logs = (
            self.db.query(AuditLog)
            .filter(AuditLog.id.notin_(audit_log_ids_before) if audit_log_ids_before else True)
            .all()
        )
        for audit_log in remaining_new_audit_logs:
            self.db.delete(audit_log)

        ticket = self.db.get(Ticket, ticket_id)
        if ticket is not None:
            ticket.category = ticket_before["category"]
            ticket.priority = ticket_before["priority"]
            ticket.sentiment = ticket_before["sentiment"]
            ticket.status = ticket_before["status"]
            ticket.ai_summary = ticket_before["ai_summary"]
            ticket.recommended_department = ticket_before["recommended_department"]
            ticket.assigned_to = ticket_before["assigned_to"]
            ticket.closed_at = ticket_before["closed_at"]

        self.db.commit()

    def _load_ticket(self, state: TicketMultiAgentState) -> TicketMultiAgentState:
        ticket = self.ticket_service.get_ticket(state["ticket_id"])
        return {"ticket": TicketRead.model_validate(ticket).model_dump(mode="json")}

    def _supervisor(self, state: TicketMultiAgentState) -> TicketMultiAgentState:
        result = self.supervisor_agent.run(ticket=state["ticket"])
        return {
            "supervisor_result": result,
            "audit_trail": self._append_audit_entry(
                state,
                agent_name="SupervisorAgent",
                action="plan_multi_agent_workflow",
                input_summary=f"Ticket #{state['ticket_id']} entered multi-agent workflow.",
                output_summary=f"Planned agents: {', '.join(result['planned_agents'])}.",
            ),
        }

    def _triage(self, state: TicketMultiAgentState) -> TicketMultiAgentState:
        result = self.triage_agent.run(ticket_id=state["ticket_id"])
        classification = result["classification"]
        return {
            "triage_result": result,
            "audit_trail": self._append_audit_entry(
                state,
                agent_name="TriageAgent",
                action="classify_ticket",
                input_summary=f"Classify ticket #{state['ticket_id']} for category, priority, and sentiment.",
                output_summary=(
                    f"Category={classification['category']}, "
                    f"Priority={classification['priority']}, "
                    f"Sentiment={classification['sentiment']}."
                ),
            ),
        }

    def _knowledge(self, state: TicketMultiAgentState) -> TicketMultiAgentState:
        result = self.knowledge_agent.run(ticket_id=state["ticket_id"])
        return {
            "knowledge_result": result,
            "audit_trail": self._append_audit_entry(
                state,
                agent_name="KnowledgeAgent",
                action="search_knowledge_base",
                input_summary="Retrieve relevant knowledge base chunks for the triaged ticket.",
                output_summary=(
                    f"Found {len(result['hits'])} hits with confidence {result['confidence']}."
                ),
            ),
        }

    def _similar_case(self, state: TicketMultiAgentState) -> TicketMultiAgentState:
        result = self.similar_case_agent.run(ticket_id=state["ticket_id"])
        return {
            "similar_case_result": result,
            "audit_trail": self._append_audit_entry(
                state,
                agent_name="SimilarCaseAgent",
                action="search_similar_tickets",
                input_summary="Search resolved historical tickets that are similar to the current issue.",
                output_summary=(
                    f"Found {len(result['similar_tickets'])} similar historical tickets."
                ),
            ),
        }

    def _reply(self, state: TicketMultiAgentState) -> TicketMultiAgentState:
        result = self.reply_agent.run(
            ticket_id=state["ticket_id"],
            triage_result=state["triage_result"],
            knowledge_result=state["knowledge_result"],
            similar_case_result=state["similar_case_result"],
        )
        reply = result["reply_suggestion"]
        return {
            "reply_result": result,
            "audit_trail": self._append_audit_entry(
                state,
                agent_name="ReplyAgent",
                action="generate_reply_draft",
                input_summary="Draft a customer reply from triage, knowledge retrieval, and similar-case context.",
                output_summary=(
                    f"Created reply suggestion #{reply['id']} "
                    f"with confidence {reply['confidence']}."
                ),
            ),
        }

    def _risk(self, state: TicketMultiAgentState) -> TicketMultiAgentState:
        result = self.risk_agent.run(
            ticket_id=state["ticket_id"],
            reply_result=state["reply_result"],
        )
        risk_check = result["risk_check"]
        return {
            "risk_result": result,
            "audit_trail": self._append_audit_entry(
                state,
                agent_name="RiskAgent",
                action="evaluate_reply_risk",
                input_summary="Evaluate reply risk and whether human approval is required.",
                output_summary=(
                    f"Risk level={risk_check['risk_level']}, "
                    f"requires_human_review={risk_check['requires_human_review']}."
                ),
            ),
        }

    def _workflow(self, state: TicketMultiAgentState) -> TicketMultiAgentState:
        result = self.workflow_agent.run(
            ticket_id=state["ticket_id"],
            triage_result=state["triage_result"],
            risk_result=state["risk_result"],
        )
        return {
            "workflow_result": result,
            "ticket": result["updated_ticket"],
            "audit_trail": self._append_audit_entry(
                state,
                agent_name="WorkflowAgent",
                action="recommend_ticket_workflow",
                input_summary="Recommend the next ticket status, owner department, and follow-up action.",
                output_summary=(
                    f"next_status={result['next_status']}, "
                    f"assign_to_department={result['assign_to_department']}."
                ),
            ),
        }

    def _human_review(self, state: TicketMultiAgentState) -> TicketMultiAgentState:
        reply_suggestion = AIReplyDraftRead.model_validate(state["reply_result"]["reply_suggestion"])
        payload = {
            "ticket_id": state["ticket_id"],
            "suggestion_id": reply_suggestion.id,
            "supervisor_result": state["supervisor_result"],
            "triage_result": state["triage_result"],
            "knowledge_result": state["knowledge_result"],
            "similar_case_result": state["similar_case_result"],
            "reply_result": state["reply_result"],
            "risk_result": state["risk_result"],
            "workflow_result": state["workflow_result"],
            "draft_reply": reply_suggestion.suggested_content,
            "sources": [
                source.model_dump() if hasattr(source, "model_dump") else dict(source)
                for source in reply_suggestion.sources_json
            ],
            "confidence": reply_suggestion.confidence,
        }
        decision = interrupt(payload)
        return {
            "human_review_payload": payload,
            "review_decision": decision,
        }

    def _finalize(self, state: TicketMultiAgentState) -> TicketMultiAgentState:
        return {
            "final_output": {
                "ticket": state["ticket"],
                "supervisor_result": state["supervisor_result"],
                "triage_result": state["triage_result"],
                "knowledge_result": state["knowledge_result"],
                "similar_case_result": state["similar_case_result"],
                "reply_result": state["reply_result"],
                "risk_result": state["risk_result"],
                "workflow_result": state["workflow_result"],
                "audit_trail": state.get("audit_trail", []),
                "review_decision": state.get("review_decision"),
            }
        }

    @staticmethod
    def _append_audit_entry(
        state: TicketMultiAgentState,
        *,
        agent_name: str,
        action: str,
        input_summary: str,
        output_summary: str,
        status: str = "success",
    ) -> list[dict]:
        # audit_trail 是前端时间线和面试讲解的核心亮点，
        # 每个 Agent 跑完都统一补一条标准结构记录。
        entries = list(state.get("audit_trail", []))
        entries.append(
            {
                "agent_name": agent_name,
                "action": action,
                "input_summary": input_summary,
                "output_summary": output_summary,
                "status": status,
                "timestamp": datetime.now(UTC).isoformat(),
            }
        )
        return entries
