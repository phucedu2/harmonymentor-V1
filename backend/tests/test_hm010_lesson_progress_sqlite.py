"""HM-010 trên CSDL mặc định (SQLite): start/complete gọi lặp lại không đổi lịch sử học.

Phần va chạm đồng thời chỉ tái hiện được trên PostgreSQL, xem test_hm010_lesson_progress_concurrency.py.
"""

from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.db.models import LessonProgress, ReviewItem, ReviewState, User
from app.db.session import SessionLocal
from app.main import app
from tests.auth_helpers import answer_lesson_correctly, auth, correct_answer


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


def progress_snapshot(user_id: str, lesson_id: str):
    with SessionLocal() as db:
        row = db.scalar(select(LessonProgress).where(
            LessonProgress.user_id == user_id, LessonProgress.lesson_id == lesson_id))
        return None if row is None else (row.status, row.started_at, row.completed_at)


def review_snapshot(user_id: str) -> list[tuple]:
    with SessionLocal() as db:
        rows = db.scalars(select(ReviewState).where(ReviewState.user_id == user_id).order_by(ReviewState.id)).all()
        return [(r.review_item_id, r.status, r.stage, r.interval_days, r.due_at, r.success_streak,
                 r.failure_count, r.last_reviewed_at) for r in rows]


def test_complete_without_mastery_creates_no_progress_row():
    """Bài chưa làm đúng hết thì 409 và không để lại dòng tiến độ hay thẻ ôn nào (giữ hành vi cũ)."""
    with TestClient(app) as client:
        user_id = make_user()
        response = client.post("/api/v1/lessons/L02/complete", json={}, headers=auth(user_id))
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "LESSON_NOT_MASTERED"
        with SessionLocal() as db:
            rows = db.scalar(select(func.count()).select_from(LessonProgress).where(
                LessonProgress.user_id == user_id))
        assert rows == 0
        assert review_snapshot(user_id) == []


def test_complete_without_mastery_after_start_keeps_started_row():
    """Đã mở bài rồi bấm hoàn thành khi còn câu sai: dòng vẫn "started", không có completed_at, không có thẻ ôn."""
    with TestClient(app) as client:
        user_id = make_user()
        headers = auth(user_id)
        assert client.post("/api/v1/lessons/L01/start", json={}, headers=headers).status_code == 200
        before = progress_snapshot(user_id, "L01")
        response = client.post("/api/v1/lessons/L01/complete", json={}, headers=headers)
        assert response.status_code == 409
        assert progress_snapshot(user_id, "L01") == before
        assert before[0] == "started" and before[2] is None
        assert review_snapshot(user_id) == []


def test_recomplete_after_reviews_keeps_completion_and_leitner_state():
    """Đã ôn thẻ (lên hộp, có lần sai) rồi hoàn thành lại và mở lại bài: tiến độ và thẻ ôn giữ nguyên."""
    with TestClient(app) as client:
        user_id = make_user()
        headers = auth(user_id)
        answer_lesson_correctly(client, "L01", headers)
        assert client.post("/api/v1/lessons/L01/complete", json={}, headers=headers).status_code == 200

        with SessionLocal() as db:
            items = db.scalars(select(ReviewItem).where(ReviewItem.lesson_id == "L01").order_by(ReviewItem.id)).all()
            reviews = [(item.id, correct_answer({"answer_key": item.answer_key}), "good") for item in items[:3]]
            reviews.append((items[3].id, "sai-có-chủ-đích", "auto"))
        for item_id, answer, rating in reviews:
            reply = client.post(f"/api/v1/review/{item_id}/answer", json={"answer": answer, "rating": rating},
                                headers=headers)
            assert reply.status_code == 200, reply.json()

        progress_before = progress_snapshot(user_id, "L01")
        states_before = review_snapshot(user_id)
        # Phép thử chỉ có nghĩa khi thẻ đã rời trạng thái ban đầu: có thẻ lên hộp và có thẻ bị tính sai.
        assert any(state[2] > 0 for state in states_before)
        assert any(state[6] > 0 for state in states_before)

        assert client.post("/api/v1/lessons/L01/complete", json={}, headers=headers).status_code == 200
        assert client.post("/api/v1/lessons/L01/start", json={}, headers=headers).status_code == 200
        assert client.post("/api/v1/lessons/L01/complete", json={}, headers=headers).status_code == 200

        assert progress_snapshot(user_id, "L01") == progress_before
        assert review_snapshot(user_id) == states_before
