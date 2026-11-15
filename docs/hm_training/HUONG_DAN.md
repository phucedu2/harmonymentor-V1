# HarmonyMentor AI Training Starter (pilot only)

This starter is ADDITIVE. It does not change the repository, a database, any
published lesson, the existing Music Engine, or the existing Gemini tutor.
It is not a trained model. It prepares data, demonstrates Qdrant indexing, and
contains the GPU training script for a Qwen3 4B LoRA adapter.

## 0. Existing repo functions you should not duplicate

- `scripts/ai/gop_y/finetune_e5.py`: existing E5 embedding fine-tuning.
- `backend/app/ai/local_embedder.py`: local 384-dim multilingual E5 ONNX.
- `backend/app/ai/tutor/chunker.py`, `retriever.py`: published lesson chunks.
- `backend/app/ai/tutor/guardrail.py`: Music Engine validation.
- `backend/app/ai/tutor/schema.py`: expected structured LLM output.
- `backend/app/admin/ai_service.py`: draft lesson generation from documents.

The current local tutor uses cosine/BM25; it does NOT query Qdrant. The
Qdrant pilot script is separate, so you can compare retrieval before wiring it in.
IMPORTANT: existing `lesson_chunks()` reads the code-level `LESSON_SPECS`, not
the published lessons or admin overrides in PostgreSQL. Publishing an AI draft
into the DB does NOT automatically make it available to this KB. A production
RAG integration must also index published DB lessons and content revisions,
reconcile hidden/unpublished/deleted items, and reindex on content changes.

## 1. Copy these folders into the clone of harmonymentor-V1, branch phuc-music

From this ZIP copy `scripts/ai/hm_training/` and `data/hm_training/` into the
same relative folders in your repository. Keep any model weights, API tokens,
private documents and prepared training data out of Git.

The `data/hm_training/examples.demo.jsonl` is intentionally UNAPPROVED, contains
just 6 handcrafted illustrative records and MUST NOT be published as evidence
of model accuracy. Before a real run, manually check the facts, rights and
source references, add many independent examples, and set approved fields.

## 2. First run: data validation, without a GPU

```bash
python scripts/ai/hm_training/prepare_dataset.py \
  --input data/hm_training/examples.demo.jsonl \
  --out outputs/hm_dataset_demo --allow-demo

python -m unittest discover -s tests -v
```

If you copy only the two script/data folders, the unittest folder is not part
of your repo; use the starter's tests or skip that second command.

For REAL training data: use a new input file containing reviewed examples
with `reviewed_by_human: true` and `rights_cleared: true`. Omit `--allow-demo`.
Require `--verify-engine` for real training so all model-declared claims
are re-computed using the repository's current deterministic engine.
Use at least 50 approved training examples for the training script to start;
for meaningful quality improvement, aim for a much larger curated dataset.
Keep `group_id` entire families of paraphrases in the same split to avoid
leakage. Use the `source_manifest.example.csv` as provenance checklist.

## 3. Qdrant pilot, no need to change the app

First install the repo backend requirements, and download the pinned local E5:

```bash
cd backend
python -m pip install -r requirements.txt
python -m app.ai.local_embedder download
cd ..
python -m pip install -r requirements-rag.txt
```

You can start with Qdrant LOCAL MODE (no Docker needed):

```bash
python scripts/ai/hm_training/qdrant_pilot.py index \
  --local-path outputs/qdrant_pilot --collection hm_lessons_e5_v1_pilot

python scripts/ai/hm_training/qdrant_pilot.py query \
  --local-path outputs/qdrant_pilot --collection hm_lessons_e5_v1_pilot \
  --question "Cmaj7 vs C7" --top-k 5
```

Or use Qdrant server with `QDRANT_URL=http://127.0.0.1:6333`, no `--local-path`:

```bash
docker run --name hm-qdrant -p 6333:6333 -p 6334:6334 \
  -v hm_qdrant_data:/qdrant/storage -d qdrant/qdrant
```

The script calls the EXISTING E5 embedder, whose embeddings are 384 dimensional.
Do NOT use BGE-M3 or another embedding model in the same collection without
migrating all vectors. Do NOT mix original E5 and fine-tuned E5: their scales
and thresholds differ. A fresh collection per model + corpus revision is safer.

For a previously indexed _pilot collection, `--replace` removes it and recreates
its entire content; it is deliberately disallowed for any name without _pilot.
Do not grant unauthenticated public access to Qdrant in deployment.

## 4. QLoRA of a Qwen3 4B instruct model (NVIDIA GPU)

Use a compatible Linux/Colab CUDA runtime. Install PyTorch and Unsloth using
the current official installation documentation, then:

