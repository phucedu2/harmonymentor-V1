"""HM-011: máy chủ không được tin `input_method` do client gửi.

Lỗi (rà soát 29/10): gửi `input_method="piano"` là bài chuyển sang chấm cao độ, bỏ qua chính tả,
nên L01-Q04 (dựng D minor) nhận `D E# A` là đúng. Chế độ chấm cao độ chỉ được dùng khi chính
phiên bản câu hỏi cho phép nhập bằng piano.

Các test dưới đây viết TRƯỚC khi sửa (Phúc chốt 30/10, phương án A): chúng đỏ có chủ đích cho tới
khi Thắng duyệt hợp đồng API trong docs/bao-cao/HM-011_DE_XUAT_API.md.
"""

from __future__ import annotations

from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.db.models import Attempt, User
from app.db.session import SessionLocal
from app.main import app
from tests.auth_helpers import auth


def make_user() -> str:
    user_id = "hm011-" + uuid4().hex[:12]
    with SessionLocal() as db:
        db.add(User(id=user_id, display_name="HM-011 test user"))
        db.commit()
    return user_id


def version_of(client: TestClient, lesson_id: str, exercise_id: str) -> str:
    exercises = client.get(f"/api/v1/lessons/{lesson_id}").json()["exercises"]
    return next(e["version_id"] for e in exercises if e["id"] == exercise_id)


def attempts_of(user_id: str) -> int:
    with SessionLocal() as db:
        return db.scalar(select(func.count()).select_from(Attempt).where(Attempt.user_id == user_id))


def submit(client: TestClient, user_id: str, version_id: str, answer: str, input_method: str | None):
    body = {"exercise_version_id": version_id, "answer": answer}
    if input_method is not None:
        body["input_method"] = input_method
    return client.post("/api/v1/attempts", json=body, headers=auth(user_id))


def test_l01_q04_misspelled_d_minor_is_wrong_when_typed():
    with TestClient(app) as client:
        user_id = make_user()
        version = version_of(client, "L01", "L01-Q04")
        for method in (None, "text"):
            reply = submit(client, user_id, version, "D E# A", method)
            assert reply.status_code == 200, reply.json()
            assert reply.json()["correct"] is False


def test_l01_q04_client_cannot_switch_to_pitch_grading_by_sending_piano():
    """Tái hiện HM-011: hiện tại câu trả lời sai chính tả được chấm đúng chỉ vì client tự khai piano."""
    with TestClient(app) as client:
        user_id = make_user()
        version = version_of(client, "L01", "L01-Q04")
        reply = submit(client, user_id, version, "D E# A", "piano")
        assert reply.status_code == 422, reply.json()
        assert reply.json()["error"]["code"] == "INPUT_METHOD_NOT_ALLOWED"


def test_rejected_input_method_records_no_attempt():
    # Lượt bị từ chối không được vào lịch sử, mastery hay "đã làm đúng" của bài.
    with TestClient(app) as client:
        user_id = make_user()
        version = version_of(client, "L01", "L01-Q04")
        submit(client, user_id, version, "D E# A", "piano")
        assert attempts_of(user_id) == 0


def test_correct_spelling_still_rejected_when_piano_not_allowed():
    # Đúng hay sai đều vậy: quyền nhập do câu hỏi quyết định, không do đáp án.
    with TestClient(app) as client:
        user_id = make_user()
        version = version_of(client, "L01", "L01-Q04")
        reply = submit(client, user_id, version, "D F A", "piano")
        assert reply.status_code == 422


def test_lesson_api_exposes_allowed_input_methods_per_version():
    # Frontend chỉ hiện nút "Kiểm tra bằng piano" khi máy chủ nói phiên bản này cho phép.
    with TestClient(app) as client:
        exercises = {e["id"]: e for e in client.get("/api/v1/lessons/L01").json()["exercises"]}
        assert "text" in exercises["L01-Q04"]["allowed_input_methods"]
        assert "piano" not in exercises["L01-Q04"]["allowed_input_methods"]
        l04 = {e["id"]: e for e in client.get("/api/v1/lessons/L04").json()["exercises"]}
        assert "piano" in l04["L04-Q03"]["allowed_input_methods"]


def test_piano_allowed_exercise_grades_pitch_classes_only():
    """L04-Q03 (G7) là câu duy nhất có khối piano gửi bài; phím đàn không mang chính tả nên chấm cao độ."""
    with TestClient(app) as client:
        user_id = make_user()
        version = version_of(client, "L04", "L04-Q03")
        assert version != "L04-Q03-v1", "bật piano cho câu đã phát hành phải tăng version (ADR-006)"
        reply = submit(client, user_id, version, "G B D E#", "piano")
        assert reply.status_code == 200, reply.json()
        assert reply.json()["correct"] is True
        typed = submit(client, user_id, version, "G B D E#", "text")
        assert typed.status_code == 200 and typed.json()["correct"] is False
