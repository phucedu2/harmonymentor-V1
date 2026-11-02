"""Mẫu nền (FR-17): danh sách phong cách cho giao diện, lấy từ style pack (styles/, ADR-012 đề xuất).

Trước 02/11/2026 file này chứa 4 mẫu 1 ô lặp y hệt. Nay mẫu thật nằm ở `styles/<id>.py` và bộ phối khí
`arranger.py`; file này giữ tên cũ (`STYLES`, `drum_events`) để mã và dự án cũ vẫn chạy (id pop/ballad/bossa/lofi
giữ nguyên).
"""
from __future__ import annotations

from typing import Optional

from .arranger import BEATS_PER_BAR, drum_events_for
from .styles import ORDER, public

STYLES: dict[str, dict] = {sid: public(sid) for sid in ORDER}


def drum_events(style: str, bars: int, key: str = "C", chords: Optional[list[Optional[str]]] = None,
                seed: int = 1, energy: int = 2) -> list[dict]:
    """Trải trống của cả bản phối (4 vòng) ra sự kiện có start_beat tính từ đầu bài."""
    return drum_events_for(key, style, chords or [None] * bars, seed, energy)


__all__ = ["BEATS_PER_BAR", "STYLES", "drum_events"]