```bash
python -m pip install -r requirements-train.txt
python scripts/ai/hm_training/train_qlora.py \
  --data-dir outputs/hm_dataset_demo --output outputs/hm_qwen_demo \
  --epochs 1 --max-seq-length 1024 --max-steps 5 --allow-demo
```

The command above is a **GPU smoke test**, NOT a model to evaluate or deploy.
The sample has only four training rows. Real experiments must omit `--allow-demo`
and use reviewed data; start with:

```bash
python scripts/ai/hm_training/prepare_dataset.py \
  --input data/hm_training/examples.approved.jsonl \
  --out outputs/hm_dataset_v1 --verify-engine
python scripts/ai/hm_training/train_qlora.py \
  --data-dir outputs/hm_dataset_v1 --output outputs/hm_qwen_v1 \
  --epochs 2 --max-seq-length 1024
```

`outputs/hm_qwen_v1/adapter/` contains the saved LoRA adapter; the base model
still needs to be available when serving inference. Training saves a report
with hyperparameters, hashes and validation loss. Validation loss is NOT a
substitute for ground-truth music accuracy or human assessment.

Expected model: `unsloth/Qwen3-4B-Instruct-2507-unsloth-bnb-4bit`, derivative
of Qwen3-4B-Instruct-2507 (Apache 2.0). Do not confuse with Qwen3.5: Unsloth
currently recommends LoRA in 16-bit, NOT QLoRA in 4-bit, for Qwen3.5.

## 5. Chatbot integration after passing evaluation

Keep backend -> router -> retriever -> Music Engine -> generator -> guardrail.
Create a new implementation of `LLMProvider` in `backend/app/ai/tutor/llm.py`
or a sibling module, with `.generate(system, user, schema) -> LLMResult`.
The local model must output the exact `TutorAnswer` JSON keys. Continue to
validate using `parse_answer`, reject unknown citation block IDs, and check
`engine_claims` with the existing Music Engine. Never trust model-issued
`verified` values. Use a configuration flag such as `AI_PROVIDER=local`, and
keep Gemini/fallback unchanged while evaluating the pilot.

In a later PR, implement a Qdrant-backed retriever behind the existing
`retrieve` contract and keep BM25 fallback. Query only published, authorized
and version-matching records; enable an explicit shadow/A-B mode first.

## 6. n8n workflow blueprint (not an importable n8n export)

Manual upload -> allowlisted file types and size -> extract text and pages ->
metadata/source permissions -> human review -> chunking -> E5 embed ->
upsert *new-version* Qdrant collection -> evaluate fixed queries ->
optional index promotion -> audit log. For lesson drafting, use the
existing admin draft endpoints, review, and publish process. n8n orchestrates;
it does not rewrite the Music Engine or bypass approval.

External PDFs/books may be copyrighted. A right to READ a PDF is not the same
as permission to reproduce/distribute its contents or train on it. Review
chapter/media licenses. Store only authorized snippets and source metadata.
Do not upload private learner data to a public dataset/model hub.

## 7. Evaluation before replacing Gemini or E5

Create an independent human-authored and hidden TEST set. Compare:
A. existing Gemini + local E5/BM25;
B. existing Gemini + Qdrant retrieval;
C. base Qwen + the same retrieval;
D. LoRA Qwen + the same retrieval.

Measure Recall@1/5, MRR, proper refusal of out-of-domain questions, source
citation validity, Engine claim agreement, rate of unsupported statements,
Vietnamese explanation clarity, latency and hardware cost. Report counts and
confidence intervals: passing a few demo questions proves nothing. Test also
prompts with spelling mistakes, short questions, unsupported chord notation,
retrieved prompt-injection text, and privacy/authorization boundaries.

## 8. What has NOT been tested here

Python syntax and dataset validation were run locally. Qdrant indexing was NOT
run against your repository since the repo and ONNX weights cannot be fetched
in this execution environment. GPU QLoRA training and inference were NOT run
(no Unsloth/CUDA here). Library versions and chat-template details must be
checked in the actual runtime, pinned after the first successful run.

Official references:
- https://unsloth.ai/docs/get-started/fine-tuning-llms-guide
- https://unsloth.ai/docs/models/qwen3.5/fine-tune
- https://huggingface.co/docs/trl/sft_trainer
- https://qdrant.tech/documentation/quickstart/
- https://qdrant.tech/documentation/search-tuning/hybrid-search/
- https://docs.n8n.io/integrations/builtin/cluster-nodes/root-nodes/n8n-nodes-langchain.vectorstoreqdrant/
