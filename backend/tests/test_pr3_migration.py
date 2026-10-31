"""PR-3 (HM-003): migration d3a7f1c2e905 trên CSDL có dữ liệu kế thừa.

Fixture `fixtures/pr3_csdl_ke_thua.json` là bản sao một CSDL thật dựng bằng code cũ: seed bằng commit 5cd49d4,
làm bài (có lượt làm trên L03-Q05-v1 chấm rubric), seed lại bằng main f0d3dac (L03-Q05 thành exact), và một
dòng L01-Q01-v1 giả lập bản có từ trước repo. Mỗi test dựng CSDL ở revision b2c4e6f80a13, nạp fixture,
rồi chạy `alembic upgrade head` như trên máy thật.

SQLite chạy trong job SQLite của CI. Bản PostgreSQL (thêm trigger) chỉ chạy khi TEST_DATABASE_URL hợp lệ,
trong một schema tên ngẫu nhiên và chỉ xóa đúng schema đó (pg_test_db.py).
"""

from __future__ import annotations

import importlib.util
import json
import os
from datetime import datetime
from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import command
from alembic.config import Config
from sqlalchemy.orm import Session, sessionmaker

from app.content.seed_data import seed_initial_data
from app.content.versioning import SNAPSHOT_FIELDS, SeedConflictError, content_hash, current_version
from app.core.config import settings
from app.db.models import Attempt, Exercise, ExerciseVersion
from app.services.grading_service import grade_payload
from app.services.learning_service import ExerciseVersionSuperseded, submit_attempt
from tests.pg_test_db import create_isolated_engine, drop_isolated_schema, new_schema_name, unsafe_reason

BACKEND = Path(__file__).resolve().parents[1]
FIXTURE = json.loads((BACKEND / "tests" / "fixtures" / "pr3_csdl_ke_thua.json").read_text(encoding="utf-8"))["tables"]
BEFORE_PR3 = "b2c4e6f80a13"
PR3 = "d3a7f1c2e905"
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL", "")
PG_UNSAFE = unsafe_reason(TEST_DATABASE_URL, settings.database_url)

BACKENDS = [
    pytest.param("sqlite", id="sqlite"),
    pytest.param("postgres", id="postgres", marks=[
        pytest.mark.postgres, pytest.mark.skipif(PG_UNSAFE is not None, reason=PG_UNSAFE or ""),
    ]),
]


def _load_migration():
    path = BACKEND / "migrations" / "versions" / "20261027_pr3_exercise_version_snapshot.py"
    spec = importlib.util.spec_from_file_location("pr3_migration", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def alembic_to(engine: sa.Engine, revision: str, *, downgrade: bool = False) -> None:
    # Config không gắn alembic.ini để env.py không gọi fileConfig (sẽ tắt logger của các test khác).
    cfg = Config()
    cfg.set_main_option("script_location", str(BACKEND / "migrations"))
    with engine.begin() as connection:
        cfg.attributes["connection"] = connection
        (command.downgrade if downgrade else command.upgrade)(cfg, revision)


def load_fixture(engine: sa.Engine, mutate=None) -> None:
    tables = {name: [dict(r) for r in rows] for name, rows in FIXTURE.items()}
    if mutate:
        mutate(tables)
    meta = sa.MetaData()
    with engine.begin() as conn:
        for name in ("skills", "lessons", "users", "exercises", "exercise_versions", "attempts"):
            table = sa.Table(name, meta, autoload_with=conn)
            rows = []
            for row in tables[name]:
                fixed = dict(row)
                for column in table.columns:
                    if isinstance(column.type, sa.DateTime) and isinstance(fixed.get(column.name), str):
                        fixed[column.name] = datetime.fromisoformat(fixed[column.name])
                rows.append(fixed)
            conn.execute(table.insert(), rows)


@pytest.fixture(params=BACKENDS)
def legacy_engine(request, tmp_path):
    """Engine của một CSDL kế thừa ở revision trước PR-3, đã nạp fixture."""
    if request.param == "sqlite":
        engine = sa.create_engine(f"sqlite:///{tmp_path / 'legacy.db'}", future=True)
        cleanup = engine.dispose
    else:
        schema = new_schema_name()
        engine = create_isolated_engine(TEST_DATABASE_URL, schema)

        def cleanup():
            engine.dispose()
            drop_isolated_schema(TEST_DATABASE_URL, schema)
    try:
        alembic_to(engine, BEFORE_PR3)
        yield engine
    finally:
        cleanup()


def snapshot_table(engine, sql: str) -> list[tuple]:
    with engine.connect() as conn:
        return [tuple(r) for r in conn.execute(sa.text(sql))]


def session_factory(engine):
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, class_=Session)


