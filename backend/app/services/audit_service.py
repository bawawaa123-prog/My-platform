from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog
from app.models.user import User
from app.repositories.audit_log_repository import AuditLogRepository


class AuditService:
    def __init__(self, db: Session):
        self.repository = AuditLogRepository(db)

    def log_action(
        self,
        *,
        user: User | None,
        action: str,
        target_type: str,
        target_id: int,
        detail_json: dict,
    ) -> AuditLog:
        audit_log = AuditLog(
            user_id=user.id if user else None,
            action=action,
            target_type=target_type,
            target_id=target_id,
            detail_json=detail_json,
        )
        return self.repository.create(audit_log)
