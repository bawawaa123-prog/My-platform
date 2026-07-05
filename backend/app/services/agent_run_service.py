'''
Author: Bwaw. 1294245800@qq.com
Date: 2026-06-01 20:15:45
LastEditors: Bwaw. 1294245800@qq.com
LastEditTime: 2026-07-04 20:46:07
FilePath: \My-platform\backend\app\services\agent_run_service.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.agent_run_log import AgentRunLog
from app.repositories.agent_run_repository import AgentRunRepository


class AgentRunService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = AgentRunRepository(db)

    def upsert_run_log(
        self,
        *,
        ticket_id: int,
        run_id: str,
        run_type: str,
        status: str,
        input_json: dict,
        output_json: dict,
        audit_trail_json: list[dict],
        created_by: int | None = None,
        error_message: str | None = None,
    ) -> AgentRunLog:
        existing = self.repository.get_by_run_id(run_id)
        if existing is None:
            run_log = AgentRunLog(
                ticket_id=ticket_id,
                run_id=run_id,
                run_type=run_type,
                status=status,
                input_json=input_json,
                output_json=output_json,
                audit_trail_json=audit_trail_json,
                error_message=error_message,
                created_by=created_by,
            )
            return self.repository.create(run_log)

        existing.ticket_id = ticket_id
        existing.run_type = run_type
        existing.status = status
        existing.input_json = input_json
        existing.output_json = output_json
        existing.audit_trail_json = audit_trail_json
        existing.error_message = error_message
        if created_by is not None:
            existing.created_by = created_by
        return self.repository.save(existing)

    def list_by_ticket_id(
        self, 
        ticket_id: int,
        *,
        run_type: str | None = None,
        status: str | None = None,
        ) -> list[AgentRunLog]:
        return self.repository.list_filtered(ticket_id=ticket_id, run_type=run_type, status=status)

    def get_by_run_id(self, run_id: str) -> AgentRunLog:
        run_log = self.repository.get_by_run_id(run_id)
        if run_log is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent run log not found",
            )
        return run_log

    def list_page_by_id(
        self,
        ticket_id: int,
        *,
        run_type: str | None = None,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> dict:
        total = self.repository.count_filtered(
            ticket_id=ticket_id, run_type=run_type, status=status
        )
        items = self.repository.list_filtered(
            ticket_id=ticket_id,
            run_type=run_type,
            status=status,
            limit=limit,
            offset=offset,
        )
        return {"items": items, "total": total, "limit": limit, "offset": offset}
