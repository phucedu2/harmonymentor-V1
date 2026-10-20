"""Phase 1 vertical slice: start -> checkpoints/quiz -> progress -> complete -> review."""

from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient

from app.content.curriculum_specs import LESSON_SPECS
from app.db.models import User
from app.db.session import SessionLocal
from app.main import app
from tests.auth_helpers import answer_lesson_correctly, auth


def make_user() -> str:
    user_id = "p1-" + uuid4().hex[:12]
    with SessionLocal() as db:
        db.add(User(id=user_id, display_name="Phase 1 test user"))
        db.commit()
    return user_id


def test_checkpoint_blocks_reference_real_exercises_for_runtime_lessons():
    for lesson in LESSON_SPECS[:4]:
        exercise_ids = {item["id"] for item in lesson["exercises"]}
        checkpoints = [block for block in lesson["blocks"] if block[1] == "checkpoint"]
        assert len(checkpoints) == 2
        assert all(block[2]["exercise_id"] in exercise_ids for block in checkpoints)


def test_start_lesson_is_idempotent_and_overview_tracks_attempts():
    with TestClient(app) as client:
        user_id = make_user()
        first = client.post("/api/v1/lessons/L04/start", json={}, headers=auth(user_id))
        assert first.status_code == 200
        assert first.json()["status"] == "started"
        second = client.post("/api/v1/lessons/L04/start", json={}, headers=auth(user_id))
        assert second.status_code == 200
        assert second.json()["started_at"] == first.json()["started_at"]

        before = client.get("/api/v1/learning/overview", headers=auth(user_id))
        assert before.status_code == 200
        lesson = next(x for x in before.json()["lessons"] if x["lesson_id"] == "L04")
        assert lesson["status"] == "started"
        assert lesson["attempted_exercises"] == 0
        assert lesson["practice_progress_percent"] == 0

        detail = client.get("/api/v1/lessons/L04").json()
        q1 = next(x for x in detail["exercises"] if x["id"] == "L04-Q01")
        attempt = client.post("/api/v1/attempts", json={
            "exercise_version_id": q1["version_id"],
            "answer": "Dm7-G7-Cmaj7",
        }, headers=auth(user_id))
        assert attempt.status_code == 200 and attempt.json()["correct"] is True

        after = client.get("/api/v1/learning/overview", headers=auth(user_id))
        lesson = next(x for x in after.json()["lessons"] if x["lesson_id"] == "L04")
        assert lesson["attempted_exercises"] == 1
        assert lesson["correct_exercises"] == 1
        assert lesson["attempt_count"] == 1
        assert lesson["practice_progress_percent"] == 17
        assert lesson["attempted_exercise_ids"] == ["L04-Q01"]


def test_completion_updates_overview_and_review_counts():
    with TestClient(app) as client:
        user_id = make_user()
        client.post("/api/v1/lessons/L01/start", json={}, headers=auth(user_id))
        answer_lesson_correctly(client, "L01", auth(user_id))
        completed = client.post("/api/v1/lessons/L01/complete", json={}, headers=auth(user_id))
        assert completed.status_code == 200

        overview = client.get("/api/v1/learning/overview", headers=auth(user_id))
        assert overview.status_code == 200
        body = overview.json()
        lesson = next(x for x in body["lessons"] if x["lesson_id"] == "L01")
        assert lesson["status"] == "completed"
        assert lesson["practice_progress_percent"] == 100
        assert body["completed_lessons"] >= 1
        assert body["upcoming_reviews"] >= 8


def test_chord_inspector_supports_phase1_progression_ui_contract():
    with TestClient(app) as client:
        g7 = client.get("/api/v1/music/chords/inspect", params={"symbol": "G7", "key": "C"})
        assert g7.status_code == 200
        body = g7.json()
        assert body["notes"] == ["G", "B", "D", "F"]
        assert body["formula"] == ["1", "3", "5", "b7"]
        assert body["context"]["roman"] == "V7"
        assert body["context"]["function"] == "dominant"
