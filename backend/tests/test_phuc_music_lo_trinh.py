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
from app.content.draft_specs import COMPOSE_BLOCKS, CURRICULUM_MODULES, DRAFT_LESSON_SPECS, module_order
from app.content.seed_data import seed_initial_data
from app.content.source_registry import SOURCE_REGISTRY
from app.db.models import Base, Lesson
from app.main import app
from app.music_engine.chord import chord_tones
from app.music_engine.roman import diatonic_chords
from tests.auth_helpers import auth

BANG_7 = ["L01", "L02", "L09", "L10", "L03", "L05", "L11", "L06", "L04", "L07", "L08", "L12"]
PUBLISHED_ORDER = [x for x in BANG_7 if x not in {"L09", "L10", "L11", "L12"}]


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
        assert [x["order"] for x in lessons] == list(range(1, 9))
        assert next(x for x in lessons if x["id"] == "L03")["track"] == "M2. Hòa âm chức năng"
        assert client.get("/api/v1/lessons/L09").status_code == 404
        l01 = client.get("/api/v1/lessons/L01").json()
        assert l01["block_count"] == 14 and len(l01["blocks"]) == 14
        assert all(b["block_type"] != "compose_link" for b in l01["blocks"])
        assert client.post("/api/v1/lessons/L09/start", headers=auth("demo-user")).status_code == 404
        overview = client.get("/api/v1/learning/overview", headers=auth("demo-user")).json()
        assert [x["lesson_id"] for x in overview["lessons"]] == PUBLISHED_ORDER
        assert overview["total_lessons"] == 8


def test_che_do_nhap_hien_du_12_bai(drafts_on):
    with TestClient(app) as client:
        lessons = client.get("/api/v1/lessons").json()
        assert [x["id"] for x in lessons] == BANG_7
        assert [x["order"] for x in lessons] == list(range(1, 13))
        l09 = client.get("/api/v1/lessons/L09").json()
        assert l09["status"] == "draft" and [b["block_type"] for b in l09["blocks"]] == ["callout", "theory", "compose_link"]
        blocks = [b["block_type"] for b in client.get("/api/v1/lessons/L01").json()["blocks"]]
        assert blocks[-2:] == ["compose_link", "summary"]


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
            if lesson.id in {"L09", "L10", "L11", "L12"}:
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
