'''
Author: Bwaw. 1294245800@qq.com
Date: 2026-07-03 14:49:14
LastEditors: Bwaw. 1294245800@qq.com
LastEditTime: 2026-07-03 14:51:10
FilePath: \My-platform\backend\app\api\audit_logs.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.auth import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.audit_log import AuditLogPage, AuditLogRead
from app.services.audit_service import AuditService



router = APIRouter(prefix="/api/audit-logs", tags=["audit-logs"])


@router.get("",response_model=AuditLogPage)
def list_audit_logs(
    action: str | None = Query(default=None),
    target_type: str | None = Query(default=None),
    target_id: int | None = Query(default=None, ge=1),
    user_id: int | None = Query(default=None, ge=1),
    limit: int | None = Query(default=None, ge=1, le=100),
    offset: int | None = Query(default=None, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AuditLogPage:
    page = AuditService(db).list_audit_logs(
        action=action,
        target_type=target_type,
        target_id=target_id,
        user_id=user_id,
        limit=limit,
        offset=offset,
    )
    return AuditLogPage(
        items=[AuditLogRead.model_validate(item) for item in page["items"]],
        total=page["total"],
        limit=page["limit"],
        offset=page["offset"],
    )



