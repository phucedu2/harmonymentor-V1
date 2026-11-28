"""Cờ cho người duyệt bản nháp AI (ADR-033, đợt 3): trang sai, bám nguồn thấp, chép nguyên văn, nhắc tới hình/ví dụ,
khối trộn ý cũ.

Vì sao có file này: trước đợt 3, trang AI ghi sai bị "kẹp" lặng lẽ về trang đầu của phần (trích dẫn giả), không có gì đo
ý trong bài có thật ở trang nguồn không, không có gì bắt chép nguyên văn (nguyên tắc 11). Cờ ở đây là CẢNH BÁO (Phúc chọn 2A):
không chặn cứng, nhưng mỗi cờ phải được tick "đã đối chiếu" thì mới xuất bản được.

Mọi phép đo tất định: TF-IDF trên từ (bm25.tokenize) trong CI; e5 cục bộ nếu máy có mô hình (AI_GROUND_E5 khác "0").
Ngưỡng chọn trên bộ đánh giá `eval/ai_soan_bai/cases.jsonl` (scripts/ai/danh_gia_ai_soan_bai.py), ghi ở ADR-033.
"""

from __future__ import annotations

import hashlib
import math
import os
import re
from collections import Counter
from typing import Any, Sequence

from ..ai.tutor.bm25 import strip_accents, tokenize

# Ngưỡng bám nguồn (cosine lời giảng của khối ↔ trang được trích). Chọn theo 3A trên bộ đánh giá: recall bắt khối bịa
# >= 95% mà ít báo nhầm nhất (ADR-033 mục 4). e5-small nén điểm vào khoảng 0,83–0,96 nên ngưỡng e5 cao.
GROUND_MIN = {"tfidf": 0.30, "e5": 0.89}
# Trang khác trong phần giống hơn trang được trích ít nhất chừng này = AI ghi nhầm trang (cờ wrong_page).
BETTER_PAGE_MARGIN = {"tfidf": 0.05, "e5": 0.02}
VERBATIM_N = 12          # N4: chuỗi 12 từ liên tiếp trùng trang nguồn = chép nguyên văn
_FIGURE = re.compile(
    r"(?<!\w)(?:(?:xem|như|theo)\s+)?(?:ví dụ|vd\.?|hình|bảng|sơ đồ|khuông nhạc|khuông|bản nhạc|example|figure|fig\.|table|staff|"
    r"musical example)\s*(?:số\s*)?\d+(?:[.\-–]\d+)*|(?:ví dụ|bản nhạc|hình|khuông nhạc)\s+(?:dưới đây|bên dưới|sau đây|trên)",
    re.IGNORECASE)
_WORD = re.compile(r"[\wÀ-ỹ#♯♭]+", re.UNICODE)
_VI = re.compile(r"[ăâđêôơưạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ]", re.IGNORECASE)

FLAG_TEXT = {
    "page_out_of_range": "Trang AI ghi nằm ngoài phần đang soạn",
    "low_grounding": "Ý trong khối ít giống trang được trích",
    "wrong_page": "Ý trong khối giống trang khác hơn trang được trích",
    "grounding_unchecked": "Không đo được bám nguồn",
    "verbatim": "Có đoạn chép nguyên văn tài liệu",
    "figure_ref": "Nhắc tới ví dụ/hình mà bài không có",
    "source_figure": "Trang nguồn có ví dụ/hình, chữ trích có thể thiếu ký âm",
    "mixed_block": "Khối có thể trộn ý trang web đã dạy",
    "truncated": "Chữ gửi AI bị cắt bớt",
    "few_questions": "Ít câu luyện tập hơn mức tối thiểu",
    "injection_stripped": "Tài liệu có dòng giống lệnh điều khiển AI đã bị lọc bỏ",
    "injection_echo": "Bài có chữ giống lệnh điều khiển AI hoặc lộ khóa",
}

# 7A (zip thầy G-28, 23/11): kiểm cả ĐẦU RA. Cổng tải lên đã lọc dòng giống lệnh, nhưng biến thể lọt qua có thể được AI
# chép vào bài. Chỉ dùng mẫu hẹp: mẫu "quên/bỏ qua … quy tắc" của Tutor bắt nhầm câu nhạc lý ("đừng quên quy tắc bè").
_ECHO = re.compile(r"\b(system prompt|system instruction|developer mode|jailbreak|prompt he thong|api key|khoa api|"
                   r"gemini_api_key|secret key|ignore (all |the )?previous|bo qua (moi |tat ca )?(chi dan|huong dan) (truoc|tren))\b"
                   r"|<<<|>>>|hm_data|hm_end|<\s*/?\s*system\s*>")


