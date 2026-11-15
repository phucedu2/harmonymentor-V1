"""Index the ALREADY PUBLISHED HarmonyMentor lesson KB to Qdrant (pilot).

Drop this file under scripts/ai/hm_training/ in harmonymentor-V1. This script
reuses the project's existing multilingual-e5-small ONNX embedder and chunks.
It does not upload any external textbook or unapproved draft to Qdrant.

Use a fresh collection per model/corpus version. --replace requires _pilot suffix.
"""
from __future__ import annotations

import argparse
import os
import sys
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "backend"))


def client_for(local_path: str | None):
    from qdrant_client import QdrantClient
    return QdrantClient(path=local_path) if local_path else QdrantClient(
        url=os.environ.get("QDRANT_URL", "http://localhost:6333"),
        api_key=os.environ.get("QDRANT_API_KEY") or None,
    )


def embedder_for():
    from app.ai.local_embedder import get_local_embedder
    embedder = get_local_embedder()
    if embedder is None:
        raise RuntimeError(
            "Local E5 unavailable. Run: cd backend && python -m app.ai.local_embedder download"
        )
    return embedder


def published_chunks():
    from app.ai.tutor.retriever import knowledge_base
    from app.ai.tutor.chunker import lesson_titles
    titles = lesson_titles()
    chunks = list(knowledge_base())
    return chunks, [c.embed_text(titles.get(c.lesson_id, "")) for c in chunks]


def index(client, collection: str, replace: bool):
    from qdrant_client.models import Distance, PointStruct, VectorParams
    emb = embedder_for()
    chunks, texts = published_chunks()
    if client.collection_exists(collection):
        if not replace:
            raise RuntimeError(
                "Collection exists; do not append stale content. Choose a new collection "
                "or use --replace on a _pilot collection."
            )
        if not collection.endswith("_pilot"):
            raise RuntimeError("--replace is allowed only for collection names ending _pilot")
        client.delete_collection(collection)
    client.create_collection(collection_name=collection, vectors_config=VectorParams(
        size=emb.dim, distance=Distance.COSINE,
    ))
    print("embedding model", emb.model, "dim", emb.dim, "chunks", len(chunks))
    for start in range(0, len(chunks), 16):
        chunk_batch = chunks[start:start + 16]
        vectors = emb.embed(texts[start:start + 16], "RETRIEVAL_DOCUMENT")
        points = []
        for c, vector in zip(chunk_batch, vectors):
            point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, "harmonymentor/lesson/" + c.chunk_id))
            points.append(PointStruct(id=point_id, vector=vector, payload={
                "chunk_id": c.chunk_id, "lesson_id": c.lesson_id,
                "block_id": c.block_id, "title": c.title,
                "text": c.text, "source": c.source,
                "content_hash": c.content_hash,
                "embedding_model": emb.model, "status": "published", "doc_type": "lesson",
            }))
        client.upsert(collection_name=collection, wait=True, points=points)
    print("Indexed", len(chunks), "published chunks into", collection)


def query(client, collection: str, question: str, top_k: int):
    from qdrant_client.models import FieldCondition, Filter, MatchValue
    emb = embedder_for()
    query_vec = emb.embed([question], "RETRIEVAL_QUERY")[0]
    result = client.query_points(
        collection_name=collection, query=query_vec,
        query_filter=Filter(must=[
            FieldCondition(key="embedding_model", match=MatchValue(value=emb.model)),
            FieldCondition(key="status", match=MatchValue(value="published")),
            FieldCondition(key="doc_type", match=MatchValue(value="lesson")),
        ]), limit=top_k, with_payload=True,
    ).points
    for i, item in enumerate(result, 1):
        p = item.payload or {}
        print(f"{i}. score={item.score:.4f} {p.get('lesson_id')}/{p.get('block_id')} "
              f"source={p.get('source')}\n    {str(p.get('text', ''))[:320]}")
    if not result:
        print("No matching published chunks (this does NOT imply factual absence).")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["index", "query"])
    ap.add_argument("--collection", default="hm_lessons_e5_v1_pilot")
    ap.add_argument("--local-path", default=None, help="local Qdrant, no Docker required")
    ap.add_argument("--replace", action="store_true", help="DELETES collection, only allowed for *_pilot")
    ap.add_argument("--question", help="required for query")
    ap.add_argument("--top-k", type=int, default=5)
    args = ap.parse_args()
    client = client_for(args.local_path)
    try:
        if args.command == "index":
            index(client, args.collection, args.replace)
        else:
            if not args.question:
                ap.error("--question is required for query")
            query(client, args.collection, args.question, args.top_k)
    finally:
        client.close()


if __name__ == "__main__":
    main()
