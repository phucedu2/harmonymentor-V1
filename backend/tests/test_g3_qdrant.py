"""G3 (T3): nạp và truy vấn Qdrant. Dùng FakeEmbedder (không tải mô hình) và Qdrant chạy nhúng trong tiến trình
(QdrantClient(":memory:")). Bài kiểm tích hợp với MÁY CHỦ Qdrant thật chạy khi đặt QDRANT_TEST_URL (CI có service container)."""

import dataclasses
import json
import os

import pytest
from qdrant_client import QdrantClient

from app.ai.embedder import FakeEmbedder
from app.core.ai_config import RagConfig
from app.rag import ingest as ing
from app.rag.chunker import WhitespaceCounter, chunk_text, dedupe
from app.rag.errors import RagError
from app.rag.query import search
from app.rag.sources import corpus_records, lesson_records
from app.rag.store import QdrantStore, Record, point_id

DIM = 64


def _store(client=None, name="t") -> QdrantStore:
    s = QdrantStore(client or QdrantClient(":memory:"), name, DIM)
    s.ensure_collection()
    return s


def _cfg(tmp_path, **kw) -> RagConfig:
    return dataclasses.replace(RagConfig(), corpus_dir=str(tmp_path), dim=DIM, embedder="fake", **kw)


# ---- chunker ----
def test_chunk_tach_theo_token_co_chong_lan_va_giu_tieu_de():
    text = " ".join(f"Câu số {i} nói về hợp âm Cmaj7 trong giọng C." for i in range(30))
    chunks = chunk_text(text, "Hợp âm", WhitespaceCounter(), max_tokens=40, overlap_tokens=12)
    assert len(chunks) > 3
    assert all(c.tokens + 2 <= 40 for c in chunks)          # đoạn + tiêu đề ("Hợp âm" = 2 từ) vẫn vừa giới hạn
    assert chunks[1].text.split(". ")[0] in chunks[0].text  # đoạn sau lặp lại câu cuối đoạn trước (chồng lấn)
    assert chunks[0].index == 0 and [c.index for c in chunks] == list(range(len(chunks)))


def test_dedupe_bo_doan_trung():
    a = chunk_text("Quãng ba trưởng có bốn nửa cung.", "T", WhitespaceCounter(), 50, 5)
    assert len(dedupe(a + a)) == len(a)


# ---- store ----
def test_upsert_idempotent_va_xoa_doan_cu():
    s, emb = _store(), FakeEmbedder(DIM)
    recs = [Record(point_id("lessons", "L1/b", i, str(i)), f"đoạn {i}", {"source": "lessons", "lesson_id": "L1", "lang": "vi"}) for i in range(3)]
    vec = emb.embed([r.text for r in recs], "RETRIEVAL_DOCUMENT")
    s.upsert(recs, vec)
    s.upsert(recs, vec)
    assert s.count() == 3                                   # nạp lại không nhân đôi
    assert s.delete_stale("lessons", {recs[0].id}) == 2     # đoạn không còn trong nguồn bị xóa
    assert s.count() == 1


def test_doi_chieu_vector_la_loi_ro_rang():
    c = QdrantClient(":memory:")
    _store(c, "x")
    with pytest.raises(RagError, match="recreate"):
        QdrantStore(c, "x", 128).ensure_collection()


def test_search_loc_nguon_bai_va_nguong_diem():
    s, emb = _store(), FakeEmbedder(DIM)
    rows = [("lessons", "L1", "Cmaj7 là hợp âm bảy trưởng"), ("lessons", "L2", "Dm7 là hợp âm bảy thứ"), ("corpus", "", "Công thức nấu phở")]
    recs = [Record(point_id(src, lid + t, 0, "h"), t, {"source": src, "lesson_id": lid, "lang": "vi", "title": t}) for src, lid, t in rows]
    s.upsert(recs, emb.embed([r.text for r in recs], "RETRIEVAL_DOCUMENT"))
    cfg = RagConfig()
    top = search(s, emb, "Cmaj7 là hợp âm bảy trưởng", cfg=cfg, min_score=0.0)
    assert top[0].payload["lesson_id"] == "L1" and top[0].score == pytest.approx(1.0, abs=1e-5)
    assert all(a.score >= b.score for a, b in zip(top, top[1:]))
    assert {h.payload["source"] for h in search(s, emb, "x", cfg=cfg, min_score=-1, source="corpus")} == {"corpus"}
    assert {h.payload["lesson_id"] for h in search(s, emb, "x", cfg=cfg, min_score=-1, lesson_id="L2")} == {"L2"}
    assert len(search(s, emb, "x", cfg=cfg, min_score=-1, top_k=2)) == 2
    assert search(s, emb, "câu hỏi hoàn toàn khác", cfg=cfg, min_score=0.99) == []   # dưới ngưỡng → rỗng
    assert search(s, emb, "   ", cfg=cfg) == []


