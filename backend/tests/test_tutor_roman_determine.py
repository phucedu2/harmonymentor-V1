"""Câu hỏi "là bậc mấy": thiếu giọng/hợp âm thì hỏi lại, đủ dữ kiện thì tra Music Engine (không đoán).

Bao gồm các ca B1-B3 của buổi demo Mốc 8 (27/11/2026) và kiểm tra giá trị số La Mã mới.
"""
import pytest

from app.ai.tutor.engine_query import engine_answer

ASK_KEY = "Bạn chọn giọng và loại giọng để mình xác định bậc của hợp âm nhé."


def _tools(ans):
    return [f["tool"] for f in ans.facts]


def _roman(ans):
    return [f["result"] for f in ans.facts if f["tool"] == "get_roman_numeral"]


# --- B1, B2, B3: thiếu giọng thì hỏi lại ---------------------------------------------------------------------------

def test_b1_chord_referent_without_context_asks_for_key():
    ans = engine_answer("Hợp âm này là bậc mấy?")
    assert ans.context_note and ans.context_note.startswith(ASK_KEY)
    assert not _roman(ans)


def test_b2_named_chord_without_key_asks_for_key():
    ans = engine_answer("Bm là bậc mấy?")
    assert ans.context_note and ans.context_note.startswith(ASK_KEY)
    assert not _roman(ans)  # không được đoán bậc khi chưa có giọng


def test_b3_em_is_pronoun_not_e_minor():
    ans = engine_answer("Em chỉ thấy ô nốt gốc B đang sáng. Xác định bậc hợp âm được chưa?",
                        context={"selected_root": "B"})
    assert ans.context_note and ans.context_note.startswith(ASK_KEY)
    assert not any(f["args"].get("symbol") == "Em" for f in ans.facts), "đại từ 'Em' bị nhận thành hợp âm Mi thứ"


@pytest.mark.parametrize("tail", ["chỉ", "thấy", "biết", "hiểu", "vẫn", "mới", "vừa", "đã"])
def test_em_pronoun_tails_are_not_chords(tail):
    ans = engine_answer(f"Em {tail} G7 là bậc mấy trong C trưởng?")
    assert not any(f["args"].get("symbol") == "Em" for f in ans.facts)


def test_em_as_explicit_chord_is_still_recognised():
    ans = engine_answer("Em hỏi về hợp âm Em")
    assert any(f["args"].get("symbol") == "Em" for f in ans.facts)


# --- Giá trị số La Mã (kiểm tra C): đối chiếu lý thuyết, không phải chỉ so với đầu ra cũ -----------------------------

@pytest.mark.parametrize("question,expected", [
    ("G7 là bậc mấy trong C trưởng?", "V7"),
    ("Dm7 là bậc mấy trong C trưởng?", "ii7"),
    ("Bm là bậc mấy trong G trưởng?", "iii"),
    ("Em thấy G7 là bậc mấy trong C trưởng?", "V7"),
])
def test_roman_numeral_values_match_theory(question, expected):
    ans = engine_answer(question)
    assert _roman(ans) == [expected], ans.facts
    assert not ans.context_note


@pytest.mark.parametrize("chord,roman", [("G7", "V7"), ("Dm7", "ii7")])
def test_selected_chord_from_ui_context(chord, roman):
    ctx = {"selected_key": "C", "mode": "major", "selected_chord": chord}
    ans = engine_answer("Hợp âm này là bậc mấy?", context=ctx)
    assert _roman(ans) == [roman]


# --- Không kéo câu hỏi khái niệm vào luồng hỏi lại ------------------------------------------------------------------

@pytest.mark.parametrize("question", [
    "Số La Mã là gì?",
    "Đề cho một hợp âm bảy, em nên ghi số La Mã thế nào?",
])
def test_concept_questions_do_not_trigger_ask_for_key(question):
    ans = engine_answer(question)
    assert not ans.context_note
    assert not _roman(ans)


# --- Câu hỏi bậc đảo thứ tự: "X là bậc mấy trong K ...", "Tính bậc của X trong K ..." -----------------------------------

@pytest.mark.parametrize("question,expected", [
    ("Tính bậc của Am trong C trưởng", "vi"),
    ("Tinh bac cua Am trong C truong", "vi"),
    ("Bậc của Am trong C trưởng là gì?", "vi"),
    ("Bậc của hợp âm Dm7 trong C trưởng là gì?", "ii7"),
    ("Fm là bậc mấy trong C thứ tự nhiên?", "iv"),
    ("Am là bậc mấy trong A thứ tự nhiên?", "i"),
])
def test_word_first_roman_questions_return_roman_numeral(question, expected):
    ans = engine_answer(question)
    assert _roman(ans) == [expected], (ans.facts, ans.unknown)
    assert not ans.context_note


@pytest.mark.parametrize("question", [
    "Fm là bậc mấy trong C thứ?",
    "Tính bậc của Fm trong C thứ",
    "Fm là bậc mấy trong C minor?",
])
def test_unspecified_minor_asks_which_minor_not_guess(question):
    ans = engine_answer(question)
    assert not _roman(ans), "không được tự chọn dạng thứ"
    assert ans.unknown, "phải ghi nhận cần làm rõ dạng thứ"


def test_word_first_does_not_duplicate_facts():
    ans = engine_answer("Dm7 là bậc mấy trong C trưởng?")
    assert _roman(ans) == ["ii7"]