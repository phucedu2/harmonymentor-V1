"""Hợp âm: bảng loại hợp âm, đọc ký hiệu, viết tên nốt, nhận diện.

Bảng loại hợp âm là dữ liệu (báo cáo v1 §6.3): mỗi loại có quãng, bí danh và claim.
Tên nốt luôn suy từ quãng tính từ nốt gốc (SRS 4.4.1), nên Bm7b5 = B D F A, Ebm7b5 = Eb Gb Bbb Db.

Claim:
- MUS-TRIAD-001  Bốn loại hợp âm ba theo quãng 3 và quãng 5 từ nốt gốc (OMT Triads). 1 nguồn.
- MUS-7TH-001    Hợp âm bảy át = ba trưởng + 7 thứ (F tr. 150; OMT Seventh Chords). 2 nguồn.
- MUS-7TH-004    maj7, m7, nửa giảm, giảm 7 (OMT Seventh Chords). 1 nguồn.
- MUS-TRIAD-005  Thể đảo do nốt bass quyết định (F tr. 157).
- MUS-CHSYM-005  Nốt bass trong hợp âm gạch chéo không cần thuộc hợp âm (OMT Chord Symbols).
- sus2, sus4     CHƯA CÓ NGUỒN. Có trong SRS nên vẫn dựng, nhưng gắn `verified=False`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

from .errors import InvalidChordSymbol, NoMatch, UnknownQuality
from .interval import interval_between, transpose
from .pitch import Note, parse_note


@dataclass(frozen=True)
class ChordType:
    id: str
    intervals: tuple[str, ...]
    display: str                 # hậu tố hiển thị chuẩn (theo SRS)
    claim_ids: tuple[str, ...]
    verified: bool               # có ít nhất 1 nguồn đã đọc


CHORD_TYPES: dict[str, ChordType] = {t.id: t for t in [
    ChordType("maj", ("P1", "M3", "P5"), "", ("MUS-TRIAD-001",), True),
    ChordType("min", ("P1", "m3", "P5"), "m", ("MUS-TRIAD-001",), True),
    ChordType("dim", ("P1", "m3", "d5"), "dim", ("MUS-TRIAD-001",), True),
    ChordType("aug", ("P1", "M3", "A5"), "aug", ("MUS-TRIAD-001",), True),
    ChordType("7", ("P1", "M3", "P5", "m7"), "7", ("MUS-7TH-001",), True),
    ChordType("maj7", ("P1", "M3", "P5", "M7"), "maj7", ("MUS-7TH-004",), True),
    ChordType("m7", ("P1", "m3", "P5", "m7"), "m7", ("MUS-7TH-004",), True),
    ChordType("m7b5", ("P1", "m3", "d5", "m7"), "m7b5", ("MUS-7TH-004",), True),
    ChordType("dim7", ("P1", "m3", "d5", "d7"), "dim7", ("MUS-7TH-004",), True),
    ChordType("sus2", ("P1", "M2", "P5"), "sus2", (), False),
    ChordType("sus4", ("P1", "P4", "P5"), "sus4", (), False),
]}

# --- Bí danh ký hiệu ------------------------------------------------------------
# Hồ sơ "srs": đúng danh sách SRS 4.4.1 (maj7 = M7 = Δ7; m7b5 = ø7; min = m = -; dim = °),
# áp dụng cả trong hậu tố dài (m7 = min7 = -7; dim7 = °7).
SRS_ALIASES: dict[str, str] = {
    "": "maj", "maj": "maj",
    "m": "min", "min": "min", "-": "min",
    "dim": "dim", "°": "dim",
    "aug": "aug",
    "7": "7",
    "maj7": "maj7", "M7": "maj7", "Δ7": "maj7",
    "m7": "m7", "min7": "m7", "-7": "m7",
    "m7b5": "m7b5", "min7b5": "m7b5", "-7b5": "m7b5", "ø7": "m7b5",
    "dim7": "dim7", "°7": "dim7",
    "sus2": "sus2", "sus4": "sus4",
}
# Hồ sơ "extended" (QĐ-2.11, đang chờ duyệt): thêm cách viết trong OMT (Chord Symbols, Triads,
# Seventh Chords) và Fankhauser tr. 467. Chỉ dùng khi NHẬP; hiển thị vẫn dùng dạng chuẩn SRS.
EXTENDED_ALIASES: dict[str, str] = {
    **SRS_ALIASES,
    "mi": "min",
    "o": "dim", "m(b5)": "dim", "m(-5)": "dim",  # OMT: Cm(♭5) là hợp âm BA giảm
    "+": "aug",
    "ma7": "maj7", "Δ": "maj7", "∆7": "maj7", "∆": "maj7",
    "mi7": "m7",
    "mi7b5": "m7b5", "m7(b5)": "m7b5", "ø": "m7b5", "∅7": "m7b5", "∅": "m7b5",
    "o7": "dim7",
}
ALIAS_PROFILES = {"srs": SRS_ALIASES, "extended": EXTENDED_ALIASES}
DEFAULT_ALIAS_PROFILE = "extended"  # theo khuyến nghị QĐ-2.11; đổi thành "srs" nếu bạn chọn Không

_SYMBOL_RE = re.compile(r"^\s*([A-G])(#|b|♯|♭)?([^/]*?)(?:/([A-G])(#|b|♯|♭)?)?\s*$")


def _normalize_quality(q: str) -> str:
    return q.replace("♭", "b").replace("♯", "#").replace(" ", "")


@dataclass(frozen=True)
class ChordSymbol:
    root: Note
    type: ChordType
    bass: Optional[Note] = None

    @property
    def notes(self) -> list[Note]:
        """Các nốt của hợp âm ở thể gốc, viết tên theo quãng từ nốt gốc."""
        return [transpose(self.root, iv) for iv in self.type.intervals]

    @property
    def bass_in_chord(self) -> bool:
        return self.bass is None or any(n.same_spelling(self.bass) for n in self.notes)

    @property
    def inversion(self) -> Optional[int]:
        """0 = thể gốc, 1 = bass là nốt 3, 2 = nốt 5, 3 = nốt 7; None nếu bass ngoài hợp âm."""
        if self.bass is None:
            return 0
        for i, n in enumerate(self.notes):
            if n.same_spelling(self.bass):
                return i
        return None

    @property
    def symbol(self) -> str:
        s = f"{self.root.name}{self.type.display}"
        return f"{s}/{self.bass.name}" if self.bass is not None else s

    def __str__(self) -> str:
        return self.symbol


def parse_chord_symbol(text: str, alias_profile: str = DEFAULT_ALIAS_PROFILE) -> ChordSymbol:
    """Đọc '<root><quality>[/<bass>]'. Không khớp bảng → UNKNOWN_QUALITY (không đoán)."""
    if alias_profile not in ALIAS_PROFILES:
        raise InvalidChordSymbol("Hồ sơ bí danh không tồn tại", alias_profile=alias_profile)
    m = _SYMBOL_RE.match(text or "")
    if not m:
        raise InvalidChordSymbol(f"Không đọc được ký hiệu hợp âm: {text!r}", value=text)
    root = parse_note(m.group(1) + (m.group(2) or ""))
    quality = _normalize_quality(m.group(3))
    aliases = ALIAS_PROFILES[alias_profile]
    if quality not in aliases:
        raise UnknownQuality(
            f"Không nhận ra loại hợp âm {quality!r} trong {text!r}",
            value=text, quality=quality, alias_profile=alias_profile,
        )
    bass = parse_note(m.group(4) + (m.group(5) or "")) if m.group(4) else None
    return ChordSymbol(root, CHORD_TYPES[aliases[quality]], bass)


def chord_tones(symbol: str, alias_profile: str = DEFAULT_ALIAS_PROFILE) -> list[Note]:
    """Công cụ get_chord_tones (SRS FR-AI-13): 'Ebm7b5' → Eb Gb Bbb Db."""
    return parse_chord_symbol(symbol, alias_profile).notes


def build_chord(root: str | Note, chord_type: str) -> ChordSymbol:
    if chord_type not in CHORD_TYPES:
        raise UnknownQuality(f"Loại hợp âm không hỗ trợ: {chord_type!r}", supported=list(CHORD_TYPES))
    return ChordSymbol(parse_note(root).with_octave(None), CHORD_TYPES[chord_type])


@dataclass
class ChordMatch:
    chord: ChordSymbol
    inversion: Optional[int]
    spelled_exactly: bool  # False = chỉ khớp lớp cao độ (sai tên nốt)
    notes_matched: list[str] = field(default_factory=list)


def identify_chord(notes: list[str | Note], bass: str | Note | None = None,
                   match_spelling: bool = True) -> list[ChordMatch]:
    """Nhận diện tập nốt. Trả DANH SÁCH mọi cách gọi tên (báo cáo v1 §6.2), vì có tập nốt
    có nhiều tên (ví dụ Am7 và C6 khi có thêm loại 6; hợp âm tăng, giảm 7 đối xứng).

    - `match_spelling=True`: tên nốt phải khớp chính xác (strict_spelling).
    - `match_spelling=False`: chỉ so lớp cao độ (pitch_class_only); nốt gốc vẫn thử theo tên nhập.
    - `bass`: nốt thấp nhất; nếu không cho, lấy nốt đầu tiên trong danh sách.
    """
    parsed = [parse_note(n).with_octave(None) for n in notes]
    if not parsed:
        raise NoMatch("Danh sách nốt rỗng")
    bass_note = parse_note(bass).with_octave(None) if bass is not None else parsed[0]

    def key(n: Note):
        return (n.letter, n.accidental) if match_spelling else n.pitch_class

    given = {key(n) for n in parsed}
    candidates_roots = []
    for n in parsed:
        if not any(n.same_spelling(r) for r in candidates_roots):
            candidates_roots.append(n)

    matches: list[ChordMatch] = []
    for root in candidates_roots:
        for ct in CHORD_TYPES.values():
            try:
                tones = [transpose(root, iv) for iv in ct.intervals]
            except Exception:
                continue  # cần dấu hóa vượt ±2
            if {key(t) for t in tones} != given:
                continue
            exact = {(t.letter, t.accidental) for t in tones} == {(n.letter, n.accidental) for n in parsed}
            inv = None
            for i, t in enumerate(tones):
                if key(t) == key(bass_note):
                    inv = i
                    break
            chord = ChordSymbol(root, ct, None if inv == 0 else bass_note)
            matches.append(ChordMatch(chord, inv, exact, [str(t) for t in tones]))
    if not matches:
        raise NoMatch("Tập nốt không khớp loại hợp âm nào trong bảng",
                      notes=[str(n) for n in parsed])
    # Ưu tiên: bass là nốt gốc, rồi khớp tên chính xác, rồi hợp âm đã có nguồn.
    matches.sort(key=lambda m: (m.inversion != 0, not m.spelled_exactly, not m.chord.type.verified))
    return matches


def chord_member(chord: ChordSymbol, note: str | Note) -> Optional[str]:
    """Vai trò của một nốt trong hợp âm: 'root', 'third', 'fifth', 'seventh', 'second', 'fourth'."""
    n = parse_note(note).with_octave(None)
    for t in chord.notes:
        if t.same_spelling(n):
            num = interval_between(chord.root, t).number
            return {1: "root", 2: "second", 3: "third", 4: "fourth", 5: "fifth", 7: "seventh"}[num]
    return None
