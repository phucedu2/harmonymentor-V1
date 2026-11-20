"""BM25 cục bộ cho kho đoạn bài học: dự phòng khi Gemini embedding không dùng được (đề GĐ3 mục 2).

Tách từ đơn giản cho tiếng Việt: chữ thường, giữ dấu, và thêm bản bỏ dấu của mỗi từ để người gõ
không dấu ("hop am") vẫn khớp "hợp âm". Ký hiệu hợp âm (Cmaj7, C7) giữ nguyên thành một từ."""

from __future__ import annotations

import math
import re
import unicodedata
from collections import Counter
from typing import Sequence

_TOKEN = re.compile(r"[0-9A-Za-zÀ-ỹĐđ#♯♭]+")
# Hư từ tiếng Việt hay gặp trong câu hỏi ("... là gì", "thế nào"): không mang chủ đề, bỏ để BM25 không
# chấm điểm cao cho câu ngoài phạm vi chỉ vì trùng các từ này.
STOPWORDS = frozenset("""là gì thế nào có không của và các những cho được trong một mình bạn sao như hôm nay này
khi thì ở đi ta với vì theo hay làm để ra về bao nhiêu nhé ạ ơi đó kia cũng rất lại đã đang sẽ thể nên giúp
hãy muốn biết hỏi ai đâu""".split())


def strip_accents(text: str) -> str:
    text = text.replace("đ", "d").replace("Đ", "D")
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")


_PLAIN_STOP = frozenset(strip_accents(w) for w in STOPWORDS)


def tokenize(text: str) -> list[str]:
    out: list[str] = []
    for tok in _TOKEN.findall(unicodedata.normalize("NFC", text).lower()):
        if tok in STOPWORDS or strip_accents(tok) in _PLAIN_STOP:
            continue
        out.append(tok)
        plain = strip_accents(tok)
        if plain != tok:
            out.append(plain)
    return out


class BM25:
    def __init__(self, docs: Sequence[str], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b = k1, b
        self.docs = [Counter(tokenize(d)) for d in docs]
        self.lengths = [sum(d.values()) for d in self.docs]
        self.avg = (sum(self.lengths) / len(self.lengths)) if self.lengths else 0.0
        df: Counter[str] = Counter()
        for d in self.docs:
            df.update(d.keys())
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def scores(self, query: str) -> list[float]:
        terms = set(tokenize(query))
        out = []
        for doc, length in zip(self.docs, self.lengths):
            s = 0.0
            for t in terms:
                f = doc.get(t)
                if not f:
                    continue
                s += self.idf[t] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * length / (self.avg or 1)))
            out.append(s)
        return out