ATTEMPTS_SQL = "SELECT id, user_id, exercise_version_id, answer, correct, score, created_at FROM attempts ORDER BY id"
VERSION_CORE_SQL = ("SELECT id, exercise_id, version, answer_key, grader_config, explanation, provenance, created_at "
                    "FROM exercise_versions ORDER BY id")


def test_upgrade_keeps_every_row_and_restores_only_existing_versions(legacy_engine):
    load_fixture(legacy_engine)
    attempts_before = snapshot_table(legacy_engine, ATTEMPTS_SQL)
    versions_before = snapshot_table(legacy_engine, VERSION_CORE_SQL)
    exercises_before = snapshot_table(legacy_engine, "SELECT id, lesson_id, skill_id FROM exercises ORDER BY id")

    # Nâng đúng tới PR-3 (không phải "head"): migration sau PR-3 (vd practice_attempts) có test riêng.
    alembic_to(legacy_engine, PR3)

    # Không mất, không đổi, không thêm dòng nào; chỉ thêm cột.
    assert snapshot_table(legacy_engine, ATTEMPTS_SQL) == attempts_before
    assert snapshot_table(legacy_engine, VERSION_CORE_SQL) == versions_before
    assert snapshot_table(legacy_engine, "SELECT id, lesson_id, skill_id FROM exercises ORDER BY id") == exercises_before
    assert len(attempts_before) == 8 and len(versions_before) == 33
    origins = dict(snapshot_table(legacy_engine, "SELECT id, snapshot_origin FROM exercise_versions"))
    assert origins.pop("L01-Q01-v1") == "missing"
    assert set(origins.values()) == {"git_history"}
    # Bản cũ chỉ được khôi phục nếu thật sự có trong CSDL: L01-Q0x-v2 không có ở đây nên không được tạo ra.
    assert "L01-Q02-v2" not in origins
    assert set(snapshot_table(legacy_engine, "SELECT DISTINCT status FROM exercise_versions")) == {("published",)}
    assert snapshot_table(legacy_engine, "SELECT version_num FROM alembic_version") == [(PR3,)]


def test_old_rubric_version_keeps_its_meaning_after_upgrade(legacy_engine):
    load_fixture(legacy_engine)
    alembic_to(legacy_engine, "head")
    factory = session_factory(legacy_engine)
    with factory() as db:
        v1 = db.get(ExerciseVersion, "L03-Q05-v1")
        v2 = db.get(ExerciseVersion, "L03-Q05-v2")
        assert (v1.grading_strategy, v1.options) == ("rubric", None)
        assert v1.prompt.startswith("Vì sao không nên gán chức năng")
        assert (v2.grading_strategy, len(v2.options)) == ("exact", 4)
        # Chấm lại MỌI lượt cũ theo ảnh chụp của chính phiên bản đó: ra đúng như kết quả đã lưu.
        checked = 0
        for attempt in db.scalars(sa.select(Attempt)).all():
            version = db.get(ExerciseVersion, attempt.exercise_version_id)
            if version.snapshot_origin == "missing":
                continue
            regrade = grade_payload(version.grading_strategy, version.answer_key, version.grader_config, attempt.answer)
            assert regrade.correct == attempt.correct, (version.id, attempt.answer)
            checked += 1
        assert checked == 7
        with pytest.raises(ExerciseVersionSuperseded) as caught:
            submit_attempt(db, "legacy-learner", "L03-Q05-v1", "ngữ cảnh")
        assert caught.value.current_version_id == "L03-Q05-v2"


def test_seed_after_upgrade_is_idempotent(legacy_engine):
    load_fixture(legacy_engine)
    alembic_to(legacy_engine, "head")
    before = snapshot_table(legacy_engine, "SELECT id, content_hash, snapshot_origin, status FROM exercise_versions ORDER BY id")
    factory = session_factory(legacy_engine)
    for _ in range(2):
        with factory() as db:
            seed_initial_data(db)
    assert snapshot_table(legacy_engine, "SELECT id, content_hash, snapshot_origin, status FROM exercise_versions ORDER BY id") == before
    with factory() as db:
        # Câu L01-Q01 vẫn hiện bằng v4 dù có một bản cũ v1 không khôi phục được.
        assert current_version(db.get(Exercise, "L01-Q01")).id == "L01-Q01-v4"


