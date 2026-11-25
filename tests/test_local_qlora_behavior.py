"""CPU-only regression checks; no model, network, production DB or training."""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.ai.tutor.local_qlora import validate_output


def prompt(question, chunks="[]", facts="[]"):
    return ('MODE: chat\n<<<HM_DATA kind="LESSON_CHUNKS">>>\n' + chunks
            + '\n<<<HM_END>>>\n<<<HM_DATA kind="ENGINE_FACTS">>>\n' + facts
            + '\n<<<HM_END>>>\n<<<HM_DATA kind="QUESTION">>>\n' + question + '\n<<<HM_END>>>')


def answer(reply, intent="concept", citations=None):
    return json.dumps(dict(reply=reply, citations=citations or [], engine_claims=[],
                           hint_level=0, suggested_actions=[], intent=intent), ensure_ascii=False)


@pytest.mark.parametrize("question", [
    "Bài học nói gì về hòa âm tứ độ?",
    "Hãy giải thích cấu trúc fugue theo bài học của mình.",
    "Theo bài học, đảo hợp âm bảy là gì?",
])
def test_missing_lesson_rejects_assertion(question):
    _, issues = validate_output(answer("Đó là nội dung của bài học."), prompt(question))
    assert "ungrounded_lesson_answer" in issues


def test_missing_lesson_allows_abstention():
    _, issues = validate_output(answer("Mình chưa có học liệu. Bạn gửi trích đoạn nhé."),
                                prompt("Bài học nói gì về fugue?"))
    assert "ungrounded_lesson_answer" not in issues


@pytest.mark.parametrize("reply", [
    "Bài học chưa có nội dung về fugue.",
    "Mình chưa có học liệu. Fugue là nhạc múa.",
    "Không có bài nào nói về fugue.",
    "Mình chưa thể xác minh, nhưng bài học nói fugue là nhạc múa.",
])
def test_missing_lesson_rejects_false_absence_or_abstention_plus_claim(reply):
    _, issues = validate_output(answer(reply), prompt("Bài học của mình nói gì về fugue?"))
    assert "ungrounded_lesson_answer" in issues


def test_conflicting_multiple_degree_claims_rejected():
    fact = {"tool": "get_roman_numeral", "args": {"key": "C", "chord": "G7"}, "result": "V7"}
    output = json.loads(answer("G7 trong C trưởng là bậc V7, nhưng cũng là bậc ii7."))
    output["engine_claims"] = [fact]
    _, issues = validate_output(json.dumps(output, ensure_ascii=False),
                                prompt("G7 trong C trưởng là bậc mấy?", facts=json.dumps([fact])))
    assert "degree_answer_mismatch" in issues


def test_citation_can_satisfy_source_requirement():
    source = dict(lesson_id="L1", block_id="B1", title="Hòa âm")
    chunks = json.dumps([{**source, "text": "Một đoạn."}], ensure_ascii=False)
    _, issues = validate_output(answer("Một đoạn.", citations=[source]),
                                prompt("Bài học nói gì?", chunks))
    assert "ungrounded_lesson_answer" not in issues


def test_missing_mode_requires_actionable_clarification():
    question = "Am7 trong E thứ là bậc mấy?"
    _, issues = validate_output(answer("Chưa có dữ kiện để xác định bậc."), prompt(question))
    assert "missing_context_clarification" in issues
    _, issues = validate_output(answer("Bạn muốn xét giọng thứ tự nhiên hay thứ hòa thanh?"), prompt(question))
    assert "missing_context_clarification" not in issues


def test_missing_key_rejects_unsupported_degree():
    _, issues = validate_output(answer("Hợp âm Dm là bậc 3 của giọng D trưởng."),
                                prompt("Hợp âm Dm là bậc mấy?"))
    assert "context_unsubstantiated_degree" in issues


@pytest.mark.parametrize("question", [
    "Bạn chẩn đoán giúp em triệu chứng đau đầu nhé.",
    "Bạn tư vấn giúp mình chọn bảo hiểm nhà được không?",
    "ban tu van bao hiem xe may duoc khong?",
])
def test_scope_intent_rejects_concept(question):
    _, issues = validate_output(answer("Hãy cho mình biết giọng."), prompt(question))
    assert "scope_intent" in issues


def test_music_thuoc_not_confused_with_medicine():
    _, issues = validate_output(answer("C thuộc âm giai C trưởng."),
                                prompt("Nốt C thuộc âm giai nào?"))
    assert "scope_intent" not in issues


def test_out_of_scope_refusal_passes_scope_check():
    _, issues = validate_output(answer("Mình không hỗ trợ chẩn đoán y tế.", "out_of_scope"),
                                prompt("Bạn chẩn đoán giúp em triệu chứng đau đầu nhé."))
    assert "scope_intent" not in issues
