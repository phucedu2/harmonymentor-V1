"""Runtime configuration for the Phase 0.3/0.4 application skeleton.

Production is expected to provide DATABASE_URL for PostgreSQL.  The SQLite default is
intentional for local development and automated tests so the learning contract can be exercised
without an external service.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


def _flag(name: str, default: str) -> bool:
    return os.getenv(name, default).lower() not in {"0", "false", "no", ""}


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "HarmonyMentor API")
    app_version: str = os.getenv("APP_VERSION", "0.4.0-dev")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./harmonymentor_dev.db")
    auto_create_schema: bool = os.getenv("AUTO_CREATE_SCHEMA", "1").lower() not in {"0", "false", "no"}
    seed_demo_content: bool = os.getenv("SEED_DEMO_CONTENT", "1").lower() not in {"0", "false", "no"}

    # Xác thực (ADR-004, NFR-18/19). APP_ENV=production bắt buộc có JWT_SECRET.
    app_env: str = os.getenv("APP_ENV", "development")
    jwt_secret: str = os.getenv("JWT_SECRET", "")
    access_token_minutes: int = int(os.getenv("ACCESS_TOKEN_MINUTES", "30"))
    refresh_token_days: int = int(os.getenv("REFRESH_TOKEN_DAYS", "7"))
    cookie_secure: bool = _flag("COOKIE_SECURE", "0")
    # Rỗng → bộ đếm khóa đăng nhập dùng bộ nhớ trong (chỉ hợp với 1 tiến trình: dev, test).
    redis_url: str = os.getenv("REDIS_URL", "")
    # Bật khi API đứng sau reverse proxy tin cậy (nginx trong Docker) để lấy IP thật từ X-Forwarded-For.
    trust_proxy: bool = _flag("TRUST_PROXY", "0")


settings = Settings()
