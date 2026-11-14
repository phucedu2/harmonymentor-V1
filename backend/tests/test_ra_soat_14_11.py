"""Đợt sửa 14/11/2026: RS-07, RS-19, RS-27, RS-28."""

from __future__ import annotations

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.api import ai_tutor
from app.ai.tutor import router
from app.db.models import User
from app.db.session import SessionLocal
from app.main import app
from app.services.ai_tutor_service import is_study_advice
from app.services.grading_service import _split_notes
from tests.auth_helpers import auth

client: TestClient


def ask(message):
    uid = "rs14-" + uuid4().hex[:12]
    with SessionLocal() as db:
        db.add(User(id=uid, display_name="Học sinh", email=f"{uid}@example.test"))
        db.commit()
    r = client.post("/api/v1/chat/message", headers=auth(uid), json={"message": message})
    assert r.status_code == 200, r.text
    return r.json()


@pytest.fixture(autouse=True)
def ai_off():
    global client
    app.dependency_overrides[ai_tutor.embedder_dep] = lambda: None
    app.dependency_overrides[ai_tutor.provider_dep] = lambda: None
    with TestClient(app) as client:   # chạy startup để có bảng
        yield
    app.dependency_overrides.pop(ai_tutor.embedder_dep, None)
    app.dependency_overrides.pop(ai_tutor.provider_dep, None)


@pytest.mark.parametrize("q", ["Mình nên học bài nào tiếp?", "nen hoc bai nao tiep theo", "Bài tiếp theo là gì",
                               "Tôi nên bắt đầu từ đâu", "gợi ý bài học cho mình"])
def test_study_advice_questions_are_recognised(q):
    assert is_study_advice(q)


@pytest.mark.parametrize("q", ["Hợp âm là gì?", "Quãng ba trưởng gồm mấy cung", "C la not gi vay", "Cảm ơn bạn"])
def test_music_questions_are_not_study_advice(q):
    assert not is_study_advice(q)


def test_rs27_new_learner_gets_recommendation_not_refusal():
    """RS-27: trước đây bị từ chối là "ngoài âm nhạc". Nay trả lời bằng hệ gợi ý, không cần AI."""
    body = ask("Mình nên học bài nào tiếp?")
    assert body["intent"] == "study_advice"
    assert "Mình chỉ là trợ lý âm nhạc" not in body["reply"]
    assert body["source_label"] == "Gợi ý theo tiến độ của bạn"
    assert body["reply"].strip()


def test_rs07_ai_off_says_not_found_without_off_topic_pointer():
    body = ask("Kết cấu fugue là gì?")
    assert "chưa tìm thấy" in body["reply"] and "tạm nghỉ" not in body["reply"]


def test_rs28_no_nearest_lesson_below_gray_threshold():
    """Điểm khớp dưới ngưỡng xám thì không gợi ý "bài gần nhất" (gợi ý lạc đề)."""
    dec = router.decide("zxqv blorp", None)
    assert dec.nearest_lesson is None


def test_rs19_trailing_punctuation_after_note_name():
    assert _split_notes(["Son", "Si", "Rê."]) == ["G", "B", "D"]
    assert _split_notes("Son Si Rê.") == ["G", "B", "D"]
    assert _split_notes(["Rê,", "Fa;", "La"]) == ["D", "F", "A"]


def test_rs11_song_example_blocks_are_valid_draft_and_hidden():
    """RS-11: ví dụ nghe được gắn vòng hợp âm quen thuộc; hợp âm do Engine hiểu, khối nháp ẩn với người học."""
    from app.content.draft_specs import SONG_EXAMPLE_BLOCKS, blocks_with_drafts
    from app.content.curriculum_specs import LESSON_SPECS
    from app.content.versioning import block_visible
    from app.music_engine import parse_chord_symbol

    by_id = {s["id"]: s for s in LESSON_SPECS}
    for lesson_id, (_, _, progression, _) in SONG_EXAMPLE_BLOCKS.items():
        for symbol in progression:
            parse_chord_symbol(symbol)   # ném lỗi nếu Engine không hiểu
        blocks = [b for b in blocks_with_drafts(by_id[lesson_id]) if b[0] == f"{lesson_id}-BVD"]
        assert len(blocks) == 1 and blocks[0][2]["status"] == "draft"
        assert not block_visible(blocks[0][2])
