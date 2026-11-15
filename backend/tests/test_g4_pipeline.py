"""G4 (T3 phần 2): pipeline chatbot kiểu n8n. Không gọi mạng: FakeProvider, FakeEmbedder, Qdrant nhúng (:memory:)."""

from __future__ import annotations

import dataclasses
import json
import re
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from qdrant_client import QdrantClient
from sqlalchemy import select

from app.ai.embedder import FakeEmbedder
from app.ai.pipeline.core import Ctx, Node, Pipeline, PipelineLoop
from app.ai.tutor.llm import FakeProvider
from app.ai.tutor.retriever import Hit
from app.api import ai_tutor
from app.core.ai_config import PipelineConfig, pipeline_config
from app.db.models import ChatMessage, ChatSession, User
from app.db.session import SessionLocal
from app.main import app
from app.rag.ingest import ingest
from app.rag.sources import lesson_records
from app.rag.store import QdrantStore
from app.services import ai_pipeline as ap
from tests.auth_helpers import auth

client = TestClient(app)
DIM = 64
ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module", autouse=True)
def _schema_and_seed():
    with TestClient(app):
        yield


@pytest.fixture(autouse=True)
def _clean(monkeypatch):
    app.dependency_overrides[ai_tutor.embedder_dep] = lambda: None
    app.dependency_overrides[ai_tutor.provider_dep] = lambda: None
    ap.reset_rate_limits()
    monkeypatch.setenv("CHAT_RATE_LIMIT_PER_MIN", "0")
    yield
    app.dependency_overrides.pop(ai_tutor.embedder_dep, None)
    app.dependency_overrides.pop(ai_tutor.provider_dep, None)


def make_user() -> str:
    uid = "g4-" + uuid4().hex[:12]
    with SessionLocal() as db:
        db.add(User(id=uid, display_name="Học sinh", email=f"{uid}@example.test"))
        db.commit()
    return uid


def ask(uid, text, status=200, **kw):
    r = client.post("/api/v1/chat/message", headers=auth(uid), json={"message": text, **kw})
    assert r.status_code == status, r.text
    return r


def last_tool_calls(uid) -> dict:
    with SessionLocal() as db:
        rows = db.scalars(select(ChatMessage).join(ChatSession, ChatSession.id == ChatMessage.session_id).where(
            ChatMessage.role == "assistant", ChatSession.user_id == uid).order_by(ChatMessage.id.desc())).all()
        return rows[0].tool_calls


def reply_json(text, **kw):
    return json.dumps({"reply": text, "citations": [], "engine_claims": [], "hint_level": 0, "suggested_actions": [],
                       "intent": "out_of_scope", **kw}, ensure_ascii=False)


# --- Khung pipeline -----------------------------------------------------------------------------------------------

class Mark(Node):
    def __init__(self, name, log, *, applies=True, done=False, goto=None, always=False):
        self.name, self._log, self._applies, self._done, self._goto, self.always = name, log, applies, done, goto, always

    def applies(self, ctx):
        return self._applies

    def run(self, ctx):
        self._log.append(self.name)
        ctx.done = self._done or ctx.done
        if self._goto and ctx.data.get("n", 0) < 1:
            ctx.data["n"] = 1
            ctx.goto = self._goto


def test_core_thu_tu_bo_qua_ket_thuc_som_va_node_luon_chay():
    log = []
    ctx = Pipeline([Mark("a", log), Mark("b", log, applies=False), Mark("c", log, done=True), Mark("d", log),
                    Mark("log", log, always=True)]).run(Ctx())
    assert log == ["a", "c", "log"]
    assert [(t.node, t.status) for t in ctx.trace] == [("a", "ok"), ("b", "skipped"), ("c", "ok"), ("log", "ok")]


def test_core_goto_quay_lai_dung_mot_lan_va_chan_vong_lap():
    log = []
    Pipeline([Mark("a", log), Mark("b", log, goto="a")]).run(Ctx())
    assert log == ["a", "b", "a", "b"]

    class Forever(Node):
        name = "f"

        def run(self, ctx):
            ctx.goto = "f"

    with pytest.raises(PipelineLoop):
        Pipeline([Forever()], max_steps=10).run(Ctx())
    with pytest.raises(ValueError):
        Pipeline([Mark("x", []), Mark("x", [])])


