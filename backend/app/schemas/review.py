from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SuggestionApproveRequest(BaseModel):
    final_content: str | None = Field(default=None, min_length=1)


class SuggestionEditRequest(BaseModel):
    final_content: str = Field(min_length=1)


class SuggestionRejectRequest(BaseModel):
    reject_reason: str = Field(min_length=1, max_length=1000)


class SuggestionReviewResponse(BaseModel):
    id: int
    ticket_id: int
    suggestion_type: str
    suggested_content: str
    reasoning_summary: str | None
    sources_json: list[dict]
    confidence: float
    status: str
    reviewed_by: int | None
    reviewed_at: datetime | None
    final_content: str | None
    reject_reason: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
