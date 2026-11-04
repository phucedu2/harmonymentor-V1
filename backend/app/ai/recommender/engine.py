"""Ghép ba tầng thành danh sách bài (04 mục 6.5 bước 1–7, R-1: tối đa k ≤ 5 bài, `few_eligible`)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping, Sequence

from ..skill_mapping import is_mvp
from .cf import skill_cf
from .reasons import reason_for
from .scoring import FULL, Components, Weights, cold_of, lesson_score

MAX_K = 5
DEFAULT_THRESHOLDS = (0.60, 0.80)


@dataclass(frozen=True)
class LessonInfo:
    lesson_id: str
    order: int
    title: str
    skills: frozenset[str]   # skill_id của các câu đang chạy trong bài (04 mục 6.5)
    prereqs: frozenset[str]  # tiên quyết của các kỹ năng đó, trừ kỹ năng bài tự dạy


@dataclass(frozen=True)
class Ranked:
    lesson_id: str
    order: int
    title: str
    score: float
    content: float
    mastery: float
    due: float
    cf: float | None
    reason_code: str
    reason: str
    badge: str
    skills: tuple[str, ...]


@dataclass
class RecInput:
    lessons: Sequence[LessonInfo]
    mastery: Mapping[str, float]            # chỉ kỹ năng đã đánh giá; thiếu = 0 ở bước lọc (ADR-008 mục 3)
    due_skills: frozenset[str]
    content: Mapping[str, float]            # điểm nội dung theo kỹ năng; thiếu = 0
    neighbor_ids: Sequence[str] | None      # None hoặc rỗng → công thức người học mới
    neighbor_mastery: Mapping[str, Mapping[str, float]]
    k: int = MAX_K
    goal_text: str | None = None
    thresholds: Mapping[str, tuple[float, float]] = field(default_factory=dict)
    weights: Weights = FULL                 # trọng số đầy đủ lấy từ cấu hình; bản người học mới suy ra bằng cold_of
    skill_names: Mapping[str, str] = field(default_factory=dict)
    new_learner: bool = False               # chưa làm gì, chưa placement → lý do "bắt đầu từ nền tảng"


@dataclass
class RecOutput:
    ranked: list[Ranked]
    few_eligible: bool
    weights: Weights
    excluded: dict[str, str]


def _thr(inp: RecInput, skill: str) -> tuple[float, float]:
    return inp.thresholds.get(skill, DEFAULT_THRESHOLDS)


def rule_filter(lesson: LessonInfo, inp: RecInput) -> str | None:
    """Bước 1. Trả lý do loại, hoặc None nếu bài qua lọc."""
    mvp = [s for s in lesson.skills if is_mvp(s)]
    if not mvp:
        return "no_mvp_skill"
    if all(inp.mastery.get(s, 0.0) >= _thr(inp, s)[1] for s in mvp):
        return "all_mastered"
    if any(inp.mastery.get(p, 0.0) < _thr(inp, p)[0] for p in lesson.prereqs):
        return "prereq_not_ready"
    return None


def recommend(inp: RecInput) -> RecOutput:
    if not 1 <= inp.k <= MAX_K:
        raise ValueError("k phải trong khoảng 1–5 (R-1)")
    weights = inp.weights if inp.neighbor_ids else cold_of(inp.weights)
    excluded: dict[str, str] = {}
    scored: list[Ranked] = []
    for lesson in inp.lessons:
        why = rule_filter(lesson, inp)
        if why:
            excluded[lesson.lesson_id] = why
            continue
        comps = []
        for s in sorted(x for x in lesson.skills if is_mvp(x)):
            cf = skill_cf(s, inp.neighbor_ids, inp.neighbor_mastery, ready=_thr(inp, s)[0]) if inp.neighbor_ids else None
            comps.append(Components(s, inp.content.get(s, 0.0), inp.mastery.get(s, 0.0),
                                    1.0 if s in inp.due_skills else 0.0, cf))
        # Bước 6: chỉ kỹ năng chưa thành thạo. Lọc trước theo ngưỡng riêng của từng kỹ năng (cột
        # mastery_threshold), nên lesson_score không lọc thêm.
        open_comps = [c for c in comps if c.mastery < _thr(inp, c.skill_id)[1]]
        ls = lesson_score(open_comps, weights, mastery_threshold=float("inf"))
        code, text, badge = reason_for(ls, weights, inp.goal_text, inp.skill_names, foundation=inp.new_learner)
        scored.append(Ranked(lesson.lesson_id, lesson.order, lesson.title, ls.score, ls.content, ls.mastery,
                             ls.due, ls.cf, code, text, badge, tuple(c.skill_id for c in ls.skills)))
    # Bằng điểm thì theo thứ tự chương trình, để danh sách tất định.
    scored.sort(key=lambda r: (-round(r.score, 12), r.order, r.lesson_id))
    top = scored[: inp.k]
    return RecOutput(top, few_eligible=len(scored) < MAX_K, weights=weights, excluded=excluded)
