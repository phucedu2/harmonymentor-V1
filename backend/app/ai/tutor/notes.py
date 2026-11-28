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
    rf"(?<![A-Za-z0-9#/])(?P<sym>{CHORD}(?:/{NOTE})?)(?![A-Za-z0-9#])\s*(?:=|:|\(|là|gồm(?: các nốt)?|có các nốt|có nốt)\s*"
    rf"(?P<notes>{NOTE_SEQ})(?![A-Za-z0-9#])")
# "âm giai G major: G A B C D E F#", "âm giai Rê trưởng gồm D E F# ..."
SCALE_WITH_NOTES = re.compile(
    rf"(?:âm giai|gam|scale)\s+(?P<tonic>{NOTE})\s*(?P<kind>major|trưởng|natural minor|thứ tự nhiên|minor|thứ)"
    rf"[^A-G\n]{{0,25}}(?P<notes>{NOTE}(?:{_SEP}{NOTE}){{5,7}})(?![A-Za-z0-9#])", re.IGNORECASE)
# "D–F# là M3", "từ D lên Gb là quãng d4", "A–C = quãng 3 thứ". Chỉ bắt câu khẳng định ngay sau cặp nốt
# ("là", "=", ":"), nên "D–Gb không phải M3" không bị hiểu thành D–Gb = M3. Nốt dưới trước, đi lên.
_IV_QUAL_VI = {"trưởng": "M", "thứ": "m", "đúng": "P", "tăng": "A", "giảm": "d"}
# RS-26: AI hay viết "quãng ba giảm" (số bằng chữ) và "B và F tạo quãng ...". Số bằng chữ được đổi về chữ số.
_NUM_WORDS = {"hai": "2", "ba": "3", "bốn": "4", "tư": "4", "năm": "5", "sáu": "6", "bảy": "7", "tám": "8"}
_NUM = r"(?P<num>[1-8]|hai|ba|bốn|tư|năm|sáu|bảy|tám)"
_IV_TAIL = (rf"(?:(?P<code>[PMmAd][1-8])(?![A-Za-z0-9])|{_NUM}\s*(?P<qual>trưởng|thứ|đúng|tăng|giảm)(?![\wÀ-ỹ]))")
INTERVAL_WITH_NAME = re.compile(
    rf"(?<![A-Za-z0-9#])(?P<lo>{NOTE})\s*(?:–|—|-|→|lên)\s*(?P<hi>{NOTE})(?![A-Za-z0-9#–—-])\s*"
    rf"(?:(?:tạo\s+(?:thành|nên)|tạo|là|=|:)\s*)(?:một\s+)?(?:quãng\s*)?{_IV_TAIL}")
# "B và F tạo quãng ba giảm": thứ tự nốt không rõ, nên đúng nếu khớp một trong hai chiều (xem guardrail).
INTERVAL_PAIR_WITH_NAME = re.compile(
    rf"(?<![A-Za-z0-9#])(?P<lo>{NOTE})\s+(?:và|với)\s+(?P<hi>{NOTE})(?![A-Za-z0-9#])\s*(?:\([^)]*\)\s*)?"
    rf"(?:(?:tạo\s+(?:thành|nên)|tạo|là|=|:)\s*)(?:một\s+)?quãng\s*{_IV_TAIL}")


# Số La Mã: giữ mode; "thứ" không rõ loại cần làm rõ, không mặc định thành trưởng.
ROMAN = r"(?:vii|VII|iii|III|iv|IV|vi|VI|ii|II|v|V|i|I)(?:maj7|M7|ø7|°7|7|°|ø)?"
ROMAN_MODE = r"thứ tự nhiên|thu tu nhien|natural minor|thứ hòa âm|thu hoa am|harmonic minor|thứ giai điệu|thu giai dieu|melodic minor|trưởng|truong|major|thứ|thu|minor"

