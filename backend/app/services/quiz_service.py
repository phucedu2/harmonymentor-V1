"""Quiz theo kỹ năng (FR-14 rút gọn, FR-AI-18).

Bản rút gọn: KHÔNG sinh câu mới bằng AI. Quiz là tối đa N câu có sẵn trong ngân hàng của đúng kỹ năng đó, mỗi câu
đã được Music Engine kiểm đáp án khi phát hành. Vì vậy mọi câu đều chấm tất định, và lượt làm đi qua /attempts nên
mastery cập nhật đúng luật D-3 như làm trong bài. Ưu tiên câu chưa làm, rồi câu từng sai, rồi câu đã đúng."""

from __future__ import annotations

import random
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..content import versioning
from ..db.models import Attempt, Exercise, ExerciseVersion, Skill
from .grading_service import is_self_check
from .learning_service import visible_lessons

MAX_QUIZ = 10


def build_quiz(db: Session, user_id: str, skill_id: str, n: int = MAX_QUIZ, seed: int | None = None) -> dict[str, Any]:
    if db.get(Skill, skill_id) is None:
        raise LookupError("SKILL_NOT_FOUND")
    n = max(1, min(int(n), MAX_QUIZ))
    lesson_ids = {lesson.id for lesson in visible_lessons(db)}
    exercises = [e for e in db.scalars(select(Exercise).where(Exercise.skill_id == skill_id)).unique().all()
                 if e.lesson_id in lesson_ids]
    pool: list[tuple[ExerciseVersion, Exercise]] = []
    for exercise in exercises:
        version = versioning.current_version(exercise)
        if version is None or is_self_check(version.grading_strategy, version.grader_config or {}):
            continue  # câu tự đánh giá (thẻ ý mở) không chấm được tự động
        pool.append((version, exercise))

    first_try: dict[str, bool] = {}
    ids = [e.id for _, e in pool]
    if ids:
        rows = db.execute(select(Attempt, ExerciseVersion.exercise_id).join(ExerciseVersion, ExerciseVersion.id == Attempt.exercise_version_id)
                          .where(Attempt.user_id == user_id, Attempt.is_test.is_(False), ExerciseVersion.exercise_id.in_(ids))
                          .order_by(Attempt.created_at)).all()
        ever_wrong: set[str] = set()
        for attempt, exercise_id in rows:
            first_try.setdefault(exercise_id, True)
            if not attempt.correct:
                ever_wrong.add(exercise_id)
        first_try = {k: (k not in ever_wrong) for k in first_try}

    def bucket(item: tuple[ExerciseVersion, Exercise]) -> int:
        seen = first_try.get(item[1].id)
        return 0 if seen is None else (1 if seen is False else 2)  # chưa làm → từng sai → đã đúng

    rng = random.Random(seed)
    rng.shuffle(pool)
    pool.sort(key=bucket)
    chosen = pool[:n]
    rng.shuffle(chosen)
    return {"skill_id": skill_id, "requested": n, "available": len(pool), "questions": [
        {"exercise_id": e.id, "exercise_version_id": v.id, "skill_id": e.skill_id, "kind": v.kind, "prompt": v.prompt,
         "options": v.options, "lesson_id": e.lesson_id} for v, e in chosen]}
