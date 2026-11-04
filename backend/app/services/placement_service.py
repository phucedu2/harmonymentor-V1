"""Bài kiểm tra đầu vào (UC-06, FR-LRN-12, C9 của nhiệm vụ pipeline AI).

Chỉ dùng câu đã xuất bản sẵn có (không tạo câu mới chưa qua duyệt). 12 câu, mỗi câu một kỹ năng
MVP, theo thứ tự bài L01 → L04 nên đi từ dễ đến khó và trải đều 7 nhóm có dữ liệu.
Lượt làm placement KHÔNG ghi vào `attempts`: nếu ghi, lượt làm câu đó trong bài sau này thành "đúng
lặp lại" và không được cộng (S7), tức là người làm placement bị thiệt.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..content import versioning
from ..db.models import Exercise, ExerciseVersion, PlacementResult
from . import mastery_service
from .grading_service import grade_payload

# 13 kỹ năng MVP, đề 02 yêu cầu 12 câu: bỏ function.predominant vì tonic/dominant/progression đã phủ
# nhóm progressions (5 kỹ năng). Danh sách chờ Đạt duyệt; đổi ở đây không cần migration.
PLACEMENT_SKILLS: tuple[str, ...] = (
    "pitch.spelling", "interval.naming", "chord.triad_formula", "chord.triad_build",
    "scale.major", "chord.seventh_quality", "chord.seventh_build", "roman.major_seventh",
    "function.tonic", "function.dominant", "function.progression", "progression.ii_v_i",
)


class PlacementAlreadyDone(Exception):
    pass


def questions(db: Session) -> list[tuple[ExerciseVersion, Exercise]]:
    out = []
    for skill_id in PLACEMENT_SKILLS:
        exercises = db.scalars(select(Exercise).where(Exercise.skill_id == skill_id)
                               .order_by(Exercise.lesson_id, Exercise.position, Exercise.id)).all()
        for exercise in exercises:
            # Chỉ bản published: placement là đo năng lực thật, không dùng câu nháp kể cả ở dev.
            version = versioning.current_version(exercise, {"published"})
            if version is not None and version.snapshot_origin != "missing":
                out.append((version, exercise))
                break
    return out


def status(db: Session, user_id: str) -> str:
    row = db.get(PlacementResult, user_id)
    return "not_started" if row is None else row.status


def submit(db: Session, user_id: str, answers: list[dict], confirm_retake: bool, now: datetime | None = None) -> list[dict]:
    now = now or datetime.now(timezone.utc)
    row = db.get(PlacementResult, user_id)
    if row is not None and row.status == "completed" and not confirm_retake:
        raise PlacementAlreadyDone()
    allowed = {v.id: (v, e) for v, e in questions(db)}
    graded: list[dict] = []
    for entry in answers:
        pair = allowed.get(entry["exercise_version_id"])
        if pair is None:
            continue  # không nhận câu ngoài đề placement (không cho client tự chọn kỹ năng)
        version, exercise = pair
        outcome = grade_payload(version.grading_strategy, version.answer_key, version.grader_config, entry.get("answer"))
        graded.append({"exercise_version_id": version.id, "skill_id": exercise.skill_id,
                       "answer": entry.get("answer"), "correct": outcome.correct})
    if row is None:
        row = PlacementResult(user_id=user_id, status="completed", answers=graded, taken_count=1, completed_at=now)
        db.add(row)
    else:
        row.taken_count = (row.taken_count or 0) + 1
        row.status, row.answers, row.completed_at = "completed", graded, now
    db.flush()
    mastery_service.apply_placement(db, user_id, graded, now)
    db.commit()
    return graded


def skip(db: Session, user_id: str, now: datetime | None = None) -> None:
    now = now or datetime.now(timezone.utc)
    row = db.get(PlacementResult, user_id)
    if row is None:
        db.add(PlacementResult(user_id=user_id, status="skipped", answers=[], taken_count=0, completed_at=now))
        db.commit()
