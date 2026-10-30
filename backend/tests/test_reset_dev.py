"""scripts/reset_dev.py chỉ tạo lại DB dev khi DB không do Alembic quản lý."""

import importlib.util
import sqlite3
from contextlib import closing
from pathlib import Path

_spec = importlib.util.spec_from_file_location("reset_dev", Path(__file__).resolve().parents[2] / "scripts" / "reset_dev.py")
reset_dev = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(reset_dev)


def test_needs_rebuild_only_for_create_all_db(tmp_path):
    db = tmp_path / "dev.db"
    assert not reset_dev.needs_rebuild(db)  # chưa có DB: để Alembic tạo mới

    with closing(sqlite3.connect(db)) as conn:
        conn.execute("CREATE TABLE lessons (id TEXT)")
        conn.commit()
    assert reset_dev.needs_rebuild(db)  # kiểu create_all: thiếu alembic_version

    with closing(sqlite3.connect(db)) as conn:
        conn.execute("CREATE TABLE alembic_version (version_num TEXT)")
        conn.commit()
    assert not reset_dev.needs_rebuild(db)  # Alembic quản lý: giữ dữ liệu, chỉ upgrade