def roman_mode(text: str | None) -> str:
    value = (text or "major").lower().strip()
    if value in {"major", "trưởng", "truong"}:
        return "major"
    if value in {"natural minor", "thứ tự nhiên", "thu tu nhien"}:
        return "natural_minor"
    return "unspecified_minor" if value in {"minor", "thứ", "thu"} else "unsupported_minor"

_KEY = rf"(?:giọng\s+|giong\s+)?(?P<key>{NOTE})(?![A-Za-z0-9#♯♭])(?:\s*(?P<mode>(?i:{ROMAN_MODE}))(?![\wÀ-ỹ]))?"
ROMAN_IN_KEY_IS_CHORD = re.compile(
    rf"(?<![A-Za-z])(?P<rn>{ROMAN})(?![A-Za-z0-9])\s+(?:trong|của)\s+{_KEY}\s*(?:là|=|:)\s*(?:hợp âm\s+)?"
    rf"(?P<chord>{CHORD})(?![A-Za-z0-9#])")
CHORD_IS_ROMAN_IN_KEY = re.compile(
    rf"(?<![A-Za-z0-9#/])(?P<chord>{CHORD})(?![A-Za-z0-9#])\s*(?:là|=)\s*(?:hợp âm\s+)?(?P<rn>{ROMAN})"
    rf"(?![A-Za-z0-9])\s+(?:trong|của)\s+{_KEY}")


# Prefix format emitted by fact_text: "Trong giọng A thứ tự nhiên, Am là i."
KEY_CHORD_IS_ROMAN = re.compile(
    rf"(?i:trong)\s+{_KEY}\s*[,;:]\s*(?P<chord>{CHORD})(?![A-Za-z0-9#])\s+(?:là|=)\s+"
    rf"(?P<rn>{ROMAN})(?![A-Za-z0-9])")


