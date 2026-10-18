"""Runtime configuration for the Phase 0.3/0.4 application skeleton.

Production is expected to provide DATABASE_URL for PostgreSQL.  The SQLite default is
intentional for local development and automated tests so the learning contract can be exercised
without an external service.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "HarmonyMentor API")
    app_version: str = os.getenv("APP_VERSION", "0.4.0-dev")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./harmonymentor_dev.db")
    auto_create_schema: bool = os.getenv("AUTO_CREATE_SCHEMA", "1").lower() not in {"0", "false", "no"}
    seed_demo_content: bool = os.getenv("SEED_DEMO_CONTENT", "1").lower() not in {"0", "false", "no"}


settings = Settings()
