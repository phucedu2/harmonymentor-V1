"""Quãng: số + tính chất.

Claim:
- MUS-INT-001  Số quãng đếm chữ cái, tính cả nốt đầu (Fankhauser tr. 43; OMT Intervals).
- MUS-INT-002  Quãng từ chủ âm âm giai trưởng: P1 M2 M3 P4 P5 M6 M7 P8 (F tr. 43–44; OMT).
- MUS-INT-003  Tăng/giảm = lớn/nhỏ hơn nửa cung so với đúng/trưởng/thứ (F tr. 43; OMT).
- MUS-INT-005  A4 và d5 cùng 6 nửa cung nhưng khác tên (F tr. 44; SRS 4.4.1).
- MUS-INT-008  Không có quãng 1 giảm (F bài tập 20).
- MUS-INT-009  Đảo quãng: số cộng = 9, M↔m, P↔P, A↔d (F tr. 55; OMT).
- MUS-INT-010  Quãng kép = quãng đơn + 7, tính chất giữ nguyên (F tr. 55; OMT).

Quy ước hiển thị (QĐ-2.1 = A): dùng A/d như SRS; nhận cả +/°/o khi nhập (OMT ghi "A or +", "d or o").
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .errors import InvalidInterval, UnsupportedInterval, UnsupportedSpelling
from .pitch import LETTERS, NATURAL_PC, Note, parse_note

# Số nửa cung của quãng đúng/trưởng tính từ chủ âm âm giai trưởng (MUS-INT-002).
_BASE_SEMITONES = {1: 0, 2: 2, 3: 4, 4: 5, 5: 7, 6: 9, 7: 11}
_PERFECT_NUMBERS = {1, 4, 5}

# Độ lệch (nửa cung) so với quãng đúng/trưởng → tính chất (MUS-INT-003).
_PERFECT_QUALITIES = {-2: "dd", -1: "d", 0: "P", 1: "A", 2: "AA"}
_MAJOR_QUALITIES = {-3: "dd", -2: "d", -1: "m", 0: "M", 1: "A", 2: "AA"}
_QUALITY_OFFSET_PERFECT = {v: k for k, v in _PERFECT_QUALITIES.items()}
_QUALITY_OFFSET_MAJOR = {v: k for k, v in _MAJOR_QUALITIES.items()}

# Bí danh nhập → dạng chuẩn.
_QUALITY_ALIASES = {
    "P": "P", "M": "M", "m": "m",
    "A": "A", "+": "A", "aug": "A",
    "d": "d", "°": "d", "o": "d", "dim": "d",
    "AA": "AA", "++": "AA",
    "dd": "dd", "°°": "dd", "oo": "dd",
}
_INTERVAL_RE = re.compile(r"^\s*(AA|dd|\+\+|°°|oo|aug|dim|P|M|m|A|\+|d|°|o)(\d+)\s*$")

_INVERT_QUALITY = {"P": "P", "M": "m", "m": "M", "A": "d", "d": "A", "AA": "dd", "dd": "AA"}


@dataclass(frozen=True)
class Interval:
    quality: str  # "dd", "d", "m", "M", "P", "A", "AA"
    number: int   # 1 = đồng âm, 8 = quãng tám, 9 = quãng 9 ...

    def __post_init__(self):
        if self.number < 1:
            raise InvalidInterval("Số của quãng phải ≥ 1", number=self.number)
        simple = self.simple_number
        table = _QUALITY_OFFSET_PERFECT if simple in _PERFECT_NUMBERS else _QUALITY_OFFSET_MAJOR
        if self.quality not in table:
            kind = "đúng/tăng/giảm" if simple in _PERFECT_NUMBERS else "trưởng/thứ/tăng/giảm"
            raise InvalidInterval(
                f"Quãng {self.number} chỉ có tính chất {kind}", quality=self.quality, number=self.number
            )
        if self.number == 1 and table[self.quality] < 0:
            # MUS-INT-008: không có quãng 1 giảm.
            raise InvalidInterval("Không có quãng 1 giảm", quality=self.quality, number=self.number)

    @property
    def simple_number(self) -> int:
        """Số của quãng đơn tương ứng (1..7). Quãng 8 → 1 về tính chất (đúng)."""
        return (self.number - 1) % 7 + 1

    @property
    def is_compound(self) -> bool:
        return self.number > 8

    @property
    def semitones(self) -> int:
        simple = self.simple_number
        octaves = (self.number - 1) // 7
        table = _QUALITY_OFFSET_PERFECT if simple in _PERFECT_NUMBERS else _QUALITY_OFFSET_MAJOR
        return _BASE_SEMITONES[simple] + 12 * octaves + table[self.quality]

    @property
    def name(self) -> str:
        return f"{self.quality}{self.number}"

    def __str__(self) -> str:
        return self.name


def parse_interval(text: str | Interval) -> Interval:
    """Đọc 'M3', 'A4', '+4', '°5', 'o5', 'P8', 'M9'."""
    if isinstance(text, Interval):
        return text
    m = _INTERVAL_RE.match(text or "")
    if not m:
        raise InvalidInterval(f"Không đọc được tên quãng: {text!r}", value=text)
    return Interval(_QUALITY_ALIASES[m.group(1)], int(m.group(2)))


def _quality_from_offset(simple: int, offset: int) -> str:
    table = _PERFECT_QUALITIES if simple in _PERFECT_NUMBERS else _MAJOR_QUALITIES
    if offset not in table:
        raise UnsupportedInterval(
            "Tính chất quãng vượt tăng kép/giảm kép", simple_number=simple, offset=offset
        )
    return table[offset]


def interval_between(lower: str | Note, upper: str | Note) -> Interval:
    """Quãng đi lên từ `lower` tới `upper`.

    - Có quãng tám ở cả hai nốt: tính chính xác, kể cả quãng kép (MUS-INT-010).
    - Không có quãng tám: coi `upper` là nốt gần nhất phía trên, kết quả là quãng đơn.
    """
    a, b = parse_note(lower), parse_note(upper)
    if (a.octave is None) != (b.octave is None):
        raise InvalidInterval("Hai nốt phải cùng có hoặc cùng không có quãng tám")

    if a.octave is not None:
        steps = b.diatonic_index - a.diatonic_index
        if steps < 0:
            raise InvalidInterval("Nốt thứ hai thấp hơn nốt thứ nhất; Engine chỉ gọi tên quãng đi lên",
                                  lower=str(a), upper=str(b))
        semis = b.midi - a.midi
        simple = steps % 7 + 1
        offset = semis - (_BASE_SEMITONES[simple] + 12 * (steps // 7))
        if steps == 0 and offset < 0:
            raise InvalidInterval("Nốt thứ hai thấp hơn nốt thứ nhất (không có quãng 1 giảm)",
                                  lower=str(a), upper=str(b))
        return Interval(_quality_from_offset(simple, offset), steps + 1)

    steps = (b.letter_index - a.letter_index) % 7
    simple = steps + 1
    semis = (b.pitch_class - a.pitch_class) % 12
    offset = (semis - _BASE_SEMITONES[simple] + 6) % 12 - 6
    if steps == 0 and offset < 0:
        raise InvalidInterval("Cùng chữ cái nhưng nốt sau thấp hơn: không có quãng 1 giảm",
                              lower=str(a), upper=str(b))
    return Interval(_quality_from_offset(simple, offset), simple)


def transpose(note: str | Note, interval: str | Interval) -> Note:
    """Dựng nốt cách `note` một quãng đi lên. Tên nốt suy từ chữ cái (quãng 3 = chữ cái + 2...)."""
    n, iv = parse_note(note), parse_interval(interval)
    steps = iv.number - 1
    idx = n.letter_index + steps
    letter = LETTERS[idx % 7]
    octave_shift = idx // 7
    target = NATURAL_PC[n.letter] + n.accidental + iv.semitones
    natural = NATURAL_PC[letter] + 12 * octave_shift
    accidental = target - natural
    if not -2 <= accidental <= 2:
        raise UnsupportedSpelling(
            f"{n} + {iv} cần dấu hóa vượt ±2", note=str(n), interval=iv.name, accidental=accidental
        )
    octave = None if n.octave is None else n.octave + octave_shift
    return Note(letter, accidental, octave)


def invert(interval: str | Interval) -> Interval:
    """Đảo quãng đơn (MUS-INT-009). Quãng 1 ↔ quãng 8."""
    iv = parse_interval(interval)
    if iv.number > 8:
        raise UnsupportedInterval("Chỉ đảo quãng đơn (tới quãng 8)", interval=iv.name)
    return Interval(_INVERT_QUALITY[iv.quality], 9 - iv.number)
