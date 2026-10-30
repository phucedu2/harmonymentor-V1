"""Kiểm định trải nghiệm người mới học (20/10/2026): chấm điểm, luật hoàn thành bài, lịch Leitner.

Mỗi test ứng với một lỗ hổng tìm được khi chạy thử web bằng tài khoản học sinh mới
(docs/giai-doan/phase-2.3/AUDIT_NGUOI_MOI_HOC.md).
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.content.curriculum_specs import LESSON_SPECS, MIGRATED_LESSON_IDS, lesson_by_id
from app.db.models import ReviewState, User
from app.db.session import SessionLocal
from app.main import app
from app.services.grading_service import grade_payload
from app.services.review_scheduler import REVIEW_INTERVALS_DAYS, apply_review_result
from tests.auth_helpers import answer_lesson_correctly, auth


def make_user() -> str:
    user_id = "audit-" + uuid4().hex[:12]
    with SessionLocal() as db:
        db.add(User(id=user_id, display_name="Audit learner"))
        db.commit()
    return user_id


def item(item_id: str) -> dict:
    for lesson in LESSON_SPECS:
        for row in lesson["exercises"] + lesson["review_items"]:
            if row["id"] == item_id:
                return row
    raise KeyError(item_id)


def grade(item_id: str, answer, input_method: str | None = None) -> bool:
    row = item(item_id)
    return grade_payload(row["strategy"], row["answer_key"], row["grader_config"], answer, input_method).correct


# --- Chấm đúng khi sai -------------------------------------------------------------

def test_runtime_lessons_have_no_keyword_graded_exercises():
    # "không biết" từng được chấm Đúng vì có chữ "không". Câu tự luận trong bài 1–4 nay là nút chọn.
    for lesson_id in MIGRATED_LESSON_IDS:
        for row in lesson_by_id(lesson_id)["exercises"]:
            assert row["grader_config"].get("mode") != "contains_any", row["id"]


def test_yes_no_question_is_a_choice_and_rejects_the_wrong_choice():
    q05 = item("L01-Q05")
    assert q05["options"] == ["Có", "Không"]
    assert grade("L01-Q05", "Không") is True
    assert grade("L01-Q05", "Có") is False


@pytest.mark.parametrize("answer", ["không biết", "Khong biet", "tôi không hiểu", "idk"])
def test_keyword_rubric_rejects_unsure_answers(answer):
    config = {"mode": "contains_any", "strip_accents": True}
    outcome = grade_payload("rubric", {"accepted": ["không", "khong"]}, config, answer)
    assert outcome.correct is False


# --- Chấm sai khi đúng -------------------------------------------------------------

@pytest.mark.parametrize("item_id, answer", [
    ("L01-Q03", "1 b3 5"),
    ("L01-Q03", "1-♭3-5"),
    ("L01-Q03", "1, b3, 5"),
    ("L04-Q02", "Gm7 C7 Fmaj7"),
    ("L04-Q02", "Gm7 → C7 → Fmaj7"),
    ("L03-Q04", "T → PD → D → T"),
    ("L03-Q04", "T - SD - D - T"),
    ("L04-Q04", "B-F"),
    ("L04-Q04", "F, B"),
    ("L04-Q04", "B và F"),
    ("L04-F07", "F → E"),
])
def test_equivalent_formats_are_accepted(item_id, answer):
    assert grade(item_id, answer) is True


@pytest.mark.parametrize("item_id, answer", [
    ("L01-Q03", "1 3 5"),
    ("L04-Q02", "Fmaj7 C7 Gm7"),
    ("L04-Q04", "B D"),
    ("L04-F07", "E → F"),
])
def test_format_tolerance_does_not_accept_wrong_content(item_id, answer):
    assert grade(item_id, answer) is False


def test_solfege_names_are_understood():
    # Học sinh Việt Nam quen Đô–Rê–Mi; Engine vẫn kiểm dấu hóa.
    assert grade("L01-Q02", "Son Si Rê") is True
    assert grade("L01-Q04", "Rê Fa La") is True
    assert grade("L01-Q04", "Rê Fa thăng La") is False


# --- Piano không mang chính tả tên nốt ---------------------------------------------

def test_piano_input_grades_pitch_only_but_typed_input_keeps_spelling():
    config = {"kind": "build_chord", "symbol": "Eb"}
    assert grade_payload("music_engine", {}, config, "D# G A#", input_method="piano").correct is True
    assert grade_payload("music_engine", {}, config, "D# G A#").correct is False
    assert grade_payload("music_engine", {}, config, "Eb G Bb").correct is True


def test_grader_config_root_position_only_is_honoured():
    config = {"kind": "build_chord", "symbol": "C", "root_position_only": True}
    assert grade_payload("music_engine", {}, config, "C4 E4 G4").correct is True
    outcome = grade_payload("music_engine", {}, config, "E4 G4 C5")
    assert outcome.correct is False and outcome.primary_error == "NOT_ROOT_POSITION"


# --- Giải thích và luật hoàn thành bài ---------------------------------------------

def test_explanation_appears_after_two_wrong_attempts_or_when_correct():
    with TestClient(app) as client:
        headers = auth(make_user())
        first = client.post("/api/v1/attempts", headers=headers, json={"exercise_version_id": "L01-Q01-v4", "answer": "m3"}).json()
        assert first["correct"] is False and first["explanation"] is None and first["wrong_attempts"] == 1
        second = client.post("/api/v1/attempts", headers=headers, json={"exercise_version_id": "L01-Q01-v4", "answer": "P5"}).json()
        assert second["wrong_attempts"] == 2 and "4 nửa cung" in second["explanation"]

        other = auth(make_user())
        right = client.post("/api/v1/attempts", headers=other, json={"exercise_version_id": "L01-Q01-v4", "answer": "M3"}).json()
        assert right["correct"] is True and right["explanation"]


def test_lesson_cannot_be_completed_by_guessing():
    with TestClient(app) as client:
        headers = auth(make_user())
        lesson = client.get("/api/v1/lessons/L01").json()
        for exercise in lesson["exercises"]:
            client.post("/api/v1/attempts", headers=headers, json={"exercise_version_id": exercise["version_id"], "answer": "xx"})
        refused = client.post("/api/v1/lessons/L01/complete", headers=headers)
        assert refused.status_code == 409
        assert refused.json()["error"]["code"] == "LESSON_NOT_MASTERED"

        answer_lesson_correctly(client, "L01", headers)
        assert client.post("/api/v1/lessons/L01/complete", headers=headers).status_code == 200


def test_changed_questions_publish_a_new_version():
    with TestClient(app) as client:
        versions = {e["id"]: e["version_id"] for e in client.get("/api/v1/lessons/L01").json()["exercises"]}
        assert versions["L01-Q05"] == "L01-Q05-v5"
        assert versions["L01-Q01"] == "L01-Q01-v4"


# --- Leitner 1-2-4-8-16 ------------------------------------------------------------

def test_leitner_boxes_move_one_step_on_success_and_reset_on_failure():
    assert REVIEW_INTERVALS_DAYS == [1, 2, 4, 8, 16]
    state = ReviewState(user_id="x", review_item_id="y", status="active", stage=0, interval_days=1,
                        due_at=datetime.now(timezone.utc), failure_count=0, success_streak=0)
    seen = []
    for rating in ["good", "easy", "good", "good", "good"]:
        apply_review_result(state, True, rating)
        seen.append(state.interval_days)
    assert seen == [2, 4, 8, 16, 16]
    apply_review_result(state, False, "auto")
    assert (state.stage, state.interval_days) == (0, 1)


def test_open_review_cards_are_self_checked():
    with TestClient(app) as client:
        headers = auth(make_user())
        answer_lesson_correctly(client, "L01", headers)
        client.post("/api/v1/lessons/L01/complete", headers=headers)
        cards = {c["review_item_id"]: c for c in client.get("/api/v1/review/due", params={"include_future": "true"}, headers=headers).json()}
        assert cards["L01-F08"]["self_check"] is True and cards["L01-F08"]["back"]
        assert cards["L01-F01"]["self_check"] is False and cards["L01-F01"]["back"] is None

        remembered = client.post("/api/v1/review/L01-F08/answer", headers=headers, json={"answer": "", "rating": "good"}).json()
        assert remembered["correct"] is True and remembered["leitner_box"] == 2
        forgot = client.post("/api/v1/review/L01-F08/answer", headers=headers, json={"answer": "", "rating": "again"}).json()
        assert forgot["correct"] is False and forgot["leitner_box"] == 1


# --- Chữ của lập trình viên không lọt ra giao diện người học -----------------------

FRONTEND = __import__("pathlib").Path(__file__).resolve().parents[2] / "frontend" / "src"


@pytest.mark.parametrize("phrase", ["vertical slice", "source-audited", "Phase 2 adds", "prototype v0.1.0",
                                    "ReviewState thật", "bản MVP", "đang được xây ở Giai đoạn", "Mở Learn", "Practice tự do"])
def test_learner_pages_do_not_show_developer_jargon(phrase):
    pages = ["pages/Learn.tsx", "pages/Dashboard.tsx", "pages/Practice.tsx", "pages/Progress.tsx",
             "pages/app/CompositionLabPage.tsx", "components/learning/LessonRunner.tsx",
             "components/learning/Lesson1Explorers.tsx"]
    for page in pages:
        assert phrase not in (FRONTEND / page).read_text(encoding="utf-8"), (page, phrase)


def test_review_card_fronts_are_vietnamese_questions():
    for lesson_id in MIGRATED_LESSON_IDS:
        for row in lesson_by_id(lesson_id)["review_items"]:
            assert not row["front"].startswith("Build "), row["id"]