def test_so_do_tai_lieu_liet_ke_du_moi_node():
    doc = (ROOT / "docs" / "AI_PIPELINE.md").read_text(encoding="utf-8")
    missing = [n.name for n in ap.NODES if f"`{n.name}`" not in doc]
    assert not missing, f"docs/AI_PIPELINE.md thiếu node: {missing}"
    assert "```mermaid" in doc


# --- Rewrite, rerank, cắt câu -------------------------------------------------------------------------------------

def test_rewrite_chi_noi_cau_hoi_tiep_noi_ngan():
    turns = [("user", "Cmaj7 gồm những nốt nào?"), ("assistant", "C E G B.")]
    assert ap.rewrite_query("còn Dm7 thì sao?", turns) == "Cmaj7 gồm những nốt nào? còn Dm7 thì sao?"
    assert ap.rewrite_query("Dm7 gồm những nốt nào?", turns) == "Dm7 gồm những nốt nào?"      # câu đủ ý: giữ nguyên
    assert ap.rewrite_query("còn Dm7 thì sao?", []) == "còn Dm7 thì sao?"                       # chưa có lịch sử
    long = "vậy " + "từ " * 10
    assert ap.rewrite_query(long, turns) == long


def _hit(block, score, title="", text=""):
    from app.ai.tutor.chunker import Chunk
    return Hit(Chunk(f"{block}#1", "L01", block, title, text, "s", "h"), score)


def test_rerank_doi_thu_tu_giu_nguyen_diem_va_bo_trung():
    hits = [_hit("B1", 0.860, "Nhịp", "phách mạnh"), _hit("B2", 0.855, "Hợp âm Cmaj7", "Cmaj7 gồm C E G B"),
            _hit("B2", 0.850, "x", "y"), _hit("B3", 0.80)]
    out = ap.rerank("Cmaj7 gồm nốt nào", hits, weight=0.15, top_k=3)
    assert [h.chunk.block_id for h in out] == ["B2", "B1", "B3"]          # B2 trùng từ khóa nên lên đầu, B2 thứ hai bị bỏ
    assert {h.chunk.block_id: h.score for h in out} == {"B2": 0.855, "B1": 0.86, "B3": 0.80}
    assert ap.rerank("???", hits, 0.15, 2) == hits[:2]


def test_clip_sentences():
    assert ap.clip_sentences("Một. Hai. Ba. Bốn.", 2) == "Một. Hai."
    assert ap.clip_sentences("Chỉ một câu", 2) == "Chỉ một câu"
    long = ap.clip_sentences("từ " * 400, 2, max_chars=100)
    assert len(long) <= 101 and long.endswith("…")


# --- Qdrant trong bước Retrieve ---------------------------------------------------------------------------------

@pytest.fixture
def qdrant_mem(monkeypatch):
    store = QdrantStore(QdrantClient(":memory:"), "g4", DIM)
    store.ensure_collection()
    cfg = dataclasses.replace(__import__("app.core.ai_config", fromlist=["x"]).RagConfig(), dim=DIM, qdrant_url="memory://")
    ingest(store, FakeEmbedder(DIM), ["lessons"], cfg)
    monkeypatch.setenv("QDRANT_URL", "memory://")
    monkeypatch.setenv("RAG_EMBED_DIM", str(DIM))
    monkeypatch.setenv("RAG_ENABLED", "1")
    monkeypatch.setattr(ap, "_store", lambda rcfg: store)
    return store


def test_qdrant_retrieve_tra_dung_doan_va_dung_lai_chunk(qdrant_mem):
    rec = lesson_records()[5]
    r, note = ap.qdrant_retrieve(rec.text, FakeEmbedder(DIM), pipeline_config())
    assert note == "ok" and r.method == "embedding"
    top = r.hits[0]
    assert top.score == pytest.approx(1.0, abs=1e-3)
    assert (top.chunk.lesson_id, top.chunk.block_id, top.chunk.chunk_id) == (
        rec.payload["lesson_id"], rec.payload["block_id"], rec.payload["chunk_id"])
    assert len(r.hits) == pipeline_config().rerank_pool


