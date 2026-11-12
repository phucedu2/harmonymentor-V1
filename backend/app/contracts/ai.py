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
    reason_code: Literal["content", "mastery", "due", "cf", "foundation", "route"]
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
    mode: Literal["full", "cold_start", "fallback"]
    weights_mode: Literal["full", "cold"]
    cf_source: Literal["real", "synthetic", "none"]
    fallback_reason: Optional[Literal["no_assessed_dims", "no_valid_neighbors", "cf_disabled"]] = None
    min_shared_dims: int
    neighbors_count: int
    content_source: Literal["embedding", "none"]
    draft_descriptions: bool
    few_eligible: bool
    route_fallback: bool = False
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


# --- AI Tutor (GĐ3, 04 mục 3.3 "Hỏi AI Tutor", Bảng 12, Bảng 13) ----------------------------------

class ChatContextIn(BaseModel):
    page: Optional[str] = Field(None, max_length=40)
    lesson_id: Optional[str] = Field(None, max_length=16)
    block_id: Optional[str] = Field(None, max_length=40)


class ChatMessageIn(BaseModel):
    session_id: Optional[str] = Field(None, max_length=36)
    message: str = Field(min_length=1, max_length=1000)
    context: Optional[ChatContextIn] = None


class ExplainAttemptIn(BaseModel):
    attempt_id: str = Field(min_length=1, max_length=64)
    # Bỏ trống: máy chủ tự tăng mức theo số lần đã hỏi cho lượt này (1 → 3).
    hint_level: Optional[int] = Field(None, ge=1, le=3)
    session_id: Optional[str] = Field(None, max_length=36)


class ChatCitationOut(BaseModel):
    lesson_id: str
    block_id: str
    title: str
    lesson_title: str


class EngineClaimOut(BaseModel):
    tool: str
    args: dict[str, str]
    claimed: str
    engine: Optional[str]
    status: Literal["verified", "contradicted", "unsupported"]
    origin: str


class ChatReplyOut(BaseModel):
    message_id: int
    session_id: str
    reply: str
    citations: list[ChatCitationOut]
    engine_claims: list[EngineClaimOut]
    verified: bool
    verified_label: Optional[str]
    intent: Literal["concept", "explain_error", "quiz", "study_advice", "composition", "out_of_scope",
                    "greeting", "help"]
    hint_level: int
    status: Literal["ok", "failed", "fallback"]
    suggested_actions: list[str]
    fallback_reason: Optional[str]
    retrieval_method: Optional[str]
    quiz: Optional[dict[str, Any]] = None
    quota_remaining_today: int
    attempt_id: Optional[str] = None
    next_hint_level: Optional[int] = None
    # Bộ định tuyến 4 luồng (ADR-017): luồng nào trả lời, nhãn nguồn hiện trên giao diện, bài gợi ý khi "không biết",
    # trang hướng dẫn khi hỏi cách dùng.
    flow: Optional[Literal["A", "B", "C", "D", "G"]] = None
    source_label: Optional[str] = None
    suggested_lesson: Optional[dict[str, Any]] = None
    help_page: Optional[dict[str, str]] = None


class ChatSessionOut(BaseModel):
    id: str
    mode: str
    created_at: datetime
    updated_at: datetime


class ChatHistoryItem(BaseModel):
    id: int
    role: str
    content: str
    intent: Optional[str]
    citations: list[dict[str, Any]]
    engine_claims: list[dict[str, Any]]
    hint_level: Optional[int]
    status: str
    created_at: datetime


class ChatRatingIn(BaseModel):
    stars: int = Field(ge=1, le=5)
    comment: Optional[str] = Field(None, max_length=1000)
