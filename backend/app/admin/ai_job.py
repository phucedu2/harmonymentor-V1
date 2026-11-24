"""AI tóm tắt CẢ tài liệu thành các bài nháp, chạy nền (ADR-029, Phúc chọn 1A 2A 3A 4A 5A 6A 7A 8A ngày 18/11/2026).

Luồng:
1. `plan_parts` chia tài liệu theo chương/mục (nhận dòng "Chương 2", "Bài 3", "Chapter 4"... ở đầu trang), mỗi phần
   tối đa 15 trang và PART_CHARS ký tự; trang bìa, mục lục, lời nói đầu, tài liệu tham khảo, trang trống và trang cổng nhạc
   lý đã bỏ thì không gửi AI và được ghi lý do. Chia bằng luật (không tốn lượt Gemini, chạy lại ra đúng kết quả cũ).
2. Mỗi phần một lần gọi AI. AI nhận danh mục kiến thức trang web ĐÃ CÓ (bài chính thức, bài AI đã xuất bản, bản nháp đang
   chờ, câu luyện tập) và chỉ tóm tắt khái niệm mới. Sau đó máy soát lại bằng độ giống (e5 nếu máy có mô hình, không thì
   TF-IDF): khối lý thuyết quá giống bài đã có bị bỏ dù AI không nhận ra. Phần không còn gì mới thì không tạo bản nháp.
3. Hết hạn mức Gemini (429) thì tạm dừng, phần đang làm trở về "chờ"; Quản trị viên bấm "Chạy tiếp" để làm nốt.

AI vẫn chỉ viết BẢN NHÁP: mọi bản nháp sinh ra đi qua đúng cửa duyệt và xuất bản như trước (ADR-025, ADR-028).

Đợt 3 (ADR-033): mỗi bước là một "node" kiểu n8n, ghi nhật ký vào `part["log"]` (node, ms, vào, ra, lý do):
Retrieve (truy xuất đoạn ĐÃ CÓ giống nhất, V1/V2) → Generate (thử lại 1 lần khi JSON hỏng, V6) → Validate (schema, trang,
Engine) → Dedup (bỏ khối trùng KÈM câu hỏi của khối, N3) → Flags (bám nguồn, chép nguyên văn, hình, N4/V8) → Draft.
Hạn mức: một bộ đếm theo khóa Gemini chung với Tutor (app/ai/budget.py, V5), không còn đếm riêng theo người bấm.
"""

from __future__ import annotations

import math
import os
import re
import threading
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Sequence
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..ai import budget
from ..ai.tutor.bm25 import strip_accents, tokenize
from ..ai.tutor.llm import LLMProvider, LLMUnavailable
from ..db.models import AiLessonDraft, AiSummaryJob, Exercise, LessonBlock, SourceDocument, User
from ..services.learning_service import visible_lessons
from . import ai_review, ai_service
from .content_service import AdminContentError, audit

PART_PAGES = 15            # như giới hạn cũ của một lần soạn: đầu ra 8192 token đủ cho 2–5 khối + 20 câu
PART_CHARS = 24000         # chữ gửi AI mỗi phần (~6–8 nghìn token), dư chỗ cho danh mục kiến thức đã có
MIN_PART_CHARS = 1500      # chương quá ngắn thì gộp với chương sau để không tạo bài một đoạn
CONTEXT_TOP_K = 3          # V1: mỗi trang của phần lấy 3 đoạn ĐÃ CÓ giống nhất
CONTEXT_MAX = 10           # tối đa 10 đoạn ĐÃ CÓ gửi AI mỗi phần
CONTEXT_CHARS = 360        # mỗi đoạn ĐÃ CÓ gửi phần đầu nội dung, không chỉ tên khối

# Ngưỡng trùng (cosine). e5 nén điểm vào khoảng 0,7–1,0 nên ngưỡng cao hơn TF-IDF. ADR-033 hiệu chỉnh trên bộ cặp có nhãn
# eval/ai_soan_bai/cases.jsonl (scripts/ai/danh_gia_ai_soan_bai.py); e5 so ĐỐI XỨNG ("query:" cả hai phía, V3).
DUP_BLOCK = {"e5": 0.95, "tfidf": 0.70}   # 0,90/0,55 trước đợt 3: bộ cặp cho P 0,55/0,57 (ADR-033 mục 4)
DUP_QUESTION = {"e5": 0.95, "tfidf": 0.80}

