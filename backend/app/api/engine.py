"""Legacy deterministic Music Engine API retained for Practice during migration."""

from __future__ import annotations

from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..music_engine import (
    build_scale,
    diatonic_chords,
    interval_between,
    key_signature,
    parse_chord_symbol,
    roman_numeral,
    transpose,
)
from ..music_engine import grading
from ..music_engine.rhythm import grade_taps
from ..music_engine.tools import TOOL_DECLARATIONS

router = APIRouter(prefix="/api/v1/engine", tags=["legacy-engine"])
GradingMode = Literal["strict_spelling", "pitch_class_only"]


@router.get("/chord/{symbol}")
def get_chord(symbol: str):
    cs = parse_chord_symbol(symbol)
    return {"symbol": cs.symbol, "notes": [str(n) for n in cs.notes],
            "bass": cs.bass.name if cs.bass else None, "inversion": cs.inversion,
            "source_claims": list(cs.type.claim_ids), "verified": cs.type.verified}


@router.get("/scale/{tonic}")
def get_scale(tonic: str, scale_type: str = "major", descending: bool = False):
    return {"tonic": tonic, "scale_type": scale_type,
            "notes": [str(n) for n in build_scale(tonic, scale_type, descending)]}


@router.get("/interval")
def get_interval(lower: str, upper: str):
    iv = interval_between(lower, upper)
    return {"interval": iv.name, "semitones": iv.semitones}


@router.get("/transpose")
def get_transpose(note: str, interval: str):
    return {"note": str(transpose(note, interval))}


@router.get("/key/{tonic}")
def get_key(tonic: str, mode: Literal["major", "minor"] = "major"):
    ks = key_signature(tonic, mode)
    return {"key": ks.label, "kind": ks.kind, "count": ks.count, "accidentals": [str(n) for n in ks.accidentals]}


@router.get("/diatonic/{tonic}")
def get_diatonic(tonic: str, sevenths: bool = False):
    return [{"degree": r.degree, "numeral": r.numeral, "chord": r.chord.symbol,
             "convention_id": r.convention_id, "convention_verified": r.convention_verified}
            for r in diatonic_chords(tonic, sevenths)]


@router.get("/roman")
def get_roman(key: str, chord: str):
    r = roman_numeral(key, chord)
    return {"numeral": r.numeral, "degree": r.degree, "convention_id": r.convention_id,
            "convention_verified": r.convention_verified}


@router.get("/ai-tools")
def get_ai_tools():
    return TOOL_DECLARATIONS


class BuildChordIn(BaseModel):
    symbol: str = Field(examples=["G7"])
    answer: list[str] = Field(examples=[["G", "B", "D", "F#"]])
    grading_mode: GradingMode = "strict_spelling"
    root_position_only: bool = False


class BuildScaleIn(BaseModel):
    tonic: str = Field(examples=["D"])
    scale_type: str = "major"
    answer: list[str]
    grading_mode: GradingMode = "strict_spelling"


class BuildIntervalIn(BaseModel):
    root: str = Field(examples=["C4"])
    interval: str = Field(examples=["M3"])
    answer: str


class IdentifyIntervalIn(BaseModel):
    lower: str
    upper: str
    answer: str


class IdentifyChordIn(BaseModel):
    notes: list[str]
    answer: str


class RomanIn(BaseModel):
    key: str = Field(examples=["C"])
    chord: str = Field(examples=["Dm7"])
    answer: str = Field(examples=["ii7"])


class TapIn(BaseModel):
    expected_beats: list[float]
    taps_seconds: list[float]
    bpm: float
    tolerance_ms: float = 80


@router.post("/grade/build-chord")
def grade_build_chord(body: BuildChordIn):
    return grading.grade_build_chord(body.symbol, body.answer, body.grading_mode, body.root_position_only)


@router.post("/grade/build-scale")
def grade_build_scale(body: BuildScaleIn):
    return grading.grade_build_scale(body.tonic, body.scale_type, body.answer, body.grading_mode)


@router.post("/grade/build-interval")
def grade_build_interval(body: BuildIntervalIn):
    return grading.grade_build_interval(body.root, body.interval, body.answer)


@router.post("/grade/identify-interval")
def grade_identify_interval(body: IdentifyIntervalIn):
    return grading.grade_identify_interval(body.lower, body.upper, body.answer)


@router.post("/grade/identify-chord")
def grade_identify_chord(body: IdentifyChordIn):
    return grading.grade_identify_chord(body.notes, body.answer)


@router.post("/grade/roman-numeral")
def grade_roman_numeral(body: RomanIn):
    return grading.grade_roman_numeral(body.key, body.chord, body.answer)


@router.post("/grade/tap-rhythm")
def grade_tap_rhythm(body: TapIn):
    return grade_taps(body.expected_beats, body.taps_seconds, body.bpm, body.tolerance_ms)
