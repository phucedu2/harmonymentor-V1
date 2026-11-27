"""PR 2 hoàn thiện Admin (Phúc 1A, 5A, 24/11/2026): tạo/xóa/sắp xếp bài, soạn câu luyện tập bằng form.

FR-ADM-13 tạo bài, 15 xóa bài (mềm), 16 sắp xếp, 24–28 câu hỏi + đáp án + lời giải, 29 độ khó. Đáp án do Music Engine
tính; sửa câu thêm phiên bản (ADR-006)."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models import AdminAuditLog, Exercise, ExerciseVersion, Lesson
from app.db.session import SessionLocal
from app.main import app
from tests.auth_helpers import auth
from tests.test_admin_quan_tri import make_user

A = "/api/v1/admin"


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c
    with SessionLocal() as db:
        # Trả thứ tự và xóa mềm của bài seed về như cũ. Bài M- thử nghiệm giữ ở trạng thái đã xóa mềm: phiên bản câu đã
        # phát hành không xóa cứng được (ADR-006), và bài đã xóa không hiện với người học hay trong thống kê.
        for lesson in db.scalars(select(Lesson)):
            lesson.sort_key = None
            lesson.deleted_at = lesson.deleted_at if lesson.id.startswith("M-") else None
            if lesson.id.startswith("M-") and lesson.deleted_at is None:
                lesson.deleted_at = datetime.now(timezone.utc)
        db.commit()


@pytest.fixture()
def h():
    return auth(make_user("admin"), "admin")


def new_lesson(client, h, title="Quãng ghép"):
    r = client.post(f"{A}/lessons", headers=h, json={"title": title, "objectives": ["Gọi tên quãng ghép"],
                                                     "block_title": "Quãng ghép là gì",
                                                     "paragraphs": ["Quãng ghép lớn hơn một quãng tám đúng."]})
    assert r.status_code == 201, r.text
    return r.json()["id"]


MCQ = {"kind": "mcq", "level": "nho", "prompt": "Quãng từ C lên E là quãng gì?", "skill_id": "interval.naming",
       "options": ["m3", "M3", "P4"], "answer": "M3", "check": {"type": "interval", "lower": "C", "upper": "E"},
       "explanation": "C lên E cách 4 nửa cung: quãng 3 trưởng."}


def visible_ids(client):
    return [x["id"] for x in client.get("/api/v1/lessons").json()]


def test_tao_bai_moi_an_toi_khi_bam_hien_va_them_khoi(client, h):
    lid = new_lesson(client, h)
    assert lid.startswith("M-") and lid not in visible_ids(client)
    r = client.post(f"{A}/lessons/{lid}/blocks", headers=h, json={"title": "Đổi quãng ghép về quãng đơn",
                                                                  "paragraphs": ["Trừ đi 7 để ra quãng đơn."]})
    assert r.status_code == 201 and r.json()["position"] == 2
    client.post(f"{A}/lessons/{lid}/visibility", headers=h, json={"hidden": False})
    assert lid in visible_ids(client)
    body = client.get(f"/api/v1/lessons/{lid}").json()
    assert [b["payload"]["title"] for b in body["blocks"]] == ["Quãng ghép là gì", "Đổi quãng ghép về quãng đơn"]
    with SessionLocal() as db:
        assert db.scalar(select(AdminAuditLog).where(AdminAuditLog.action == "lesson.create", AdminAuditLog.target_id == lid))


def test_tao_bai_thieu_noi_dung_bi_tu_choi(client, h):
    r = client.post(f"{A}/lessons", headers=h, json={"title": "X", "block_title": "Y", "paragraphs": ["   "]})
    assert r.status_code == 422 and r.json()["error"]["code"] == "LESSON_INCOMPLETE"


def test_xoa_mem_bai_an_khoi_hoc_sinh_va_khoi_phuc_duoc(client, h):
    assert "L03" in visible_ids(client)
    assert client.delete(f"{A}/lessons/L03", headers=h).status_code == 200
    assert "L03" not in visible_ids(client)
    assert client.get("/api/v1/lessons/L03").status_code == 404
    row = next(x for x in client.get(f"{A}/lessons", headers=h).json() if x["id"] == "L03")
    assert row["deleted"] and row["order"] == 0
    with SessionLocal() as db:
        assert db.get(Lesson, "L03") is not None   # xóa mềm, không mất dữ liệu
    assert client.post(f"{A}/lessons/L03/restore", headers=h).status_code == 200
    assert "L03" in visible_ids(client)


def test_sap_xep_bai_doi_thu_tu_hoc_sinh_thay_va_giu_qua_seed(client, h):
    rows = [x for x in client.get(f"{A}/lessons", headers=h).json() if not x["deleted"]]
    ids = [x["id"] for x in rows]
    wanted = [ids[1], ids[0], *ids[2:]]
    r = client.post(f"{A}/lessons/reorder", headers=h, json={"lesson_ids": wanted})
    assert r.status_code == 200, r.text
    assert [x for x in visible_ids(client) if x in wanted][:2] == [ids[1], ids[0]]
    from app.content.seed_data import seed_initial_data   # seed chạy lại lúc khởi động không làm mất thứ tự
    with SessionLocal() as db:
        seed_initial_data(db)
        db.commit()
    assert [x for x in visible_ids(client) if x in wanted][:2] == [ids[1], ids[0]]
    bad = client.post(f"{A}/lessons/reorder", headers=h, json={"lesson_ids": wanted[:-1]})
    assert bad.status_code == 409 and bad.json()["error"]["code"] == "ORDER_MISMATCH"


def test_them_cau_engine_tinh_dap_an_hoc_sinh_lam_duoc(client, h):
    lid = new_lesson(client, h)
    r = client.post(f"{A}/lessons/{lid}/exercises", headers=h, json=MCQ)
    assert r.status_code == 201, r.text
    ex = r.json()
    assert ex["version"] == 1 and ex["question"]["answer"] == "M3" and ex["question"]["check"]["upper"] == "E"
    assert ex["question"]["level"] == "nho"   # FR-ADM-29 độ khó
    client.post(f"{A}/lessons/{lid}/visibility", headers=h, json={"hidden": False})
    learner = auth(make_user())
    item = client.get(f"/api/v1/lessons/{lid}").json()["exercises"][0]
    ok = client.post("/api/v1/attempts", headers=learner, json={"exercise_version_id": item["version_id"], "answer": "M3"})
    assert ok.status_code == 200 and ok.json()["correct"]
    build = client.post(f"{A}/lessons/{lid}/exercises", headers=h, json={
        "kind": "build_chord", "level": "van_dung", "prompt": "Dựng hợp âm Ebm7b5 bằng tên nốt.", "skill_id": "chord.seventh_build",
        "symbol": "Ebm7b5", "explanation": "Ebm7b5 = Eb Gb Bbb Db."}).json()
    assert build["engine_answer"] == ["Eb", "Gb", "Bbb", "Db"]


def test_bo_trong_loi_giai_thi_engine_tu_viet(client, h):
    """27/11/2026 (Phúc 4A, 5A): câu Engine tính được mà bỏ trống lời giải thì Engine viết lời giải và lời chỉ chỗ sai."""
    lid = new_lesson(client, h)
    r = client.post(f"{A}/lessons/{lid}/exercises", headers=h, json={**MCQ, "explanation": ""})
    assert r.status_code == 201, r.text
    q = r.json()["question"]
    assert "4 nửa cung" in q["explanation"]
    with SessionLocal() as db:
        cfg = db.get(ExerciseVersion, f"{r.json()['id']}-v1").grader_config
    assert "quãng 3 trưởng" in cfg["option_feedback"]["m3"]


@pytest.mark.parametrize("patch,code", [
    ({"answer": "m3"}, "ENGINE_DISAGREES"),               # Engine tính M3: không tự sửa giúp, báo người soạn
    # 8A: câu khái niệm (Engine không tính được) phải có lời giải; câu Engine tính được thì Engine tự viết (27/11, 4A).
    ({"explanation": "", "check": None, "prompt": "Quãng nào nghe ổn định nhất?", "options": ["P8", "m2", "A4"], "answer": "P8"},
     "NO_EXPLANATION"),
    ({"skill_id": "khong.co"}, "QUESTION_INVALID"),
    ({"prompt": "Quãng từ D lên F là quãng gì?"}, "QUESTION_INVALID"),   # đề lệch phần kiểm C–E
])
def test_cau_sai_bi_tu_choi_va_noi_ro(client, h, patch, code):
    lid = new_lesson(client, h)
    r = client.post(f"{A}/lessons/{lid}/exercises", headers=h, json={**MCQ, **patch})
    assert r.status_code in (409, 422) and r.json()["error"]["code"] == code, r.text


def test_sua_cau_tang_phien_ban_luot_cu_giu_ban_cu_va_bo_cau(client, h):
    lid = new_lesson(client, h)
    ex = client.post(f"{A}/lessons/{lid}/exercises", headers=h, json=MCQ).json()
    same = client.put(f"{A}/exercises/{ex['id']}", headers=h, json=MCQ).json()
    assert same["version"] == 1   # không đổi gì thì không thêm phiên bản
    edited = client.put(f"{A}/exercises/{ex['id']}", headers=h, json={
        **MCQ, "prompt": "Quãng từ C lên Eb là quãng gì?", "answer": "m3",
        "check": {"type": "interval", "lower": "C", "upper": "Eb"}, "explanation": "C lên Eb cách 3 nửa cung: quãng 3 thứ."})
    assert edited.status_code == 200, edited.text
    assert edited.json()["version"] == 2 and edited.json()["engine_answer"] == "m3"
    with SessionLocal() as db:
        versions = sorted(db.scalars(select(ExerciseVersion).where(ExerciseVersion.exercise_id == ex["id"])), key=lambda v: v.version)
        assert [v.version for v in versions] == [1, 2] and versions[0].answer_key["expected"] == "M3"
    assert client.delete(f"{A}/exercises/{ex['id']}", headers=h).status_code == 200
    assert client.get(f"{A}/lessons/{lid}/exercises", headers=h).json()["exercises"] == []
    with SessionLocal() as db:
        assert db.get(Exercise, ex["id"]).deleted_at is not None


def test_bai_seed_khong_cho_sua_cau_bang_form(client, h):
    r = client.post(f"{A}/lessons/L01/exercises", headers=h, json=MCQ)
    assert r.status_code == 409 and r.json()["error"]["code"] == "SEED_LESSON"
    listing = client.get(f"{A}/lessons/L01/exercises", headers=h).json()
    assert listing["editable"] is False and listing["exercises"] and listing["exercises"][0]["prompt"]


def test_nguoi_hoc_khong_goi_duoc_route_moi(client):
    learner = auth(make_user())
    assert client.post(f"{A}/lessons", headers=learner, json={}).status_code == 403
    assert client.delete(f"{A}/lessons/L01", headers=learner).status_code == 403
