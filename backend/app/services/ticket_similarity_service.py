from __future__ import annotations

import hashlib
import math

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.ticket import Ticket
from app.models.ticket_embedding import TicketEmbedding
from app.repositories.suggestion_repository import SuggestionRepository
from app.repositories.ticket_embedding_repository import TicketEmbeddingRepository
from app.repositories.ticket_message_repository import TicketMessageRepository
from app.repositories.ticket_repository import TicketRepository
from app.schemas.ticket import SimilarTicketRead
from app.services.embedding_service import get_embedding_provider


class TicketSimilarityService:
    def __init__(self, db: Session):
        self.db = db
        self.ticket_repository = TicketRepository(db)
        self.ticket_embedding_repository = TicketEmbeddingRepository(db)
        self.ticket_message_repository = TicketMessageRepository(db)
        self.suggestion_repository = SuggestionRepository(db)
        self.embedding_provider = get_embedding_provider()

    def list_similar_tickets(self, ticket_id: int, top_k: int = 5) -> list[SimilarTicketRead]:
        ticket = self.ticket_repository.get_by_id(ticket_id)
        if ticket is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found",
            )

        self.ensure_ticket_embedding(ticket)
        current_vector = self.embedding_provider.embed_text(self._build_embedding_text(ticket))

        historical_tickets = self.ticket_repository.list_resolved_or_closed_excluding(ticket.id)
        if not historical_tickets:
            return []

        results: list[SimilarTicketRead] = []
        for historical_ticket in historical_tickets:
            self.ensure_ticket_embedding(historical_ticket)
            historical_vector = self.embedding_provider.embed_text(
                self._build_embedding_text(historical_ticket)
            )
            similarity = round(self._cosine_similarity(current_vector, historical_vector), 6)
            results.append(
                SimilarTicketRead(
                    ticket_id=historical_ticket.id,
                    title=historical_ticket.title,
                    content_preview=self._build_content_preview(historical_ticket.content),
                    similarity=similarity,
                    resolution=self._build_resolution_summary(historical_ticket),
                )
            )

        results.sort(key=lambda item: item.similarity, reverse=True)
        return results[:top_k]

    def ensure_ticket_embedding(self, ticket: Ticket) -> TicketEmbedding:
        embedding_text = self._build_embedding_text(ticket)
        content_hash = self._build_content_hash(embedding_text)
        embedding_id = self.embedding_provider.build_embedding_id(embedding_text)

        existing = self.ticket_embedding_repository.get_by_ticket_id(ticket.id)
        if existing is None:
            return self.ticket_embedding_repository.create(
                TicketEmbedding(
                    ticket_id=ticket.id,
                    embedding_id=embedding_id,
                    content_hash=content_hash,
                )
            )

        if existing.content_hash == content_hash and existing.embedding_id == embedding_id:
            return existing

        existing.content_hash = content_hash
        existing.embedding_id = embedding_id
        return self.ticket_embedding_repository.save(existing)

    @staticmethod
    def _build_embedding_text(ticket: Ticket) -> str:
        parts = [ticket.title, ticket.content, ticket.category, ticket.priority]
        return "\n".join(part.strip() for part in parts if part and part.strip())

    @staticmethod
    def _build_content_hash(content: str) -> str:
        normalized = " ".join(content.split()).strip()
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

    def _build_resolution_summary(self, ticket: Ticket) -> str:
        reviewed_suggestion = self.suggestion_repository.get_latest_reviewed_reply_by_ticket_id(ticket.id)
        if reviewed_suggestion and reviewed_suggestion.final_content:
            return reviewed_suggestion.final_content

        messages = self.ticket_message_repository.list_by_ticket_id(ticket.id)
        for message in reversed(messages):
            if message.sender_type in {"agent", "system", "ai"}:
                return message.content

        if ticket.ai_summary:
            return ticket.ai_summary

        return "No recorded resolution summary available."

    @staticmethod
    def _build_content_preview(content: str, max_length: int = 200) -> str:
        normalized = " ".join(content.split()).strip()
        if len(normalized) <= max_length:
            return normalized
        return f"{normalized[: max_length - 3]}..."

    @staticmethod
    def _cosine_similarity(left: list[float], right: list[float]) -> float:
        if not left or not right or len(left) != len(right):
            return 0.0

        numerator = sum(a * b for a, b in zip(left, right, strict=False))
        left_norm = math.sqrt(sum(a * a for a in left))
        right_norm = math.sqrt(sum(b * b for b in right))
        if left_norm == 0.0 or right_norm == 0.0:
            return 0.0
        return numerator / (left_norm * right_norm)
