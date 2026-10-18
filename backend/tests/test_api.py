from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
P = "/api/v1/engine"


def test_chord_lookup():
    r = client.get(f"{P}/chord/Ebm7b5")
    assert r.status_code == 200
    assert r.json()["notes"] == ["Eb", "Gb", "Bbb", "Db"]


def test_engine_error_is_structured_422():
    r = client.get(f"{P}/chord/Cmaj13")
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "UNKNOWN_QUALITY"


def test_grade_build_chord():
    r = client.post(f"{P}/grade/build-chord", json={"symbol": "G7", "answer": ["G", "B", "D", "F#"]})
    body = r.json()
    assert body["correct"] is False and body["primary_error"] == "SEVENTH_QUALITY"


def test_grade_roman():
    r = client.post(f"{P}/grade/roman-numeral", json={"key": "C", "chord": "Dm7", "answer": "ii7"})
    assert r.json()["correct"] is True


def test_a_minor_key_signature_is_empty():
    r = client.get(f"{P}/key/A", params={"mode": "minor"})
    assert r.json()["accidentals"] == []
