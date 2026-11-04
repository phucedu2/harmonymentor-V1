"""Nhóm C và R của hợp đồng test CP2, Bảng 21 của 04 mục 6.5, độ nhạy trọng số và lý do gợi ý.
Hàm thuần."""

from __future__ import annotations

import itertools
from datetime import datetime, timedelta, timezone

import pytest

from app.ai.recommender.cf import mastery_as_of, skill_cf
from app.ai.recommender.engine import LessonInfo, RecInput, recommend
from app.ai.recommender.knn import find_neighbors
from app.ai.recommender.reasons import reason_for
from app.ai.recommender.scoring import COLD, FULL, Components, Weights, lesson_score, skill_score
from app.ai.recommender.vector import build_vector

S = "function.tonic"


# --- C ---------------------------------------------------------------------------------------

NEIGHBOR_MASTERY = {"N1": {S: 0.66}, "N2": {S: 0.60}, "N3": {S: 0.51}, "N4": {}}


def test_c1_ready_threshold_inclusive():
    assert skill_cf(S, ["N1", "N2", "N3", "N4"], NEIGHBOR_MASTERY) == pytest.approx(0.50)


def test_c2_neighbor_without_skill_stays_in_denominator():
    assert skill_cf(S, ["N1", "N2", "N3"], NEIGHBOR_MASTERY) == pytest.approx(2 / 3)


def test_c3_only_top_10_neighbors():
    target = build_vector({"pitch.spelling": 0.3, "interval.naming": 0.5, "chord.triad_formula": 0.6})
    pool, mastery = {}, {}
    for i in range(12):
        # Càng về sau càng khác người học → hai người cuối bị loại khỏi top 10.
        pool[f"n{i:02d}"] = build_vector({"pitch.spelling": 0.3 + 0.05 * i, "interval.naming": 0.5,
                                          "chord.triad_formula": 0.6 - 0.04 * i})
        mastery[f"n{i:02d}"] = {S: 0.9 if i < 10 else 0.0}
    result = find_neighbors(target, pool, k=10, min_shared=3)
    ids = [n.user_id for n in result.neighbors]
    assert len(ids) == 10 and "n10" not in ids and "n11" not in ids
    assert skill_cf(S, ids, mastery) == pytest.approx(1.0)


def test_c4_events_after_cutoff_ignored():
    t0 = datetime(2026, 11, 1, tzinfo=timezone.utc)
    events = [(t0, S, 0.51), (t0 + timedelta(days=2), S, 0.66)]
    at_cutoff = mastery_as_of(events, cutoff=t0 + timedelta(days=1))
    assert at_cutoff == {S: 0.51}
    mastery = dict(NEIGHBOR_MASTERY, N3=at_cutoff)
    assert skill_cf(S, ["N1", "N2", "N3", "N4"], mastery) == pytest.approx(0.50)


def test_c4b_cutoff_is_strict():
    # "Trước thời điểm gợi ý": sự kiện đúng tại mốc không được dùng.
    t0 = datetime(2026, 11, 1, tzinfo=timezone.utc)
    assert mastery_as_of([(t0, S, 0.7)], cutoff=t0) == {}


def test_c5_no_neighbors_no_cf():
    assert skill_cf(S, [], NEIGHBOR_MASTERY) is None


def test_c6_zero_norm_not_in_denominator():
    a = build_vector({"pitch.spelling": 0.3, "interval.naming": 0.5})
    z = build_vector({"pitch.spelling": 0.0, "interval.naming": 0.0})
    result = find_neighbors(a, {"good": a, "zero": z}, min_shared=2)
    ids = [n.user_id for n in result.neighbors]
    assert ids == ["good"]
    assert skill_cf(S, ids, {"good": {S: 0.7}, "zero": {}}) == 1.0


def test_c7_lesson_cf_mean_over_unmastered_skills():
    comps = [Components("a", 0, 0.5, 0, 0.2), Components("b", 0, 0.7, 0, 0.6), Components("c", 0, 0.85, 0, 1.0)]
    ls = lesson_score(comps, FULL, mastery_threshold=0.80)
    assert ls.cf == pytest.approx(0.4)
    assert [c.skill_id for c in ls.skills] == ["a", "b"]