def test_current_version_not_matching_source_is_marked_missing(legacy_engine):
    def edit_prompt_without_bump(tables):
        # Ai đó sửa đề trong nguồn mà quên tăng version: exercises mang đề lạ so với git.
        row = next(r for r in tables["exercises"] if r["id"] == "L02-Q01")
        row["prompt"] = "Đề đã bị sửa mà không tăng version"

    load_fixture(legacy_engine, edit_prompt_without_bump)
    alembic_to(legacy_engine, "head")
    assert snapshot_table(legacy_engine, "SELECT snapshot_origin, prompt FROM exercise_versions WHERE id = 'L02-Q01-v1'") == [("missing", None)]
    factory = session_factory(legacy_engine)
    with factory() as db:
        assert current_version(db.get(Exercise, "L02-Q01")) is None
    before = snapshot_table(legacy_engine, VERSION_CORE_SQL)
    with factory() as db:
        with pytest.raises(SeedConflictError) as caught:
            seed_initial_data(db)
    assert [(c.code, c.target) for c in caught.value.conflicts] == [("SEED_SNAPSHOT_MISSING", "L02-Q01-v1")]
    assert snapshot_table(legacy_engine, VERSION_CORE_SQL) == before


def test_downgrade_is_refused(legacy_engine):
    load_fixture(legacy_engine)
    alembic_to(legacy_engine, PR3)
    with pytest.raises(RuntimeError, match="khôi phục CSDL từ bản sao lưu"):
        alembic_to(legacy_engine, BEFORE_PR3, downgrade=True)
    assert snapshot_table(legacy_engine, "SELECT version_num FROM alembic_version") == [(PR3,)]


@pytest.mark.postgres
@pytest.mark.skipif(PG_UNSAFE is not None, reason=PG_UNSAFE or "")
@pytest.mark.parametrize("sql", [
    "UPDATE exercise_versions SET prompt = 'sửa tay' WHERE id = 'L03-Q05-v1'",
    "UPDATE exercise_versions SET answer_key = '{\"expected\": \"X\"}' WHERE id = 'L01-Q01-v4'",
    "UPDATE exercise_versions SET grading_strategy = 'exact' WHERE id = 'L03-Q05-v1'",
    "UPDATE exercise_versions SET status = 'draft' WHERE id = 'L02-Q01-v1'",
    "UPDATE exercise_versions SET snapshot_origin = 'seed' WHERE id = 'L01-Q01-v1'",
    "DELETE FROM exercise_versions WHERE id = 'L02-Q01-v1'",
    "UPDATE exercises SET skill_id = 'pitch.spelling' WHERE id = 'L03-Q05'",
])
def test_postgres_trigger_blocks_direct_sql(sql):
    schema = new_schema_name()
    engine = create_isolated_engine(TEST_DATABASE_URL, schema)
    try:
        alembic_to(engine, BEFORE_PR3)
        load_fixture(engine)
        alembic_to(engine, "head")
        with pytest.raises(sa.exc.DBAPIError, match="IMMUTABLE"):
            with engine.begin() as conn:
                conn.execute(sa.text(sql))
        with engine.begin() as conn:
            # Bản sao đề trên exercises vẫn sửa được (seed cập nhật nó); chỉ danh tính câu bị khóa.
            conn.execute(sa.text("UPDATE exercises SET position = position WHERE id = 'L03-Q05'"))
    finally:
        engine.dispose()
        drop_isolated_schema(TEST_DATABASE_URL, schema)


def test_migration_hash_matches_application_hash():
    migration = _load_migration()
    known = migration.load_known_snapshots()
    assert len(known) == 38
    for version_id, snapshot in known.items():
        assert migration.content_hash(snapshot) == content_hash(snapshot), version_id
    assert migration.SNAPSHOT_FIELDS == SNAPSHOT_FIELDS


def test_tampered_snapshot_file_stops_migration(tmp_path, monkeypatch):
    migration = _load_migration()
    data = json.loads(migration.SNAPSHOT_FILE.read_text(encoding="utf-8"))
    data["versions"]["L03-Q05-v1"]["grading_strategy"] = "exact"
    tampered = tmp_path / "tampered.json"
    tampered.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(migration, "SNAPSHOT_FILE", tampered)
    with pytest.raises(RuntimeError, match="đã bị sửa"):
        migration.load_known_snapshots()
