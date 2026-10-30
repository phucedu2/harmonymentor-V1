# HarmonyMentor AI - Phase 2 Interactive Music Layer (`v0.5.3-dev`)

HarmonyMentor is evolving from a deterministic music-theory prototype into a source-grounded learning platform. Phase 2 adds the first interactive music layer and also fixes a pedagogical problem found during Phase 1 testing: Lessons 1-4 were structurally complete but too compressed for a true beginner.

## What changed in Phase 2

### 1. Beginner content hardening

Lessons 1-4 teach prerequisite vocabulary before assessing it. Phase 2.3 hardens Lesson 1 after browser testing showed that the previous version still over-relied on C-only examples and did not make interval-quality relationships explicit enough.

- Lesson 1 now begins with the physical piano layout, explicitly teaches that **E-F and B-C have no black key between them**, and defines semitone / whole tone before interval arithmetic.
- The spelling section first explains the everyday idea (one piano key can have two names) and only then introduces the terms `enharmonic` and `spelling`.
- Interval quality is taught as two families: `P` for 1/4/5/8 and the `m↔M` pair for 2/3/6/7, with an explicit `d ← standard → A` visual spectrum. Lesson 1 still practices only `M3`, `m3`, `P5`, `d5`, while `A5` appears only to explain augmented triads.
- Triads are built in two steps: choose the correct letter frame (C-E-G, D-F-A...) and then apply interval formulas. A shared 12-root selector updates interval examples, triad spelling, piano highlighting, notation, and audio; the lesson adds a tiered overview of 12 major + 12 minor tonic triads.
- The parallel comparison now keeps root C throughout: C major, C minor, C diminished.
- Free-response placeholders show format only and never reveal the current answer. Checkpoints use non-C examples and provide optional randomized practice across 12 roots / 24 major-minor tonic triads.
- Lesson 2 defines whole step vs half step, major-scale pattern, seventh-chord symbols, Roman numerals, and key/tonic context.
- Lesson 3 separates chord structure from harmonic function and defines tonic, predominant/subdominant, dominant, and progression.
- Lesson 4 defines ii-V-I, guide tones, voice leading, common tone, and voicing before keyboard work.

Nền tảng có từ trước (v0.4.0, CP1, Giai đoạn A–B):

- Music Theory Engine Python thuần (`backend/app/music_engine/`);
- regression fixes của Phase 0.2;
- FastAPI modular routers;
- SQLAlchemy 2 + Alembic;
- PostgreSQL target qua `DATABASE_URL`, SQLite fallback cho local/test;
- canonical source registry cho Open Music Theory, Working in Harmony, Terefenko Workbook và Trần Khải Hoàn;
- **26 skills + 36 prerequisite edges** trong Skill Graph;
- **8 lesson specifications** đã source-audit;
- **48 quiz + 64 flashcard/review item** đã viết lại, mỗi item có skill + grader contract + provenance;
- **Lessons 1–4** chạy thành learning vertical slice: theory blocks → 2 inline checkpoints → final quiz → progress → completion → review queue;
- Lessons 5–8 giữ ở mức `source_audited` specification, chưa đưa vào runtime exercise bank;
- versioned `ExerciseVersion` và persisted `Attempt`;
- item-level source provenance trong audited `ExerciseVersion` và `ReviewItem`;
- flashcard/review state theo mốc 1–3–7–14–30 ngày;
- backend contract cho `ChordInspector`;
- frontend `Dashboard / Learn / Practice / Composition Lab / Progress` (Giai đoạn B: thêm trang chủ, đăng nhập/đăng ký, route `/app/*`);
- `LearningOverview` tổng hợp LessonProgress + Attempt + ReviewState;
- ChordInspector UI tái sử dụng trong progression blocks;
- Dashboard/Learn/Progress đọc state thật từ backend;
- Learn runtime đọc lesson content từ Content Service thay vì TypeScript draft.

### 2. Virtual Piano V2

`frontend/src/components/music/VirtualPiano.tsx`

