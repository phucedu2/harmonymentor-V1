"""Nhóm 3 phần Admin còn thiếu (Phúc 6A, 25/11/2026): thẻ ôn do Quản trị viên soạn (FR-ADM-31..34)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.content.seed_data import seed_initial_data
from app.db.models import AdminAuditLog, LessonProgress, ReviewItem, ReviewState
from app.db.session import SessionLocal
from app.main import app
from tests.auth_helpers import auth
from tests.test_admin_bai_hoc import A, new_lesson
from tests.test_admin_quan_tri import make_user


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c
    with SessionLocal() as db:
        # Thẻ thử nghiệm: xóa hẳn (thẻ ôn không có phiên bản bất biến) cùng trạng thái ôn của chúng; bài M- xóa mềm.
        ids = list(db.scalars(select(ReviewItem.id).where(ReviewItem.id.like("%-R__") | ReviewItem.id.like("%-R-%"))))
        states = list(db.scalars(select(ReviewState.id).where(ReviewState.review_item_id.in_(ids)))) if ids else []
        from app.db.models import ReviewAttempt, Lesson
        if states:
            db.execute(delete(ReviewAttempt).where(ReviewAttempt.review_state_id.in_(states)))
            db.execute(delete(ReviewState).where(ReviewState.id.in_(states)))
        db.execute(delete(ReviewItem).where(ReviewItem.id.in_(ids)))
        for lesson in db.scalars(select(Lesson)):
            lesson.sort_key = None
            if lesson.id.startswith("M-") and lesson.deleted_at is None:
                lesson.deleted_at = datetime.now(timezone.utc)
        db.commit()


@pytest.fixture()
def h():
    return auth(make_user("admin"), "admin")


RECALL = {"kind": "recall", "front": "Quãng F–A là quãng gì?", "back": "M3 · 4 nửa cung", "expected": "M3", "skill_id": "interval.naming"}


def test_them_sua_xoa_mem_the_recall_va_hoc_sinh_on_duoc(client, h):
    lid = new_lesson(client, h)
    client.post(f"{A}/lessons/{lid}/visibility", headers=h, json={"hidden": False})
    r = client.post(f"{A}/lessons/{lid}/cards", headers=h, json=RECALL)
    assert r.status_code == 201, r.text
    card = r.json()
    assert card["id"] == f"{lid}-R01" and card["editable"] and card["form"]["expected"] == "M3"
    # Học sinh hoàn thành bài (ở đây: kích hoạt trực tiếp) rồi ôn thẻ: đúng/sai chấm theo expected.
    uid = make_user()
    with SessionLocal() as db:
        db.add(LessonProgress(user_id=uid, lesson_id=lid, status="completed", completed_at=datetime.now(timezone.utc)))
        db.commit()
    again = client.post(f"{A}/lessons/{lid}/cards", headers=h, json={**RECALL, "front": "Quãng D–F?", "back": "m3", "expected": "m3"})
    assert again.json()["activated_for"] >= 1   # người đã hoàn thành bài được kích hoạt thẻ mới
    lh = auth(uid)
    due = client.get("/api/v1/review/due", headers=lh).json()
    assert {x["review_item_id"] for x in due} == {f"{lid}-R01", f"{lid}-R02"}
    ok = client.post(f"/api/v1/review/{lid}-R01/answer", headers=lh, json={"answer": "M3", "rating": "auto"})
    assert ok.status_code == 200 and ok.json()["correct"] is True
    bad = client.post(f"/api/v1/review/{lid}-R02/answer", headers=lh, json={"answer": "M3", "rating": "auto"})
    assert bad.json()["correct"] is False and "m3" in bad.json()["feedback"]
    # Sửa thẻ: đáp án mới có hiệu lực, nhật ký giữ giá trị cũ.
    r = client.put(f"{A}/cards/{lid}-R01", headers=h, json={**RECALL, "back": "M3 (4 nửa cung)", "expected": "M3"})
    assert r.status_code == 200 and r.json()["back"] == "M3 (4 nửa cung)"
    # Xóa mềm: biến khỏi hàng đợi, khỏi chi tiết bài, không ôn được nữa; id không tái dùng.
    assert client.delete(f"{A}/cards/{lid}-R02", headers=h).status_code == 200
    due = client.get("/api/v1/review/due", headers=lh).json()
    assert {x["review_item_id"] for x in due} <= {f"{lid}-R01"}
    assert client.post(f"/api/v1/review/{lid}-R02/answer", headers=lh, json={"answer": "m3", "rating": "auto"}).status_code == 404
    detail = client.get(f"/api/v1/lessons/{lid}").json()
    assert [x["id"] for x in detail["review_items"]] == [f"{lid}-R01"] and detail["review_item_count"] == 1
    third = client.post(f"{A}/lessons/{lid}/cards", headers=h, json=RECALL).json()
    assert third["id"] == f"{lid}-R03"
    with SessionLocal() as db:
        log = db.scalars(select(AdminAuditLog).where(AdminAuditLog.action == "card.update", AdminAuditLog.target_id == f"{lid}-R01")).all()
        assert log and log[0].detail["from"]["back"] == "M3 · 4 nửa cung"


def test_the_do_engine_tinh_va_the_tu_danh_gia(client, h):
    lid = new_lesson(client, h)
    chord = client.post(f"{A}/lessons/{lid}/cards", headers=h, json={
        "kind": "build_chord", "front": "Dựng hợp âm Ebm7b5: gồm những nốt nào?", "symbol": "Ebm7b5", "skill_id": "chord.seventh_build"})
    assert chord.status_code == 201, chord.text
    assert chord.json()["back"] == "Eb–Gb–Bbb–Db"   # Engine tính, không phải người soạn gõ
    scale = client.post(f"{A}/lessons/{lid}/cards", headers=h, json={
        "kind": "build_scale", "front": "Viết âm giai G trưởng.", "tonic": "G", "scale_type": "major", "skill_id": "scale.major"})
    assert scale.json()["back"] == "G–A–B–C–D–E–F#"
    interval = client.post(f"{A}/lessons/{lid}/cards", headers=h, json={
        "kind": "interval", "front": "Quãng D–F?", "check": {"lower": "D", "upper": "F"}, "skill_id": "interval.naming"})
    assert interval.json()["back"] == "m3"
    roman = client.post(f"{A}/lessons/{lid}/cards", headers=h, json={
        "kind": "roman", "front": "Roman numeral của Dm7 trong C major?", "check": {"key": "C", "chord": "Dm7"}, "skill_id": "roman.major_seventh"})
    assert roman.status_code == 201 and roman.json()["back"] == "ii7"
    selfc = client.post(f"{A}/lessons/{lid}/cards", headers=h, json={
        "kind": "self_check", "front": "Vì sao G7 muốn về C?", "back": "Nốt cảm B lên C.", "keywords": ["nốt cảm", "tritone"],
        "skill_id": "function.dominant"})
    assert selfc.status_code == 201
    with SessionLocal() as db:
        item = db.get(ReviewItem, selfc.json()["id"])
        from app.services.grading_service import is_self_check
        assert is_self_check(item.grading_strategy, item.grader_config)   # học sinh tự đánh giá, máy không đoán nghĩa
        assert db.get(ReviewItem, chord.json()["id"]).grading_strategy == "music_engine"


def test_the_sai_bi_tu_choi_the_goc_chi_xem_va_gan_duoc_vao_bai_goc(client, h):
    lid = new_lesson(client, h)
    bad = {"kind": "build_chord", "front": "Dựng hợp âm C: nốt nào?", "symbol": "Cxyz", "skill_id": "chord.triad_build"}
    assert client.post(f"{A}/lessons/{lid}/cards", headers=h, json=bad).status_code == 422
    mismatch = {"kind": "build_chord", "front": "Dựng hợp âm G: nốt nào?", "symbol": "C", "skill_id": "chord.triad_build"}
    assert client.post(f"{A}/lessons/{lid}/cards", headers=h, json=mismatch).status_code == 422   # đề nói G, Engine nhận C
    assert client.post(f"{A}/lessons/{lid}/cards", headers=h, json={**RECALL, "skill_id": "khong.co"}).json()["error"]["code"] == "CARD_SKILL"
    assert client.post(f"{A}/lessons/{lid}/cards", headers=h, json={**RECALL, "back": ""}).status_code == 422
    assert client.post(f"{A}/lessons/{lid}/cards", headers=h, json={**RECALL, "kind": "khac"}).json()["error"]["code"] == "CARD_KIND"
    seed = client.get(f"{A}/lessons/L01/cards", headers=h).json()["cards"]
    assert seed and all(c["editable"] is False and c["form"] is None for c in seed)
    assert client.put(f"{A}/cards/L01-F01", headers=h, json=RECALL).json()["error"]["code"] == "SEED_CARD"
    assert client.delete(f"{A}/cards/L01-F01", headers=h).json()["error"]["code"] == "SEED_CARD"
    # Thẻ gắn vào bài gốc L01: seed khởi động lại không xóa, thẻ gốc vẫn nguyên.
    mine = client.post(f"{A}/lessons/L01/cards", headers=h, json=RECALL).json()
    assert mine["id"].startswith("L01-R")
    with SessionLocal() as db:
        n_seed = len(db.scalars(select(ReviewItem).where(ReviewItem.id.like("L01-F%"))).all())
        seed_initial_data(db)
        db.commit()
        assert db.get(ReviewItem, mine["id"]) is not None and db.get(ReviewItem, mine["id"]).deleted_at is None
        assert len(db.scalars(select(ReviewItem).where(ReviewItem.id.like("L01-F%"))).all()) == n_seed
    assert client.delete(f"{A}/cards/{mine['id']}", headers=h).status_code == 200
    learner = auth(make_user())
    assert client.post(f"{A}/lessons/{lid}/cards", headers=learner, json=RECALL).status_code == 403
    assert client.get(f"{A}/lessons/{lid}/cards", headers=learner).status_code == 403


def test_nhap_file_co_the_on_theo_ma_va_nhap_lai_khong_trung(client, h):
    import yaml
    from uuid import uuid4
    from app.content.source_registry import SOURCE_REGISTRY
    code = f"the-{uuid4().hex[:8]}"
    lid = f"M-{code}"
    doc = {"format": "harmonymentor/1", "lessons": [{
        "code": code, "title": "Thẻ nhập", "blocks": [{"title": "Khối", "paragraphs": ["Nội dung."]}],
        "sources": [{"source_id": next(iter(SOURCE_REGISTRY)), "locator": "c1"}],
        "cards": [{"key": "ca", "kind": "build_scale", "front": "Viết âm giai G trưởng.", "tonic": "G", "scale_type": "major",
                   "skill_id": "scale.major"}]}]}

    def post(d):
        return client.post(f"{A}/import", headers=h, files={"file": ("t.yaml", yaml.safe_dump(d, allow_unicode=True).encode(), "text/plain")})
    first = post(doc)
    assert first.status_code == 200, first.text
    row = first.json()["lessons"][0]
    assert row["cards_added"] == [f"{lid}-R-ca"] and not row["cards_revised"]
    row = post(doc).json()["lessons"][0]
    assert not row["cards_added"] and not row["cards_revised"]            # nhập lại y nguyên: không đổi gì
    doc["lessons"][0]["cards"][0]["tonic"] = "D"
    doc["lessons"][0]["cards"][0]["front"] = "Viết âm giai D trưởng."
    row = post(doc).json()["lessons"][0]
    assert row["cards_revised"] == [f"{lid}-R-ca"]
    cards = client.get(f"{A}/lessons/{lid}/cards", headers=h).json()["cards"]
    assert [c["back"] for c in cards] == ["D–E–F#–G–A–B–C#"]
    doc["lessons"][0]["cards"] = []
    assert post(doc).json()["lessons"][0]["cards_not_in_file"] == [f"{lid}-R-ca"]   # chỉ báo, không tự xóa
    doc["lessons"][0]["cards"] = [{"key": "cb", "kind": "build_chord", "front": "Dựng C.", "symbol": "G", "skill_id": "chord.triad_build"}]
    bad = post(doc)
    assert bad.status_code == 422 and "thẻ “cb”" in bad.json()["error"]["message"]
