"""Câu hỏi nối tiếp trong cùng phiên drawer (28/11, phương án a). Không gọi model thật."""
from types import SimpleNamespace

import pytest

from app.ai.tutor.engine_query import engine_answer
from app.ai.tutor.followup import chord_from_turns, is_followup

GM7 = [("user", "Gm7 gồm những nốt nào?"),
       ("assistant", "Gm7 là G–Bb–D–F. Đây là minor triad + minor seventh. Trong Gm7, Bb là 3rd, F là b7.")]


@pytest.mark.parametrize("text,expected", [
    ("Vậy nó là bậc mấy trong F major?", True),
    ("Hợp âm đó gồm nốt nào?", True),
    ("Nó có phải hợp âm thứ không?", True),
    ("Gm7 gồm những nốt nào?", False),
    ("Hợp âm này là bậc mấy?", False),   # "này" = hợp âm chọn trên giao diện
    ("Nói thêm về quãng ba", False),      # "nói" không phải "nó"
])
def test_is_followup(text, expected):
    assert is_followup(text) is expected


def test_chord_from_previous_question():
    assert chord_from_turns(GM7) == "Gm7"


def test_chord_from_assistant_when_question_has_none():
    turns = [("user", "Cho mình một ví dụ hợp âm bảy"), ("assistant", "Ví dụ G7 gồm G, B, D, F.")]
    assert chord_from_turns(turns) == "G7"


@pytest.mark.parametrize("turns", [
    [],
    [("user", "Cmaj7 khác C7 chỗ nào?"), ("assistant", "Cmaj7 có B, C7 có Bb.")],  # hai hợp âm: không đoán
    [("user", "Quãng ba là gì?"), ("assistant", "Quãng ba là khoảng cách giữa hai nốt.")],
])
def test_no_single_chord_returns_none(turns):
    assert chord_from_turns(turns) is None


def test_latest_turn_wins():
    turns = [*GM7, ("user", "Còn Am7 thì sao?"), ("assistant", "Am7 gồm A, C, E, G.")]
    assert chord_from_turns(turns) == "Am7"


def test_engine_answers_degree_with_resolved_chord():
    out = engine_answer("Vậy nó là bậc mấy trong F major?", context={"selected_chord": "Gm7"})
    romans = [(f["args"]["key"], f["args"]["chord"], f["result"]) for f in out.facts if f["tool"] == "get_roman_numeral"]
    assert romans == [("F", "Gm7", "ii7")]
    assert out.context_note is None


def _run_handle_message(monkeypatch, text, turns, context=None):
    from app.services import ai_tutor_service as ts
    captured = {}
    monkeypatch.setattr(ts, "get_session", lambda *a, **k: SimpleNamespace(id="s"))
    monkeypatch.setattr(ts, "recent_turns", lambda *a, **k: list(turns))
    def answer(*args, **kwargs):
        captured.update(turns=args[3], context=kwargs["context"])
        return SimpleNamespace(suggested_actions=[]), {}
    monkeypatch.setattr(ts, "answer_question", answer)
    monkeypatch.setattr(ts, "_save", lambda *a, **k: None)
    monkeypatch.setattr(ts, "out", lambda *a: {})
    monkeypatch.setattr(ts, "quota_remaining", lambda *a: 5)
    rows = []
    def add(row): row.id = 1; rows.append(row)
    db = SimpleNamespace(add=add, flush=lambda: None)
    ts.handle_message(db, SimpleNamespace(id="u"), text, session_id="s", context=context)
    return captured, rows[0]


def test_followup_gets_history_and_resolved_chord(monkeypatch):
    captured, user_msg = _run_handle_message(monkeypatch, "Vậy nó là bậc mấy trong F major?", GM7)
    assert captured["context"].get("selected_chord") == "Gm7"
    assert captured["turns"] == GM7
    assert user_msg.tool_calls["resolved_chord"] == "Gm7"
    assert user_msg.content == "Vậy nó là bậc mấy trong F major?"  # không sửa câu của người học


def test_independent_question_gets_no_history(monkeypatch):
    captured, user_msg = _run_handle_message(monkeypatch, "Am7 gồm những nốt nào?", GM7)
    assert captured["turns"] == [] and "selected_chord" not in captured["context"]
    assert "resolved_chord" not in user_msg.tool_calls


def test_ui_selected_chord_is_not_overridden(monkeypatch):
    ctx = {"selected_chord": "C7"}
    captured, _ = _run_handle_message(monkeypatch, "Vậy nó là bậc mấy trong F major?", GM7, context=ctx)
    assert captured["context"]["selected_chord"] == "C7"
