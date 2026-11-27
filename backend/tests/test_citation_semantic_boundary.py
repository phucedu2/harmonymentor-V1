"""Offline, synthetic tests for the citation/semantic-check boundary."""
import json

from app.ai.tutor.llm import FakeProvider
from app.services.ai_tutor_service import _chat_behavior_issue, _llm_round


def make_answer(text, citations):
    return json.dumps({"reply": text, "citations": citations, "engine_claims": [],
                       "hint_level": 0, "suggested_actions": [], "intent": "concept"}, ensure_ascii=False)


def check(answer):
    return _chat_behavior_issue(answer, "Bài học của mình nói gì về fugue?",
                                has_lesson_hits=False, has_engine_facts=False)


def test_fabricated_citation_cannot_satisfy_grounding_on_retry():
    fake_source = {"lesson_id": "L99", "block_id": "L99-B99", "title": "Bịa"}
    provider = FakeProvider([make_answer("Bài học nói fugue là nhạc múa.", [fake_source])] * 2)
    answer, _, calls, reason = _llm_round(provider, lambda correction: "synthetic", {}, {}, check)
    assert answer is None and len(calls) == 2 and reason == "lesson_ungrounded"


def test_honest_abstention_with_bad_citation_does_not_invent_source():
    fake_source = {"lesson_id": "L99", "block_id": "L99-B99", "title": "Bịa"}
    provider = FakeProvider([make_answer("Mình chưa có học liệu để trả lời.", [fake_source])] * 2)
    answer, _, calls, reason = _llm_round(provider, lambda correction: "synthetic", {}, {}, check)
    assert answer is not None and answer.citations == [] and len(calls) == 2 and reason is None


def test_allowed_citation_still_satisfies_grounding():
    source = {"lesson_id": "L01", "block_id": "L01-B01", "title": "Đoạn"}
    provider = FakeProvider([make_answer("Bài học nói về fugue.", [source])])
    answer, _, calls, reason = _llm_round(provider, lambda correction: "synthetic", {"L01-B01": object()}, {}, check)
    assert answer is not None and len(answer.citations) == 1 and len(calls) == 1 and reason is None


def test_degree_claim_requires_roman_engine_fact_not_unrelated_chord_fact():
    from app.ai.tutor.schema import parse_answer

    answer = parse_answer(make_answer("Cmaj7 là bậc III trong A thứ tự nhiên.", []))
    assert answer is not None
    unrelated = [{"tool": "get_chord_tones", "args": {"symbol": "Cmaj7"}, "result": "C E G B"}]
    issue = _chat_behavior_issue(answer, "Cmaj7 trong A thứ tự nhiên là bậc mấy?",
                                 has_lesson_hits=False, has_engine_facts=True,
                                 engine_facts=unrelated)
    assert issue is not None and "số La Mã" in issue


def test_degree_claim_accepts_matching_roman_engine_fact():
    from app.ai.tutor.schema import parse_answer

    answer = parse_answer(make_answer("Cmaj7 là bậc IIIM7 trong A thứ tự nhiên.", []))
    assert answer is not None
    matching = [{"tool": "get_roman_numeral", "args": {"key": "A", "chord": "Cmaj7", "mode": "natural_minor"},
                 "result": "IIIM7"}]
    assert _chat_behavior_issue(answer, "Cmaj7 trong A thứ tự nhiên là bậc mấy?",
                                has_lesson_hits=False, has_engine_facts=True,
                                engine_facts=matching) is None


def test_incorrect_answer_is_rejected_even_with_correct_engine_fact():
    from app.ai.tutor.schema import parse_answer
    answer = parse_answer(make_answer("G7 là bậc ii7.", []))
    facts = [{"tool": "get_roman_numeral", "args": {"key": "C", "chord": "G7"}, "result": "V7"}]
    assert _chat_behavior_issue(answer, "G7 trong C trưởng là bậc mấy?",
                                has_lesson_hits=False, has_engine_facts=True,
                                engine_facts=facts) is not None


def test_unrelated_roman_fact_and_bare_answer_are_rejected():
    from app.ai.tutor.schema import parse_answer

    answer = parse_answer(make_answer("III", []))
    wrong = [{"tool": "get_roman_numeral", "args": {"key": "C", "chord": "Dm7"}, "result": "ii7"}]
    assert _chat_behavior_issue(answer, "Cmaj7 trong A thứ tự nhiên là bậc mấy?",
                                has_lesson_hits=False, has_engine_facts=True,
                                engine_facts=wrong) is not None


def test_unfounded_absence_or_added_assertion_cannot_pass_retry():
    for text in ("Bài học chưa có nội dung về fugue.",
                 "Mình chưa có học liệu để trả lời. Fugue là nhạc múa."):
        provider = FakeProvider([make_answer(text, [])] * 2)
        answer, _, calls, reason = _llm_round(provider, lambda correction: "synthetic", {}, {}, check)
        assert answer is None and len(calls) == 2 and reason == "lesson_ungrounded"


def test_conflicting_multiple_degrees_rejected_with_correct_fact():
    from app.ai.tutor.schema import parse_answer
    fact = {"tool": "get_roman_numeral", "args": {"key": "C", "chord": "G7"}, "result": "V7"}
    response = parse_answer(make_answer("G7 là bậc V7 nhưng cũng là bậc ii7.", []))
    assert _chat_behavior_issue(response, "G7 trong C trưởng là bậc mấy?",
                                has_lesson_hits=False, has_engine_facts=True, engine_facts=[fact])


