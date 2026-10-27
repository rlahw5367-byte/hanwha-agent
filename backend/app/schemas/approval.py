
from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field

class ApprovalOut(BaseModel):
    req_id: str
    text: str
    requester: str
    action_type: str
    status: str
    requested_at: datetime
    events: list[str]

class ApprovalSummaryOut(BaseModel):
    waiting: int
    approved_today: int
    rejected_today: int
    avg_minutes: int | None

class ApprovalListOut(BaseModel):
    summary: ApprovalSummaryOut
    items: list[ApprovalOut]

class DecisionOut(BaseModel):
    req_id: str
    status: str
    message: str

class RejectIn(BaseModel):
    note: str = Field(min_length=1)
