"""SQLAlchemy persistence model for the learning contract.

The schema is deliberately small for the 2-3 week MVP.  Assessment results are versioned so a
future grader/content change never silently changes the meaning of an old attempt.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy import false as sa_false, true as sa_true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(160))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    # Cột xác thực (ADR-001, ADR-004). email/hashed_password rỗng với demo-user cũ và người học mô phỏng.
    email: Mapped[Optional[str]] = mapped_column(String(320), unique=True, index=True, nullable=True)
    hashed_password: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    role: Mapped[str] = mapped_column(String(16), default="learner", server_default="learner")
    preferred_instrument: Mapped[Optional[str]] = mapped_column(String(16), nullable=True)
    goal_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=sa_true())
    is_synthetic: Mapped[bool] = mapped_column(Boolean, default=False, server_default=sa_false())


class RefreshToken(Base):
    """Refresh token đã cấp; chỉ lưu SHA-256 để lộ CSDL cũng không dùng lại được (NFR-18)."""

    __tablename__ = "refresh_tokens"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    domain: Mapped[str] = mapped_column(String(80), default="theory")


class SkillPrerequisite(Base):
    __tablename__ = "skill_prerequisites"
    __table_args__ = (UniqueConstraint("skill_id", "prerequisite_skill_id", name="uq_skill_prerequisite"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    skill_id: Mapped[str] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), index=True)
    prerequisite_skill_id: Mapped[str] = mapped_column(ForeignKey("skills.id", ondelete="CASCADE"), index=True)


class Lesson(Base):
    __tablename__ = "lessons"

    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    order_index: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    track: Mapped[str] = mapped_column(String(80))
    title: Mapped[str] = mapped_column(String(240))
    status: Mapped[str] = mapped_column(String(32), default="draft")
    objectives: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    blocks: Mapped[list["LessonBlock"]] = relationship(back_populates="lesson", cascade="all, delete-orphan")
    exercises: Mapped[list["Exercise"]] = relationship(back_populates="lesson", cascade="all, delete-orphan")
    review_items: Mapped[list["ReviewItem"]] = relationship(back_populates="lesson", cascade="all, delete-orphan")


class LessonBlock(Base):
    __tablename__ = "lesson_blocks"
    __table_args__ = (UniqueConstraint("lesson_id", "position", name="uq_lesson_block_position"),)

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    lesson_id: Mapped[str] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), index=True)
    position: Mapped[int] = mapped_column(Integer)
    block_type: Mapped[str] = mapped_column(String(40))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    lesson: Mapped[Lesson] = relationship(back_populates="blocks")


class SourceWork(Base):
    __tablename__ = "source_works"

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    title: Mapped[str] = mapped_column(String(300))
    author: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(800), nullable=True)


class LessonSource(Base):
    __tablename__ = "lesson_sources"
    __table_args__ = (UniqueConstraint("lesson_id", "source_work_id", "locator", name="uq_lesson_source"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lesson_id: Mapped[str] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), index=True)
    source_work_id: Mapped[str] = mapped_column(ForeignKey("source_works.id", ondelete="CASCADE"), index=True)
    locator: Mapped[str] = mapped_column(String(300))
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    lesson_id: Mapped[str] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), index=True)
    skill_id: Mapped[str] = mapped_column(ForeignKey("skills.id"), index=True)
    kind: Mapped[str] = mapped_column(String(40))
    prompt: Mapped[str] = mapped_column(Text)
    options: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    grading_strategy: Mapped[str] = mapped_column(String(40))
    position: Mapped[int] = mapped_column(Integer, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

    lesson: Mapped[Lesson] = relationship(back_populates="exercises")
    versions: Mapped[list["ExerciseVersion"]] = relationship(back_populates="exercise", cascade="all, delete-orphan")


class ExerciseVersion(Base):
    __tablename__ = "exercise_versions"
    __table_args__ = (UniqueConstraint("exercise_id", "version", name="uq_exercise_version"),)

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    exercise_id: Mapped[str] = mapped_column(ForeignKey("exercises.id", ondelete="CASCADE"), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    answer_key: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    grader_config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    provenance: Mapped[Optional[list[dict[str, Any]]]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    exercise: Mapped[Exercise] = relationship(back_populates="versions")


class Attempt(Base):
    __tablename__ = "attempts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    exercise_version_id: Mapped[str] = mapped_column(ForeignKey("exercise_versions.id"), index=True)
    answer: Mapped[Any] = mapped_column(JSON)
    correct: Mapped[bool] = mapped_column(Boolean)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    primary_error: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)


class AttemptError(Base):
    __tablename__ = "attempt_errors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    attempt_id: Mapped[str] = mapped_column(ForeignKey("attempts.id", ondelete="CASCADE"), index=True)
    code: Mapped[str] = mapped_column(String(100))
    detail: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)


class LessonProgress(Base):
    __tablename__ = "lesson_progress"
    __table_args__ = (UniqueConstraint("user_id", "lesson_id", name="uq_user_lesson_progress"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    lesson_id: Mapped[str] = mapped_column(ForeignKey("lessons.id"), index=True)
    status: Mapped[str] = mapped_column(String(32), default="started")
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class ReviewItem(Base):
    __tablename__ = "review_items"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    lesson_id: Mapped[str] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), index=True)
    skill_id: Mapped[str] = mapped_column(ForeignKey("skills.id"), index=True)
    mode: Mapped[str] = mapped_column(String(32), default="recall")
    front: Mapped[str] = mapped_column(Text)
    back: Mapped[str] = mapped_column(Text)
    grading_strategy: Mapped[str] = mapped_column(String(40), default="exact")
    answer_key: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    grader_config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    provenance: Mapped[Optional[list[dict[str, Any]]]] = mapped_column(JSON, nullable=True)

    lesson: Mapped[Lesson] = relationship(back_populates="review_items")


class ReviewState(Base):
    __tablename__ = "review_states"
    __table_args__ = (UniqueConstraint("user_id", "review_item_id", name="uq_user_review_item"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    review_item_id: Mapped[str] = mapped_column(ForeignKey("review_items.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(32), default="active")
    stage: Mapped[int] = mapped_column(Integer, default=0)
    interval_days: Mapped[int] = mapped_column(Integer, default=1)
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    success_streak: Mapped[int] = mapped_column(Integer, default=0)
    failure_count: Mapped[int] = mapped_column(Integer, default=0)
    last_reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)


class ReviewAttempt(Base):
    __tablename__ = "review_attempts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    review_state_id: Mapped[int] = mapped_column(ForeignKey("review_states.id", ondelete="CASCADE"), index=True)
    answer: Mapped[Any] = mapped_column(JSON)
    correct: Mapped[bool] = mapped_column(Boolean)
    rating: Mapped[str] = mapped_column(String(16), default="auto")
    response_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
