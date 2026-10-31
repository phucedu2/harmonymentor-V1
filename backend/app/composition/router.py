"""API Harmony Lab (FR-17, FR-18): mẫu nền, gợi ý theo luật, phân tích, và CRUD dự án theo chủ sở hữu.

Gợi ý không tự sửa dự án (nguyên tắc bất biến 5): API chỉ trả ứng viên, người học bấm "Dùng hợp âm này" rồi
lưu dự án. Thứ tự ứng viên theo luật cố định; chưa có lớp AI để xếp hạng/giải thích lại (ADR-010), nên
`ranked_by` luôn là "rule" và mọi thứ chạy khi AI_ENABLED=false.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth.deps import get_current_user
from ..core.errors import AppError
from ..db.models import ChordEvent, CompositionProject, DrumEvent, User
from ..db.session import get_db
from ..music_engine import diatonic_chords
from ..music_engine.key import all_supported_keys
from .presets import BEATS_PER_BAR, STYLES, drum_events
from .rules import LEVEL_LABELS, RULES, CompositionInputError, analyze, suggest, voicing

router = APIRouter(prefix="/api/v1", tags=["composition"])


def _input_error(exc: CompositionInputError) -> AppError:
    return AppError(422, exc.code, exc.message_vi)


# --- mẫu nền, gợi ý, phân tích ---------------------------------------------------------------------

@router.get("/composition/options")
def composition_options():
    """Giọng (chỉ trưởng, QĐ-2.2), hợp âm trong từng giọng do Engine dựng, mẫu nền và bảng mức độ lạ."""
    keys = []
    for signature in all_supported_keys("major"):
        tonic = signature.tonic.name
        keys.append({"key": tonic, "chords": [{"symbol": rn.chord.symbol, "numeral": rn.numeral}
                                              for rn in diatonic_chords(tonic)]})
    return {
        "keys": keys,
        "styles": [{"id": style_id, **style} for style_id, style in STYLES.items()],
        "levels": [{"level": level, "label": label} for level, label in LEVEL_LABELS.items()],
        "rules": [{"id": rule_id, "level": level, "label": label} for rule_id, (level, label) in RULES.items()],
        "tempo": {"min": 60, "max": 160},
        "bars": {"min": 4, "max": 8},
    }


class SuggestIn(BaseModel):
    key: str
    chords: list[Optional[str]] = Field(min_length=1, max_length=8)
    index: int = Field(ge=0, le=7)
    max_level: int = Field(default=3, ge=0, le=3)


@router.post("/composition/suggestions")
def composition_suggestions(body: SuggestIn, _user: User = Depends(get_current_user)):
    try:
        candidates = suggest(body.key, body.chords, body.index, body.max_level)
    except CompositionInputError as exc:
        raise _input_error(exc) from exc
    return {"candidates": candidates, "ranked_by": "rule", "ai_used": False}


class VoicingsIn(BaseModel):
    chords: list[str] = Field(min_length=1, max_length=16)


@router.post("/composition/voicings")
def composition_voicings(body: VoicingsIn):
    """Cao độ để phát (Tone.js) và vẽ khuông (VexFlow), công khai như các API Music Engine."""
    try:
        return {symbol: voicing(symbol) for symbol in dict.fromkeys(body.chords)}
    except CompositionInputError as exc:
        raise _input_error(exc) from exc


class AnalyzeIn(BaseModel):
    key: str
    chords: list[Optional[str]] = Field(min_length=1, max_length=8)


@router.post("/composition/analyze")
def composition_analyze(body: AnalyzeIn, _user: User = Depends(get_current_user)):
    try:
        return analyze(body.key, body.chords)
    except CompositionInputError as exc:
        raise _input_error(exc) from exc


# --- dự án -----------------------------------------------------------------------------------------

class ProjectIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    key: str
    tempo_bpm: int = Field(ge=60, le=160)
    bars: int = Field(ge=4, le=8)
    style: str
    chords: list[Optional[str]]


def _validate(body: ProjectIn) -> list[Optional[str]]:
    if body.style not in STYLES:
        raise AppError(422, "UNKNOWN_STYLE", f"Mẫu nền {body.style!r} không có.")
    if len(body.chords) != body.bars:
        raise AppError(422, "BARS_MISMATCH", f"Lưới có {body.bars} ô nhưng gửi {len(body.chords)} hợp âm.")
    try:
        # Dùng phân tích để kiểm tra giọng và từng ký hiệu bằng Music Engine; lưu đúng tên chuẩn Engine trả về.
        result = analyze(body.key, body.chords)
    except CompositionInputError as exc:
        raise _input_error(exc) from exc
    return [bar["symbol"] for bar in result["bars"]]


def _out(project: CompositionProject) -> dict:
    chords: list[Optional[str]] = [None] * project.bars
    for event in project.chord_events:
        bar = int(event.start_beat // BEATS_PER_BAR)
        if 0 <= bar < project.bars:
            chords[bar] = event.symbol
    return {
        "id": project.id, "name": project.name, "key": project.key, "tempo_bpm": project.tempo_bpm,
        "time_signature": project.time_signature, "bars": project.bars, "style": project.style, "chords": chords,
        "drum_events": [{"drum": d.drum, "start_beat": d.start_beat, "velocity": d.velocity} for d in project.drum_events],
        "created_at": project.created_at, "updated_at": project.updated_at,
    }


def _fill(project: CompositionProject, body: ProjectIn, symbols: list[Optional[str]]) -> None:
    project.name = body.name.strip()
    project.key = body.key
    project.tempo_bpm = body.tempo_bpm
    project.bars = body.bars
    project.style = body.style
    project.updated_at = datetime.now(timezone.utc)
    # Mỗi ô một hợp âm, dài 4 phách (lưới tối thiểu của Bước 4). Ô trống không có sự kiện.
    project.chord_events = [ChordEvent(id=str(uuid4()), start_beat=float(i * BEATS_PER_BAR),
                                       duration_beats=float(BEATS_PER_BAR), symbol=symbol)
                            for i, symbol in enumerate(symbols) if symbol]
    project.drum_events = [DrumEvent(id=str(uuid4()), drum=e["drum"], start_beat=float(e["start_beat"]),
                                     velocity=e["velocity"]) for e in drum_events(body.style, body.bars)]


def _owned(db: Session, user: User, project_id: str) -> CompositionProject:
    # Dự án của người khác hoặc đã xóa mềm → 404 (nguyên tắc bất biến 4), không lộ là có tồn tại.
    project = db.scalar(select(CompositionProject).where(
        CompositionProject.id == project_id, CompositionProject.user_id == user.id,
        CompositionProject.deleted_at.is_(None)))
    if project is None:
        raise AppError(404, "PROJECT_NOT_FOUND", "Không tìm thấy dự án.")
    return project


@router.get("/projects")
def list_projects(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(CompositionProject).where(
        CompositionProject.user_id == user.id, CompositionProject.deleted_at.is_(None)
    ).order_by(CompositionProject.updated_at.desc())).all()
    return [{"id": p.id, "name": p.name, "key": p.key, "bars": p.bars, "style": p.style, "updated_at": p.updated_at}
            for p in rows]


@router.post("/projects", status_code=201)
def create_project(body: ProjectIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    symbols = _validate(body)
    project = CompositionProject(id=str(uuid4()), user_id=user.id, is_test=user.role == "admin",
                                 created_at=datetime.now(timezone.utc))
    _fill(project, body, symbols)
    db.add(project)
    db.commit()
    db.refresh(project)
    return _out(project)


@router.get("/projects/{project_id}")
def get_project(project_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return _out(_owned(db, user, project_id))


@router.put("/projects/{project_id}")
def update_project(project_id: str, body: ProjectIn, user: User = Depends(get_current_user),
                   db: Session = Depends(get_db)):
    project = _owned(db, user, project_id)
    symbols = _validate(body)
    _fill(project, body, symbols)
    db.commit()
    db.refresh(project)
    return _out(project)


@router.delete("/projects/{project_id}", status_code=204)
def delete_project(project_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    project = _owned(db, user, project_id)
    project.deleted_at = datetime.now(timezone.utc)  # xóa mềm (nguyên tắc bất biến 7)
    db.commit()
    return Response(status_code=204)
