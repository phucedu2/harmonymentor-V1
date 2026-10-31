"""phuc-music Bước 4: migration f6a2b3c4d5e7 (dự án Harmony Lab) chỉ thêm 3 bảng, khớp model, gỡ được."""

from __future__ import annotations

import sqlalchemy as sa
from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext

from app.db.base import Base
from app.db import models  # noqa: F401
from tests.test_phuc_music_practice_migration import PRACTICE, alembic_to, version

COMPOSITION = "f6a2b3c4d5e7"
TABLES = {"composition_projects", "chord_events", "drum_events"}


def test_head_la_composition_va_model_khop_migration(tmp_path):
    engine = sa.create_engine(f"sqlite:///{tmp_path / 'hl.db'}", future=True)
    try:
        alembic_to(engine, "head")
        assert version(engine) == COMPOSITION
        cols = {c["name"] for c in sa.inspect(engine).get_columns("composition_projects")}
        assert cols == {"id", "user_id", "name", "key", "tempo_bpm", "time_signature", "bars", "style", "is_test",
                        "created_at", "updated_at", "deleted_at"}
        with engine.connect() as conn:
            diff = compare_metadata(MigrationContext.configure(conn), Base.metadata)
        assert [d for d in diff if any(t in str(d) for t in TABLES)] == []
    finally:
        engine.dispose()


def test_go_migration_chi_xoa_ba_bang_moi(tmp_path):
    engine = sa.create_engine(f"sqlite:///{tmp_path / 'hl.db'}", future=True)
    try:
        alembic_to(engine, "head")
        before = set(sa.inspect(engine).get_table_names())
        alembic_to(engine, PRACTICE, downgrade=True)
        assert version(engine) == PRACTICE
        assert before - set(sa.inspect(engine).get_table_names()) == TABLES
    finally:
        engine.dispose()
