from __future__ import annotations

from copy import deepcopy

from sqlalchemy.orm import Session

from app.graphs.ticket_multi_agent_graph import TicketMultiAgentGraph
from app.services.agent_run_service import AgentRunService
from app.services.audit_service import AuditService
from app.services.ticket_service import TicketService


class MCPAgentService:
    def __init__(self, db: Session):
        self.db = db
        self.ticket_service = TicketService(db)
        self.agent_run_service = AgentRunService(db)
        self.audit_service = AuditService(db)

    def run_multi_agent_ticket_process(self, *, ticket_id: int, dry_run: bool = True) -> dict:
        self.ticket_service.get_ticket(ticket_id)
        graph = TicketMultiAgentGraph(self.db)

        if dry_run:
            return graph.preview(ticket_id)

        result = graph.start(
            ticket_id,
            created_by_user_id=self.ticket_service.get_system_user().id,
        ).model_dump(mode="json")
        self.audit_service.log_action(
            user=self.ticket_service.get_system_user(),
            action="mcp_run_multi_agent_ticket_process",
            target_type="ticket",
            target_id=ticket_id,
            detail_json={
                "dry_run": False,
                "run_id": result["run_id"],
                "pending_node": result["pending_node"],
                "status": result["status"],
            },
        )
        return result

    def get_agent_audit_trail(self, *, ticket_id: int) -> dict:
        self.ticket_service.get_ticket(ticket_id)
        run_logs = self.agent_run_service.list_by_ticket_id(ticket_id)
        latest_multi_agent_run = next(
            (run_log for run_log in run_logs if run_log.run_type == "multi_agent"),
            None,
        )
        if latest_multi_agent_run is None:
            return {
                "ticket_id": ticket_id,
                "run_id": None,
                "status": "not_found",
                "audit_trail": [],
            }

        return {
            "ticket_id": ticket_id,
            "run_id": latest_multi_agent_run.run_id,
            "status": latest_multi_agent_run.status,
            "audit_trail": deepcopy(latest_multi_agent_run.audit_trail_json or []),
        }
