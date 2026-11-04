"""Demo 10/11, nhiệm vụ C: 5 câu vàng Thắng đặt cho AI Tutor (rag_gold.json, mục demo_1011).

Không gọi mạng (FakeProvider). Kiểm: khối trích dẫn có trong kho; claim tham chiếu khớp Music Engine; đáp án
tham chiếu không bị Engine bác; mẫu trả lời sai bị bác và KHÔNG tới tay người học; câu không có claim nào kiểm
được thì không mang nhãn "đã kiểm"; khẳng định quãng trong lời văn ("D–Gb là M3") cũng bị kiểm.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.ai.tutor.guardrail import run_tool, scan_reply
from app.ai.tutor.llm import FakeProvider
from app.ai.tutor.retriever import knowledge_base
from app.api import ai_tutor
from app.content.source_registry import SOURCE_REGISTRY
from app.db.models import User
from app.db.session import SessionLocal
from app.main import app
from tests.auth_helpers import auth

GOLD = json.loads((Path(__file__).resolve().parents[2] / "scripts" / "ai" / "data" / "rag_gold.json")
                  .read_text(encoding="utf-8"))["demo_1011"]["items"]
IDS = [g["id"] for g in GOLD]


def test_five_gold_questions_from_thang():
    assert [g["q"] for g in GOLD] == [
        "C7 khác Cmaj7 ở điểm nào?", "Vì sao D–F# khác D–Gb về tên quãng?", "V7 trong G trưởng gồm những nốt nào?",
        "ii–V–I trong C trưởng là gì?", "Vì sao G–B–D–F# không phải G7?"]


@pytest.mark.parametrize("g", GOLD, ids=IDS)
def test_gold_blocks_sources_and_claims(g):
    assert set(g["blocks"]) <= {c.block_id for c in knowledge_base()}
    assert g["sources"] and {s["source_id"] for s in g["sources"]} <= set(SOURCE_REGISTRY)
    assert g["claims"]
    for c in g["claims"]:
        assert run_tool(c["tool"], c["args"])[0] == c["expect"], (g["id"], c)


@pytest.mark.parametrize("g", GOLD, ids=IDS)
def test_reference_answer_is_not_contradicted_and_has_checked_facts(g):
    checked = scan_reply(g["ref"])
    assert checked and all(c.status == "verified" for c in checked), [(c.args, c.claimed, c.status) for c in checked]


WRONG = [(g["id"], w) for g in GOLD for w in g["wrong_samples"]]


@pytest.mark.parametrize("gid,w", WRONG, ids=[f"{gid}-{i}" for i, (gid, _) in enumerate(WRONG)])
def test_wrong_samples_are_caught_by_engine(gid, w):
    statuses = {c.status for c in scan_reply(w["reply"])}
    if w["expect"] == "contradicted":
        assert "contradicted" in statuses, (gid, w)
    else:  # giới hạn đã biết, ghi để không ai tưởng là đã kiểm
        assert "contradicted" not in statuses, (gid, w)


@pytest.mark.parametrize("text,claimed,status", [
    ("D–F# là M3.", "M3", "verified"),
    ("Từ D lên Gb là quãng 3 trưởng.", "M3", "contradicted"),
    ("A-C = quãng 3 thứ", "m3", "verified"),
    ("D–Gb là d4.", "d4", "verified"),
    ("B–F là P5.", "P5", "contradicted"),
])
def test_interval_statements_in_prose_are_checked(text, claimed, status):
    (c,) = scan_reply(text)
    assert (c.tool, c.claimed, c.status) == ("identify_interval", claimed, status)


@pytest.mark.parametrize("text", ["D–Gb không phải M3.", "D–F#–A–C là D7", "Cmaj7 = C–E–G–B"])
def test_interval_scanner_ignores_negations_and_chord_spellings(text):
    assert not [c for c in scan_reply(text) if c.tool == "identify_interval"]


# --- Qua API /chat/message với FakeProvider ---------------------------------------------------------

@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        app.dependency_overrides[ai_tutor.embedder_dep] = lambda: None
        yield c
        app.dependency_overrides.pop(ai_tutor.embedder_dep, None)
        app.dependency_overrides.pop(ai_tutor.provider_dep, None)


def user() -> str:
    uid = "d1011-" + uuid4().hex[:10]
    with SessionLocal() as db:
        db.add(User(id=uid, display_name="demo", email=f"{uid}@example.test"))
        db.commit()
    return uid


def citing_first(reply: str, claims=None):
    def make(system, prompt):
        part = prompt.split('kind="LESSON_CHUNKS"', 1)[1].split("<<<HM_END>>>")[0]
        b = re.findall(r'"block_id": "([^"]+)"', part)[0]
        return json.dumps({"reply": reply, "citations": [{"lesson_id": b.split("-")[0], "block_id": b, "title": "?"}],
                           "engine_claims": claims or [], "hint_level": 0, "suggested_actions": [],
                           "intent": "concept"}, ensure_ascii=False)
    return make


def ask(client, provider, q):
    app.dependency_overrides[ai_tutor.provider_dep] = lambda: provider
    r = client.post("/api/v1/chat/message", headers=auth(user()), json={"message": q})
    assert r.status_code == 200, r.text
    return r.json()


@pytest.mark.parametrize("g", GOLD, ids=IDS)
def test_reference_answer_shown_with_verified_label_and_citation(client, g):
    claims = [{"tool": c["tool"], "args": c["args"], "result": c["expect"]} for c in g["claims"]]
    body = ask(client, FakeProvider([citing_first(g["ref"], claims)]), g["q"])
    assert body["status"] == "ok" and body["verified"] and body["verified_label"], body
    assert body["citations"] and body["citations"][0]["title"] != "?"
    assert not [c for c in body["engine_claims"] if c["status"] != "verified"]


@pytest.mark.parametrize("gid,w", [x for x in WRONG if x[1]["expect"] == "contradicted"])
def test_wrong_answer_never_reaches_learner(client, gid, w):
    g = next(x for x in GOLD if x["id"] == gid)
    body = ask(client, FakeProvider([citing_first(w["reply"]), citing_first(w["reply"])]), g["q"])
    assert body["status"] == "fallback" and body["fallback_reason"] == "engine_contradiction", body
    assert w["reply"] not in body["reply"]


def test_unsupported_is_not_labelled_verified(client):
    body = ask(client, FakeProvider([citing_first("ii–V–I là chuỗi ba hợp âm quen thuộc trong jazz.")]),
               "ii–V–I trong C trưởng là gì?")
    assert body["status"] == "ok" and not body["verified"] and not body["verified_label"], body
