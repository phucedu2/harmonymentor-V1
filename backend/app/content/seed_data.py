"""Source-audited seed content for Phase 0.4B.

Runtime content is now derived from ``curriculum_specs`` rather than the old frontend draft bank.
Lessons 1-4 are fully migrated; Lessons 5-8 keep metadata + source provenance only until Phase 1.
"""

from __future__ import annotations

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from .curriculum_specs import LESSON_SPECS, MIGRATED_LESSON_IDS
from .skill_graph import PREREQUISITES, SKILLS
from .source_registry import SOURCE_REGISTRY
from ..db.models import (
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
    for position, (block_id, block_type, payload) in enumerate(spec["blocks"], start=1):
        db.add(LessonBlock(
            id=block_id, lesson_id=spec["id"], position=position,
            block_type=block_type, payload=payload,
        ))


def _upsert_exercises(db: Session, spec: dict) -> None:
    # L01 was source-audited as v2. The beginner-pedagogy rewrite changes prompts,
    # answer guidance, and one diminished-triad target, so keep previous attempts traceable
    # by publishing the revised multi-key lesson exercises as v4.
    target_version = 4 if spec["id"] == "L01" else 1
    for position, item in enumerate(spec["exercises"], start=1):
        exercise = db.get(Exercise, item["id"])
        if exercise is None:
            exercise = Exercise(
                id=item["id"], lesson_id=spec["id"], skill_id=item["skill"], kind=item["kind"],
                prompt=item["prompt"], options=item["options"], grading_strategy=item["strategy"],
                position=position, active=True,
            )
            db.add(exercise)
        else:
            exercise.lesson_id = spec["id"]
            exercise.skill_id = item["skill"]
            exercise.kind = item["kind"]
            exercise.prompt = item["prompt"]
            exercise.options = item["options"]
            exercise.grading_strategy = item["strategy"]
            exercise.position = position
            exercise.active = True

        version_id = f'{item["id"]}-v{target_version}'
        version = db.get(ExerciseVersion, version_id)
        if version is None:
            db.add(ExerciseVersion(
                id=version_id, exercise_id=item["id"], version=target_version,
                answer_key=item["answer_key"], grader_config=item["grader_config"],
                explanation=item["explanation"], provenance=item["provenance"],
            ))
        else:
            version.answer_key = item["answer_key"]
            version.grader_config = item["grader_config"]
            version.explanation = item["explanation"]
            version.provenance = item["provenance"]


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


def seed_initial_data(db: Session) -> None:
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

    # Curriculum index and source matrix for all eight lessons.
    for spec in LESSON_SPECS:
        _upsert_lesson(db, spec)
    db.flush()
    for spec in LESSON_SPECS:
        _sync_sources(db, spec["id"], spec["sources"])

    # Full runtime migration only for L1-L4 in Phase 0.4B.
    for spec in LESSON_SPECS:
        if spec["id"] not in MIGRATED_LESSON_IDS:
            continue
        _upsert_blocks(db, spec)
        _upsert_exercises(db, spec)
        _upsert_reviews(db, spec)

    db.commit()
