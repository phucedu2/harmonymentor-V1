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
