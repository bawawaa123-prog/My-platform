from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.ai_suggestion import AISuggestion


class SuggestionRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, suggestion: AISuggestion) -> AISuggestion:
        self.db.add(suggestion)
        self.db.commit()
        self.db.refresh(suggestion)
        return suggestion

    def get_by_id(self, suggestion_id: int) -> AISuggestion | None:
        return self.db.get(AISuggestion, suggestion_id)

    def save(self, suggestion: AISuggestion) -> AISuggestion:
        self.db.add(suggestion)
        self.db.commit()
        self.db.refresh(suggestion)
        return suggestion

    def list_by_ticket_id(self, ticket_id: int) -> list[AISuggestion]:
        statement = (
            select(AISuggestion)
            .where(AISuggestion.ticket_id == ticket_id)
            .order_by(AISuggestion.created_at.desc(), AISuggestion.id.desc())
        )
        return list(self.db.scalars(statement).all())

    def list_reply_suggestions_by_ticket_id(self, ticket_id: int) -> list[AISuggestion]:
        statement = (
            select(AISuggestion)
            .where(
                AISuggestion.ticket_id == ticket_id,
                AISuggestion.suggestion_type == "reply",
            )
            .order_by(AISuggestion.created_at.desc(), AISuggestion.id.desc())
        )
        return list(self.db.scalars(statement).all())

    def get_latest_reviewed_reply_by_ticket_id(self, ticket_id: int) -> AISuggestion | None:
        statement = (
            select(AISuggestion)
            .where(
                AISuggestion.ticket_id == ticket_id,
                AISuggestion.suggestion_type == "reply",
                AISuggestion.status.in_(("approved", "edited")),
            )
            .order_by(AISuggestion.reviewed_at.desc(), AISuggestion.id.desc())
        )
        return self.db.scalar(statement)
