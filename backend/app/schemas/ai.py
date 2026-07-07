from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.utils.datetime_utils import UTCDatetime

from app.schemas.ticket import (
    RecommendedDepartment,
    TicketCategory,
    TicketPriority,
    TicketSentiment,
)


class TicketClassification(BaseModel):
    category: TicketCategory
    priority: TicketPriority
    sentiment: TicketSentiment
    need_human: bool
    summary: str = Field(min_length=1, max_length=500)
    recommended_department: RecommendedDepartment

    model_config = ConfigDict(extra="forbid")


class AIReplySource(BaseModel):
    doc_id: int
    chunk_id: int
    chunk_index: int
    content_preview: str
    score: float


class AIReplyDraftRead(BaseModel):
    id: int
    ticket_id: int
    suggestion_type: str
    source_workflow: str = "single_agent_rag"
    source_run_id: str | None = None
    suggested_content: str
    reasoning_summary: str | None
    sources_json: list[AIReplySource]
    confidence: float
    status: str
    reviewed_by: int | None = None
    reviewed_at: UTCDatetime | None = None
    final_content: str | None = None
    reject_reason: str | None = None
    created_at: UTCDatetime
    updated_at: UTCDatetime

    model_config = ConfigDict(from_attributes=True)


class AIWorkflowProcessRead(BaseModel):
    ticket: dict
    classification: dict
    knowledge_hits: list[dict]
    similar_tickets: list[dict]
    reply_suggestion: dict
    risk_check: dict
    reviewed_suggestion: dict | None = None
    review_decision: dict | None = None


class AIWorkflowPendingReviewRead(BaseModel):
    run_id: str
    thread_id: str
    status: Literal["pending_review"]
    pending_node: str
    interrupt_id: str | None = None
    ticket: dict
    classification: dict
    knowledge_hits: list[dict]
    similar_tickets: list[dict]
    draft_reply: dict
    sources: list[dict]
    confidence: float
    risk_check: dict


class AIMultiAgentPendingReviewRead(BaseModel):
    run_id: str
    thread_id: str
    status: Literal["pending_review"]
    pending_node: str
    interrupt_id: str | None = None
    ticket: dict
    supervisor_result: dict
    triage_result: dict
    knowledge_result: dict
    similar_case_result: dict
    reply_result: dict
    risk_result: dict
    workflow_result: dict
    draft_reply: dict
    sources: list[dict]
    confidence: float
    audit_trail: list[dict]


class AIMultiAgentProcessRead(BaseModel):
    ticket: dict
    supervisor_result: dict
    triage_result: dict
    knowledge_result: dict
    similar_case_result: dict
    reply_result: dict
    risk_result: dict
    workflow_result: dict
    audit_trail: list[dict] = []
    review_decision: dict | None = None
    reviewed_suggestion: dict | None = None


class AIWorkflowResumeRequest(BaseModel):
    action: Literal["approve", "edit", "reject"]
    thread_id: str | None = None
    run_id: str | None = None
    final_content: str | None = Field(default=None, min_length=1)
    reject_reason: str | None = Field(default=None, min_length=1, max_length=1000)

    @model_validator(mode="after")
    def validate_resume_payload(self) -> "AIWorkflowResumeRequest":
        if not self.thread_id and not self.run_id:
            raise ValueError("Either thread_id or run_id is required")
        if self.thread_id and self.run_id and self.thread_id != self.run_id:
            raise ValueError("thread_id and run_id must match when both are provided")
        if self.action == "edit" and not self.final_content:
            raise ValueError("final_content is required when action=edit")
        if self.action == "reject" and not self.reject_reason:
            raise ValueError("reject_reason is required when action=reject")
        return self

    def workflow_id(self) -> str:
        return self.thread_id or self.run_id or ""
