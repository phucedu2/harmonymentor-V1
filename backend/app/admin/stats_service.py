"""Thống kê cho Quản trị viên: số liệu người học để vẽ biểu đồ. Chỉ tính người học thật, bỏ lượt thử của Admin
(is_test, nguyên tắc 8) và người học mô phỏng (nguyên tắc 9). Gộp ở Python để chạy giống nhau trên SQLite và PostgreSQL."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import (Attempt, Exercise, ExerciseVersion, Lesson, LessonProgress, MasteryState, ReviewAttempt, ReviewState,
                         Skill, User)

MASTERY_BUCKETS = (("Chưa học", 0.0, 0.3), ("Đang học", 0.3, 0.65), ("Đủ để học tiếp", 0.65, 0.8), ("Thành thạo", 0.8, 1.01))


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


def _day(value: datetime) -> date:
    return _aware(value).date()


def overview(db: Session, days: int = 30, now: datetime | None = None) -> dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    since = now - timedelta(days=days)
    week = now - timedelta(days=7)

    learners = db.scalars(select(User).where(User.role == "learner", User.is_synthetic.is_(False))).all()
    learner_ids = {u.id for u in learners}

    attempts = [a for a in db.scalars(select(Attempt).where(Attempt.is_test.is_(False), Attempt.created_at >= since)).all()
                if a.user_id in learner_ids]
    review_rows = [r for r, owner in db.execute(
        select(ReviewAttempt, ReviewState.user_id).join(ReviewState, ReviewState.id == ReviewAttempt.review_state_id)
        .where(ReviewAttempt.created_at >= since)).all() if owner in learner_ids]

    active_week = {a.user_id for a in attempts if _aware(a.created_at) >= week}
    for r, owner in db.execute(select(ReviewAttempt, ReviewState.user_id).join(ReviewState, ReviewState.id == ReviewAttempt.review_state_id)
                               .where(ReviewAttempt.created_at >= week)).all():
        if owner in learner_ids:
            active_week.add(owner)

    # --- theo ngày ---
    per_day: dict[date, list[int]] = defaultdict(lambda: [0, 0])
    for a in attempts:
        cell = per_day[_day(a.created_at)]
        cell[0] += 1
        cell[1] += 1 if a.correct else 0
    review_per_day = Counter(_day(r.created_at) for r in review_rows)
    timeline = []
    for offset in range(days - 1, -1, -1):
        d = (now - timedelta(days=offset)).date()
        total, right = per_day.get(d, [0, 0])
        timeline.append({"date": d.isoformat(), "attempts": total, "correct": right, "reviews": review_per_day.get(d, 0)})

    # --- phễu từng bài ---
    lessons = db.scalars(select(Lesson).order_by(Lesson.order_index)).unique().all()
    progress = [p for p in db.scalars(select(LessonProgress)).all() if p.user_id in learner_ids]
    started = Counter(p.lesson_id for p in progress)
    completed = Counter(p.lesson_id for p in progress if p.status == "completed")
    funnel = [{"lesson_id": l.id, "title": l.title, "status": l.status, "started": started.get(l.id, 0), "completed": completed.get(l.id, 0),
               "completion_rate": round(completed.get(l.id, 0) / started[l.id], 3) if started.get(l.id) else None}
              for l in lessons if started.get(l.id) or l.status != "draft"]

    # --- kỹ năng và câu khó (mọi thời gian, lượt đầu tiên của mỗi người ở mỗi câu) ---
    skill_names = {s.id: s.name for s in db.scalars(select(Skill)).all()}
    first_try: dict[tuple[str, str], bool] = {}
    for a, exercise_id, skill_id in db.execute(
        select(Attempt, ExerciseVersion.exercise_id, Exercise.skill_id)
        .join(ExerciseVersion, ExerciseVersion.id == Attempt.exercise_version_id)
        .join(Exercise, Exercise.id == ExerciseVersion.exercise_id)
        .where(Attempt.is_test.is_(False)).order_by(Attempt.created_at)).all():
        if a.user_id in learner_ids and (a.user_id, exercise_id) not in first_try:
            first_try[(a.user_id, exercise_id)] = bool(a.correct)
    per_exercise: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    exercise_skill = {e.id: e.skill_id for e in db.scalars(select(Exercise)).all()}
    for (_, exercise_id), ok in first_try.items():
        per_exercise[exercise_id][0] += 1
        per_exercise[exercise_id][1] += 1 if ok else 0
    per_skill: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for exercise_id, (n, right) in per_exercise.items():
        cell = per_skill[exercise_skill.get(exercise_id, "?")]
        cell[0] += n
        cell[1] += right
    skills = sorted(({"skill_id": sid, "name": skill_names.get(sid, sid), "first_try_total": n, "first_try_correct_rate": round(r / n, 3)}
                     for sid, (n, r) in per_skill.items() if n), key=lambda x: x["first_try_correct_rate"])
    hardest = sorted(({"exercise_id": eid, "first_try_total": n, "first_try_correct_rate": round(r / n, 3)}
                      for eid, (n, r) in per_exercise.items() if n >= 3), key=lambda x: x["first_try_correct_rate"])[:8]

    # --- mastery ---
    scores = [m.score for m in db.scalars(select(MasteryState)).all() if m.user_id in learner_ids]
    mastery = [{"label": label, "count": sum(1 for s in scores if lo <= s < hi)} for label, lo, hi in MASTERY_BUCKETS]

    due_now = sum(1 for s in db.scalars(select(ReviewState).where(ReviewState.status == "active")).all()
                  if s.user_id in learner_ids and _aware(s.due_at) <= now)
    return {
        "generated_at": now.isoformat(), "days": days,
        "totals": {"learners": len(learners), "new_learners": sum(1 for u in learners if _aware(u.created_at) >= since),
                   "active_last_7_days": len(active_week), "attempts": len(attempts),
                   "correct_rate": round(sum(1 for a in attempts if a.correct) / len(attempts), 3) if attempts else None,
                   "lessons_completed": sum(completed.values()), "reviews": len(review_rows), "cards_due_now": due_now},
        "timeline": timeline, "funnel": funnel, "skills": skills, "hardest_exercises": hardest, "mastery": mastery,
    }