def _echo(text: str) -> bool:
    return bool(_ECHO.search(" ".join(strip_accents(text.lower()).split())))


def _id(kind: str, where: str, detail: str) -> str:
    return hashlib.sha1(f"{kind}|{where}|{detail}".encode("utf-8")).hexdigest()[:12]


def flag(kind: str, where: str, detail: str) -> dict[str, Any]:
    return {"id": _id(kind, where, detail), "type": kind, "label": FLAG_TEXT[kind], "where": where, "detail": detail}


def is_vietnamese(text: str) -> bool:
    letters = sum(ch.isalpha() for ch in text) or 1
    return len(_VI.findall(text)) / letters > 0.02


def words(text: str) -> list[str]:
    return [w.lower() for w in _WORD.findall(text)]


def verbatim_hits(text: str, source: str, n: int = VERBATIM_N) -> list[str]:
    """Các chuỗi >= n từ của `text` có nguyên trong `source` (đã gộp chuỗi chồng nhau)."""
    a, b = words(text), words(source)
    if len(a) < n or len(b) < n:
        return []
    grams = {tuple(b[i:i + n]) for i in range(len(b) - n + 1)}
    hits, i = [], 0
    while i <= len(a) - n:
        if tuple(a[i:i + n]) in grams:
            j = i + n
            while j < len(a) and tuple(a[j - n + 1:j + 1]) in grams:
                j += 1
            hits.append(" ".join(a[i:j]))
            i = j
        else:
            i += 1
    return hits


class PageScorer:
    """Độ giống giữa một đoạn chữ và từng trang nguồn. Đối xứng: cả hai phía cùng cách biểu diễn."""

    def __init__(self, pages: dict[int, str]):
        self.pages = {n: t for n, t in pages.items() if t and t.strip()}
        self.backend = "tfidf"
        self._e5 = None
        if os.getenv("AI_GROUND_E5", os.getenv("AI_DEDUP_E5", "1")) != "0" and self.pages:
            try:
                from ..ai.local_embedder import get_local_embedder

                self._e5 = get_local_embedder()
            except Exception:   # thiếu onnxruntime/tokenizers hoặc mô hình: dùng TF-IDF
                self._e5 = None
        if self._e5 is not None:
            self.backend = "e5"
            # e5: "query: " cho bài toán đối xứng (so hai đoạn chữ với nhau), xem ADR-033 mục V3.
            self._vecs = dict(zip(self.pages, self._e5.embed(list(self.pages.values()), "query")))
        else:
            tfs = {n: Counter(tokenize(t)) for n, t in self.pages.items()}
            df: Counter[str] = Counter()
            for tf in tfs.values():
                df.update(tf.keys())
            total = len(tfs) + 1
            self._idf = {t: math.log(total / (1 + c)) + 1.0 for t, c in df.items()}
            self._default_idf = math.log(total) + 1.0
            self._w = {n: self._weights(tf) for n, tf in tfs.items()}

    def _weights(self, tf: Counter[str]) -> dict[str, float]:
        w = {t: (1 + math.log(c)) * self._idf.get(t, self._default_idf) for t, c in tf.items()}
        norm = math.sqrt(sum(v * v for v in w.values())) or 1.0
        return {t: v / norm for t, v in w.items()}

    def scores(self, text: str) -> dict[int, float]:
        if not self.pages or not text.strip():
            return {}
        if self._e5 is not None:
            q = self._e5.embed([text], "query")[0]
            return {n: round(sum(a * b for a, b in zip(q, v)), 3) for n, v in self._vecs.items()}
        wq = self._weights(Counter(tokenize(text)))
        return {n: round(sum(v * wp.get(t, 0.0) for t, v in wq.items()), 3) for n, wp in self._w.items()}


def block_text(block: dict[str, Any]) -> str:
    return f"{block.get('title', '')}. " + " ".join(block.get("paragraphs", []))


