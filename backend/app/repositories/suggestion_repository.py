'''
Author: Bwaw. 1294245800@qq.com
Date: 2026-06-01 16:02:25
LastEditors: Bwaw. 1294245800@qq.com
LastEditTime: 2026-07-03 17:10:47
FilePath: \My-platform\backend\app\repositories\suggestion_repository.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.ai_suggestion import AISuggestion
from app.models.ticket import Ticket


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

    def _apply_pending_filters(
        self,
        statement,
        *,
        ticket_id: int | None = None,
    ):
        statement = statement.where(AISuggestion.suggestion_type == "reply", AISuggestion.status == "draft")
        if ticket_id is not None:
            statement = statement.where(AISuggestion.ticket_id == ticket_id)
        return statement

    def list_pending_reply_suggestions(
        self,
        *,
        ticket_id: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[tuple[AISuggestion, Ticket]]:
        statement = select(AISuggestion, Ticket).join(Ticket, AISuggestion.ticket_id == Ticket.id)
        statement = self._apply_pending_filters(statement, ticket_id=ticket_id)
        statement = statement.order_by(AISuggestion.created_at.desc(), AISuggestion.id.desc())
        if limit is not None:
            statement = statement.limit(limit)  
        if offset is not None:
            statement = statement.offset(offset)
        rows = self.db.execute(statement).all()
        return [(row[0], row[1]) for row in rows]

    def count_pending_reply_suggestions(
        self,
        *,
        ticket_id: int | None = None,
    ) -> int:
        statement = select(func.count(AISuggestion.id))
        statement = self._apply_pending_filters(statement, ticket_id=ticket_id)
        result = self.db.execute(statement).scalar()
        return result or 0
