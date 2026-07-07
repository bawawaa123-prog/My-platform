'''
Author: Bwaw. 1294245800@qq.com
Date: 2026-06-01 16:29:51
LastEditors: Bwaw. 1294245800@qq.com
LastEditTime: 2026-07-03 16:27:18
FilePath: \My-platform\backend\app\schemas\review.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.utils.datetime_utils import UTCDatetime


class SuggestionApproveRequest(BaseModel):
    final_content: str | None = Field(default=None, min_length=1)


class SuggestionEditRequest(BaseModel):
    final_content: str = Field(min_length=1)


class SuggestionRejectRequest(BaseModel):
    reject_reason: str = Field(min_length=1, max_length=1000)


class PendingSuggestionRead(BaseModel):
    id: int
    ticket_id: int
    ticket_title: str
    ticket_status: str
    ticket_priority: str
    ticket_category: str
    customer_email: str
    suggestion_type: str
    source_workflow: str = "single_agent_rag"
    source_run_id: str | None = None
    suggested_content: str
    reasoning_summary: str | None
    sources_json: list[dict]
    confidence: float
    status: str
    created_at: UTCDatetime
    updated_at: UTCDatetime

    model_config = ConfigDict(from_attributes=True)


class PendingSuggestionPage(BaseModel):
    items: list[PendingSuggestionRead]
    total: int
    limit: int | None = None
    offset: int | None = None

class SuggestionReviewResponse(BaseModel):
    id: int
    ticket_id: int
    suggestion_type: str
    source_workflow: str = "single_agent_rag"
    source_run_id: str | None = None
    suggested_content: str
    reasoning_summary: str | None
    sources_json: list[dict]
    confidence: float
    status: str
    reviewed_by: int | None
    reviewed_at: UTCDatetime | None
    final_content: str | None
    reject_reason: str | None
    created_at: UTCDatetime
    updated_at: UTCDatetime

    model_config = ConfigDict(from_attributes=True)
