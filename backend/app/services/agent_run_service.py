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

    def list_by_ticket_id(self, ticket_id: int) -> list[AgentRunLog]:
        return self.repository.list_by_ticket_id(ticket_id)

    def get_by_run_id(self, run_id: str) -> AgentRunLog:
        run_log = self.repository.get_by_run_id(run_id)
        if run_log is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent run log not found",
            )
        return run_log
