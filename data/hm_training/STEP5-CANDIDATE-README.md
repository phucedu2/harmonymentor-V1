# Step 5 candidate materialization

This directory contains candidate JSONL generated after user approval of A01-A26 and C01-C08.

- `examples.step5-A-C.candidate.jsonl` is a separate candidate artifact; it is not production data and is not merged into train/dev/test.
- B01-B04 remain excluded because they are out-of-curriculum and need source/provenance review.
- Technical validation is still required: duplicate/group checks, schema, engine claims where applicable, tokenizer, and assistant-only mask.
- `production_ready` remains false until the candidates pass validation and the training threshold is met.
