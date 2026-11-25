"""Tests for curated knowledge outside the lesson corpus."""
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.ai.tutor.supplemental import answer


@pytest.mark.parametrize("question", [
    "Vibrato trên violin khác vibrato trên guitar thế nào?",
    "Vibrato của violin và guitar khác nhau ở đâu?",
    "Cách tạo vibrato trên violin có giống guitar không?",
])
def test_vibrato_comparison_with_ai_off(question):
    from app.services import ai_tutor_service as tutor

    draft, _ = tutor.answer_question(None, None, question, [], None, None, datetime.now(timezone.utc))
    assert draft.flow == "B" and draft.route == "supplemental" and draft.status == "ok"
    assert draft.source_label == "Ngoài giáo trình · Nguồn tham khảo"
    assert draft.supplemental_source["url"] == "https://en.wikipedia.org/wiki/Finger_vibrato"
    assert "guitar cổ điển" in draft.reply and "guitar điện" in draft.reply
    assert not draft.citations and not draft.claims and not draft.suggested_lesson and not draft.llm_calls


def test_vibrato_catalog_does_not_override_other_requests():
    assert answer("Trong bài L02, vibrato trên violin khác vibrato trên guitar thế nào?") is None
    assert answer("Vibrato trên violin khác vibrato trên guitar thế nào? Nhịp 6/8 là gì?") is None
    assert answer("Vibrato trên cello hoạt động thế nào?") is None


@pytest.mark.parametrize("reason", ["ai_disabled", "unavailable", "global_budget"])
def test_unsourced_music_fallback_ignores_unconfirmed_nearest_lesson(reason):
    from app.services import ai_tutor_service as tutor

    decision = SimpleNamespace(kind="unknown", later_lesson=None, nearest_lesson="L02")
    draft = tutor._b_without_ai(decision, {"L02": "Âm giai trưởng"}, reason, "Vibrato trên cello hoạt động thế nào?")
    assert draft.flow == "B" and draft.status == "fallback" and draft.fallback_reason == reason
    assert draft.source_label == "Ngoài giáo trình · Chưa có nguồn tham khảo trong kho"
    assert not draft.citations and not draft.claims and not draft.supplemental_source
    assert "L02" not in draft.reply and not draft.suggested_lesson and not draft.suggested_actions


def test_music_fallback_keeps_confirmed_later_lesson():
    from app.services import ai_tutor_service as tutor

    decision = SimpleNamespace(kind="unknown", later_lesson="L07", nearest_lesson="L02")
    draft = tutor._b_without_ai(decision, {"L07": "Bài sau"}, "ai_disabled")
    assert draft.suggested_lesson == "L07" and draft.suggested_actions == ["Mở bài L07"]
    assert "L07" in draft.reply and "L02" not in draft.reply


def test_uncatalogued_vibrato_routes_as_music_with_ai_off():
    from app.services import ai_tutor_service as tutor

    draft, _ = tutor.answer_question(None, None, "Vibrato trên cello hoạt động thế nào?", [], None, None,
                                     datetime.now(timezone.utc))
    assert draft.flow == "B" and draft.source_label == "Ngoài giáo trình · Chưa có nguồn tham khảo trong kho"
    assert not draft.suggested_lesson and not draft.suggested_actions


def test_string_bending_is_a_curated_outside_lesson_answer():
    item = answer("String bending trên guitar là gì?")
    assert item is not None
    assert "cao độ" in item.reply
    assert item.source_url.startswith("https://")


def test_curated_answer_does_not_match_unrelated_guitar_question():
    assert answer("Guitar có bao nhiêu dây?") is None


def test_tab_bend_variant_is_supported():
    assert answer("Trên tab guitar, ký hiệu bend bảo em làm gì?") is not None


def test_catalog_does_not_override_lesson_or_compound_request():
    assert answer("Trong bài L01, string bending là gì?") is None
    assert answer("String bending là gì? Em muốn học Python.") is None
    assert answer("bend guitar bằng Python") is None


def test_b03_reply_contract_without_provider_or_database():
    from datetime import datetime, timezone
    from types import SimpleNamespace

    from app.contracts.ai import ChatReplyOut
    from app.services import ai_tutor_service as tutor

    class UnusedProvider:
        def generate(self, *_args, **_kwargs):
            raise AssertionError("B03 should not call the provider")

    for provider in (None, UnusedProvider()):
        draft, _ = tutor.answer_question(
            None, None, "Trên tab guitar, ký hiệu bend bảo em làm gì?", [], None,
            provider, datetime.now(timezone.utc),
        )
        assert draft.flow == "B"
        assert draft.route == "supplemental"
        assert draft.llm_calls == 0
        assert not draft.citations and not draft.claims and not draft.suggested_lesson
        row = SimpleNamespace(
            id=1, content=draft.reply, citations=draft.citations, engine_claims=draft.claims,
            intent=draft.intent, status=draft.status, hint_level=draft.hint_level,
            tool_calls={"flow": draft.flow, "source_label": draft.source_label,
                        "supplemental_source": draft.supplemental_source},
        )
        response = ChatReplyOut.model_validate(tutor.out(row, SimpleNamespace(id="test"), 1))
        assert response.supplemental_source == draft.supplemental_source
        assert not response.verified
        assert not response.citations


def test_b01_b02_b04_sources_and_guardrails():
    b01 = answer("Nhịp 6/8 là gì?")
    assert b01 is not None and "compound duple" in b01.reply and b01.source_url.endswith("/compound-meters/")
    b02 = answer("Thế đảo 1 của hợp âm C trưởng là gì?")
    assert b02 is not None and "E–G–C" in b02.reply and "inversion" in b02.source_url
    b04 = answer("Vì sao quãng năm đúng song song bị tránh trong hòa âm cổ điển?")
    assert b04 is not None and "không phải quy tắc tuyệt đối" in b04.reply
    assert answer("Trong bài L01, nhịp 6/8 là gì?") is None
    assert answer("Nhịp 6/8 là gì? Em muốn học Python.") is None
