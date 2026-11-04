"""Nhóm S11–S15 của hợp đồng test CP2: mastery qua API thật (lưu cùng giao dịch với lượt làm)."""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.content.curriculum_specs import lesson_by_id
from app.db.models import Attempt, MasteryState, User
from app.db.session import SessionLocal
from app.main import app
from tests.auth_helpers import auth, correct_answer

client = TestClient(app)


def make_user(role: str = "learner") -> str:
    user_id = "cp2s-" + uuid4().hex[:12]
    with SessionLocal() as db:
        db.add(User(id=user_id, display_name="CP2 S", role=role))
        db.commit()
    return user_id


def version_and_answer(lesson_id: str, exercise_id: str):
    lesson = client.get(f"/api/v1/lessons/{lesson_id}").json()
    version_id = next(e["version_id"] for e in lesson["exercises"] if e["id"] == exercise_id)
    spec = next(e for e in lesson_by_id(lesson_id)["exercises"] if e["id"] == exercise_id)
    return version_id, correct_answer(spec)


def submit(user_id: str, lesson_id: str, exercise_id: str, role: str = "learner", wrong: bool = False):
    version_id, answer = version_and_answer(lesson_id, exercise_id)
    response = client.post("/api/v1/attempts", headers=auth(user_id, role), json={
        "exercise_version_id": version_id, "answer": "zzz" if wrong else answer,
    })
    assert response.status_code == 200, response.text
    return response.json()


def state(user_id: str, skill_id: str) -> MasteryState | None:
    with SessionLocal() as db:
        return db.scalar(select(MasteryState).where(MasteryState.user_id == user_id,
                                                    MasteryState.skill_id == skill_id))


def test_s11_post_mvp_attempt_recorded_but_no_mastery_row():
    user_id = make_user()
    assert submit(user_id, "L04", "L04-Q03")["correct"]
    assert state(user_id, "voicing.guide_tones") is None


def test_s12_first_correct_mvp():
    user_id = make_user()
    submit(user_id, "L04", "L04-Q01")
    row = state(user_id, "progression.ii_v_i")
    assert row is not None
    assert row.score == pytest.approx(0.30)
    assert row.attempts_count == 1


def test_s12b_repeat_correct_counts_attempt_but_not_score():
    # L-4: attempts_count đếm mọi lượt không is_test, kể cả đúng lặp; điểm giữ nguyên (S7).
    user_id = make_user()
    submit(user_id, "L04", "L04-Q01")
    submit(user_id, "L04", "L04-Q01")
    row = state(user_id, "progression.ii_v_i")
    assert (round(row.score, 9), row.attempts_count) == (0.3, 2)


def test_s12c_wrong_records_last_error():
    user_id = make_user()
    submit(user_id, "L02", "L02-Q02", wrong=True)
    row = state(user_id, "chord.seventh_build")
    assert row.score == pytest.approx(0.0) and row.attempts_count == 1
    assert row.last_error_code


def test_s13_admin_attempt_is_test_and_no_mastery():
    admin_id = make_user("admin")
    submit(admin_id, "L04", "L04-Q01", role="admin")
    with SessionLocal() as db:
        attempts = db.scalars(select(Attempt).where(Attempt.user_id == admin_id)).all()
    assert attempts and all(a.is_test for a in attempts)
    assert state(admin_id, "progression.ii_v_i") is None


def test_s14_me_mastery_only_mvp_and_own():
    me, other = make_user(), make_user()
    submit(me, "L04", "L04-Q01")
    submit(other, "L01", "L01-Q01")
    response = client.get("/api/v1/me/mastery", headers=auth(me))
    assert response.status_code == 200
    body = response.json()
    by_id = {s["skill_id"]: s for s in body["skills"]}
    assert "voicing.guide_tones" not in by_id and "scale.parallel_minor" not in by_id
    assert all(s["group_code"] for s in body["skills"])
    assert by_id["progression.ii_v_i"]["assessed"] is True
    assert by_id["progression.ii_v_i"]["score"] == pytest.approx(0.3)
    # Kỹ năng người khác vừa làm vẫn là "chưa đánh giá" với mình.
    assert by_id["interval.naming"]["assessed"] is False
    assert by_id["interval.naming"]["score"] is None
    assert client.get("/api/v1/me/mastery").status_code == 401


def test_s15_placement_correct_sets_065_wrong_sets_zero():
    user_id = make_user()
    headers = auth(user_id)
    placement = client.get("/api/v1/placement", headers=headers).json()
    assert placement["status"] == "not_started"
    questions = placement["questions"]
    assert len(questions) == 12
    first, second = questions[0], questions[1]
    spec_answers = {}
    for lesson_id in ("L01", "L02", "L03", "L04"):
        for e in lesson_by_id(lesson_id)["exercises"]:
            spec_answers[e["id"]] = correct_answer(e)
    response = client.post("/api/v1/placement/submit", headers=headers, json={"answers": [
        {"exercise_version_id": first["exercise_version_id"], "answer": spec_answers[first["exercise_id"]]},
        {"exercise_version_id": second["exercise_version_id"], "answer": "zzz"},
    ]})
    assert response.status_code == 200, response.text
    assert state(user_id, first["skill_id"]).score == pytest.approx(0.65)
    assert state(user_id, second["skill_id"]).score == pytest.approx(0.0)
    # Câu không trả lời: chưa đánh giá, không có dòng.
    assert state(user_id, questions[5]["skill_id"]) is None
    # Làm lại phải xác nhận.
    again = client.post("/api/v1/placement/submit", headers=headers, json={"answers": []})
    assert again.status_code == 409
    assert client.get("/api/v1/placement", headers=headers).json()["status"] == "completed"


def test_s15b_placement_skip_leaves_everything_unassessed():
    user_id = make_user()
    headers = auth(user_id)
    assert client.post("/api/v1/placement/skip", headers=headers).status_code == 200
    assert client.get("/api/v1/placement", headers=headers).json()["status"] == "skipped"
    body = client.get("/api/v1/me/mastery", headers=headers).json()
    assert not any(s["assessed"] for s in body["skills"])


def test_s15c_placement_only_mvp_machine_graded_published():
    user_id = make_user()
    questions = client.get("/api/v1/placement", headers=auth(user_id)).json()["questions"]
    from app.ai.skill_mapping import is_mvp
    assert all(is_mvp(q["skill_id"]) for q in questions)
    assert len({q["skill_id"] for q in questions}) == 12
    # Không lộ đáp án.
    assert all("answer_key" not in q for q in questions)
