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
# "D–F# là M3", "từ D lên Gb là quãng d4", "A–C = quãng 3 thứ". Chỉ bắt câu khẳng định ngay sau cặp nốt
# ("là", "=", ":"), nên "D–Gb không phải M3" không bị hiểu thành D–Gb = M3. Nốt dưới trước, đi lên.
_IV_QUAL_VI = {"trưởng": "M", "thứ": "m", "đúng": "P", "tăng": "A", "giảm": "d"}
INTERVAL_WITH_NAME = re.compile(
    rf"(?<![A-Za-z0-9#])(?P<lo>{NOTE})\s*(?:–|—|-|→|lên)\s*(?P<hi>{NOTE})(?![A-Za-z0-9#–—-])\s*"
    rf"(?:là|=|:)\s*(?:một\s+)?(?:quãng\s*)?"
    rf"(?:(?P<code>[PMmAd][1-8])(?![A-Za-z0-9])|(?P<num>[1-8])\s*(?P<qual>trưởng|thứ|đúng|tăng|giảm))")


# "V7 trong G trưởng là D7", "V7 của G là G7", "Am7 là vi7 trong C trưởng". Chỉ giọng trưởng: giọng thứ
# ("trong A thứ", "Am") bị bỏ qua vì Engine MVP chỉ đặt số La Mã cho giọng trưởng.
ROMAN = r"(?:vii|VII|iii|III|iv|IV|vi|VI|ii|II|v|V|i|I)(?:maj7|M7|ø7|°7|7|°|ø)?"
_KEY = rf"(?:giọng\s+)?(?P<key>{NOTE})(?![A-Za-z0-9#♯♭])(?!\s*(?:thứ|minor))(?:\s*(?:trưởng|major))?"
ROMAN_IN_KEY_IS_CHORD = re.compile(
    rf"(?<![A-Za-z])(?P<rn>{ROMAN})(?![A-Za-z0-9])\s+(?:trong|của)\s+{_KEY}\s*(?:là|=|:)\s*(?:hợp âm\s+)?"
    rf"(?P<chord>{CHORD})(?![A-Za-z0-9#])")
CHORD_IS_ROMAN_IN_KEY = re.compile(
    rf"(?<![A-Za-z0-9#])(?P<chord>{CHORD})(?![A-Za-z0-9#])\s*(?:là|=)\s*(?:hợp âm\s+)?(?P<rn>{ROMAN})"
    rf"(?![A-Za-z0-9])\s+(?:trong|của)\s+{_KEY}")


def interval_name(match: re.Match) -> str:
    """Tên quãng dạng mã Engine (M3, d4...) từ một kết quả INTERVAL_WITH_NAME."""
    if match["code"]:
        return match["code"]
    return _IV_QUAL_VI[match["qual"]] + match["num"]


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
