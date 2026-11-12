"""phuc-music Bước 4: migration f6a2b3c4d5e7 (dự án Harmony Lab) chỉ thêm 3 bảng, khớp model, gỡ được."""

from __future__ import annotations

import sqlalchemy as sa
from alembic.autogenerate import compare_metadata
from alembic.runtime.migration import MigrationContext

from app.db.base import Base
from app.db import models  # noqa: F401
from tests.test_phuc_music_practice_migration import PRACTICE, alembic_to, version

COMPOSITION = "f6a2b3c4d5e7"
ARRANGEMENT = "a7c4d5e6f8b9"  # 02/11: seed, energy, mix, arrangement_version (ADR-012 đề xuất)
SONG_FORM = "b8d5e6f7a9c1"  # 02/11 chiều: cột JSON form cho chế độ Bài hát (ADR-013 đề xuất)
TABLES = {"composition_projects", "chord_events", "drum_events"}


def test_head_la_composition_va_model_khop_migration(tmp_path):
    # Từ 04/11 head là migration GĐ1 pipeline AI (c1a2b3d4e5f6, chỉ thêm, có test riêng), nên dừng ở SONG_FORM.
    engine = sa.create_engine(f"sqlite:///{tmp_path / 'hl.db'}", future=True)
    try:
        alembic_to(engine, SONG_FORM)
        assert version(engine) == SONG_FORM
        cols = {c["name"] for c in sa.inspect(engine).get_columns("composition_projects")}
        assert cols == {"id", "user_id", "name", "key", "tempo_bpm", "time_signature", "bars", "style", "is_test",
                        "created_at", "updated_at", "deleted_at", "seed", "energy", "mix", "arrangement_version", "form"}
        with engine.connect() as conn:
            diff = compare_metadata(MigrationContext.configure(conn), Base.metadata)
        assert [d for d in diff if any(t in str(d) for t in TABLES)] == []
    finally:
        engine.dispose()


def test_go_migration_chi_xoa_ba_bang_moi(tmp_path):
    engine = sa.create_engine(f"sqlite:///{tmp_path / 'hl.db'}", future=True)
    try:
        alembic_to(engine, SONG_FORM)
        before = set(sa.inspect(engine).get_table_names())
        alembic_to(engine, PRACTICE, downgrade=True)
        assert version(engine) == PRACTICE
        assert before - set(sa.inspect(engine).get_table_names()) == TABLES
    finally:
        engine.dispose()
