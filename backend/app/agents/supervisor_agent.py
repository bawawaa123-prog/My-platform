from __future__ import annotations

from app.agents.base_agent import BaseTicketAgent


class SupervisorAgent(BaseTicketAgent):
    agent_name = "SupervisorAgent"

    def run(self, *, ticket: dict) -> dict:
        return {
            "agent_name": self.agent_name,
            "workflow_mode": "fixed_sequence_v1",
            "planned_agents": ["triage", "knowledge", "similar_case", "reply", "risk", "workflow"],
            "requires_human_review": True,
            "summary": (
                f"Ticket #{ticket['id']} will go through triage, knowledge retrieval, "
                "historical similar-case analysis, reply drafting, risk review, workflow routing, "
                "and then human approval."
            ),
        }