- click/tap playback;
- octave-aware scientific pitch names;
- optional note selection;
- target/error highlighting;
- black-key enharmonic labels such as `C#/Db`;
- explicit separation between sounding pitch and spelling-sensitive grading.

The legacy Practice page now reuses the same piano component. `frontend/src/Piano.tsx` stays as the small display-only SVG keyboard for the public home page.

### 3. Tone.js AudioEngine

`frontend/src/audio/AudioEngine.ts`

Current MVP capabilities:

- play a single note;
- play a chord;
- schedule chord progressions;
- BPM control;
- metronome;
- shared transport cleanup.

The current sound source is a Tone.js `PolySynth` fallback so the interaction works without shipping unverified audio assets. A self-hosted licensed piano sample set can replace this through a later sampler increment without changing lesson contracts.

### 4. VexFlow notation blocks

`frontend/src/components/music/NotationStaff.tsx`

Phase 2 supports simple SVG notation examples for:

- intervals;
- triads/seventh-chord examples;
- guide-tone examples.

The renderer is intentionally narrow. It is not a score editor.

### 5. Reusable music lesson blocks

`LessonRunner` now understands:

```text
THEORY
CALLOUT
GLOSSARY
NOTATION
PROGRESSION
PIANO
AUDIO
CHECKPOINT
SUMMARY
```

This keeps interactive music features data-driven instead of hard-coding a unique React page for every lesson.

### 6. ChordInspector audio

ChordInspector still obtains deterministic chord facts from the backend Music Theory Engine. Phase 2 adds audio preview while retaining:

- chord tones;
- formula;
- slash-bass information;
- Roman numeral/function when a key is provided.

## Runtime curriculum status

```text
L01 Foundation                    reviewed / runtime / Phase 2 enriched
L02 Major Scale & Seventh Chords reviewed / runtime / Phase 2 enriched
L03 Harmonic Function            reviewed / runtime / Phase 2 enriched
L04 ii-V-I & Voice Leading       reviewed / runtime / Phase 2 enriched
L05 Secondary Dominants          source_audited spec only
L06 Modal Interchange            source_audited spec only
L07 Tensions / Chord-Scale       source_audited spec only
L08 Jazz Piano Voicing           source_audited spec only
```

Current block counts for the runtime lessons:

```text
L01 12 blocks
L02 10 blocks
L03  9 blocks
L04 11 blocks
```

The assessment bank remains 48 quiz items and 64 review items across the eight audited specifications. Only L01-L04 are runtime-migrated.

## Curriculum sources

Canonical source policy remains in `backend/app/content/source_registry.py`.

- Open Music Theory v2: foundation, functional basics, jazz basics, and Pop concepts.
- Working in Harmony: academic cross-check for fundamentals, diatonic/chromatic harmony, and voice leading.
- Terefenko Jazz Theory Workbook: keyboard, ear-training, ii-V-I, chord-scale, voicing, and practice design.
- Tran Khai Hoan: Vietnamese jazz-harmony reference for function, tensions, secondary dominants, modal interchange, and voicing.

The canonical lesson data is `backend/app/content/curriculum_specs.py`. `content/curriculum/lesson_specs.json` is a generated review snapshot.

## Dependencies added in Phase 2

Frontend `package.json` now includes:

```text
tone 15.1.22
vexflow 5.0.0
```

`package-lock.json` was regenerated with these dependencies when v0.5.3 was merged into `main` (20/10/2026); use `npm ci`.

## Run locally

Lần đầu clone và **sau mỗi lần `git pull`** (tắt uvicorn trước), từ thư mục gốc repo:

```bash
python scripts/reset_dev.py           # pip install, alembic upgrade head, npm ci
python scripts/reset_dev.py --fresh   # sao lưu DB dev rồi tạo mới hoàn toàn
```

Script giữ dữ liệu trong `backend/harmonymentor_dev.db` nếu DB do Alembic quản lý. DB tạo bằng `create_all` (không có version trong `alembic_version`) thì không nâng cấp được, nội dung bài học kẹt ở bản cũ: script sao lưu thành `harmonymentor_dev.db.bak-<thời điểm>` rồi tạo lại.