# --- Bảng 21 và công thức ---------------------------------------------------------------------

TABLE_21 = {"L10": (0.58, 0.10, 0, 0.60, 0.548), "L03": (0.42, 0.20, 0, 0.50, 0.447),
            "L09": (0.31, 0.00, 0, 0.30, 0.419)}


@pytest.mark.parametrize("lesson", sorted(TABLE_21))
def test_table_21(lesson):
    content, mastery, due, cf, expected = TABLE_21[lesson]
    assert skill_score(Components("x", content, mastery, due, cf), FULL) == pytest.approx(expected, abs=5e-4)


def test_table_21_due_one():
    content, mastery, _, cf, _ = TABLE_21["L03"]
    assert skill_score(Components("x", content, mastery, 1, cf), FULL) == pytest.approx(0.647, abs=5e-4)


def test_cold_formula_moves_cf_weight_to_content():
    assert (COLD.content, COLD.mastery, COLD.due, COLD.cf) == (0.55, 0.25, 0.20, 0.0)
    assert skill_score(Components("x", 0.58, 0.10, 0, None), COLD) == pytest.approx(0.55 * 0.58 + 0.25 * 0.9)


def test_full_weights_sum_to_one():
    assert FULL.content + FULL.mastery + FULL.due + FULL.cf == pytest.approx(1.0)


def _moves():
    names = ("content", "mastery", "due", "cf")
    for src, dst in itertools.permutations(names, 2):
        w = {n: getattr(FULL, n) for n in names}
        w[src] -= 0.05
        w[dst] += 0.05
        yield f"{src}->{dst}", Weights(**w)


@pytest.mark.parametrize("label,weights", list(_moves()))
def test_weight_sensitivity_plus_minus_005(label, weights):
    # Chuyển 0,05 giữa hai tầng bất kỳ (tổng vẫn bằng 1): thứ tự Bảng 21 không đổi.
    scores = {k: skill_score(Components("x", c, m, d, f), weights) for k, (c, m, d, f, _) in TABLE_21.items()}
    assert sorted(scores, key=scores.get, reverse=True) == ["L10", "L03", "L09"], (label, scores)


# --- Lý do ------------------------------------------------------------------------------------

def test_reason_top_contribution():
    assert reason_for(Components("x", 0.58, 0.10, 0, 0.60), FULL, goal_text="đệm hát pop")[0] == "mastery"
    assert reason_for(Components("x", 0.9, 0.7, 0, 0.1), FULL, goal_text="đệm hát pop")[0] == "content"
    assert reason_for(Components("x", 0.2, 0.7, 1, 0.1), FULL, goal_text=None)[0] == "due"
    assert reason_for(Components("x", 0.0, 0.7, 0, 1.0), FULL, goal_text=None)[0] == "cf"


def test_reason_text_quotes_goal_and_is_short():
    code, text, badge = reason_for(Components("x", 0.9, 0.7, 0, 0.1), FULL, goal_text="đệm hát nhạc pop cho lớp " * 10)
    assert code == "content" and badge == "Theo mục tiêu"
    assert "đệm hát nhạc pop" in text and len(text) < 120


# --- R: danh sách gợi ý ------------------------------------------------------------------------

def lessons():
    return [
        LessonInfo("L01", 1, "Bài 1", frozenset({"pitch.spelling", "interval.naming"}), frozenset()),
        LessonInfo("L02", 2, "Bài 2", frozenset({"scale.major"}), frozenset({"pitch.spelling"})),
        LessonInfo("L03", 3, "Bài 3", frozenset({"function.tonic"}), frozenset({"scale.major"})),
        LessonInfo("L08", 8, "Bài 8", frozenset({"voicing.shell"}), frozenset()),
    ]


