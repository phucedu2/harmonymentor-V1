"""GĐ4: bộ người học mô phỏng và hai script đánh giá. Không gọi mạng.

Kiểm điều làm số liệu đáng tin: bộ mô phỏng độc lập với bộ gợi ý (không import), tất định (kể cả khi
PYTHONHASHSEED khác), và bộ chuẩn RAG trỏ tới khối có thật, đáp án nhạc lý khớp Music Engine.
"""

from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SIM = ROOT / "scripts" / "ai" / "sim" / "nguoi_mo_phong.py"
GOLD = ROOT / "scripts" / "ai" / "data" / "rag_gold.json"
sys.path.insert(0, str(ROOT / "scripts" / "ai"))


def _imports(path: Path) -> set[str]:
    mods = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            mods |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            mods.add(node.module)
    return mods


def test_simulator_does_not_import_recommender_or_services():
    mods = _imports(SIM)
    assert not any(m.startswith(("app.ai", "app.services", "app.db")) for m in mods), mods
    assert {"app.content.curriculum_specs", "app.content.skill_graph"} <= mods


def test_simulator_runtime_modules_exclude_recommender():
    code = ("import sys; sys.path[:0]=['scripts/ai','backend']; from sim.nguoi_mo_phong import generate; "
            "generate(5, 1); print(any(m.startswith('app.ai.recommender') for m in sys.modules))")
    out = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, check=True)
    assert out.stdout.strip() == "False"


def _digest(hashseed: str) -> str:
    code = ("import sys, hashlib; sys.path[:0]=['scripts/ai','backend']; from sim.nguoi_mo_phong import generate; "
            "print(hashlib.sha256(repr([(u.uid, u.persona, [tuple(vars(e).values()) for e in u.events]) "
            "for u in generate(30, 7)]).encode()).hexdigest())")
    env = {**os.environ, "PYTHONHASHSEED": hashseed}
    return subprocess.run([sys.executable, "-c", code], cwd=ROOT, env=env, capture_output=True, text=True,
                          check=True).stdout.strip()


def test_simulator_deterministic_across_hash_seeds():
    assert _digest("1") == _digest("2")


def test_simulator_shape():
    from sim.nguoi_mo_phong import LEARNABLE, PERSONAS, generate, load_curriculum

    users = generate(40, 3)
    assert {u.persona for u in users} == {p.name for p in PERSONAS}
    lessons = set(load_curriculum().lessons)
    assert lessons and lessons <= {"L01", "L02", "L03", "L04"}  # chỉ bài có câu đang chạy trong ứng dụng
    for u in users:
        ts = [e.t for e in u.events]
        assert ts == sorted(ts)
        assert {e.lesson for e in u.events if e.lesson} <= lessons
        starts = [e.lesson for e in u.events if e.kind == "start"]
        assert len(starts) == len(set(starts))  # mỗi bài bắt đầu lần đầu đúng một lần
        for e in u.events:
            if e.kind == "review":
                assert e.next_due is not None and e.next_due > e.t
    assert LEARNABLE == {"reviewed", "published"}


def test_rag_gold_blocks_exist_and_engine_answers_match():
    from app.ai.tutor.guardrail import run_tool
    from app.ai.tutor.retriever import knowledge_base

    data = json.loads(GOLD.read_text(encoding="utf-8"))
    assert len(data["concept"]) == 30 and len(data["out_of_scope"]) == 10 and len(data["attacks"]) == 10
    blocks = {c.block_id for c in knowledge_base()}
    ids = [g["id"] for g in data["concept"]]
    assert len(ids) == len(set(ids))
    for g in data["concept"]:
        assert g["blocks"] and set(g["blocks"]) <= blocks, g["id"]
        if g.get("engine"):
            assert run_tool(g["engine"]["tool"], g["engine"]["args"])[0] == g["engine"]["expect"], g["id"]
    assert {s["wrong"] for s in data["seeded_errors"]} == {True, False}


def _run(script: str, *args: str) -> str:
    env = {k: v for k, v in os.environ.items() if k not in {"GEMINI_API_KEY", "GOOGLE_API_KEY"}}
    env["AI_ENABLED"] = "0"
    return subprocess.run([sys.executable, str(ROOT / "scripts" / "ai" / script), *args], cwd=ROOT / "backend",
                          env=env, capture_output=True, text=True, check=True, timeout=300).stdout


def test_evaluate_rag_offline_smoke(tmp_path):
    out = tmp_path / "rag.json"
    _run("evaluate_rag.py", "--out", str(out))
    res = json.loads(out.read_text(encoding="utf-8"))
    assert res["gold_engine_checked"]["n"] == res["gold_engine_checked"]["ok"] > 0
    assert res["retrieval"]["gemini"].startswith("NOT EVALUATED")
    assert res["answers"].startswith("NOT EVALUATED")
    assert res["guardrail"]["false_alarm"] == 0 and res["gating"]["concept_wrongly_blocked"] == 0


def test_evaluate_recommender_smoke(tmp_path):
    out = tmp_path / "rec.json"
    _run("evaluate_recommender.py", "--n", "60", "--boot", "20", "--out", str(out))
    res = json.loads(out.read_text(encoding="utf-8"))
    assert {"P0", "P1", "P2", "P3-s3a", "P2-bo-tien-quyet"} <= set(res["results"])
    assert res["evaluated_users"] + sum(res["skipped"].values()) <= 60
    for entry in res["results"].values():
        assert entry["n_users"] == res["evaluated_users"]


def test_fallback_lead_says_busy_unless_ai_disabled():
    # GĐ4 chạy thật: khi Gemini quá tải (429/503) mà báo "đang tạm nghỉ" là sai sự thật với người học.
    from app.ai.tutor import fallback as fb
    from app.services.ai_tutor_service import offline_answer

    assert offline_answer([], [], {}, "ai_disabled").reply.startswith(fb.UNAVAILABLE)
    for reason in ("rate_limited", "unavailable", "timeout", "invalid"):
        assert offline_answer([], [], {}, reason).reply.startswith(fb.BUSY)