PART_STATUSES = ("pending", "running", "done", "no_new", "not_theory", "failed")


# --- 1. chia phần ----------------------------------------------------------------------------------------

_HEADING = re.compile(
    r"^\s*(chương|chuong|bài|bai|phần|phan|chapter|part|lesson|unit)\s+([0-9]{1,3}|[ivxlc]{1,6}\b|"
    r"một|hai|ba|bốn|năm|sáu|bảy|tám|chín|mười)", re.IGNORECASE)
_SKIP_HEAD = [
    ("mục lục", "mục lục"), ("muc luc", "mục lục"), ("table of contents", "mục lục"), ("contents", "mục lục"),
    ("lời nói đầu", "lời nói đầu"), ("loi noi dau", "lời nói đầu"), ("lời giới thiệu", "lời nói đầu"), ("preface", "lời nói đầu"),
    ("lời cảm ơn", "lời cảm ơn"), ("acknowledg", "lời cảm ơn"),
    ("tài liệu tham khảo", "tài liệu tham khảo"), ("tai lieu tham khao", "tài liệu tham khảo"), ("references", "tài liệu tham khảo"),
    ("bibliography", "tài liệu tham khảo"), ("chỉ mục", "chỉ mục"), ("index", "chỉ mục"),
]
_TOC_LINE = re.compile(r"(\.{3,}|…{2,}|\s{3,})\s*\d{1,3}\s*$")


def _first_lines(text: str, n: int = 3) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()][:n]


def skip_reason(index: int, text: str, dropped: set[int], total: int = 99) -> str | None:
    """Lý do bỏ trang (số trang tính từ 1), hoặc None nếu là trang nội dung."""
    page = index + 1
    if page in dropped:
        return "không liên quan nhạc lý (cổng kiểm tra lúc tải lên)"
    if not text.strip():
        return "trang trống hoặc không có chữ"
    head = " ".join(_first_lines(text)).lower()[:160]
    for needle, reason in _SKIP_HEAD:
        if head.startswith(needle) or f"\n{needle}" in "\n" + head[:60]:
            return reason
    lines = [line for line in text.splitlines() if line.strip()]
    if len(lines) >= 5 and sum(bool(_TOC_LINE.search(line)) for line in lines) / len(lines) >= 0.5:
        return "mục lục"
    # Bìa: một trong hai trang đầu, rất ít chữ, không mở đầu chương. Tài liệu ngắn (chữ dán vào) không có bìa.
    if total > 3 and page <= 2 and len(text.strip()) < 300 and heading_of(text) is None:
        return "trang bìa"
    return None


def heading_of(text: str) -> str | None:
    for line in _first_lines(text):
        if _HEADING.match(line):
            return line[:120]
    return None


