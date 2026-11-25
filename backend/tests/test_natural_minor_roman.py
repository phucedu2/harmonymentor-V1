"""Natural-minor Roman contract: pure engine/chatbot tests, no database or network."""
import pytest
from app.music_engine.roman import roman_numeral, diatonic_chords
from app.music_engine.scale import build_scale
from app.music_engine.chord import chord_tones
from app.music_engine.grading import grade_roman_numeral
from app.music_engine.errors import NotDiatonic, NotSupportedInMvp
from app.music_engine.tools import TOOL_DECLARATIONS
from app.ai.tutor.engine_query import engine_answer, fact_text
from app.ai.tutor.guardrail import run_tool, check_roman, check_declared, scan_reply
from app.ai.tutor.schema import Claim, LLM_SCHEMA

ROOTS = ["C", "Db", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
PATTERNS = {
    ("major", False): ["I", "ii", "iii", "IV", "V", "vi", "vii°"],
    ("major", True): ["IM7", "ii7", "iii7", "IVM7", "V7", "vi7", "viiø7"],
    ("natural_minor", False): ["i", "ii°", "III", "iv", "v", "VI", "VII"],
    ("natural_minor", True): ["i7", "iiø7", "IIIM7", "iv7", "v7", "VIM7", "VII7"],
}

@pytest.mark.parametrize("root", ROOTS)
@pytest.mark.parametrize("mode,sevenths", PATTERNS)
def test_24_keys_all_degrees(root, mode, sevenths):
    rows = diatonic_chords(root, sevenths=sevenths, mode=mode)
    assert [x.numeral for x in rows] == PATTERNS[mode, sevenths]
    scale = [str(x) for x in build_scale(root, mode)]
    for degree, row in enumerate(rows):
        expected = [scale[(degree + 2*k) % 7] for k in range(4 if sevenths else 3)]
        assert [str(x) for x in chord_tones(row.chord.symbol)] == expected
        assert roman_numeral(root, row.chord.symbol, mode=mode).numeral == row.numeral
        assert row.mode == mode

@pytest.mark.parametrize("answer", ["IIImaj7", "IIIM7"])
def test_grader_aliases(answer):
    assert grade_roman_numeral("A", "Cmaj7", answer, mode="natural_minor")["correct"]
    assert not grade_roman_numeral("A", "Cmaj7", "III7", mode="natural_minor")["correct"]

@pytest.mark.parametrize("mode", ["minor", "harmonic_minor", "melodic_minor", "dorian"])
def test_unsupported_modes_are_not_major(mode):
    with pytest.raises(NotSupportedInMvp):
        roman_numeral("A", "Am", mode=mode)

def test_outside_natural_minor_not_universally_wrong():
    with pytest.raises(NotDiatonic, match="thứ tự nhiên"):
        roman_numeral("A", "E7", mode="natural_minor")
    assert check_roman("A", "E7", "V7", "natural_minor").status == "unsupported"

def test_accidental_spelling():
    rows = diatonic_chords("Eb", sevenths=True, mode="natural_minor")
    assert [str(x) for x in chord_tones(rows[1].chord.symbol)] == ["F", "Ab", "Cb", "Eb"]

def test_tool_and_schema_preserve_mode():
    value, raw = run_tool("get_roman_numeral", {"key": "A", "chord": "Am", "mode": "natural_minor"})
    assert value == "i" and raw["mode"] == "natural_minor"
    declaration = next(x for x in TOOL_DECLARATIONS if x["name"] == "get_roman_numeral")
    assert "natural_minor" in declaration["parameters"]["properties"]["mode"]["enum"]
    props = LLM_SCHEMA["properties"]["engine_claims"]["items"]["properties"]["args"]["properties"]
    assert "mode" in props

def test_declared_mode_and_major_regression():
    c = Claim(tool="get_roman_numeral", args={"key":"A", "chord":"Cmaj7", "mode":"natural_minor"}, result="IIImaj7")
    result = check_declared([c])[0]
    assert result.status == "verified" and result.args["mode"] == "natural_minor"
    assert check_roman("A", "Am", "I", "natural_minor").status == "contradicted"
    assert check_roman("C", "G7", "V7").status == "verified"
    assert check_roman("A", "Cmaj7", "IIImaj7", "major").status != "verified"

@pytest.mark.parametrize("question,chord,numeral", [
    ("Am trong A thứ tự nhiên là bậc mấy?", "Am", "i"),
    ("Cmaj7 trong giọng La thứ tự nhiên là bậc mấy?", "Cmaj7", "IIIM7"),
    ("iiø7 trong A thứ tự nhiên gồm nốt nào?", "Bm7b5", "iiø7"),
    ("IIImaj7 trong A natural minor gồm nốt nào?", "Cmaj7", "IIIM7"),
    ("Dm trong Re thu tu nhien la bac may?", "Dm", "i"),
])
def test_questions(question, chord, numeral):
    out = engine_answer(question)
    facts = [f for f in out.facts if f["tool"] == "get_roman_numeral"]
    assert len(facts) == 1, out
    assert facts[0]["args"]["chord"] == chord
    assert facts[0]["args"]["mode"] == "natural_minor"
    assert facts[0]["result"] == numeral
    assert "thứ tự nhiên" in fact_text(facts[0])

@pytest.mark.parametrize("kind", ["thứ", "minor", "thứ hòa âm", "thứ giai điệu"])
def test_questions_do_not_silently_use_major(kind):
    out = engine_answer(f"Am trong giọng A {kind} là bậc mấy?")
    assert not any(f["tool"] == "get_roman_numeral" for f in out.facts)
    assert out.unknown

@pytest.mark.parametrize("reply,status", [
    ("i trong A thứ tự nhiên là Am", "verified"),
    ("Cmaj7 là IIImaj7 trong A thứ tự nhiên", "verified"),
    ("Am là I trong A thứ tự nhiên", "contradicted"),
    ("Am là i trong A thứ", "unsupported"),
    ("E7 là V7 trong A thứ tự nhiên", "unsupported"),
])
def test_scanned_claims(reply, status):
    rows = [x for x in scan_reply(reply) if x.tool == "get_roman_numeral"]
    assert len(rows) == 1
    assert rows[0].status == status


@pytest.mark.parametrize("reply,status", [
    ("Trong giọng La thứ tự nhiên, Am là i.", "verified"),
    ("Trong giọng A thứ tự nhiên, Am là I.", "contradicted"),
    ("iiø7 trong La thứ tự nhiên là Bm7b5.", "verified"),
    ("ii7 trong A thứ là Bm7b5", "unsupported"),
    ("V7 trong G trưởng là D7.", "verified"),
    ("V7 trong G trưởng là G7.", "contradicted"),
    ("Cmaj7 là Imaj7 trong giọng C trưởng", "verified"),
    ("Am là i trong A thứ hòa âm", "unsupported"),
])
def test_additional_scanned_claims(reply, status):
    rows = [x for x in scan_reply(reply) if x.tool == "get_roman_numeral"]
    assert len(rows) == 1 and rows[0].status == status


def test_fact_text_round_trip():
    for question in ["IIImaj7 trong A thứ tự nhiên gồm nốt nào?", "V7 trong G trưởng gồm nốt nào?"]:
        fact = next(f for f in engine_answer(question).facts if f["tool"] == "get_roman_numeral")
        rows = [x for x in scan_reply(fact_text(fact)) if x.tool == "get_roman_numeral"]
        assert len(rows) == 1 and rows[0].status == "verified"


def test_engine_api_functions_no_application_or_database():
    # Import only this pure router, never app.main or DB services.
    from app.api.engine import RomanIn, get_roman, get_diatonic, grade_roman_numeral as endpoint
    from pydantic import ValidationError
    assert get_roman("A", "Am", mode="natural_minor")["numeral"] == "i"
    assert get_roman("C", "G7")["numeral"] == "V7"
    assert get_diatonic("A", mode="natural_minor")[1]["numeral"] == "ii°"
    assert endpoint(RomanIn(key="A", chord="Cmaj7", answer="IIImaj7", mode="natural_minor"))["correct"]
    with pytest.raises(ValidationError):
        RomanIn(key="A", chord="Am", answer="i", mode="minor")


def test_outside_scale_question_keeps_scope():
    out = engine_answer("E7 trong A thứ tự nhiên là bậc mấy?")
    assert not any(f["tool"] == "get_roman_numeral" for f in out.facts)
    assert any("không đồng nghĩa sai nhạc lý" in text for text in out.unknown)


@pytest.mark.parametrize("root", ROOTS)
@pytest.mark.parametrize("sevenths", [False, True])
def test_minor_chord_spelling_against_music21(root, sevenths):
    music21 = pytest.importorskip("music21")
    scale = music21.scale.MinorScale(root.replace("b", "-")).getPitches()[:7]
    for degree, row in enumerate(diatonic_chords(root, sevenths=sevenths, mode="natural_minor")):
        expected = [scale[(degree + 2*k) % 7].name.replace("-", "b")
                    for k in range(4 if sevenths else 3)]
        assert [str(n) for n in row.chord.notes] == expected
