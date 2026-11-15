"""Đọc nguồn để nạp vào Qdrant: bài học đã phát hành và kho tài liệu thô (data/corpus/raw, không nằm trong git)."""

from __future__ import annotations

import json
from pathlib import Path

from ..admin.relevance.errors import RelevanceError
from ..admin.relevance.extract import extract
from ..ai.tutor.chunker import lesson_chunks, lesson_titles
from ..core.ai_config import RagConfig
from .chunker import TokenCounter, chunk_text, dedupe, text_hash
from .store import Record, point_id

SIDECAR = ".meta.json"
SUPPORTED = {".pdf", ".docx", ".png", ".jpg", ".jpeg", ".xml", ".musicxml", ".mxl", ".mid", ".midi", ".md", ".txt"}


def lesson_records() -> list[Record]:
    """Mỗi đoạn bài học = một điểm. Chỉ bài đã phát hành, không nháp, không đề/đáp án (do lesson_chunks lọc sẵn)."""
    titles = lesson_titles()
    out = []
    for i, c in enumerate(lesson_chunks()):
        out.append(Record(
            id=point_id("lessons", f"{c.lesson_id}/{c.block_id}", i, c.content_hash),
            text=c.embed_text(titles.get(c.lesson_id, "")),
            payload={"source": "lessons", "lesson_id": c.lesson_id, "block_id": c.block_id, "title": c.title,
                     "lang": "vi", "chunk_idx": i, "license": c.source, "text": c.text}))
    return out


def corpus_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in SUPPORTED)


def _meta(path: Path) -> dict:
    side = path.with_name(path.name + SIDECAR)
    if side.exists():
        try:
            return json.loads(side.read_text(encoding="utf-8"))
        except ValueError:
            return {}
    return {}


def corpus_records(cfg: RagConfig, counter: TokenCounter) -> tuple[list[Record], list[str]]:
    """Trả (bản ghi, cảnh báo). Tệp lỗi hoặc rỗng bị bỏ qua và ghi vào cảnh báo, không làm hỏng cả lần nạp."""
    root, warns, out = Path(cfg.corpus_dir), [], []
    for path in corpus_files(root):
        rel = path.relative_to(root).as_posix()
        meta = _meta(path)
        try:
            ex = extract(path.name, path.read_bytes())
        except RelevanceError as e:
            warns.append(f"{rel}: bỏ qua ({e.code})")
            continue
        title = meta.get("title") or path.stem
        chunks = dedupe([c for page in ex.pages for c in chunk_text(page, title, counter, cfg.chunk_tokens, cfg.chunk_overlap_tokens)])
        if not chunks:
            warns.append(f"{rel}: không có chữ để nạp")
            continue
        for c in chunks:
            out.append(Record(
                id=point_id("corpus", rel, c.index, text_hash(c.text)),
                text=f"{title}\n{c.text}",   # tiêu đề đi cùng đoạn khi nhúng; chunk_text đã chừa chỗ
                payload={"source": "corpus", "lesson_id": meta.get("lesson_id", ""), "block_id": rel, "title": title,
                         "lang": meta.get("lang", "vi"), "chunk_idx": c.index,
                         "license": meta.get("license", "chưa ghi"), "text": c.text}))
    return out, warns
