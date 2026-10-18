"""Phase 0.3/0.4 contract tests: Content -> Attempt -> ReviewState."""

from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from app.db.models import User
from app.db.session import SessionLocal
from app.main import app


def make_user() -> str:
    user_id = "test-" + uuid4().hex[:12]
    with SessionLocal() as db:
        db.add(User(id=user_id, display_name="Phase04 test user"))
        db.commit()
    return user_id


def test_lesson_index_and_lesson1_content_are_served_from_backend():
    with TestClient(app) as client:
        index = client.get("/api/v1/lessons")
        assert index.status_code == 200
        lessons = index.json()
        assert len(lessons) == 8
        l01 = next(x for x in lessons if x["id"] == "L01")
        assert l01["exercise_count"] == 6
        assert l01["review_item_count"] == 8
        assert l01["block_count"] == 7

        detail = client.get("/api/v1/lessons/L01")
        assert detail.status_code == 200
        body = detail.json()
        assert len(body["exercises"]) == 6
        assert len(body["review_items"]) == 8
        assert len(body["sources"]) == 4
        # Quiz answer keys are server-side only.
        assert "answer_key" not in detail.text
        assert "grader_config" not in detail.text


def test_attempt_contract_handles_exact_and_music_engine_grading():
    with TestClient(app) as client:
        user_id = make_user()

        good_interval = client.post("/api/v1/attempts", json={
            "user_id": user_id, "exercise_version_id": "L01-Q01-v2", "answer": "M3"
        })
        assert good_interval.status_code == 200
        assert good_interval.json()["correct"] is True

        wrong_case_is_wrong_quality = client.post("/api/v1/attempts", json={
            "user_id": user_id, "exercise_version_id": "L01-Q01-v2", "answer": "m3"
        })
        assert wrong_case_is_wrong_quality.status_code == 200
        assert wrong_case_is_wrong_quality.json()["correct"] is False

        good_chord = client.post("/api/v1/attempts", json={
            "user_id": user_id, "exercise_version_id": "L01-Q02-v2", "answer": "C E G"
        })
        assert good_chord.status_code == 200
        assert good_chord.json()["correct"] is True

        extra_note = client.post("/api/v1/attempts", json={
            "user_id": user_id, "exercise_version_id": "L01-Q02-v2", "answer": "C E G G#"
        })
        assert extra_note.status_code == 200
        assert extra_note.json()["correct"] is False
        assert extra_note.json()["primary_error"] == "EXTRA_TONE"


def test_complete_lesson_activates_review_states_idempotently():
    with TestClient(app) as client:
        user_id = make_user()
        first = client.post("/api/v1/lessons/L01/complete", json={"user_id": user_id})
        assert first.status_code == 200
        body = first.json()
        assert body["status"] == "completed"
        assert body["activated_review_items"] == 8
        assert body["first_review_due_at"] is not None

        second = client.post("/api/v1/lessons/L01/complete", json={"user_id": user_id})
        assert second.status_code == 200
        assert second.json()["activated_review_items"] == 8

        reviews = client.get("/api/v1/review/due", params={"user_id": user_id, "include_future": "true"})
        assert reviews.status_code == 200
        assert len(reviews.json()) == 8
        assert {x["review_item_id"] for x in reviews.json()} == {f"L01-F{i:02d}" for i in range(1, 9)}


def test_review_answer_advances_1_3_7_14_30_schedule():
    with TestClient(app) as client:
        user_id = make_user()
        client.post("/api/v1/lessons/L01/complete", json={"user_id": user_id})

        result = client.post("/api/v1/review/L01-F01/answer", json={
            "user_id": user_id, "answer": "M3", "rating": "auto", "response_time_ms": 1800
        })
        assert result.status_code == 200
        body = result.json()
        assert body["correct"] is True
        assert body["rating_applied"] == "good"
        assert body["next_stage"] == 1
        assert body["interval_days"] == 3

        wrong = client.post("/api/v1/review/L01-F01/answer", json={
            "user_id": user_id, "answer": "m3", "rating": "auto"
        })
        assert wrong.status_code == 200
        body = wrong.json()
        assert body["correct"] is False
        assert body["rating_applied"] == "again"
        assert body["next_stage"] == 0
        assert body["interval_days"] == 1


def test_chord_inspector_contract_is_deterministic():
    with TestClient(app) as client:
        result = client.get("/api/v1/music/chords/inspect", params={"symbol": "G7", "key": "C"})
        assert result.status_code == 200
        body = result.json()
        assert body["notes"] == ["G", "B", "D", "F"]
        assert body["formula"] == ["1", "3", "5", "b7"]
        assert body["context"] == {"key": "C", "roman": "V7", "function": "dominant"}

        slash = client.get("/api/v1/music/chords/inspect", params={"symbol": "C/E", "key": "C"})
        assert slash.status_code == 200
        assert slash.json()["bass"] == "E"
        assert slash.json()["inversion"] == 1
