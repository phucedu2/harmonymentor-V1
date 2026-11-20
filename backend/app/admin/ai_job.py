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
"""

from __future__ import annotations

import json
import math
import os
import re
import threading
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Sequence
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..ai.tutor.bm25 import strip_accents, tokenize
from ..ai.tutor.llm import LLMProvider, LLMUnavailable
from ..db.models import AdminAuditLog, AiLessonDraft, AiSummaryJob, Exercise, LessonBlock, SourceDocument, User
from ..services.learning_service import visible_lessons
from . import ai_service
from .content_service import AdminContentError, audit

PART_PAGES = 15            # như giới hạn cũ của một lần soạn: đầu ra 8192 token đủ cho 2–5 khối + 20 câu
PART_CHARS = 24000         # chữ gửi AI mỗi phần (~6–8 nghìn token), dư chỗ cho danh mục kiến thức đã có
MIN_PART_CHARS = 1500      # chương quá ngắn thì gộp với chương sau để không tạo bài một đoạn
DAILY_PART_LIMIT = 40      # lượt gọi AI soạn phần mỗi Quản trị viên mỗi 24 giờ (bảo vệ hạn mức Gemini chung)
CATALOG_CHARS = 6000       # danh mục "đã có" gửi kèm mỗi lần gọi

# Ngưỡng trùng (cosine). e5 nén điểm vào khoảng 0,7–1,0 nên ngưỡng cao hơn TF-IDF. Là mức ban đầu, ghi trong ADR-029:
# cần hiệu chỉnh trên tài liệu thật của nhóm.
DUP_BLOCK = {"e5": 0.90, "tfidf": 0.55}
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


def catalog_prompt(known: Sequence[Known]) -> str:
    """Danh mục gọn cho AI: mỗi bài một dòng "mã · tên: khối; khối"."""
    lines: dict[str, tuple[str, list[str]]] = {}
    for k in known:
        if k.kind != "block":
            continue
        title, labels = lines.setdefault(k.ref, (k.title, []))
        if k.label not in labels:
            labels.append(k.label)
    out, size = [], 0
    for ref, (title, labels) in lines.items():
        line = f"- {ref} · {title}: {'; '.join(labels)}"[:400]
        if size + len(line) > CATALOG_CHARS:
            out.append("- …(còn nữa)")
            break
        out.append(line)
        size += len(line)
    return "\n".join(out) or "(chưa có bài nào)"


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
            self._vecs = self._e5.embed([k.text for k in self.known], "passage") if self.known else []
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
            self._vecs.extend(self._e5.embed([k.text for k in items], "passage"))
        else:
            self._rebuild_tfidf()

    def best(self, text: str, kind: str) -> tuple[float, Known | None]:
        idx = [i for i, k in enumerate(self.known) if k.kind == kind]
        if not idx or not text.strip():
            return 0.0, None
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
        score, i = max(scores)
        return round(score, 3), self.known[i]


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


def _part_text(doc: SourceDocument, part: dict[str, Any]) -> str:
    return "\n\n".join(f"[Trang {n}]\n{doc.pages[n - 1]}" for n in part["pages"] if doc.pages[n - 1])[:PART_CHARS]


def run_part(db: Session, admin_id: str | None, provider: LLMProvider, doc: SourceDocument, part: dict[str, Any],
             sim: Similarity, catalog_text: str) -> dict[str, Any]:
    """Soạn một phần. Trả phần đã cập nhật (status done/no_new/not_theory). Lỗi AI ném ra cho run_job xử lý."""
    user = (f"Nguồn: {doc.source_title}\nPhần: {part['heading']} (trang {part['page_from']}–{part['page_to']})\n"
            f"Kỹ năng được phép dùng: {', '.join(ai_service._skill_ids(db))}\n"
            f"Kiến thức ĐÃ CÓ trên trang web (không soạn lại):\n{catalog_text}\n"
            f"Hãy viết 2–5 khối lý thuyết và 10–{ai_service.MAX_QUESTIONS} câu luyện tập trộn đủ các dạng và 3 mức, chỉ cho khái niệm mới.\n"
            f"<<<DOCUMENT>>>\n{_part_text(doc, part)}\n<<<END>>>")
    result = provider.generate(PART_SYSTEM, user, ai_service.SCHEMA, 8192)
    try:
        raw = json.loads(result.text)
    except ValueError as exc:
        raise AdminContentError("AI_BAD_FORMAT", "AI trả về sai định dạng.", 502) from exc
    if not isinstance(raw, dict):
        raise AdminContentError("AI_BAD_FORMAT", "AI trả về sai định dạng.", 502)
    part = {**part, "model": result.model}
    if raw.get("not_theory") is True:
        return {**part, "status": "not_theory", "note": "AI thấy phần này không có kiến thức nhạc lý nên không soạn bài."}

    # (a) Khái niệm AI nhận là đã có.
    dups: list[dict[str, Any]] = []
    for c in raw.get("concepts") or []:
        if isinstance(c, dict) and c.get("status") == "covered" and isinstance(c.get("name"), str):
            dups.append({"concept": c["name"][:160], "where": str(c.get("covered_by") or "")[:80], "by": "ai", "score": None})
    # (b) Máy soát lại từng khối: AI có thể bỏ sót, nhất là khi diễn đạt khác.
    threshold = DUP_BLOCK[sim.backend]
    kept_blocks = []
    for b in raw.get("blocks") or []:
        if not isinstance(b, dict):
            continue
        text = f"{b.get('title', '')}. " + " ".join(p for p in (b.get("paragraphs") or []) if isinstance(p, str))
        score, hit = sim.best(text, "block")
        if hit is not None and score >= threshold:
            dups.append({"concept": str(b.get("title") or "")[:160], "where": f"{hit.ref} · {hit.label}"[:160], "by": sim.backend, "score": score})
        else:
            kept_blocks.append(b)
    q_threshold = DUP_QUESTION[sim.backend]
    kept_questions, dup_questions = [], []
    for q in raw.get("questions") or []:
        prompt = q.get("prompt") if isinstance(q, dict) else None
        score, hit = sim.best(prompt, "question") if isinstance(prompt, str) else (0.0, None)
        if hit is not None and score >= q_threshold:
            dup_questions.append(f"“{prompt[:40]}”: trùng câu đã có ở {hit.ref}")
        else:
            kept_questions.append(q)
    # Gộp báo cáo trùng theo tên khái niệm (AI và máy có thể cùng báo một ý).
    seen: set[str] = set()
    dups = [d for d in dups if not (_norm_name(d["concept"]) in seen or seen.add(_norm_name(d["concept"])))]  # type: ignore[func-returns-value]
    part["duplicates"] = dups[:40]
    if not kept_blocks:
        return {**part, "status": "no_new", "note": "Mọi kiến thức của phần này trang web đã có nên không tạo bài mới."}

    content = ai_service.normalize_content(db, {**raw, "blocks": kept_blocks, "questions": kept_questions},
                                           part["page_from"], part["page_to"])
    content["dropped_questions"] = dup_questions + content["dropped_questions"]
    content["duplicates"] = part["duplicates"]
    content["part"] = {"heading": part["heading"], "index": part["index"]}
    draft = AiLessonDraft(id=str(uuid4()), document_id=doc.id, created_by=admin_id, page_from=part["page_from"],
                          page_to=part["page_to"], content=content, engine_report=ai_service.engine_check(content),
                          model=result.model, tokens_in=result.tokens_in, tokens_out=result.tokens_out)
    db.add(draft)
    # Bản nháp vừa soạn thành "đã có" cho các phần sau: sách hay ôn lại chương trước.
    sim.add([Known(f"Bản nháp “{content['title'][:60]}”", content["title"], b["title"], " ".join(b["paragraphs"]), "block")
             for b in content["blocks"]])
    return {**part, "status": "done", "draft_id": draft.id, "note": None}


# --- 4. việc chạy nền -----------------------------------------------------------------------------------

_active: set[str] = set()
_lock = threading.Lock()


def _set_parts(job: AiSummaryJob, parts: list[dict[str, Any]]) -> None:
    job.parts = [dict(p) for p in parts]   # gán danh sách mới: cột JSON không tự theo dõi sửa tại chỗ


def _calls_today(db: Session, admin_id: str | None, now: datetime) -> int:
    return db.scalar(select(func.count()).select_from(AdminAuditLog).where(
        AdminAuditLog.actor_id == admin_id, AdminAuditLog.action == "ai.job.part",
        AdminAuditLog.created_at >= now - timedelta(days=1))) or 0


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
            catalog_text = catalog_prompt(sim.known)
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
                if _calls_today(db, job.created_by, clock()) >= DAILY_PART_LIMIT:
                    job.status, job.pause_reason = "paused", "daily_limit"
                    db.commit()
                    return
                todo["status"] = "running"
                _set_parts(job, parts)
                db.commit()
                if admin:
                    audit(db, admin, "ai.job.part", "ai_summary_job", job.id, {"part": todo["index"]})
                    db.commit()   # tính lượt ngay cả khi phần này lỗi (rollback bên dưới không xóa)
                try:
                    done = run_part(db, job.created_by, provider, doc, todo, sim, catalog_text)
                    failures = 0
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
            "parts": [{k: p.get(k) for k in ("index", "page_from", "page_to", "heading", "status", "draft_id", "duplicates", "note")}
                      for p in job.parts],
            "skipped_pages": job.skipped_pages, "total": len(job.parts), "finished": finished,
            "drafts": counts["done"], "created_at": job.created_at, "updated_at": job.updated_at}


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
