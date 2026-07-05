'''
Author: Bwaw. 1294245800@qq.com
Date: 2026-06-01 20:15:06
LastEditors: Bwaw. 1294245800@qq.com
LastEditTime: 2026-07-04 20:43:09
FilePath: \My-platform\backend\app\repositories\agent_run_repository.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.agent_run_log import AgentRunLog


class AgentRunRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, run_log: AgentRunLog) -> AgentRunLog:
        self.db.add(run_log)
        self.db.commit()
        self.db.refresh(run_log)
        return run_log

    def save(self, run_log: AgentRunLog) -> AgentRunLog:
        self.db.add(run_log)
        self.db.commit()
        self.db.refresh(run_log)
        return run_log

    def get_by_run_id(self, run_id: str) -> AgentRunLog | None:
        statement = select(AgentRunLog).where(AgentRunLog.run_id == run_id)
        return self.db.scalar(statement)

    def list_by_ticket_id(self, 
    ticket_id: int,
    *,
    run_type: str | None = None,
    status: str | None = None,
    ) -> list[AgentRunLog]:
        return self.list_filtered(ticket_id=ticket_id, run_type=run_type, status=status)

    def _apply_filters(
        self,
        statement,
        *,
        ticket_id: int | None = None,
        run_type: str | None = None,
        status: str | None = None,
    ):
        statement = statement.where(AgentRunLog.ticket_id == ticket_id)
        if run_type:
            statement = statement.where(AgentRunLog.run_type == run_type)
        if status:
            statement = statement.where(AgentRunLog.status == status)
        return statement

    def list_filtered(
        self,
        *,
        ticket_id: int | None = None,
        run_type: str | None = None,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[AgentRunLog]:
        statement = select(AgentRunLog)
        statement = self._apply_filters(
            statement,
            ticket_id=ticket_id,
            run_type=run_type,
            status=status,
        )
        statement = statement.order_by(AgentRunLog.created_at.desc(), AgentRunLog.id.desc())
        if limit is not None:
            statement = statement.limit(limit)
        if offset is not None:
            statement = statement.offset(offset)
        return list(self.db.scalars(statement).all())

    def count_filtered(
        self,
        *,
        ticket_id: int | None = None,
        run_type: str | None = None,
        status: str | None = None,
    ) -> int:
        statement = select(func.count()).select_from(AgentRunLog)
        statement = self._apply_filters(
            statement,
            ticket_id=ticket_id,
            run_type=run_type,
            status=status,
        )
        return self.db.scalar(statement) or 0
