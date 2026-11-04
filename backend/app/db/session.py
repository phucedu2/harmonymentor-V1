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
    # Bộ phối khí (02/11/2026, migration a7c4d5e6f8b9): CSDL SQLite dựng bằng create_all trước ngày này thiếu cột
    # seed/energy/mix, mở Harmony Lab sẽ lỗi 500. stamp + upgrade giữ nguyên dữ liệu (đã thử trên bản sao CSDL cũ).
    if "seed" not in {c["name"] for c in inspector.get_columns("composition_projects")}:
        raise RuntimeError(
            "CSDL cũ thiếu cột seed/energy/mix của composition_projects (bộ phối khí, ADR-012). Giữ dữ liệu: "
            "`alembic -c alembic.ini stamp f6a2b3c4d5e7 && alembic -c alembic.ini upgrade head` (CSDL tạo bằng "
            "create_all) hoặc chỉ `alembic -c alembic.ini upgrade head` (CSDL do Alembic quản lý). "
            "Không cần dữ liệu cũ: xóa harmonymentor_dev.db để tạo lại."
        )
    # Chế độ Bài hát (02/11/2026 chiều, migration b8d5e6f7a9c1): thiếu cột form thì Harmony Lab lỗi 500.
    if "form" not in {c["name"] for c in inspector.get_columns("composition_projects")}:
        raise RuntimeError(
            "CSDL cũ thiếu cột form của composition_projects (chế độ Bài hát, ADR-013). Giữ dữ liệu: "
            "`alembic -c alembic.ini upgrade head` (CSDL đã nâng tới a7c4d5e6f8b9). "
            "Không cần dữ liệu cũ: xóa harmonymentor_dev.db để tạo lại."
        )
    # Pipeline AI GĐ1 (04/11/2026, migration c1a2b3d4e5f6): thiếu cột thì mọi lượt làm bài lỗi 500.
    if "is_test" not in {c["name"] for c in inspector.get_columns("attempts")}:
        raise RuntimeError(
            "CSDL cũ thiếu cột attempts.is_test và bảng mastery (pipeline AI GĐ1). Giữ dữ liệu: "
            "`alembic -c alembic.ini upgrade head` rồi `python -m app.ai.rebuild_mastery`. "
            "Không cần dữ liệu cũ: xóa harmonymentor_dev.db để tạo lại."
        )
    columns = {c["name"] for c in inspector.get_columns("users")}
    if "email" not in columns:
        raise RuntimeError(
            "CSDL cũ thiếu cột users.email (tạo trước Giai đoạn B). Với SQLite dev: xóa file harmonymentor_dev.db "
            "để tạo lại. Với CSDL do Alembic quản lý: chạy `alembic -c alembic.ini upgrade head`."
        )
