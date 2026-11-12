"""phuc-music Bước 2: lộ trình 12 bài theo SRS 2.1 Bảng 7, bài nháp L09–L12 và mục "Dùng vào sáng tác".

Khẳng định: thứ tự và module đúng Bảng 7; nội dung nháp ẩn với người học khi tắt SHOW_DRAFT_CONTENT
(bài đã phát hành không đổi gì người học thấy); seed đổi thứ tự trên CSDL cũ không vướng UNIQUE order_index;
và các câu nhạc lý trong phần nháp khớp Music Engine.
"""

from __future__ import annotations

from dataclasses import replace
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.content import versioning
from app.content.curriculum_specs import LESSON_SPECS, MIGRATED_LESSON_IDS
from app.content.draft_specs import (
    COMPOSE_BLOCKS,
    CURRICULUM_MODULES,
    DRAFT_LESSON_SPECS,
    DRAFT_REVIEW_ITEMS,
    GOAL_LABELS,
    LESSON_GOALS,
    blocks_with_drafts,
    module_order,
)
from app.content.seed_data import seed_initial_data
from app.content.source_registry import SOURCE_REGISTRY
from app.db.models import Base, Lesson
from app.main import app
from app.music_engine.chord import chord_tones
from app.music_engine.roman import diatonic_chords
from app.services.grading_service import is_self_check
from tests.auth_helpers import auth

BANG_7 = ["L01", "L02", "L09", "L10", "L03", "L05", "L11", "L06", "L04", "L07", "L08", "L12"]
PUBLISHED_ORDER = [x for x in BANG_7 if x not in {"L09", "L10", "L12"}]


@pytest.fixture()
def drafts_on(monkeypatch):
    # Settings là dataclass đóng băng: thay cả đối tượng trong module versioning.
    monkeypatch.setattr(versioning, "settings", replace(versioning.settings, show_draft_content=True))


def test_thu_tu_va_module_trong_dac_ta_dung_bang_7():
    assert [lid for _, ids in CURRICULUM_MODULES for lid in ids] == BANG_7
    expected = module_order()
    for spec in LESSON_SPECS + DRAFT_LESSON_SPECS:
        assert (spec["order"], spec["track"]) == expected[spec["id"]], spec["id"]
    assert sorted(s["order"] for s in LESSON_SPECS + DRAFT_LESSON_SPECS) == list(range(1, 13))


def test_bai_nhap_chi_co_dan_y_va_nguon_hop_le():
    for spec in DRAFT_LESSON_SPECS:
        assert spec["status"] == "draft" and spec["exercises"] == [] and spec["review_items"] == []
        assert spec["id"] not in MIGRATED_LESSON_IDS
        assert spec["sources"] and all(s["source_id"] in SOURCE_REGISTRY for s in spec["sources"])
        assert all(payload["status"] == "draft" for _, _, payload in spec["blocks"])


def test_nguoi_hoc_khong_thay_noi_dung_nhap():
    with TestClient(app) as client:
        lessons = client.get("/api/v1/lessons").json()
        assert [x["id"] for x in lessons] == PUBLISHED_ORDER
        # Số "Bài n" liền nhau theo danh sách đang thấy, không nhảy vì bài nháp bị ẩn.
        assert [x["order"] for x in lessons] == list(range(1, 10))
        assert next(x for x in lessons if x["id"] == "L03")["track"] == "M2. Hòa âm chức năng"
        assert client.get("/api/v1/lessons/L09").status_code == 404
        l01 = client.get("/api/v1/lessons/L01").json()
        assert l01["block_count"] == 15 and len(l01["blocks"]) == 15
        assert all(b["block_type"] != "compose_link" for b in l01["blocks"])
        assert all(not b["id"].endswith("-BTHE") for b in l01["blocks"])
        assert l01["review_item_count"] == 8
        assert client.post("/api/v1/lessons/L09/start", headers=auth("demo-user")).status_code == 404
        overview = client.get("/api/v1/learning/overview", headers=auth("demo-user")).json()
        assert [x["lesson_id"] for x in overview["lessons"]] == PUBLISHED_ORDER
        assert overview["total_lessons"] == 9


def test_che_do_nhap_hien_du_12_bai(drafts_on):
    with TestClient(app) as client:
        lessons = client.get("/api/v1/lessons").json()
        assert [x["id"] for x in lessons] == BANG_7
        assert [x["order"] for x in lessons] == list(range(1, 13))
        l09 = client.get("/api/v1/lessons/L09").json()
        assert l09["status"] == "draft" and [b["block_type"] for b in l09["blocks"]] == ["callout", "theory", "compose_link"]
        l01 = client.get("/api/v1/lessons/L01").json()
        assert [b["block_type"] for b in l01["blocks"]][-3:] == ["compose_link", "theory", "summary"]
        # Thẻ nháp chỉ là khối để duyệt, không vào hàng đợi ôn kể cả ở chế độ nháp.
        assert l01["review_item_count"] == 8


