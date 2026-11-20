"""Mastery EMA theo 04 mục 6.3, D-3/L-3/L-4 (Thắng chốt 31/10) và luật ôn 2A (Phúc chốt 04/11).

Hàm thuần, không đọc CSDL, để test bằng số và để `rebuild_mastery` tính lại từ lịch sử cho ra
đúng kết quả như lúc cập nhật trực tiếp.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

EMA_ALPHA = 0.3
PLACEMENT_SCORE = 0.65
WEAK_MIN_ATTEMPTS = 5  # 04 Bảng 19: "dưới 0,60 sau ít nhất 5 lượt"
# Giờ Việt Nam cố định UTC+7 (không có giờ mùa hè), dùng cho giới hạn "1 lượt ôn/kỹ năng/ngày".
VN_TZ = timezone(timedelta(hours=7))


def ema(old: float, result: float, alpha: float = EMA_ALPHA) -> float:
    return old + alpha * (result - old)


def exercise_result(history: list[bool], correct: bool) -> float | None:
    """Kết quả của một lượt làm câu bài tập, cho EMA.

    `history` là các lượt trước của cùng exercise_id (mọi phiên bản, không tính is_test), cũ → mới.
    None nghĩa là không cập nhật điểm (đúng lặp lại sau khi đã đúng: chống cày điểm, S7).
    """
    if not correct:
        return 0.0  # L-3: mọi lượt sai hợp lệ đều kéo EMA về 0
    if not history:
        return 1.0  # đúng ngay lần đầu
    return 0.5 if history[-1] is False else None  # đúng sau lượt sai = "làm lại"


def review_result(correct: bool) -> float:
    return 1.0 if correct else 0.0


def review_counts(*, self_check: bool, due_at: datetime, now: datetime, already_counted_today: bool) -> bool:
    """Luật 2A: lượt ôn có thành sự kiện mastery không."""
    if self_check:  # thẻ tự đánh giá không kiểm chứng được (1A đã bỏ)
        return False
    if due_at > now:  # ôn trước hạn không tính, khớp luật Leitner PR #14
        return False
    return not already_counted_today


def vn_day(moment: datetime) -> str:
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.astimezone(VN_TZ).date().isoformat()


def is_ready(score: float, ready_threshold: float) -> bool:
    return score >= ready_threshold


def is_mastered(score: float, mastery_threshold: float) -> bool:
    return score >= mastery_threshold


def is_weak(score: float, attempts_count: int, ready_threshold: float) -> bool:
    return attempts_count >= WEAK_MIN_ATTEMPTS and score < ready_threshold


def level(score: float | None, attempts_count: int, ready: float, master: float) -> str:
    if score is None:
        return "not_assessed"
    if is_mastered(score, master):
        return "mastered"
    if is_ready(score, ready):
        return "ready"
    return "weak" if is_weak(score, attempts_count, ready) else "learning"
