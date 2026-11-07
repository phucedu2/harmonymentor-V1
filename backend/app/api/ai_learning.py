"""API của pipeline AI GĐ1: GET /me/mastery, bài kiểm tra đầu vào. Mọi endpoint cần đăng nhập;
user_id luôn lấy từ token, không nhận từ client (nguyên tắc 4)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..ai import mastery as m
from ..ai.skill_mapping import SKILL_GROUP_MAP_VERSION, is_mvp
from ..auth.deps import get_current_user
from ..contracts.ai import (
    MasteryOut,
    PlacementOut,
    PlacementQuestionOut,
    PlacementResultItem,
    PlacementSubmitIn,
    PlacementSubmitOut,
    SkillMasteryOut,
)
from ..core.errors import AppError
from ..db.models import MasteryState, Skill, User
from ..db.session import get_db
from ..services import placement_service

router = APIRouter(prefix="/api/v1", tags=["ai-learning"])


@router.get("/me/mastery", response_model=MasteryOut)
def my_mastery(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> MasteryOut:
    states = {s.skill_id: s for s in db.scalars(select(MasteryState).where(MasteryState.user_id == user.id))}
    skills = [s for s in db.scalars(select(Skill).order_by(Skill.id)) if is_mvp(s.id)]
    out = []
    for skill in skills:
        st = states.get(skill.id)
        score = None if st is None else st.score
        count = 0 if st is None else st.attempts_count
        out.append(SkillMasteryOut(
            skill_id=skill.id, name=skill.name, srs_code=skill.srs_code, group_code=skill.group_code,
            assessed=st is not None, score=score, attempts_count=count,
            level=m.level(score, count, skill.ready_threshold, skill.mastery_threshold),
            ready_threshold=skill.ready_threshold, mastery_threshold=skill.mastery_threshold,
        ))
    return MasteryOut(skill_group_map_version=SKILL_GROUP_MAP_VERSION, skills=out)


@router.get("/placement", response_model=PlacementOut)
def get_placement(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> PlacementOut:
    qs = [PlacementQuestionOut(exercise_id=e.id, exercise_version_id=v.id, skill_id=e.skill_id,
                               kind=v.kind, prompt=v.prompt, options=v.options)
          for v, e in placement_service.questions(db)]
    return PlacementOut(status=placement_service.status(db, user.id), questions=qs)


@router.post("/placement/submit", response_model=PlacementSubmitOut)
def submit_placement(body: PlacementSubmitIn, user: User = Depends(get_current_user),
                     db: Session = Depends(get_db)) -> PlacementSubmitOut:
    try:
        graded = placement_service.submit(db, user.id, [a.model_dump() for a in body.answers], body.confirm_retake)
    except placement_service.PlacementAlreadyDone as exc:
        raise AppError(409, "PLACEMENT_ALREADY_DONE",
                       "Bạn đã làm bài kiểm tra đầu vào. Muốn làm lại, hãy xác nhận vì kết quả cũ sẽ được thay.") from exc
    return PlacementSubmitOut(status="completed", results=[
        PlacementResultItem(skill_id=g["skill_id"], correct=g["correct"],
                            score=m.PLACEMENT_SCORE if g["correct"] else 0.0) for g in graded])


@router.post("/placement/skip", response_model=PlacementOut)
def skip_placement(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> PlacementOut:
    placement_service.skip(db, user.id)
    return PlacementOut(status=placement_service.status(db, user.id), questions=[])
