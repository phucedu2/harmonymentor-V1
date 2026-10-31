"""SQLAlchemy persistence model for the learning contract.

The schema is deliberately small for the 2-3 week MVP.  Assessment results are versioned so a
future grader/content change never silently changes the meaning of an old attempt.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
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
    # Xóa mềm (nguyên tắc 7): câu retired vẫn giữ phiên bản và lượt làm, chỉ không hiện cho người học.
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    # kind/prompt/options/grading_strategy ở đây chỉ là bản sao của phiên bản mới nhất trong nguồn (ERD 04 Bảng 5).
    # Chấm bài và hiển thị luôn đọc từ ExerciseVersion (ADR-006).

    lesson: Mapped[Lesson] = relationship(back_populates="exercises")
    versions: Mapped[list["ExerciseVersion"]] = relationship(back_populates="exercise", cascade="all, delete-orphan")


class ExerciseVersion(Base):
    __tablename__ = "exercise_versions"
    __table_args__ = (
        UniqueConstraint("exercise_id", "version", name="uq_exercise_version"),
        CheckConstraint("status IN ('draft', 'published')", name="ck_exercise_versions_status"),
        CheckConstraint("snapshot_origin IN ('seed', 'git_history', 'missing')", name="ck_exercise_versions_origin"),
        # Chỉ bản cũ không khôi phục được (missing) mới được thiếu ảnh chụp; mọi bản khác phải đủ để chấm lại.
        CheckConstraint(
            "snapshot_origin = 'missing' OR (kind IS NOT NULL AND prompt IS NOT NULL "
            "AND grading_strategy IS NOT NULL AND content_hash IS NOT NULL)",
            name="ck_exercise_versions_snapshot",
        ),
    )

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    exercise_id: Mapped[str] = mapped_column(ForeignKey("exercises.id", ondelete="CASCADE"), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    # Ảnh chụp bất biến (HM-003): lượt làm cũ luôn hiển thị và chấm lại được theo đúng bản đã làm.
    kind: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    options: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)
    grading_strategy: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    answer_key: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    grader_config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    provenance: Mapped[Optional[list[dict[str, Any]]]] = mapped_column(JSON, nullable=True)
    # Mặc định phía CSDL là giá trị an toàn: dòng chèn tay thiếu thông tin thì bị ẩn (draft) và không được chấm (missing).
    status: Mapped[str] = mapped_column(String(16), server_default="draft")
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    snapshot_origin: Mapped[str] = mapped_column(String(16), server_default="missing")
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


# --- Bảo vệ phiên bản đã khóa ở tầng ORM (HM-003, ADR-006) ---------------------------------------
# Lưới này chặn mọi đường ghi qua SQLAlchemy (seed, Admin sau này). Câu SQL viết tay thì không đi qua đây:
# trên PostgreSQL có thêm trigger do migration PR-3 tạo; trên SQLite chỉ có lưới này.


class PracticeAttempt(Base):
    """Lượt làm ở trang Luyện tập (đề sinh ngẫu nhiên, không thuộc bài học) — FR-LRN-08 "lịch sử học tập".

    Tách khỏi `attempts` vì `attempts.exercise_version_id` bắt buộc trỏ tới câu đã phát hành (ADR-006),
    còn đề luyện tập do Music Engine sinh mỗi lần. Chỉ ghi lịch sử, KHÔNG cập nhật mastery: luyện tập
    có tính vào mastery hay không là quyết định còn mở của PR-5 (D-3). Bảng chưa có trong ERD tài liệu 04,
    xem ADR-009-de-xuat (chờ Thắng duyệt schema).
    """

    __tablename__ = "practice_attempts"
    __table_args__ = (CheckConstraint("kind IN ('chord', 'interval', 'scale', 'roman')", name="ck_practice_kind"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    kind: Mapped[str] = mapped_column(String(16))
    level: Mapped[Optional[str]] = mapped_column(String(8), nullable=True)
    question: Mapped[dict[str, Any]] = mapped_column(JSON)
    answer: Mapped[Any] = mapped_column(JSON)
    correct: Mapped[bool] = mapped_column(Boolean)
    primary_error: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    # Lượt của Admin không tính vào thống kê (nguyên tắc bất biến số 8).
    is_test: Mapped[bool] = mapped_column(Boolean, default=False, server_default=sa_false())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)

class CompositionProject(Base):
    """Dự án Harmony Lab (FR-17, tài liệu 04 Bảng 8 và mục 6.8): lưu ký hiệu, thời gian theo phách, không lưu âm thanh.

    Thêm `style` (mẫu nền pop/ballad/bossa/lofi) và `created_at`/`updated_at` so với ERD; xem ADR-010 (chờ Thắng duyệt).
    """

    __tablename__ = "composition_projects"
    __table_args__ = (
        CheckConstraint("tempo_bpm BETWEEN 60 AND 160", name="ck_composition_tempo"),
        CheckConstraint("bars BETWEEN 4 AND 8", name="ck_composition_bars"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    key: Mapped[str] = mapped_column(String(8))
    tempo_bpm: Mapped[int] = mapped_column(Integer)
    time_signature: Mapped[str] = mapped_column(String(8), default="4/4", server_default="4/4")
    bars: Mapped[int] = mapped_column(Integer)
    style: Mapped[str] = mapped_column(String(16))
    is_test: Mapped[bool] = mapped_column(Boolean, default=False, server_default=sa_false())
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    chord_events: Mapped[list["ChordEvent"]] = relationship(
        back_populates="project", cascade="all, delete-orphan", order_by="ChordEvent.start_beat")
    drum_events: Mapped[list["DrumEvent"]] = relationship(
        back_populates="project", cascade="all, delete-orphan", order_by="DrumEvent.start_beat")


class ChordEvent(Base):
    __tablename__ = "chord_events"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("composition_projects.id"), index=True)
    start_beat: Mapped[float] = mapped_column(Float)
    duration_beats: Mapped[float] = mapped_column(Float)
    symbol: Mapped[str] = mapped_column(String(32))

    project: Mapped[CompositionProject] = relationship(back_populates="chord_events")


class DrumEvent(Base):
    __tablename__ = "drum_events"
    __table_args__ = (CheckConstraint("drum IN ('kick', 'snare', 'hat')", name="ck_drum_kind"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("composition_projects.id"), index=True)
    drum: Mapped[str] = mapped_column(String(8))
    start_beat: Mapped[float] = mapped_column(Float)
    velocity: Mapped[int] = mapped_column(Integer)

    project: Mapped[CompositionProject] = relationship(back_populates="drum_events")


from sqlalchemy import event, inspect as sa_inspect, select  # noqa: E402

_LOCKED_VERSION_COLUMNS = (
    "id", "exercise_id", "version", "kind", "prompt", "options", "grading_strategy", "answer_key",
    "grader_config", "explanation", "provenance", "content_hash", "snapshot_origin",
)


def _has_attempts(connection, version_id: str) -> bool:
    return connection.execute(
        select(Attempt.id).where(Attempt.exercise_version_id == version_id).limit(1)
    ).first() is not None


def _really_changed(state, name: str) -> bool:
    # Gán lại đúng giá trị cũ vẫn để lại history; chỉ tính là đổi khi giá trị khác thật.
    history = state.attrs[name].history
    if not history.has_changes():
        return False
    if history.deleted and history.added:
        return history.deleted[0] != history.added[0]
    return True


def _old_value(state, name: str):
    history = state.attrs[name].history
    if history.deleted:
        return history.deleted[0]
    return getattr(state.object, name)


@event.listens_for(ExerciseVersion, "before_update")
def _guard_version_update(_mapper, connection, target: ExerciseVersion) -> None:
    from ..content.versioning import ImmutableVersionError

    state = sa_inspect(target)
    changed = [name for name in _LOCKED_VERSION_COLUMNS if _really_changed(state, name)]
    old_status = _old_value(state, "status")
    if old_status == "published" and target.status != "published":
        raise ImmutableVersionError(f"Phiên bản {target.id} đã phát hành, không được chuyển về {target.status}.")
    if changed and (old_status == "published" or _has_attempts(connection, _old_value(state, "id"))):
        raise ImmutableVersionError(
            f"Phiên bản {target.id} đã khóa (đã phát hành hoặc đã có lượt làm); không sửa {', '.join(changed)}. "
            "Hãy phát hành phiên bản mới."
        )


@event.listens_for(ExerciseVersion, "before_delete")
def _guard_version_delete(_mapper, connection, target: ExerciseVersion) -> None:
    from ..content.versioning import ImmutableVersionError

    if target.status == "published" or _has_attempts(connection, target.id):
        raise ImmutableVersionError(f"Không xóa phiên bản {target.id}: đã phát hành hoặc đã có lượt làm. Dùng xóa mềm câu hỏi.")


@event.listens_for(Exercise, "before_update")
def _guard_exercise_identity(_mapper, connection, target: Exercise) -> None:
    from ..content.versioning import ImmutableVersionError

    state = sa_inspect(target)
    moved = [name for name in ("lesson_id", "skill_id") if _really_changed(state, name)]
    if moved:
        has_versions = connection.execute(
            select(ExerciseVersion.id).where(ExerciseVersion.exercise_id == target.id).limit(1)
        ).first() is not None
        if has_versions:
            raise ImmutableVersionError(f"Câu {target.id} đã có phiên bản; đổi {', '.join(moved)} thì phải tạo câu mới với id mới.")
