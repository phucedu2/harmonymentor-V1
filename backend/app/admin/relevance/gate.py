"""Cổng nhạc lý: tệp/chữ -> quyết định nhận / chờ duyệt / từ chối, kèm lý do tiếng Việt."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ...core.ai_config import RelevanceConfig, relevance_config
from .clean import clean_text, strip_injection
from .errors import RelevanceError
from .extract import Extracted, extract, split_text
from .scorer import RelevanceScorer, default_scorer

ACCEPTED, PENDING, REJECTED = "accepted", "pending", "rejected"


@dataclass
class GateResult:
    status: str
    score: float
    reason_vi: str
    kind: str
    pages: list[str]                      # đã làm sạch; trang lạc đề đã bị bỏ trống
    detail: dict[str, Any] = field(default_factory=dict)


def decide(score: float, cfg: RelevanceConfig) -> str:
    if score < cfg.low:
        return REJECTED
    return PENDING if score < cfg.high else ACCEPTED


MAX_SCORED_CHUNKS = 150     # quá số đoạn này thì chấm theo trang để giữ thời gian xử lý


def chunk_page(page: str, target: int = 200) -> list[str]:
    """Gộp các đoạn văn liền nhau thành khối cỡ ~target ký tự để chấm điểm từng khối (bắt được tài liệu lẫn lộn)."""
    chunks, cur = [], ""
    for para in (p.strip() for p in page.split("\n\n")):
        if not para:
            continue
        cur = f"{cur}\n\n{para}" if cur else para
        if len(cur) >= target:
            chunks.append(cur)
            cur = ""
    if cur:
        if chunks and len(cur) < target // 2:
            chunks[-1] = f"{chunks[-1]}\n\n{cur}"    # khối đuôi quá ngắn thì nối vào khối trước, tránh điểm nhiễu
        else:
            chunks.append(cur)
    return chunks


def _reason(status: str, score: float, cfg: RelevanceConfig, dropped: int, notes: list[str]) -> str:
    pct = round(score * 100)
    if status == REJECTED:
        text = (f"Nội dung không liên quan nhạc lý hoặc hòa âm (điểm {pct}/100, ngưỡng tối thiểu {round(cfg.low * 100)}). "
                "Hãy tải tài liệu về hợp âm, quãng, âm giai, nhịp, chức năng hòa âm...")
    elif status == PENDING:
        text = (f"Chưa chắc tài liệu này về nhạc lý (điểm {pct}/100, giữa {round(cfg.low * 100)} và {round(cfg.high * 100)}). "
                "Đã đưa vào hàng chờ duyệt: Quản trị viên xem lại rồi duyệt hoặc từ chối.")
    else:
        text = f"Tài liệu liên quan nhạc lý (điểm {pct}/100)."
    if dropped and status != REJECTED:
        text += f" Đã bỏ {dropped} đoạn không liên quan nhạc lý."
    return " ".join([text, *notes])


def evaluate(ex: Extracted, scorer: RelevanceScorer | None = None, cfg: RelevanceConfig | None = None) -> GateResult:
    cfg = cfg or relevance_config()
    scorer = scorer or default_scorer(cfg)
    notes = list(ex.notes)
    pages: list[str] = []
    removed = total_lines = 0
    for page in ex.pages:
        cleaned, dropped, lines = strip_injection(clean_text(page)[: cfg.max_text_chars])
        pages.append(cleaned)
        removed, total_lines = removed + dropped, total_lines + lines
    if total_lines and removed / total_lines > cfg.max_injection_line_ratio:
        raise RelevanceError("INJECTION", "Tài liệu chứa nhiều dòng giống chỉ dẫn điều khiển AI (ví dụ “bỏ qua chỉ dẫn trước”), không nhận.")
    if removed:
        notes.append(f"Đã bỏ {removed} dòng giống chỉ dẫn điều khiển AI.")

    non_empty = [(i, p) for i, p in enumerate(pages) if p.strip()]
    total_chars = sum(len(p) for _, p in non_empty)
    if not ex.music_native and total_chars < cfg.min_chars:
        raise RelevanceError("TOO_SHORT", f"Chữ quá ngắn ({total_chars} ký tự) để đánh giá có liên quan nhạc lý hay không; cần ít nhất {cfg.min_chars} ký tự.")

    if ex.music_native:
        # MusicXML/MIDI tự nó là dữ liệu âm nhạc: không cần đoán từ chữ mô tả.
        score, lex, emb, dropped_chunks, dropped_pages = 1.0, 1.0, None, 0, []
        page_scores = {i: 1.0 for i, _ in non_empty}
    else:
        chunked = {i: chunk_page(p) for i, p in non_empty}
        if sum(len(c) for c in chunked.values()) > MAX_SCORED_CHUNKS:      # tài liệu rất dài: chấm theo trang cho nhẹ
            chunked = {i: [p] for i, p in non_empty}
        scored: dict[int, list[tuple[str, float]]] = {i: [(c, scorer.score(c).value) for c in cs] for i, cs in chunked.items()}
        weight = sum(len(c) for cs in scored.values() for c, _ in cs)
        score = sum(len(c) * v for cs in scored.values() for c, v in cs) / weight
        page_scores = {i: sum(len(c) * v for c, v in cs) / sum(len(c) for c, _ in cs) for i, cs in scored.items()}
        lex = emb = None
        dropped_chunks, dropped_pages = 0, []
    status = decide(score, cfg)
    if status != REJECTED and not ex.music_native:
        # Chỉ phần liên quan nhạc lý được giữ lại cho bộ sinh bài; đoạn lạc đề (ví dụ công thức nấu ăn) bị bỏ.
        for i, cs in scored.items():
            kept = [c for c, v in cs if v >= cfg.low]
            dropped_chunks += len(cs) - len(kept)
            pages[i] = "\n\n".join(kept)
            if not kept:
                dropped_pages.append(i + 1)
    detail = {"scorer": getattr(scorer, "name", "?") if not ex.music_native else "music-native",
              "low": cfg.low, "high": cfg.high, "page_scores": {str(i + 1): round(v, 3) for i, v in page_scores.items()},
              "dropped_pages": dropped_pages, "dropped_chunks": dropped_chunks, "injection_lines_removed": removed, "notes": notes}
    return GateResult(status, round(score, 3), _reason(status, score, cfg, dropped_chunks, notes), ex.kind, pages, detail)


def evaluate_file(filename: str, data: bytes, scorer: RelevanceScorer | None = None, cfg: RelevanceConfig | None = None) -> GateResult:
    return evaluate(extract(filename, data), scorer, cfg)


def evaluate_pasted_text(text: str, scorer: RelevanceScorer | None = None, cfg: RelevanceConfig | None = None) -> GateResult:
    cfg = cfg or relevance_config()
    if not text or not text.strip():
        raise RelevanceError("FILE_EMPTY", "Chưa có chữ nào để đánh giá.")
    if len(text) > cfg.max_text_chars:
        raise RelevanceError("FILE_TOO_BIG", f"Chữ dán vào dài hơn {cfg.max_text_chars} ký tự.", 413)
    return evaluate(Extracted("paste", split_text(text)), scorer, cfg)
