"""Demo 10/11 với Gemini thật: 5 câu vàng của Thắng (đánh dấu live, CI không chạy).

    cd backend && RUN_LIVE=1 AI_ENABLED=1 GEMINI_API_KEY=... pytest -q -m live tests/test_demo1011_live.py

Đạt khi: trả lời bằng Gemini (status ok) hoặc dự phòng có lý do rõ; có trích dẫn khối trong bài đúng;
không có khẳng định nào bị Music Engine bác lọt tới người học.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.db.models import User
from app.db.session import SessionLocal
from app.main import app
from tests.auth_helpers import auth

pytestmark = [pytest.mark.live,
              pytest.mark.skipif(os.getenv("RUN_LIVE") != "1", reason="cần RUN_LIVE=1 và khóa Gemini")]

GOLD = json.loads((Path(__file__).resolve().parents[2] / "scripts" / "ai" / "data" / "rag_gold.json")
                  .read_text(encoding="utf-8"))["demo_1011"]["items"]


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


@pytest.mark.parametrize("g", GOLD, ids=[g["id"] for g in GOLD])
def test_gold_question_live(client, g):
    uid = "live1011-" + uuid4().hex[:8]
    with SessionLocal() as db:
        db.add(User(id=uid, display_name="live", email=f"{uid}@example.test"))
        db.commit()
    time.sleep(5)  # free tier: gọi liên tục dễ 429/503 (GĐ4)
    body = client.post("/api/v1/chat/message", headers=auth(uid), json={"message": g["q"]}).json()
    print("\nLIVE", g["id"], json.dumps({k: body.get(k) for k in (
        "status", "fallback_reason", "model", "verified", "verified_label", "reply")}, ensure_ascii=False))
    print("LIVE", g["id"], "citations", [c["block_id"] for c in body.get("citations", [])],
          "claims", [(c["tool"], c.get("claimed"), c["status"]) for c in body.get("engine_claims", [])])
    assert body["status"] in {"ok", "fallback"}, body
    lessons = {b.split("-")[0] for b in g["blocks"]}
    assert lessons & {c["lesson_id"] for c in body["citations"]}, body
    assert not [c for c in body["engine_claims"] if c["status"] == "contradicted"], body
