"""Phase 0.4B: source-audited curriculum, skill graph, and Lessons 2-4 runtime migration."""

from __future__ import annotations

from collections import defaultdict, deque
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.content.curriculum_specs import LESSON_SPECS, MIGRATED_LESSON_IDS, all_exercises, all_review_items
from app.content.skill_graph import LESSON_SKILLS, PREREQUISITES, SKILLS
from app.content.source_registry import SOURCE_REGISTRY
from app.db.models import ExerciseVersion, ReviewItem, SkillPrerequisite, User
from app.db.session import SessionLocal
from app.main import app


def make_user() -> str:
    user_id = "p04b-" + uuid4().hex[:12]
    with SessionLocal() as db:
        db.add(User(id=user_id, display_name="Phase04B test user"))
        db.commit()
    return user_id


def test_curriculum_bank_is_exactly_8_48_64_and_ids_are_unique():
    assert len(LESSON_SPECS) == 8
    exercises = all_exercises()
    reviews = all_review_items()
    assert len(exercises) == 48
    assert len(reviews) == 64
    assert len({x["id"] for x in exercises}) == 48
    assert len({x["id"] for x in reviews}) == 64


def test_every_item_is_skill_mapped_and_source_grounded():
    skill_ids = {x[0] for x in SKILLS}
    source_ids = set(SOURCE_REGISTRY)
    for lesson in LESSON_SPECS:
        assert lesson["id"] in LESSON_SKILLS
        assert set(lesson["skills"]) == set(LESSON_SKILLS[lesson["id"]])
        assert lesson["sources"]
        for source in lesson["sources"]:
            assert source["source_id"] in source_ids
            assert source["locator"].strip()
        for item in [*lesson["exercises"], *lesson["review_items"]]:
            assert item["skill"] in skill_ids
            assert item["provenance"], item["id"]
            assert all(x["source_id"] in source_ids for x in item["provenance"])


def test_skill_graph_is_a_dag_and_all_edges_reference_defined_skills():
    nodes = {x[0] for x in SKILLS}
    incoming = {node: 0 for node in nodes}
    outgoing = defaultdict(list)
    for skill, prerequisite in PREREQUISITES:
        assert skill in nodes
        assert prerequisite in nodes
        outgoing[prerequisite].append(skill)
        incoming[skill] += 1
    queue = deque([node for node, degree in incoming.items() if degree == 0])
    visited = 0
    while queue:
        node = queue.popleft()
        visited += 1
        for child in outgoing[node]:
            incoming[child] -= 1
            if incoming[child] == 0:
                queue.append(child)
    assert visited == len(nodes)


def test_skill_prerequisites_are_persisted():
    with TestClient(app):
        with SessionLocal() as db:
            persisted = db.scalars(select(SkillPrerequisite)).all()
            assert len(persisted) >= len(PREREQUISITES)


def test_lessons_1_to_4_are_migrated_and_5_to_8_are_specs_only():
    with TestClient(app) as client:
        lessons = {x["id"]: x for x in client.get("/api/v1/lessons").json()}
        assert set(MIGRATED_LESSON_IDS) == {"L01", "L02", "L03", "L04"}
        expected_block_counts = {"L01": 14, "L02": 10, "L03": 9, "L04": 11}
        for lesson_id in ["L01", "L02", "L03", "L04"]:
            assert lessons[lesson_id]["exercise_count"] == 6
            assert lessons[lesson_id]["review_item_count"] == 8
            assert lessons[lesson_id]["block_count"] == expected_block_counts[lesson_id]
            assert lessons[lesson_id]["status"] == "reviewed"
        for lesson_id in ["L05", "L06", "L07", "L08"]:
            assert lessons[lesson_id]["exercise_count"] == 0
            assert lessons[lesson_id]["review_item_count"] == 0
            assert lessons[lesson_id]["status"] == "source_audited"


def test_lesson2_scale_and_roman_music_engine_graders_work_end_to_end():
    with TestClient(app) as client:
        user_id = make_user()
        detail = client.get("/api/v1/lessons/L02").json()
        versions = {x["id"]: x["version_id"] for x in detail["exercises"]}

        scale = client.post("/api/v1/attempts", json={
            "user_id": user_id,
            "exercise_version_id": versions["L02-Q01"],
            "answer": "G A B C D E F#",
        })
        assert scale.status_code == 200
        assert scale.json()["correct"] is True

        wrong_order = client.post("/api/v1/attempts", json={
            "user_id": user_id,
            "exercise_version_id": versions["L02-Q01"],
            "answer": "G B A C D E F#",
        })
        assert wrong_order.status_code == 200
        assert wrong_order.json()["correct"] is False
        assert wrong_order.json()["primary_error"] == "WRONG_SCALE_DEGREE_ORDER"

        roman = client.post("/api/v1/attempts", json={
            "user_id": user_id,
            "exercise_version_id": versions["L02-Q03"],
            "answer": "ii7",
        })
        assert roman.status_code == 200
        assert roman.json()["correct"] is True


def test_lesson3_and_lesson4_contracts_are_live():
    with TestClient(app) as client:
        user_id = make_user()
        l03 = client.get("/api/v1/lessons/L03").json()
        l04 = client.get("/api/v1/lessons/L04").json()
        assert len(l03["sources"]) >= 4
        assert len(l04["sources"]) >= 5

        l03q2 = next(x for x in l03["exercises"] if x["id"] == "L03-Q02")
        r = client.post("/api/v1/attempts", json={
            "user_id": user_id, "exercise_version_id": l03q2["version_id"], "answer": "Predominant"
        })
        assert r.status_code == 200 and r.json()["correct"] is True

        l04q2 = next(x for x in l04["exercises"] if x["id"] == "L04-Q02")
        r = client.post("/api/v1/attempts", json={
            "user_id": user_id, "exercise_version_id": l04q2["version_id"], "answer": "Gm7-C7-Fmaj7"
        })
        assert r.status_code == 200 and r.json()["correct"] is True


def test_audited_item_provenance_is_persisted_for_runtime_lessons():
    with TestClient(app):
        with SessionLocal() as db:
            # L01 multi-key pedagogy rewrite publishes v4; L02-L04 use their first audited version.
            for version_id in ["L01-Q01-v4", "L02-Q01-v1", "L03-Q01-v1", "L04-Q01-v1"]:
                version = db.get(ExerciseVersion, version_id)
                assert version is not None
                assert version.provenance
                assert all(x.get("source_id") and x.get("locator") for x in version.provenance)

            for review_id in ["L01-F01", "L02-F01", "L03-F01", "L04-F01"]:
                item = db.get(ReviewItem, review_id)
                assert item is not None
                assert item.provenance
                assert all(x.get("source_id") and x.get("locator") for x in item.provenance)
