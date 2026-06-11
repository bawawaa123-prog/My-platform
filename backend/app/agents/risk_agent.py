from __future__ import annotations

from app.agents.base_agent import BaseTicketAgent
from app.schemas.ai import AIReplyDraftRead


class RiskAgent(BaseTicketAgent):
    agent_name = "RiskAgent"

    def run(self, *, ticket_id: int, reply_result: dict) -> dict:
        ticket = self.ticket_service.get_ticket(ticket_id)
        suggestion = AIReplyDraftRead.model_validate(reply_result["reply_suggestion"])
        risk = self.risk_service.evaluate_ticket_reply(
            ticket=ticket,
            reply_suggestion=suggestion,
        )
        return {
            "agent_name": self.agent_name,
            "risk_check": risk.model_dump(mode="json"),
        }
