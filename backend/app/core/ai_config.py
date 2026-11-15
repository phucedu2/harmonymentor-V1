"""Cấu hình AI của đợt góp ý thầy T1–T6: mọi ngưỡng, tên mô hình, kích thước nằm MỘT chỗ, ghi đè bằng biến môi trường.

Vì sao tách khỏi core/config.py: nhóm cần hiệu chỉnh các con số này theo dữ liệu thật (LOW/HIGH, ...) mà không động tới
phần cấu hình chung; test cần dựng cấu hình riêng. Cổng G3–G6 sẽ thêm mục của mình vào cùng file này."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _f(name: str, default: float) -> float:
    return float(os.getenv(name, str(default)))


def _i(name: str, default: int) -> int:
    return int(os.getenv(name, str(default)))


@dataclass(frozen=True)
class RelevanceConfig:
    """Cổng nhạc lý cho tài liệu Admin tải lên (T1)."""

    # Dưới LOW: từ chối. Từ LOW tới dưới HIGH: chờ Admin duyệt. Từ HIGH trở lên: nhận. Giá trị ban đầu, hiệu chỉnh sau.
    low: float = field(default_factory=lambda: _f("RELEVANCE_LOW", 0.35))
    high: float = field(default_factory=lambda: _f("RELEVANCE_HIGH", 0.60))
    # "hybrid" = từ vựng nhạc lý + nhúng so với câu neo; "lexicon" = chỉ từ vựng (không cần mô hình); G6 thêm "classifier".
    scorer: str = field(default_factory=lambda: os.getenv("RELEVANCE_SCORER", "hybrid"))
    lexicon_weight: float = field(default_factory=lambda: _f("RELEVANCE_LEXICON_WEIGHT", 0.5))
    # Cosine e5 bị nén (0,73–0,92 theo GĐ0), nên quy về 0..1 bằng đoạn [emb_floor, emb_ceil] đo trên bộ ca thật.
    emb_floor: float = field(default_factory=lambda: _f("RELEVANCE_EMB_FLOOR", 0.82))
    emb_ceil: float = field(default_factory=lambda: _f("RELEVANCE_EMB_CEIL", 0.92))
    # Mật độ từ khóa trên 100 từ để điểm từ vựng đạt ~0,63; xem scorer.lexicon_score.
    lexicon_density_scale: float = field(default_factory=lambda: _f("RELEVANCE_LEXICON_DENSITY", 3.0))
    min_chars: int = field(default_factory=lambda: _i("RELEVANCE_MIN_CHARS", 120))
    max_bytes: int = field(default_factory=lambda: _i("RELEVANCE_MAX_BYTES", 10 * 1024 * 1024))
    max_text_chars: int = field(default_factory=lambda: _i("RELEVANCE_MAX_TEXT_CHARS", 400_000))
    max_pages: int = field(default_factory=lambda: _i("RELEVANCE_MAX_PAGES", 600))
    # Giới hạn giải nén DOCX/MXL để chặn zip bomb.
    max_unzipped_bytes: int = field(default_factory=lambda: _i("RELEVANCE_MAX_UNZIPPED", 50 * 1024 * 1024))
    # Quá tỉ lệ dòng giống chỉ dẫn tấn công thì từ chối cả tệp.
    max_injection_line_ratio: float = field(default_factory=lambda: _f("RELEVANCE_MAX_INJECTION_RATIO", 0.5))
    ocr_lang: str = field(default_factory=lambda: os.getenv("OCR_LANG", "vie+eng"))
    ocr_max_pages: int = field(default_factory=lambda: _i("OCR_MAX_PAGES", 30))
    # Trang PDF có ít hơn số ký tự này coi là "ảnh quét", thử OCR.
    ocr_min_chars_per_page: int = field(default_factory=lambda: _i("OCR_MIN_CHARS_PER_PAGE", 25))


def relevance_config() -> RelevanceConfig:
    """Đọc lại môi trường mỗi lần gọi để test và Admin đổi ngưỡng không cần khởi động lại."""
    return RelevanceConfig()


@dataclass(frozen=True)
class RagConfig:
    """Kho vector Qdrant và nạp dữ liệu (T3). Mô hình nhúng mặc định là e5-small vì máy nhóm chỉ có CPU và 8 GB RAM."""

    # Rỗng = không dùng Qdrant (AI Tutor tiếp tục dùng e5 + BM25 như trước, ADR-017). Trong Docker compose: http://qdrant:6333.
    qdrant_url: str = field(default_factory=lambda: os.getenv("QDRANT_URL", ""))
    collection: str = field(default_factory=lambda: os.getenv("QDRANT_COLLECTION", "harmony_knowledge"))
    # e5 = multilingual-e5-small (384 chiều, 512 token). Mô hình lớn hơn (bge-m3, 1024 chiều, ~2,3 GB RAM) chưa hỗ trợ ở bản này.
    embedder: str = field(default_factory=lambda: os.getenv("RAG_EMBEDDER", "e5"))
    dim: int = field(default_factory=lambda: _i("RAG_EMBED_DIM", 384))
    # Chia đoạn theo token của mô hình nhúng (e5 đọc tối đa 512 gồm tiền tố), chừa chỗ cho tiêu đề.
    chunk_tokens: int = field(default_factory=lambda: _i("RAG_CHUNK_TOKENS", 320))
    chunk_overlap_tokens: int = field(default_factory=lambda: _i("RAG_CHUNK_OVERLAP", 48))
    top_k: int = field(default_factory=lambda: _i("QDRANT_TOP_K", 5))
    # Cosine e5 bị nén (0,73–0,92), nên ngưỡng 0,80 chỉ là giá trị ban đầu; G5 hiệu chỉnh trên bộ câu chuẩn.
    min_score: float = field(default_factory=lambda: _f("QDRANT_MIN_SCORE", 0.80))
    corpus_dir: str = field(default_factory=lambda: os.getenv("RAG_CORPUS_DIR", "data/corpus/raw"))
    upsert_batch: int = field(default_factory=lambda: _i("RAG_UPSERT_BATCH", 64))


def rag_config() -> RagConfig:
    return RagConfig()


@dataclass(frozen=True)
class PipelineConfig:
    """Pipeline chatbot (T3 phần 2, G4). Mọi cờ đọc lại từ môi trường ở mỗi lần gọi để test và Admin đổi được."""

    # Bật thì bước Retrieve hỏi Qdrant (cần QDRANT_URL và collection đã nạp); tắt hoặc Qdrant lỗi thì dùng đường e5 + BM25 cũ.
    rag_enabled: bool = field(default_factory=lambda: os.getenv("RAG_ENABLED", "0").lower() in ("1", "true", "yes"))
    # Nguồn trong Qdrant mà chatbot được trích. Mặc định chỉ bài học; thêm "corpus" để cho phép tài liệu ngoài.
    rag_sources: tuple[str, ...] = field(default_factory=lambda: tuple(
        s.strip() for s in os.getenv("RAG_SOURCES", "lessons").split(",") if s.strip()))
    rerank_weight: float = field(default_factory=lambda: _f("RAG_RERANK_WEIGHT", 0.15))
    rerank_pool: int = field(default_factory=lambda: _i("RAG_RERANK_POOL", 12))
    # Số lượt hỏi tối đa mỗi người mỗi phút (0 = tắt). Trong bộ nhớ của tiến trình; nhiều worker thì mỗi worker đếm riêng.
    rate_limit_per_min: int = field(default_factory=lambda: _i("CHAT_RATE_LIMIT_PER_MIN", 20))
    # Câu lạc đề: trả lời tối đa chừng này câu rồi dẫn về nhạc lý (Phúc chốt 14/11/2026). "refuse" = từ chối như ADR-020.
    offtopic_mode: str = field(default_factory=lambda: os.getenv("OFFTOPIC_MODE", "brief"))
    offtopic_max_sentences: int = field(default_factory=lambda: _i("OFFTOPIC_MAX_SENTENCES", 2))
    # Bật thì độ tin cậy truy xuất thấp là "mình không biết + gợi ý bài", không để Gemini trả lời bằng kiến thức chung (ADR-020).
    strict_grounding: bool = field(default_factory=lambda: os.getenv("RAG_STRICT_GROUNDING", "0").lower() in ("1", "true", "yes"))
    # Giá mỗi 1 triệu token (USD) để ước tính chi phí trong nhật ký. 0 = chưa cấu hình, không ghi chi phí.
    price_in_per_m: float = field(default_factory=lambda: _f("AI_PRICE_IN_PER_M", 0.0))
    price_out_per_m: float = field(default_factory=lambda: _f("AI_PRICE_OUT_PER_M", 0.0))


def pipeline_config() -> PipelineConfig:
    return PipelineConfig()