# ---- nguồn ----
def test_lesson_records_co_day_du_payload_va_khong_nhap():
    recs = lesson_records()
    assert len(recs) > 20
    for r in recs[:50]:
        assert {"source", "lesson_id", "block_id", "title", "lang", "chunk_idx", "license"} <= set(r.payload)
        assert r.payload["source"] == "lessons"
    assert len({r.id for r in recs}) == len(recs)


def test_corpus_doc_txt_md_va_meta(tmp_path):
    (tmp_path / "a.md").write_text("Hợp âm Cmaj7 gồm C E G B.\n\nQuãng ba trưởng có hai cung.", encoding="utf-8")
    (tmp_path / "a.md.meta.json").write_text(json.dumps({"title": "Ghi chú A", "license": "tự soạn", "lang": "vi"}), encoding="utf-8")
    (tmp_path / "bo-qua.exe").write_bytes(b"MZ")
    (tmp_path / "hong.pdf").write_bytes(b"khong phai pdf")
    recs, warns = corpus_records(_cfg(tmp_path), WhitespaceCounter())
    assert recs and all(r.text.startswith("Ghi chú A") for r in recs)      # tiêu đề được nhúng cùng đoạn
    assert recs and all(r.payload["title"] == "Ghi chú A" and r.payload["license"] == "tự soạn" for r in recs)
    assert any("hong.pdf" in w for w in warns)              # tệp lỗi: cảnh báo, không sập


# ---- ingest ----
def test_ingest_lessons_roi_nap_lai_khong_nhan_doi():
    s, emb, cfg = _store(), FakeEmbedder(DIM), dataclasses.replace(RagConfig(), dim=DIM)
    r1 = ing.ingest(s, emb, ["lessons"], cfg)
    n = s.count({"source": "lessons"})
    assert n == r1["sources"]["lessons"]["upserted"] > 0
    r2 = ing.ingest(s, emb, ["lessons"], cfg)
    assert s.count({"source": "lessons"}) == n and r2["sources"]["lessons"]["deleted_stale"] == 0


def test_ingest_xoa_doan_khi_tai_lieu_bi_go(tmp_path):
    s, emb, cfg = _store(), FakeEmbedder(DIM), _cfg(tmp_path)
    f = tmp_path / "x.txt"
    f.write_text("Âm giai trưởng gồm bảy nốt theo công thức T T S T T T S.", encoding="utf-8")
    ing.ingest(s, emb, ["corpus"], cfg)
    assert s.count({"source": "corpus"}) >= 1
    f.unlink()
    r = ing.ingest(s, emb, ["corpus"], cfg)
    assert s.count({"source": "corpus"}) == 0 and r["sources"]["corpus"]["deleted_stale"] >= 1


def test_dry_run_khong_ghi_va_khong_goi_embedder(tmp_path):
    s, emb, cfg = _store(), FakeEmbedder(DIM), _cfg(tmp_path)
    r = ing.ingest(s, emb, ["lessons"], cfg, dry_run=True)
    assert r["sources"]["lessons"]["chunks"] > 0 and s.count() == 0 and emb.calls == []


def test_nguon_khong_hop_le():
    with pytest.raises(RagError):
        ing.ingest(_store(), FakeEmbedder(DIM), ["abc"], RagConfig())


def test_cli_dry_run_khong_can_qdrant(monkeypatch, capsys, tmp_path):
    monkeypatch.setenv("RAG_EMBEDDER", "fake")
    monkeypatch.setenv("RAG_EMBED_DIM", str(DIM))
    monkeypatch.setenv("RAG_CORPUS_DIR", str(tmp_path))
    monkeypatch.delenv("QDRANT_URL", raising=False)
    assert ing.main(["--source", "lessons", "--dry-run"]) == 0
    assert json.loads(capsys.readouterr().out)["sources"]["lessons"]["chunks"] > 0
    assert ing.main(["--source", "lessons"]) == 2            # thiếu QDRANT_URL: báo lỗi rõ, mã thoát 2
    assert "QDRANT_URL" in capsys.readouterr().err


# ---- tích hợp máy chủ Qdrant thật (CI service container hoặc docker compose của máy nhóm) ----
@pytest.mark.skipif(not os.getenv("QDRANT_TEST_URL"), reason="cần Qdrant thật: đặt QDRANT_TEST_URL (CI có service container)")
def test_tich_hop_may_chu_qdrant_that():
    url = os.getenv("QDRANT_TEST_URL", "http://localhost:6333")
    client = QdrantClient(url=url, timeout=30)
    s, emb = QdrantStore(client, "g3_it", DIM), FakeEmbedder(DIM)
    s.ensure_collection(recreate=True)
    cfg = dataclasses.replace(RagConfig(), dim=DIM)
    ing.ingest(s, emb, ["lessons"], cfg)
    ing.ingest(s, emb, ["lessons"], cfg)
    st = s.stats()
    assert st["by_source"]["lessons"] == st["total"] > 0
    q = lesson_records()[0]
    top = search(s, emb, q.text, cfg=cfg, min_score=0.5, source="lessons")
    assert top and top[0].id == q.id
    client.delete_collection("g3_it")
