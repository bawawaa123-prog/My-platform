from sqlalchemy import select,func
from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


class AuditLogRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, audit_log: AuditLog) -> AuditLog:
        self.db.add(audit_log)
        self.db.commit()
        self.db.refresh(audit_log)
        return audit_log

    def list_by_target(self, target_type: str, target_id: int) -> list[AuditLog]:
        statement = (
            select(AuditLog)
            .where(AuditLog.target_type == target_type, AuditLog.target_id == target_id)
            .order_by(AuditLog.created_at.asc(), AuditLog.id.asc())
        )
        return list(self.db.scalars(statement).all())

    def _apply_filters(
        self,
        statement,
        *,
        action: str | None = None,
        target_type: str | None = None,
        target_id: int | None = None,
        user_id: int | None = None,
    ):
        if action:
            statement = statement.where(AuditLog.action == action)
        if target_type:
            statement = statement.where(AuditLog.target_type == target_type)
        if target_id:
            statement = statement.where(AuditLog.target_id == target_id)
        if user_id:
            statement = statement.where(AuditLog.user_id == user_id)
        return statement

    def list_filtered(
        self,
        *,
        action: str | None = None,
        target_type: str | None = None,
        target_id: int | None = None,
        user_id: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> list[AuditLog]:
        statement = select(AuditLog)
        statement = self._apply_filters(
            statement,
            action=action,
            target_type=target_type,
            target_id=target_id,
            user_id=user_id,
        )
        if limit is not None:
            statement = statement.limit(limit)
        if offset is not None:
            statement = statement.offset(offset)
        return list(self.db.scalars(statement).all())

    def count_filtered(
        self,
        action: str | None = None,
        target_type: str | None = None,
        target_id: int | None = None,
        user_id: int | None = None,
    ) -> int:
        statement = select(func.count()).select_from(AuditLog)
        statement = self._apply_filters(
            statement,
            action=action,
            target_type=target_type,
            target_id=target_id,
            user_id=user_id,
        )
        return self.db.scalar(statement) or 0

