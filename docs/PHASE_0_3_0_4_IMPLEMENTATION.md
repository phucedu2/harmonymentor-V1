# HarmonyMentor Phase 0.3–0.4 — Application Skeleton + Database + Learning Contract

Version: `v0.3.0-dev`

## 1. Scope completed

This phase turns the Phase 0.2 frontend/content prototype into a persisted application skeleton.

Implemented:

- modular FastAPI routers;
- SQLAlchemy 2 persistence model;
- Alembic initial migration;
- PostgreSQL-compatible `DATABASE_URL` configuration;
- SQLite local/test fallback;
- Content Service contract for lessons;
- versioned exercises and persisted attempts;
- lesson completion state;
- review items, review state, review attempts;
- deterministic 1–3–7–14–30 day review scheduler;
- first deterministic `Chord Inspector` API contract;
- Lesson 1 migrated from frontend-only TypeScript into backend seed content;
- frontend Learn now consumes the backend Content Service;
- Lesson 1 can submit quiz attempts and activate review state.

Not implemented yet:

- mastery aggregation / recommendation engine;
- Lessons 2–8 full block/exercise migration;
- piano/audio/VexFlow;
- AI Harmony Assistant;
- authentication beyond the seeded `demo-user`.

## 2. Runtime architecture

```text
React / TypeScript
      |
      | /api/v1
      v
FastAPI modular monolith
  |-- /engine     legacy Practice API
  |-- /music      deterministic inspect contracts
  |-- /lessons    curriculum/content
  |-- /attempts   versioned assessment evidence
  `-- /review     spaced-review state
      |
      v
SQLAlchemy 2
      |
      +-- PostgreSQL (target)
      `-- SQLite (local/test fallback)
```

## 3. Database tables

- `users`
- `skills`
- `skill_prerequisites`
- `lessons`
- `lesson_blocks`
- `source_works`
- `lesson_sources`
- `exercises`
- `exercise_versions`
- `attempts`
- `attempt_errors`
- `lesson_progress`
- `review_items`
- `review_states`
- `review_attempts`

### Why exercise versions are mandatory

An `attempt` points to `exercise_version_id`, not only `exercise_id`. If the grader/rubric or wording changes later, historic evidence remains traceable to the exact contract that produced it.

## 4. Lesson 1 migration

`L01 — Nốt, quãng và cấu trúc hợp âm` is now backend-owned and contains:

- 5 lesson blocks;
- 6 exercises;
- 8 active-recall review items;
- 2 source mappings.

The runtime frontend no longer imports Lesson 1 from `frontend/src/content/lessons.ts`. That file is retained only as a temporary migration source for Lessons 2–8.

## 5. Learning API contract

### List lessons

`GET /api/v1/lessons`

Returns only public lesson metadata and real migrated counts.

### Lesson detail

`GET /api/v1/lessons/L01`

Returns:

- objectives;
- lesson blocks;
- source references;
- exercise prompts/options/version IDs;
- review items.

It intentionally does **not** return quiz `answer_key` or `grader_config`.

### Submit attempt

`POST /api/v1/attempts`

```json
{
  "user_id": "demo-user",
  "exercise_version_id": "L01-Q02-v1",
  "answer": "C E G"
}
```

The persisted exercise contract selects one of:

- `exact`;
- `music_engine`;
- deterministic `rubric`.

Assessment evidence is written to `attempts` and `attempt_errors`.

### Complete lesson

`POST /api/v1/lessons/L01/complete`

```json
{"user_id":"demo-user"}
```

This writes/updates `lesson_progress` and idempotently activates all review items for the lesson.

### Review queue

`GET /api/v1/review/due?user_id=demo-user`

For development inspection of future cards:

`GET /api/v1/review/due?user_id=demo-user&include_future=true`

### Answer a review item

`POST /api/v1/review/L01-F01/answer`

```json
{
  "user_id": "demo-user",
  "answer": "M3",
  "rating": "auto",
  "response_time_ms": 1800
}
```

MVP scheduler:

- new card: 1 day;
- successful auto/good review: next stage 3, 7, 14, 30 days;
- `again` or incorrect: reset to 1 day;
- `hard`: hold stage;
- `easy`: advance two stages where possible.

Review state remains separate from future mastery scoring.

## 6. Music contract

`GET /api/v1/music/chords/G7?key=C`

Example semantics:

```json
{
  "symbol": "G7",
  "quality": "7",
  "formula": ["1", "3", "5", "b7"],
  "notes": ["G", "B", "D", "F"],
  "context": {"key": "C", "roman": "V7", "function": "dominant"}
}
```

This is the first backend contract for the future `ChordInspector`. LLM output is not used to calculate chord tones.

## 7. Database setup

### Quick local SQLite

By default:

```bash
cd backend
uvicorn app.main:app --reload
```

creates `harmonymentor_dev.db`, schema, and demo seed data.

### PostgreSQL target

```bash
docker compose up -d postgres
cd backend
export DATABASE_URL='postgresql+psycopg://harmonymentor:harmonymentor@127.0.0.1:5432/harmonymentor'
export AUTO_CREATE_SCHEMA=0
alembic -c alembic.ini upgrade head
uvicorn app.main:app --reload
```

`AUTO_CREATE_SCHEMA=1` exists only to reduce friction during Phase 0 local development. Migration-driven schema management should be used for shared/production-like environments.

## 8. Verification performed

Backend regression + contract suite:

```text
101 passed, 1 skipped
```

The skipped test is the pre-existing optional `music21` cross-check when that package is unavailable.

Alembic was verified with:

```text
upgrade head -> downgrade base -> upgrade head
PASS
```

Frontend package installation could not be completed in this execution environment; therefore a full Vite production build is not claimed. Source is additionally syntax-transpiled in the handoff verification.

## 9. Phase gate

Phase 0.3–0.4 is considered complete when:

- legacy Practice endpoints remain green;
- schema migration is reversible;
- lesson list/detail come from backend;
- quiz answers are not leaked in lesson API;
- an L01 attempt is persisted and graded;
- L01 completion activates 8 review states idempotently;
- a correct review advances 1 -> 3 days;
- an incorrect review resets to 1 day.

All of these conditions are covered by automated tests.

## 10. Next phase

Proceed to **Phase 1 — Learning Platform vertical slice**:

1. migrate Lessons 2–4 first (then 5–8);
2. create real checkpoint state and lesson progress UI;
3. add mastery evidence aggregation after enough exercise contracts exist;
4. build reusable `ChordInspector` UI against `/api/v1/music/chords/{symbol}`;
5. then begin Piano + audio + notation.