def plan_parts(pages: Sequence[str], dropped: set[int]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Trả (các phần, các trang bị bỏ). Phần = {index, page_from, page_to, heading, pages: [số trang nội dung]}."""
    skipped: list[dict[str, Any]] = []
    chunks: list[dict[str, Any]] = []   # các nhóm trang liên tiếp theo chương
    current: dict[str, Any] | None = None
    for i, text in enumerate(pages):
        reason = skip_reason(i, text, dropped, len(pages))
        if reason:
            skipped.append({"page": i + 1, "reason": reason})
            continue
        head = heading_of(text)
        size = len(text)
        too_big = current is not None and (len(current["pages"]) >= PART_PAGES or current["chars"] + size > PART_CHARS)
        if current is None or head is not None or too_big:
            if current is not None:
                chunks.append(current)
            title = head or (f"{current['heading']} (tiếp)" if current and too_big and current["heading"] else None)
            current = {"heading": title, "pages": [], "chars": 0, "chapter": head is not None}
        current["pages"].append(i + 1)
        current["chars"] += size
    if current is not None:
        chunks.append(current)
    # Gộp chương quá ngắn vào phần sau (hoặc phần trước nếu là chương cuối) khi còn chỗ.
    merged: list[dict[str, Any]] = []
    for chunk in chunks:
        prev = merged[-1] if merged else None
        if prev is not None and prev["chars"] < MIN_PART_CHARS and len(prev["pages"]) + len(chunk["pages"]) <= PART_PAGES \
                and prev["chars"] + chunk["chars"] <= PART_CHARS:
            prev["pages"] += chunk["pages"]
            prev["chars"] += chunk["chars"]
            prev["heading"] = prev["heading"] or chunk["heading"]
            continue
        merged.append(chunk)
    if len(merged) >= 2 and merged[-1]["chars"] < MIN_PART_CHARS:
        last, prev = merged[-1], merged[-2]
        if len(prev["pages"]) + len(last["pages"]) <= PART_PAGES and prev["chars"] + last["chars"] <= PART_CHARS:
            prev["pages"] += last["pages"]
            prev["chars"] += last["chars"]
            merged.pop()
    parts = []
    for n, chunk in enumerate(merged, start=1):
        a, b = chunk["pages"][0], chunk["pages"][-1]
        parts.append({"index": n, "page_from": a, "page_to": b, "pages": chunk["pages"],
                      "heading": chunk["heading"] or (f"Trang {a}–{b}" if a != b else f"Trang {a}"),
                      "status": "pending", "draft_id": None, "duplicates": [], "note": None})
    return parts, skipped


# --- 2. kiến thức đã có và độ giống ---------------------------------------------------------------------

@dataclass
class Known:
    ref: str        # mã bài (L03, AI-1a2b3c4d) hoặc "Bản nháp: <tên>"
    title: str      # tên bài
    label: str      # tên khối hoặc "câu hỏi"
    text: str
    kind: str       # block | question


def _strings(value: Any, out: list[str], limit: int = 1500) -> None:
    """Gom mọi chuỗi trong payload khối bài (mỗi loại khối có cấu trúc riêng) để so độ giống."""
    if sum(map(len, out)) >= limit:
        return
    if isinstance(value, str):
        out.append(value)
    elif isinstance(value, dict):
        for v in value.values():
            _strings(v, out, limit)
    elif isinstance(value, list):
        for v in value:
            _strings(v, out, limit)


def build_catalog(db: Session) -> list[Known]:
    """5A: bài chính thức + bài AI đã xuất bản + câu luyện tập/quiz; thêm bản nháp đang chờ để hai tài liệu nói cùng một
    ý không sinh hai bài."""
    from ..content.versioning import current_version

    known: list[Known] = []
    for lesson in visible_lessons(db):
        for block in sorted(lesson.blocks, key=lambda b: b.position):
            parts: list[str] = []
            _strings(block.payload, parts)
            text = " ".join(parts).strip()
            if text:
                label = (block.payload or {}).get("title") if isinstance(block.payload, dict) else None
                known.append(Known(lesson.id, lesson.title, str(label or block.block_type), text[:1500], "block"))
        for exercise in lesson.exercises:
            version = current_version(exercise)
            if version is not None and version.prompt:
                known.append(Known(lesson.id, lesson.title, "câu hỏi", version.prompt[:600], "question"))
    for draft in db.scalars(select(AiLessonDraft).where(AiLessonDraft.status == "draft")):
        title = str(draft.content.get("title") or "bản nháp")
        for block in draft.content.get("blocks", []):
            known.append(Known(f"Bản nháp “{title[:60]}”", title, block["title"], " ".join(block["paragraphs"])[:1500], "block"))
    return known


def context_prompt(sim: "Similarity", pages: Sequence[str]) -> tuple[str, list[str]]:
    """V1 (ADR-033): RAG thật cho "ĐÃ CÓ". Với mỗi trang của phần, lấy các đoạn đã có GIỐNG NHẤT và gửi NỘI DUNG đoạn
    (không gửi cả danh mục tên khối bị cắt ở 6.000 ký tự như trước). V2: bản nháp của phần trước đã được thêm vào `sim`
    nên phần sau thấy ngay. Trả (chữ gửi AI, mã các đoạn đã gửi để ghi nhật ký)."""
    picked: dict[int, tuple[float, Known]] = {}
    for text in pages:
        for score, k in sim.top(text, "block", CONTEXT_TOP_K):
            key = id(k)
            if key not in picked or picked[key][0] < score:
                picked[key] = (score, k)
    best = sorted(picked.values(), key=lambda x: -x[0])[:CONTEXT_MAX]
    if not best:
        return "(chưa có bài nào giống phần này)", []
    lines = [f"- [{k.ref} · {k.label}] {k.text[:CONTEXT_CHARS]}" for _, k in best]
    return "\n".join(lines), [f"{k.ref} · {k.label} ({s:.2f})" for s, k in best]


class Similarity:
    """Tìm mục đã có giống nhất. e5 cục bộ nếu máy có mô hình (AI_DEDUP_E5 khác "0"), không thì TF-IDF trên từ đã tách
    (bm25.tokenize: giữ dấu + thêm bản bỏ dấu), tất định và chạy được trong CI."""

    def __init__(self, known: Sequence[Known]):
        self.known = list(known)
        self.backend = "tfidf"
        self._e5 = None
        if os.getenv("AI_DEDUP_E5", "1") != "0":
            try:
                from ..ai.local_embedder import get_local_embedder

                self._e5 = get_local_embedder()
            except Exception:   # thiếu onnxruntime/tokenizers: dùng TF-IDF
                self._e5 = None
        if self._e5 is not None:
            self.backend = "e5"
            # V3: so trùng là bài toán ĐỐI XỨNG (đoạn với đoạn) nên cả hai phía dùng tiền tố "query:" của e5.
            self._vecs = self._e5.embed([k.text for k in self.known], "query") if self.known else []
        else:
            self._rebuild_tfidf()

    def _rebuild_tfidf(self) -> None:
        self._tf = [Counter(tokenize(k.text)) for k in self.known]
        df: Counter[str] = Counter()
        for tf in self._tf:
            df.update(tf.keys())
        n = len(self._tf) + 1
        self._idf = {t: math.log(n / (1 + c)) + 1.0 for t, c in df.items()}
        self._norms = [self._norm(tf) for tf in self._tf]

    def _weight(self, tf: Counter[str]) -> dict[str, float]:
        return {t: c * self._idf.get(t, math.log(len(self._tf) + 1) + 1.0) for t, c in tf.items()}

    def _norm(self, tf: Counter[str]) -> float:
        return math.sqrt(sum(w * w for w in self._weight(tf).values())) or 1.0

    def add(self, items: Sequence[Known]) -> None:
        if not items:
            return
        self.known.extend(items)
        if self._e5 is not None:
            self._vecs.extend(self._e5.embed([k.text for k in items], "query"))
        else:
            self._rebuild_tfidf()

    def best(self, text: str, kind: str) -> tuple[float, Known | None]:
        top = self.top(text, kind, 1)
        return top[0] if top else (0.0, None)

    def top(self, text: str, kind: str, k: int) -> list[tuple[float, Known]]:
        idx = [i for i, kn in enumerate(self.known) if kn.kind == kind]
        if not idx or not text.strip():
            return []
        if self._e5 is not None:
            q = self._e5.embed([text], "query")[0]
            scores = [(sum(a * b for a, b in zip(q, self._vecs[i])), i) for i in idx]
        else:
            tf = Counter(tokenize(text))
            wq = self._weight(tf)
            nq = math.sqrt(sum(w * w for w in wq.values())) or 1.0
            scores = []
            for i in idx:
                wd = self._weight(self._tf[i])
                dot = sum(w * wd.get(t, 0.0) for t, w in wq.items())
                scores.append((dot / (nq * self._norms[i]), i))
        scores.sort(key=lambda x: (-x[0], x[1]))
        return [(round(score, 3), self.known[i]) for score, i in scores[:k]]


def _norm_name(text: str) -> str:
    return strip_accents(text).lower().strip()


# --- 3. chạy một phần -----------------------------------------------------------------------------------

PART_SYSTEM = ai_service.SYSTEM + """
Tài liệu dài được chia thành nhiều phần; bạn đang soạn MỘT phần. Trang web đã dạy nhiều kiến thức (danh mục ĐÃ CÓ):
- Liệt kê mọi khái niệm nhạc lý của phần trong 'concepts'. Khái niệm trùng ý với danh mục ĐÃ CÓ thì status "covered" và
  'covered_by' ghi mã bài đã có (ví dụ L03); khái niệm trang web chưa dạy thì status "new".
- CHỈ viết khối lý thuyết và câu luyện tập cho khái niệm "new". Không viết lại điều trang web đã dạy, kể cả khi tài liệu giải
  thích khác đi. Phần không còn khái niệm mới thì để 'blocks' và 'questions' rỗng.
- Phần không có kiến thức nhạc lý (lời tựa, tiểu sử, quảng cáo, tài liệu kỹ thuật phần mềm...) thì 'not_theory' = true.
- 'expansion' = true khi kiến thức mới không thuộc kỹ năng nào trong danh sách; khi đó vẫn chọn skill_id gần nhất."""


class _Log:
    """Nhật ký từng node của một phần, như màn "Executions" của n8n: node, thời gian, số vào/ra, ghi chú."""

    def __init__(self) -> None:
        self.rows: list[dict[str, Any]] = []
        self._t = time.perf_counter()

    def add(self, node: str, *, inp: int | None = None, out: int | None = None, note: str | None = None, **extra: Any) -> None:
        now = time.perf_counter()
        row = {"node": node, "ms": int((now - self._t) * 1000)}
        if inp is not None:
            row["in"] = inp
        if out is not None:
            row["out"] = out
        if note:
            row["note"] = note[:400]
        row.update({k: v for k, v in extra.items() if v is not None})
        self.rows.append(row)
        self._t = now


def run_part(db: Session, admin_id: str | None, provider: LLMProvider, doc: SourceDocument, part: dict[str, Any],
             sim: Similarity, catalog_text: str | None = None) -> dict[str, Any]:
    """Soạn một phần. Trả phần đã cập nhật (status done/no_new/not_theory). Lỗi AI ném ra cho run_job xử lý.
    `catalog_text` chỉ còn để tương thích chỗ gọi cũ: ngữ cảnh ĐÃ CÓ giờ truy xuất theo từng phần (V1)."""
    log = _Log()
    text, used_pages, truncated = ai_service.document_text(doc, part["pages"], PART_CHARS)
    log.add("extract", inp=len(part["pages"]), out=len(used_pages), note=truncated, chars=len(text))
    context, context_refs = context_prompt(sim, [doc.pages[n - 1] for n in used_pages])
    log.add("retrieve", out=len(context_refs), note="; ".join(context_refs[:6]) or None, backend=sim.backend)
    user = (f"Nguồn: {doc.source_title}\nPhần: {part['heading']} (trang {part['page_from']}–{part['page_to']})\n"
            f"Kỹ năng được phép dùng: {', '.join(ai_service._skill_ids(db))}\n"
            f"Các đoạn trang web ĐÃ CÓ giống phần này nhất (không soạn lại ý trong đó):\n{context}\n"
            f"Hãy viết 2–5 khối lý thuyết và 10–{ai_service.MAX_QUESTIONS} câu luyện tập trộn đủ các dạng và 3 mức, chỉ cho khái niệm mới.\n"
            f"<<<DOCUMENT>>>\n{text}\n<<<END>>>")
    raw, result, calls = ai_service.call_json(db, provider, admin_id, ("ai_document", doc.id), f"part:{part['index']}",
                                              PART_SYSTEM, user, ai_service.SCHEMA)
    log.add("generate", out=len(raw.get("blocks") or []), calls=calls, model=result.model,
            note="JSON hỏng lần đầu, đã thử lại 1 lần" if calls > 1 else None)
    part = {**part, "model": result.model}
    if raw.get("not_theory") is True:
        log.add("switch", note="not_theory")
        return {**part, "status": "not_theory", "log": log.rows,
                "note": "AI thấy phần này không có kiến thức nhạc lý nên không soạn bài."}

    # (a) Khái niệm AI nhận là đã có (kèm trang, để gắn cờ khối trộn ý cũ, V4).
    dups: list[dict[str, Any]] = []
    for c in raw.get("concepts") or []:
        if isinstance(c, dict) and c.get("status") == "covered" and isinstance(c.get("name"), str):
            dups.append({"concept": c["name"][:160], "where": str(c.get("covered_by") or "")[:80], "by": "ai", "score": None,
                         "page": c.get("page") if isinstance(c.get("page"), int) else None})
    # (b) Máy soát lại từng khối: AI có thể bỏ sót, nhất là khi diễn đạt khác.
    threshold = DUP_BLOCK[sim.backend]
    raw_blocks = [b for b in (raw.get("blocks") or []) if isinstance(b, dict)]
    kept_blocks, renumber = [], {}
    for i, b in enumerate(raw_blocks, start=1):
        text_b = f"{b.get('title', '')}. " + " ".join(p for p in (b.get("paragraphs") or []) if isinstance(p, str))
        score, hit = sim.best(text_b, "block")
        if hit is not None and score >= threshold:
            dups.append({"concept": str(b.get("title") or "")[:160], "where": f"{hit.ref} · {hit.label}"[:160], "by": sim.backend,
                         "score": score, "block": i})
        else:
            kept_blocks.append(b)
            renumber[i] = len(kept_blocks)
    dropped_blocks = {d["block"] for d in dups if d.get("block")}
    q_threshold = DUP_QUESTION[sim.backend]
    kept_questions, dup_questions = [], []
    for q in raw.get("questions") or []:
        prompt = q.get("prompt") if isinstance(q, dict) else None
        ref = q.get("block_ref") if isinstance(q, dict) else None
        if isinstance(ref, int) and ref in dropped_blocks:
            # N3: bỏ khối vì trùng thì bỏ cả câu hỏi của khối đó, không để bài nháp hỏi điều đã cắt khỏi bài.
            dup_questions.append(f"“{str(prompt)[:40]}”: hỏi về khối “{raw_blocks[ref - 1].get('title', '')}” đã bỏ vì trùng")
            continue
        score, hit = sim.best(prompt, "question") if isinstance(prompt, str) else (0.0, None)
        if hit is not None and score >= q_threshold:
            dup_questions.append(f"“{prompt[:40]}”: trùng câu đã có ở {hit.ref}")
        else:
            if isinstance(q, dict) and isinstance(ref, int):
                q = {**q, "block_ref": renumber.get(ref, ref + 1000)}   # số khối sau khi bỏ; số lạ → cần duyệt
            kept_questions.append(q)
    log.add("dedup", inp=len(raw_blocks), out=len(kept_blocks), backend=sim.backend,
            note=f"bỏ {len(raw_blocks) - len(kept_blocks)} khối, {len(dup_questions)} câu" if dup_questions or dropped_blocks else None)
    # Gộp báo cáo trùng theo tên khái niệm (AI và máy có thể cùng báo một ý).
    seen: set[str] = set()
    dups = [d for d in dups if not (_norm_name(d["concept"]) in seen or seen.add(_norm_name(d["concept"])))]  # type: ignore[func-returns-value]
    part["duplicates"] = dups[:40]
    if not kept_blocks:
        log.add("switch", note="no_new")
        return {**part, "status": "no_new", "log": log.rows,
                "note": "Mọi kiến thức của phần này trang web đã có nên không tạo bài mới."}

    page_to = used_pages[-1] if used_pages else part["page_to"]
    content = ai_service.normalize_content(db, {**raw, "blocks": kept_blocks, "questions": kept_questions},
                                           part["page_from"], page_to)
    content["dropped_questions"] = dup_questions + content["dropped_questions"]

    def _not_known(prompt: str) -> str | None:
        score, hit = sim.best(prompt, "question")
        return f"“{prompt[:40]}”: trùng câu đã có ở {hit.ref}" if hit is not None and score >= q_threshold else None

    ai_service.top_up_questions(db, provider, admin_id, ("ai_document", doc.id), doc.source_title, text, content,
                                part["page_from"], page_to, accept=_not_known, log=log)
    ai_service.mark_injection(doc, content)
    content["prompt_version"] = ai_service.prompt_version(PART_SYSTEM, ai_service.SCHEMA)
    content["duplicates"] = part["duplicates"]
    content["part"] = {"heading": part["heading"], "index": part["index"]}
    if truncated:
        content["truncated"] = truncated
    review = sum(1 for q in content["questions"] if ai_service.aq_needs_review(q))
    log.add("validate", inp=len(kept_questions), out=len(content["questions"]),
            note=f"loại {len(content['dropped_questions']) - len(dup_questions)} câu, {review} câu cần duyệt")
    content["flags"] = ai_review.review_flags(doc.pages, content, part["page_from"], page_to)
    log.add("flags", out=len(content["flags"]), note=", ".join(sorted({f["type"] for f in content["flags"]})) or None)
    log.add("draft", out=1)
    content["log"] = log.rows
    draft = AiLessonDraft(id=str(uuid4()), document_id=doc.id, created_by=admin_id, page_from=part["page_from"],
                          page_to=page_to, content=content, engine_report=ai_service.engine_check(content),
                          model=result.model, tokens_in=result.tokens_in, tokens_out=result.tokens_out)
    db.add(draft)
    # Bản nháp vừa soạn thành "đã có" cho các phần sau: sách hay ôn lại chương trước.
    sim.add([Known(f"Bản nháp “{content['title'][:60]}”", content["title"], b["title"], " ".join(b["paragraphs"]), "block")
             for b in content["blocks"]])
    return {**part, "status": "done", "draft_id": draft.id, "note": truncated, "log": log.rows}


# --- 4. việc chạy nền -----------------------------------------------------------------------------------

_active: set[str] = set()
_lock = threading.Lock()


def _set_parts(job: AiSummaryJob, parts: list[dict[str, Any]]) -> None:
    job.parts = [dict(p) for p in parts]   # gán danh sách mới: cột JSON không tự theo dõi sửa tại chỗ


def create_job(db: Session, admin: User, provider: LLMProvider | None, doc_id: str) -> AiSummaryJob:
    if provider is None:
        raise AdminContentError("AI_DISABLED", "Tính năng AI đang tắt (AI_ENABLED=false hoặc chưa có khóa).", 503)
    doc = ai_service._doc(db, doc_id)
    if doc.relevance_status != "accepted":
        raise AdminContentError("DOC_NOT_APPROVED", "Tài liệu này đang chờ Quản trị viên duyệt nội dung nhạc lý nên chưa dùng để soạn bài được.", 409)
    active = db.scalar(select(AiSummaryJob).where(AiSummaryJob.document_id == doc.id, AiSummaryJob.status.in_(("running", "paused")))
                       .order_by(AiSummaryJob.created_at.desc()))
    if active is not None:
        return active   # bấm lại khi đang chạy: trả việc cũ, không tạo việc thứ hai
    parts, skipped = plan_parts(doc.pages, set((doc.relevance_detail or {}).get("dropped_pages", [])))
    if not parts:
        raise AdminContentError("NO_CONTENT", "Tài liệu không còn trang nội dung nhạc lý nào để tóm tắt.", 422)
    job = AiSummaryJob(id=str(uuid4()), document_id=doc.id, created_by=admin.id, status="running", parts=parts, skipped_pages=skipped)
    db.add(job)
    audit(db, admin, "ai.job.create", "ai_summary_job", job.id, {"document": doc.id, "parts": len(parts), "skipped": len(skipped)})
    db.commit()
    return job


def run_job(job_id: str, provider: LLMProvider, session_factory: Callable[[], Session], now: Callable[[], datetime] | None = None) -> None:
    """Làm lần lượt các phần còn "chờ". Gọi trong luồng nền (start_job) hoặc trực tiếp trong test."""
    clock = now or (lambda: datetime.now(timezone.utc))
    with _lock:
        _active.add(job_id)
    try:
        with session_factory() as db:
            job = db.get(AiSummaryJob, job_id)
            if job is None or job.status != "running":
                return
            doc = db.get(SourceDocument, job.document_id)
            if doc is None or doc.deleted_at is not None:
                job.status, job.pause_reason = "cancelled", "document_deleted"
                db.commit()
                return
            sim = Similarity(build_catalog(db))
            admin = db.get(User, job.created_by) if job.created_by else None
            failures = 0
            while True:
                db.refresh(job)
                if job.status != "running":
                    return   # Quản trị viên bấm dừng
                parts = [dict(p) for p in job.parts]
                todo = next((p for p in parts if p["status"] in ("pending", "running")), None)
                if todo is None:
                    job.status, job.pause_reason = "done", None
                    if admin:
                        audit(db, admin, "ai.job.done", "ai_summary_job", job.id, {"drafts": sum(p["status"] == "done" for p in parts)})
                    db.commit()
                    return
                if budget.remaining(db, "authoring", clock()) == 0:
                    # V5: một bộ đếm theo khóa Gemini, đếm cả việc không có người tạo (created_by rỗng).
                    job.status, job.pause_reason = "paused", "daily_limit"
                    db.commit()
                    return
                todo["status"] = "running"
                _set_parts(job, parts)
                db.commit()
                if admin:
                    audit(db, admin, "ai.job.part", "ai_summary_job", job.id, {"part": todo["index"]})
                    db.commit()
                try:
                    done = run_part(db, job.created_by, provider, doc, todo, sim)
                    failures = 0
                except budget.BudgetExceeded:
                    parts = [{**p, "status": "pending"} if p["index"] == todo["index"] else p for p in parts]
                    _set_parts(job, parts)
                    job.status, job.pause_reason = "paused", "daily_limit"
                    db.commit()
                    return
                except LLMUnavailable as exc:
                    if exc.reason == "rate_limited":
                        # Hết hạn mức: phần này làm lại từ đầu khi chạy tiếp, không tính là lỗi.
                        parts = [{**p, "status": "pending"} if p["index"] == todo["index"] else p for p in parts]
                        _set_parts(job, parts)
                        job.status, job.pause_reason = "paused", "quota"
                        db.commit()
                        return
                    failures += 1
                    done = {**todo, "status": "failed", "note": "AI chưa trả lời được (quá giờ hoặc lỗi máy chủ Gemini)."}
                except AdminContentError as exc:
                    db.rollback()
                    failures += 1
                    done = {**todo, "status": "failed", "note": exc.message}
                db.refresh(job)
                parts = [done if p["index"] == todo["index"] else p for p in (dict(x) for x in job.parts)]
                _set_parts(job, parts)
                if failures >= 2:
                    # Hai phần liền nhau lỗi: Gemini đang trục trặc, dừng lại thay vì đốt hết lượt.
                    job.status, job.pause_reason = "paused", "unavailable"
                db.commit()
                if job.status != "running":
                    return
    finally:
        with _lock:
            _active.discard(job_id)


def start_job(job_id: str, provider: LLMProvider, session_factory: Callable[[], Session]) -> None:
    """Chạy nền trong một luồng. Một việc chỉ chạy một luồng một lúc."""
    with _lock:
        if job_id in _active:
            return
        _active.add(job_id)   # đánh dấu trước khi luồng chạy để job_view không tưởng là việc bị bỏ dở
    threading.Thread(target=run_job, args=(job_id, provider, session_factory), daemon=True, name=f"ai-job-{job_id[:8]}").start()


def resume_job(db: Session, admin: User, provider: LLMProvider | None, job_id: str) -> AiSummaryJob:
    if provider is None:
        raise AdminContentError("AI_DISABLED", "Tính năng AI đang tắt (AI_ENABLED=false hoặc chưa có khóa).", 503)
    job = get_job(db, job_id)
    if job.status == "cancelled":
        raise AdminContentError("JOB_CANCELLED", "Việc này đã dừng hẳn. Bấm soạn lại từ đầu nếu cần.", 409)
    parts = [{**p, "status": "pending", "note": None} if p["status"] in ("failed", "running") else p for p in job.parts]
    if not any(p["status"] == "pending" for p in parts):
        raise AdminContentError("JOB_FINISHED", "Mọi phần đã soạn xong.", 409)
    _set_parts(job, parts)
    job.status, job.pause_reason = "running", None
    audit(db, admin, "ai.job.resume", "ai_summary_job", job.id)
    db.commit()
    return job


def cancel_job(db: Session, admin: User, job_id: str) -> AiSummaryJob:
    job = get_job(db, job_id)
    if job.status in ("running", "paused"):
        job.status, job.pause_reason = "cancelled", "admin"
        _set_parts(job, [{**p, "status": "pending"} if p["status"] == "running" else p for p in job.parts])
        audit(db, admin, "ai.job.cancel", "ai_summary_job", job.id)
        db.commit()
    return job


def get_job(db: Session, job_id: str) -> AiSummaryJob:
    job = db.get(AiSummaryJob, job_id)
    if job is None:
        raise AdminContentError("JOB_NOT_FOUND", "Không có việc tóm tắt này.", 404)
    return job


def job_view(db: Session, job: AiSummaryJob) -> dict[str, Any]:
    if job.status == "running" and job.id not in _active:
        # Máy chủ khởi động lại giữa chừng: luồng nền đã mất, chuyển sang tạm dừng để Quản trị viên bấm chạy tiếp.
        job.status, job.pause_reason = "paused", "interrupted"
        _set_parts(job, [{**p, "status": "pending"} if p["status"] == "running" else p for p in job.parts])
        db.commit()
    counts = Counter(p["status"] for p in job.parts)
    finished = sum(counts[s] for s in ("done", "no_new", "not_theory", "failed"))
    return {"id": job.id, "document_id": job.document_id, "status": job.status, "pause_reason": job.pause_reason,
            "parts": [{**{k: p.get(k) for k in ("index", "page_from", "page_to", "heading", "status", "draft_id", "duplicates", "note")},
                       "log": p.get("log", [])} for p in job.parts],
            "skipped_pages": job.skipped_pages, "total": len(job.parts), "finished": finished,
            "drafts": counts["done"], "created_at": job.created_at, "updated_at": job.updated_at, "budget": budget.summary(db)}


def latest_jobs(db: Session) -> list[dict[str, Any]]:
    """Việc mới nhất của mỗi tài liệu (màn quản trị hiện tiến độ ngay dưới tài liệu)."""
    rows = db.scalars(select(AiSummaryJob).order_by(AiSummaryJob.created_at.desc()).limit(100)).all()
    seen: set[str] = set()
    out = []
    for job in rows:
        if job.document_id in seen:
            continue
        seen.add(job.document_id)
        out.append(job_view(db, job))
    return out
