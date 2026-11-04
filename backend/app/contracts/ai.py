"""Hợp đồng API của pipeline AI (GĐ1: mastery, bài kiểm tra đầu vào; GĐ2: gợi ý, mục tiêu)."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field


class SkillMasteryOut(BaseModel):
    skill_id: str
    name: str
    srs_code: str
    group_code: str
    assessed: bool
    score: Optional[float] = None
    attempts_count: int = 0
    level: Literal["not_assessed", "learning", "weak", "ready", "mastered"]
    ready_threshold: float
    mastery_threshold: float


class MasteryOut(BaseModel):
    skill_group_map_version: str
    skills: list[SkillMasteryOut]


class PlacementQuestionOut(BaseModel):
    exercise_id: str
    exercise_version_id: str
    skill_id: str
    kind: str
    prompt: str
    options: Optional[list[str]] = None


class PlacementOut(BaseModel):
    status: Literal["not_started", "completed", "skipped"]
    questions: list[PlacementQuestionOut]


class PlacementAnswerIn(BaseModel):
    exercise_version_id: str = Field(max_length=80)
    answer: Any = None


class PlacementSubmitIn(BaseModel):
    answers: list[PlacementAnswerIn] = Field(default_factory=list, max_length=20)
    # Làm lại khi đã có kết quả phải xác nhận tường minh (nhiệm vụ GĐ1 mục 4).
    confirm_retake: bool = False


class PlacementResultItem(BaseModel):
    skill_id: str
    correct: bool
    score: float


class PlacementSubmitOut(BaseModel):
    status: Literal["completed"]
    results: list[PlacementResultItem]


# --- GĐ2: gợi ý bài học (04 mục 6.5, G-3 cách B) ---------------------------------------------

class RecComponentsOut(BaseModel):
    content: float
    mastery: float
    due: float
    cf: Optional[float] = None


class RecLessonOut(BaseModel):
    lesson_id: str
    order: int
    title: str
    score: float
    components: RecComponentsOut
    reason_code: Literal["content", "mastery", "due", "cf"]
    reason: str
    badge: str
    skills: list[str]
    label: Optional[str] = None


class ContinueLessonOut(BaseModel):
    lesson_id: str
    order: int
    title: str
    status: Literal["started"]


class RecommendOut(BaseModel):
    generated_at: datetime
    log_id: str
    algorithm_version: str
    skill_group_map_version: str
    weights_mode: Literal["full", "cold"]
    cf_source: Literal["real", "synthetic", "none"]
    fallback_reason: Optional[Literal["no_assessed_dims", "no_valid_neighbors"]] = None
    min_shared_dims: int
    neighbors_count: int
    content_source: Literal["embedding", "tfidf", "none"]
    draft_descriptions: bool
    few_eligible: bool
    continue_: list[ContinueLessonOut] = Field(alias="continue", serialization_alias="continue")
    next: list[RecLessonOut]
    review: list[RecLessonOut]

    model_config = {"populate_by_name": True}


class RecClickIn(BaseModel):
    lesson_id: str = Field(max_length=32)


class GoalIn(BaseModel):
    goal_text: Optional[str] = Field(default=None, max_length=500)


class GoalOut(BaseModel):
    goal_text: Optional[str] = None
    embedded: bool
    embedding_model: Optional[str] = None