@pytest.mark.parametrize("env,embedder,note", [
    ({"QDRANT_URL": ""}, FakeEmbedder(DIM), "no_qdrant_url"),
    ({}, None, "no_embedder"),
    ({"RAG_EMBED_DIM": "384"}, FakeEmbedder(DIM), "dim_mismatch"),
])
def test_qdrant_retrieve_lui_ve_duong_cu(qdrant_mem, monkeypatch, env, embedder, note):
    for k, v in env.items():
        monkeypatch.setenv(k, v)
    assert ap.qdrant_retrieve("Cmaj7", embedder, pipeline_config()) == (None, note)


def test_qdrant_collection_rong_hoac_loi_thi_lui_ve(qdrant_mem, monkeypatch):
    monkeypatch.setattr(ap, "_store", lambda rcfg: QdrantStore(QdrantClient(":memory:"), "empty", DIM).__class__(
        QdrantClient(":memory:"), "empty", DIM))
    _, note = ap.qdrant_retrieve("Cmaj7", FakeEmbedder(DIM), pipeline_config())
    assert note.startswith("qdrant_error") or note == "collection_empty"

    def boom(rcfg):
        raise ConnectionError("down")
    monkeypatch.setattr(ap, "_store", boom)
    assert ap.qdrant_retrieve("Cmaj7", FakeEmbedder(DIM), pipeline_config()) == (None, "qdrant_error:ConnectionError")


def test_pipeline_end_to_end_voi_qdrant_va_khi_qdrant_sap(qdrant_mem, monkeypatch):
    app.dependency_overrides[ai_tutor.embedder_dep] = lambda: FakeEmbedder(DIM)
    uid = make_user()
    ask(uid, "Cmaj7 gồm những nốt nào?")
    tc = last_tool_calls(uid)
    assert tc["retrieval"]["source"] == "qdrant" and tc["retrieval"]["note"] == "ok"
    nodes = {n["node"]: n["status"] for n in tc["pipeline"]["nodes"]}
    assert nodes["retrieve"] == "ok" and nodes["rerank"] == "ok" and nodes["log"] == "ok"

    monkeypatch.setattr(ap, "_store", lambda rcfg: (_ for _ in ()).throw(ConnectionError("down")))
    uid2 = make_user()
    r = ask(uid2, "Cmaj7 gồm những nốt nào?")
    assert r.json()["reply"]                                       # chatbot vẫn trả lời
    tc2 = last_tool_calls(uid2)
    assert tc2["retrieval"]["source"] == "legacy" and tc2["retrieval"]["note"] == "qdrant_error:ConnectionError"
    assert {n["node"]: n["status"] for n in tc2["pipeline"]["nodes"]}["rerank"] == "skipped"


def test_rag_tat_thi_khong_cham_qdrant(monkeypatch):
    monkeypatch.setattr(ap, "_store", lambda rcfg: pytest.fail("không được gọi Qdrant khi RAG_ENABLED=0"))
    uid = make_user()
    ask(uid, "Cmaj7 gồm những nốt nào?")
    assert last_tool_calls(uid)["retrieval"]["source"] == "legacy"


# --- Giới hạn tốc độ -------------------------------------------------------------------------------------------

def test_rate_limit_429_khong_luu_tin_va_nguoi_khac_khong_bi_anh_huong(monkeypatch):
    monkeypatch.setenv("CHAT_RATE_LIMIT_PER_MIN", "3")
    a, b = make_user(), make_user()
    for _ in range(3):
        ask(a, "Chào bạn")
    r = ask(a, "Chào bạn", status=429)
    assert r.json()["error"]["code"] == "AI_RATE_LIMITED" and int(r.headers["Retry-After"]) >= 1
    ask(b, "Chào bạn")
    with SessionLocal() as db:
        n = db.scalars(select(ChatMessage).join(ChatSession, ChatSession.id == ChatMessage.session_id).where(
            ChatMessage.role == "user", ChatSession.user_id == a)).all()
    assert len(n) == 3                                              # tin bị chặn không lưu


# --- Câu lạc đề ----------------------------------------------------------------------------------------------------

