"""Demo 10/11, nhiệm vụ A: 6 câu mới (đã phát hành 04/11) L01-Q07/Q08, L02-Q07..Q10.

Kiểm bốn điều Thắng yêu cầu: (1) đáp án đúng được chấm đúng, mọi phương án nhiễu bị từ chối, tên đồng âm
không được nhận; (2) đáp án khớp Music Engine; (3) đã phát hành (Thắng + Đạt duyệt 04/11/2026) nên hiện với người học và bắt buộc để
hoàn thành bài; (4) ba câu độc lập
đúng lần đầu đưa mastery kỹ năng lên 1 − 0,7³ = 0,657 và người học bỏ qua placement đi được L01 → L02 →
L03 → L04 qua API thật, không hạ ngưỡng 0,60/0,80.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.api import ai_recommend
from app.content.curriculum_specs import lesson_by_id
from app.content.source_registry import SOURCE_REGISTRY
from app.db.models import MasteryState, User
from app.db.session import SessionLocal
from app.main import app
from app.music_engine.grading import grade_roman_numeral
from app.music_engine.roman import roman_numeral
from app.music_engine.tools import get_chord_tones, identify_interval
from app.services.grading_service import grade_payload
from tests.auth_helpers import auth, correct_answer

NEW_IDS = ["L01-Q07", "L01-Q08", "L02-Q07", "L02-Q08", "L02-Q09", "L02-Q10"]


def item(exercise_id: str) -> dict:
    return next(x for x in lesson_by_id(exercise_id[:3])["exercises"] if x["id"] == exercise_id)


def grade(exercise_id: str, answer):
    spec = item(exercise_id)
    return grade_payload(spec["strategy"], spec["answer_key"], spec["grader_config"], answer)


# --- Nội dung và nguồn -----------------------------------------------------------------------------

def test_six_new_questions_are_published_with_two_sources_and_known_source_ids():
    for exercise_id in NEW_IDS:
        spec = item(exercise_id)
        assert spec["status"] == "published", exercise_id
        assert spec["version"] is None  # câu mới, chưa phát hành lần nào
        sources = {p["source_id"] for p in spec["provenance"]}
        assert {"MT21C", "OMT_V2"} <= sources, exercise_id
        assert sources <= set(SOURCE_REGISTRY)
        assert all(p["locator"] for p in spec["provenance"])
        assert spec["explanation"]


def test_expected_answers_come_from_music_engine():
    # Không tin đáp án viết tay: Engine phải ra cùng kết quả.
    def iv(lower, upper):
        return identify_interval(lower=lower, upper=upper)["interval"]

    assert iv("D", "F#") == "M3"
    assert iv("A", "C") == "m3"
    assert iv("D", "Gb") == "d4"   # cùng phím với F# nhưng là quãng 4
    assert iv("A", "B#") == "A2"   # cùng phím với C nhưng là quãng 2
    assert get_chord_tones(symbol="D7")["notes"] == ["D", "F#", "A", "C"]
    assert get_chord_tones(symbol="Fmaj7")["notes"] == item("L02-Q08")["answer_key"]["expected"]
    assert roman_numeral("G", "D7").numeral == item("L02-Q09")["answer_key"]["expected"] == "V7"
    assert roman_numeral("C", "Am7").numeral == item("L02-Q10")["answer_key"]["expected"] == "vi7"
    # Bậc V của G trưởng là D7 (không phải Dmaj7/Dm7/Ddim7).
    assert roman_numeral("G", "D7").degree == 5


# --- Chấm điểm ------------------------------------------------------------------------------------

@pytest.mark.parametrize("exercise_id,right,wrong", [
    ("L01-Q07", "F#", ["Gb", "F", "G", "f#"]),
    ("L01-Q08", "C", ["C#", "B#", "B", "c"]),
    ("L02-Q07", "D7", ["Dmaj7", "Dm7", "Ddim7", "d7"]),
])
def test_choice_questions_accept_only_the_exact_option(exercise_id, right, wrong):
    assert item(exercise_id)["answer_key"]["expected"] == right
    assert set(item(exercise_id)["options"]) >= {right, *[w for w in wrong if w in item(exercise_id)["options"]]}
    assert grade(exercise_id, right).correct
    assert grade(exercise_id, f"  {right} ").correct  # khoảng trắng hai đầu không tính là sai
    for answer in wrong:
        assert not grade(exercise_id, answer).correct, (exercise_id, answer)


def test_every_distractor_is_rejected():
    for exercise_id in ("L01-Q07", "L01-Q08", "L02-Q07"):
        spec = item(exercise_id)
        assert len(spec["options"]) == 4 and len(set(spec["options"])) == 4
        for option in spec["options"]:
            assert grade(exercise_id, option).correct == (option == spec["answer_key"]["expected"]), option


@pytest.mark.parametrize("answer,ok,error", [
    ("F A C E", True, None),
    ("F-A-C-E", True, None),
    ("F, A, C, E", True, None),
    ("F A C", False, "MISSING_TONE"),
    ("F A C E G", False, "EXTRA_TONE"),
    ("F A C Eb", False, "SEVENTH_QUALITY"),
    ("E# A C E", False, "ENHARMONIC_SPELLING"),
    ("F A C Fb", False, "ENHARMONIC_SPELLING"),
    ("F Ab C E", False, None),
])
def test_fmaj7_needs_exactly_four_correctly_spelled_notes(answer, ok, error):
    outcome = grade("L02-Q08", answer)
    assert outcome.correct is ok, (answer, outcome)
    if error:
        assert outcome.primary_error == error


@pytest.mark.parametrize("exercise_id,answer,ok", [
    ("L02-Q09", "V7", True), ("L02-Q09", " V7 ", True),
    ("L02-Q09", "v7", False), ("L02-Q09", "V", False), ("L02-Q09", "V⁷", False), ("L02-Q09", "V 7", False),
    ("L02-Q09", "I7", False), ("L02-Q09", "Vmaj7", False),
    ("L02-Q10", "vi7", True),
    ("L02-Q10", "VI7", False), ("L02-Q10", "vi", False), ("L02-Q10", "vi 7", False), ("L02-Q10", "ii7", False),
])
def test_roman_numerals_check_case_and_convention(exercise_id, answer, ok):
    assert grade(exercise_id, answer).correct is ok, (exercise_id, answer)


def test_roman_wrong_case_is_reported_as_quality_mark_not_degree():
    assert grade_roman_numeral("C", "Am7", "VI7")["primary_error"] == "ROMAN_QUALITY_MARK"
    assert grade_roman_numeral("G", "D7", "IV7")["primary_error"] == "ROMAN_DEGREE"


# --- Nháp: ẩn, không bắt buộc; sau phát hành: mastery và lộ trình ---------------------------------

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:  # lifespan seed CSDL dev, gồm cả 6 câu nháp
        app.dependency_overrides[ai_recommend.embedder_dep] = lambda: None  # không gọi mạng
        yield c
        app.dependency_overrides.pop(ai_recommend.embedder_dep, None)


def new_user() -> str:
    uid = "demo1011-" + uuid4().hex[:10]
    with SessionLocal() as db:
        db.add(User(id=uid, display_name="demo 10/11", email=f"{uid}@example.test"))
        db.commit()
    return uid


def learn_via_api(client, uid: str, lesson_id: str) -> None:
    headers = auth(uid)
    lesson = client.get(f"/api/v1/lessons/{lesson_id}").json()
    by_id = {x["id"]: x for x in lesson_by_id(lesson_id)["exercises"]}
    for exercise in lesson["exercises"]:
        r = client.post("/api/v1/attempts", headers=headers, json={
            "exercise_version_id": exercise["version_id"], "answer": correct_answer(by_id[exercise["id"]])})
        assert r.status_code == 200 and r.json()["correct"], (exercise["id"], r.json())
    r = client.post(f"/api/v1/lessons/{lesson_id}/complete", headers=headers)
    assert r.status_code == 200, r.json()


def mastery(uid: str) -> dict[str, float]:
    with SessionLocal() as db:
        return {m.skill_id: round(m.score, 3)
                for m in db.scalars(select(MasteryState).where(MasteryState.user_id == uid))}


def next_lessons(client, uid: str) -> list[str]:
    r = client.get("/api/v1/recommend", headers=auth(uid))
    assert r.status_code == 200, r.json()
    return [x["lesson_id"] for x in r.json()["next"]]


def test_published_questions_are_shown_and_required(client):
    """Thắng + Đạt duyệt 04/11/2026: 6 câu đã phát hành, hiện cho người học và cần đúng để hoàn thành bài."""
    for lesson_id, n in (("L01", 8), ("L02", 10)):
        shown = [x["id"] for x in client.get(f"/api/v1/lessons/{lesson_id}").json()["exercises"]]
        assert len(shown) == n and {i for i in NEW_IDS if i[:3] == lesson_id} <= set(shown)
    uid = new_user()
    r = client.post("/api/v1/lessons/L01/complete", headers=auth(uid))
    assert r.status_code == 409


def test_three_independent_first_correct_answers_reach_0657(client):
    uid = new_user()
    learn_via_api(client, uid, "L01")
    learn_via_api(client, uid, "L02")
    m = mastery(uid)
    for skill in ("pitch.spelling", "chord.seventh_quality", "chord.seventh_build", "roman.major_seventh"):
        assert m[skill] == pytest.approx(1 - 0.7 ** 3, abs=1e-3), (skill, m[skill])


def test_new_learner_without_placement_walks_l01_to_l04(client):
    uid = new_user()
    steps = []
    for done, target in (("L01", "L02"), ("L02", "L03"), ("L03", "L04")):
        learn_via_api(client, uid, done)
        suggested = next_lessons(client, uid)
        steps.append((done, suggested))
        print(f"\nKQ xong {done}: next = {suggested}; mastery = {mastery(uid)}")
        assert target in suggested, (steps, mastery(uid))
