"""Nốt nhạc: (letter, accidental, octave) theo SRS 4.4.

Claim: MUS-PITCH-002 (Đô giữa = C4, số quãng tám đổi tại nốt C),
MUS-ACC-002 (♯/♭ = ±1 nửa cung, 𝄪/𝄫 = ±2), MUS-ACC-003/004 (đồng âm khác tên).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from .errors import InvalidPitch, UnsupportedSpelling

LETTERS = "CDEFGAB"
# Lớp cao độ của 7 nốt trắng, tính từ C = 0.
NATURAL_PC = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}

MIN_ACCIDENTAL, MAX_ACCIDENTAL = -2, 2
MIN_OCTAVE, MAX_OCTAVE = 0, 8

# Dạng nhập được chấp nhận cho dấu hóa. Dạng hiển thị chuẩn là "#", "##", "b", "bb" (SRS: "Eb4", "F##3").
_ACCIDENTAL_TOKENS = {
    "": 0,
    "#": 1, "♯": 1,
    "##": 2, "x": 2, "𝄪": 2, "♯♯": 2,
    "b": -1, "♭": -1,
    "bb": -2, "𝄫": -2, "♭♭": -2,
    "n": 0, "♮": 0,
}
_PITCH_RE = re.compile(r"^\s*([A-Ga-g])(##|bb|♯♯|♭♭|#|b|♯|♭|x|𝄪|𝄫|n|♮)?(-?\d+)?\s*$")


@dataclass(frozen=True, order=False)
class Note:
    """Một tên nốt. `octave` là None khi chỉ quan tâm lớp cao độ (bài hợp âm, âm giai)."""

    letter: str
    accidental: int = 0
    octave: Optional[int] = None

    def __post_init__(self):
        if self.letter not in LETTERS:
            raise InvalidPitch(f"Tên chữ không hợp lệ: {self.letter!r}", letter=self.letter)
        if not MIN_ACCIDENTAL <= self.accidental <= MAX_ACCIDENTAL:
            raise UnsupportedSpelling(
                "Engine chỉ hỗ trợ dấu hóa từ giáng kép tới thăng kép",
                letter=self.letter,
                accidental=self.accidental,
            )
        if self.octave is not None and not MIN_OCTAVE <= self.octave <= MAX_OCTAVE:
            raise InvalidPitch(f"Quãng tám ngoài phạm vi 0–8: {self.octave}", octave=self.octave)

    # --- Thuộc tính suy ra -------------------------------------------------

    @property
    def letter_index(self) -> int:
        """Vị trí chữ cái trong C D E F G A B (0..6)."""
        return LETTERS.index(self.letter)

    @property
    def pitch_class(self) -> int:
        """Lớp cao độ 0..11 (MUS-PITCH-001). B#=0, Cb=11."""
        return (NATURAL_PC[self.letter] + self.accidental) % 12

    @property
    def midi(self) -> int:
        """SRS 4.4.1: midi = 12 × (octave + 1) + pc(letter) + accidental. Không dùng % 12,
        nên B#3 = 60 (= C4) và Cb4 = 59 (= B3), đúng quy tắc số quãng tám theo tên chữ."""
        if self.octave is None:
            raise InvalidPitch("Nốt không có quãng tám nên không có số MIDI", note=self.name)
        return 12 * (self.octave + 1) + NATURAL_PC[self.letter] + self.accidental

    @property
    def diatonic_index(self) -> int:
        """Số bậc chữ cái tuyệt đối (octave × 7 + letter_index), dùng để đếm số của quãng."""
        if self.octave is None:
            raise InvalidPitch("Cần quãng tám", note=self.name)
        return self.octave * 7 + self.letter_index

    @property
    def name(self) -> str:
        """Tên không kèm quãng tám, ví dụ 'Eb', 'F##'."""
        acc = "#" * self.accidental if self.accidental > 0 else "b" * -self.accidental
        return f"{self.letter}{acc}"

    def __str__(self) -> str:
        return self.name if self.octave is None else f"{self.name}{self.octave}"

    def __repr__(self) -> str:
        return f"Note('{self}')"

    # --- So sánh ------------------------------------------------------------

    def same_spelling(self, other: "Note") -> bool:
        """Cùng tên (bỏ qua quãng tám). Dùng cho chế độ strict_spelling."""
        return self.letter == other.letter and self.accidental == other.accidental

    def enharmonic_to(self, other: "Note") -> bool:
        """Cùng lớp cao độ (MUS-ACC-003). Dùng cho chế độ pitch_class_only."""
        return self.pitch_class == other.pitch_class

    def with_octave(self, octave: Optional[int]) -> "Note":
        return Note(self.letter, self.accidental, octave)


def parse_note(text: str | Note) -> Note:
    """Đọc 'Eb4', 'F##3', 'C', 'b♭', 'Fx'. Chữ cái viết thường được chấp nhận khi nhập."""
    if isinstance(text, Note):
        return text
    if not isinstance(text, str):
        raise InvalidPitch("Nốt phải là chuỗi", value=repr(text))
    m = _PITCH_RE.match(text)
    if not m:
        raise InvalidPitch(f"Không đọc được tên nốt: {text!r}", value=text)
    letter, acc_token, octave = m.group(1).upper(), m.group(2) or "", m.group(3)
    return Note(letter, _ACCIDENTAL_TOKENS[acc_token], int(octave) if octave is not None else None)


def note_from_midi(midi: int, prefer: str = "sharp") -> Note:
    """Đổi MIDI → tên nốt. CHỈ dùng cho đầu vào không có tên (micro, MIDI keyboard).

    Cao độ không cho biết tên nốt (G#4 và Ab4 đều là 68), nên kết quả phụ thuộc `prefer`
    và phải được chấm ở chế độ pitch_class_only hoặc đặt tên lại theo ngữ cảnh giọng.
    """
    if prefer not in ("sharp", "flat"):
        raise InvalidPitch("prefer phải là 'sharp' hoặc 'flat'", prefer=prefer)
    pc, octave = midi % 12, midi // 12 - 1
    for letter, base in NATURAL_PC.items():
        if base == pc:
            return Note(letter, 0, octave)
    if prefer == "sharp":
        letter = next(l for l, b in NATURAL_PC.items() if b == pc - 1)
        return Note(letter, 1, octave)
    letter = next(l for l, b in NATURAL_PC.items() if b == pc + 1)
    return Note(letter, -1, octave)
