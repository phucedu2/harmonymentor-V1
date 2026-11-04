"""GĐ1 pipeline AI: lượt ôn tính mastery theo luật 2A, và đường mở L03 theo ngày (C1).

2A (Phúc chốt 04/11/2026, bỏ 1A): lượt ôn thẻ **máy chấm**, **đã đến hạn hoặc quá hạn**, là một
sự kiện mastery cho skill của thẻ: đúng = 1, sai = 0. Tối đa một sự kiện ôn mỗi kỹ năng mỗi ngày
theo giờ Việt Nam. Ôn trước hạn và thẻ tự đánh giá không tính.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.content.curriculum_specs import lesson_by_id
from app.db.models import MasteryEvent, MasteryState, ReviewItem, ReviewState, User
from app.db.session import SessionLocal
from app.main import app
from app.services import learning_service as ls
from app.services.grading_service import is_self_check
from tests.auth_helpers import correct_answer

# 08:00 giờ Việt Nam = 01:00 UTC.
DAY0 = datetime(2026, 11, 2, 1, 0, tzinfo=timezone.utc)


@pytest.fixture(scope="module", autouse=True)
def _schema_and_seed():
    # Chạy lifespan của app (create_schema + seed) để file test chạy riêng lẻ trên CSDL mới vẫn được.
    with TestClient(app):
        yield


def make_user() -> str:
    user_id = "gd1-" + uuid4().hex[:12]
    with SessionLocal() as db:
        db.add(User(id=user_id, display_name="GĐ1"))
        db.commit()
    return user_id


def learn_lesson(user_id: str, lesson_id: str, now: datetime) -> None:
    with SessionLocal() as db:
        for spec in lesson_by_id(lesson_id)["exercises"]:
            ex = db.get(ls.Exercise, spec["id"])
            version = ls.versioning.current_version(ex)
            attempt, _ = ls.submit_attempt(db, user_id, version.id, correct_answer(spec), now=now)
            assert attempt.correct, spec["id"]
        ls.complete_lesson(db, user_id, lesson_id, now=now)


def cards(user_id: str, skill_id: str) -> list[tuple[str, bool]]:
    with SessionLocal() as db:
        rows = db.execute(select(ReviewItem, ReviewState)
                          .join(ReviewState, ReviewState.review_item_id == ReviewItem.id)
                          .where(ReviewState.user_id == user_id, ReviewItem.skill_id == skill_id)
                          .order_by(ReviewItem.id)).all()
        return [(item.id, is_self_check(item.grading_strategy, item.grader_config)) for item, _ in rows]


def review(user_id: str, item_id: str, now: datetime, correct: bool = True) -> None:
    with SessionLocal() as db:
        item = db.get(ReviewItem, item_id)
        answer = (item.answer_key.get("accepted") or [item.answer_key.get("expected")])[0] if correct else "zzz"
        if isinstance(answer, list):
            answer = " ".join(answer)
        _, _, _, outcome, _ = ls.answer_review(db, user_id, item_id, answer, "auto", None, now=now)
        assert outcome.correct is correct, (item_id, outcome.feedback)


def score(user_id: str, skill_id: str) -> float | None:
    with SessionLocal() as db:
        row = db.scalar(select(MasteryState).where(MasteryState.user_id == user_id, MasteryState.skill_id == skill_id))
        return None if row is None else row.score


def review_events(user_id: str, skill_id: str) -> int:
    with SessionLocal() as db:
        return len(db.scalars(select(MasteryEvent).where(
            MasteryEvent.user_id == user_id, MasteryEvent.skill_id == skill_id,
            MasteryEvent.source == "review", MasteryEvent.counted.is_(True))).all())


def test_c1_reproduce_exercises_alone_cap_roman_at_030():
    """Tái hiện C1: một câu duy nhất → roman.major_seventh tối đa 0,30, L03 không bao giờ đủ điều kiện."""
    user_id = make_user()
    learn_lesson(user_id, "L01", DAY0)
    learn_lesson(user_id, "L02", DAY0)
    assert score(user_id, "roman.major_seventh") == pytest.approx(0.30)
    # Làm lại đúng câu đó không cộng (S7).
    learn_lesson(user_id, "L02", DAY0 + timedelta(hours=1))
    assert score(user_id, "roman.major_seventh") == pytest.approx(0.30)


def test_2a_due_reviews_unlock_l03_on_day_3():
    user_id = make_user()
    learn_lesson(user_id, "L01", DAY0)
    learn_lesson(user_id, "L02", DAY0 + timedelta(days=1))
    roman_cards = [cid for cid, self_check in cards(user_id, "roman.major_seventh") if not self_check]
    assert len(roman_cards) == 4
    day1 = DAY0 + timedelta(days=1, minutes=10)
    for cid in roman_cards:  # cả 4 thẻ đến hạn ngay sau khi xong bài
        review(user_id, cid, day1)
    # Chỉ 1 sự kiện ôn/kỹ năng/ngày: 0,30 → 0,51, không phải 0,83.
    assert score(user_id, "roman.major_seventh") == pytest.approx(0.51)
    assert review_events(user_id, "roman.major_seventh") == 1
    # Ngày 2: thẻ ở hộp 2 hẹn sau 2 ngày, chưa đến hạn → ôn trước hạn không tính.
    review(user_id, roman_cards[0], DAY0 + timedelta(days=2))
    assert score(user_id, "roman.major_seventh") == pytest.approx(0.51)
    # Ngày 3: đến hạn → 0,657 ≥ 0,60.
    review(user_id, roman_cards[1], DAY0 + timedelta(days=3, minutes=20))
    assert score(user_id, "roman.major_seventh") == pytest.approx(0.657)


def test_2a_wrong_due_review_counts_zero():
    user_id = make_user()
    learn_lesson(user_id, "L01", DAY0)
    card = next(cid for cid, self_check in cards(user_id, "interval.naming") if not self_check)
    review(user_id, card, DAY0 + timedelta(minutes=5), correct=False)
    assert score(user_id, "interval.naming") == pytest.approx(0.30 * 0.7)


def test_2a_self_check_card_never_counts():
    user_id = make_user()
    learn_lesson(user_id, "L01", DAY0)
    card = next(cid for cid, self_check in cards(user_id, "pitch.spelling") if self_check)
    with SessionLocal() as db:
        ls.answer_review(db, user_id, card, "", "good", None, now=DAY0 + timedelta(minutes=5))
    assert score(user_id, "pitch.spelling") == pytest.approx(0.30)
    assert review_events(user_id, "pitch.spelling") == 0


def test_2a_daily_limit_uses_vietnam_calendar_day():
    """23:30 và 00:30 giờ Việt Nam là hai ngày khác nhau, dù cùng ngày UTC."""
    user_id = make_user()
    learn_lesson(user_id, "L01", DAY0)
    learn_lesson(user_id, "L02", DAY0)
    roman = [cid for cid, self_check in cards(user_id, "roman.major_seventh") if not self_check]
    late = datetime(2026, 11, 2, 16, 30, tzinfo=timezone.utc)   # 23:30 VN ngày 02/11
    early = datetime(2026, 11, 2, 17, 30, tzinfo=timezone.utc)  # 00:30 VN ngày 03/11
    review(user_id, roman[0], late)
    review(user_id, roman[1], early)
    assert review_events(user_id, "roman.major_seventh") == 2


def test_rebuild_mastery_matches_online_and_is_deterministic():
    from app.services.mastery_service import rebuild_user

    user_id = make_user()
    learn_lesson(user_id, "L01", DAY0)
    learn_lesson(user_id, "L02", DAY0 + timedelta(days=1))
    for cid in [c for c, s in cards(user_id, "roman.major_seventh") if not s][:2]:
        review(user_id, cid, DAY0 + timedelta(days=1, minutes=10))
    with SessionLocal() as db:
        online = {r.skill_id: (round(r.score, 9), r.attempts_count)
                  for r in db.scalars(select(MasteryState).where(MasteryState.user_id == user_id))}
        first = rebuild_user(db, user_id)
        second = rebuild_user(db, user_id)
        db.commit()
    assert first == second == online
