from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from sqlalchemy.orm import Session

from app.models.ai_suggestion import AISuggestion
from app.models.ticket import Ticket
from app.repositories.suggestion_repository import SuggestionRepository
from app.schemas.ai import AIReplyDraftRead
from app.services.knowledge_service import KnowledgeSearchItem, KnowledgeService
from app.services.llm_service import LLMGenerationError, get_llm_client


@dataclass
class RetrievedContext:
    chunks: list[KnowledgeSearchItem]
    confidence: float
    low_confidence_reason: str | None = None


class RagService:
    def __init__(self, db: Session):
        self.db = db
        self.knowledge_service = KnowledgeService(db)
        self.suggestion_repository = SuggestionRepository(db)
        self.llm_client = get_llm_client()

    def retrieve_context(self, query: str, top_k: int = 5) -> RetrievedContext:
        # 这里除了拿回知识命中结果，还负责给出一个可解释的 confidence，
        # 方便前端和 RiskAgent 判断“这份草稿靠不靠谱”。
        chunks = self.knowledge_service.search_knowledge(query=query, top_k=top_k)
        if not chunks:
            return RetrievedContext(
                chunks=[],
                confidence=0.15,
                low_confidence_reason="No matching knowledge base content was found.",
            )

        top_score = max(chunk.score for chunk in chunks)
        avg_score = sum(chunk.score for chunk in chunks) / len(chunks)
        confidence = max(0.15, min(0.95, round((top_score * 0.7) + (avg_score * 0.3), 3)))

        if top_score < 0.2:
            return RetrievedContext(
                chunks=chunks,
                confidence=0.25,
                low_confidence_reason="Knowledge matches are weak, so the reply should stay cautious.",
            )

        return RetrievedContext(chunks=chunks, confidence=confidence)

    @staticmethod
    def build_ticket_search_query(ticket: Ticket) -> str:
        return "\n".join(
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

    def build_answer_prompt(
        self,
        ticket: Ticket,
        context: RetrievedContext,
        *,
        supplemental_context: str | None = None,
    ) -> str:
        # 回复生成 prompt 同时接收知识命中、低置信度提示和补充上下文，
        # 让 ReplyAgent 能把 triage / similar case 信息也拼进来。
        sources_block = self._build_sources_block(context.chunks)
        low_confidence_note = context.low_confidence_reason or "None"
        template = self._load_generate_reply_prompt()
        return template.format(
            title=ticket.title,
            content=ticket.content,
            customer_name=ticket.customer_name,
            customer_email=ticket.customer_email,
            category=ticket.category,
            priority=ticket.priority,
            sentiment=ticket.sentiment,
            ai_summary=ticket.ai_summary or "",
            recommended_department=ticket.recommended_department or "",
            confidence=context.confidence,
            low_confidence_reason=low_confidence_note,
            sources_block=sources_block,
            supplemental_context=supplemental_context or "None",
        )

    def generate_ticket_reply(self, ticket: Ticket) -> AIReplyDraftRead:
        # 标准入口：先根据工单构造检索 query，再走统一的 suggestion 创建逻辑。
        search_query = self.build_ticket_search_query(ticket)
        context = self.retrieve_context(search_query, top_k=5)
        return self.generate_ticket_reply_from_context(ticket, context)

    def generate_ticket_reply_from_context(
        self,
        ticket: Ticket,
        context: RetrievedContext,
        *,
        supplemental_context: str | None = None,
        source_workflow: str = "single_agent",
    ) -> AIReplyDraftRead:
        return self._create_reply_suggestion(
            ticket,
            context,
            supplemental_context=supplemental_context,
            source_workflow=source_workflow,
        )

    @staticmethod
    def deserialize_knowledge_hits(items: list[dict]) -> list[KnowledgeSearchItem]:
        return [
            KnowledgeSearchItem(
                doc_id=item["doc_id"],
                chunk_id=item["chunk_id"],
                chunk_index=item["chunk_index"],
                content_preview=item["content_preview"],
                score=item["score"],
                embedding_id=item.get("embedding_id"),
            )
            for item in items
        ]

    def _create_reply_suggestion(
        self,
        ticket: Ticket,
        context: RetrievedContext,
        *,
        supplemental_context: str | None = None,
        source_workflow: str = "single_agent",
    ) -> AIReplyDraftRead:
        # 无论是普通 RAG 还是 Multi-Agent ReplyAgent，
        # 最终都统一落成 AISuggestion，保证审核流只维护一套数据结构。
        if not context.chunks:
            draft_reply = (
                "We have received your request and started reviewing it. "
                "At the moment, we could not find a strong matching knowledge-base article, "
                "so a support agent should review the case before sending a final response."
            )
            if supplemental_context:
                draft_reply = (
                    f"{draft_reply} Our team is also checking similar resolved cases and "
                    "the triage assessment before confirming the final response."
                )
            reasoning_summary = self._build_reasoning_summary(
                context,
                supplemental_context=supplemental_context,
            )
        else:
            prompt = self.build_answer_prompt(
                ticket,
                context,
                supplemental_context=supplemental_context,
            )
            try:
                draft_reply = self.llm_client.generate_text(prompt, temperature=0.2)
            except LLMGenerationError:
                draft_reply = self._build_fallback_reply(
                    ticket,
                    context,
                    supplemental_context=supplemental_context,
                )
            reasoning_summary = self._build_reasoning_summary(
                context,
                supplemental_context=supplemental_context,
            )

        sources = [
            {
                "doc_id": chunk.doc_id,
                "chunk_id": chunk.chunk_id,
                "chunk_index": chunk.chunk_index,
                "content_preview": chunk.content_preview,
                "score": chunk.score,
            }
            for chunk in context.chunks
        ]

        suggestion = AISuggestion(
            ticket_id=ticket.id,
            suggestion_type="reply",
            source_workflow=source_workflow,
            suggested_content=draft_reply,
            reasoning_summary=reasoning_summary,
            sources_json=sources,
            confidence=context.confidence,
            status="draft",
        )
        created = self.suggestion_repository.create(suggestion)
        return AIReplyDraftRead.model_validate(created)

    @staticmethod
    def _build_sources_block(chunks: list[KnowledgeSearchItem]) -> str:
        if not chunks:
            return "No sources found."
        return "\n\n".join(
            f"[Doc {chunk.doc_id} / Chunk {chunk.chunk_id} / Score {chunk.score}] {chunk.content_preview}"
            for chunk in chunks
        )

    @staticmethod
    def _build_reasoning_summary(
        context: RetrievedContext,
        *,
        supplemental_context: str | None = None,
    ) -> str:
        base_reason = context.low_confidence_reason
        if not base_reason:
            base_reason = f"Reply drafted from {len(context.chunks)} retrieved knowledge chunks."
        if supplemental_context:
            return f"{base_reason} Historical similar-case context was also considered."
        return base_reason

    @staticmethod
    def _build_fallback_reply(
        ticket: Ticket,
        context: RetrievedContext,
        *,
        supplemental_context: str | None = None,
    ) -> str:
        if not context.chunks:
            fallback = (
                "We have received your request and escalated it for manual review because we could not "
                "find enough verified knowledge to draft a confident reply."
            )
            if supplemental_context:
                fallback = (
                    f"{fallback} We are also comparing this case with similar previously resolved requests."
                )
            return fallback

        fallback = (
            f"We have received your request about \"{ticket.title}\" and are reviewing it based on our internal knowledge base. "
            "A support agent will confirm the final handling steps before replying to the customer."
        )
        if supplemental_context:
            fallback = (
                f"{fallback} We are also referencing similar resolved cases to keep the response consistent."
            )
        return fallback

    @staticmethod
    def _load_generate_reply_prompt() -> str:
        prompt_path = Path(__file__).resolve().parent.parent / "prompts" / "generate_reply.txt"
        return prompt_path.read_text(encoding="utf-8")
