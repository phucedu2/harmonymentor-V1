import pytest

from app.music_engine.claims import CLAIMS
from app.music_engine.chord import CHORD_TYPES
from app.music_engine.errors import NotSupportedInMvp
from app.music_engine.rhythm import check_measure, grade_taps, measure_capacity
from app.music_engine.scale import SCALE_TYPES


# --- Nhịp (SRS: MVP chỉ 4/4, dung sai ±80 ms) --------------------------------------

def test_only_4_4_in_mvp():
    assert measure_capacity("4/4") == 4
    with pytest.raises(NotSupportedInMvp):
        measure_capacity("6/8")


def test_measure_fill():
    assert check_measure([("half", 1), ("quarter", 0)])["status"] == "ok"   # trắng chấm + đen = 4
    assert check_measure([("whole", 0), ("eighth", 0)])["status"] == "over"


def test_tap_grading_at_120_bpm():
    beats = [0, 1, 2, 3]                        # 120 BPM → 0.0, 0.5, 1.0, 1.5 giây
    r = grade_taps(beats, [0.01, 0.56, 1.0, 1.5], bpm=120)
    assert r["correct"] is True                # lệch 10 ms và 60 ms, đều < 80 ms
    r = grade_taps(beats, [0.0, 0.59, 1.0], bpm=120)
    assert [e["code"] for e in r["events"]] == ["OK", "LATE_ONSET", "OK", "MISSED_BEAT"]
    r = grade_taps(beats, [0.0, 0.5, 0.75, 1.0, 1.5], bpm=120)
    assert [e["code"] for e in r["events"]][-1] == "EXTRA_TAP"


# --- Sổ nhận định ------------------------------------------------------------------

def test_every_claim_used_by_code_exists():
    used = {c for t in CHORD_TYPES.values() for c in t.claim_ids} | \
           {c for t in SCALE_TYPES.values() for c in t.claim_ids}
    missing = used - set(CLAIMS)
    assert not missing, missing


def test_nothing_is_approved_yet():
    """Chưa mục nào được duyệt: không quy tắc nào đạt ngưỡng QĐ-2.4. Test này sẽ đổi khi bạn duyệt."""
    assert not any(c.meets_engine_threshold for c in CLAIMS.values())


def test_single_source_claims_are_flagged_for_exemption_or_not_engine_core():
    single = {c.id for c in CLAIMS.values() if c.source_count < 2}
    exempt = {c.id for c in CLAIMS.values() if c.exemption_requested}
    # Lõi Engine 1 nguồn phải nằm trong danh sách xin miễn trừ.
    assert {"MUS-TRIAD-001", "MUS-7TH-004", "MUS-SCALE-003", "MUS-RHY-001"} <= exempt <= single
