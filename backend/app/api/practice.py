from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..auth.deps import get_current_user
from ..ai.tutor.llm import LLMProvider
from ..api.ai_tutor import provider_dep
from ..contracts.practice import (
    OpenFeedbackIn,
    PracticeAttemptIn,
    PracticeAttemptOut,
    PracticeHistoryItem,
    PracticeHistoryOut,
    PracticeKindStat,
    PracticeOptionsIn,
)
from ..core.errors import AppError
from ..db.models import User
from ..db.session import get_db
from ..services.learning_service import ExerciseVersionSuperseded
from ..services.open_answer_service import NotOpenQuestion, open_feedback
from ..services.practice_mcq import OptionsUnavailable, make_options
from ..services.quiz_service import bank_skills, build_bank_set, build_quiz
from ..services.practice_service import PracticeInputInvalid, PracticeQuestionInvalid, practice_history, record_practice

router = APIRouter(prefix="/api/v1/practice", tags=["practice"])


@router.post("/attempts", response_model=PracticeAttemptOut)
def submit_practice(body: PracticeAttemptIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    try:
        row, result = record_practice(db, user, body.kind, body.level, body.question, body.answer, body.input)
    except PracticeQuestionInvalid as exc:
        raise AppError(422, "PRACTICE_QUESTION_INVALID", f"Đề luyện tập thiếu trường: {exc}.") from exc
    except PracticeInputInvalid as exc:
        raise AppError(422, "PRACTICE_INPUT_INVALID", f"Dạng bài {exc} chỉ trả lời bằng chữ, không bấm piano.") from exc
    return PracticeAttemptOut(
        id=row.id, kind=row.kind, correct=row.correct, expected=result["expected"], message_vi=result["message_vi"],
        primary_error=result.get("primary_error"), errors=result.get("errors", []),
        convention_verified=result.get("convention_verified"),
    )


@router.get("/history", response_model=PracticeHistoryOut)
def get_practice_history(limit: int = Query(default=20, ge=1, le=100), user: User = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    items, stats = practice_history(db, user.id, limit)
    return PracticeHistoryOut(
        items=[PracticeHistoryItem(id=i.id, kind=i.kind, level=i.level, question=i.question, answer=i.answer,
                                   correct=i.correct, primary_error=i.primary_error, created_at=i.created_at) for i in items],
        stats=[PracticeKindStat(**item) for item in stats],
    )


@router.get("/quiz")
def get_quiz(skill_id: str = Query(min_length=1, max_length=64), n: int = Query(default=10, ge=1, le=10),
             user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Quiz tối đa 10 câu cho một kỹ năng (FR-14 rút gọn). Không trả đáp án; làm xong nộp từng câu qua /attempts."""
    try:
        return build_quiz(db, user.id, skill_id, n)
    except LookupError as exc:
        raise AppError(404, "SKILL_NOT_FOUND", "Không có kỹ năng này.") from exc


@router.post("/options")
def get_options(body: PracticeOptionsIn, user: User = Depends(get_current_user)):
    """4 phương án trắc nghiệm cho đề Luyện tập (ADR-028). Không trả đáp án: chấm vẫn qua /practice/attempts."""
    try:
        return {"options": make_options(body.kind, body.question)}
    except OptionsUnavailable as exc:
        raise AppError(422, "PRACTICE_OPTIONS_UNAVAILABLE", "Chưa tạo được phương án cho đề này, hãy bấm Câu khác.") from exc


@router.get("/bank/skills")
def get_bank_skills(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Kỹ năng có câu luyện tập "Từ tài liệu" (AI soạn, Quản trị viên đã duyệt và xuất bản)."""
    return {"skills": bank_skills(db)}


@router.get("/bank")
def get_bank(skill_id: str | None = Query(default=None, max_length=64), level: str | None = Query(default=None, pattern="^(de|vua|kho)$"),
             n: int = Query(default=10, ge=1, le=10), user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Tối đa 10 câu "Từ tài liệu"; câu tất định nộp qua /attempts (tính mastery), câu mở qua /practice/open-feedback."""
    return build_bank_set(db, user.id, skill_id, level, n)


@router.post("/open-feedback")
def post_open_feedback(body: OpenFeedbackIn, user: User = Depends(get_current_user), db: Session = Depends(get_db),
                       provider: LLMProvider | None = Depends(provider_dep)):
    """Câu tự luận mở: trả đáp án mẫu + rubric, kèm nhận xét AI khi AI bật. Không ghi lượt làm, không tính mastery."""
    try:
        return open_feedback(db, user.id, body.exercise_version_id, body.answer, provider)
    except ExerciseVersionSuperseded as exc:
        raise AppError(409, "EXERCISE_VERSION_SUPERSEDED", "Câu hỏi này vừa được cập nhật. Hãy tải lại câu hỏi.") from exc
    except NotOpenQuestion as exc:
        raise AppError(422, "NOT_OPEN_QUESTION", "Câu này không phải câu tự luận mở.") from exc
    except LookupError as exc:
        raise AppError(404, "EXERCISE_NOT_FOUND", "Không có câu hỏi này.") from exc
