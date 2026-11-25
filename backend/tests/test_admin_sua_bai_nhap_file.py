"""Nhóm 1 phần Admin còn thiếu (Phúc 3A, 4A, 25/11/2026): FR-ADM-14 sửa bài/khối, FR-ADM-39 nhập nội dung từ file."""

from __future__ import annotations

import json
from uuid import uuid4

import yaml
from sqlalchemy import select

from app.content.source_registry import SOURCE_REGISTRY
from app.db.models import AdminAuditLog, Exercise, Lesson
from app.db.seed import seed_initial_data
from app.db.session import SessionLocal
from tests.test_admin_bai_hoc import A, MCQ, client, h, new_lesson  # noqa: F401  (fixture dùng lại)

SRC = next(iter(SOURCE_REGISTRY))


# --- FR-ADM-14 ---------------------------------------------------------------------------------------------

def test_sua_ten_bai_goc_khong_bi_seed_ghi_de_va_khoi_phuc_duoc(client, h):
    with SessionLocal() as db:
        original = db.get(Lesson, "L01").title
    r = client.put(f"{A}/lessons/L01", headers=h, json={"title": "Ký âm cho người mới", "objectives": ["Đọc nốt"]})
    assert r.status_code == 200 and r.json()["changed"] is True
    with SessionLocal() as db:
        seed_initial_data(db)   # seed chạy lại như lúc khởi động
        db.commit()
        assert db.get(Lesson, "L01").title == "Ký âm cho người mới"
        assert db.get(Lesson, "L01").objectives == ["Đọc nốt"]
    assert client.get("/api/v1/lessons/L01").json()["title"] == "Ký âm cho người mới"
    r = client.put(f"{A}/lessons/L01", headers=h, json={"reset": True})
    assert r.status_code == 200 and r.json()["title"] == original
    with SessionLocal() as db:
        assert db.get(Lesson, "L01").admin_meta is None
        log = db.scalars(select(AdminAuditLog).where(AdminAuditLog.action == "lesson.update",
                                                     AdminAuditLog.target_id == "L01")).all()
        assert log and log[0].detail["to"]["title"] == "Ký âm cho người mới"


def test_ten_bai_trong_bi_tu_choi_va_bai_tu_tao_khong_co_ten_goc(client, h):
    lid = new_lesson(client, h)
    assert client.put(f"{A}/lessons/{lid}", headers=h, json={"title": "  "}).status_code == 422
    assert client.put(f"{A}/lessons/{lid}", headers=h, json={"reset": True}).json()["error"]["code"] == "NOTHING_TO_RESET"
    r = client.put(f"{A}/lessons/{lid}", headers=h, json={"title": "Quãng ghép (sửa)", "objectives": []})
    assert r.status_code == 200
    with SessionLocal() as db:
        assert db.get(Lesson, lid).admin_meta is None   # bài M- ghi thẳng cột, seed không đụng


def test_xoa_va_sap_xep_khoi_chi_bai_tu_tao(client, h):
    lid = new_lesson(client, h)
    for t in ("Khối 2", "Khối 3"):
        client.post(f"{A}/lessons/{lid}/blocks", headers=h, json={"title": t, "paragraphs": ["Nội dung."]})
    b1, b2, b3 = f"{lid}-B01", f"{lid}-B02", f"{lid}-B03"
    r = client.post(f"{A}/lessons/{lid}/blocks/reorder", headers=h, json={"block_ids": [b3, b1, b2]})
    assert r.status_code == 200
    detail = client.get(f"{A}/lessons/{lid}", headers=h).json()
    assert [b["id"] for b in detail["blocks"]] == [b3, b1, b2]
    assert client.post(f"{A}/lessons/{lid}/blocks/reorder", headers=h, json={"block_ids": [b1, b2]}).status_code == 409
    assert client.delete(f"{A}/lessons/{lid}/blocks/{b1}", headers=h).status_code == 200
    detail = client.get(f"{A}/lessons/{lid}", headers=h).json()
    assert [(b["id"], b["position"]) for b in detail["blocks"]] == [(b3, 1), (b2, 2)]
    # Thêm khối sau khi xóa: mã mới không trùng mã cũ.
    r = client.post(f"{A}/lessons/{lid}/blocks", headers=h, json={"title": "Khối 4", "paragraphs": ["x"]})
    assert r.status_code == 201 and r.json()["id"] == f"{lid}-B04"
    client.delete(f"{A}/lessons/{lid}/blocks/{b2}", headers=h)
    client.delete(f"{A}/lessons/{lid}/blocks/{b3}", headers=h)
    assert client.delete(f"{A}/lessons/{lid}/blocks/{lid}-B04", headers=h).json()["error"]["code"] == "LAST_BLOCK"
    with SessionLocal() as db:
        gone = db.scalars(select(AdminAuditLog).where(AdminAuditLog.action == "lesson.delete_block",
                                                      AdminAuditLog.target_id == lid)).all()
        assert gone and gone[0].detail["payload"]["title"] == "Quãng ghép là gì"   # nội dung khối còn trong nhật ký
    assert client.delete(f"{A}/lessons/L01/blocks/L01-B01", headers=h).json()["error"]["code"] == "SEED_LESSON"


# --- FR-ADM-39 ---------------------------------------------------------------------------------------------