def test_valid_arabic_ordinal_alongside_exact_engine_result_is_accepted():
    from app.ai.tutor.schema import parse_answer
    fact = {"tool": "get_roman_numeral", "args": {"key": "C", "chord": "G7"}, "result": "V7"}
    response = parse_answer(make_answer("G7 là bậc 5, tức V7.", []))
    assert _chat_behavior_issue(response, "G7 trong C trưởng là bậc mấy?",
                                has_lesson_hits=False, has_engine_facts=True, engine_facts=[fact]) is None


def test_wrong_arabic_ordinal_alongside_correct_roman_is_rejected():
    from app.ai.tutor.schema import parse_answer
    fact = {"tool": "get_roman_numeral", "args": {"key": "C", "chord": "G7"}, "result": "V7"}
    response = parse_answer(make_answer("G7 là bậc 2, tức V7.", []))
    assert _chat_behavior_issue(response, "G7 trong C trưởng là bậc mấy?",
                                has_lesson_hits=False, has_engine_facts=True, engine_facts=[fact]) is not None


def test_bad_degree_response_retried_then_rejected():
    question = "Cmaj7 trong A thứ tự nhiên là bậc mấy?"
    facts = [{"tool": "get_chord_tones", "args": {"symbol": "Cmaj7"}, "result": "C E G B"}]
    provider = FakeProvider([make_answer("III", [])] * 2)
    def validate(answer):
        return _chat_behavior_issue(answer, question, has_lesson_hits=False,
                                    has_engine_facts=True, engine_facts=facts)
    answer, _, calls, reason = _llm_round(provider, lambda correction: "synthetic", {}, {}, validate)
    assert answer is None and len(calls) == 2 and reason == "engine_fact_missing"


# --- Câu hỏi khái niệm về số La Mã không bị ép phải có số La Mã cụ thể từ Engine; nhãn lý do được tách ---------------------

import pytest
from app.services.ai_tutor_service import BehaviorIssue, _is_concept_roman_question

CONCEPT_REPLY = "Số La Mã cho biết bậc của hợp âm trong giọng. Với hợp âm bảy, ghi thêm số 7 sau số La Mã, ví dụ V7 hay ii7."


def _concept_answer(text=CONCEPT_REPLY):
    return make_answer(text, [])


def _issue(question, reply=CONCEPT_REPLY, *, facts=None, context=None):
    from app.ai.tutor.schema import parse_answer
    answer = parse_answer(_concept_answer(reply))
    return _chat_behavior_issue(answer, question, has_lesson_hits=True, has_engine_facts=bool(facts),
                                engine_facts=facts or [], context=context)


@pytest.mark.parametrize("question", [
    "Đề cho một hợp âm bảy, em nên ghi số La Mã thế nào?",
    "Số La Mã là gì?",
    "Số La Mã dùng để làm gì?",
])
def test_concept_roman_question_is_not_forced_to_have_engine_fact(question):
    assert _is_concept_roman_question(question, None)
    assert _issue(question) is None


@pytest.mark.parametrize("question,context", [
    ("G7 trong C trưởng là bậc mấy?", None),
    ("Bm là bậc mấy?", None),
    ("Hợp âm này là bậc mấy?", None),
    ("Hợp âm này là bậc mấy?", {"selected_root": "G", "selected_chord": "G7", "selected_key": "C", "mode": "major"}),
])
def test_specific_degree_question_still_fails_closed_without_engine_fact(question, context):
    assert not _is_concept_roman_question(question, context)
    issue = _issue(question, "Đó là bậc V.", context=context)
    assert isinstance(issue, BehaviorIssue) and issue.code == "engine_fact_missing"


def test_specific_degree_wrong_answer_gets_engine_fact_mismatch_code():
    facts = [{"tool": "get_roman_numeral", "args": {"key": "C", "chord": "G7"}, "result": "V7"}]
    issue = _issue("G7 trong C trưởng là bậc mấy?", "Đó là bậc IV.", facts=facts)
    assert isinstance(issue, BehaviorIssue) and issue.code == "engine_fact_mismatch"


def test_llm_round_reports_specific_reason_not_answer_leak():
    from app.services.ai_tutor_service import _llm_round
    q = "Cmaj7 trong A thứ tự nhiên là bậc mấy?"
    provider = FakeProvider([make_answer("III", [])] * 2)
    check_fn = lambda a: _chat_behavior_issue(a, q, has_lesson_hits=False, has_engine_facts=False)
    answer, _, calls, reason = _llm_round(provider, lambda c: "synthetic", {}, {}, check_fn)
    assert answer is None and len(calls) == 2 and reason == "engine_fact_missing" and reason != "answer_leak"


def test_plain_string_issue_keeps_answer_leak_label():
    from app.services.ai_tutor_service import _llm_round
    provider = FakeProvider([make_answer("Đáp án đúng là C E G B.", [])] * 2)
    answer, _, calls, reason = _llm_round(provider, lambda c: "synthetic", {}, {}, lambda a: "Không được nêu đáp án.")
    assert answer is None and reason == "answer_leak"