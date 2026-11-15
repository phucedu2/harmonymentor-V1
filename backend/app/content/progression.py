"""Đổi vòng hợp âm viết bằng số La Mã sang ký hiệu hợp âm của một giọng, hoàn toàn bằng Music Engine.

Vì sao có file này: ví dụ trong bài từng ghi cứng "Cmaj7 -> Dm7 -> G7", nên bài nào cũng chỉ thấy giọng C.
Nội dung giờ khai báo `numerals`; frontend hỏi API này để lấy ký hiệu theo giọng người học chọn (nguyên tắc 1:
frontend không tự tính nhạc lý)."""

from __future__ import annotations

from ..music_engine import build_chord, parse_note, transpose
from ..music_engine.roman import diatonic_chords

# 12 giọng trưởng thường dùng (tên chính tả quen thuộc; Gb thay F#).
KEYS = ("C", "G", "D", "A", "E", "B", "F", "Bb", "Eb", "Ab", "Db", "Gb")

# Số La Mã ngoài giọng, kiểu pop: mượn từ giọng thứ hoặc bậc hạ.
_BORROWED = {"iv": ("P4", "min"), "bVII": ("m7", "maj"), "bVI": ("m6", "maj"), "bIII": ("m3", "maj")}


class UnknownNumeral(ValueError):
    pass


def _canon(numeral: str) -> str:
    # Engine ghi "M7", bài học viết "maj7"; "Ø7"/"o7" không dùng trong nội dung.
    return numeral.replace("maj7", "M7")


def _diatonic(key: str, numeral: str):
    wanted = _canon(numeral)
    for sevenths in (False, True):
        for rn in diatonic_chords(key, sevenths=sevenths):
            if rn.numeral == wanted:
                return rn.chord
    return None


def resolve_numeral(key: str, numeral: str) -> str:
    if key not in KEYS:
        raise UnknownNumeral(f"Giọng {key!r} chưa hỗ trợ")
    numeral = numeral.strip()
    if "/" in numeral:
        # V7/ii, V/V: dominant của một bậc khác (secondary dominant).
        applied, target = numeral.split("/", 1)
        if applied not in ("V", "V7"):
            raise UnknownNumeral(f"Chưa hỗ trợ {numeral!r}")
        target_chord = _diatonic(key, target)
        if target_chord is None:
            raise UnknownNumeral(f"Không có bậc {target!r} trong giọng {key}")
        return build_chord(transpose(target_chord.root, "P5"), "7" if applied == "V7" else "maj").symbol
    chord = _diatonic(key, numeral)
    if chord is not None:
        return chord.symbol
    if numeral in _BORROWED:
        interval, kind = _BORROWED[numeral]
        return build_chord(transpose(parse_note(key).with_octave(None), interval), kind).symbol
    raise UnknownNumeral(f"Không hiểu số La Mã {numeral!r}")


def resolve_progression(key: str, numerals: list[str]) -> list[str]:
    return [resolve_numeral(key, n) for n in numerals]