def test_the_on_nhap_dung_dang_tu_danh_gia_va_chua_seed():
    published = {item["id"] for spec in LESSON_SPECS for item in spec["review_items"]}
    exercises = {e["id"]: e for spec in LESSON_SPECS for e in spec["exercises"]}
    # Mỗi thẻ tự diễn đạt lại ý của một câu đã chuyển sang trắc nghiệm, cùng kỹ năng.
    goc = {"L01-F09": "L01-Q05", "L03-F09": "L03-Q05", "L04-F09": "L04-Q06"}
    cards = [card for lesson_cards in DRAFT_REVIEW_ITEMS.values() for card in lesson_cards]
    assert sorted(card["id"] for card in cards) == sorted(goc)
    for card in cards:
        assert card["id"] not in published
        assert is_self_check(card["strategy"], card["grader_config"]), card["id"]
        assert card["skill"] == exercises[goc[card["id"]]]["skill"], card["id"]
        assert card["provenance"] and all(s["source_id"] in SOURCE_REGISTRY for s in card["provenance"])
    for spec in LESSON_SPECS:
        drafts = [p for bid, _, p in blocks_with_drafts(spec) if bid.endswith("-BTHE")]
        assert len(drafts) == (1 if spec["id"] in DRAFT_REVIEW_ITEMS else 0), spec["id"]
        assert all(p["status"] == "draft" for p in drafts)


def test_seed_doi_thu_tu_tren_csdl_cu(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'cu.db'}", future=True)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine, future=True)
    with Session() as db:
        seed_initial_data(db)
        # Giả lập CSDL trước Bước 2: L01..L08 mang thứ tự 1..8, chưa có bài nháp.
        for lesson in db.scalars(select(Lesson)).all():
            lesson.order_index = -100 - int(lesson.id[1:])
        db.flush()
        for lesson in db.scalars(select(Lesson)).all():
            if lesson.id in {"L09", "L10", "L12"}:
                db.delete(lesson)
            else:
                lesson.order_index = int(lesson.id[1:])
        db.commit()
    with Session() as db:
        seed_initial_data(db)
        rows = db.scalars(select(Lesson).order_by(Lesson.order_index)).all()
        assert [x.id for x in rows] == BANG_7
        assert [x.order_index for x in rows] == list(range(1, 13))
    engine.dispose()


def test_nhac_ly_trong_muc_sang_tac_khop_engine():
    in_c = {r.chord.root.name + r.chord.type.display for r in diatonic_chords("C")}
    in_c7 = {r.chord.root.name + r.chord.type.display: r.numeral for r in diatonic_chords("C", sevenths=True)}
    # L01: C – Am – F – G và Bdim đều thuận giọng C trưởng (độ lạ 0).
    for symbol in ["C", "Am", "F", "G", "Bdim"]:
        assert symbol.replace("dim", "°") in in_c or symbol in in_c, symbol
    # L02: các hợp âm bảy được nêu là bảy thuận giọng C; G7 là hợp âm bảy át duy nhất.
    for symbol in ["Cmaj7", "Am7", "Dm7", "G7"]:
        assert symbol in in_c7, symbol
    assert [s for s in in_c7 if s.endswith("7") and not s.endswith(("maj7", "m7", "m7b5", "ø7"))] == ["G7"]
    # L03: F (IV) và Dm (ii) cùng nhóm tiền át.
    assert {"F", "Dm"} <= in_c
    # L04: guide tone F là 3 của Dm7 và 7 của G7; E là 3 của Cmaj7; C là 7 của Dm7, B là 3 của G7 và 7 của Cmaj7.
    names = lambda symbol: [n.name for n in chord_tones(symbol)]
    assert names("Dm7")[1] == "F" and names("Dm7")[3] == "C"
    assert names("G7")[1] == "B" and names("G7")[3] == "F"
    assert names("Cmaj7")[1] == "E" and names("Cmaj7")[3] == "B"
    assert set(COMPOSE_BLOCKS) == {"L01", "L02", "L03", "L04"}


def test_moi_muc_sang_tac_co_nhan_muc_tieu_a_b():
    for spec in LESSON_SPECS + DRAFT_LESSON_SPECS:
        compose = [p for _, kind, p in blocks_with_drafts(spec) if kind == "compose_link"]
        if spec["id"] in set(COMPOSE_BLOCKS) | {s["id"] for s in DRAFT_LESSON_SPECS}:
            assert len(compose) == 1 and compose[0]["goals"], spec["id"]
            assert set(compose[0]["goals"]) <= set(GOAL_LABELS)
    # Cả hai mục tiêu đều có bài phục vụ, và bài thực hành cuối (L12) gom cả A lẫn B.
    assert {g for goals in LESSON_GOALS.values() for g in goals} == {"A", "B"}
    assert LESSON_GOALS["L12"] == ["A", "B"]


def test_rs14_so_bai_hien_thi_thong_nhat_giua_danh_sach_chi_tiet_va_tong_quan():
    """RS-14: "Bài n" là vị trí trong danh sách đang thấy, ở mọi nơi (danh sách, chi tiết)."""
    from fastapi.testclient import TestClient
    from app.main import app
    with TestClient(app) as client:
        rows = client.get("/api/v1/lessons").json()
        assert [r["order"] for r in rows] == list(range(1, len(rows) + 1))
        for row in rows:
            assert client.get(f"/api/v1/lessons/{row['id']}").json()["order"] == row["order"], row["id"]
