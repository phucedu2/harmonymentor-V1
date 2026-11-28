"""Thành phần cộng tác cf (ADR-008 mục 4, D-2 chờ Thắng duyệt)."""

from __future__ import annotations

from datetime import datetime
from typing import Iterable, Mapping, Sequence

READY = 0.60


def skill_cf(skill: str, neighbor_ids: Sequence[str], neighbor_mastery: Mapping[str, Mapping[str, float]],
             ready: float = READY) -> float | None:
    """Tỷ lệ láng giềng hợp lệ có mastery ≥ ngưỡng sẵn sàng tại mốc thời gian.

    Láng giềng chưa làm kỹ năng vẫn ở mẫu số (tính là chưa học tốt). Không có láng giềng thì không có cf."""
    if not neighbor_ids:
        return None
    good = sum(1 for n in neighbor_ids if neighbor_mastery.get(n, {}).get(skill, 0.0) >= ready)
    return good / len(neighbor_ids)


def mastery_as_of(events: Iterable[tuple[datetime, str, float]], cutoff: datetime) -> dict[str, float]:
    """Mastery từng kỹ năng ngay trước mốc cutoff, từ các sự kiện (thời điểm, kỹ năng, score_after).

    Mốc là chặt: sự kiện đúng tại cutoff không được dùng ("trước thời điểm gợi ý")."""
    latest: dict[str, tuple[datetime, float]] = {}
    for at, skill, score in events:
        if at < cutoff and (skill not in latest or at >= latest[skill][0]):
            latest[skill] = (at, score)
    return {skill: score for skill, (_, score) in latest.items()}
