from __future__ import annotations

from typing import Any, TypedDict


class TicketAgentState(TypedDict, total=False):
    ticket_id: int
    run_id: str
    thread_id: str
    ticket: dict[str, Any]
    classification: dict[str, Any]
    retrieved_context: dict[str, Any]
    knowledge_hits: list[dict[str, Any]]
    similar_tickets: list[dict[str, Any]]
    reply_suggestion: dict[str, Any]
    risk_check: dict[str, Any]
    human_review_payload: dict
    review_decision: dict
    reviewed_suggestion: dict[str, Any]
    final_output: dict[str, Any]
