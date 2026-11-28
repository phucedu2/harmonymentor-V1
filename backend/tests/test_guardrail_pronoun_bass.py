"""Bộ kiểm hiểu "Nó / hợp âm này" và nốt bass của hợp âm có dấu "/" (28/11)."""

import pytest

from app.ai.tutor.engine_query import engine_answer, fact_text
from app.ai.tutor.guardrail import check_answer, scan_reply


def _st(reply: str) -> list[tuple[str, str]]:
    return [(c.claimed, c.status) for c in scan_reply(reply)]


# --- "Nó / hợp âm này" -------------------------------------------------------------------------

def test_real_gm7_pronoun_reply_is_contradicted():
    # Câu trả lời thật của model M6 ngày 28/11, lọt qua bộ kiểm trước bản sửa.
    reply = ("Gm7 là hợp âm thứ ba, không phải thứ ba trong giọng. "
             "Nó là hợp âm thứ ba trong giọng C major, nên mình sẽ giải thích theo giọng C major.")
    claims = scan_reply(reply)
    assert [(c.args.get("chord"), c.claimed, c.status) for c in claims] == [("Gm7", "bậc 3", "contradicted")]
    assert check_answer(reply, []).contradicted


@pytest.mark.parametrize("reply", [
    "Gm7 gồm G, Bb, D, F. Nó là hợp âm bậc 2 trong giọng F trưởng.",
    "Gm7 gồm G, Bb, D, F. Hợp âm này là ii7 trong giọng F major.",
    "Hợp âm Gm7 rất hay gặp. Hợp âm đó là hợp âm thứ hai trong giọng F.",
])
def test_pronoun_correct_claims_verified(reply):
    assert all(s == "verified" for _, s in _st(reply)) and _st(reply)


def test_pronoun_wrong_roman_contradicted():
    assert ("V7", "contradicted") in _st("Gm7 gồm G, Bb, D, F. Nó là V7 trong giọng F major.")


@pytest.mark.parametrize("reply", [
    "Gm7 khác Am7. Nó là hợp âm bậc 2 trong giọng F.",   # hai hợp âm: không đoán "Nó" là cái nào
    "Nó là hợp âm bậc 2 trong giọng F.",                  # không có hợp âm nào trước đó
])
def test_pronoun_unclear_is_unsupported_not_verified(reply):
    claims = scan_reply(reply)
    assert claims and all(c.status == "unsupported" for c in claims)
    assert not check_answer(reply, []).all_verified


def test_pronoun_without_degree_number_not_extracted():
    assert _st("Gm7 gồm G, Bb, D, F. Nó là hợp âm thứ trong giọng F.") == [("G Bb D F", "verified")]


# --- C/E: nốt bass ------------------------------------------------------------------------------

def test_slash_chord_notes_no_longer_false_contradiction():
    # Trước bản sửa: chữ E sau "/" bị hiểu là hợp âm E -> "contradicted" nhầm.
    assert _st("C/E gồm các nốt C, E, G, với E ở bass.") == [("C E G", "verified"), ("bass E", "verified")]


@pytest.mark.parametrize("reply,claimed", [
    ("C/E là hợp âm C với nốt bass là C.", "bass C"),
    ("C/E gồm C, E, G; nốt thấp nhất là G.", "bass G"),
])
def test_wrong_bass_contradicted(reply, claimed):
    assert (claimed, "contradicted") in _st(reply)
    assert check_answer(reply, []).contradicted


def test_other_slash_chord_bass_verified():
    assert ("bass B", "verified") in _st("G7/B: nốt trầm là B.")


@pytest.mark.parametrize("q", ["Slash chord C/E là gì?", "Hợp âm C/E gồm những nốt nào?"])
def test_engine_fact_for_slash_chord_has_bass(q):
    facts = engine_answer(q).facts
    assert [(f["args"]["symbol"], f["result"], f.get("bass")) for f in facts] == [("C/E", "C E G", "E")]
    text = fact_text(facts[0])
    assert "nốt bass là E" in text
    # Câu viết sẵn từ Engine phải tự qua bộ kiểm.
    assert all(c.status == "verified" for c in scan_reply(text)) and len(scan_reply(text)) == 2


def test_plain_chords_unchanged():
    facts = engine_answer("Cmaj7 khác C7 chỗ nào?").facts
    assert [(f["args"]["symbol"], "bass" in f) for f in facts] == [("Cmaj7", False), ("C7", False)]
