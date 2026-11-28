"""Migration GĐ1 pipeline AI (c1a2b3d4e5f6): chỉ thêm, khớp model, hạ phiên bản không mất dữ liệu cũ."""

from __future__ import annotations

import sqlalchemy as sa

from tests.test_phuc_music_practice_migration import alembic_to, version

GD1 = "c1a2b3d4e5f6"
SONG_FORM = "b8d5e6f7a9c1"
NEW_TABLES = {"mastery_states", "mastery_events", "placement_results"}


def test_gd1_revision_reachable(tmp_path):
    # Từ GĐ2, head là migration GĐ2; việc khớp model với head nằm ở test_ai_gd2_migration.py.
    engine = sa.create_engine(f"sqlite:///{tmp_path / 'gd1.db'}", future=True)
    try:
        alembic_to(engine, GD1)
        assert version(engine) == GD1
    finally:
        engine.dispose()


def test_upgrade_keeps_old_rows_and_downgrade_removes_only_new(tmp_path):
    engine = sa.create_engine(f"sqlite:///{tmp_path / 'gd1.db'}", future=True)
    try:
        alembic_to(engine, SONG_FORM)
        with engine.begin() as conn:
            conn.execute(sa.text("INSERT INTO users (id, display_name, created_at, role, is_active, is_synthetic) "
                                 "VALUES ('u1', 'cũ', '2026-11-01', 'learner', 1, 0)"))
            conn.execute(sa.text("INSERT INTO skills (id, name, domain) VALUES ('pitch.spelling', 'x', 'foundation')"))
        before = set(sa.inspect(engine).get_table_names())
        alembic_to(engine, GD1)
        insp = sa.inspect(engine)
        assert set(insp.get_table_names()) - before == NEW_TABLES
        with engine.connect() as conn:
            row = conn.execute(sa.text("SELECT ready_threshold, mastery_threshold FROM skills")).one()
            assert tuple(row) == (0.6, 0.8)
            assert conn.execute(sa.text("SELECT count(*) FROM users")).scalar_one() == 1
        alembic_to(engine, SONG_FORM, downgrade=True)
        assert set(sa.inspect(engine).get_table_names()) == before
        assert "is_test" not in {c["name"] for c in sa.inspect(engine).get_columns("attempts")}
        with engine.connect() as conn:
            assert conn.execute(sa.text("SELECT count(*) FROM users")).scalar_one() == 1
    finally:
        engine.dispose()
