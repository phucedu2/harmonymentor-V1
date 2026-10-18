from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class SourceRefOut(BaseModel):
    source_id: str
    title: str
    author: str | None = None
    locator: str
    note: str | None = None
    url: str | None = None


class LessonBlockOut(BaseModel):
    id: str
    position: int
    block_type: str
    payload: dict[str, Any]


class ExerciseOut(BaseModel):
    id: str
    version_id: str
    version: int
    position: int
    kind: str
    prompt: str
    options: list[str] | None = None
    grading_strategy: str
    skill_id: str


class ReviewItemOut(BaseModel):
    id: str
    mode: str
    front: str
    back: str
    skill_id: str


class LessonSummaryOut(BaseModel):
    id: str
    order: int
    track: str
    title: str
    status: str
    objectives: list[str]
    block_count: int
    exercise_count: int
    review_item_count: int


class LessonDetailOut(LessonSummaryOut):
    blocks: list[LessonBlockOut]
    exercises: list[ExerciseOut]
    review_items: list[ReviewItemOut]
    sources: list[SourceRefOut]


class AttemptIn(BaseModel):
    user_id: str = "demo-user"
    exercise_version_id: str
    answer: Any


class AttemptErrorOut(BaseModel):
    code: str
    detail: dict[str, Any] = Field(default_factory=dict)


class AttemptOut(BaseModel):
    attempt_id: str
    user_id: str
    exercise_version_id: str
    correct: bool
    score: float
    primary_error: str | None = None
    feedback: str | None = None
    errors: list[AttemptErrorOut] = Field(default_factory=list)


class CompleteLessonIn(BaseModel):
    user_id: str = "demo-user"


class CompleteLessonOut(BaseModel):
    lesson_id: str
    user_id: str
    status: str
    completed_at: datetime
    activated_review_items: int
    first_review_due_at: datetime | None = None


ReviewRating = Literal["again", "hard", "good", "easy", "auto"]


class ReviewAnswerIn(BaseModel):
    user_id: str = "demo-user"
    answer: Any
    rating: ReviewRating = "auto"
    response_time_ms: int | None = Field(default=None, ge=0)


class ReviewStateOut(BaseModel):
    review_item_id: str
    lesson_id: str
    front: str
    mode: str
    skill_id: str
    stage: int
    interval_days: int
    due_at: datetime
    status: str


class ReviewAnswerOut(BaseModel):
    review_attempt_id: str
    review_item_id: str
    correct: bool
    rating_applied: str
    next_stage: int
    interval_days: int
    next_due_at: datetime
    feedback: str | None = None


class StartLessonOut(BaseModel):
    lesson_id: str
    user_id: str
    status: str
    started_at: datetime
    completed_at: datetime | None = None


class LessonLearningProgressOut(BaseModel):
    lesson_id: str
    order: int
    title: str
    track: str
    status: str
    started_at: datetime | None = None
    completed_at: datetime | None = None
    exercise_count: int
    attempted_exercises: int
    correct_exercises: int
    attempt_count: int
    correct_attempt_count: int
    practice_progress_percent: int
    attempted_exercise_ids: list[str] = Field(default_factory=list)
    correct_exercise_ids: list[str] = Field(default_factory=list)


class LearningOverviewOut(BaseModel):
    user_id: str
    total_lessons: int
    started_lessons: int
    completed_lessons: int
    due_reviews: int
    upcoming_reviews: int
    lessons: list[LessonLearningProgressOut]
