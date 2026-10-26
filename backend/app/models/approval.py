from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base

# 외부로 나가는 요청 하나를 저장하는 테이블(모델)
class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    thread_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    run_id: Mapped[str | None] = mapped_column(ForeignKey("runs.id"), nullable=True)
    requester_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    approver_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    action_type: Mapped[str] = mapped_column(String(16), default="slack")
    payload: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(24), default="대기중") # 대기중, 승인, 승인 실행, 반려됨, 실패...
    requested_at: Mapped[datetime] = mapped_column(default=datetime.now)
    decided_at: Mapped[datetime | None] = mapped_column(nullable=True)

# 누가 언제 무엇을 했는지 정보를 저장하는 테이블 
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    approval_id: Mapped[str | None] = mapped_column(ForeignKey("approval_requests.id"), nullable=True, index=True)
    run_id: Mapped[str | None] = mapped_column(String(32), nullable=True)
    at: Mapped[datetime] = mapped_column(default=datetime.now)
    actor: Mapped[str] = mapped_column(String(50))
    event: Mapped[str] = mapped_column(String(64))
    detail: Mapped[str] = mapped_column(Text, default="")

