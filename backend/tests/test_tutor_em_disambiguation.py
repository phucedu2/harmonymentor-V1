"""Regression checks for the Vietnamese pronoun Em versus E minor; no live services."""

from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from app.ai.tutor.engine_query import engine_answer
from app.ai.tutor.llm import LLMUnavailable
from app.services import ai_tutor_service as tutor


QUESTION = "Nửa cung là gì? Em đếm trên bàn phím piano như thế nào?"


def chords(question, **kwargs):
    return {f["args"]["symbol"]: f["result"] for f in engine_answer(question, **kwargs).facts
            if f["tool"] == "get_chord_tones"}


@pytest.mark.parametrize(("question", "expected"), [
    (QUESTION, {}),
    ("Em dem nua cung the nao?", {}),
    ("Em muốn học Python.", {}),
    ("Em muốn biết Am7 gồm nốt nào?", {"Am7": "A C E G"}),
    ("Em hỏi về hợp âm Em.", {"Em": "E G B"}),
    ("Em gồm những nốt nào?", {"Em": "E G B"}),
    ("Hợp âm Em cần những nốt nào?", {"Em": "E G B"}),
    ("Em7 gồm những nốt nào?", {"Em7": "E G B D"}),
    ("Vòng Em–Am–Dm chơi thế nào?", {"Em": "E G B", "Am": "A C E", "Dm": "D F A"}),
    ("Hợp âm C gồm những nốt nào?", {"C": "C E G"}),
    ("Cmaj7 gồm những nốt nào?", {"Cmaj7": "C E G B"}),
    ("G7 gồm những nốt nào?", {"G7": "G B D F"}),
    ("F#dim gồm những nốt nào?", {"F#dim": "F# A C"}),
])
def test_chord_candidates(question, expected):
    assert chords(question) == expected


def test_pronoun_does_not_override_selected_chord():
    assert chords("Em muốn hỏi hợp âm này gồm những nốt nào?", context={"selected_chord": "Dm"}) == {"Dm": "D F A"}


class FailingProvider:
    def generate(self, *_args):
        raise LLMUnavailable("unavailable")


@pytest.mark.parametrize("provider", [None, FailingProvider()], ids=["offline", "simulated-provider-failure"])
def test_semitone_answer_falls_back_to_correct_lesson(provider, monkeypatch):
    monkeypatch.setattr(tutor, "_llm_rows_today", lambda *_: 0)
    monkeypatch.setattr(tutor, "_weak_skill_names", lambda *_: [])
    draft, _ = tutor.answer_question(None, SimpleNamespace(id="test", goal_text=""), QUESTION, [], None, provider,
                                     datetime.now(timezone.utc))
    assert draft.flow == "A"
    assert draft.fallback_reason == ("unavailable" if provider else "ai_disabled")
    assert [citation["block_id"] for citation in draft.citations] == ["L01-B02"]
    assert "phím sát bên cạnh" in draft.reply
    assert "phím xuất phát được tính là 0" in draft.reply
    assert "E, G, B" not in draft.reply


def test_pronoun_does_not_turn_out_of_scope_into_music():
    draft, _ = tutor.answer_question(None, None, "Em muốn học Python.", [], None, None,
                                     datetime.now(timezone.utc))
    assert draft.flow == "C"
    assert draft.intent == "out_of_scope"
    assert not draft.citations
    assert not draft.claims
