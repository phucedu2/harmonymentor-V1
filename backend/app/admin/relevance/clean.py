"""Làm sạch chữ đã trích và lọc dòng giống chỉ dẫn tấn công (prompt injection) trước khi chữ tới bộ sinh bài."""

from __future__ import annotations

import re
import unicodedata

from ...ai.tutor.injection import looks_like_injection

_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def clean_text(text: str) -> str:
    text = unicodedata.normalize("NFC", text)
    text = _CTRL.sub(" ", text)
    text = re.sub(r"[ \t ]+", " ", text)
    text = re.sub(r"-\n(?=\w)", "", text)          # nối từ bị ngắt dòng bằng gạch nối
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def strip_injection(text: str) -> tuple[str, int, int]:
    """Bỏ các dòng giống chỉ dẫn tấn công. Trả (chữ đã lọc, số dòng bỏ, tổng số dòng có chữ)."""
    kept, dropped, total = [], 0, 0
    for line in text.split("\n"):
        if line.strip():
            total += 1
            if looks_like_injection(line):
                dropped += 1
                continue
        kept.append(line)
    return "\n".join(kept), dropped, total
