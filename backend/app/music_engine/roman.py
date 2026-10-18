"""Số La Mã cho hợp âm thuận giọng, hồ sơ quy ước CONV-ROMAN-CLASSICAL.

Phạm vi theo quyết định:
- QĐ-2.2 = A: MVP chỉ giọng trưởng. Giọng thứ → NOT_SUPPORTED_IN_MVP.
- QĐ-2.3 (khuyến nghị, chờ bạn chốt): chỉ thể gốc. Hợp âm có bass khác nốt gốc → NOT_SUPPORTED_IN_MVP.
- Hồ sơ jazz-pop chưa có nguồn cho cách viết số La Mã → CONVENTION_NOT_VERIFIED.

Claim:
- MUS-ROMAN-001  Chữ hoa = trưởng, chữ thường = thứ, ° = giảm (F tr. 120; OMT Roman Numerals).
- MUS-TRIAD-002  Giọng trưởng: I ii iii IV V vi vii° (F tr. 120; OMT Triads).
- MUS-ROMAN-006  Thêm 7 cho hợp âm bảy; ø = nửa giảm, ° = giảm (OMT Roman Numerals: "V7, ii7, viio7").
- Ký hiệu "M7" cho hợp âm bảy trưởng (IM7, IVM7): CHƯA CÓ NGUỒN đã đọc (Fankhauser Ch. 23 thiếu).
"""

from __future__ import annotations

from dataclasses import dataclass

from .chord import CHORD_TYPES, ChordSymbol, build_chord, parse_chord_symbol
from .errors import ConventionNotVerified, NotDiatonic, NotSupportedInMvp
from .interval import transpose
from .pitch import Note, parse_note
from .scale import build_scale

CONVENTION_ID = "CONV-ROMAN-CLASSICAL"
NUMERALS = ("I", "II", "III", "IV", "V", "VI", "VII")
_LOWER_TYPES = {"min", "dim", "m7", "m7b5", "dim7"}
_SUFFIX = {"maj": "", "min": "", "dim": "°", "aug": "+", "7": "7", "maj7": "M7", "m7": "7",
           "m7b5": "ø7", "dim7": "°7"}
# Hậu tố có trong nguồn đã đọc. "M7" chưa có → kết quả dùng nó bị gắn convention_verified=False.
_VERIFIED_SUFFIXES = {"", "°", "+", "7", "ø7", "°7"}


@dataclass(frozen=True)
class RomanNumeral:
    numeral: str          # ví dụ "ii7"
    degree: int           # 1..7
    chord: ChordSymbol
    key: str              # ví dụ "C"
    convention_id: str = CONVENTION_ID
    convention_verified: bool = True


def _guard(mode: str, profile: str) -> None:
    if profile != "classical":
        raise ConventionNotVerified(
            "Hồ sơ số La Mã jazz-pop chưa có nguồn đã xác minh", profile=profile)
    if mode != "major":
        raise NotSupportedInMvp("MVP chỉ dạy số La Mã trong giọng trưởng (QĐ-2.2)", mode=mode)


def _numeral_for(degree: int, chord_type: str) -> str:
    base = NUMERALS[degree - 1]
    if chord_type in _LOWER_TYPES:
        base = base.lower()
    return base + _SUFFIX[chord_type]


def diatonic_chords(key: str | Note, sevenths: bool = False, mode: str = "major",
                    profile: str = "classical") -> list[RomanNumeral]:
    """Bảy hợp âm thuận giọng xếp chồng quãng 3 trên mỗi bậc của âm giai trưởng."""
    _guard(mode, profile)
    tonic = parse_note(key).with_octave(None)
    scale = build_scale(tonic, "major")
    result = []
    for degree, root in enumerate(scale, start=1):
        size = 4 if sevenths else 3
        tones = [scale[(degree - 1 + 2 * k) % 7] for k in range(size)]
        ct = _type_from_tones(root, tones)
        numeral = _numeral_for(degree, ct)
        result.append(RomanNumeral(numeral, degree, build_chord(root, ct), tonic.name,
                                   convention_verified=_SUFFIX[ct] in _VERIFIED_SUFFIXES))
    return result


def _type_from_tones(root: Note, tones: list[Note]) -> str:
    for ct in CHORD_TYPES.values():
        if len(ct.intervals) != len(tones):
            continue
        spelled = [transpose(root, iv) for iv in ct.intervals]
        if all(a.same_spelling(b) for a, b in zip(spelled, tones)):
            return ct.id
    raise NotDiatonic("Không xác định được loại hợp âm thuận giọng", root=root.name)


def roman_numeral(key: str | Note, chord: str | ChordSymbol, mode: str = "major",
                  profile: str = "classical") -> RomanNumeral:
    """Bài roman_numeral của SRS: {key: "C", chord: "Dm7"} → "ii7"."""
    _guard(mode, profile)
    cs = parse_chord_symbol(chord) if isinstance(chord, str) else chord
    if cs.bass is not None and not cs.bass.same_spelling(cs.root):
        raise NotSupportedInMvp("MVP chỉ hỏi số La Mã ở thể gốc (QĐ-2.3)", chord=cs.symbol)
    tonic = parse_note(key).with_octave(None)
    sevenths = len(cs.type.intervals) == 4
    for rn in diatonic_chords(tonic, sevenths=sevenths):
        if rn.chord.root.same_spelling(cs.root):
            if rn.chord.type.id != cs.type.id:
                raise NotDiatonic(
                    f"{cs.symbol} không thuộc giọng {tonic.name} trưởng; hợp âm thuận giọng trên bậc "
                    f"{rn.degree} là {rn.chord.symbol}",
                    chord=cs.symbol, key=tonic.name, expected=rn.chord.symbol)
            return rn
    raise NotDiatonic(f"Nốt gốc {cs.root.name} không thuộc giọng {tonic.name} trưởng",
                      chord=cs.symbol, key=tonic.name)
