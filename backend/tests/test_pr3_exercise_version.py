"""PR-3 (HM-003): phiên bản câu hỏi bất biến, seed không ghi đè, 409 cho bản cũ, draft, xóa mềm.

Mỗi test dùng một file SQLite riêng trong tmp_path và một bản sao sâu của curriculum_specs, nên sửa "nguồn"
trong test không ảnh hưởng CSDL dev hay test khác.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker

from app.content import versioning
from app.content.curriculum_specs import LESSON_SPECS, q
from app.content.seed_data import seed_initial_data
from app.content.versioning import ImmutableVersionError, SeedConflictError, content_hash, current_version
from app.core.config import Settings, _flag, check_runtime_settings
from app.db.base import Base
from app.db.models import Attempt, Exercise, ExerciseVersion, LessonProgress, User
from app.db.session import get_db
from app.main import app
from app.services.grading_service import grade_payload
from app.services.learning_service import (
    ExerciseVersionSuperseded,
    LessonNotMastered,
    complete_lesson,
    submit_attempt,
)
from tests.auth_helpers import auth, correct_answer

KNOWN_SNAPSHOTS = json.loads(
    (Path(__file__).resolve().parents[1] / "migrations" / "data" / "pr3_anh_chup_lich_su.json").read_text(encoding="utf-8")
)["versions"]

CURRENT_VERSION_IDS = {
    "L01-Q01-v4", "L01-Q02-v4", "L01-Q03-v5", "L01-Q04-v4", "L01-Q05-v5", "L01-Q06-v4",
    "L02-Q01-v1", "L02-Q02-v1", "L02-Q03-v1", "L02-Q04-v1", "L02-Q05-v1", "L02-Q06-v1",
    "L03-Q01-v1", "L03-Q02-v1", "L03-Q03-v1", "L03-Q04-v2", "L03-Q05-v2", "L03-Q06-v1",
    "L04-Q01-v1", "L04-Q02-v2", "L04-Q03-v1", "L04-Q04-v2", "L04-Q05-v2", "L04-Q06-v2",
}


@pytest.fixture()
def factory(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'pr3.db'}", future=True, connect_args={"check_same_thread": False})
    Base.metadata.create_all(engine)
    yield sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, class_=Session)
    engine.dispose()


@pytest.fixture()
def drafts_visible(monkeypatch):
    monkeypatch.setattr(versioning, "visible_statuses", lambda: {"draft", "published"})


def specs() -> list[dict]:
    return copy.deepcopy(LESSON_SPECS)


def item_of(lesson_specs: list[dict], exercise_id: str) -> dict:
    lesson = next(s for s in lesson_specs if s["id"] == exercise_id[:3])
    return next(i for i in lesson["exercises"] if i["id"] == exercise_id)


def seed(factory, lesson_specs=None) -> None:
    with factory() as db:
        seed_initial_data(db, lesson_specs)


def new_user(factory) -> str:
    user_id = "pr3-" + uuid4().hex[:10]
    with factory() as db:
        db.add(User(id=user_id, display_name="PR-3 test"))
        db.commit()
    return user_id


def version_rows(factory) -> dict[str, tuple]:
    with factory() as db:
        return {v.id: (v.content_hash, v.status, v.snapshot_origin, v.created_at, v.prompt, json.dumps(v.answer_key))
                for v in db.scalars(select(ExerciseVersion)).all()}


def answer(factory, user_id: str, version_id: str, text: str):
    with factory() as db:
        attempt, _ = submit_attempt(db, user_id, version_id, text)
        return attempt


def client_for(factory) -> TestClient:
    def override():
        db = factory()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override
    # Không dùng `with`: lifespan sẽ seed vào CSDL mặc định thay vì CSDL tạm của test.
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture(autouse=True)
def _clear_overrides():
    yield
    app.dependency_overrides.pop(get_db, None)


# --- Seed idempotent và danh sách id vàng ------------------------------------------------------------

def test_seed_three_times_changes_nothing(factory):
    seed(factory)
    first = version_rows(factory)
    seed(factory)
    seed(factory)
    assert version_rows(factory) == first
    assert set(first) == CURRENT_VERSION_IDS
    assert {row[1] for row in first.values()} == {"published"}
    assert {row[2] for row in first.values()} == {"seed"}


def test_current_version_ids_are_exactly_the_published_24(factory):
    seed(factory)
    with factory() as db:
        current = {current_version(e).id for e in db.scalars(select(Exercise)).all()}
    assert current == CURRENT_VERSION_IDS
    assert "L01-Q01-v4" in current and "L01-Q03-v5" in current


def test_seeded_snapshots_equal_git_history_snapshots(factory):
    # Nội dung seed tạo ra phải trùng ảnh chụp git mà migration dùng; lệch là migration sẽ khôi phục sai.
    seed(factory)
    with factory() as db:
        for version in db.scalars(select(ExerciseVersion)).all():
            known = KNOWN_SNAPSHOTS[version.id]
            for name in ("kind", "prompt", "options", "grading_strategy", "answer_key", "grader_config", "explanation", "provenance"):
                assert getattr(version, name) == known[name], (version.id, name)


def test_exercise_mirror_matches_latest_version(factory):
    seed(factory)
    with factory() as db:
        for exercise in db.scalars(select(Exercise)).all():
            latest = max(exercise.versions, key=lambda v: v.version)
            assert (exercise.kind, exercise.prompt, exercise.options, exercise.grading_strategy) == (
                latest.kind, latest.prompt, latest.options, latest.grading_strategy), exercise.id


# --- Seed gặp nội dung lệch thì dừng, không ghi đè, không tự tăng version ---------------------------

CHANGES = {
    "prompt": ("prompt", lambda v: v + " (sửa)"),
    "options": ("options", lambda v: ["A", "B"]),
    "kind": ("kind", lambda v: "active_recall" if v != "active_recall" else "mcq"),
    "strategy": ("grading_strategy", lambda v: "rubric"),
    "answer_key": ("answer_key", lambda v: {"expected": "m3"}),
    "grader_config": ("grader_config", lambda v: {**v, "strip_accents": not v.get("strip_accents", False)}),
    "explanation": ("explanation", lambda v: "Lời giải khác."),
    "provenance": ("provenance", lambda v: []),
}


@pytest.mark.parametrize("spec_field", sorted(CHANGES))
def test_changing_published_version_without_bump_fails_and_rolls_back(factory, spec_field):
    seed(factory)
    before = version_rows(factory)
    with factory() as db:
        mirror_before = db.get(Exercise, "L01-Q01").prompt
    changed = specs()
    db_field, change = CHANGES[spec_field]
    item = item_of(changed, "L01-Q01")
    item[spec_field] = change(item[spec_field])
    with pytest.raises(SeedConflictError) as caught:
        seed(factory, changed)
    conflict = caught.value.conflicts[0]
    assert (conflict.code, conflict.target) == ("SEED_VERSION_CHANGED", "L01-Q01-v4")
    assert conflict.fields == [db_field]
    assert "L01-Q01-v4" in str(caught.value)
    # Rollback toàn bộ: không phiên bản nào đổi, kể cả bản sao trên exercises.
    assert version_rows(factory) == before
    with factory() as db:
        assert db.get(Exercise, "L01-Q01").prompt == mirror_before


def test_version_bump_keeps_old_snapshot_and_attempts(factory):
    seed(factory)
    user = new_user(factory)
    old_attempt = answer(factory, user, "L01-Q01-v4", "M3")
    before = version_rows(factory)["L01-Q01-v4"]
    changed = specs()
    item = item_of(changed, "L01-Q01")
    item["prompt"] += " (bản 5)"
    item["version"] = 5
    seed(factory, changed)
    rows = version_rows(factory)
    assert rows["L01-Q01-v4"] == before
    assert rows["L01-Q01-v5"][2] == "seed"
    with factory() as db:
        assert db.get(Attempt, old_attempt.id).exercise_version_id == "L01-Q01-v4"
        assert current_version(db.get(Exercise, "L01-Q01")).id == "L01-Q01-v5"
    seed(factory, changed)
    assert version_rows(factory) == rows


def test_identity_change_is_rejected(factory):
    seed(factory)
    changed = specs()
    item_of(changed, "L01-Q01")["skill"] = "pitch.spelling"
    with pytest.raises(SeedConflictError) as caught:
        seed(factory, changed)
    assert [c.code for c in caught.value.conflicts] == ["SEED_IDENTITY_CHANGED"]


def test_version_must_increase(factory):
    seed(factory)
    changed = specs()
    item = item_of(changed, "L01-Q03")
    item["version"] = 4
    with pytest.raises(SeedConflictError) as caught:
        seed(factory, changed)
    assert [(c.code, c.target) for c in caught.value.conflicts] == [("SEED_VERSION_NOT_INCREASING", "L01-Q03-v4")]


def test_conflicts_never_auto_create_versions(factory):
    seed(factory)
    changed = specs()
    item_of(changed, "L02-Q01")["answer_key"] = {"expected": ["G"]}
    with pytest.raises(SeedConflictError):
        seed(factory, changed)
    assert set(version_rows(factory)) == CURRENT_VERSION_IDS


# --- Draft / published ------------------------------------------------------------------------------

def draft_spec(prompt: str = "Câu nháp: quãng từ C lên E là gì?", status: str = "draft") -> list[dict]:
    changed = specs()
    lesson = next(s for s in changed if s["id"] == "L02")
    lesson["exercises"].append(q(
        "L02-Q07", "active_recall", prompt, "interval.identify", "exact", {"expected": "M3"},
        explanation="C lên E là quãng ba trưởng.", provenance=[{"source_id": "omt", "locator": "Intervals"}],
        status=status,
    ))
    return changed


def test_draft_hidden_by_default_and_not_required_for_completion(factory):
    seed(factory, draft_spec())
    user = new_user(factory)
    client = client_for(factory)
    lesson = client.get("/api/v1/lessons/L02").json()
    assert "L02-Q07" not in [x["id"] for x in lesson["exercises"]]
    assert lesson["exercise_count"] == 6
    response = client.post("/api/v1/attempts", headers=auth(user), json={"exercise_version_id": "L02-Q07-v1", "answer": "M3"})
    assert response.status_code == 404
    for item in next(s for s in LESSON_SPECS if s["id"] == "L02")["exercises"]:
        answer(factory, user, f'{item["id"]}-v1', correct_answer(item))
    with factory() as db:
        progress, _ = complete_lesson(db, user, "L02")
        assert progress.status == "completed"


def test_draft_visible_only_when_enabled(factory, drafts_visible):
    seed(factory, draft_spec())
    lesson = client_for(factory).get("/api/v1/lessons/L02").json()
    draft = next(x for x in lesson["exercises"] if x["id"] == "L02-Q07")
    assert draft["version_id"] == "L02-Q07-v1"


def test_draft_editable_until_attempted_then_locked(factory, drafts_visible):
    seed(factory, draft_spec())
    seed(factory, draft_spec(prompt="Câu nháp đã sửa: quãng từ C lên E là gì?"))
    with factory() as db:
        version = db.get(ExerciseVersion, "L02-Q07-v1")
        assert version.prompt.startswith("Câu nháp đã sửa")
        assert version.content_hash == content_hash(version.__dict__)
    user = new_user(factory)
    answer(factory, user, "L02-Q07-v1", "M3")
    with pytest.raises(SeedConflictError) as caught:
        seed(factory, draft_spec(prompt="Sửa lần ba"))
    assert caught.value.conflicts[0].code == "SEED_VERSION_CHANGED"


def test_publish_draft_then_it_is_locked(factory):
    seed(factory, draft_spec())
    seed(factory, draft_spec(status="published"))
    with factory() as db:
        version = db.get(ExerciseVersion, "L02-Q07-v1")
        assert version.status == "published" and version.published_at is not None
    with pytest.raises(SeedConflictError) as caught:
        seed(factory, draft_spec(status="draft"))
    assert caught.value.conflicts[0].code == "SEED_STATUS_DOWNGRADE"


def test_production_refuses_draft_flag(monkeypatch):
    with pytest.raises(RuntimeError, match="SHOW_DRAFT_CONTENT"):
        check_runtime_settings(Settings(app_env="production", show_draft_content=True))
    check_runtime_settings(Settings(app_env="production", show_draft_content=False))
    check_runtime_settings(Settings(app_env="development", show_draft_content=True))
    # Không đặt biến môi trường thì bản nháp bị ẩn.
    monkeypatch.delenv("SHOW_DRAFT_CONTENT", raising=False)
    assert _flag("SHOW_DRAFT_CONTENT", "0") is False


# --- 409 cho phiên bản cũ, chấm theo ảnh chụp -------------------------------------------------------

def bump_l01_q01(factory) -> None:
    changed = specs()
    item = item_of(changed, "L01-Q01")
    item["prompt"] += " (bản 5)"
    item["version"] = 5
    seed(factory, changed)


def test_attempt_on_superseded_version_returns_409(factory):
    seed(factory)
    user = new_user(factory)
    bump_l01_q01(factory)
    client = client_for(factory)
    old = client.post("/api/v1/attempts", headers=auth(user), json={"exercise_version_id": "L01-Q01-v4", "answer": "M3"})
    assert old.status_code == 409
    error = old.json()["error"]
    assert error["code"] == "EXERCISE_VERSION_SUPERSEDED"
    assert error["fields"] == {"exercise_version_id": "L01-Q01-v4", "current_version_id": "L01-Q01-v5"}
    with factory() as db:
        assert db.scalar(select(func.count()).select_from(Attempt)) == 0
    current = client.post("/api/v1/attempts", headers=auth(user), json={"exercise_version_id": "L01-Q01-v5", "answer": "M3"})
    assert current.status_code == 200 and current.json()["correct"]
    lesson = client.get("/api/v1/lessons/L01").json()
    q01 = next(x for x in lesson["exercises"] if x["id"] == "L01-Q01")
    assert q01["version_id"] == "L01-Q01-v5" and q01["prompt"].endswith("(bản 5)")


def test_old_rubric_version_keeps_meaning_after_exact_version(factory):
    """Đúng tình huống đã tái hiện (mục 2.3 bản thiết kế): L03-Q05 v1 chấm rubric, v2 chấm exact."""
    legacy = specs()
    item = item_of(legacy, "L03-Q05")
    v1 = KNOWN_SNAPSHOTS["L03-Q05-v1"]
    item.update(version=None, prompt=v1["prompt"], options=v1["options"], strategy=v1["grading_strategy"],
                answer_key=v1["answer_key"], grader_config=v1["grader_config"], explanation=v1["explanation"],
                provenance=v1["provenance"])
    seed(factory, legacy)
    user = new_user(factory)
    old = answer(factory, user, "L03-Q05-v1", "Vì chức năng phụ thuộc ngữ cảnh")
    assert old.correct
    seed(factory)  # nguồn hiện tại: v2 trắc nghiệm, chấm exact
    with factory() as db:
        v1_row = db.get(ExerciseVersion, "L03-Q05-v1")
        v2_row = db.get(ExerciseVersion, "L03-Q05-v2")
        assert (v1_row.grading_strategy, v1_row.options) == ("rubric", None)
        assert v2_row.grading_strategy == "exact" and v2_row.options
        # Chấm lại lượt cũ theo ảnh chụp của chính nó vẫn ra đúng như đã lưu (trước PR-3 ra sai).
        regrade = grade_payload(v1_row.grading_strategy, v1_row.answer_key, v1_row.grader_config, old.answer)
        assert regrade.correct is True
        assert db.get(Attempt, old.id).correct is True
        with pytest.raises(ExerciseVersionSuperseded):
            submit_attempt(db, user, "L03-Q05-v1", "ngữ cảnh")


def test_missing_snapshot_current_version_is_hidden_and_not_graded(factory):
    seed(factory)
    with factory() as db:
        # Mô phỏng bản migration không khôi phục được (dòng ghi tay, thiếu đề).
        db.add(ExerciseVersion(id="L02-Q06-v2", exercise_id="L02-Q06", version=2, answer_key={"expected": "?"},
                               grader_config={}, status="published", snapshot_origin="missing"))
        db.commit()
    client = client_for(factory)
    lesson = client.get("/api/v1/lessons/L02").json()
    assert "L02-Q06" not in [x["id"] for x in lesson["exercises"]]
    user = new_user(factory)
    for vid in ("L02-Q06-v2", "L02-Q06-v1"):
        assert client.post("/api/v1/attempts", headers=auth(user), json={"exercise_version_id": vid, "answer": "x"}).status_code == 404


# --- Xóa mềm (retired) và câu biến mất khỏi nguồn ---------------------------------------------------

def test_retired_exercise_is_soft_deleted_and_history_kept(factory):
    seed(factory)
    user = new_user(factory)
    kept = answer(factory, user, "L02-Q06-v1", "C D E")
    changed = specs()
    item_of(changed, "L02-Q06")["retired"] = True
    seed(factory, changed)
    with factory() as db:
        exercise = db.get(Exercise, "L02-Q06")
        assert exercise.deleted_at is not None and exercise.active is False
        assert db.get(ExerciseVersion, "L02-Q06-v1") is not None
        assert db.get(Attempt, kept.id).exercise_version_id == "L02-Q06-v1"
    lesson = client_for(factory).get("/api/v1/lessons/L02").json()
    assert "L02-Q06" not in [x["id"] for x in lesson["exercises"]]
    for item in next(s for s in LESSON_SPECS if s["id"] == "L02")["exercises"][:5]:
        answer(factory, user, f'{item["id"]}-v1', correct_answer(item))
    with factory() as db:
        assert complete_lesson(db, user, "L02")[0].status == "completed"
    seed(factory)  # bỏ retired: khôi phục câu
    with factory() as db:
        assert db.get(Exercise, "L02-Q06").deleted_at is None


def test_exercise_removed_from_spec_without_retired_fails(factory):
    seed(factory)
    changed = specs()
    lesson = next(s for s in changed if s["id"] == "L02")
    lesson["exercises"] = [i for i in lesson["exercises"] if i["id"] != "L02-Q06"]
    with pytest.raises(SeedConflictError) as caught:
        seed(factory, changed)
    assert [(c.code, c.target) for c in caught.value.conflicts] == [("SEED_EXERCISE_MISSING", "L02-Q06")]


# --- Hoàn thành bài khi có câu/phiên bản mới (6A) ---------------------------------------------------

def answer_all(factory, user: str, lesson_id: str) -> None:
    with factory() as db:
        exercises = db.scalars(select(Exercise).where(Exercise.lesson_id == lesson_id)).all()
        targets = [(current_version(e).id, item_of(LESSON_SPECS, e.id)) for e in exercises]
    for version_id, item in targets:
        assert answer(factory, user, version_id, correct_answer(item)).correct, version_id


def test_correct_on_old_version_still_counts_after_new_version(factory):
    seed(factory)
    user = new_user(factory)
    answer_all(factory, user, "L01")
    bump_l01_q01(factory)
    with factory() as db:
        assert complete_lesson(db, user, "L01")[0].status == "completed"


def test_completed_lesson_stays_completed_when_question_added(factory):
    seed(factory)
    user = new_user(factory)
    answer_all(factory, user, "L02")
    with factory() as db:
        progress, _ = complete_lesson(db, user, "L02")
        completed_at = progress.completed_at.replace(tzinfo=None)
    seed(factory, draft_spec(status="published"))
    with factory() as db:
        again, _ = complete_lesson(db, user, "L02")
        # SQLite trả datetime không múi giờ; so phần giá trị để thấy completed_at không bị viết lại.
        assert again.status == "completed" and again.completed_at.replace(tzinfo=None) == completed_at
    overview = client_for(factory).get("/api/v1/learning/overview", headers=auth(user)).json()
    row = next(r for r in overview["lessons"] if r["lesson_id"] == "L02")
    assert row["status"] == "completed" and row["exercise_count"] == 7 and row["practice_progress_percent"] == 100


def test_started_lesson_must_answer_new_question(factory):
    seed(factory)
    user = new_user(factory)
    answer_all(factory, user, "L02")
    seed(factory, draft_spec(status="published"))
    with factory() as db:
        with pytest.raises(LessonNotMastered) as caught:
            complete_lesson(db, user, "L02")
        assert caught.value.remaining == ["L02-Q07"]
        assert db.scalar(select(func.count()).select_from(LessonProgress).where(
            LessonProgress.user_id == user, LessonProgress.status == "completed")) == 0


def test_wrong_attempts_counted_per_exercise_across_versions(factory):
    # D-2: đếm số lần sai theo câu, nên ra phiên bản mới không làm người học phải sai lại từ đầu mới thấy lời giải.
    seed(factory)
    user = new_user(factory)
    client = client_for(factory)
    for _ in range(2):
        client.post("/api/v1/attempts", headers=auth(user), json={"exercise_version_id": "L01-Q01-v4", "answer": "P5"})
    bump_l01_q01(factory)
    result = client.post("/api/v1/attempts", headers=auth(user), json={"exercise_version_id": "L01-Q01-v5", "answer": "P5"}).json()
    assert result["wrong_attempts"] == 3 and result["explanation"]


# --- Lưới ORM ---------------------------------------------------------------------------------------

def test_orm_guard_blocks_edits_and_deletes(factory):
    seed(factory)
    cases = [
        lambda v, e: setattr(v, "prompt", "sửa tay"),
        lambda v, e: setattr(v, "answer_key", {"expected": "x"}),
        lambda v, e: setattr(v, "status", "draft"),
        lambda v, e: setattr(e, "skill_id", "pitch.spelling"),
    ]
    for mutate in cases:
        with factory() as db:
            mutate(db.get(ExerciseVersion, "L01-Q01-v4"), db.get(Exercise, "L01-Q01"))
            with pytest.raises(ImmutableVersionError):
                db.flush()
    with factory() as db:
        db.delete(db.get(ExerciseVersion, "L01-Q01-v4"))
        with pytest.raises(ImmutableVersionError):
            db.flush()
    with factory() as db:
        version = db.get(ExerciseVersion, "L01-Q01-v4")
        version.answer_key = dict(version.answer_key)  # cùng giá trị: không phải sửa thật
        db.flush()
