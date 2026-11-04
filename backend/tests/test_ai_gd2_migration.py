"""Migration GĐ2 pipeline AI (d2b3c4d5e6f7): chỉ thêm, khớp model, hạ phiên bản giữ dữ liệu cũ."""

from __future__ import annotations

import sqlalchemy as sa
from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext

from app.db import models  # noqa: F401
from app.db.base import Base
from tests.test_phuc_music_practice_migration import alembic_to, version

GD1 = "c1a2b3d4e5f6"
GD2 = "d2b3c4d5e6f7"


def test_head_is_gd2_and_model_matches(tmp_path):
    engine = sa.create_engine(f"sqlite:///{tmp_path / 'gd2.db'}", future=True)
    try:
        alembic_to(engine, "head")
        assert version(engine) == GD2
        with engine.connect() as conn:
            diff = compare_metadata(MigrationContext.configure(conn), Base.metadata)
        assert diff == [], diff
    finally:
        engine.dispose()


def test_upgrade_keeps_goal_text_and_downgrade_removes_only_new(tmp_path):
    engine = sa.create_engine(f"sqlite:///{tmp_path / 'gd2.db'}", future=True)
    try:
        alembic_to(engine, GD1)
        with engine.begin() as conn:
            conn.execute(sa.text("INSERT INTO users (id, display_name, created_at, role, is_active, is_synthetic, goal_text) "
                                 "VALUES ('u1', 'cũ', '2026-11-01', 'learner', 1, 0, 'đệm hát pop')"))
        before = set(sa.inspect(engine).get_table_names())
        alembic_to(engine, "head")
        assert set(sa.inspect(engine).get_table_names()) - before == {"recommendation_logs"}
        with engine.connect() as conn:
            row = conn.execute(sa.text("SELECT goal_text, goal_embedding FROM users")).one()
            assert tuple(row) == ("đệm hát pop", None)
        alembic_to(engine, GD1, downgrade=True)
        assert set(sa.inspect(engine).get_table_names()) == before
        cols = {c["name"] for c in sa.inspect(engine).get_columns("users")}
        assert "goal_embedding" not in cols and "goal_text" in cols
        with engine.connect() as conn:
            assert conn.execute(sa.text("SELECT goal_text FROM users")).scalar_one() == "đệm hát pop"
    finally:
        engine.dispose()
