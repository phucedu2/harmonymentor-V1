"""HM-012: lịch Leitner theo tài liệu 04 mục 6.4 (bản 2.1).

Thẻ mới đến hạn ngay; đúng khi chưa đến hạn thì giữ hộp và giữ ngày hẹn; sai lúc nào cũng về
hộp 1, hẹn sau 1 ngày; đúng khi đến hạn lên một hộp, tối đa hộp 5. Lỗi cũ: bấm "Đã nhớ" liên tục
một thẻ trong vài giây là thẻ nhảy từ hộp 1 lên hộp 5.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.db.models import ReviewItem, ReviewState, User
from app.db.session import SessionLocal
from app.main import app
from app.services.review_scheduler import apply_review_result, leitner_box
from tests.auth_helpers import answer_lesson_correctly, auth, correct_answer

T0 = datetime(2026, 11, 2, 8, 0, tzinfo=timezone.utc)


def make_user() -> str:
    user_id = "hm012-" + uuid4().hex[:12]
    with SessionLocal() as db:
        db.add(User(id=user_id, display_name="HM-012 test user"))
        db.commit()
    return user_id


def card(box: int, due_at: datetime) -> ReviewState:
    return ReviewState(user_id="x", review_item_id="y", status="active", stage=box - 1,
                       interval_days=[1, 2, 4, 8, 16][box - 1], due_at=due_at,
                       failure_count=0, success_streak=0)


def aware(value: datetime) -> datetime:
    # SQLite đọc lại cột timezone=True thành giờ không múi; PostgreSQL giữ nguyên.
    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


# --- Luật chuyển hộp (đơn vị) ----------------------------------------------------------

def test_correct_before_due_keeps_box_and_due_date():
    due = T0 + timedelta(days=2)
    state = card(2, due)
    apply_review_result(state, True, "good", now=T0)
    assert (leitner_box(state.stage), state.interval_days) == (2, 2)
    assert state.due_at == due


def test_easy_before_due_also_keeps_box_and_due_date():
    due = T0 + timedelta(hours=1)
    state = card(1, due)
    apply_review_result(state, True, "easy", now=T0)
    assert leitner_box(state.stage) == 1 and state.due_at == due


def test_wrong_before_due_resets_to_box_1_due_in_one_day():
    state = card(4, T0 + timedelta(days=5))
    apply_review_result(state, False, "auto", now=T0)
    assert (leitner_box(state.stage), state.interval_days) == (1, 1)
    assert state.due_at == T0 + timedelta(days=1)
    assert state.failure_count == 1


def test_again_rating_before_due_resets_to_box_1():
    state = card(3, T0 + timedelta(days=3))
    apply_review_result(state, True, "again", now=T0)
    assert leitner_box(state.stage) == 1 and state.due_at == T0 + timedelta(days=1)


def test_correct_when_due_moves_up_exactly_one_box():
    for box, next_days in [(1, 2), (2, 4), (3, 8), (4, 16)]:
        state = card(box, T0)
        apply_review_result(state, True, "good", now=T0)
        assert (leitner_box(state.stage), state.interval_days) == (box + 1, next_days)
        assert state.due_at == T0 + timedelta(days=next_days)


def test_correct_when_overdue_moves_up_exactly_one_box():
    state = card(2, T0 - timedelta(days=10))
    apply_review_result(state, True, "good", now=T0)
    assert leitner_box(state.stage) == 3 and state.due_at == T0 + timedelta(days=4)


def test_box_5_stays_box_5():
    state = card(5, T0)
    apply_review_result(state, True, "easy", now=T0)
    assert (leitner_box(state.stage), state.interval_days) == (5, 16)
    assert state.due_at == T0 + timedelta(days=16)


def test_hard_when_due_keeps_box_and_reschedules():
    # "hard" không có trong 04 mục 6.4; nhóm chốt 30/10: đúng nhưng chật vật thì giữ hộp (ADR-002, phần bổ sung 30/10).
    state = card(3, T0)
    apply_review_result(state, True, "hard", now=T0)
    assert leitner_box(state.stage) == 3 and state.due_at == T0 + timedelta(days=4)


def test_hard_before_due_keeps_due_date():
    due = T0 + timedelta(days=3)
    state = card(3, due)
    apply_review_result(state, True, "hard", now=T0)
    assert leitner_box(state.stage) == 3 and state.due_at == due


def test_due_card_walks_1_to_5_only_on_schedule():
    state = card(1, T0)
    now = T0
    boxes = []
    for _ in range(6):
        apply_review_result(state, True, "good", now=now)
        boxes.append(leitner_box(state.stage))
        now = state.due_at
    assert boxes == [2, 3, 4, 5, 5, 5]


# --- Qua API -----------------------------------------------------------------------------

def test_new_cards_are_due_immediately_after_completing_lesson():
    with TestClient(app) as client:
        user_id = make_user()
        headers = auth(user_id)
        answer_lesson_correctly(client, "L01", headers)
        before = datetime.now(timezone.utc)
        body = client.post("/api/v1/lessons/L01/complete", json={}, headers=headers).json()
        assert datetime.fromisoformat(body["first_review_due_at"].replace("Z", "+00:00")).replace(
            tzinfo=timezone.utc) <= datetime.now(timezone.utc)
        due = client.get("/api/v1/review/due", headers=headers).json()
        assert {c["review_item_id"] for c in due} == {f"L01-F{i:02d}" for i in range(1, 9)}
        assert all(c["leitner_box"] == 1 for c in due)
        with SessionLocal() as db:
            states = db.scalars(select(ReviewState).where(ReviewState.user_id == user_id)).all()
        assert len(states) == 8 and all(aware(s.due_at) <= datetime.now(timezone.utc) for s in states)
        assert all(aware(s.due_at) >= before - timedelta(seconds=5) for s in states)


def test_spamming_remembered_does_not_climb_boxes():
    """Tái hiện HM-012: trước khi sửa, 5 lần "good" liên tiếp đưa thẻ từ hộp 1 lên hộp 5."""
    with TestClient(app) as client:
        user_id = make_user()
        headers = auth(user_id)
        answer_lesson_correctly(client, "L01", headers)
        client.post("/api/v1/lessons/L01/complete", json={}, headers=headers)
        with SessionLocal() as db:
            item = db.get(ReviewItem, "L01-F01")
            answer = correct_answer({"answer_key": item.answer_key})
        boxes = []
        for _ in range(5):
            reply = client.post("/api/v1/review/L01-F01/answer", json={"answer": answer, "rating": "good"},
                                headers=headers)
            assert reply.status_code == 200, reply.json()
            assert reply.json()["correct"] is True
            boxes.append(reply.json()["leitner_box"])
        assert boxes == [2, 2, 2, 2, 2]

        # Sai trước hạn vẫn bị tính: về hộp 1, hẹn sau 1 ngày.
        wrong = client.post("/api/v1/review/L01-F01/answer", json={"answer": "sai-có-chủ-đích", "rating": "auto"},
                            headers=headers).json()
        assert wrong["correct"] is False and wrong["leitner_box"] == 1 and wrong["interval_days"] == 1
