"""So khớp đáp án gõ chữ có tính chất ký hiệu nhạc (RS-01, RS-02).

Vì sao có file này: bộ chấm cũ hạ chữ hoa/thường rồi so chuỗi, nên `GM7` (G trưởng bảy) bị chấm giống `Gm7`,
`V7/II` giống `V7/ii`, `FM` giống `Fm`; ngược lại `E 7`, `F thứ`, `Mi 7`, `G, B, F` bị chấm sai dù đúng nhạc lý.
Ở đây ký hiệu được đọc thành dạng chuẩn rồi mới so, và chỉ bỏ qua phần không mang nghĩa (khoảng trắng, dấu nối,
chữ hoa/thường của TÊN nốt). Chữ hoa/thường của PHẨM CHẤT (M và m) và của số La Mã vẫn được giữ.

Không tính nhạc lý: không suy luận nốt của hợp âm, không đổi đồng âm (A# khác Bb). Việc dựng/kiểm nốt vẫn do
Music Engine làm ở các câu `music_engine`.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

_SOLFEGE = {"do": "C", "re": "D", "mi": "E", "fa": "F", "son": "G", "sol": "G", "la": "A", "si": "B"}
_ACCIDENTAL_WORDS = {"thang": "#", "giang": "b"}

# Phẩm chất hợp âm, đã bỏ khoảng trắng. Khóa so theo chữ thường, trừ "M" đơn lẻ (xử lý riêng ở _quality).
_QUALITY = {
    "": "maj", "maj": "maj", "major": "maj", "truong": "maj",
    "m": "min", "min": "min", "minor": "min", "-": "min", "mi": "min", "thu": "min",
    "7": "7", "dom7": "7",
    "maj7": "maj7", "major7": "maj7", "m7": "min7", "min7": "min7", "mi7": "min7", "minor7": "min7", "-7": "min7",
    "dim": "dim", "o": "dim", "dim7": "dim7", "o7": "dim7",
    "m7b5": "m7b5", "min7b5": "m7b5", "ø": "m7b5", "ø7": "m7b5", "hdim": "m7b5", "hdim7": "m7b5",
    "aug": "aug", "+": "aug", "sus4": "sus4", "sus2": "sus2", "sus": "sus4",
    "6": "6", "m6": "min6", "min6": "min6", "9": "9", "maj9": "maj9", "m9": "min9", "min9": "min9",
    "add9": "add9", "11": "11", "13": "13", "m11": "min11", "m13": "min13",
}

# Mảnh phẩm chất đứng rời sau tên nốt: "E 7", "F thứ", "F minor", "La giáng" (giáng/thăng xử lý riêng).
_QUALITY_FRAGMENT = re.compile(r"^(?:\d+|m|M|min|maj|minor|major|dim|aug|sus\d?|thứ|thu|trưởng|truong|m7|M7|maj7|min7|dim7)$")

_ROMAN = re.compile(r"^([b#]?)(VII|VI|IV|V|III|II|I|vii|vi|iv|v|iii|ii|i)(.*)$")
_ROMAN_SUFFIX = {"": "", "7": "7", "maj7": "maj7", "M7": "maj7", "ø": "ø", "ø7": "ø", "o": "o", "°": "o", "o7": "o7",
                 "°7": "o7", "6": "6", "65": "65", "43": "43", "42": "42", "64": "64", "9": "9"}


def strip_accents(text: str) -> str:
    return "".join(ch for ch in unicodedata.normalize("NFD", text) if unicodedata.category(ch) != "Mn").replace("đ", "d").replace("Đ", "D")


def _prepare(text: Any) -> str:
    text = unicodedata.normalize("NFC", str(text)).strip()
    text = text.replace("♭", "b").replace("♯", "#").replace("△", "maj").replace("Δ", "maj").replace("°", "o")
    text = text.replace("–", "-").replace("—", "-").replace("−", "-")
    text = re.sub(r"\([^)]*\)", " ", text)           # chú thích kèm theo: "E7 (E-G#-B-D)"
    text = re.sub(r"\s*/\s*", "/", text)             # "V7 / ii" -> "V7/ii"
    text = re.sub(r"\s+(?:của|cua)\s+", "/", text, flags=re.IGNORECASE)   # "V7 của ii" -> "V7/ii"
    return text


_SEP = re.compile(r"\s+(?:và|va|and|với|voi|with)\s+|\s*(?:->|=>|→|⇒|>|[,;+.\-\s])\s*", re.IGNORECASE)


def _raw_tokens(text: Any) -> list[str]:
    return [t for t in _SEP.split(_prepare(text)) if t]


def _root(token: str) -> tuple[str, str] | None:
    """Tách tên nốt đầu token: (chữ cái hoa + dấu hóa, phần còn lại). Hỗ trợ Đô–Rê–Mi và chữ cái."""
    folded = strip_accents(token).casefold()
    for name in ("sol", "son", "do", "re", "mi", "fa", "la", "si"):
        if folded.startswith(name) and len(token) >= len(name):
            # "mi" cũng có thể là phẩm chất "mi" (min) sau chữ cái, nhưng ở đầu token nó là tên nốt.
            rest = token[len(name):]
            letter = _SOLFEGE[name]
            acc = ""
            if rest[:1] in ("#", "b"):
                acc, rest = rest[0], rest[1:]
            return letter + acc, rest
    if token and token[0] in "ABCDEFGabcdefg":
        letter, rest = token[0].upper(), token[1:]
        acc = ""
        if rest[:1] in ("#", "b") and not (rest[:1] == "b" and rest[1:2].isdigit() and False):
            acc, rest = rest[0], rest[1:]
        return letter + acc, rest
    return None


def _quality(rest: str) -> str | None:
    rest = rest.strip()
    if rest == "M":
        return "maj"
    if len(rest) > 1 and rest[0] == "M" and rest[1:].isdigit():          # "M7", "M9": M hoa là trưởng
        return {"7": "maj7", "9": "maj9"}.get(rest[1:])
    return _QUALITY.get(strip_accents(rest).casefold())


def _chord(token: str) -> str | None:
    parts = _root(token)
    if not parts:
        return None
    root, rest = parts
    quality = _quality(rest)
    return f"{root}:{quality}" if quality else None


def _roman(token: str) -> str | None:
    match = _ROMAN.match(token)
    if not match:
        return None
    acc, numeral, tail = match.groups()
    target = ""
    if "/" in tail:
        tail, target = tail.split("/", 1)
        sub = _ROMAN.match(target)
        if not sub or sub.group(3):
            return None
        target = "/" + sub.group(1) + sub.group(2)
    suffix = _ROMAN_SUFFIX.get(tail)
    if suffix is None:
        return None
    # V/ii và V7/ii cùng là át phụ của ii; cách viết ngắn không ghi 7 vẫn được nhận.
    if target and numeral == "V" and suffix == "":
        suffix = "7"
    return f"{acc}{numeral}{suffix}{target}"


def _merge_fragments(tokens: list[str]) -> list[str]:
    merged: list[str] = []
    for token in tokens:
        folded = strip_accents(token).casefold()
        previous = merged[-1] if merged else None
        if previous and folded in _ACCIDENTAL_WORDS and _root(previous) and _root(previous)[1] == "" and len(_root(previous)[0]) == 1:
            merged[-1] = previous + _ACCIDENTAL_WORDS[folded]
        elif previous and _QUALITY_FRAGMENT.match(token) and _root(previous) and _quality(_root(previous)[1]) == "maj" \
                and _root(previous)[1] == "" and not _roman(previous):
            merged[-1] = previous + token
        else:
            merged.append(token)
    return merged


def symbol_tokens(text: Any) -> tuple[str, list[str]] | None:
    """('chord' | 'roman', các token dạng chuẩn) nếu mọi token đều là ký hiệu hợp âm/số La Mã, ngược lại None."""
    tokens = _merge_fragments(_raw_tokens(text))
    if not tokens:
        return None
    chords = [_chord(t) for t in tokens]
    if all(chords):
        return "chord", [c for c in chords if c]
    romans = [_roman(t) for t in tokens]
    if all(romans):
        return "roman", [r for r in romans if r]
    return None


def symbolic_equal(got: Any, expected: Any) -> bool | None:
    """None nếu `expected` không phải ký hiệu (để bộ chấm cũ xử lý); ngược lại đúng/sai theo ký hiệu chuẩn."""
    if isinstance(expected, (list, dict)) or expected is None:
        return None
    want = symbol_tokens(expected)
    if want is None:
        return None
    have = symbol_tokens(got)
    if have is None or have[0] != want[0]:
        return False
    return have[1] == want[1]


def note_list(text: Any) -> list[str] | None:
    """Danh sách tên nốt đã chuẩn hóa (Đô–Rê–Mi, hoa/thường, dấu nối bất kỳ) hoặc None nếu có token không phải nốt."""
    tokens = _merge_fragments(_raw_tokens(text))
    if not tokens:
        return None
    notes = []
    for token in tokens:
        parts = _root(token)
        if not parts or parts[1]:
            return None
        notes.append(parts[0])
    return notes


# Công thức "1 b3 5": nhận "3b", "m3 + P5", "♭3".
_FORMULA = re.compile(r"^[b#]?\d+(?:-[b#]?\d+)+$")
_FORMULA_QUALITY = {"m": "b", "M": "", "P": "", "d": "b", "A": "#"}


def formula_tokens(text: Any) -> list[str]:
    out = []
    for token in _raw_tokens(text):
        match = re.fullmatch(r"([mMPdA])(\d+)", token)
        if match:
            out.append(_FORMULA_QUALITY[match.group(1)] + match.group(2))
            continue
        match = re.fullmatch(r"(\d+)([b#])", token)
        out.append(match.group(2) + match.group(1) if match else token.lower())
    return out


def is_formula(expected: Any) -> bool:
    return isinstance(expected, str) and bool(_FORMULA.match(unicodedata.normalize("NFC", expected).replace("♭", "b").replace("♯", "#").strip()))


# Nhãn chức năng hòa âm: S, SD, Hạ át đều là Predominant; Chủ là Tonic.
_FUNCTION = {"t": "T", "tonic": "T", "chu": "T", "pd": "PD", "s": "PD", "sd": "PD", "predominant": "PD",
             "subdominant": "PD", "haat": "PD", "d": "D", "dominant": "D", "at": "D"}


def function_tokens(text: Any) -> list[str] | None:
    folded = re.sub(r"h[aạ]\s+[aá]t", "haat", strip_accents(_prepare(text)).casefold())
    tokens = [t for t in _SEP.split(folded) if t]
    mapped = [_FUNCTION.get(t) for t in tokens]
    return mapped if tokens and all(mapped) else None
