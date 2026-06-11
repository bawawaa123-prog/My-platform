from __future__ import annotations

from app.agents.base_agent import BaseTicketAgent


class TriageAgent(BaseTicketAgent):
    agent_name = "TriageAgent"

    def run(self, *, ticket_id: int) -> dict:
        system_user = self.ticket_service.get_system_user()
        classification = self.ticket_service.classify_ticket(ticket_id, system_user)
        return {
            "agent_name": self.agent_name,
            "classification": classification.model_dump(mode="json"),
        }
