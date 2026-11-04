"""Nhóm M của hợp đồng test CP2 (docs/CP2_HOP_DONG_TEST.md): ánh xạ kỹ năng → srs_code, group_code."""

from __future__ import annotations

import pytest
from sqlalchemy import select

from app.ai import skill_mapping as sm
from app.content.skill_graph import PREREQUISITES, SKILLS
from app.db.models import Skill
from app.db.session import SessionLocal
from app.main import app  # noqa: F401  (tạo schema + seed như các test khác)

SKILL_IDS = {s[0] for s in SKILLS}


def test_m1_mapping_covers_exactly_skill_graph():
    assert set(sm.SKILL_MAPPING) == SKILL_IDS


def test_m2_each_skill_once():
    ids = [row[0] for row in sm.MAPPING_ROWS]
    assert len(ids) == len(set(ids))


def test_m3_value_domains():
    for srs, group in sm.SKILL_MAPPING.values():
        assert srs in set(sm.SRS_CODES) | {sm.POST_MVP}
        assert group in sm.GROUP_CODES


def test_m4_mvp_group_equals_srs():
    for srs, group in sm.SKILL_MAPPING.values():
        if srs != sm.POST_MVP:
            assert group == srs


def test_m5_groups_11_14_iff_post_mvp():
    tail = set(sm.GROUP_CODES[10:])
    for srs, group in sm.SKILL_MAPPING.values():
        assert (group in tail) == (srs == sm.POST_MVP)


def test_m6_groups_without_skills_declared_explicitly():
    used = {group for _, group in sm.SKILL_MAPPING.values()}
    assert set(sm.GROUP_CODES) - used == set(sm.GROUPS_WITHOUT_SKILLS)
    assert set(sm.GROUPS_WITHOUT_SKILLS) == {"note_names", "minor_scales", "rhythm_basics", "pop_harmony"}


def test_m7_mvp_prereqs_are_mvp_and_acyclic():
    for skill, pre in PREREQUISITES:
        if sm.is_mvp(skill):
            assert sm.is_mvp(pre), (skill, pre)
    graph: dict[str, list[str]] = {}
    for skill, pre in PREREQUISITES:
        graph.setdefault(skill, []).append(pre)
    state: dict[str, int] = {}

    def visit(node: str) -> None:
        assert state.get(node) != 1, f"chu trình tại {node}"
        if state.get(node) == 2:
            return
        state[node] = 1
        for nxt in graph.get(node, []):
            visit(nxt)
        state[node] = 2

    for node in graph:
        visit(node)


def test_m8_validator_reports_missing_skill():
    errors = sm.validate_mapping(SKILL_IDS | {"fake.skill"}, sm.MAPPING_ROWS)
    assert any("fake.skill" in e for e in errors)


def test_m9_validator_reports_duplicate_row():
    errors = sm.validate_mapping(SKILL_IDS, sm.MAPPING_ROWS + [sm.MAPPING_ROWS[0]])
    assert any("trùng" in e for e in errors)
    assert sm.validate_mapping(SKILL_IDS, sm.MAPPING_ROWS) == []


def test_m10_parallel_minor_is_post_mvp_chromatic():
    assert sm.SKILL_MAPPING["scale.parallel_minor"] == (sm.POST_MVP, "chromatic_harmony")


@pytest.mark.parametrize("skill", ["voicing.guide_tones", "voicing.voice_leading"])
def test_m11_l04_voicing_post_mvp(skill):
    assert sm.SKILL_MAPPING[skill] == (sm.POST_MVP, "jazz_voicing")


def test_m12_group_order():
    assert sm.GROUP_CODES == (
        "note_names", "accidentals", "intervals", "major_scales", "minor_scales", "triads",
        "seventh_chords", "diatonic_chords", "progressions", "rhythm_basics",
        "chromatic_harmony", "pop_harmony", "jazz_voicing", "jazz_scales_tensions",
    )
    assert sm.SRS_CODES == sm.GROUP_CODES[:10]
    assert sm.SKILL_GROUP_MAP_VERSION


def test_m13_thresholds_after_seed():
    with SessionLocal() as db:
        skills = db.scalars(select(Skill)).all()
    assert {s.id for s in skills} >= SKILL_IDS
    for s in skills:
        assert s.ready_threshold == pytest.approx(0.6)
        assert s.mastery_threshold == pytest.approx(0.8)
        assert 0 < s.ready_threshold < s.mastery_threshold <= 1
        assert (s.srs_code, s.group_code) == sm.SKILL_MAPPING[s.id]
