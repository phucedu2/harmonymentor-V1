"""Phase 0.2 regression tests for defects found during the v0.1.0 audit.

These tests intentionally describe behavior that must remain fixed before mastery/adaptive
learning is allowed to consume assessment results.
"""

import math

import pytest

from app.music_engine.errors import InvalidRhythm
from app.music_engine.grading import grade_build_chord, grade_build_scale
from app.music_engine.rhythm import grade_taps


def test_build_chord_rejects_extra_same_letter_tone_regardless_of_order():
    """F01: an extra F# must not disappear just because the correct F is also present."""
    answers = [
        ["G", "B", "D", "F", "F#"],
        ["G", "B", "D", "F#", "F"],
    ]
    for answer in answers:
        result = grade_build_chord("G7", answer)
        assert result["correct"] is False
        assert result["primary_error"] == "EXTRA_TONE"
        assert any(error.get("extra") == "F#" for error in result["errors"])


def test_build_chord_rejects_duplicate_tone_in_full_chord_exercise():
    """A full-chord construction task expects each required chord tone once."""
    result = grade_build_chord("G7", ["G", "B", "D", "F", "F"])
    assert result["correct"] is False
    assert result["primary_error"] == "EXTRA_TONE"


def test_build_chord_valid_answer_stays_correct_after_regression_fix():
    result = grade_build_chord("G7", ["F", "D", "G", "B"])
    assert result["correct"] is True
    assert result["errors"] == []


def test_scale_swapped_degrees_are_not_reported_as_out_of_key():
    """F03: D and E are both in C major; swapping them is an order/degree error."""
    result = grade_build_scale("C", "major", ["C", "E", "D", "F", "G", "A", "B"])
    assert result["correct"] is False
    assert result["primary_error"] == "WRONG_SCALE_DEGREE_ORDER"
    assert result["wrong_degrees"] == [2, 3]
    assert "NOT_IN_KEY" not in {error["code"] for error in result["errors"]}


def test_tap_rhythm_rejects_empty_expected_pattern_even_with_invalid_bpm():
    """F04: no expected beats means there is no assessable task; it must not pass as correct."""
    with pytest.raises(InvalidRhythm):
        grade_taps([], [], 0)


def test_tap_rhythm_rejects_nonfinite_timing_values():
    with pytest.raises(InvalidRhythm):
        grade_taps([0.0, 1.0], [0.0, math.nan], 120)
    with pytest.raises(InvalidRhythm):
        grade_taps([0.0, math.inf], [0.0, 0.5], 120)
    with pytest.raises(InvalidRhythm):
        grade_taps([0.0], [0.0], math.inf)


def test_api_surfaces_phase0_regressions_as_structured_results():
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)
    prefix = "/api/v1/engine"

    chord = client.post(f"{prefix}/grade/build-chord", json={
        "symbol": "G7", "answer": ["G", "B", "D", "F", "F#"]
    })
    assert chord.status_code == 200
    assert chord.json()["correct"] is False
    assert chord.json()["primary_error"] == "EXTRA_TONE"

    scale = client.post(f"{prefix}/grade/build-scale", json={
        "tonic": "C", "scale_type": "major", "answer": ["C", "E", "D", "F", "G", "A", "B"]
    })
    assert scale.status_code == 200
    assert scale.json()["primary_error"] == "WRONG_SCALE_DEGREE_ORDER"

    rhythm = client.post(f"{prefix}/grade/tap-rhythm", json={
        "expected_beats": [], "taps_seconds": [], "bpm": 0, "tolerance_ms": 80
    })
    assert rhythm.status_code == 422
    assert rhythm.json()["error"]["code"] == "INVALID_RHYTHM"
