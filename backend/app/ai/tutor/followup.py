"""Câu hỏi nối tiếp trong cùng phiên drawer ("Vậy nó là bậc mấy trong F major?"), 28/11 phương án (a).

Drawer dùng lại phiên. Backend chỉ dùng lịch sử khi câu mới chỉ tới hợp âm trước đó bằng "nó / hợp âm đó…",
và chỉ lấy MỘT hợp âm do Music Engine nhận ra trong lượt gần nhất. Lượt có từ hai hợp âm trở lên thì không đoán.
"Hợp âm này / đang chọn" vẫn là hợp âm chọn trên giao diện (xem engine_query._add_context_facts)."""

from __future__ import annotations

import re
from typing import Sequence

_FOLLOWUP = re.compile(
    r"(?<![\wÀ-ỹ])(?:nó|hợp âm (?:đó|ấy|trên|kia|vừa rồi|vừa nãy|lúc nãy)|hop am (?:do|ay|tren|vua roi))(?![\wÀ-ỹ])",
    re.IGNORECASE)

MAX_USER_TURNS = 3  # chỉ nhìn tối đa 3 câu hỏi gần nhất, tránh lấy hợp âm đã cũ


def is_followup(text: str) -> bool:
    return bool(_FOLLOWUP.search(text or ""))


def _chords(text: str) -> set[str]:
    from .engine_query import engine_answer

    return {f["args"]["symbol"] for f in engine_answer(text).facts if f["tool"] == "get_chord_tones"}


def chord_from_turns(turns: Sequence[tuple[str, str]]) -> str | None:
    """Hợp âm mà "nó" chỉ tới: xét câu hỏi gần nhất, rồi câu trả lời ngay sau nó; cũ hơn nếu cả hai không có hợp âm."""
    rows = list(turns)
    seen_users = 0
    for i in range(len(rows) - 1, -1, -1):
        role, content = rows[i]
        if role != "user":
            continue
        seen_users += 1
        candidates = [content]
        if i + 1 < len(rows) and rows[i + 1][0] == "assistant":
            candidates.append(rows[i + 1][1])
        for text in candidates:
            found = _chords(text)
            if len(found) == 1:
                return found.pop()
            if len(found) > 1:
                return None  # không đoán giữa nhiều hợp âm
        if seen_users >= MAX_USER_TURNS:
            break
    return None
