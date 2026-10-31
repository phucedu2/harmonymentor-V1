"""phuc-music Bước 2: migration e5f1a2b3c4d6 (practice_attempts) chỉ thêm bảng, khớp model, gỡ được."""

from __future__ import annotations

from pathlib import Path

import sqlalchemy as sa
from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.runtime.migration import MigrationContext

from app.db.base import Base
from app.db import models  # noqa: F401  (đăng ký mọi bảng vào Base.metadata)

BACKEND = Path(__file__).resolve().parents[1]
PR3 = "d3a7f1c2e905"
PRACTICE = "e5f1a2b3c4d6"


def alembic_to(engine: sa.Engine, revision: str, *, downgrade: bool = False) -> None:
    cfg = Config()
    cfg.set_main_option("script_location", str(BACKEND / "migrations"))
    with engine.begin() as connection:
        cfg.attributes["connection"] = connection
        (command.downgrade if downgrade else command.upgrade)(cfg, revision)


def version(engine: sa.Engine) -> str:
    with engine.connect() as conn:
        return conn.execute(sa.text("SELECT version_num FROM alembic_version")).scalar_one()


def test_practice_va_model_khop_migration(tmp_path):
    # Nâng tới đúng migration này (không phải "head"): migration sau (vd dự án Harmony Lab) có test riêng.
    engine = sa.create_engine(f"sqlite:///{tmp_path / 'pm.db'}", future=True)
    try:
        alembic_to(engine, PRACTICE)
        assert version(engine) == PRACTICE
        cols = {c["name"] for c in sa.inspect(engine).get_columns("practice_attempts")}
        assert cols == {"id", "user_id", "kind", "level", "question", "answer", "correct", "primary_error", "is_test", "created_at"}
        # Giống `alembic check`: model và migration không lệch nhau ở bảng mới.
        with engine.connect() as conn:
            diff = compare_metadata(MigrationContext.configure(conn), Base.metadata)
        assert [d for d in diff if "practice_attempts" in str(d)] == []
    finally:
        engine.dispose()


def test_go_migration_chi_xoa_bang_moi(tmp_path):
    engine = sa.create_engine(f"sqlite:///{tmp_path / 'pm.db'}", future=True)
    try:
        alembic_to(engine, PRACTICE)
        tables_before = set(sa.inspect(engine).get_table_names())
        alembic_to(engine, PR3, downgrade=True)
        assert version(engine) == PR3
        assert tables_before - set(sa.inspect(engine).get_table_names()) == {"practice_attempts"}
    finally:
        engine.dispose()
