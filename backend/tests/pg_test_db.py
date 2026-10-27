"""CSDL PostgreSQL dùng riêng cho test đồng thời (HM-010).

Test cần tạo và xóa bảng, nên không bao giờ làm việc trên schema `public`: mỗi lần chạy tự tạo một schema
tên ngẫu nhiên, chỉ tạo bảng trong đó và cuối cùng chỉ xóa đúng schema vừa tạo. Trước đó phải qua đủ các
điều kiện ở `unsafe_reason`; thiếu một điều kiện là dừng trước khi tạo engine.
"""

from __future__ import annotations

import re
from uuid import uuid4

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.exc import ArgumentError

SCHEMA_PREFIX = "hm_pgtest_"
_SCHEMA_RE = re.compile(rf"^{SCHEMA_PREFIX}[0-9a-f]{{12}}$")
_LOOPBACK = {"localhost", "127.0.0.1", "::1"}


def _db_identity(url_text: str) -> tuple[str, int, str] | None:
    """(host, port, tên CSDL) của một URL PostgreSQL; None nếu không phải PostgreSQL."""
    url = make_url(url_text)
    if not url.drivername.startswith("postgresql"):
        return None
    host = (url.host or "localhost").lower()
    # localhost và 127.0.0.1 là cùng một máy: so như nhau để không lọt CSDL của app.
    host = "loopback" if host in _LOOPBACK else host
    return host, url.port or 5432, url.database or ""


def unsafe_reason(test_url: str, app_url: str) -> str | None:
    """Lý do KHÔNG được chạy test phá hủy trên test_url; None nghĩa là đủ điều kiện."""
    if not test_url:
        return "Chưa đặt TEST_DATABASE_URL"
    try:
        test_id = _db_identity(test_url)
    except ArgumentError:
        return "TEST_DATABASE_URL không đúng định dạng URL"
    if test_id is None:
        return "TEST_DATABASE_URL phải trỏ tới PostgreSQL (HM-010 không tái hiện được trên SQLite)"
    if not test_id[2].endswith("_test"):
        return "Tên CSDL trong TEST_DATABASE_URL phải kết thúc bằng _test"
    try:
        app_id = _db_identity(app_url) if app_url else None
    except ArgumentError:
        app_id = None
    if app_id is not None and app_id == test_id:
        return "TEST_DATABASE_URL trùng CSDL của ứng dụng (DATABASE_URL)"
    return None


def new_schema_name() -> str:
    return SCHEMA_PREFIX + uuid4().hex[:12]


def create_isolated_engine(test_url: str, schema: str, **engine_kwargs) -> Engine:
    """Tạo schema mới (phải chưa tồn tại) và trả engine mà mọi bảng không ghi schema đều nằm trong nó."""
    if not _SCHEMA_RE.match(schema):
        raise ValueError(f"Tên schema test không hợp lệ: {schema!r}")
    admin = create_engine(test_url, future=True)
    try:
        with admin.begin() as conn:
            exists = conn.execute(text("SELECT 1 FROM information_schema.schemata WHERE schema_name = :s"),
                                  {"s": schema}).first()
            if exists:
                raise RuntimeError(f"Schema {schema} đã tồn tại; dừng để không ghi đè dữ liệu của ai khác")
            conn.execute(text(f'CREATE SCHEMA "{schema}"'))
    finally:
        admin.dispose()
    # search_path chỉ có schema test: bảng tạo ra và câu truy vấn đều không chạm tới public.
    return create_engine(test_url, future=True, connect_args={"options": f"-csearch_path={schema}"},
                         **engine_kwargs)


def drop_isolated_schema(test_url: str, schema: str) -> None:
    """Xóa đúng schema test đã tạo; từ chối mọi tên khác mẫu, nên không thể xóa public hay schema khác."""
    if not _SCHEMA_RE.match(schema):
        raise ValueError(f"Từ chối xóa schema không phải của test: {schema!r}")
    admin = create_engine(test_url, future=True)
    try:
        with admin.begin() as conn:
            conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
    finally:
        admin.dispose()
