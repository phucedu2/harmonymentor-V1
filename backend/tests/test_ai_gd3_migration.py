"""Migration GĐ3 pipeline AI (e3c4d5e6f7a8): chỉ thêm ba bảng chat, khớp model, hạ phiên bản giữ dữ liệu cũ."""

from __future__ import annotations

import sqlalchemy as sa
from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext

from app.db import models  # noqa: F401
from app.db.base import Base
from tests.test_phuc_music_practice_migration import alembic_to, version

GD2 = "d2b3c4d5e6f7"
GD3 = "e3c4d5e6f7a8"
CHAT = {"chat_sessions", "chat_messages", "chat_feedback"}


def test_head_matches_model(tmp_path):
    engine = sa.create_engine(f"sqlite:///{tmp_path / 'gd3.db'}", future=True)
    try:
        alembic_to(engine, "head")
        assert version(engine) == "f4d5e6f7a8b9"  # head hiện tại: migration Quản trị
        with engine.connect() as conn:
            diff = compare_metadata(MigrationContext.configure(conn), Base.metadata)
        assert diff == [], diff
    finally:
        engine.dispose()


def test_upgrade_adds_only_chat_tables_and_downgrade_keeps_old_rows(tmp_path):
    engine = sa.create_engine(f"sqlite:///{tmp_path / 'gd3.db'}", future=True)
    try:
        alembic_to(engine, GD2)
        with engine.begin() as conn:
            conn.execute(sa.text("INSERT INTO users (id, display_name, created_at, role, is_active, is_synthetic, goal_text) "
                                 "VALUES ('u1', 'cũ', '2026-11-01', 'learner', 1, 0, 'đệm hát pop')"))
        before = set(sa.inspect(engine).get_table_names())
        alembic_to(engine, GD3)
        assert set(sa.inspect(engine).get_table_names()) - before == CHAT
        alembic_to(engine, GD2, downgrade=True)
        assert set(sa.inspect(engine).get_table_names()) == before
        with engine.connect() as conn:
            assert conn.execute(sa.text("SELECT goal_text FROM users")).scalar_one() == "đệm hát pop"
    finally:
        engine.dispose()
