"""Nhận diện câu tấn công prompt rõ ràng trước khi gọi LLM (NFR-08, đề GĐ3 mục 7).

Đây chỉ là lớp đầu, rẻ và tất định. Lớp sau: lệnh tách khỏi dữ liệu (prompt.py), chuỗi canh gác, và
guardrail Music Engine trên câu trả lời. Không cố bắt mọi biến thể; câu lọt qua vẫn bị các lớp sau chặn."""

from __future__ import annotations

import re

from .bm25 import strip_accents

_PATTERNS = [
    r"\b(bo qua|phot lo|quen|ignore|disregard|forget)\b.{0,40}\b(huong dan|chi dan|lenh|quy tac|instruction|rule|prompt)",
    r"\b(system prompt|system instruction|developer mode|jailbreak|dan mode|prompt he thong|loi nhac he thong)\b",
    r"\b(in ra|tiet lo|cho (minh|toi|tao) xem|reveal|print|show|repeat).{0,40}\b(huong dan|prompt|chi dan|quy tac|instruction)",
    r"\b(dong vai|gia vo|hay la|act as|pretend|you are now|tu gio ban la)\b",
    r"\b(api key|khoa api|mat khau|password|token|gemini_api_key)\b",
    r"<<<|>>>|hm_data|hm_end|\[\s*system\s*\]|<\s*/?\s*system\s*>",
    r"\b(user_id|email) cua (nguoi khac|user khac|ban khac)",
]
_RE = [re.compile(p) for p in _PATTERNS]


def looks_like_injection(text: str) -> bool:
    plain = " ".join(strip_accents(text.lower()).split())
    return any(r.search(plain) for r in _RE)