Backend:

```bash
cd backend
pytest -q                          # chạy trên SQLite tạm riêng, không đụng DB dev
uvicorn app.main:app --reload
```

Schema chỉ do Alembic tạo (`AUTO_CREATE_SCHEMA` mặc định `0`); khi khởi động, app seed curriculum runtime vào DB đã migrate.

Đăng nhập (Giai đoạn B): mọi route có dữ liệu cá nhân cần Bearer token (ADR-004); đăng ký tài khoản ở trang `/dang-ky` của frontend. Tạo tài khoản quản trị:

```bash
cd backend
python -m app.seed_admin --email admin@example.com   # hỏi mật khẩu, hoặc đặt biến ADMIN_PASSWORD
```

Biến môi trường xem ở [`.env.example`](.env.example). Không đặt `JWT_SECRET` thì môi trường dev dùng khóa tạm (khởi động lại là access token cũ hết hạn, refresh cookie vẫn lấy lại phiên); `APP_ENV=production` bắt buộc có khóa.

Nếu backend báo thiếu bảng/cột (ví dụ `users.email`) hoặc nội dung bài học cũ hơn code: chạy `python scripts/reset_dev.py`.

API docs: `http://127.0.0.1:8000/docs`

Frontend:

```bash
cd frontend
npm run build
npm run dev
```

The browser must receive a user gesture before Web Audio can start; clicking a piano/audio control provides that gesture.

Route frontend (Giai đoạn B): `/` trang chủ, `/dang-nhap`, `/dang-ky`, `/app` (tổng quan), `/app/hoc`, `/app/luyen-tap`, `/app/tien-do`, `/app/composition`, `/app/ho-so`, `/admin`. Mọi trang `/app/*` cần đăng nhập theo hợp đồng `docs/decisions/ADR-004-hop-dong-xac-thuc.md`; khi backend chưa có `/api/v1/auth/*` thì chỉ trang chủ dùng được.

## Chạy toàn bộ bằng Docker (Giai đoạn B)

Cần Docker Desktop (hoặc Docker Engine + Compose v2). Từ thư mục gốc repo:

```bash
cp .env.example .env          # rồi điền DB_PASSWORD (chuỗi bất kỳ), các biến khác để mặc định được
docker compose up --build
```

- Web: http://localhost:5173 (nginx phục vụ bản build Vite, chuyển `/api` sang dịch vụ `api` cùng origin).
- API docs: http://127.0.0.1:8000/docs (chỉ mở cho máy đang chạy).
- Tạo admin: `docker compose exec -e ADMIN_PASSWORD=<mật-khẩu> api python -m app.seed_admin --email admin@example.com`.
- Bảng độ trễ p95: `docker compose logs api --no-log-prefix | python scripts/p95.py`.
- Xóa sạch dữ liệu: `docker compose down -v`.

4 dịch vụ theo SRS 10.2: `db` (PostgreSQL 16 + pgvector, CSDL `harmony`), `redis` (bộ đếm khóa đăng nhập), `api` (chạy `alembic upgrade head` rồi uvicorn), `web` (nginx, cổng `5173:80`). `/health` trả 503 khi CSDL hoặc Redis lỗi; compose dùng nó để chờ `api` sẵn sàng rồi mới mở `web`.

## PostgreSQL target (chạy backend ngoài Docker)

```bash
docker compose up -d db        # cần mở cổng: thêm ports: ["127.0.0.1:5432:5432"] cho dịch vụ db
cd backend
export DATABASE_URL='postgresql+psycopg://harmony:<DB_PASSWORD>@127.0.0.1:5432/harmony'
export AUTO_CREATE_SCHEMA=0
alembic -c alembic.ini upgrade head
uvicorn app.main:app --reload
```

Trong môi trường shared/production-like, dùng Alembic (`AUTO_CREATE_SCHEMA=0`) thay vì `create_all`.

## Kiểm thử (cập nhật Giai đoạn A, 18/10/2026)

