"""Nhận diện câu tấn công prompt rõ ràng trước khi gọi LLM (NFR-08, đề GĐ3 mục 7).

Đây chỉ là lớp đầu, rẻ và tất định. Lớp sau: lệnh tách khỏi dữ liệu (prompt.py), chuỗi canh gác, và
guardrail Music Engine trên câu trả lời. Không cố bắt mọi biến thể; câu lọt qua vẫn bị các lớp sau chặn."""

from __future__ import annotations

import re

from .bm25 import strip_accents

_PATTERNS = [
    r"\b(bo qua|phot lo|quen|ignore|disregard|forget)\b.{0,40}\b(huong dan|chi dan|lenh|quy tac|luat le|luat|instruction|rule|prompt)",
    r"\b(system prompt|system instruction|developer mode|jailbreak|dan mode|prompt he thong|loi nhac he thong)\b",
    r"\b(in ra|in lai|tiet lo|cho (minh|toi|tao) xem|reveal|print|show|repeat).{0,40}\b(huong dan|prompt|chi dan|quy tac|instruction)",
    # "đóng vai trò" và "C# hay là Db" là câu nhạc lý bình thường, trước đây bị chặn nhầm.
    r"\b(dong vai(?! tro)|gia vo|act as|pretend|you are now|tu gio ban la)\b",
    r"\bhay la (mot |1 )?(tro ly|chatbot|bot|ai|nguoi|hacker|giao vien|chuyen gia)\b",
    r"\b(api key|khoa api|gemini_api_key|secret key)\b",
    # Mật khẩu/token chỉ là tấn công khi đòi xem/lấy, hoặc của hệ thống/người khác. "Đổi/quên mật khẩu" là câu hỏi
    # cách dùng hợp lệ (luồng D), trước đây bị chặn nhầm (GĐ0 góp ý thầy, lỗ hổng 7).
    r"\b(in ra|tiet lo|cho (minh|toi|tao) (xem|biet)|dua|gui|reveal|print|show|tell me|give me|lay)\b.{0,30}"
    r"\b(mat khau|password|token)\b",
    r"\b(mat khau|password|token)\b.{0,30}\b(he thong|admin|quan tri|cua ban|nguoi khac|user khac|server|database)\b",
    r"<<<|>>>|hm_data|hm_end|\[\s*system\s*\]|<\s*/?\s*system\s*>",
    r"\b(user_id|email) cua (nguoi khac|user khac|ban khac)",
]
_RE = [re.compile(p) for p in _PATTERNS]


def looks_like_injection(text: str) -> bool:
    plain = " ".join(strip_accents(text.lower()).split())
    return any(r.search(plain) for r in _RE)
