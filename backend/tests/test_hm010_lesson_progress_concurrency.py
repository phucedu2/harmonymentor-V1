"""HM-010: mở bài trên PostgreSQL trả 500 vì hai request start chạy song song cùng chèn lesson_progress.

Chỉ chạy khi TEST_DATABASE_URL trỏ tới một CSDL PostgreSQL riêng cho test (tên kết thúc bằng `_test`, khác
CSDL của app). Bảng được tạo trong một schema tên ngẫu nhiên và chỉ schema đó bị xóa khi xong (pg_test_db.py).
SQLite khóa cả file khi ghi nên không tái hiện được lỗi.
Ví dụ: TEST_DATABASE_URL=postgresql+psycopg://hm:hm@127.0.0.1:55432/harmony_test pytest -m postgres
"""

from __future__ import annotations

import os
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings
from app.db.base import Base
from app.db.models import LessonProgress, ReviewState, User
from app.db.seed import seed_database
from app.db.session import get_db
from app.main import app
from app.services.learning_service import complete_lesson, start_lesson
from tests.auth_helpers import answer_lesson_correctly, auth
from tests.pg_test_db import create_isolated_engine, drop_isolated_schema, new_schema_name, unsafe_reason

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "")
WORKERS = 10
# Kiểm tra trước khi tạo bất kỳ engine nào; không đủ điều kiện thì cả module bị bỏ qua.
UNSAFE_REASON = unsafe_reason(TEST_DATABASE_URL, settings.database_url)

pytestmark = [
    pytest.mark.postgres,
    pytest.mark.skipif(UNSAFE_REASON is not None, reason=UNSAFE_REASON or ""),
]


@pytest.fixture(scope="module")
def pg_schema():
    """(engine, tên schema) của schema test vừa tạo; chỉ schema này bị xóa khi module chạy xong."""
    schema = new_schema_name()
    # Pool đủ lớn để 10 luồng giữ 10 kết nối cùng lúc, nếu không các luồng phải xếp hàng và không còn song song.
    engine = create_isolated_engine(TEST_DATABASE_URL, schema, pool_size=WORKERS + 5, max_overflow=5)
    try:
        with engine.connect() as conn:
            assert conn.execute(text("SELECT current_schema()")).scalar() == schema
        from app.db import models  # noqa: F401  (đăng ký bảng trước create_all)

        Base.metadata.create_all(engine)
        yield engine, schema
    finally:
        engine.dispose()
        drop_isolated_schema(TEST_DATABASE_URL, schema)


@pytest.fixture(scope="module")
def pg_sessionmaker(pg_schema):
    engine, _ = pg_schema
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, class_=Session)
    with factory() as db:
        seed_database(db)
    # Mở sẵn đủ kết nối: nếu không, luồng đầu tiên tốn thời gian bắt tay TCP và các luồng tự xếp hàng.
    warm = [engine.connect() for _ in range(WORKERS)]
    for conn in warm:
        conn.close()
    return factory


@pytest.fixture()
def pg_client(pg_sessionmaker):
    def override_get_db():
        db = pg_sessionmaker()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    # Không dùng `with TestClient(...)` để lifespan không seed vào CSDL mặc định của app.
    # raise_server_exceptions=False để thấy đúng mã HTTP người dùng nhận (500), không phải exception Python.
    yield TestClient(app, raise_server_exceptions=False)
    app.dependency_overrides.pop(get_db, None)


def make_user(factory) -> str:
    user_id = "hm010-" + uuid4().hex[:12]
    with factory() as db:
        db.add(User(id=user_id, display_name="HM-010 test user"))
        db.commit()
    return user_id


def run_concurrently(fn, workers: int = WORKERS) -> list:
    """Chạy fn ở `workers` luồng, thả cùng lúc bằng Barrier để tối đa khả năng va chạm."""
    barrier = threading.Barrier(workers)

    def task(_):
        barrier.wait()
        try:
            return fn()
        except Exception as exc:  # trả lỗi về để assert, không để luồng nuốt mất
            return exc

    with ThreadPoolExecutor(max_workers=workers) as pool:
        return list(pool.map(task, range(workers)))


def count_progress(factory, user_id: str, lesson_id: str) -> int:
    with factory() as db:
        return db.scalar(select(func.count()).select_from(LessonProgress).where(
            LessonProgress.user_id == user_id, LessonProgress.lesson_id == lesson_id))


def count_reviews(factory, user_id: str) -> int:
    with factory() as db:
        return db.scalar(select(func.count()).select_from(ReviewState).where(ReviewState.user_id == user_id))


def test_tables_live_only_in_the_isolated_schema(pg_schema, pg_sessionmaker):
    engine, schema = pg_schema
    with engine.connect() as conn:
        schemas = {row[0] for row in conn.execute(text(
            "SELECT table_schema FROM information_schema.tables WHERE table_name = 'lesson_progress'"))}
        assert schema in schemas
        assert conn.execute(text("SELECT current_schema()")).scalar() == schema


def test_isolated_schema_refuses_existing_schema(pg_schema):
    _, schema = pg_schema
    with pytest.raises(RuntimeError, match="đã tồn tại"):
        create_isolated_engine(TEST_DATABASE_URL, schema)


def test_service_start_lesson_concurrent_creates_single_row(pg_sessionmaker):
    user_id = make_user(pg_sessionmaker)

    def call():
        with pg_sessionmaker() as db:
            return start_lesson(db, user_id, "L01").id

    results = run_concurrently(call)
    errors = [r for r in results if isinstance(r, Exception)]
    assert errors == [], [repr(e) for e in errors]
    assert len(set(results)) == 1
    assert count_progress(pg_sessionmaker, user_id, "L01") == 1


