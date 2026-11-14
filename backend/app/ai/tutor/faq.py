"""RS-07: hỏi đáp cơ bản cho người mới khi không gọi được AI (AI tắt hoặc Gemini lỗi).

So khớp NGUYÊN CÂU sau khi bỏ dấu, dấu câu và từ đệm ("vậy", "ạ", "bạn ơi"): chỉ câu hỏi định nghĩa ngắn mới khớp,
nên "hợp âm mượn là gì" không bị trả lời bằng định nghĩa "hợp âm". Câu gõ không dấu khớp như câu có dấu (RS-28)."""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

_PATH = Path(__file__).with_name("faq_co_ban.json")
# Từ đệm cuối/đầu câu không đổi nghĩa câu hỏi.
_FILLER = {"vay", "a", "ha", "ban", "oi", "nhi", "the", "nhe", "z", "j", "ah", "nha", "cho", "minh", "hoi", "em", "toi",
           "la", "thi"}


@dataclass(frozen=True)
class FaqItem:
    id: str
    answer: str
    lesson_id: str
    source: str
    status: str


def normalize(text: str) -> str:
    t = unicodedata.normalize("NFD", text.lower()).replace("đ", "d")
    t = "".join(ch for ch in t if unicodedata.category(ch) != "Mn")
    words = re.findall(r"[a-z0-9#]+", t)
    words = ["gi" if w == "j" else w for w in words]
    # Bỏ từ đệm ở hai đầu câu, giữ ở giữa ("hop am la gi" vẫn còn "la").
    while words and words[-1] in _FILLER - {"la"}:
        words.pop()
    while words and words[0] in _FILLER - {"la"}:
        words.pop(0)
    return " ".join(words)


@lru_cache(maxsize=1)
def _table() -> dict[str, FaqItem]:
    data = json.loads(_PATH.read_text(encoding="utf-8"))
    out: dict[str, FaqItem] = {}
    for m in data["muc"]:
        item = FaqItem(m["id"], m["tra_loi"], m["bai"], m["nguon"], m["status"])
        for q in m["cau_hoi"]:
            out[normalize(q)] = item
    return out


def match(question: str, *, show_draft: bool = False) -> FaqItem | None:
    """Mục nháp chỉ dùng khi bật SHOW_DRAFT_CONTENT (nguyên tắc 17: chỉ Đạt duyệt sang approved)."""
    item = _table().get(normalize(question))
    if item is None or (item.status != "approved" and not show_draft):
        return None
    return item
