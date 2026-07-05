'''
Author: Bwaw. 1294245800@qq.com
Date: 2026-05-30 16:12:09
LastEditors: Bwaw. 1294245800@qq.com
LastEditTime: 2026-07-02 15:31:05
FilePath: \My-platform\backend\app\schemas\ticket.py
Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
'''
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.utils.datetime_utils import UTCDatetime


TicketCategory = Literal[
    "payment",
    "account",
    "product",
    "refund",
    "invoice",
    "technical",
    "hr",
    "it",
    "other",
]
TicketPriority = Literal["low", "medium", "high", "urgent"]
TicketSentiment = Literal["positive", "neutral", "negative", "angry"]
TicketStatus = Literal["open", "ai_processing", "waiting_review", "in_progress", "resolved", "closed"]
RecommendedDepartment = Literal[
    "customer_support",
    "billing",
    "technical_support",
    "finance",
    "product",
    "hr",
    "it",
    "operations",
]


class TicketCreate(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    customer_name: str = Field(min_length=1, max_length=100)
    customer_email: EmailStr
    category: TicketCategory = "other"
    priority: TicketPriority = "medium"
    source: str = Field(default="manual", min_length=1, max_length=50)


class TicketUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    content: str | None = Field(default=None, min_length=1)
    customer_name: str | None = Field(default=None, min_length=1, max_length=100)
    customer_email: EmailStr | None = None
    category: TicketCategory | None = None
    priority: TicketPriority | None = None
    status: TicketStatus | None = None
    source: str | None = Field(default=None, min_length=1, max_length=50)
    assigned_to: int | None = None


class TicketRead(BaseModel):
    id: int
    title: str
    content: str
    customer_name: str
    customer_email: EmailStr
    category: TicketCategory
    priority: TicketPriority
    sentiment: TicketSentiment
    status: TicketStatus
    source: str
    ai_summary: str | None
    recommended_department: RecommendedDepartment | None
    assigned_to: int | None
    created_by: int
    closed_at: UTCDatetime | None
    created_at: UTCDatetime
    updated_at: UTCDatetime

    model_config = ConfigDict(from_attributes=True)


class SimilarTicketRead(BaseModel):
    ticket_id: int
    title: str
    content_preview: str
    similarity: float
    resolution: str

class TicketPage(BaseModel):
    items: list[TicketRead]
    total: int
    limit: int
    offset: int