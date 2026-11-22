"""Một bộ đếm lượt Gemini cho cả khóa, chia phần cho AI soạn bài và AI Tutor (ADR-033 mục V5, Phúc chọn 8A ngày 22/11/2026).

Vì sao: hạn mức thật của Google tính theo KHÓA (gói miễn phí của nhóm: 30 lượt/ngày), dùng chung cho soạn bài và Tutor.
Trước đợt 3 có hai bộ đếm không khớp nhau (20 bản nháp/24 giờ theo người tạo và 40 phần/24 giờ theo nhật ký), việc nền
thiếu `created_by` thì không bị đếm, và soạn bài có thể đốt hết lượt của học sinh.

- GEMINI_DAILY_BUDGET: tổng lượt mỗi ngày của khóa. 0 = không giới hạn chung (mặc định để test và máy không có khóa).
- GEMINI_AUTHORING_SHARE: phần cho soạn bài (mặc định 0,4: 30 lượt → 12 soạn bài, 18 Tutor). Phần còn lại của Tutor
  không cho soạn bài mượn, để học sinh luôn còn lượt hỏi.
- "Ngày Gemini" bắt đầu lúc 0 giờ Thái Bình Dương (giờ Google đặt lại hạn mức, 15:00 giờ Việt Nam mùa đông).
- Mỗi lần gọi `generate` của soạn bài (kể cả lần thử lại khi JSON hỏng) ghi một dòng `ai.llm.call` vào nhật ký, không phụ
  thuộc ai bấm. Tutor đếm theo tin nhắn đã gọi LLM như cũ (ai_tutor_service._llm_rows_today).
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import AdminAuditLog, ChatMessage

CALL_ACTION = "ai.llm.call"

try:
    from zoneinfo import ZoneInfo

    _PT = ZoneInfo("America/Los_Angeles")
except Exception:   # máy thiếu dữ liệu múi giờ: lấy giờ chuẩn Thái Bình Dương cố định
    _PT = timezone(timedelta(hours=-8))


class BudgetExceeded(RuntimeError):
    def __init__(self, purpose: str, used: int, limit: int):
        super().__init__(f"{purpose}:{used}/{limit}")
        self.purpose, self.used, self.limit = purpose, used, limit


def _now(now: datetime | None) -> datetime:
    now = now or datetime.now(timezone.utc)
    return now if now.tzinfo else now.replace(tzinfo=timezone.utc)


def day_start(now: datetime | None = None) -> datetime:
    """0 giờ Thái Bình Dương của "ngày Gemini" chứa `now`, đổi về UTC."""
    local = _now(now).astimezone(_PT)
    return local.replace(hour=0, minute=0, second=0, microsecond=0).astimezone(timezone.utc)


def total() -> int:
    try:
        return max(0, int(os.getenv("GEMINI_DAILY_BUDGET", "0")))
    except ValueError:
        return 0


def share() -> float:
    try:
        return min(1.0, max(0.0, float(os.getenv("GEMINI_AUTHORING_SHARE", "0.4"))))
    except ValueError:
        return 0.4


def limit(purpose: str) -> int | None:
    """Số lượt mỗi ngày của một bên; None = không giới hạn (GEMINI_DAILY_BUDGET=0)."""
    t = total()
    if t == 0:
        return None
    authoring = int(t * share())
    return authoring if purpose == "authoring" else t - authoring


def used(db: Session, purpose: str, now: datetime | None = None) -> int:
    start = day_start(now)
    # SQLite trả datetime không múi giờ (đã là UTC): so ở Python sau khi gắn UTC.
    if purpose == "authoring":
        rows = db.scalars(select(AdminAuditLog.created_at).where(AdminAuditLog.action == CALL_ACTION,
                                                                 AdminAuditLog.created_at >= start - timedelta(days=1)))
        return sum(1 for c in rows if (c if c.tzinfo else c.replace(tzinfo=timezone.utc)) >= start)
    q = select(ChatMessage.tool_calls, ChatMessage.created_at).where(
        ChatMessage.role == "assistant", ChatMessage.created_at >= start - timedelta(days=1))
    n = 0
    for tool_calls, created in db.execute(q):
        created = created if created.tzinfo else created.replace(tzinfo=timezone.utc)
        if created >= start and (tool_calls or {}).get("llm_calls"):
            n += 1
    return n


def remaining(db: Session, purpose: str, now: datetime | None = None) -> int | None:
    cap = limit(purpose)
    return None if cap is None else max(0, cap - used(db, purpose, now))


def require(db: Session, purpose: str, now: datetime | None = None) -> None:
    cap = limit(purpose)
    if cap is not None:
        n = used(db, purpose, now)
        if n >= cap:
            raise BudgetExceeded(purpose, n, cap)


def record_authoring(db: Session, actor_id: str | None, target_type: str, target_id: str, what: str) -> None:
    """Ghi một lượt gọi Gemini của soạn bài. Ghi cả khi không có người bấm (việc nền) để không lọt bộ đếm."""
    db.add(AdminAuditLog(actor_id=actor_id, action=CALL_ACTION, target_type=target_type, target_id=target_id[:96],
                         detail={"what": what}, created_at=_now(None)))


def summary(db: Session, now: datetime | None = None) -> dict:
    return {"total": total(), "authoring": {"limit": limit("authoring"), "used": used(db, "authoring", now)},
            "tutor": {"limit": limit("tutor"), "used": used(db, "tutor", now)}, "resets_at": day_start(now) + timedelta(days=1)}
