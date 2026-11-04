"""Nhận diện ký hiệu hợp âm, tên nốt và tên nốt tiếng Việt trong văn bản (kế hoạch AI Tutor 02/11: chuẩn hóa
tên nốt tiếng Việt). Chỉ nhận diện; mọi phán đoán đúng/sai do Music Engine làm."""

from __future__ import annotations

import re
import unicodedata

# Đô Rê Mi Fa Sol La Si (viết hoa) + "thăng"/"giáng". Chỉ dùng khi có từ 3 tên liên tiếp, vì "La", "Mi"
# đứng một mình dễ là chữ thường trong câu.
_SOLFEGE = {"đô": "C", "do": "C", "rê": "D", "re": "D", "mi": "E", "fa": "F", "sol": "G", "son": "G",
            "la": "A", "si": "B"}
_SOLF_TOKEN = r"(?:Đô|Do|Rê|Re|Mi|Fa|Sol|Son|La|Si)(?:\s+(?:thăng|giáng)(?:\s+kép)?)?"
_SOLF_SEQ = re.compile(rf"\b{_SOLF_TOKEN}(?:\s*[,–\-]?\s*{_SOLF_TOKEN}){{2,}}\b")

NOTE = r"[A-G](?:##|#|bb|b|x|♯|♭)?"
# Hậu tố theo Music Engine (04 Bảng 16) và các cách viết hay gặp. Thứ tự dài trước ngắn.
_QUAL = r"(?:maj7|M7|m7b5|ø7|ø|dim7|°7|dim|°|aug|\+|m7|min7|mM7|m|min|7|6|9|sus2|sus4)?"
CHORD = rf"{NOTE}{_QUAL}"
_SEP = r"\s*(?:[,–\-]|\s)\s*"
NOTE_SEQ = rf"{NOTE}(?:{_SEP}{NOTE}){{2,}}"

# "G7 = G B D F", "Cmaj7 gồm C, E, G, B", "C7 (C – E – G – Bb)", "Cmaj7: C E G B"
CHORD_WITH_NOTES = re.compile(
    rf"(?<![A-Za-z0-9#])(?P<sym>{CHORD})(?![A-Za-z0-9#])\s*(?:=|:|\(|là|gồm(?: các nốt)?|có các nốt|có nốt)\s*"
    rf"(?P<notes>{NOTE_SEQ})(?![A-Za-z0-9#])")
# "âm giai G major: G A B C D E F#", "âm giai Rê trưởng gồm D E F# ..."
SCALE_WITH_NOTES = re.compile(
    rf"(?:âm giai|gam|scale)\s+(?P<tonic>{NOTE})\s*(?P<kind>major|trưởng|natural minor|thứ tự nhiên|minor|thứ)"
    rf"[^A-G\n]{{0,25}}(?P<notes>{NOTE}(?:{_SEP}{NOTE}){{5,7}})(?![A-Za-z0-9#])", re.IGNORECASE)
SYMBOL_IN_QUESTION = re.compile(rf"(?<![A-Za-z0-9#])(?P<sym>{NOTE}(?:maj7|M7|m7b5|ø7|dim7|dim|aug|m7|m|7))"
                                rf"(?![A-Za-z0-9#])")


def norm_accidentals(text: str) -> str:
    return text.replace("♯", "#").replace("♭", "b").replace("x", "##")


def split_notes(seq: str) -> list[str]:
    return [norm_accidentals(n) for n in re.findall(NOTE, seq)]


def solfege_to_letters(text: str) -> str:
    """'Đô, Mi, Sol, Si giáng' → 'C, E, G, Bb' (chỉ với dãy từ 3 tên)."""

    def one(tok: str) -> str:
        parts = tok.split()
        base = _SOLFEGE[unicodedata.normalize("NFC", parts[0]).lower()]
        acc = ""
        if len(parts) > 1:
            acc = "#" if parts[1] == "thăng" else "b"
            if len(parts) > 2:
                acc *= 2
        return base + acc

    def repl(m: re.Match) -> str:
        toks = re.findall(_SOLF_TOKEN, m.group(0))
        return " ".join(one(t) for t in toks)

    return _SOLF_SEQ.sub(repl, unicodedata.normalize("NFC", text))
