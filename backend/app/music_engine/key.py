"""Giọng và hóa biểu.

Claim:
- MUS-KEY-001  Hóa biểu = dấu hóa của giọng trưởng hoặc thứ tự nhiên (F tr. 34; OMT Minor Scales).
- MUS-KEY-002  Thứ tự dấu thăng F C G D A E B, dấu giáng B E A D G C F (F tr. 35; OMT Major Scales).
- MUS-KEY-003  Dấu thăng cuối thấp hơn chủ âm nửa cung; dấu giáng áp cuối là chủ âm;
               Đô trưởng và Fa trưởng phải học thuộc (F tr. 35; OMT Major Scales).
- MUS-KEY-004  Giọng thứ tương quan thấp hơn quãng 3 thứ (F tr. 36; OMT: "three half steps below").
- MUS-KEY-005  Tối đa 7 dấu hóa; vượt quá thì dùng giọng đồng âm (F tr. 36; OMT: C♭, C♯ trưởng).
"""

from __future__ import annotations

from dataclasses import dataclass

from .errors import UnsupportedKey
from .interval import transpose
from .pitch import Note, parse_note
from .scale import build_scale

ORDER_OF_SHARPS = ("F", "C", "G", "D", "A", "E", "B")
ORDER_OF_FLATS = ("B", "E", "A", "D", "G", "C", "F")
MODES = ("major", "minor")


@dataclass(frozen=True)
class KeySignature:
    tonic: Note
    mode: str              # "major" | "minor"
    kind: str              # "sharp" | "flat" | "none"
    accidentals: tuple[Note, ...]  # theo thứ tự viết trên khuông

    @property
    def count(self) -> int:
        return len(self.accidentals)

    @property
    def label(self) -> str:
        """Nhãn theo quy ước F tr. 120 / tr. 36: giọng thứ viết chữ thường ('c:'), trưởng chữ hoa ('C:')."""
        name = self.tonic.name
        return name if self.mode == "major" else name[0].lower() + name[1:]


def _check_mode(mode: str) -> str:
    if mode not in MODES:
        raise UnsupportedKey(f"Mode phải là 'major' hoặc 'minor', nhận {mode!r}", mode=mode)
    return mode


def key_signature(tonic: str | Note, mode: str = "major") -> KeySignature:
    """Hóa biểu của một giọng. Giọng thứ dùng thứ tự nhiên (MUS-KEY-001)."""
    _check_mode(mode)
    root = parse_note(tonic).with_octave(None)
    scale = build_scale(root, "major" if mode == "major" else "natural_minor")
    altered = [n for n in scale if n.accidental != 0]
    if any(abs(n.accidental) > 1 for n in altered) or (
        any(n.accidental > 0 for n in altered) and any(n.accidental < 0 for n in altered)
    ):
        raise UnsupportedKey(
            f"Giọng {root.name} {mode} cần hơn 7 dấu hóa; dùng giọng đồng âm",
            tonic=root.name,
            mode=mode,
            suggestion=_enharmonic_suggestion(root, mode),
        )
    if not altered:
        return KeySignature(root, mode, "none", ())
    kind = "sharp" if altered[0].accidental > 0 else "flat"
    order = ORDER_OF_SHARPS if kind == "sharp" else ORDER_OF_FLATS
    letters = {n.letter for n in altered}
    acc = 1 if kind == "sharp" else -1
    ordered = tuple(Note(l, acc) for l in order if l in letters)
    # Hóa biểu luôn là tiền tố của thứ tự dấu (F, FC, FCG...). Nếu không, có lỗi trong Engine.
    assert [n.letter for n in ordered] == list(order[: len(ordered)]), "hóa biểu sai thứ tự"
    return KeySignature(root, mode, kind, ordered)


def _enharmonic_suggestion(root: Note, mode: str) -> str | None:
    for candidate_acc in (-1, 0, 1):
        for letter in "CDEFGAB":
            try:
                cand = Note(letter, candidate_acc)
            except Exception:
                continue
            if cand.pitch_class == root.pitch_class and not cand.same_spelling(root):
                try:
                    key_signature(cand, mode)
                    return f"{cand.name} {mode}"
                except UnsupportedKey:
                    continue
    return None


def key_from_signature(count: int, kind: str, mode: str = "major") -> Note:
    """Từ số dấu thăng/giáng → chủ âm. Mỗi dấu thăng: lên quãng 5; mỗi dấu giáng: lên quãng 4."""
    _check_mode(mode)
    if not 0 <= count <= 7:
        raise UnsupportedKey("Hóa biểu có từ 0 tới 7 dấu (MUS-KEY-005)", count=count)
    if kind not in ("sharp", "flat") and count:
        raise UnsupportedKey("kind phải là 'sharp' hoặc 'flat'", kind=kind)
    tonic = Note("C")
    for _ in range(count):
        tonic = transpose(tonic, "P5" if kind == "sharp" else "P4")
    return relative_minor(tonic) if mode == "minor" else tonic


def relative_minor(major_tonic: str | Note) -> Note:
    """Thấp hơn quãng 3 thứ = cao hơn quãng 6 trưởng (MUS-KEY-004)."""
    return transpose(parse_note(major_tonic).with_octave(None), "M6")


def relative_major(minor_tonic: str | Note) -> Note:
    return transpose(parse_note(minor_tonic).with_octave(None), "m3")


def all_supported_keys(mode: str = "major") -> list[KeySignature]:
    """15 giọng trưởng hoặc 15 giọng thứ (0–7 thăng, 1–7 giáng)."""
    keys = [key_signature(key_from_signature(0, "sharp", mode), mode)]
    for kind in ("sharp", "flat"):
        for count in range(1, 8):
            keys.append(key_signature(key_from_signature(count, kind, mode), mode))
    return keys
