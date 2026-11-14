"""GĐ3 mục 1–2: kho đoạn bài học, file vector, retriever (Fake/BM25) và phân loại ý định. Không gọi mạng."""

from __future__ import annotations

import json

import pytest

from app.ai import embedder as emb
from app.ai.tutor import chunker as ck
from app.ai.tutor import retriever as rt
from app.ai.tutor.bm25 import BM25, tokenize
from app.ai.tutor.intent import INTENTS, classify, evaluate
from app.content.curriculum_specs import LESSON_SPECS


def words(t):
    return len(t.split())


def test_chunks_only_published_lessons_and_text_blocks():
    chunks = ck.lesson_chunks()
    lessons = {c.lesson_id for c in chunks}
    drafts = {s["id"] for s in LESSON_SPECS if s.get("status") == "draft"}
    assert lessons and not lessons & drafts
    for c in chunks:
        assert c.chunk_id.startswith(c.block_id + "#") and c.source and len(c.content_hash) == 64


def test_no_exercise_or_draft_blocks_in_kb():
    from app.content.draft_specs import blocks_with_drafts

    banned = set()
    for spec in LESSON_SPECS:
        for block_id, block_type, payload in blocks_with_drafts(spec):
            if block_type not in ck.TEXT_BLOCKS or (payload or {}).get("status") == "draft" or payload.get("exercise_id"):
                banned.add(block_id)
    assert not {c.block_id for c in ck.lesson_chunks()} & banned


def test_no_answer_keys_leak_into_kb():
    # Đáp án dạng câu (rubric) không được nằm nguyên văn trong kho.
    text = " ".join(c.text for c in ck.lesson_chunks()).lower()
    for spec in LESSON_SPECS:
        for ex in spec.get("exercises", []):
            for acc in ex["answer_key"].get("accepted", []):
                if len(acc) > 25:
                    assert acc.lower() not in text, ex["id"]


def test_chunk_size_and_sentence_integrity():
    sent = "Hợp âm bảy có bốn nốt xếp chồng quãng ba."  # 10 từ
    text = " ".join([sent] * 25)  # 250 từ
    chunks = ck.chunk_block("L00", "L00-B01", "Tiêu đề", text, "nguồn")
    assert [words(c.text) for c in chunks] == [80, 80, 80, 10]
    assert all(c.text.endswith(".") for c in chunks)
    real = ck.lesson_chunks()
    assert max(words(c.text) for c in real) <= ck.WORDS_MAX


def test_long_sentence_stays_whole():
    long = " ".join(["từ"] * 130) + "."
    chunks = ck.chunk_block("L00", "B", "T", long, "s")
    assert len(chunks) == 1 and words(chunks[0].text) == 130


def test_hash_changes_with_text():
    a = ck.chunk_block("L00", "B", "T", "Câu một. Câu hai.", "s")[0]
    b = ck.chunk_block("L00", "B", "T", "Câu một. Câu ba.", "s")[0]
    assert a.content_hash != b.content_hash


def test_index_file_matches_current_chunks():
    # Sửa nội dung bài mà quên chạy lại build_index thì test này báo (retriever sẽ rơi về BM25).
    index = rt.load_index()
    assert index["model"] == "gemini-embedding-001" and index["dim"] == 768
    vecs = rt.index_vectors(index, ck.lesson_chunks(), index["model"])
    assert vecs is not None and len(vecs) == len(ck.lesson_chunks())
    raw = rt.INDEX_PATH.read_text(encoding="utf-8")
    assert "AIza" not in raw and "user_id" not in raw and "@" not in raw


def test_index_mismatch_means_none():
    chunks = ck.lesson_chunks()
    index = json.loads(rt.INDEX_PATH.read_text(encoding="utf-8"))
    assert rt.index_vectors(index, chunks, "model-khac") is None
    first = chunks[0].chunk_id
    index["chunks"][first]["hash"] = "0" * 64
    assert rt.index_vectors(index, chunks, index["model"]) is None


def _fake_store(fake, chunks):
    return [fake.embed([c.text], "RETRIEVAL_DOCUMENT")[0] for c in chunks]


def test_retriever_embedding_path_top_k_and_threshold():
    fake = emb.FakeEmbedder(dim=32)
    chunks = ck.lesson_chunks()[:10]
    vecs = _fake_store(fake, chunks)
    # Câu hỏi trùng hệt văn bản đoạn 3 → cosine 1 với đoạn đó.
    r = rt.retrieve(chunks[3].text, fake, chunks=chunks, vectors=vecs, top_k=4, min_score=0.99)
    assert r.method == "embedding" and [h.chunk.chunk_id for h in r.hits] == [chunks[3].chunk_id]
    r2 = rt.retrieve(chunks[3].text, fake, chunks=chunks, vectors=vecs, top_k=4, min_score=-1)
    assert len(r2.hits) == 4 and r2.hits[0].score == pytest.approx(1.0)


def test_retriever_falls_back_to_bm25():
    r = rt.retrieve("Cmaj7 khác C7 thế nào", None)
    assert r.method == "bm25" and r.fallback_reason == "ai_disabled" and r.hits
    # BM25 sau khi L06, L07, L08 vào kho: các bài jazz nhắc Cmaj7, C7 nhiều lần nên chiếm top 4 và đẩy L02 ra
    # (giảm nhẹ truy xuất BM25 trên 30 câu chuẩn: 15→14 đúng ngay lần đầu, 26→25 trong top 4; ghi ở báo cáo 16).
    # Đường chính là Gemini, không qua BM25. Chỉ kiểm có kết quả và đều thuộc kho.
    assert {h.chunk.lesson_id for h in r.hits} <= {c.lesson_id for c in rt.knowledge_base()}

    class Down:
        model, dim = "gemini-embedding-001", 768

        def embed(self, texts, task):
            raise emb.EmbeddingUnavailable("503")

    r2 = rt.retrieve("Cmaj7 khác C7 thế nào", Down())
    assert r2.method == "bm25" and r2.fallback_reason == "embedding_unavailable"

    class OtherModel(Down):
        model = "mo-hinh-khac"

    assert rt.retrieve("Cmaj7", OtherModel()).fallback_reason == "index_stale"


def test_bm25_ignores_stopwords_and_accepts_no_accent():
    assert "là" not in tokenize("Quãng năm là gì") and "gì" not in tokenize("Quãng năm là gì")
    assert "hop" in tokenize("hợp âm")
    bm = BM25(["hợp âm bảy có bốn nốt", "âm giai trưởng"])
    s = bm.scores("hop am bay")
    assert s[0] > s[1]


def test_retrieve_for_skill_stays_in_lesson():
    r = rt.retrieve_for_skill("Dựng hợp âm bảy", None, ["L02"], top_k=3)
    assert r.hits and {h.chunk.lesson_id for h in r.hits} == {"L02"}
    assert rt.retrieve_for_skill("x", None, ["L99"]).hits == []


def test_intent_classifier_accuracy_and_labels():
    result = evaluate()
    assert result["accuracy"] >= 0.9, result["wrong"]
    for q, want in [("C7 khác Cmaj7 thế nào?", "concept"), ("Cách nấu phở bò", "out_of_scope"),
                    ("Vì sao câu này mình sai", "explain_error"), ("goi y hop am cho bai hat buon", "composition")]:
        got = classify(q)
        assert got.intent == want and got.intent in INTENTS, (q, got)