def _doc(code, exercises=None, blocks=None, sources=None):
    return {"format": "harmonymentor/1", "lessons": [{
        "code": code, "title": "Quãng ba", "objectives": ["Nhận ra quãng 3"],
        "blocks": blocks or [{"title": "Quãng 3", "paragraphs": ["Quãng 3 trưởng có 4 nửa cung."]}],
        "sources": [{"source_id": SRC, "locator": "Chương 1"}] if sources is None else sources,
        "exercises": [{"key": "q1", **MCQ}] if exercises is None else exercises}]}


def _post(client, h, doc, name="bai.yaml", dry=False):
    raw = yaml.safe_dump(doc, allow_unicode=True) if name.endswith((".yaml", ".yml")) else json.dumps(doc, ensure_ascii=False)
    return client.post(f"{A}/import", headers=h, files={"file": (name, raw.encode(), "text/plain")},
                       data={"dry_run": "true" if dry else "false"})


def test_nhap_file_tao_bai_an_va_nhap_lai_khong_trung(client, h):
    code = f"thu-{uuid4().hex[:8]}"
    lid = f"M-{code}"
    r = _post(client, h, _doc(code), dry=True)
    assert r.status_code == 200 and r.json()["dry_run"] is True
    with SessionLocal() as db:
        assert db.get(Lesson, lid) is None   # thử trước: không ghi gì
    r = _post(client, h, _doc(code))
    assert r.status_code == 200, r.text
    row = r.json()["lessons"][0]
    assert row["created"] is True and row["exercises_added"] == [f"{lid}-q1"]
    assert lid not in [x["id"] for x in client.get("/api/v1/lessons").json()]   # bài nhập ẩn tới khi bấm hiện
    # Nhập lại y nguyên (lần này dạng JSON): không thêm gì.
    row = _post(client, h, _doc(code), name="bai.json").json()["lessons"][0]
    assert row["created"] is False and not row["exercises_added"] and not row["exercises_revised"]
    assert not row["blocks_changed"] and row["sources_added"] == 0
    # Đổi lời giải câu q1 và thêm khối: câu lên bản 2, khối dựng lại, câu cũ vẫn giữ.
    q = {"key": "q1", **MCQ, "explanation": "C–E: 4 nửa cung, quãng 3 trưởng (M3)."}
    blocks = [{"title": "Quãng 3", "paragraphs": ["Quãng 3 trưởng có 4 nửa cung."]},
              {"title": "Quãng 3 thứ", "paragraphs": ["Quãng 3 thứ có 3 nửa cung."]}]
    row = _post(client, h, _doc(code, exercises=[q], blocks=blocks)).json()["lessons"][0]
    assert row["exercises_revised"] == [f"{lid}-q1 (bản 2)"] and row["blocks_changed"] is True
    # Câu không còn trong file: chỉ báo, không tự bỏ.
    row = _post(client, h, _doc(code, exercises=[], blocks=blocks)).json()["lessons"][0]
    assert row["exercises_not_in_file"] == [f"{lid}-q1"]
    with SessionLocal() as db:
        lesson = db.get(Lesson, lid)
        assert len(lesson.blocks) == 2 and db.get(Exercise, f"{lid}-q1").deleted_at is None
        assert len(db.get(Exercise, f"{lid}-q1").versions) == 2


def test_file_loi_khong_ghi_gi_va_bao_du_vi_tri(client, h):
    code = f"loi-{uuid4().hex[:8]}"
    wrong = {"key": "q1", **MCQ, "answer": "m3"}             # Engine tính M3
    no_why = {"key": "q2", **MCQ, "explanation": ""}
    r = _post(client, h, _doc(code, exercises=[wrong, no_why], sources=[{"source_id": "khong-co"}]))
    assert r.status_code == 422
    msg = r.json()["error"]["message"]
    assert "chưa nhập gì" in msg and "câu “q1”" in msg and "câu “q2”" in msg and "khong-co" in msg
    with SessionLocal() as db:
        assert db.get(Lesson, f"M-{code}") is None
    assert _post(client, h, {"format": "khac"}).json()["error"]["code"] == "IMPORT_INVALID"
    bad = client.post(f"{A}/import", headers=h, files={"file": ("a.yaml", b"lessons: [", "text/plain")})
    assert bad.json()["error"]["code"] == "IMPORT_SYNTAX"
    assert client.post(f"{A}/import", headers=h, files={"file": ("a.txt", b"x", "text/plain")}).status_code == 422
    assert "format: harmonymentor/1" in client.get(f"{A}/import/template", headers=h).json()["content"]


def test_mau_nhap_dung_cau_truc_va_nguoi_hoc_bi_chan(client, h):
    from app.admin.content_import import TEMPLATE
    from tests.auth_helpers import auth
    from tests.test_admin_quan_tri import make_user
    doc = yaml.safe_load(TEMPLATE)
    assert doc["format"] == "harmonymentor/1" and doc["lessons"][0]["exercises"][0]["kind"] == "build_chord"
    # Mẫu nhập được thật (chỉ thay nguồn ví dụ bằng nguồn có sẵn): Engine nhận đề "Hợp âm C".
    doc["lessons"][0]["code"] = f"mau-{uuid4().hex[:8]}"
    doc["lessons"][0]["sources"][0]["source_id"] = SRC
    r = _post(client, h, doc, dry=True)
    assert r.status_code == 200, r.text
    learner = auth(make_user())
    assert _post(client, learner, _doc("x1")).status_code == 403
    assert client.put(f"{A}/lessons/L01", headers=learner, json={"title": "x"}).status_code == 403
