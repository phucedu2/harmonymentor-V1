"""Conservative shared checks for ungrounded lesson answers and Roman numerals."""
from __future__ import annotations

import re
import unicodedata


def _fold(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", text or "")
                   if unicodedata.category(c) != "Mn").lower().replace("đ", "d").strip()


def asks_lesson(question: str) -> bool:
    return any(term in _fold(question) for term in ("bai hoc", "giao trinh", "hoc lieu"))


def safe_lesson_abstention(reply: str) -> bool:
    """Only accept complete, fixed abstentions; uncertainty plus an assertion is unsafe."""
    text = re.sub(r"\s+", " ", _fold(reply)).rstrip(" .!?")
    return text in {
        "minh chua co hoc lieu de tra loi",
        "minh chua co hoc lieu",
        "minh chua co hoc lieu. ban gui trich doan nhe",
        "minh chua co trich doan bai hoc de xac minh",
        "minh chua co trich doan bai hoc de xac minh. ban hay gui trich doan nhe",
    }


def conflicting_degree_statements(reply: str, expected: str) -> bool:
    """Reject explicit conflicting degree expressions; not a complete semantic parser."""
    roman = r"[IViv]{1,5}(?:maj7|M7|ø7|°7|7)?"
    pattern = r"\b(?:bậc|bac)\s+(" + roman + r"|[1-7])\b|\bhợp\s+âm\s+thứ\s+([1-7])\b"
    # Arabic ordinals may accompany, but never replace, the exact Engine result.
    # Roman case and chord quality remain significant for Roman expressions.
    ordinal = {"I": "1", "II": "2", "III": "3", "IV": "4", "V": "5", "VI": "6", "VII": "7"}
    base = re.match(r"(?:VII|III|VI|IV|II|V|I)", expected.upper())
    for match in re.finditer(pattern, reply, flags=re.IGNORECASE):
        actual = match.group(1) or match.group(2)
        if actual.isdigit() and base and actual == ordinal.get(base.group(0)):
            continue
        if actual != expected:
            return True
    return False
