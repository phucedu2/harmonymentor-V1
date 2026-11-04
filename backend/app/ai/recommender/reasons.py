"""Lý do gợi ý theo tầng đóng góp nhiều điểm nhất (04 mục 6.5 bước 7). Mẫu câu cố định, không sinh bằng LLM."""

from __future__ import annotations

from .scoring import Components, LessonScore, Weights

# Khi bằng điểm, ưu tiên theo thứ tự này để kết quả tất định.
_ORDER = ("due", "content", "mastery", "cf")
BADGES = {"due": "Cần ôn tập", "content": "Theo mục tiêu", "mastery": "Củng cố kỹ năng", "cf": "Phù hợp trình độ"}


def _short(goal: str, limit: int = 40) -> str:
    goal = " ".join(goal.split())
    return goal if len(goal) <= limit else goal[: limit - 1].rstrip() + "…"


def reason_for(c: Components | LessonScore, w: Weights, goal_text: str | None) -> tuple[str, str, str]:
    parts = {"due": w.due * c.due, "content": w.content * c.content,
             "mastery": w.mastery * (1 - c.mastery), "cf": w.cf * (c.cf or 0.0)}
    code = max(_ORDER, key=lambda k: (parts[k], -_ORDER.index(k)))
    if code == "content" and goal_text:
        text = f"Phù hợp với mục tiêu “{_short(goal_text)}” của bạn."
    elif code == "content":
        text = "Phù hợp với nội dung bạn đang hướng tới."
    elif code == "due":
        text = "Đã đến lịch ôn tập để không quên kiến thức."
    elif code == "mastery":
        text = "Giúp bạn củng cố kỹ năng còn yếu."
    else:
        text = "Người học có trình độ tương tự thường học tốt bài này ở bước tiếp theo."
    return code, text, BADGES[code]
