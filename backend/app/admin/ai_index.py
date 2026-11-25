"""Nạp bài AI đã xuất bản vào kho kiến thức của AI Tutor (ADR-033 mục N5, Phúc chọn 1A và 6A ngày 22/11/2026).

Vì sao: trước đợt 3, kho của Tutor chỉ đọc bài tĩnh trong code (curriculum_specs), nên học sinh hỏi về bài AI vừa học thì
Tutor "không biết". Giờ theo mẫu ingestion của n8n "Data Loader → Text Splitter → Embeddings → Vector Store":

- Data Loader: `ai_lesson_chunks` đọc khối lý thuyết của bài AI ĐANG HIỆN (bảng Lesson/LessonBlock), nguồn "sách X, trang n".
- Text Splitter: cùng `chunker.chunk_block` (đoạn 80–100 từ) như bài tĩnh.
- Embeddings + Vector Store: Qdrant là kho chính (khi RAG_ENABLED và QDRANT_URL bật): `sync_lesson` gỡ điểm cũ của bài rồi
  nạp lại khi bài được hiện, chỉ gỡ khi bài bị ẩn. Đường dự phòng (e5 trong bộ nhớ + BM25) đọc thẳng `lesson_chunks()`
  nên chỉ cần xóa bộ nhớ đệm (1A: không phải dựng lại file vector).
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

log = logging.getLogger(__name__)
AI_TRACK = "AI soạn từ tài liệu"
ADMIN_TRACK = "Quản trị viên soạn"          # bài tạo bằng form hoặc nhập file (ADR-035)
TUTOR_TRACKS = (AI_TRACK, ADMIN_TRACK)       # Phúc 9A (25/11/2026): bài M- đang hiện cũng vào kho AI Tutor


def _source_label(db: Session, lesson_id: str) -> str:
    from ..db.models import LessonSource, SourceWork

    row = db.execute(select(LessonSource, SourceWork).join(SourceWork, SourceWork.id == LessonSource.source_work_id)
                     .where(LessonSource.lesson_id == lesson_id)).first()
    if row:
        return f"{row[1].title} · {row[0].locator}"
    return "Giáo trình do Quản trị viên soạn" if lesson_id.startswith("M-") else "Tài liệu do Quản trị viên tải lên"


def ai_lessons(db: Session) -> list[Any]:
    """Bài do AI hoặc Quản trị viên soạn mà học sinh đang thấy (đã xuất bản, không ẩn, không xóa)."""
    from ..content.overrides import hidden_lesson_ids
    from ..db.models import Lesson

    hidden = hidden_lesson_ids(db)
    return [lesson for lesson in db.scalars(select(Lesson).where(Lesson.track.in_(TUTOR_TRACKS)).order_by(Lesson.order_index, Lesson.id))
            if lesson.id not in hidden]


def ai_lesson_chunks(db: Session) -> list[Any]:
    from ..ai.tutor.chunker import block_text, chunk_block
    from ..content.overrides import effective_blocks

    out = []
    for lesson in ai_lessons(db):
        source = _source_label(db, lesson.id)
        title = source.split(" · ")[0]
        # Chữ đã sửa và xuất bản (ADR-023) thắng chữ gốc: Tutor trả lời đúng điều học sinh đang đọc.
        for block, payload in effective_blocks(db, lesson):
            if block.block_type != "theory":
                continue
            # Trích dẫn theo trang của KHỐI (publish ghi source_page) để Tutor nói "sách X, trang n", không cả khoảng trang.
            label = f"{title} · trang {payload['source_page']}" if isinstance(payload.get("source_page"), int) else source
            out.extend(chunk_block(lesson.id, block.id, payload.get("title", block.id), block_text("theory", payload), label))
    return out


def ai_lesson_titles(db: Session) -> dict[str, str]:
    return {lesson.id: lesson.title for lesson in ai_lessons(db)}


def db_chunks_and_titles() -> tuple[list[Any], dict[str, str]]:
    """Cho chunker: mở phiên riêng; CSDL chưa sẵn sàng (lệnh dựng chỉ mục, test không có bảng) thì trả rỗng."""
    try:
        from ..db.session import SessionLocal

        with SessionLocal() as db:
            return ai_lesson_chunks(db), ai_lesson_titles(db)
    except Exception as exc:   # noqa: BLE001 - kho tĩnh vẫn phải dùng được khi không đọc được CSDL
        log.warning("ai_index_db_unavailable type=%s", type(exc).__name__)
        return [], {}


def invalidate_caches() -> None:
    """Đường dự phòng đọc lại kho ở lần hỏi sau."""
    from ..ai.tutor import retriever

    for fn in (retriever.knowledge_base, retriever._bm25, retriever._cached_vectors):
        fn.cache_clear()


def sync_lesson(db: Session, lesson_id: str) -> dict[str, Any]:
    """Đồng bộ một bài với kho Tutor sau khi Quản trị viên hiện/ẩn. Không bao giờ làm hỏng thao tác hiện/ẩn: lỗi Qdrant
    chỉ được báo lại (và ghi log) để Quản trị viên bấm "Nạp lại vào Tutor"."""
    from ..core.ai_config import pipeline_config, rag_config

    invalidate_caches()
    visible = any(lesson.id == lesson_id for lesson in ai_lessons(db))
    chunks = [c for c in ai_lesson_chunks(db) if c.lesson_id == lesson_id] if visible else []
    out: dict[str, Any] = {"lesson_id": lesson_id, "visible": visible, "chunks": len(chunks), "fallback": "ok"}
    rcfg, pcfg = rag_config(), pipeline_config()
    if not rcfg.qdrant_url or not pcfg.rag_enabled:
        out["qdrant"] = "off"
        return out
    try:
        from ..rag.embedding import get_embedder
        from ..rag.sources import lesson_records
        from ..services.ai_pipeline import _store

        store = _store(rcfg)
        store.delete_lesson("lessons", lesson_id)
        records = [r for r in lesson_records() if r.payload.get("lesson_id") == lesson_id] if visible else []
        if records:
            embedder = get_embedder(rcfg)
            store.upsert(records, embedder.embed([r.text for r in records], "RETRIEVAL_DOCUMENT"), rcfg.upsert_batch)
        out["qdrant"] = "indexed" if records else "removed"
        out["qdrant_points"] = len(records)
    except Exception as exc:   # noqa: BLE001 - Qdrant sập: bài vẫn hiện, đường dự phòng vẫn tìm được bài
        log.warning("ai_index_qdrant_error lesson=%s type=%s", lesson_id, type(exc).__name__)
        out["qdrant"] = "error"
        out["error"] = type(exc).__name__
    return out