# Khẳng định bậc bằng số thứ tự hoặc chữ "bậc": "Gm7 là hợp âm thứ ba trong giọng G major",
# "G7 là hợp âm bậc V của C trưởng", "Gm7 là bậc 2 trong F". Phải có giọng thì Engine mới kiểm được.
# "thứ bảy" bị bỏ qua vì dễ lẫn với "hợp âm bảy thứ" (minor seventh); bậc 7 phải viết "bậc bảy" / "bậc 7".
_DEG_WORDS = {"một": 1, "nhất": 1, "hai": 2, "ba": 3, "bốn": 4, "tư": 4, "năm": 5, "sáu": 6, "bảy": 7}
_DEG_ROMAN = {"i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5, "vi": 6, "vii": 7}
_DEG_THU = r"[1-7]|một|nhất|hai|ba|bốn|tư|năm|sáu"
_DEG_BAC = r"[1-7]|một|hai|ba|bốn|tư|năm|sáu|bảy|VII|VI|IV|V|III|II|I|vii|vi|iv|v|iii|ii|i"
CHORD_IS_DEGREE_IN_KEY = re.compile(
    rf"(?<![A-Za-z0-9#/])(?P<chord>{CHORD})(?![A-Za-z0-9#])\s*(?:là|=)\s*(?:một\s+)?(?:hợp âm\s+)?(?:(?:ở|trên)\s+)?"
    rf"(?:bậc\s+(?P<deg_b>{_DEG_BAC})|thứ\s+(?P<deg_t>{_DEG_THU}))(?![\wÀ-ỹ])\s*(?:\([^)]*\)\s*)?"
    rf"(?:trong|của)\s+{_KEY}")
# "Trong giọng G major, ii7 là Am7" (số La Mã trước, hợp âm sau).
KEY_ROMAN_IS_CHORD = re.compile(
    rf"(?i:trong)\s+{_KEY}\s*[,;:]\s*(?P<rn>{ROMAN})(?![A-Za-z0-9])\s+(?:là|=)\s+(?:hợp âm\s+)?"
    rf"(?P<chord>{CHORD})(?![A-Za-z0-9#])")


# "Nó / hợp âm này / hợp âm đó là hợp âm thứ ba trong giọng C": hợp âm được chỉ tới do guardrail tìm trong câu trả lời.
_PRONOUN = r"(?:[Nn]ó|[Hh]ợp âm (?:này|đó|ấy|trên))"
PRONOUN_IS_DEGREE_IN_KEY = re.compile(
    rf"(?<![\wÀ-ỹ])(?P<pron>{_PRONOUN})(?![\wÀ-ỹ])\s*(?:là|=)\s*(?:một\s+)?(?:hợp âm\s+)?(?:(?:ở|trên)\s+)?"
    rf"(?:bậc\s+(?P<deg_b>{_DEG_BAC})|thứ\s+(?P<deg_t>{_DEG_THU}))(?![\wÀ-ỹ])\s*(?:\([^)]*\)\s*)?"
    rf"(?:trong|của)\s+{_KEY}")
PRONOUN_IS_ROMAN_IN_KEY = re.compile(
    rf"(?<![\wÀ-ỹ])(?P<pron>{_PRONOUN})(?![\wÀ-ỹ])\s*(?:là|=)\s*(?:hợp âm\s+)?(?P<rn>{ROMAN})"
    rf"(?![A-Za-z0-9])\s+(?:trong|của)\s+{_KEY}")

# Nốt bass của hợp âm có dấu "/": "C/E ... nốt bass là E", "C/E ... với E ở bass", "G7/B: nốt trầm là B".
BASS_CLAIM = re.compile(
    rf"(?<![A-Za-z0-9#/])(?P<sym>{CHORD}/{NOTE})(?![A-Za-z0-9#])[^.!?\n]{{0,60}}?"
    rf"(?:(?:bass|trầm|thấp nhất|dưới cùng)\s*(?:là|:|=)\s*(?:nốt\s+)?(?P<b1>{NOTE})(?![A-Za-z0-9#])"
    rf"|(?P<b2>{NOTE})(?![A-Za-z0-9#])\s+(?:ở|làm|nằm ở|đặt ở)\s+(?:vị trí\s+)?(?:nốt\s+)?(?:bass|trầm|thấp nhất|dưới cùng))")


def degree_number(match: re.Match) -> int:
    """Số bậc 1–7 từ một kết quả CHORD_IS_DEGREE_IN_KEY."""
    tok = match["deg_b"] or match["deg_t"]
    if tok.isdigit():
        return int(tok)
    return _DEG_WORDS.get(tok.lower()) or _DEG_ROMAN[tok.lower()]


def interval_name(match: re.Match) -> str:
    """Tên quãng dạng mã Engine (M3, d4...) từ một kết quả INTERVAL_WITH_NAME."""
    if match["code"]:
        return match["code"]
    return _IV_QUAL_VI[match["qual"]] + _NUM_WORDS.get(match["num"], match["num"])


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


_SOLF1 = {"đô": "C", "do": "C", "rê": "D", "re": "D", "mi": "E", "fa": "F", "pha": "F", "sol": "G", "son": "G",
          "la": "A", "si": "B"}
_SOLF_ONE = re.compile(r"\b(Đô|Do|Rê|Re|Mi|Fa|Pha|Sol|Son|La|Si)(\s+(?:thăng|giáng))?(?=\s+(?:trưởng|thứ|truong|thu|major|minor|natural minor))",
                       re.IGNORECASE)

def normalize_key_names(text: str) -> str:
    """'Rê trưởng' → 'D trưởng', 'Si giáng thứ' → 'Bb thứ' (một tên nốt đứng trước trưởng/thứ)."""

    def one(m: re.Match) -> str:
        base = _SOLF1[unicodedata.normalize("NFC", m[1]).lower()]
        acc = (m[2] or "").lower()
        return base + ("#" if "thăng" in acc else "b" if "giáng" in acc else "")

    return _SOLF_ONE.sub(one, solfege_to_letters(text))