def run(mastery, **kw):
    return recommend(RecInput(lessons=lessons(), mastery=mastery, due_skills=frozenset(),
                              content={}, neighbor_ids=None, neighbor_mastery={}, **kw))


def test_r1_fewer_than_5_no_repeats():
    out = run({"pitch.spelling": 0.65, "interval.naming": 0.3})
    ids = [r.lesson_id for r in out.ranked]
    assert ids == sorted(set(ids), key=ids.index)
    assert set(ids) == {"L01", "L02"} and out.few_eligible


def test_r2_prereq_below_ready_never_listed():
    out = run({"pitch.spelling": 0.59})
    assert "L02" not in [r.lesson_id for r in out.ranked]
    assert out.excluded["L02"] == "prereq_not_ready"


def test_r3_nothing_eligible_is_empty():
    only_blocked = [LessonInfo("L02", 2, "Bài 2", frozenset({"scale.major"}), frozenset({"pitch.spelling"}))]
    out = recommend(RecInput(lessons=only_blocked, mastery={}, due_skills=frozenset(), content={},
                             neighbor_ids=None, neighbor_mastery={}))
    assert out.ranked == [] and out.few_eligible


def test_r4_all_mastered_or_post_mvp_only_excluded():
    out = run({"pitch.spelling": 0.85, "interval.naming": 0.80})
    ids = [r.lesson_id for r in out.ranked]
    assert "L01" not in ids and out.excluded["L01"] == "all_mastered"
    assert "L08" not in ids and out.excluded["L08"] == "no_mvp_skill"


def test_cold_vs_full_mode():
    cold = run({"pitch.spelling": 0.65})
    assert cold.weights == COLD
    full = recommend(RecInput(lessons=lessons(), mastery={"pitch.spelling": 0.65}, due_skills=frozenset(),
                              content={}, neighbor_ids=["n1"], neighbor_mastery={"n1": {"scale.major": 0.7}}))
    assert full.weights == FULL
    l02 = next(r for r in full.ranked if r.lesson_id == "L02")
    assert l02.cf == 1.0


def test_unassessed_prereq_counts_as_zero():
    # ADR-008 mục 3: ở bước lọc, kỹ năng chưa đánh giá = 0, chưa đủ làm tiên quyết.
    assert "L02" not in [r.lesson_id for r in run({}).ranked]


def test_ranking_ties_follow_curriculum_order():
    two = [LessonInfo("L05", 5, "Bài 5", frozenset({"function.dominant"}), frozenset()),
           LessonInfo("L01", 1, "Bài 1", frozenset({"pitch.spelling"}), frozenset())]
    out = recommend(RecInput(lessons=two, mastery={}, due_skills=frozenset(), content={},
                             neighbor_ids=None, neighbor_mastery={}))
    assert [r.lesson_id for r in out.ranked] == ["L01", "L05"]


def test_k_limit_and_max_5():
    many = [LessonInfo(f"L{i:02d}", i, f"Bài {i}", frozenset({"function.tonic"}), frozenset()) for i in range(1, 9)]
    out = recommend(RecInput(lessons=many, mastery={}, due_skills=frozenset(), content={},
                             neighbor_ids=None, neighbor_mastery={}, k=5))
    assert len(out.ranked) == 5 and not out.few_eligible
    with pytest.raises(ValueError):
        recommend(RecInput(lessons=many, mastery={}, due_skills=frozenset(), content={},
                           neighbor_ids=None, neighbor_mastery={}, k=6))


def test_due_skill_lifts_lesson():
    two = [LessonInfo("L01", 1, "Bài 1", frozenset({"pitch.spelling"}), frozenset()),
           LessonInfo("L05", 5, "Bài 5", frozenset({"function.dominant"}), frozenset())]
    out = recommend(RecInput(lessons=two, mastery={}, due_skills=frozenset({"function.dominant"}), content={},
                             neighbor_ids=None, neighbor_mastery={}))
    assert [r.lesson_id for r in out.ranked] == ["L05", "L01"]
    assert out.ranked[0].reason_code == "due"