Backend trên fresh SQLite, đã cài đủ `requirements.txt` (gồm `music21`):

```text
326 passed, 21 skipped   (30/10/2026, thêm test reset_dev; 21 test PostgreSQL (HM-010 + migration PR-3) chạy khi có TEST_DATABASE_URL)
220 passed   (cũ: sau khi gộp v0.5.3 với Giai đoạn B, 20/10/2026; 191 passed trên PostgreSQL 16 ở Giai đoạn B)
```

CI GitHub Actions chạy lại toàn bộ trên mỗi PR, kể cả 21 test PostgreSQL; xem `docs/CI.md`.

Nếu không cài được `music21`, bộ đối chiếu music21 bị bỏ qua và số test sẽ ít hơn (ví dụ 113 passed, 1 skipped ở bản v0.4.0 gốc trước khi thêm test CP1).

Frontend: `cd frontend && npm ci && npm run build` **đạt** (Node 22, 20/10/2026, sau khi gộp v0.5.3 với Giai đoạn B; đã có `package-lock.json` mới gồm Tone.js và VexFlow).

## Tài liệu phase

Báo cáo và nhật ký kiểm chứng của từng giai đoạn nằm trong [`docs/giai-doan/`](docs/giai-doan/), mỗi giai đoạn một thư mục con; mục lục ở [`docs/giai-doan/README.md`](docs/giai-doan/README.md). Kế hoạch và truy vết FR của Giai đoạn A: `docs/giai-doan/phase-A/PHASE_A_PLAN.md`, `docs/giai-doan/phase-A/PHASE_A_TRUY_VET_FR.md`.

Đặc tả dùng chung giữ ở `docs/`:

- `docs/CURRICULUM_SOURCE_MATRIX.md`
- `docs/LESSON_SPECIFICATIONS.md`
- `docs/SKILL_GRAPH.md`
- `docs/CP1_*.md` (minh chứng CP1)

## Next implementation gate

Do not move directly to the AI assistant until Phase 2 receives a local browser smoke test. The next gate is:

1. `npm install && npm run build` on the project machine;
2. visually verify VexFlow notation and Virtual Piano layout;
3. verify browser audio + metronome interaction;
4. only then proceed to Harmony Lab and the composition/backing-track layer.


## Phase 2.1 hotfix

Fixed a VexFlow 5 `IncompleteVoice` crash in lesson notation blocks by using `Formatter.FormatAndDraw`, added local notation fallback handling, and wrapped the lesson runtime in a React error boundary so a visualization failure cannot blank the entire app.

## Phase 2.3 Multi-key Lesson 1 hardening

Lesson 1 now uses one shared root selection across its interval, triad, notation, piano, and audio explorers. The selector exposes all 12 pitch positions and an explicit enharmonic spelling choice for black-key roots. The new 24-key overview is deliberately presented as **tonic triads representing 12 major + 12 minor keys**; the full concept of key/scale remains Lesson 2 material. Random practice is formative only and does not update mastery in this MVP.

The interval-quality explanation also avoids treating “bright/dark” as the definition of Major/Minor. `Major` and `Minor` are taught first as interval sizes, with any listening-color description framed only as a tendency.

## Phase 2.2 Lesson 1 pedagogy rewrite

The Lesson 1 content contract was rewritten from a zero-beginner perspective after usability testing. The rewrite keeps the existing 8-lesson MVP architecture but turns L01 into a scaffolded sequence with continuous section numbering, early piano visualization, explicit spelling rules, interval formulas required by triad construction, parallel-root triad comparison, and format-aware answer inputs. L01 exercise versions are published as `v4` so earlier attempts remain traceable.

Kế hoạch hiện hành là **Giai đoạn B–F** trong [`docs/giai-doan/phase-A/PHASE_A_PLAN.md`](docs/giai-doan/phase-A/PHASE_A_PLAN.md) (thay cho mục "Phase 2 — Interactive Music Layer" cũ). Hướng dẫn cho Claude Code nằm ở [`CLAUDE.md`](CLAUDE.md).
