"""Vector (value, assessed) 14 chiều của một người học (ADR-008 mục 3)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping

import numpy as np

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


# Tính sẵn chiều của từng kỹ năng MVP: build_vector chạy cho mọi ứng viên láng giềng mỗi lần gợi ý (E11).
_DIM = {skill: GROUP_CODES.index(group) for skill, (_, group) in SKILL_MAPPING.items() if is_mvp(skill)}
_EMPTY = frozenset()


def build_vector(mastery: Mapping[str, float]) -> GroupVector:
    """mastery chỉ chứa kỹ năng đã đánh giá. Chiều chưa đánh giá để value 0 cho đủ hình dạng,
    không có nghĩa mastery bằng 0; kỹ năng chưa đánh giá trong một nhóm không kéo trung bình xuống."""
    n = len(GROUP_CODES)
    total = [0.0] * n
    names: list[list[str]] = [[] for _ in range(n)]
    for skill, score in mastery.items():
        i = _DIM.get(skill)
        if i is None:
            if skill not in SKILL_MAPPING:
                raise KeyError(f"Kỹ năng {skill} không có trong bảng ánh xạ ADR-008")
            continue  # post_mvp: không thuộc vector (V5)
        total[i] += float(score)
        names[i].append(skill)
    return GroupVector(values=tuple(total[i] / len(names[i]) if names[i] else 0.0 for i in range(n)),
                       assessed=tuple(bool(x) for x in names),
                       skills=tuple(frozenset(x) if x else _EMPTY for x in names))


@dataclass(frozen=True)
class PoolMatrix:
    """Vector của nhiều người dưới dạng ma trận, id đã sắp xếp. Cùng nghĩa với dict {id: GroupVector}
    nhưng dựng thẳng từ các dòng mastery bằng numpy, để 2.000 ứng viên không phải tạo 2.000 đối tượng."""

    ids: tuple[str, ...]
    values: np.ndarray    # (n, 14)
    assessed: np.ndarray  # (n, 14) bool


def build_pool(rows: Iterable[tuple[str, str, float]]) -> PoolMatrix:
    """rows: (user_id, skill_id, score) của kỹ năng đã đánh giá. Kỹ năng post_mvp bị bỏ qua như build_vector."""
    users: list[str] = []
    r_idx: list[str] = []
    d_idx: list[int] = []
    scores: list[float] = []
    for uid, skill, score in rows:
        d = _DIM.get(skill)
        if d is None:
            if skill not in SKILL_MAPPING:
                raise KeyError(f"Kỹ năng {skill} không có trong bảng ánh xạ ADR-008")
            continue
        r_idx.append(uid)
        d_idx.append(d)
        scores.append(float(score))
    ids = tuple(sorted(set(r_idx)))
    pos = {u: i for i, u in enumerate(ids)}
    n, k = len(ids), len(GROUP_CODES)
    total, count = np.zeros((n, k)), np.zeros((n, k))
    if n:
        rr = np.fromiter((pos[u] for u in r_idx), dtype=np.int64, count=len(r_idx))
        dd = np.asarray(d_idx, dtype=np.int64)
        np.add.at(total, (rr, dd), np.asarray(scores))
        np.add.at(count, (rr, dd), 1.0)
    with np.errstate(divide="ignore", invalid="ignore"):
        values = np.where(count > 0, total / np.maximum(count, 1), 0.0)
    return PoolMatrix(ids, values, count > 0)
