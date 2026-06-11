from __future__ import annotations

from typing import Any, TypedDict


class TicketMultiAgentState(TypedDict, total=False):
    ticket_id: int
    run_id: str
    thread_id: str
    ticket: dict[str, Any]
    supervisor_result: dict[str, Any]
    triage_result: dict[str, Any]
    knowledge_result: dict[str, Any]
    similar_case_result: dict[str, Any]
    reply_result: dict[str, Any]
    risk_result: dict[str, Any]
    workflow_result: dict[str, Any]
    audit_trail: list[dict[str, Any]]
    human_review_payload: dict[str, Any]
    review_decision: dict[str, Any]
    final_output: dict[str, Any]
