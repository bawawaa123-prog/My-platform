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

    def list_by_ticket_id(self, ticket_id: int) -> list[AgentRunLog]:
        statement = (
            select(AgentRunLog)
            .where(AgentRunLog.ticket_id == ticket_id)
            .order_by(AgentRunLog.created_at.desc(), AgentRunLog.id.desc())
        )
        return list(self.db.scalars(statement).all())
