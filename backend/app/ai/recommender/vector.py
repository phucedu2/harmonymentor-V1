"""Vector (value, assessed) 14 chiều của một người học (ADR-008 mục 3)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from ..skill_mapping import GROUP_CODES, SKILL_MAPPING, is_mvp


@dataclass(frozen=True)
class GroupVector:
    values: tuple[float, ...]
    assessed: tuple[bool, ...]
    # Tập kỹ năng đã đánh giá của từng chiều, để đo độ trùng kỹ năng (ADR-008 mục 3b).
    skills: tuple[frozenset[str], ...]

    @property
    def assessed_count(self) -> int:
        return sum(self.assessed)


def build_vector(mastery: Mapping[str, float]) -> GroupVector:
    """mastery chỉ chứa kỹ năng đã đánh giá. Chiều chưa đánh giá để value 0 cho đủ hình dạng,
    không có nghĩa mastery bằng 0; kỹ năng chưa đánh giá trong một nhóm không kéo trung bình xuống."""
    buckets: list[list[float]] = [[] for _ in GROUP_CODES]
    names: list[set[str]] = [set() for _ in GROUP_CODES]
    for skill, score in mastery.items():
        if skill not in SKILL_MAPPING:
            raise KeyError(f"Kỹ năng {skill} không có trong bảng ánh xạ ADR-008")
        if not is_mvp(skill):
            continue
        i = GROUP_CODES.index(SKILL_MAPPING[skill][1])
        buckets[i].append(float(score))
        names[i].add(skill)
    values = tuple(sum(b) / len(b) if b else 0.0 for b in buckets)
    return GroupVector(values=values, assessed=tuple(bool(b) for b in buckets),
                       skills=tuple(frozenset(n) for n in names))
