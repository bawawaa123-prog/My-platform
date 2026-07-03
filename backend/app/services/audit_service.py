'''
Author: Bwaw. 1294245800@qq.com
Date: 2026-05-30 16:21:19
LastEditors: Bwaw. 1294245800@qq.com
LastEditTime: 2026-07-03 14:48:20
FilePath: \My-platform\backend\app\services\audit_service.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
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

    def list_audit_logs(
        self,
        *,
        user_id: int | None = None,
        action: str | None = None,
        target_type: str | None = None,
        target_id: int | None = None,
        limit: int = 10,
        offset: int = 0,
    ) -> dict:
        items=self.repository.list_filtered(
            user_id=user_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            limit=limit,
            offset=offset
        )
        total=self.repository.count_filtered(
            user_id=user_id,
            action=action,
            target_type=target_type,
            target_id=target_id
        )
        return {"items": items, "limit": limit, "offset": offset, "total": total}
