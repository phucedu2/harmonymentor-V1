"""Source-audited seed content for Phase 0.4B.

Runtime content is now derived from ``curriculum_specs`` rather than the old frontend draft bank.
Lessons 1-4 are fully migrated; Lessons 5-8 keep metadata + source provenance only until Phase 1.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from .curriculum_specs import LESSON_SPECS, MIGRATED_LESSON_IDS
from .draft_specs import DRAFT_LESSON_SPECS, blocks_with_drafts
from .skill_graph import PREREQUISITES, SKILLS
from .source_registry import SOURCE_REGISTRY
from .versioning import (
    ORIGIN_MISSING,
    ORIGIN_SEED,
    SNAPSHOT_FIELDS,
    STATUS_DRAFT,
    STATUS_PUBLISHED,
    SeedConflict,
    SeedConflictError,
    content_hash,
    snapshot_from_row,
    snapshot_from_spec,
)
from ..db.models import (
    Attempt,
    Exercise,
    ExerciseVersion,
    Lesson,
    LessonBlock,
    LessonSource,
    ReviewItem,
    Skill,
    SkillPrerequisite,
    SourceWork,
    User,
)


def _upsert_lesson(db: Session, spec: dict) -> Lesson:
    lesson = db.get(Lesson, spec["id"])
    runtime_status = "reviewed" if spec["id"] in MIGRATED_LESSON_IDS else "source_audited"
    if spec.get("status") == STATUS_DRAFT:
        # Bài nháp (phuc-music): chỉ hiện khi bật SHOW_DRAFT_CONTENT, xem versioning.lesson_visible.
        runtime_status = STATUS_DRAFT
    if lesson is None:
        lesson = Lesson(
            id=spec["id"], order_index=spec["order"], track=spec["track"], title=spec["title"],
            status=runtime_status, objectives=spec["objectives"],
        )
        db.add(lesson)
    else:
        lesson.order_index = spec["order"]
        lesson.track = spec["track"]
        lesson.title = spec["title"]
        lesson.status = runtime_status
        lesson.objectives = spec["objectives"]
    return lesson


def _sync_sources(db: Session, lesson_id: str, sources: list[dict]) -> None:
    db.execute(delete(LessonSource).where(LessonSource.lesson_id == lesson_id))
    for source in sources:
        db.add(LessonSource(
            lesson_id=lesson_id,
            source_work_id=source["source_id"],
            locator=source["locator"],
            note=source.get("note"),
        ))


def _upsert_blocks(db: Session, spec: dict) -> None:
    # Blocks are presentation/content units and are not referenced by attempts. Rebuild the
    # lesson block sequence atomically so inserting Phase 1 checkpoints cannot collide with
    # the unique (lesson_id, position) constraint on an existing Phase 0.4B database.
    db.execute(delete(LessonBlock).where(LessonBlock.lesson_id == spec["id"]))
    db.flush()
    for position, (block_id, block_type, payload) in enumerate(blocks_with_drafts(spec), start=1):
        db.add(LessonBlock(
            id=block_id, lesson_id=spec["id"], position=position,
            block_type=block_type, payload=payload,
        ))


def _upsert_exercises(db: Session, spec: dict, now: datetime, conflicts: list[SeedConflict]) -> None:
    """Đồng bộ câu hỏi của một bài mà không bao giờ sửa phiên bản đã khóa (HM-003, ADR-006).

    Nội dung khác với phiên bản cùng id thì ghi xung đột; seed_initial_data rollback và báo lỗi.
    Không tự tăng version: cùng một câu phải mang cùng id phiên bản trên mọi máy.
    """
    # L01 was source-audited as v2. The beginner-pedagogy rewrite changes prompts,
    # answer guidance, and one diminished-triad target, so keep previous attempts traceable
    # by publishing the revised multi-key lesson exercises as v4.
    lesson_version = 4 if spec["id"] == "L01" else 1
    for position, item in enumerate(spec["exercises"], start=1):
        exercise = db.get(Exercise, item["id"])
        if item.get("retired"):
            # Câu bị bỏ: xóa mềm, giữ nguyên phiên bản và lượt làm.
            if exercise is not None and exercise.deleted_at is None:
                exercise.deleted_at = now
                exercise.active = False
            continue

        # Câu được sửa sau khi phát hành mang version riêng (curriculum_specs.q(version=...)).
        target_version = item.get("version") or lesson_version
        snapshot = snapshot_from_spec(item)
        if exercise is None:
            exercise = Exercise(id=item["id"], lesson_id=spec["id"], skill_id=item["skill"], position=position)
            db.add(exercise)
        elif exercise.lesson_id != spec["id"] or exercise.skill_id != item["skill"]:
            conflicts.append(SeedConflict(
                "SEED_IDENTITY_CHANGED", item["id"],
                f"đang thuộc {exercise.lesson_id}/{exercise.skill_id}, nguồn ghi {spec['id']}/{item['skill']}. "
                "Đổi bài hoặc kỹ năng thì tạo câu mới với id mới và đánh dấu câu cũ retired=True.",
            ))
            continue
        exercise.position = position
        exercise.active = True
        exercise.deleted_at = None
        # Bản sao trên exercises luôn theo phiên bản mới nhất trong nguồn; không dùng để chấm.
        exercise.kind = snapshot["kind"]
        exercise.prompt = snapshot["prompt"]
        exercise.options = snapshot["options"]
        exercise.grading_strategy = snapshot["grading_strategy"]

        version_id = f'{item["id"]}-v{target_version}'
        version = db.get(ExerciseVersion, version_id)
        status = item.get("status") or STATUS_PUBLISHED
        if version is None:
            existing = db.scalars(select(ExerciseVersion.version).where(ExerciseVersion.exercise_id == item["id"])).all()
            if existing and target_version <= max(existing):
                conflicts.append(SeedConflict(
                    "SEED_VERSION_NOT_INCREASING", version_id,
                    f"đã có v{max(existing)}; phiên bản mới phải lớn hơn mọi phiên bản đã có.",
                ))
                continue
            db.add(ExerciseVersion(
                id=version_id, exercise_id=item["id"], version=target_version,
                **snapshot, status=status, published_at=now if status == STATUS_PUBLISHED else None,
                content_hash=content_hash(snapshot), snapshot_origin=ORIGIN_SEED,
            ))
            continue

        if version.snapshot_origin == ORIGIN_MISSING:
            conflicts.append(SeedConflict(
                "SEED_SNAPSHOT_MISSING", version_id,
                "phiên bản này không khôi phục được đề bài gốc nên không xác nhận được nội dung. Tăng version.",
            ))
            continue
        if version.status == STATUS_PUBLISHED and status == STATUS_DRAFT:
            conflicts.append(SeedConflict(
                "SEED_STATUS_DOWNGRADE", version_id, "đã phát hành, không chuyển về draft được. Tăng version.",
            ))
            continue
        if version.content_hash != content_hash(snapshot):
            locked = version.status == STATUS_PUBLISHED or db.scalar(
                select(Attempt.id).where(Attempt.exercise_version_id == version_id).limit(1)
            ) is not None
            if locked:
                current = snapshot_from_row(version)
                conflicts.append(SeedConflict(
                    "SEED_VERSION_CHANGED", version_id,
                    "nội dung khác bản đã khóa. Giữ nguyên bản này và tăng version=n+1 trong curriculum_specs.q().",
                    [name for name in SNAPSHOT_FIELDS if current[name] != snapshot[name]],
                ))
                continue
            # Bản nháp chưa ai làm: sửa tại chỗ được, đây là lúc Đạt và người soạn còn đang chỉnh câu.
            for name, value in snapshot.items():
                setattr(version, name, value)
            version.content_hash = content_hash(snapshot)
        if version.status == STATUS_DRAFT and status == STATUS_PUBLISHED:
            version.status = STATUS_PUBLISHED
            version.published_at = now


def _check_missing_exercises(db: Session, specs: list[dict], conflicts: list[SeedConflict]) -> None:
    """Câu còn trong CSDL mà biến khỏi nguồn: phải khai báo retired=True, không tự xóa mềm (7A)."""
    in_spec = {item["id"] for spec in specs if spec["id"] in MIGRATED_LESSON_IDS for item in spec["exercises"]}
    lesson_ids = {spec["id"] for spec in specs if spec["id"] in MIGRATED_LESSON_IDS}
    orphans = db.scalars(select(Exercise.id).where(
        Exercise.lesson_id.in_(lesson_ids), Exercise.deleted_at.is_(None),
    )).all()
    for exercise_id in sorted(set(orphans) - in_spec):
        conflicts.append(SeedConflict(
            "SEED_EXERCISE_MISSING", exercise_id,
            "có trong CSDL nhưng không còn trong curriculum_specs. Giữ mục đó và đặt retired=True để xóa mềm.",
        ))


def _upsert_reviews(db: Session, spec: dict) -> None:
    for item in spec["review_items"]:
        review = db.get(ReviewItem, item["id"])
        if review is None:
            db.add(ReviewItem(
                id=item["id"], lesson_id=spec["id"], skill_id=item["skill"], mode=item["mode"],
                front=item["front"], back=item["back"], grading_strategy=item["strategy"],
                answer_key=item["answer_key"], grader_config=item["grader_config"],
                provenance=item["provenance"],
            ))
        else:
            review.lesson_id = spec["id"]
            review.skill_id = item["skill"]
            review.mode = item["mode"]
            review.front = item["front"]
            review.back = item["back"]
            review.grading_strategy = item["strategy"]
            review.answer_key = item["answer_key"]
            review.grader_config = item["grader_config"]
            review.provenance = item["provenance"]


def seed_initial_data(db: Session, lesson_specs: list[dict] | None = None) -> None:
    """Seed idempotent; gặp xung đột phiên bản thì rollback toàn bộ và raise SeedConflictError."""
    try:
        _seed(db, LESSON_SPECS + DRAFT_LESSON_SPECS if lesson_specs is None else lesson_specs)
    except BaseException:
        db.rollback()
        raise


def _seed(db: Session, lesson_specs: list[dict]) -> None:
    if db.get(User, "demo-user") is None:
        db.add(User(id="demo-user", display_name="Demo Learner"))

    # Source registry.
    for source_id, meta in SOURCE_REGISTRY.items():
        source = db.get(SourceWork, source_id)
        if source is None:
            db.add(SourceWork(id=source_id, title=meta["title"], author=meta["author"], url=meta["url"]))
        else:
            source.title = meta["title"]
            source.author = meta["author"]
            source.url = meta["url"]

    # Skill graph.
    for skill_id, name, domain in SKILLS:
        skill = db.get(Skill, skill_id)
        if skill is None:
            db.add(Skill(id=skill_id, name=name, domain=domain))
        else:
            skill.name = name
            skill.domain = domain
    db.flush()

    for skill_id, prerequisite_id in PREREQUISITES:
        exists = db.scalar(select(SkillPrerequisite).where(
            SkillPrerequisite.skill_id == skill_id,
            SkillPrerequisite.prerequisite_skill_id == prerequisite_id,
        ))
        if exists is None:
            db.add(SkillPrerequisite(skill_id=skill_id, prerequisite_skill_id=prerequisite_id))

    # Curriculum index and source matrix. order_index là UNIQUE: khi thứ tự đổi (SRS Bảng 7) thì
    # dời mọi bài sang số âm tạm trước, để cập nhật từng bài không đụng số của bài khác.
    existing = db.scalars(select(Lesson)).all()
    wanted = {spec["id"]: spec["order"] for spec in lesson_specs}
    if any(lesson.id in wanted and lesson.order_index != wanted[lesson.id] for lesson in existing):
        for index, lesson in enumerate((x for x in existing if x.id in wanted), start=1):
            lesson.order_index = -index
        db.flush()
    for spec in lesson_specs:
        _upsert_lesson(db, spec)
    db.flush()
    for spec in lesson_specs:
        _sync_sources(db, spec["id"], spec["sources"])

    # Full runtime migration only for L1-L4 in Phase 0.4B.
    now = datetime.now(timezone.utc)
    conflicts: list[SeedConflict] = []
    for spec in lesson_specs:
        if spec.get("status") == STATUS_DRAFT:
            _upsert_blocks(db, spec)  # bài nháp chỉ có dàn ý, chưa có câu hỏi/thẻ ôn
            continue
        if spec["id"] not in MIGRATED_LESSON_IDS:
            continue
        _upsert_blocks(db, spec)
        _upsert_exercises(db, spec, now, conflicts)
        _upsert_reviews(db, spec)
    _check_missing_exercises(db, lesson_specs, conflicts)
    if conflicts:
        raise SeedConflictError(conflicts)

    db.commit()
