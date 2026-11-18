"""Trắc nghiệm ở trang Luyện tập (ADR-028, câu 2A): Music Engine sinh phương án nhiễu, không cần AI.

Phương án nhiễu là lỗi học sinh hay mắc thật: nhầm tính chất quãng (M3/m3), nhầm hai quãng cùng số nửa cung (A4/d5),
viết sai chính tả đồng âm (C# thành Db), nhầm loại hợp âm/âm giai, nhầm hoa/thường số La Mã. Mọi phương án được
chính Engine chấm lại: đúng MỘT phương án qua chấm, các phương án còn lại đều bị chấm sai. Chấm bài vẫn đi qua
practice_service.grade_practice như lúc gõ chữ, nên chọn đáp án không dễ hơn hay khác luật so với gõ.
"""

from __future__ import annotations

import random
from typing import Any, Callable

from ..music_engine import grading
from ..music_engine.chord import chord_tones, parse_chord_symbol
from ..music_engine.errors import MusicEngineError
from ..music_engine.interval import interval_between, parse_interval, transpose
from ..music_engine.pitch import Note
from ..music_engine.roman import diatonic_chords, roman_numeral
from ..music_engine.scale import build_scale

N_OPTIONS = 4
_PERFECT = {1, 4, 5, 8}
_CHORD_FAMILY = ["", "m", "dim", "aug", "7", "maj7", "m7", "m7b5", "dim7"]
_SCALE_FAMILY = ["major", "natural_minor", "harmonic_minor", "melodic_minor"]


class OptionsUnavailable(ValueError):
    """Engine không dựng đủ phương án cho đề này (đề lạ hoặc sai)."""


def _name(n: Note) -> str:
    return n.with_octave(None).name


def _respell(n: Note) -> Note | None:
    """Tên đồng âm khác chữ cái: C# → Db, Eb → D#. Nốt không dấu hóa thì không đổi (tránh E → Fb quá lạ)."""
    if n.accidental == 0:
        return None
    try:
        return transpose(n.with_octave(None), "d2" if n.accidental > 0 else "A7").with_octave(None)
    except MusicEngineError:
        return None


def _misspelled(notes: list[Note]) -> list[list[str]]:
    out = []
    for i, n in enumerate(notes):
        alt = _respell(n)
        if alt is not None:
            out.append([_name(x) if j != i else _name(alt) for j, x in enumerate(notes)])
    return out


def _interval_candidates(lower: str, upper: str) -> tuple[str, list[list[str]]]:
    iv = interval_between(lower, upper)
    num = iv.number
    common, same_semitones, rare, neighbours = [], [], [], []
    for n in range(1, 9):
        for q in (("P", "A", "d") if n in _PERFECT else ("M", "m", "A", "d")):
            name = f"{q}{n}"
            try:
                cand = parse_interval(name)
            except MusicEngineError:
                continue
            if cand.name == iv.name:
                continue
            if n == num and (q in ("M", "m", "P") or n in (4, 5)):
                common.append(name)          # M3 ↔ m3: lỗi hay gặp nhất
            elif cand.semitones % 12 == iv.semitones % 12 and n not in (1, 2, 8):
                same_semitones.append(name)  # A4 ↔ d5: cùng phím, khác tên
            elif n == num:
                rare.append(name)
            elif abs(n - num) == 1 and q in ("M", "m", "P"):
                neighbours.append(name)      # đếm sai chữ cái
    return iv.name, [common, same_semitones, neighbours, rare]


def _chord_candidates(symbol: str) -> tuple[str, list[list[str]]]:
    cs = parse_chord_symbol(symbol)
    tones = chord_tones(symbol)
    root = _name(cs.root)
    family = []
    for suffix in _CHORD_FAMILY:
        try:
            other = chord_tones(root + suffix)
        except MusicEngineError:
            continue
        if [_name(x) for x in other] != [_name(x) for x in tones]:
            family.append((len(other) != len(tones), " ".join(_name(x) for x in other)))
    same_size = [f for diff, f in family if not diff]
    other_size = [f for diff, f in family if diff]
    return " ".join(_name(x) for x in tones), [[" ".join(m) for m in _misspelled(tones)], same_size, other_size]


def _scale_candidates(tonic: str, scale_type: str) -> tuple[str, list[list[str]]]:
    notes = build_scale(tonic, scale_type)
    others = []
    for st in _SCALE_FAMILY:
        if st != scale_type:
            try:
                others.append(" ".join(_name(x) for x in build_scale(tonic, st)))
            except MusicEngineError:
                continue
    return " ".join(_name(x) for x in notes), [[" ".join(m) for m in _misspelled(notes)], others]


def _roman_candidates(key: str, chord: str) -> tuple[str, list[list[str]]]:
    rn = roman_numeral(key, chord)
    correct = rn.numeral.replace("M7", "maj7")
    sevenths = len(rn.chord.notes) >= 4
    flipped = correct.upper() if correct[:1].islower() else correct.lower()
    others = [r.numeral.replace("M7", "maj7") for r in diatonic_chords(key, sevenths=sevenths) if r.degree != rn.degree]
    near = [o for r, o in zip(diatonic_chords(key, sevenths=sevenths), others) if abs(r.degree - rn.degree) == 1]
    return correct, [[flipped], near, others]


def _grader(kind: str, q: dict[str, Any]) -> Callable[[str], bool]:
    split = lambda text: text.split()  # noqa: E731
    if kind == "interval":
        return lambda a: bool(grading.grade_identify_interval(q["lower"], q["upper"], a)["correct"])
    if kind == "chord":
        return lambda a: bool(grading.grade_build_chord(q["symbol"], split(a))["correct"])
    if kind == "scale":
        return lambda a: bool(grading.grade_build_scale(q["tonic"], q["scale_type"], split(a))["correct"])
    return lambda a: bool(grading.grade_roman_numeral(q["key"], q["chord"], a)["correct"])


def make_options(kind: str, question: dict[str, Any], seed: int | None = None) -> list[str]:
    """4 phương án (1 đúng + 3 nhiễu), thứ tự trộn. Nhóm nhiễu ưu tiên lỗi "gần" nhất trước."""
    try:
        if kind == "interval":
            correct, groups = _interval_candidates(question["lower"], question["upper"])
        elif kind == "chord":
            correct, groups = _chord_candidates(question["symbol"])
        elif kind == "scale":
            correct, groups = _scale_candidates(question["tonic"], question["scale_type"])
        elif kind == "roman":
            correct, groups = _roman_candidates(question["key"], question["chord"])
        else:
            raise OptionsUnavailable(kind)
    except (MusicEngineError, KeyError) as exc:
        raise OptionsUnavailable(str(exc)) from exc
    accepts = _grader(kind, question)
    if not accepts(correct):
        raise OptionsUnavailable("engine_self_check")
    rng = random.Random(seed)
    picked: list[str] = []
    for group in groups:
        pool = list(dict.fromkeys(group))
        rng.shuffle(pool)
        for cand in pool:
            if len(picked) == N_OPTIONS - 1:
                break
            if cand != correct and cand not in picked and not accepts(cand):
                picked.append(cand)
    if len(picked) < N_OPTIONS - 1:
        raise OptionsUnavailable("not_enough_distractors")
    options = picked + [correct]
    rng.shuffle(options)
    return options
