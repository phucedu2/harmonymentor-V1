"""Định dạng câu trả lời JSON của AI Tutor (04 Bảng 13) và cách kiểm.

Schema gửi cho Gemini (response_json_schema) không có trường verified: AI không được tự khai đã kiểm.
Nếu AI vẫn gửi verified thì máy chủ bỏ đi (đề GĐ3 mục 6)."""

from __future__ import annotations

import json
from typing import Any, Literal, Optional

from pydantic import BaseModel, Field, ValidationError, field_validator

from .intent import INTENTS

TOOLS = ("get_chord_tones", "get_scale", "identify_interval")

LLM_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "reply": {"type": "string", "description": "Câu trả lời tiếng Việt, xưng mình, gọi bạn, tối đa khoảng 120 từ."},
        "citations": {"type": "array", "items": {"type": "object", "properties": {
            "lesson_id": {"type": "string"}, "block_id": {"type": "string"}, "title": {"type": "string"}},
            "required": ["lesson_id", "block_id", "title"]}},
        "engine_claims": {"type": "array", "items": {"type": "object", "properties": {
            "tool": {"type": "string", "enum": list(TOOLS)},
            "args": {"type": "object", "properties": {
                "symbol": {"type": "string"}, "tonic": {"type": "string"}, "scale_type": {"type": "string"},
                "lower": {"type": "string"}, "upper": {"type": "string"}}},
            "result": {"type": "string", "description": "Kết quả AI khẳng định, ví dụ 'C E G Bb' hoặc 'P5'."}},
            "required": ["tool", "args", "result"]}},
        "hint_level": {"type": "integer", "minimum": 0, "maximum": 3},
        "suggested_actions": {"type": "array", "items": {"type": "string"}},
        "intent": {"type": "string", "enum": list(INTENTS)},
    },
    "required": ["reply", "citations", "engine_claims", "hint_level", "suggested_actions", "intent"],
}


class Citation(BaseModel):
    lesson_id: str = Field(max_length=16)
    block_id: str = Field(max_length=40)
    title: str = Field(max_length=200)


class Claim(BaseModel):
    tool: Literal["get_chord_tones", "get_scale", "identify_interval"]
    args: dict[str, str]
    result: str = Field(max_length=200)

    @field_validator("args", mode="before")
    @classmethod
    def _drop_empty(cls, v):
        return {k: str(x) for k, x in (v or {}).items() if x not in (None, "")}


class TutorAnswer(BaseModel):
    reply: str = Field(min_length=1, max_length=4000)
    citations: list[Citation] = Field(default_factory=list, max_length=8)
    engine_claims: list[Claim] = Field(default_factory=list, max_length=12)
    hint_level: int = Field(0, ge=0, le=3)
    suggested_actions: list[str] = Field(default_factory=list, max_length=5)
    quiz: Optional[dict[str, Any]] = None
    intent: Literal["concept", "explain_error", "quiz", "study_advice", "composition", "out_of_scope"]


def parse_answer(text: str) -> TutorAnswer | None:
    """None khi sai định dạng: dịch vụ yêu cầu soạn lại một lần rồi dùng dự phòng."""
    try:
        data = json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(data, dict):
        return None
    for claim in data.get("engine_claims") or []:
        if isinstance(claim, dict):
            claim.pop("verified", None)  # không tin cờ AI tự khai
    data["quiz"] = None  # GĐ3 chưa sinh quiz bằng AI (quiz_items cần Music Engine sinh đáp án, 04 Bảng 7)
    try:
        return TutorAnswer.model_validate(data)
    except ValidationError:
        return None
