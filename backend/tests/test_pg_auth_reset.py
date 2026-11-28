"""ADR-040 trên PostgreSQL: nhiều request đặt lại mật khẩu song song với cùng một liên kết, chỉ một cái thắng.

SQLite khóa cả file khi ghi nên không tái hiện được va chạm; ở đây dùng schema tạm như HM-010 (pg_test_db.py).
Ví dụ: TEST_DATABASE_URL=postgresql+psycopg://hm:hm@127.0.0.1:55432/harmony_test pytest -m postgres
"""

from __future__ import annotations

import os
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.auth import account
from app.auth.security import hash_password, verify_password
from app.core.config import settings
from app.db.base import Base
from app.db.models import RefreshToken, User
from app.db.session import get_db
from app.main import app
from tests.pg_test_db import create_isolated_engine, drop_isolated_schema, new_schema_name, unsafe_reason

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "")
WORKERS = 8
UNSAFE_REASON = unsafe_reason(TEST_DATABASE_URL, settings.database_url)
TOKEN_RE = re.compile(r"#token=([A-Za-z0-9_\-]+)")

pytestmark = [
    pytest.mark.postgres,
    pytest.mark.skipif(UNSAFE_REASON is not None, reason=UNSAFE_REASON or ""),
]


@pytest.fixture(scope="module")
def pg_factory():
    schema = new_schema_name()
    engine = create_isolated_engine(TEST_DATABASE_URL, schema, pool_size=WORKERS + 4, max_overflow=4)
    try:
        from app.db import models  # noqa: F401

        Base.metadata.create_all(engine)
        yield sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, class_=Session)
    finally:
        engine.dispose()
        drop_isolated_schema(TEST_DATABASE_URL, schema)


@pytest.fixture()
def pg_client(pg_factory, monkeypatch):
    def override_get_db():
        db = pg_factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    # Việc chạy nền (tra người dùng, tạo token) cũng phải vào schema tạm.
    monkeypatch.setattr(account, "session_factory", pg_factory)
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.pop(get_db, None)


def make_user(factory, password: str = "nhacly2026") -> tuple[str, str]:
    email = f"pg-{uuid4().hex[:10]}@example.com"
    user_id = str(uuid4())
    with factory() as db:
        db.add(User(id=user_id, display_name="PG", email=email, hashed_password=hash_password(password)))
        db.commit()
    return user_id, email


def test_parallel_resets_with_same_link_only_one_succeeds(pg_client, pg_factory, _hop_thu_va_gioi_han_sach):
    outbox = _hop_thu_va_gioi_han_sach
    user_id, email = make_user(pg_factory)
    assert pg_client.post("/api/v1/auth/forgot-password", json={"email": email}).status_code == 202
    token = TOKEN_RE.search([m for m in outbox.outbox if m.to == email][-1].text).group(1)

    barrier = threading.Barrier(WORKERS)

    def task(i: int) -> int:
        barrier.wait()
        return pg_client.post("/api/v1/auth/reset-password",
                              json={"token": token, "new_password": f"songSong{i}x2026"}).status_code

    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        codes = list(pool.map(task, range(WORKERS)))
    assert sorted(codes) == [200] + [400] * (WORKERS - 1), codes

    # Đúng một mật khẩu mới có hiệu lực, và chỉ một thư báo đổi mật khẩu được gửi.
    # Kiểm bằng hash trực tiếp (đăng nhập thử 8 lần sẽ chạm khóa 5 lần sai).
    with pg_factory() as db:
        hashed = db.get(User, user_id).hashed_password
    assert sum(verify_password(f"songSong{i}x2026", hashed) for i in range(WORKERS)) == 1
    assert len([m for m in outbox.outbox if m.to == email and m.subject == "Your password was changed"]) == 1


def test_reset_revokes_refresh_tokens_on_postgres(pg_client, pg_factory, _hop_thu_va_gioi_han_sach):
    outbox = _hop_thu_va_gioi_han_sach
    user_id, email = make_user(pg_factory)
    login = pg_client.post("/api/v1/auth/login", json={"email": email, "password": "nhacly2026"})
    assert login.status_code == 200
    old = {"Authorization": f"Bearer {login.json()['access_token']}"}
    pg_client.post("/api/v1/auth/forgot-password", json={"email": email})
    token = TOKEN_RE.search([m for m in outbox.outbox if m.to == email][-1].text).group(1)
    assert pg_client.post("/api/v1/auth/reset-password",
                          json={"token": token, "new_password": "moiHoan2027"}).status_code == 200
    assert pg_client.get("/api/v1/me", headers=old).status_code == 401
    with pg_factory() as db:
        live = db.scalars(select(RefreshToken).where(RefreshToken.user_id == user_id,
                                                     RefreshToken.revoked_at.is_(None))).all()
        assert live == []
