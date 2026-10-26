"""HM-010 trên CSDL mặc định (SQLite): start/complete gọi lặp lại không đổi lịch sử học.

Phần va chạm đồng thời chỉ tái hiện được trên PostgreSQL, xem test_hm010_lesson_progress_concurrency.py.
"""

from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.db.models import LessonProgress, User
from app.db.session import SessionLocal
from app.main import app
from tests.auth_helpers import answer_lesson_correctly, auth


def make_user() -> str:
    user_id = "hm010s-" + uuid4().hex[:12]
    with SessionLocal() as db:
        db.add(User(id=user_id, display_name="HM-010 SQLite test user"))
        db.commit()
    return user_id


def same_time(a: str, b: str) -> bool:
    # SQLite không lưu múi giờ: giá trị vừa ghi có hậu tố Z, đọc lại thì không. Chỉ so mốc thời gian.
    return a.removesuffix("Z") == b.removesuffix("Z")


def test_complete_again_and_start_again_keep_completed_lesson_unchanged():
    with TestClient(app) as client:
        user_id = make_user()
        headers = auth(user_id)
        started = client.post("/api/v1/lessons/L01/start", json={}, headers=headers)
        assert started.status_code == 200
        answer_lesson_correctly(client, "L01", headers)

        first = client.post("/api/v1/lessons/L01/complete", json={}, headers=headers)
        assert first.status_code == 200 and first.json()["status"] == "completed"
        again = client.post("/api/v1/lessons/L01/complete", json={}, headers=headers)
        assert again.status_code == 200
        assert same_time(again.json()["completed_at"], first.json()["completed_at"])
        assert again.json()["activated_review_items"] == first.json()["activated_review_items"]

        restart = client.post("/api/v1/lessons/L01/start", json={}, headers=headers)
        assert restart.status_code == 200
        assert restart.json()["status"] == "completed"
        assert same_time(restart.json()["started_at"], started.json()["started_at"])
        assert same_time(restart.json()["completed_at"], first.json()["completed_at"])

        with SessionLocal() as db:
            rows = db.scalar(select(func.count()).select_from(LessonProgress).where(
                LessonProgress.user_id == user_id, LessonProgress.lesson_id == "L01"))
        assert rows == 1


def test_complete_without_mastery_creates_no_progress_row():
    """Bài chưa làm đúng hết thì 409 và không để lại dòng tiến độ nào (giữ hành vi cũ)."""
    with TestClient(app) as client:
        user_id = make_user()
        response = client.post("/api/v1/lessons/L02/complete", json={}, headers=auth(user_id))
        assert response.status_code == 409
        with SessionLocal() as db:
            rows = db.scalar(select(func.count()).select_from(LessonProgress).where(
                LessonProgress.user_id == user_id))
        assert rows == 0
