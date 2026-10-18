"""Âm giai.

Mỗi âm giai được dựng bằng danh sách quãng tính từ chủ âm, nên tên nốt tự động
dùng mỗi chữ cái đúng một lần (MUS-SCALE-003, F tr. 16).

Claim:
- MUS-SCALE-002  Trưởng: 2 2 1 2 2 2 1 (F tr. 16; OMT Major Scales "W-W-H-W-W-W-H").
- MUS-SCALE-005  Thứ tự nhiên: 2 1 2 2 1 2 2 (F tr. 17; OMT Minor Scales).
- MUS-SCALE-006  Thứ hòa âm: 2 1 2 2 1 3 1 (F tr. 17; OMT).
- MUS-SCALE-007  Thứ giai điệu: lên 2 1 2 2 2 2 1, xuống = thứ tự nhiên (F tr. 17; OMT).
- MUS-SCALE-008  Dorian: 2 1 2 2 2 1 2 (F tr. 18). Cấp 4, chỉ 1 nguồn.

SRS K05 chỉ dạy thứ tự nhiên ở MVP; các dạng khác có sẵn để dùng sau, mỗi loại ghi `mvp`.
"""

from __future__ import annotations

from dataclasses import dataclass

from .errors import UnknownScaleType
from .interval import interval_between, transpose
from .pitch import Note, parse_note


@dataclass(frozen=True)
class ScaleType:
    id: str
    intervals: tuple[str, ...]
    claim_ids: tuple[str, ...]
    mvp: bool
    descending_intervals: tuple[str, ...] | None = None  # chỉ thứ giai điệu


SCALE_TYPES: dict[str, ScaleType] = {
    "major": ScaleType("major", ("P1", "M2", "M3", "P4", "P5", "M6", "M7"), ("MUS-SCALE-002",), True),
    "natural_minor": ScaleType(
        "natural_minor", ("P1", "M2", "m3", "P4", "P5", "m6", "m7"), ("MUS-SCALE-005",), True
    ),
    "harmonic_minor": ScaleType(
        "harmonic_minor", ("P1", "M2", "m3", "P4", "P5", "m6", "M7"), ("MUS-SCALE-006",), False
    ),
    "melodic_minor": ScaleType(
        "melodic_minor",
        ("P1", "M2", "m3", "P4", "P5", "M6", "M7"),
        ("MUS-SCALE-007",),
        False,
        descending_intervals=("P1", "M2", "m3", "P4", "P5", "m6", "m7"),
    ),
    "dorian": ScaleType("dorian", ("P1", "M2", "m3", "P4", "P5", "M6", "m7"), ("MUS-SCALE-008",), False),
}

# Bí danh nhập cho tiện; "minor" = thứ tự nhiên theo SRS K05.
_ALIASES = {"minor": "natural_minor", "aeolian": "natural_minor", "ionian": "major"}


def get_scale_type(scale_type: str) -> ScaleType:
    key = _ALIASES.get(scale_type, scale_type)
    if key not in SCALE_TYPES:
        raise UnknownScaleType(f"Loại âm giai không hỗ trợ: {scale_type!r}",
                               supported=sorted(SCALE_TYPES))
    return SCALE_TYPES[key]


def build_scale(tonic: str | Note, scale_type: str = "major", descending: bool = False) -> list[Note]:
    """Trả 7 nốt theo thứ tự đi lên (hoặc đi xuống nếu `descending`).

    Ví dụ: build_scale("E") → E F# G# A B C# D# (F tr. 16: bậc 3 là G#, không phải Ab).
    """
    st = get_scale_type(scale_type)
    root = parse_note(tonic)
    intervals = st.intervals
    if descending and st.descending_intervals:
        intervals = st.descending_intervals
    notes = [transpose(root, iv) for iv in intervals]
    return list(reversed(notes)) if descending else notes


def scale_degree_of(note: str | Note, tonic: str | Note, scale_type: str = "major") -> int | None:
    """Bậc (1..7) của `note` trong âm giai, hoặc None nếu không thuộc (so tên nốt, không so phím)."""
    n = parse_note(note)
    for i, s in enumerate(build_scale(tonic, scale_type), start=1):
        if s.same_spelling(n):
            return i
    return None


def scale_step_pattern(tonic: str | Note, scale_type: str = "major") -> list[int]:
    """Số nửa cung giữa các bậc liền nhau, kể cả bậc 7 → chủ âm. Dùng để kiểm thử công thức."""
    notes = build_scale(tonic, scale_type)
    root = notes[0]
    offsets = [interval_between(root, n).semitones for n in notes] + [12]
    return [b - a for a, b in zip(offsets, offsets[1:])]
