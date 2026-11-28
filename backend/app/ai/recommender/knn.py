"""Độ tương đồng chỉ trên chiều chung và tìm láng giềng (ADR-008 mục 3, 3b, 5).

Không dùng sklearn.NearestNeighbors như bản pipeline gợi ý: cosine ở đây tính trên tập chiều chung
riêng của từng cặp, nên ma trận đầy đủ của sklearn sẽ coi chiều chưa đánh giá là 0 và cho kết quả sai.
Phần tính hàng loạt dùng numpy để 2.000 ứng viên vẫn nhanh (E11).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from typing import Mapping

import numpy as np

from .vector import GroupVector, PoolMatrix


@dataclass(frozen=True)
class Similarity:
    value: float | None
    shared: tuple[int, ...]
    reason: str | None = None  # "zero_norm" khi một bên có độ dài 0 trên chiều chung


@dataclass(frozen=True)
class Neighbor:
    user_id: str
    similarity: float
    shared_dims: int


@dataclass
class NeighborResult:
    neighbors: list[Neighbor]
    # None: có láng giềng. "no_assessed_dims": người học chưa có chiều nào. "no_valid_neighbors": mọi ứng viên bị loại.
    reason: str | None
    min_shared_used: int
    excluded: Counter = field(default_factory=Counter)


def similarity(a: GroupVector, b: GroupVector) -> Similarity:
    shared = tuple(i for i, (x, y) in enumerate(zip(a.assessed, b.assessed)) if x and y)
    va = np.array([a.values[i] for i in shared], dtype=float)
    vb = np.array([b.values[i] for i in shared], dtype=float)
    na, nb = float(np.linalg.norm(va)), float(np.linalg.norm(vb))
    if not shared or na == 0.0 or nb == 0.0:
        # Q-5 phương án A (Thắng 30/10): không gán 0 hay 1, cặp này không thành láng giềng.
        return Similarity(None, shared, "zero_norm" if shared else None)
    return Similarity(float(va @ vb / (na * nb)), shared)


def skill_overlap(a: GroupVector, b: GroupVector, dim: int) -> float | None:
    """Jaccard của hai tập kỹ năng đã đánh giá trong một chiều. Chỉ để báo cáo (3b), chưa dùng để lọc."""
    sa, sb = a.skills[dim], b.skills[dim]
    if not sa or not sb:
        return None
    return len(sa & sb) / len(sa | sb)


def _matrix(pool: Mapping[str, GroupVector] | PoolMatrix) -> tuple[list[str], np.ndarray, np.ndarray]:
    if isinstance(pool, PoolMatrix):
        return list(pool.ids), pool.values, pool.assessed
    ids = sorted(pool)
    values = np.array([pool[u].values for u in ids], dtype=float).reshape(len(ids), -1)
    assessed = np.array([pool[u].assessed for u in ids], dtype=bool).reshape(len(ids), -1)
    return ids, values, assessed


def find_neighbors(target: GroupVector, pool: Mapping[str, GroupVector] | PoolMatrix, *, k: int = 10, min_shared: int = 3,
                   fallback: str = "a", exclude: str | None = None) -> NeighborResult:
    """Top k láng giềng hợp lệ, xếp theo độ tương đồng giảm dần rồi theo user_id (tất định, K10).

    fallback "a": không có láng giềng thì trả rỗng để dùng công thức người học mới.
    fallback "b": hạ ngưỡng số chiều chung dần xuống 1 rồi mới trả rỗng.
    """
    if target.assessed_count == 0:
        return NeighborResult([], "no_assessed_dims", min_shared)
    if not (pool.ids if isinstance(pool, PoolMatrix) else pool):
        return NeighborResult([], "no_valid_neighbors", min_shared)
    ids, values, assessed = _matrix(pool)
    keep = np.array([u != exclude for u in ids], dtype=bool)
    if not keep.any():
        return NeighborResult([], "no_valid_neighbors", min_shared)
    if not keep.all():
        ids = [u for u, k in zip(ids, keep) if k]
        values, assessed = values[keep], assessed[keep]
    t_val = np.array(target.values, dtype=float)
    t_ass = np.array(target.assessed, dtype=bool)
    shared = assessed & t_ass
    count = shared.sum(axis=1)
    dot = (values * t_val * shared).sum(axis=1)
    n_t = np.sqrt(((t_val ** 2) * shared).sum(axis=1))
    n_c = np.sqrt(((values ** 2) * shared).sum(axis=1))
    zero = (count > 0) & ((n_t == 0) | (n_c == 0))
    with np.errstate(divide="ignore", invalid="ignore"):
        sims = np.where(zero | (count == 0), np.nan, dot / (n_t * n_c))

    thresholds = [min_shared] if fallback == "a" else list(range(min_shared, 0, -1))
    excluded: Counter = Counter()
    for threshold in thresholds:
        valid = (~zero) & (count >= threshold) & (count > 0)
        excluded = Counter({"zero_norm": int(zero.sum()),
                            "too_few_shared": int(((~zero) & (count < threshold)).sum())})
        if valid.any():
            order = sorted(np.flatnonzero(valid), key=lambda i: (-round(float(sims[i]), 12), ids[i]))[:k]
            return NeighborResult([Neighbor(ids[i], float(sims[i]), int(count[i])) for i in order],
                                  None, threshold, excluded)
    return NeighborResult([], "no_valid_neighbors", thresholds[-1], excluded)
