"""phuc-music Bước 2: trang Luyện tập ghi lịch sử (FR-LRN-08), máy chủ tự chấm bằng Music Engine.

Khẳng định: chấm đúng/sai theo Engine (không tin client), lưu theo user_id từ token, người khác không
thấy lịch sử của nhau, lượt của Admin có is_test, và luyện tập không đụng tới lượt làm bài học.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.db.models import Attempt, PracticeAttempt, User
from app.db.session import SessionLocal
from app.main import app
from tests.auth_helpers import auth

client = TestClient(app)


@pytest.fixture(autouse=True, scope="module")
def _schema():
    # Mở TestClient dạng context để chạy lifespan (create_schema), giống các test CSDL khác.
    with TestClient(app):
        yield


def make_user(role: str = "learner") -> str:
    user_id = "pm-" + uuid4().hex[:12]
    with SessionLocal() as db:
        db.add(User(id=user_id, display_name="Luyện tập thử", role=role))
        db.commit()
    return user_id


def submit(user_id: str, kind: str, question: dict, answer, role: str = "learner", level: str | None = "de"):
    return client.post("/api/v1/practice/attempts", headers=auth(user_id, role),
                       json={"kind": kind, "level": level, "question": question, "answer": answer})


def test_cham_bang_engine_va_ghi_lich_su():
    uid = make_user()
    ok = submit(uid, "chord", {"symbol": "Cm"}, "C Eb G")
    assert ok.status_code == 200 and ok.json()["correct"] is True
    assert ok.json()["expected"] == ["C", "Eb", "G"]
    # Cùng phím đàn nhưng sai chính tả: gõ chữ thì Engine chấm sai và nói rõ chỗ sai.
    bad = submit(uid, "chord", {"symbol": "Cm"}, "C D# G")
    body = bad.json()
    assert body["correct"] is False and body["primary_error"]
    assert "Eb" in body["message_vi"] or any("Eb" in e.get("message_vi", "") for e in body["errors"])

    history = client.get("/api/v1/practice/history", headers=auth(uid)).json()
    assert [item["correct"] for item in history["items"]] == [False, True]
    assert history["items"][0]["question"] == {"symbol": "Cm"}
    assert history["stats"] == [{"kind": "chord", "attempts": 2, "correct": 1}]


def test_bon_dang_bai_deu_cham_duoc():
    uid = make_user()
    assert submit(uid, "interval", {"lower": "F4", "upper": "A4"}, "M3").json()["correct"] is True
    assert submit(uid, "scale", {"tonic": "D", "scale_type": "major"}, "D E F# G A B C#").json()["correct"] is True
    assert submit(uid, "roman", {"key": "C", "chord": "Dm7"}, "ii7").json()["correct"] is True
    stats = client.get("/api/v1/practice/history", headers=auth(uid)).json()["stats"]
    assert [s["kind"] for s in stats] == ["interval", "scale", "roman"]


def test_client_khong_tu_khai_bao_dung_sai():
    uid = make_user()
    res = client.post("/api/v1/practice/attempts", headers=auth(uid), json={
        "kind": "chord", "question": {"symbol": "G7", "extra": "x"}, "answer": "G B D", "correct": True,
    })
    assert res.status_code == 200 and res.json()["correct"] is False
    with SessionLocal() as db:
        row = db.scalars(select(PracticeAttempt).where(PracticeAttempt.user_id == uid)).one()
        assert row.correct is False
        # Chỉ lưu trường của đề, bỏ trường lạ client gửi kèm.
        assert row.question == {"symbol": "G7"}


def test_de_thieu_truong_tra_422_va_khong_ghi():
    uid = make_user()
    res = submit(uid, "interval", {"lower": "C4"}, "M3")
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "PRACTICE_QUESTION_INVALID"
    # Dạng bài lạ bị chặn ở lớp kiểm tra đầu vào (400 VALIDATION_ERROR, SRS 7.4).
    res = submit(uid, "melody", {"symbol": "C"}, "C")
    assert res.status_code == 400
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(PracticeAttempt).where(PracticeAttempt.user_id == uid)) == 0


def test_can_dang_nhap_va_chi_thay_lich_su_cua_minh():
    assert client.post("/api/v1/practice/attempts", json={"kind": "chord", "question": {"symbol": "C"}, "answer": "C E G"}).status_code == 401
    assert client.get("/api/v1/practice/history").status_code == 401
    a, b = make_user(), make_user()
    submit(a, "chord", {"symbol": "C"}, "C E G")
    assert client.get("/api/v1/practice/history", headers=auth(b)).json() == {"items": [], "stats": []}


def test_luot_admin_la_is_test():
    admin = make_user("admin")
    submit(admin, "chord", {"symbol": "C"}, "C E G", role="admin")
    with SessionLocal() as db:
        assert db.scalars(select(PracticeAttempt.is_test).where(PracticeAttempt.user_id == admin)).one() is True


def test_luyen_tap_khong_tao_luot_lam_bai_hoc():
    uid = make_user()
    submit(uid, "chord", {"symbol": "C"}, "C E G")
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Attempt).where(Attempt.user_id == uid)) == 0
