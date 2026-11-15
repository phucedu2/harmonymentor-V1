"""Chia văn bản dài thành đoạn theo GIỚI HẠN TOKEN của mô hình nhúng, có chồng lấn và giữ tiêu đề (T3).

Vì sao theo token chứ không theo từ: e5-small chỉ đọc 512 token (kể cả tiền tố), tiếng Việt tách token nhiều hơn tiếng Anh, nên
đếm từ dễ cắt đuôi đoạn mà không biết. Không cắt giữa câu; câu dài hơn ngân sách thì tách theo từ."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from typing import Protocol

from ..ai.tutor.chunker import split_sentences


class TokenCounter(Protocol):
    def count(self, text: str) -> int: ...


class WhitespaceCounter:
    """Đếm theo từ (dùng trong test và khi chưa có mô hình)."""

    def count(self, text: str) -> int:
        return len(text.split())


class TokenizerCounter:
    """Đếm đúng bằng bộ tách token của mô hình nhúng (không cắt bớt)."""

    def __init__(self, tokenizer):
        self.tok = tokenizer

    def count(self, text: str) -> int:
        return len(self.tok.encode(text, add_special_tokens=False).ids)


@dataclass(frozen=True)
class TextChunk:
    index: int
    text: str
    tokens: int


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def text_hash(text: str) -> str:
    return hashlib.sha256(normalize_text(text).lower().encode("utf-8")).hexdigest()


def _split_long(sentence: str, budget: int, counter: TokenCounter) -> list[str]:
    parts, cur = [], []
    for word in sentence.split():
        cur.append(word)
        if counter.count(" ".join(cur)) > budget and len(cur) > 1:
            cur.pop()
            parts.append(" ".join(cur))
            cur = [word]
    if cur:
        parts.append(" ".join(cur))
    return parts


def chunk_text(text: str, title: str, counter: TokenCounter, max_tokens: int, overlap_tokens: int) -> list[TextChunk]:
    """Mỗi đoạn + tiêu đề không vượt max_tokens. Đoạn sau lặp lại vài câu cuối của đoạn trước (tối đa overlap_tokens)."""
    budget = max(32, max_tokens - counter.count(title) - 2)
    overlap = min(overlap_tokens, budget // 2)
    sentences: list[str] = []
    for para in re.split(r"\n\s*\n", text):
        for s in split_sentences(normalize_text(para)):
            sentences.extend([s] if counter.count(s) <= budget else _split_long(s, budget, counter))
    chunks: list[TextChunk] = []
    cur: list[str] = []
    cur_tokens = 0
    for s in sentences:
        n = counter.count(s)
        if cur and cur_tokens + n > budget:
            body = " ".join(cur)
            chunks.append(TextChunk(len(chunks), body, counter.count(body)))
            keep: list[str] = []
            kept = 0
            for prev in reversed(cur):               # lấy các câu cuối làm phần chồng lấn
                pn = counter.count(prev)
                if kept + pn > overlap:
                    break
                keep.insert(0, prev)
                kept += pn
            cur, cur_tokens = keep, kept
        cur.append(s)
        cur_tokens += n
    if cur and (not chunks or " ".join(cur) != chunks[-1].text):
        body = " ".join(cur)
        # Đoạn đuôi chỉ gồm phần chồng lấn của đoạn trước thì không thêm (tránh đoạn trùng)
        if not chunks or normalize_text(body) not in normalize_text(chunks[-1].text):
            chunks.append(TextChunk(len(chunks), body, counter.count(body)))
    return chunks


def dedupe(chunks: list[TextChunk]) -> list[TextChunk]:
    seen, out = set(), []
    for c in chunks:
        h = text_hash(c.text)
        if h not in seen:
            seen.add(h)
            out.append(TextChunk(len(out), c.text, c.tokens))
    return out
