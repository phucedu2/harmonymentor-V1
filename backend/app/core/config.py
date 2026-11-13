"""Runtime configuration for the Phase 0.3/0.4 application skeleton.

Production is expected to provide DATABASE_URL for PostgreSQL.  The SQLite default is
intentional for local development and automated tests so the learning contract can be exercised
without an external service.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field


def _flag(name: str, default: str) -> bool:
    return os.getenv(name, default).lower() not in {"0", "false", "no", ""}


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "HarmonyMentor API")
    app_version: str = os.getenv("APP_VERSION", "0.5.4-dev")
    # Dùng `or` vì .env mẫu có dòng `DATABASE_URL=` rỗng; chuỗi rỗng phải rơi về SQLite khi chạy ngoài Docker.
    database_url: str = os.getenv("DATABASE_URL") or "sqlite:///./harmonymentor_dev.db"
    auto_create_schema: bool = os.getenv("AUTO_CREATE_SCHEMA", "1").lower() not in {"0", "false", "no"}
    seed_demo_content: bool = os.getenv("SEED_DEMO_CONTENT", "1").lower() not in {"0", "false", "no"}

    # Xác thực (ADR-004, NFR-18/19). APP_ENV=production bắt buộc có JWT_SECRET.
    app_env: str = os.getenv("APP_ENV", "development")
    jwt_secret: str = os.getenv("JWT_SECRET", "")
    access_token_minutes: int = int(os.getenv("JWT_ACCESS_MINUTES", "30"))
    refresh_token_days: int = int(os.getenv("JWT_REFRESH_DAYS", "7"))
    cookie_secure: bool = _flag("COOKIE_SECURE", "0")
    # Rỗng → bộ đếm khóa đăng nhập dùng bộ nhớ trong (chỉ hợp với 1 tiến trình: dev, test).
    redis_url: str = os.getenv("REDIS_URL", "")
    # Bật khi API đứng sau reverse proxy tin cậy (nginx trong Docker) để lấy IP thật từ X-Forwarded-For.
    trust_proxy: bool = _flag("TRUST_PROXY", "0")
    # Danh sách origin, phân tách bằng dấu phẩy (NFR-21). Rỗng vì frontend gọi API cùng origin.
    cors_origins: str = os.getenv("CORS_ORIGINS", "")
    # Hiện câu hỏi bản nháp (status=draft) cho người học. Chỉ bật tường minh ở dev/test (HM-003, ADR-006).
    show_draft_content: bool = _flag("SHOW_DRAFT_CONTENT", "0")

    # Pipeline AI (GĐ2). Tắt mặc định: AI_ENABLED=false vẫn demo trọn vòng (nguyên tắc 3).
    ai_enabled: bool = _flag("AI_ENABLED", "0")
    # Khóa chỉ đọc từ môi trường của backend; không bao giờ trả về client hay ghi log.
    gemini_api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""), repr=False)
    gemini_embed_model: str = os.getenv("EMBEDDING_MODEL", "gemini-embedding-001")  # tên biến theo 03 Bảng cấu hình
    gemini_embed_dim: int = int(os.getenv("EMBEDDING_DIM", "768"))
    # Bộ nhúng của AI Tutor (ADR-017): local = e5-small chạy cục bộ (mặc định, không cần khóa, chạy cả khi AI tắt),
    # gemini = gemini-embedding (cần khóa), bm25 = không nhúng. Gợi ý bài học vẫn dùng Gemini như GĐ2.
    tutor_embedder: str = os.getenv("TUTOR_EMBEDDER", "local")
    # Mô tả kỹ năng còn nháp (chờ Đạt/Astra duyệt) chỉ dùng cho tầng nội dung khi bật tường minh.
    allow_draft_skill_descriptions: bool = _flag("ALLOW_DRAFT_SKILL_DESCRIPTIONS", "0")
    # Hệ gợi ý (ADR-008 mục 5). Ngưỡng số chiều chung chưa chốt: 3 là giá trị tạm tới khi có thử nghiệm GĐ4.
    rec_min_shared_dims: int = int(os.getenv("RECO_MIN_SHARED_DIMS", "3"))
    rec_fallback: str = os.getenv("RECO_FALLBACK", "a")
    rec_neighbors_k: int = int(os.getenv("RECO_NEIGHBORS_K", "10"))
    reco_use_cf: bool = _flag("RECO_USE_CF", "1")
    # content,mastery,due,cf của công thức đầy đủ (04 mục 6.5); bản người học mới tự suy ra (cộng cf vào content).
    reco_weights: str = os.getenv("RECO_WEIGHTS", "0.35,0.25,0.20,0.20")
    # 9A: dùng người học thật khi có đủ số người có đủ số chiều đã đánh giá, nếu không thì dùng người mô phỏng.
    knn_real_min_users: int = int(os.getenv("KNN_REAL_MIN_USERS", "30"))
    knn_real_min_dims: int = int(os.getenv("KNN_REAL_MIN_DIMS", "3"))
    # AI Tutor (GĐ3). Tên biến theo 03 Bảng cấu hình khi có; mô hình đã xác nhận qua models.list ở GĐ0.
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    gemini_fallback_model: str = os.getenv("GEMINI_FALLBACK_MODEL", "gemini-3.6-flash")
    ai_timeout_seconds: float = float(os.getenv("AI_TIMEOUT_SECONDS", "15"))
    ai_daily_quota: int = int(os.getenv("AI_DAILY_QUOTA", "30"))          # lượt hỏi AI / người / ngày VN
    # Trần chung cả hệ thống / ngày để một sự cố (vòng lặp, bị lạm dụng) không đốt hết hạn mức Gemini.
    ai_global_daily_budget: int = int(os.getenv("AI_GLOBAL_DAILY_BUDGET", "1000"))
    rag_top_k: int = int(os.getenv("RAG_TOP_K", "4"))
    # Hiệu chỉnh ở GĐ3 với gemini-embedding-001 (báo cáo ai-gd3 mục C): câu trong phạm vi ≥ 0,61, ngoài ≤ 0,61.
    rag_min_score: float = float(os.getenv("RAG_MIN_SCORE", "0.60"))
    rag_bm25_min_score: float = float(os.getenv("RAG_BM25_MIN_SCORE", "2.0"))


def check_runtime_settings(cfg: Settings) -> None:
    """Chặn cấu hình nguy hiểm ngay lúc khởi động thay vì để lộ ra khi người học đang dùng."""
    if cfg.app_env == "production" and cfg.show_draft_content:
        raise RuntimeError("SHOW_DRAFT_CONTENT=1 không được dùng khi APP_ENV=production: người học sẽ thấy câu hỏi chưa duyệt.")
    if cfg.app_env == "production" and cfg.allow_draft_skill_descriptions:
        raise RuntimeError("ALLOW_DRAFT_SKILL_DESCRIPTIONS=1 không được dùng khi APP_ENV=production: "
                           "gợi ý sẽ dựa trên mô tả kỹ năng chưa duyệt.")
    try:
        weights = [float(x) for x in cfg.reco_weights.split(",")]
    except ValueError:
        weights = []
    if len(weights) != 4 or any(x < 0 for x in weights) or abs(sum(weights) - 1) > 1e-6:
        raise RuntimeError("RECO_WEIGHTS phải là 4 số không âm có tổng bằng 1, ví dụ 0.35,0.25,0.20,0.20.")
    if cfg.rec_fallback not in {"a", "b"}:
        raise RuntimeError("RECO_FALLBACK chỉ nhận a hoặc b (ADR-008 mục 5).")


settings = Settings()