def test_lac_de_ai_tat_hoac_nhom_cam_hoac_che_do_refuse_thi_tu_choi_khong_goi_ai(monkeypatch):
    fake = FakeProvider([reply_json("Câu trả lời bị cấm.")])
    app.dependency_overrides[ai_tutor.provider_dep] = lambda: fake
    uid = make_user()
    r = ask(uid, "Cho mình link tải nhạc lậu free").json()
    assert r["flow"] == "C" and "trợ lý âm nhạc" in r["reply"] and fake.calls == []
    monkeypatch.setenv("OFFTOPIC_MODE", "refuse")
    assert ask(uid, "Cách nấu phở bò ngon").json()["source_label"] == "Ngoài phạm vi" and fake.calls == []
    monkeypatch.delenv("OFFTOPIC_MODE")
    app.dependency_overrides[ai_tutor.provider_dep] = lambda: None
    assert ask(uid, "Cách nấu phở bò ngon").json()["source_label"] == "Ngoài phạm vi"


def test_lac_de_tra_loi_ngan_toi_da_hai_cau_roi_dan_ve():
    fake = FakeProvider([reply_json("Phở cần xương ninh lâu. Gia vị gồm hồi, quế. Ăn kèm hành. Rất ngon.")])
    app.dependency_overrides[ai_tutor.provider_dep] = lambda: fake
    r = ask(make_user(), "Cách nấu phở bò ngon").json()
    sentences_before_steer = r["reply"].split(" Mình là trợ lý âm nhạc")[0]
    assert len(re.findall(r"[.!?…]", sentences_before_steer)) <= 2 and "Ăn kèm" not in r["reply"]
    assert r["reply"].endswith("nhé.") or "Cmaj7" in r["reply"]
    assert r["flow"] == "C" and r["citations"] == [] and len(fake.calls) == 1


def test_lac_de_rong_hoac_llm_hong_thi_dung_cau_tu_choi():
    fake = FakeProvider(["không phải json", "vẫn không phải json"])
    app.dependency_overrides[ai_tutor.provider_dep] = lambda: fake
    r = ask(make_user(), "Cách nấu phở bò ngon").json()
    assert r["source_label"] == "Ngoài phạm vi" and "trợ lý âm nhạc" in r["reply"]


# --- Nghiêm ngặt: độ tin cậy thấp → "không biết" -------------------------------------------------------------------

def test_strict_grounding_noi_khong_biet_va_goi_y_bai(monkeypatch):
    monkeypatch.setenv("RAG_STRICT_GROUNDING", "1")
    fake = FakeProvider([reply_json("Fugue là hình thức phức điệu.", intent="concept")])
    app.dependency_overrides[ai_tutor.provider_dep] = lambda: fake
    r = ask(make_user(), "Kết cấu fugue là gì?").json()
    assert r["flow"] == "B" and r["source_label"] == "Không biết" and "không biết" in r["reply"].lower()
    assert fake.calls == []                                        # không để Gemini đoán


# --- Nhật ký chi phí / độ trễ ------------------------------------------------------------------------------------

def test_log_ghi_vet_token_va_chi_phi(monkeypatch):
    monkeypatch.setenv("AI_PRICE_IN_PER_M", "1.0")
    monkeypatch.setenv("AI_PRICE_OUT_PER_M", "2.0")
    fake = FakeProvider([lambda s, u: json.dumps({
        "reply": "C7 = C E G Bb.", "citations": [], "engine_claims": [], "hint_level": 0, "suggested_actions": [],
        "intent": "concept"})])
    app.dependency_overrides[ai_tutor.provider_dep] = lambda: fake
    uid = make_user()
    ask(uid, "Cmaj7 với C7 khác gì nhau?")
    p = last_tool_calls(uid)["pipeline"]
    assert p["llm_calls"] >= 1 and p["tokens_in"] and p["cost_usd"] > 0 and p["pipeline_ms"] >= 0
    names = [n["node"] for n in p["nodes"]]
    assert names[:3] == ["trigger", "rate_limit", "guard"] and names[-1] == "log"
    assert "question" not in json.dumps(p) and "Cmaj7" not in json.dumps(p)       # không ghi nội dung câu hỏi