def test_api_start_lesson_10_concurrent_requests_all_200(pg_sessionmaker, pg_client):
    user_id = make_user(pg_sessionmaker)
    headers = auth(user_id)

    results = run_concurrently(lambda: pg_client.post("/api/v1/lessons/L02/start", json={}, headers=headers))
    errors = [r for r in results if isinstance(r, Exception)]
    assert errors == [], [repr(e) for e in errors]
    assert [r.status_code for r in results] == [200] * WORKERS
    assert {r.json()["started_at"] for r in results} == {results[0].json()["started_at"]}
    assert all(r.json()["status"] == "started" for r in results)
    assert count_progress(pg_sessionmaker, user_id, "L02") == 1


def test_start_lesson_keeps_completed_lesson_unchanged(pg_sessionmaker, pg_client):
    user_id = make_user(pg_sessionmaker)
    started = datetime(2026, 10, 1, 8, 0, tzinfo=timezone.utc)
    completed = datetime(2026, 10, 2, 9, 30, tzinfo=timezone.utc)
    with pg_sessionmaker() as db:
        db.add(LessonProgress(user_id=user_id, lesson_id="L03", status="completed",
                              started_at=started, completed_at=completed))
        db.commit()

    results = run_concurrently(lambda: pg_client.post("/api/v1/lessons/L03/start", json={}, headers=auth(user_id)))
    assert [r.status_code for r in results] == [200] * WORKERS
    with pg_sessionmaker() as db:
        row = db.scalar(select(LessonProgress).where(
            LessonProgress.user_id == user_id, LessonProgress.lesson_id == "L03"))
        assert (row.status, row.started_at, row.completed_at) == ("completed", started, completed)
    assert count_progress(pg_sessionmaker, user_id, "L03") == 1


def test_complete_lesson_concurrent_without_start_is_safe(pg_sessionmaker, pg_client):
    """Bấm "Hoàn thành" nhiều lần cùng lúc (chưa từng gọi start): 1 dòng tiến độ, thẻ ôn không trùng."""
    user_id = make_user(pg_sessionmaker)
    headers = auth(user_id)
    answer_lesson_correctly(pg_client, "L01", headers)

    results = run_concurrently(lambda: pg_client.post("/api/v1/lessons/L01/complete", json={}, headers=headers))
    errors = [r for r in results if isinstance(r, Exception)]
    assert errors == [], [repr(e) for e in errors]
    assert [r.status_code for r in results] == [200] * WORKERS
    assert {r.json()["completed_at"] for r in results} == {results[0].json()["completed_at"]}
    assert count_progress(pg_sessionmaker, user_id, "L01") == 1
    assert count_reviews(pg_sessionmaker, user_id) == results[0].json()["activated_review_items"] > 0


def test_complete_not_mastered_10_concurrent_all_409_and_leaves_nothing(pg_sessionmaker, pg_client):
    user_id = make_user(pg_sessionmaker)
    results = run_concurrently(lambda: pg_client.post("/api/v1/lessons/L01/complete", json={}, headers=auth(user_id)))
    assert [r.status_code for r in results] == [409] * WORKERS
    assert count_progress(pg_sessionmaker, user_id, "L01") == 0
    assert count_reviews(pg_sessionmaker, user_id) == 0


def test_start_and_complete_concurrently_end_completed_single_row(pg_sessionmaker, pg_client):
    """5 lượt start + 5 lượt complete cùng lúc khi chưa có dòng tiến độ; lặp vài người để tăng va chạm."""
    for _ in range(5):
        user_id = make_user(pg_sessionmaker)
        headers = auth(user_id)
        answer_lesson_correctly(pg_client, "L01", headers)
        kinds = iter(["start", "complete"] * (WORKERS // 2))
        lock = threading.Lock()

        def call():
            with lock:
                kind = next(kinds)
            return kind, pg_client.post(f"/api/v1/lessons/L01/{kind}", json={}, headers=headers)

        results = run_concurrently(call)
        errors = [r for r in results if isinstance(r, Exception)]
        assert errors == [], [repr(e) for e in errors]
        assert [response.status_code for _, response in results] == [200] * WORKERS
        completes = [response.json() for kind, response in results if kind == "complete"]
        assert len({c["completed_at"] for c in completes}) == 1
        with pg_sessionmaker() as db:
            row = db.scalar(select(LessonProgress).where(
                LessonProgress.user_id == user_id, LessonProgress.lesson_id == "L01"))
            assert row.status == "completed" and row.completed_at is not None
        assert count_progress(pg_sessionmaker, user_id, "L01") == 1
        assert count_reviews(pg_sessionmaker, user_id) == completes[0]["activated_review_items"] > 0


def test_complete_lesson_again_keeps_original_completed_at(pg_sessionmaker):
    user_id = make_user(pg_sessionmaker)
    completed = datetime(2026, 10, 2, 9, 30, tzinfo=timezone.utc)
    with pg_sessionmaker() as db:
        db.add(LessonProgress(user_id=user_id, lesson_id="L04", status="completed",
                              started_at=completed, completed_at=completed))
        db.commit()
    with pg_sessionmaker() as db:
        progress, _ = complete_lesson(db, user_id, "L04")
        assert progress.completed_at == completed
