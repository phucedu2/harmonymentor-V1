"""Offline fallback regression; no application startup, database or network."""
from datetime import datetime, timezone
from types import SimpleNamespace as NS
import pytest
from app.services import ai_tutor_service as ts
from app.ai.tutor.engine_query import engine_answer

CTX = {"selected_root":"A", "selected_chord":"Am", "selected_key":"A", "mode":"natural_minor"}

def response(text, claims):
    msg = NS(id=1, content=text, engine_claims=claims, tool_calls={}, citations=[], intent="concept", hint_level=0, status="fallback")
    return ts.out(msg, NS(id="test"), 30)

@pytest.mark.parametrize("question,expected", [("Am trong C trưởng là bậc mấy?", "Trong giọng C trưởng, Am là vi."), ("Hợp âm này là bậc mấy?", "Trong giọng A thứ tự nhiên, Am là i.")])
def test_actual_routed_offline_service(question, expected):
    # Real classifier, retrieval, engine, fallback and serialization, no storage.
    draft, meta = ts.answer_question(None, NS(id="test"), question, [], None, None, datetime.now(timezone.utc), context=CTX)
    assert expected in draft.reply
    assert "F phải được nâng" not in draft.reply
    result = response(draft.reply, draft.claims)
    assert result["verified"]
    assert "dữ kiện nhạc lý hiển thị" in result["verified_label"]

def test_offline_ignores_unrelated_excerpt_when_engine_answers():
    facts = engine_answer("Am trong C trưởng là bậc mấy?", context=CTX).facts
    hit = NS(chunk=NS(text="F phải được nâng thành F#", lesson_id="L02", block_id="x", title="Âm giai"))
    draft = ts.offline_answer([hit], facts, {}, "ai_disabled")
    assert "Am là vi" in draft.reply and "F#" not in draft.reply
    assert draft.citations == []
    assert all(c["origin"] == "scanned" for c in draft.claims)

@pytest.mark.parametrize("question", ["Hợp âm C7 gồm nốt nào?", "Âm giai D trưởng", "Từ C lên E là quãng gì?", "Am trong C trưởng là bậc mấy?"])
def test_all_supported_fact_types_rendered(question):
    facts = engine_answer(question).facts
    assert facts
    draft = ts.offline_answer([], facts, {}, "timeout")
    assert ts._fact_lines(facts) in draft.reply
    assert draft.claims

@pytest.mark.parametrize("text,status,has_claims,expected", [
    ("F phải được nâng thành F# để giữ mẫu khoảng cách major scale.", "verified", True, False),
    ("Trong giọng C trưởng, Am là vi.", "verified", True, True),
    ("Trong giọng C trưởng, Am là I.", "verified", True, False),
    ("Trong giọng C trưởng, Am là vi.", "contradicted", True, False),
    ("Trong giọng C trưởng, Am là vi.", "unsupported", True, False),
    ("Trong giọng C trưởng, Am là vi.", "verified", False, False),
])
def test_legacy_metadata_does_not_verify_missing_or_wrong_reply(text,status,has_claims,expected):
    claims = [{"tool":"get_roman_numeral", "args":{"key":"C", "chord":"Am"}, "claimed":"vi", "engine":"vi", "status":status}] if has_claims else []
    out = response(text, claims)
    assert out["verified"] is expected
    assert (out["verified_label"] is not None) is expected
