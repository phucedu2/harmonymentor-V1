"""HM-011: máy chủ không được tin `input_method` do client gửi.

Lỗi (rà soát 29/10): client gửi `input_method="piano"` là chuyển sang chấm cao độ, bỏ qua chính tả,
nên L01-Q04 (dựng D minor) nhận `D E# A` là đúng.

Hợp đồng (Phúc chốt 30/10, bản 2 theo góp ý Astra; chi tiết docs/bao-cao/HM-011_DE_XUAT_API.md):
- Cách nhập hợp lệ do phiên bản câu hỏi quyết định: câu có `options` chỉ nhận `choice`, câu không có
  `options` chỉ nhận `text`; `piano` chỉ khi `grader_config.allowed_input_methods` khai báo.
- Không gửi `input_method` thì máy chủ dùng cách nhập mặc định của câu.
- `piano` chỉ nhận đúng 12 tên thăng mà VirtualPiano gửi, không quãng tám, không lặp.
- `choice` phải là một trong các `options`.
- Mọi request bị từ chối trả 422 và không ghi lượt làm.

Test viết TRƯỚC khi sửa code production, đỏ có chủ đích cho tới khi Thắng duyệt hợp đồng.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
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


def exercise(client: TestClient, lesson_id: str, exercise_id: str) -> dict:
    exercises = client.get(f"/api/v1/lessons/{lesson_id}").json()["exercises"]
    return next(e for e in exercises if e["id"] == exercise_id)


def attempts_of(user_id: str) -> int:
    with SessionLocal() as db:
        return db.scalar(select(func.count()).select_from(Attempt).where(Attempt.user_id == user_id))


def submit(client: TestClient, user_id: str, version_id: str, answer: str, input_method: str | None):
    body = {"exercise_version_id": version_id, "answer": answer}
    if input_method is not None:
        body["input_method"] = input_method
    return client.post("/api/v1/attempts", json=body, headers=auth(user_id))


def assert_rejected(reply, code: str, user_id: str) -> None:
    assert reply.status_code == 422, reply.json()
    assert reply.json()["error"]["code"] == code
    # Lượt bị từ chối không vào lịch sử, mastery hay "đã làm đúng" của bài.
    assert attempts_of(user_id) == 0


# --- Câu gõ chữ (không có options): L01-Q04, dựng D minor -------------------------------------

def test_l01_q04_misspelled_d_minor_is_wrong_when_typed():
    with TestClient(app) as client:
        user_id = make_user()
        version = exercise(client, "L01", "L01-Q04")["version_id"]
        for method in (None, "text"):
            reply = submit(client, user_id, version, "D E# A", method)
            assert reply.status_code == 200, reply.json()
            assert reply.json()["correct"] is False


@pytest.mark.parametrize("answer", ["D E# A", "D F A"])
def test_l01_q04_client_cannot_switch_to_pitch_grading_by_sending_piano(answer):
    """Tái hiện HM-011. Đúng hay sai chính tả đều bị từ chối: quyền nhập do câu hỏi quyết định."""
    with TestClient(app) as client:
        user_id = make_user()
        version = exercise(client, "L01", "L01-Q04")["version_id"]
        assert_rejected(submit(client, user_id, version, answer, "piano"), "INPUT_METHOD_NOT_ALLOWED", user_id)


def test_l01_q04_rejects_choice_because_it_has_no_options():
    with TestClient(app) as client:
        user_id = make_user()
        version = exercise(client, "L01", "L01-Q04")["version_id"]
        assert_rejected(submit(client, user_id, version, "D F A", "choice"), "INPUT_METHOD_NOT_ALLOWED", user_id)


# --- Câu trắc nghiệm (có options): L04-Q01 ----------------------------------------------------

def test_mcq_accepts_choice_and_defaults_to_choice_when_method_missing():
    with TestClient(app) as client:
        user_id = make_user()
        version = exercise(client, "L04", "L04-Q01")["version_id"]
        for method in ("choice", None):
            reply = submit(client, user_id, version, "Dm7-G7-Cmaj7", method)
            assert reply.status_code == 200, reply.json()
            assert reply.json()["correct"] is True
        wrong = submit(client, user_id, version, "Am7-Dm7-G7", "choice")
        assert wrong.status_code == 200 and wrong.json()["correct"] is False


def test_mcq_rejects_text_input():
    with TestClient(app) as client:
        user_id = make_user()
        version = exercise(client, "L04", "L04-Q01")["version_id"]
        assert_rejected(submit(client, user_id, version, "Dm7-G7-Cmaj7", "text"), "INPUT_METHOD_NOT_ALLOWED", user_id)


@pytest.mark.parametrize("answer", ["Dm7 G7 Cmaj7", "dm7-g7-cmaj7", "ii-V-I", ""])
def test_choice_must_be_one_of_the_options(answer):
    with TestClient(app) as client:
        user_id = make_user()
        version = exercise(client, "L04", "L04-Q01")["version_id"]
        assert_rejected(submit(client, user_id, version, answer, "choice"), "ANSWER_NOT_IN_OPTIONS", user_id)


# --- Câu cho phép piano: L04-Q03, dựng G7 -----------------------------------------------------

def test_lesson_api_exposes_allowed_input_methods_per_version():
    # Frontend chỉ hiện nút "Kiểm tra bằng piano" khi máy chủ nói phiên bản này cho phép.
    with TestClient(app) as client:
        assert exercise(client, "L01", "L01-Q04")["allowed_input_methods"] == ["text"]
        assert exercise(client, "L04", "L04-Q01")["allowed_input_methods"] == ["choice"]
        assert exercise(client, "L04", "L04-Q03")["allowed_input_methods"] == ["text", "piano"]


def test_enabling_piano_on_l04_q03_bumped_its_version():
    with TestClient(app) as client:
        assert exercise(client, "L04", "L04-Q03")["version_id"] != "L04-Q03-v1", \
            "bật piano cho câu đã phát hành phải tăng version (ADR-006)"


@pytest.mark.parametrize("answer", ["G B D F", "F D B G"])
def test_piano_on_allowed_exercise_grades_pitch_classes(answer):
    # VirtualPiano gửi theo thứ tự bấm, nên thứ tự không quan trọng khi chấm cao độ.
    with TestClient(app) as client:
        user_id = make_user()
        version = exercise(client, "L04", "L04-Q03")["version_id"]
        reply = submit(client, user_id, version, answer, "piano")
        assert reply.status_code == 200, reply.json()
        assert reply.json()["correct"] is True


def test_piano_wrong_pitch_is_graded_wrong_not_rejected():
    with TestClient(app) as client:
        user_id = make_user()
        version = exercise(client, "L04", "L04-Q03")["version_id"]
        reply = submit(client, user_id, version, "G B D F#", "piano")
        assert reply.status_code == 200 and reply.json()["correct"] is False
        assert attempts_of(user_id) == 1


@pytest.mark.parametrize("answer", [
    "G B D E#",      # E# không phải tên VirtualPiano gửi (Astra 30/10)
    "G B D Gb",      # VirtualPiano chỉ gửi tên thăng
    "G4 B4 D5 F5",   # không kèm quãng tám
    "G B D F F",     # không lặp nốt
    "G B D H",       # không phải tên nốt
    "",
])
def test_piano_payload_must_use_virtual_piano_names(answer):
    with TestClient(app) as client:
        user_id = make_user()
        version = exercise(client, "L04", "L04-Q03")["version_id"]
        assert_rejected(submit(client, user_id, version, answer, "piano"), "INVALID_PIANO_PAYLOAD", user_id)


def test_typed_answer_on_piano_exercise_still_checks_spelling():
    with TestClient(app) as client:
        user_id = make_user()
        version = exercise(client, "L04", "L04-Q03")["version_id"]
        for method in ("text", None):
            reply = submit(client, user_id, version, "G B D E#", method)
            assert reply.status_code == 200 and reply.json()["correct"] is False
