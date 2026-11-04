"""Công thức điểm của 04 mục 6.5 bước 5–6."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence


@dataclass(frozen=True)
class Weights:
    content: float
    mastery: float
    due: float
    cf: float


FULL = Weights(0.35, 0.25, 0.20, 0.20)
# Người học chưa có láng giềng: bỏ tầng cộng tác, cộng 0,20 vào tầng nội dung.
COLD = Weights(0.55, 0.25, 0.20, 0.0)


@dataclass(frozen=True)
class Components:
    skill_id: str
    content: float
    mastery: float
    due: float
    cf: float | None


@dataclass(frozen=True)
class LessonScore:
    score: float
    content: float
    mastery: float
    due: float
    cf: float | None
    skills: tuple[Components, ...] = field(default=())


def skill_score(c: Components, w: Weights) -> float:
    return w.content * c.content + w.mastery * (1 - c.mastery) + w.due * c.due + w.cf * (c.cf or 0.0)


def lesson_score(components: Sequence[Components], w: Weights, mastery_threshold: float = 0.80) -> LessonScore | None:
    """Trung bình trên các kỹ năng chưa thành thạo của bài. Bài không còn kỹ năng nào thì None."""
    open_ = tuple(c for c in components if c.mastery < mastery_threshold)
    if not open_:
        return None
    n = len(open_)
    cfs = [c.cf for c in open_ if c.cf is not None]
    return LessonScore(
        score=sum(skill_score(c, w) for c in open_) / n,
        content=sum(c.content for c in open_) / n,
        mastery=sum(c.mastery for c in open_) / n,
        due=sum(c.due for c in open_) / n,
        cf=sum(cfs) / len(cfs) if cfs else None,
        skills=open_,
    )
