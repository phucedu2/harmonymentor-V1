"""Nhóm S1–S10 (hàm thuần) của hợp đồng test CP2: EMA theo 04 mục 6.3 và D-3, L-3 Thắng chốt 31/10."""

from __future__ import annotations

import pytest

from app.ai import mastery as m

EPS = 1e-9


def run(results, start=0.0):
    score, out = start, []
    for r in results:
        score = m.ema(score, r)
        out.append(score)
    return out


def test_s1_first_correct_from_zero():
    assert m.ema(0.0, m.exercise_result([], True)) == pytest.approx(0.30, abs=EPS)


def test_s2_five_distinct_correct():
    assert run([1, 1, 1, 1, 1]) == pytest.approx([0.30, 0.51, 0.657, 0.7599, 0.83193], abs=EPS)


def test_s3_correct_from_half():
    assert m.ema(0.50, 1.0) == pytest.approx(0.65, abs=EPS)


def test_s4_wrong_from_065():
    assert m.ema(0.65, m.exercise_result([], False)) == pytest.approx(0.455, abs=EPS)


def test_s5_retry_wrong_then_correct_same_question():
    assert m.exercise_result([], False) == 0.0
    assert m.exercise_result([False], True) == 0.5
    assert run([0.0, 0.5]) == pytest.approx([0.0, 0.15], abs=EPS)


def test_s6_history_is_per_exercise_id_across_versions():
    # Lịch sử truyền vào là mọi lượt của cùng exercise_id, mọi phiên bản: phiên bản mới không phải câu mới.
    assert m.exercise_result([False], True) == 0.5


def test_s7_repeat_correct_does_not_add():
    assert m.exercise_result([True], True) is None
    assert m.exercise_result([True, True], True) is None


def test_d3_correct_wrong_correct_b6():
    # Thắng chốt 31/10 (B6): Đ → S → Đ = 0,30 → 0,21 → 0,297.
    h: list[bool] = []
    score = 0.0
    out = []
    for correct in (True, False, True):
        r = m.exercise_result(h, correct)
        if r is not None:
            score = m.ema(score, r)
        out.append(score)
        h.append(correct)
    assert out == pytest.approx([0.30, 0.21, 0.297], abs=EPS)


def test_l3_every_wrong_counts_zero():
    assert m.exercise_result([False, False], False) == 0.0
    assert m.exercise_result([True], False) == 0.0


def test_s8_ready_threshold_inclusive():
    assert not m.is_ready(0.51, 0.6)
    assert m.is_ready(0.657, 0.6)
    assert m.is_ready(0.60, 0.6)


def test_s9_mastered_threshold_inclusive():
    assert not m.is_mastered(0.7599, 0.8)
    assert m.is_mastered(0.83193, 0.8)
    assert m.is_mastered(0.80, 0.8)


def test_s10_weak_needs_five_attempts():
    assert m.is_weak(0.455, 5, 0.6)
    assert not m.is_weak(0.455, 4, 0.6)
    assert not m.is_weak(0.70, 9, 0.6)
