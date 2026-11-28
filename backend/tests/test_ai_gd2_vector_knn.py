"""Nhóm V và K của hợp đồng test CP2 (docs/CP2_HOP_DONG_TEST.md): vector (value, assessed) và
láng giềng. Hàm thuần, không đọc CSDL. Chiều đánh số 1–14 như trong tài liệu."""

from __future__ import annotations

import pytest

from app.ai.recommender.knn import find_neighbors, similarity, skill_overlap
from app.ai.recommender.vector import build_vector
from app.ai.skill_mapping import GROUP_CODES


def dim(n: int) -> int:
    """Chiều n của tài liệu (bắt đầu từ 1) → chỉ số mảng."""
    return n - 1


# Ví dụ dùng chung của mục K. Mỗi chiều lấy một kỹ năng đại diện của nhóm đó.
REP = {2: "pitch.spelling", 3: "interval.naming", 4: "scale.major", 6: "chord.triad_formula",
       7: "chord.seventh_quality", 9: "function.tonic"}


def vec(**by_dim: float):
    return build_vector({REP[int(k[1:])]: v for k, v in by_dim.items()})


A = vec(d2=0.30, d3=0.51, d6=0.66)
B = vec(d2=0.30, d3=0.51, d6=0.66, d7=0.51, d9=0.30)
C = vec(d2=0.66, d3=0.30, d4=0.51, d6=0.30, d7=0.83)
Z = vec(d2=0.0, d3=0.0)


# --- V ---------------------------------------------------------------------------------------

def test_v1_no_data():
    v = build_vector({})
    assert v.values == (0.0,) * 14
    assert v.assessed == (False,) * 14


def test_v2_assessed_zero_is_not_unassessed():
    v = build_vector({"pitch.spelling": 0.0, "interval.naming": 0.0})
    assert v.values[dim(2)] == 0.0 and v.assessed[dim(2)]
    assert v.values[dim(3)] == 0.0 and v.assessed[dim(3)]
    assert sum(v.assessed) == 2


def test_v3_unassessed_skill_not_counted_as_zero():
    v = build_vector({"chord.triad_formula": 0.51})
    assert v.values[dim(6)] == pytest.approx(0.51)


def test_v4_mean_of_assessed_skills():
    v = build_vector({"function.tonic": 0.30, "function.dominant": 0.66})
    assert v.values[dim(9)] == pytest.approx(0.48)


def test_v5_post_mvp_ignored():
    assert build_vector({"voicing.guide_tones": 0.9}) == build_vector({})


def test_v6_always_14_in_group_order():
    v = build_vector({"progression.ii_v_i": 0.7, "scale.major": 0.2})
    assert len(v.values) == len(v.assessed) == len(GROUP_CODES) == 14
    assert v.assessed[GROUP_CODES.index("progressions")] and v.assessed[GROUP_CODES.index("major_scales")]


def test_v_unknown_skill_rejected():
    # Kỹ năng không có trong bảng ánh xạ là lỗi dữ liệu, không lặng lẽ bỏ qua.
    with pytest.raises(KeyError):
        build_vector({"khong.ton.tai": 0.5})


# --- K ---------------------------------------------------------------------------------------

def test_k1_shared_dims_per_pair():
    ab, bc, ac = similarity(A, B), similarity(B, C), similarity(A, C)
    assert ab.shared == (dim(2), dim(3), dim(6)) and ab.value == pytest.approx(1.0, abs=1e-4)
    assert bc.shared == (dim(2), dim(3), dim(6), dim(7)) and bc.value == pytest.approx(0.8324, abs=1e-4)
    assert ac.shared == (dim(2), dim(3), dim(6)) and ac.value == pytest.approx(0.7894, abs=1e-4)


def test_k2_zero_zero_is_zero_norm():
    s = similarity(Z, Z)
    assert s.value is None and s.reason == "zero_norm"
    result = find_neighbors(Z, {"z2": Z}, min_shared=2)
    assert result.neighbors == [] and result.excluded["zero_norm"] == 1


def test_k3_one_side_zero_is_zero_norm():
    s = similarity(Z, A)
    assert s.value is None and s.reason == "zero_norm"
    assert find_neighbors(A, {"z": Z}, min_shared=2).neighbors == []


@pytest.mark.parametrize("threshold", [2, 3, 4])
def test_k4_min_shared_dims_is_parameter(threshold):
    result = find_neighbors(A, {"b": B, "c": C}, min_shared=threshold)
    ids = [n.user_id for n in result.neighbors]
    if threshold <= 3:
        assert ids == ["b", "c"]
    else:
        assert ids == [] and result.excluded["too_few_shared"] == 2


