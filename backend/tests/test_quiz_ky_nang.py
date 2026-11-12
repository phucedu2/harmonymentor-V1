"""Quiz theo kỹ năng (FR-14 rút gọn): tối đa 10 câu có sẵn, đúng kỹ năng, không lộ đáp án, nộp qua /attempts."""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.db.models import User
from app.db.session import SessionLocal
from app.main import app
from tests.auth_helpers import auth


@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c


def learner():
    uid = f"quiz-{uuid4().hex[:12]}"
    with SessionLocal() as db:
        db.add(User(id=uid, display_name="Thử quiz", email=f"{uid}@example.test", role="learner", is_active=True))
        db.commit()
    return auth(uid)


def test_quiz_chi_gom_cau_cua_ky_nang_va_khong_lo_dap_an(client):
    h = learner()
    r = client.get("/api/v1/practice/quiz?skill_id=chord.triad_build&n=10", headers=h)
    assert r.status_code == 200
    body = r.json()
    assert 3 <= len(body["questions"]) <= 10  # mỗi kỹ năng L01–L04 có ≥ 3 câu (ADR-022)
    assert body["available"] >= len(body["questions"])
    assert all(q["skill_id"] == "chord.triad_build" for q in body["questions"])
    assert len({q["exercise_id"] for q in body["questions"]}) == len(body["questions"])
    assert "answer_key" not in r.text and "expected" not in r.text


def test_quiz_n_nho_hon_so_cau_co_san(client):
    h = learner()
    body = client.get("/api/v1/practice/quiz?skill_id=chord.triad_build&n=2", headers=h).json()
    assert len(body["questions"]) == 2


def test_quiz_ky_nang_khong_ton_tai_la_404_va_can_dang_nhap(client):
    h = learner()
    assert client.get("/api/v1/practice/quiz?skill_id=khong.co", headers=h).status_code == 404
    assert client.get("/api/v1/practice/quiz?skill_id=chord.triad_build").status_code == 401
    assert client.get("/api/v1/practice/quiz?skill_id=chord.triad_build&n=11", headers=h).status_code == 400


def test_quiz_uu_tien_cau_chua_lam_roi_cau_da_dung(client):
    h = learner()
    first = client.get("/api/v1/practice/quiz?skill_id=chord.triad_build&n=1", headers=h).json()["questions"][0]
    # làm sai câu đó: lần sau nó không nằm trong nhóm "chưa làm", nên câu chưa làm phải xuất hiện trước.
    # Đáp án phải đọc được tên nốt: "###" bị /attempts trả 422 (INVALID_PITCH) nên không ghi lượt làm nào.
    r = client.post("/api/v1/attempts", headers=h, json={"exercise_version_id": first["exercise_version_id"], "answer": "C Db D", "input_method": "text"})
    assert r.status_code == 200 and r.json()["correct"] is False
    again = client.get("/api/v1/practice/quiz?skill_id=chord.triad_build&n=1", headers=h).json()["questions"][0]
    assert again["exercise_id"] != first["exercise_id"]
