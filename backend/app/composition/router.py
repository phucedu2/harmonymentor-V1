"""API Harmony Lab (FR-17, FR-18): mẫu nền, gợi ý theo luật, phân tích, và CRUD dự án theo chủ sở hữu.

Gợi ý không tự sửa dự án (nguyên tắc bất biến 5): API chỉ trả ứng viên, người học bấm "Dùng hợp âm này" rồi
lưu dự án. Thứ tự ứng viên theo luật cố định; chưa có lớp AI để xếp hạng/giải thích lại (ADR-010), nên
`ranked_by` luôn là "rule" và mọi thứ chạy khi AI_ENABLED=false.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal, Optional
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
from .arranger import ArrangementError, arrange
from .presets import BEATS_PER_BAR, STYLES, drum_events
from .song import (
    ENDINGS, LENGTHS, MAX_BARS, SECTION_LABELS, SECTION_TYPES, SONG_VERSION, TRANSITIONS, SongError, arrange_song,
    drum_events_for_song, normalize_form,
)
from .styles import ARRANGEMENT_VERSION
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
        "styles": list(STYLES.values()),
        "levels": [{"level": level, "label": label} for level, label in LEVEL_LABELS.items()],
        "rules": [{"id": rule_id, "level": level, "label": label} for rule_id, (level, label) in RULES.items()],
        "tempo": {"min": 60, "max": 160},
        "bars": {"min": 4, "max": 8},
        # Chế độ Bài hát (ADR-013 đề xuất): danh mục để giao diện dựng dòng thời gian.
        "song": {"version": SONG_VERSION, "max_bars": MAX_BARS, "lengths": list(LENGTHS),
                 "section_types": [{"id": t, "label": SECTION_LABELS[t]} for t in SECTION_TYPES],
                 "transitions": list(TRANSITIONS), "endings": list(ENDINGS)},
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


class ArrangementIn(BaseModel):
    key: str
    style: str
    chords: list[Optional[str]] = Field(min_length=1, max_length=8)
    seed: int = Field(default=1, ge=1, le=2_147_483_647)
    energy: int = Field(default=2, ge=1, le=3)
    bpm: Optional[int] = Field(default=None, ge=60, le=160)


@router.post("/composition/arrangement")
def composition_arrangement(body: ArrangementIn):
    """Bản phối 4 vòng cho từng nhạc cụ (ADR-012 đề xuất). Cao độ do Music Engine dựng; công khai như /voicings."""
    try:
        return arrange(body.key, body.style, body.chords, body.seed, body.energy, body.bpm)
    except ArrangementError as exc:
        raise AppError(422, exc.code, exc.message_vi) from exc


SectionType = Literal["intro", "verse", "pre", "chorus", "post", "bridge", "breakdown", "solo", "outro"]
Transition = Literal["auto", "none", "fill_small", "fill_big", "snare_build", "drop_bar", "stop_time", "pickup", "riser",
                     "reverse_cymbal"]


class SectionIn(BaseModel):
    id: str = Field(default="", max_length=16)
    type: SectionType
    label: Optional[str] = Field(default=None, max_length=40)
    bars: int = Field(ge=1, le=16)
    progression: Literal["A", "B", "C"] = "A"
    energy: int = Field(ge=1, le=5)
    feel: Literal["auto", "normal", "half", "double"] = "auto"
    hook: bool = True
    transition: Transition = "auto"
    seed: Optional[int] = Field(default=None, ge=1, le=2_147_483_647)


class ModulateIn(BaseModel):
    enabled: bool = False
    semitones: Literal[1, 2] = 1


class ProgressionsIn(BaseModel):
    A: list[Optional[str]] = Field(min_length=1, max_length=8)
    B: Optional[list[Optional[str]]] = Field(default=None, max_length=8)
    C: Optional[list[Optional[str]]] = Field(default=None, max_length=8)


class SongFormIn(BaseModel):
    length: Literal["short", "medium", "full"] = "medium"
    hook: bool = True
    modulate: ModulateIn = ModulateIn()
    ending: Literal["auto", "fade", "ritardando_fermata", "big_hit", "tag_x3"] = "auto"
    progressions: ProgressionsIn
    sections: Optional[list[SectionIn]] = Field(default=None, max_length=32)


class SongIn(BaseModel):
    key: str
    style: str
    seed: int = Field(default=1, ge=1, le=2_147_483_647)
    energy: int = Field(default=2, ge=1, le=3)   # "Năng lượng tổng": dời cả đường cong −1/0/+1 mức
    bpm: Optional[int] = Field(default=None, ge=60, le=160)
    form: SongFormIn


def _form_dict(form: SongFormIn) -> dict:
    data = form.model_dump()
    if data["sections"] is None:
        data.pop("sections")
    return data


@router.post("/composition/song")
def composition_song(body: SongIn):
    """Backing track dạng bài hát: đoạn, chuyển đoạn, hook, automation (ADR-013 đề xuất). Cao độ do Music Engine dựng."""
    try:
        return arrange_song(body.key, body.style, _form_dict(body.form), body.seed, body.energy, body.bpm)
    except ArrangementError as exc:
        raise AppError(422, exc.code, exc.message_vi) from exc


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

MIX_CHANNELS = ("chords", "bass", "guitar", "drums", "hook")


class ChannelMix(BaseModel):
    volume: float = Field(default=0.8, ge=0, le=1)
    muted: bool = False


class ProjectIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    key: str
    tempo_bpm: int = Field(ge=60, le=160)
    bars: int = Field(ge=4, le=8)
    style: str
    chords: list[Optional[str]]
    seed: int = Field(default=1, ge=1, le=2_147_483_647)
    energy: int = Field(default=2, ge=1, le=3)
    mix: Optional[dict[str, ChannelMix]] = None
    # Có form = dự án ở chế độ Bài hát (QĐ 9A, cột JSON `form`); không có = chế độ Vòng lặp như cũ.
    form: Optional[SongFormIn] = None


def _validate(body: ProjectIn) -> list[Optional[str]]:
    if body.style not in STYLES:
        raise AppError(422, "UNKNOWN_STYLE", f"Mẫu nền {body.style!r} không có.")
    if body.mix and set(body.mix) - set(MIX_CHANNELS):
        raise AppError(422, "UNKNOWN_CHANNEL", f"Kênh trộn chỉ gồm {', '.join(MIX_CHANNELS)}.")
    if len(body.chords) != body.bars:
        raise AppError(422, "BARS_MISMATCH", f"Lưới có {body.bars} ô nhưng gửi {len(body.chords)} hợp âm.")
    try:
        # Dùng phân tích để kiểm tra giọng và từng ký hiệu bằng Music Engine; lưu đúng tên chuẩn Engine trả về.
        result = analyze(body.key, body.chords)
    except CompositionInputError as exc:
        raise _input_error(exc) from exc
    return [bar["symbol"] for bar in result["bars"]]


def _validate_form(body: ProjectIn, symbols: list[Optional[str]]) -> Optional[dict]:
    """Form lưu kèm dự án: vòng A luôn = lưới hợp âm của dự án (chord_events, QĐ 1A); B/C chuẩn hóa qua Engine."""
    if body.form is None:
        return None
    data = _form_dict(body.form)
    progs = data["progressions"]
    progs["A"] = symbols
    for slot in ("B", "C"):
        if progs.get(slot):
            try:
                progs[slot] = [bar["symbol"] for bar in analyze(body.key, progs[slot])["bars"]]
            except CompositionInputError as exc:
                raise _input_error(exc) from exc
    try:
        return normalize_form(body.style, data)
    except SongError as exc:
        raise AppError(422, exc.code, exc.message_vi) from exc


def _expected_version(project: CompositionProject) -> int:
    # Vòng lặp giữ luật v1 y nguyên từng nốt (QĐ 2A), nên dự án vòng lặp cũ không bị báo "đã đổi" oan.
    return SONG_VERSION if project.form else ARRANGEMENT_VERSION


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
        "seed": project.seed, "energy": project.energy, "mix": project.mix,
        "arrangement_version": project.arrangement_version,
        # Dự án lưu bằng luật phối cũ: phát lại theo luật mới (cùng seed) nên có thể nghe khác lúc lưu.
        "arrangement_outdated": project.arrangement_version != _expected_version(project),
        "form": project.form,
        "created_at": project.created_at, "updated_at": project.updated_at,
    }


def _fill(project: CompositionProject, body: ProjectIn, symbols: list[Optional[str]]) -> None:
    project.name = body.name.strip()
    project.key = body.key
    project.tempo_bpm = body.tempo_bpm
    project.bars = body.bars
    project.style = body.style
    project.seed = body.seed
    project.energy = body.energy
    project.mix = {k: v.model_dump() for k, v in body.mix.items()} if body.mix else None
    form = _validate_form(body, symbols)
    project.form = form
    project.arrangement_version = SONG_VERSION if form else ARRANGEMENT_VERSION
    project.updated_at = datetime.now(timezone.utc)
    # Mỗi ô một hợp âm, dài 4 phách (lưới tối thiểu của Bước 4). Ô trống không có sự kiện.
    project.chord_events = [ChordEvent(id=str(uuid4()), start_beat=float(i * BEATS_PER_BAR),
                                       duration_beats=float(BEATS_PER_BAR), symbol=symbol)
                            for i, symbol in enumerate(symbols) if symbol]
    # drum_events trải đủ cả bài (bài hát) hoặc đủ 4 vòng (vòng lặp), đúng như lúc phát (QĐ 5A).
    try:
        events = (drum_events_for_song(body.key, body.style, form, body.seed, body.energy) if form
                  else drum_events(body.style, body.bars, body.key, symbols, body.seed, body.energy))
    except ArrangementError as exc:
        raise AppError(422, exc.code, exc.message_vi) from exc
    project.drum_events = [DrumEvent(id=str(uuid4()), drum=e["drum"], start_beat=float(e["start_beat"]),
                                     velocity=e["velocity"]) for e in events]


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
    return [{"id": p.id, "name": p.name, "key": p.key, "bars": p.bars, "style": p.style, "updated_at": p.updated_at,
             "mode": "song" if p.form else "loop"}
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