def test_k5_no_valid_neighbors_reason():
    result = find_neighbors(A, {"z": Z, "x": vec(d9=0.4)}, min_shared=2)
    assert result.neighbors == [] and result.reason == "no_valid_neighbors"


def test_k6_unassessed_target_skips_search():
    result = find_neighbors(build_vector({}), {"b": B}, min_shared=2)
    assert result.neighbors == [] and result.reason == "no_assessed_dims"


def test_k7_synthetic_users_are_ordinary_vectors():
    # Hàm thuần không biết ai là người mô phỏng; dịch vụ chọn tập ứng viên (9A). Ở đây chỉ cần
    # vector của người mô phỏng được nhận như mọi vector khác.
    result = find_neighbors(A, {"synthetic-1": B}, min_shared=3)
    assert [n.user_id for n in result.neighbors] == ["synthetic-1"]


@pytest.mark.parametrize("threshold", [2, 3, 4])
def test_k8_one_shared_dim_never_valid(threshold):
    x = build_vector({"function.tonic": 0.30})
    y = build_vector({"progression.ii_v_i": 0.30})
    raw = similarity(x, y)
    assert raw.shared == (dim(9),) and raw.value == pytest.approx(1.0)
    assert find_neighbors(x, {"y": y}, min_shared=threshold).neighbors == []
    assert skill_overlap(x, y, dim(9)) == 0.0


def test_k9_skill_overlap_jaccard():
    x = build_vector({"function.tonic": 0.3, "function.dominant": 0.5})
    y = build_vector({"function.tonic": 0.3, "progression.ii_v_i": 0.5})
    assert skill_overlap(x, y, dim(9)) == pytest.approx(1 / 3)


def test_k10_deterministic_and_tie_broken_by_id():
    pool = {"u3": B, "u1": B, "u2": C}
    first = find_neighbors(A, pool, min_shared=3)
    second = find_neighbors(A, dict(reversed(list(pool.items()))), min_shared=3)
    assert first.neighbors == second.neighbors
    assert [n.user_id for n in first.neighbors] == ["u1", "u3", "u2"]


def test_k_top_k_cap():
    pool = {f"u{i:02d}": B for i in range(15)}
    assert len(find_neighbors(A, pool, k=10, min_shared=3).neighbors) == 10


def test_k_target_excluded_from_own_pool():
    result = find_neighbors(A, {"me": A, "b": B}, min_shared=3, exclude="me")
    assert [n.user_id for n in result.neighbors] == ["b"]


def test_k_fallback_b_lowers_threshold_to_one():
    x = build_vector({"function.tonic": 0.30})
    y = build_vector({"progression.ii_v_i": 0.30})
    result = find_neighbors(x, {"y": y}, min_shared=3, fallback="b")
    assert [n.user_id for n in result.neighbors] == ["y"] and result.min_shared_used == 1
    # Dự phòng (b) không cứu được zero_norm: vẫn không có láng giềng.
    assert find_neighbors(Z, {"z": Z}, min_shared=3, fallback="b").reason == "no_valid_neighbors"


def test_pool_matrix_same_result_as_dict_pool():
    # Dịch vụ dựng ứng viên bằng build_pool (numpy) cho nhanh; kết quả phải trùng cách dựng từng vector.
    from app.ai.recommender.vector import build_pool

    people = {"b": {"pitch.spelling": 0.30, "interval.naming": 0.51, "chord.triad_formula": 0.66,
                    "chord.seventh_quality": 0.51, "function.tonic": 0.30, "voicing.shell": 0.9},
              "c": {"pitch.spelling": 0.66, "interval.naming": 0.30, "scale.major": 0.51,
                    "chord.triad_formula": 0.30, "chord.seventh_quality": 0.83},
              "z": {"pitch.spelling": 0.0, "interval.naming": 0.0},
              "me": {"pitch.spelling": 0.30, "interval.naming": 0.51, "chord.triad_formula": 0.66}}
    rows = [(u, s, v) for u, m in people.items() for s, v in m.items()]
    as_dict = {u: build_vector(m) for u, m in people.items()}
    for threshold in (2, 3, 4):
        a = find_neighbors(A, as_dict, min_shared=threshold, exclude="me")
        b = find_neighbors(A, build_pool(rows), min_shared=threshold, exclude="me")
        assert (a.neighbors, a.reason, dict(a.excluded)) == (b.neighbors, b.reason, dict(b.excluded))


def test_empty_pool_is_no_valid_neighbors():
    from app.ai.recommender.vector import build_pool

    assert find_neighbors(A, {}, min_shared=2).reason == "no_valid_neighbors"
    assert find_neighbors(A, build_pool([]), min_shared=2).reason == "no_valid_neighbors"
