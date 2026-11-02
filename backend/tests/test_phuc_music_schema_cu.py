"""CSDL dev cũ (thiếu cột bộ phối khí) phải báo rõ cách sửa lúc khởi động, không để /projects trả 500 (02/11/2026)."""
import pytest
from sqlalchemy import create_engine, text

from app.db import session as db_session
from app.db.base import Base
from app.db import models  # noqa: F401


def test_thieu_cot_seed_bao_ro_cach_sua(tmp_path, monkeypatch):
    eng = create_engine(f"sqlite:///{tmp_path / 'cu.db'}")
    Base.metadata.create_all(bind=eng)
    with eng.begin() as c:
        c.execute(text("ALTER TABLE composition_projects DROP COLUMN seed"))
    monkeypatch.setattr(db_session, "engine", eng)
    with pytest.raises(RuntimeError, match="stamp f6a2b3c4d5e7"):
        db_session._check_legacy_users_table()


def test_csdl_moi_khong_bao_loi(tmp_path, monkeypatch):
    eng = create_engine(f"sqlite:///{tmp_path / 'moi.db'}")
    Base.metadata.create_all(bind=eng)
    monkeypatch.setattr(db_session, "engine", eng)
    db_session._check_legacy_users_table()
