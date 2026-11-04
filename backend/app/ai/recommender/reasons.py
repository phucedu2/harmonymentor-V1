"""Lý do gợi ý theo tầng đóng góp nhiều điểm nhất (04 mục 6.5 bước 7). Mẫu câu cố định, không sinh bằng LLM.

Câu lý do nêu tên kỹ năng cụ thể hoặc mục tiêu của người học (đề GĐ2 mục 5)."""

from __future__ import annotations

from typing import Mapping

from .scoring import Components, LessonScore, Weights

# Khi bằng điểm, ưu tiên theo thứ tự này để kết quả tất định.
_ORDER = ("due", "content", "mastery", "cf")
BADGES = {"due": "Cần ôn tập", "content": "Theo mục tiêu", "mastery": "Củng cố kỹ năng yếu",
          "cf": "Người giống bạn chọn", "foundation": "Bắt đầu từ nền tảng"}


def _short(goal: str, limit: int = 40) -> str:
    goal = " ".join(goal.split())
    return goal if len(goal) <= limit else goal[: limit - 1].rstrip() + "…"


def _skills(c: Components | LessonScore) -> tuple[Components, ...]:
    return c.skills if isinstance(c, LessonScore) and c.skills else ((c,) if isinstance(c, Components) else ())


def _name(skill: str, names: Mapping[str, str] | None) -> str:
    return (names or {}).get(skill, skill)


def reason_for(c: Components | LessonScore, w: Weights, goal_text: str | None,
               names: Mapping[str, str] | None = None, foundation: bool = False) -> tuple[str, str, str]:
    parts = {"due": w.due * c.due, "content": w.content * c.content,
             "mastery": w.mastery * (1 - c.mastery), "cf": w.cf * (c.cf or 0.0)}
    # Người học chưa làm gì, chưa có mục tiêu (đề GĐ2 mục 6): mọi tầng đều bằng nhau nên nói thẳng là bắt đầu từ nền tảng.
    if foundation and parts["content"] == 0 and parts["due"] == 0:
        return "foundation", "Bắt đầu từ nền tảng: bài này không cần kiến thức trước.", BADGES["foundation"]
    code = max(_ORDER, key=lambda k: (parts[k], -_ORDER.index(k)))
    skills = _skills(c)
    if code == "content":
        best = max(skills, key=lambda s: (s.content, s.skill_id), default=None)
        about = f" (kỹ năng {_name(best.skill_id, names)})" if best else ""
        text = (f"Phù hợp với mục tiêu “{_short(goal_text)}” của bạn{about}." if goal_text
                else f"Phù hợp với nội dung bạn đang hướng tới{about}.")
    elif code == "due":
        due = [s for s in skills if s.due > 0]
        text = (f"Đã đến lịch ôn “{_name(due[0].skill_id, names)}” để không quên." if due
                else "Đã đến lịch ôn tập để không quên kiến thức.")
    elif code == "mastery":
        weak = min(skills, key=lambda s: (s.mastery, s.skill_id), default=None)
        text = (f"Giúp bạn củng cố “{_name(weak.skill_id, names)}”, kỹ năng còn yếu nhất của bài." if weak
                else "Giúp bạn củng cố kỹ năng còn yếu.")
    else:
        top = max(skills, key=lambda s: (s.cf or 0.0, s.skill_id), default=None)
        text = (f"Người học có trình độ giống bạn thường học tốt “{_name(top.skill_id, names)}” ở bước này." if top
                else "Người học có trình độ giống bạn thường học tốt bài này ở bước tiếp theo.")
    return code, text, BADGES[code]
