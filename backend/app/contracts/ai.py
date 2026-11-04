"""Hợp đồng API của pipeline AI (GĐ1: mastery, bài kiểm tra đầu vào)."""

from __future__ import annotations

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