def review_flags(pages: Sequence[str], content: dict[str, Any], page_from: int, page_to: int) -> list[dict[str, Any]]:
    """Tính lại mọi cờ của bản nháp từ chữ nguồn và nội dung hiện tại (gọi lúc soạn, lúc sửa và lúc xuất bản)."""
    part = {n: pages[n - 1] for n in range(page_from, min(page_to, len(pages)) + 1) if 0 < n <= len(pages)}
    scorer = PageScorer(part)
    source_all = "\n".join(part.values())
    out: list[dict[str, Any]] = []
    if content.get("truncated"):
        out.append(flag("truncated", "draft", str(content["truncated"])))
    if content.get("question_shortfall"):
        out.append(flag("few_questions", "draft", str(content["question_shortfall"])))
    if content.get("injection_lines_removed"):
        n = int(content["injection_lines_removed"])
        out.append(flag("injection_stripped", "draft", f"Cổng tải lên đã bỏ {n} dòng của tài liệu. Đọc lại bài xem có ý lạ không."))
    for i, b in enumerate(content.get("blocks", []), start=1):
        if _echo(block_text(b)):
            out.append(flag("injection_echo", f"block:{i}", "Khối có chữ giống lệnh điều khiển AI: xóa đoạn đó."))
    for i, q in enumerate(content.get("questions", []), start=1):
        parts = [q.get("prompt", ""), q.get("explanation") or "", *q.get("options", [])]
        if _echo(" ".join(str(p) for p in parts)):
            out.append(flag("injection_echo", f"question:{i}", "Câu có chữ giống lệnh điều khiển AI: xóa hoặc sửa câu."))
    lang_gap = scorer.backend == "tfidf" and bool(part) and \
        is_vietnamese(" ".join(block_text(b) for b in content.get("blocks", []))) != is_vietnamese(source_all)
    if lang_gap:
        out.append(flag("grounding_unchecked", "draft",
                        "Tài liệu nguồn và bài tóm tắt khác ngôn ngữ, máy này không có mô hình e5 nên không đo được độ bám "
                        "nguồn. Đối chiếu từng khối với trang gốc."))
    covered = [d for d in content.get("duplicates", []) if d.get("by") == "ai" and isinstance(d.get("page"), int)]
    for i, b in enumerate(content.get("blocks", []), start=1):
        where = f"block:{i}"
        text = block_text(b)
        body = " ".join(b.get("paragraphs", []))   # bám nguồn đo trên lời giảng; tiêu đề ngắn hay lặp từ khóa nên bỏ
        claimed = b.get("page_claimed")
        if isinstance(claimed, int):
            out.append(flag("page_out_of_range", where, f"AI ghi trang {claimed}, phần này chỉ gồm trang {page_from}–{page_to}. "
                                                        f"Hãy sửa trang của khối cho đúng."))
        if not lang_gap and part:
            sc = scorer.scores(body)
            cited = sc.get(b.get("page"), 0.0)
            best_page = max(sc, key=lambda n: (sc[n], -n)) if sc else None
            better = best_page is not None and best_page != b.get("page") and \
                sc[best_page] - cited >= BETTER_PAGE_MARGIN[scorer.backend]
            hint = f" Trang {best_page} giống hơn ({sc[best_page]:.2f})." if better else ""
            if cited < GROUND_MIN[scorer.backend]:
                out.append(flag("low_grounding", where, f"Độ giống với trang {b.get('page')}: {cited:.2f} "
                                                        f"(ngưỡng {GROUND_MIN[scorer.backend]:.2f}, {scorer.backend}).{hint}"))
            elif better:
                out.append(flag("wrong_page", where, f"Khối ghi trang {b.get('page')} ({cited:.2f}) nhưng trang {best_page} "
                                                     f"giống hơn ({sc[best_page]:.2f}). Kiểm lại trang trích dẫn."))
        for hit in verbatim_hits(" ".join(b.get("paragraphs", [])), source_all)[:3]:
            out.append(flag("verbatim", where, f"“{hit[:160]}”: diễn đạt lại thay vì chép (nguyên tắc 11)."))
        for m in list(_FIGURE.finditer(text))[:2]:
            out.append(flag("figure_ref", where, f"Khối viết “{m.group(0)}” nhưng bài không có hình/ví dụ đó. "
                                                 f"Bỏ câu này hoặc tự thêm ví dụ (qua Music Engine)."))
        src = part.get(b.get("page"), "")
        refs = sorted({m.group(0) for m in _FIGURE.finditer(src)})[:3]
        if refs:
            out.append(flag("source_figure", where, f"Trang {b.get('page')} có {', '.join(refs)}: ký âm trên khuông không trích được "
                                                    f"thành chữ, khối có thể thiếu ví dụ."))
        mixed = [d for d in covered if d["page"] == b.get("page")]
        if mixed:
            names = "; ".join(f"{d['concept']} ({d.get('where') or 'đã có'})" for d in mixed[:3])
            out.append(flag("mixed_block", where, f"AI báo trang {b.get('page')} cũng có ý trang web đã dạy: {names}. "
                                                  f"Xóa phần lặp trong khối nếu có."))
    return out


def unacknowledged(flags: Sequence[dict[str, Any]], acknowledged: Sequence[str]) -> list[dict[str, Any]]:
    ack = set(acknowledged or [])
    return [f for f in flags if f["id"] not in ack]
