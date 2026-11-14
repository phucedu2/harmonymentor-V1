from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

PracticeKind = Literal["chord", "interval", "scale", "roman"]
PracticeLevel = Literal["de", "vua", "kho"]


class PracticeAttemptIn(BaseModel):
    """Đề do trang Luyện tập sinh; máy chủ tự chấm bằng Music Engine, không nhận kết quả đúng/sai từ client."""

    kind: PracticeKind
    level: PracticeLevel | None = None
    question: dict[str, Any] = Field(..., description="chord: {symbol}; interval: {lower, upper}; scale: {tonic, scale_type}; roman: {key, chord}")
    answer: str | list[str]
    # GĐ5: "piano" = người học bấm phím trên piano ảo. Một phím đen có hai tên (C#/Db) nên phím không thể hiện
    # cách viết; máy chủ chấm theo lớp cao độ (Engine pitch_class_only) và nhắc cách viết chuẩn. Chỉ cho chord/scale.
    input: Literal["text", "piano"] = "text"


class PracticeAttemptOut(BaseModel):
    id: str
    kind: PracticeKind
    correct: bool
    expected: str | list[str]
    message_vi: str
    primary_error: str | None = None
    errors: list[dict[str, Any]] = Field(default_factory=list)
    convention_verified: bool | None = None


class PracticeHistoryItem(BaseModel):
    id: str
    kind: PracticeKind
    level: str | None = None
    question: dict[str, Any]
    answer: Any
    correct: bool
    primary_error: str | None = None
    created_at: datetime


class PracticeKindStat(BaseModel):
    kind: PracticeKind
    attempts: int
    correct: int


class PracticeHistoryOut(BaseModel):
    items: list[PracticeHistoryItem]
    stats: list[PracticeKindStat]
