from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from ..core.config import settings
from .base import Base


connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, future=True, pool_pre_ping=True, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, class_=Session)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_schema() -> None:
    # Imported here so SQLAlchemy has registered every table before create_all.
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _check_legacy_users_table()


def _check_legacy_users_table() -> None:
    """create_all không thêm cột vào bảng đã có. File SQLite tạo trước Giai đoạn B thiếu cột xác thực,
    nên báo rõ cách sửa thay vì để lỗi SQL khó hiểu ở lần đăng ký đầu tiên."""
    from sqlalchemy import inspect

    inspector = inspect(engine)
    if "snapshot_origin" not in {c["name"] for c in inspector.get_columns("exercise_versions")}:
        raise RuntimeError(
            "CSDL cũ thiếu cột ảnh chụp của exercise_versions (PR-3, HM-003). Với SQLite dev: xóa file "
            "harmonymentor_dev.db để tạo lại. Với CSDL do Alembic quản lý: chạy `alembic -c alembic.ini upgrade head`."
        )
    columns = {c["name"] for c in inspector.get_columns("users")}
    if "email" not in columns:
        raise RuntimeError(
            "CSDL cũ thiếu cột users.email (tạo trước Giai đoạn B). Với SQLite dev: xóa file harmonymentor_dev.db "
            "để tạo lại. Với CSDL do Alembic quản lý: chạy `alembic -c alembic.ini upgrade head`."
        )
