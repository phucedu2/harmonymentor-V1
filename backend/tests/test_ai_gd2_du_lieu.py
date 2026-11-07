"""GĐ2 góp ý thầy: dữ liệu train/dev/test tạm, sửa luật định tuyến, nguồn theo khối, tên mô hình cục bộ (07/11/2026)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
GD2 = ROOT / "scripts" / "ai" / "data" / "gd2"
sys.path.insert(0, str(ROOT / "scripts" / "ai" / "gop_y"))

from app.ai import local_embedder  # noqa: E402
from app.ai.tutor import chunker, route_classifier, router  # noqa: E402
from app.ai.tutor.retriever import help_base, knowledge_base  # noqa: E402


def _items(name: str) -> list[dict]:
    return json.loads((GD2 / f"{name}.json").read_text(encoding="utf-8"))["items"]


# --- Dữ liệu ---------------------------------------------------------------------------------------

def test_gd2_sizes_and_flows():
    sizes = {"train": 600, "dev": 150, "test_tam": 150}
    for name, least in sizes.items():
        rows = _items(name)
        assert len(rows) >= least, name
        assert {r["flow"] for r in rows} == {"A", "B", "C", "D", "G"}, name


def test_gd2_marked_as_claude_draft_not_official_test():
    for name in ("train", "dev", "test_tam"):
        data = json.loads((GD2 / f"{name}.json").read_text(encoding="utf-8"))
        assert data["author"] == "claude" and data["status"] == "draft"
        assert "KHÔNG phải tập test chính thức" in data["note"]


def test_gd2_split_by_group_no_group_in_two_sets():
    groups = {name: {r["group"] for r in _items(name)} for name in ("train", "dev", "test_tam")}
    assert not groups["train"] & groups["dev"]
    assert not groups["train"] & groups["test_tam"]
    assert not groups["dev"] & groups["test_tam"]


def test_tier1_train_only_from_gd2_train():
    """Câu dev/test tạm không bao giờ lọt vào dữ liệu train tầng 1 (backend đọc lúc chạy)."""
    tier1 = json.loads(route_classifier.GD2_PATH.read_text(encoding="utf-8"))
    train_q = {q for rows in tier1["train"].values() for q in rows} | set(tier1["a_rows"])
    assert train_q == {r["q"] for r in _items("train")}
    for name in ("dev", "test_tam"):
        assert not train_q & {r["q"] for r in _items(name)}


def test_gd2_labels_point_to_real_lessons_and_help_pages():
    lessons = {c.lesson_id for c in knowledge_base()}
    helps = {c.title for c in help_base()}
    for name in ("train", "dev", "test_tam"):
        for r in _items(name):
            if r["flow"] == "A":
                assert r["lesson"] in lessons, r
            if r["flow"] == "D":
                assert r["help"] in helps, r
            if r["flow"] == "B" and r.get("lesson"):
                assert r["lesson"] in {"L05", "L06", "L07", "L08"}, r


def test_gd2_no_overlap_with_other_sets():
    import kiem_trung_du_lieu as k

    assert k.find_overlaps(k.sets()) == []


def test_route_gd2_switch(monkeypatch):
    with_gd2 = route_classifier.load_data()
    monkeypatch.setenv("ROUTE_GD2", "0")
    without = route_classifier.load_data()
    assert sum(map(len, with_gd2["train"].values())) > sum(map(len, without["train"].values())) + 500
    assert "a_rows" not in without


# --- Luật định tuyến -------------------------------------------------------------------------------

@pytest.mark.parametrize("q, lesson", [
    ("V7/V trong C trưởng là hợp âm nào", "L05"),
    ("v/ii nghĩa là gì", "L05"),
    ("bVII trong pop là gì", "L06"),
    ("tension 9 11 13 là gì", "L07"),
    ("vi7 trong C trưởng là bậc mấy", None),
    ("hợp âm Bb trưởng gồm nốt nào", None),
])
def test_later_lesson_case_insensitive(q, lesson):
    assert router.later_lesson(q) == lesson


@pytest.mark.parametrize("q", [
    "A# vs Bb có fai cùng một phím ko",     # gõ tắt của người học
    "enharmonci là gì vậy",                 # lỗi gõ của từ kho có
    "m3 là mấy nửa cung",                   # ký hiệu quãng L01 đã dạy
    "A4 với d5 có giống nhau không",
])
def test_unknown_terms_tolerates_learner_typing(q):
    assert router.unknown_terms(q) == []


@pytest.mark.parametrize("q, term", [("pentatonic là gì", "pentatonic"), ("fugue là thể loại gì", "fugue"),
                                     ("ostinato là gì", "ostinato")])
def test_unknown_terms_still_catches_foreign_terms(q, term):
    assert term in router.unknown_terms(q)


# --- Nguồn theo khối -------------------------------------------------------------------------------

def test_block_source_narrows_to_topic():
    by_block = {c.block_id: c.source for c in chunker.lesson_chunks()}
    assert "Intervals" in by_block["L01-B05"] and "Triads" not in by_block["L01-B05"]
    assert "Triads" in by_block["L01-B08"] and "Intervals" not in by_block["L01-B08"]
    assert "Seventh Chords" in by_block["L02-B05"]


def test_block_source_falls_back_to_whole_lesson():
    spec = {"sources": [{"source_id": "X", "locator": "Ch.1", "note": ""}]}
    got = chunker.block_source(spec, {"X": {"title": "Sách X"}}, "Tiêu đề không chủ đề", "lời giảng")
    assert got == "Sách X · Ch.1"


# --- Tên mô hình cục bộ ----------------------------------------------------------------------------

def test_model_name_from_model_info(tmp_path):
    assert local_embedder.model_name(tmp_path) == local_embedder.MODEL_NAME
    (tmp_path / "model_info.json").write_text(json.dumps({"name": "e5-thu"}), encoding="utf-8")
    assert local_embedder.model_name(tmp_path) == "e5-thu"
