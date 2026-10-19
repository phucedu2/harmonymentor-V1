# HarmonyMentor AI — Phase 1 Learning Vertical Slice (`v0.4.0-dev`)

HarmonyMentor đang được chuyển từ Music Engine prototype sang learning platform có **source-grounded curriculum**, persistence và assessment/review contract có thể truy nguyên.

Phase 1 giữ nguyên nền curriculum đã audit ở Phase 0.4B và biến Lessons 1–4 thành một learning vertical slice: **lesson renderer → inline checkpoints → persisted quiz attempts → lesson progress → ChordInspector → completion → spaced review queue**.

## Trạng thái hiện tại

Đã có:

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

Chưa có:

- mastery/recommendation aggregation;
- runtime migration của Lessons 5–8;
- interactive Piano, Tone.js, VexFlow;
- audio-recognition exercise implementation;
- Harmony Assistant/LLM;
- production auth.

## Nguồn curriculum

Canonical registry: `backend/app/content/source_registry.py`.

- `OMT_V2` — Open Music Theory v2: foundation, tonicization/modal mixture, jazz basics, Pop concepts.
- `FANK_WIH` — Working in Harmony: academic cross-check cho fundamentals/diatonic/chromatic harmony/voice leading. Exact current PDF page locators chưa khóa trong Phase 0.4B.
- `TEREFENKO_WB` — Jazz Theory Workbook: pedagogical reference cho keyboard realization, ear training, ii–V–I, chord-scale, voicing và progression practice.
- `KHAIHOAN_JAZZ` — Trần Khải Hoàn: Vietnamese reference cho function, tensions, secondary dominants, modal interchange và jazz voicing.

Các quiz/flashcard trong source là **nội dung biên soạn mới**. Không copy nguyên proprietary exercise, score hoặc answer key.

## Source of truth

Từ Phase 0.4B:

```text
backend/app/content/source_registry.py   # source policy/registry
backend/app/content/skill_graph.py       # 26 skills + prerequisite DAG
backend/app/content/curriculum_specs.py  # canonical 8 lessons / 48 quiz / 64 review items
backend/app/content/seed_data.py         # runtime DB migration/seed
content/curriculum/*.json                # generated reviewable snapshots
```

`frontend/src/content/lessons.ts` đã được deprecate và **không còn là source of truth**.

## Runtime migration status

```text
L01 Foundation                         reviewed / DB runtime
L02 Major Scale & Seventh Chords      reviewed / DB runtime
L03 Harmonic Function                 reviewed / DB runtime
L04 ii–V–I & Voice Leading            reviewed / DB runtime
L05 Secondary Dominants               source_audited spec only
L06 Modal Interchange                 source_audited spec only
L07 Tensions / Modes / Chord-Scale    source_audited spec only
L08 Jazz Piano Voicing                source_audited spec only
```

Mỗi lesson runtime L01–L04 có:

- 7 blocks (5 content + 2 checkpoint);
- 6 quiz/exercises;
- 8 review items;
- source locators;
- skill mapping.

L01 audited exercise versions là `v2` để không giả mạo provenance cho version cũ. L02–L04 bắt đầu ở audited `v1`.

## Learning contract

Flow hiện chạy được cho Lessons 1–4:

```text
GET lesson content
  ↓
POST quiz attempt
  ↓
ExerciseVersion + source provenance
  ↓
persist Attempt + AttemptError
  ↓
complete lesson
  ↓
activate 8 ReviewState
  ↓
answer review
  ↓
1 → 3 → 7 → 14 → 30 days
```

`mastery` và `review due` vẫn là hai khái niệm riêng. Mastery aggregation sẽ chỉ bật sau khi skill evidence đủ tin cậy.

## Database schema

Các bảng hiện tại:

```text
users
skills
skill_prerequisites
lessons
lesson_blocks
source_works
lesson_sources
exercises
exercise_versions
attempts
attempt_errors
lesson_progress
review_items
review_states
review_attempts
```

Migration:

```text
097c446166e1  initial learning contract
c84d7c4b190a  item-level source provenance
```

Nếu bạn đã chạy bản v0.3.0 bằng SQLite `AUTO_CREATE_SCHEMA=1`, DB local cũ có thể chưa có bảng `alembic_version`. Cách đơn giản nhất trong development là xóa `backend/harmonymentor_dev.db` và chạy lại. Nếu cần giữ dữ liệu local cũ, xác nhận schema đúng với migration đầu rồi chạy:

```bash
alembic -c alembic.ini stamp 097c446166e1
alembic -c alembic.ini upgrade head
```

Không dùng `stamp` mù trên database production không rõ lịch sử.

## API chính

### Curriculum / Learning

```text
GET  /api/v1/lessons
GET  /api/v1/lessons/{lesson_id}
POST /api/v1/lessons/{lesson_id}/start
POST /api/v1/lessons/{lesson_id}/complete
GET  /api/v1/learning/overview?user_id=demo-user
```

### Assessment evidence

```text
POST /api/v1/attempts
```

Attempt luôn trỏ tới `exercise_version_id`, không chỉ `exercise_id`.

### Review

```text
GET  /api/v1/review/due
POST /api/v1/review/{review_item_id}/answer
```

### Music / ChordInspector contract

```text
GET /api/v1/music/chords/inspect?symbol=G7&key=C
GET /api/v1/music/chords/inspect?symbol=C%2FE&key=C
```

### Legacy Practice API

Các endpoint cũ vẫn giữ dưới `/api/v1/engine/*` trong quá trình migration.

## Chạy nhanh — SQLite local

Python 3.11+ và Node.js 18+.

**Terminal 1 — backend**

```bash
cd backend
pip install -r requirements.txt
pytest -q
uvicorn app.main:app --reload
```

Nếu chưa có DB, app local tạo schema và seed `demo-user` + curriculum runtime L01–L04.

Đăng nhập (Giai đoạn B): mọi route có dữ liệu cá nhân cần Bearer token (ADR-004); đăng ký tài khoản ở trang `/dang-ky` của frontend. Tạo tài khoản quản trị:

```bash
cd backend
python -m app.seed_admin --email admin@example.com   # hỏi mật khẩu, hoặc đặt biến ADMIN_PASSWORD
```

Biến môi trường xem ở [`.env.example`](.env.example). Không đặt `JWT_SECRET` thì môi trường dev dùng khóa tạm (khởi động lại là access token cũ hết hạn, refresh cookie vẫn lấy lại phiên); `APP_ENV=production` bắt buộc có khóa.

Nếu bạn có file `backend/harmonymentor_dev.db` tạo trước Giai đoạn B, backend sẽ báo thiếu cột `users.email`: xóa file đó để tạo lại.

API docs: `http://127.0.0.1:8000/docs`

**Terminal 2 — frontend**

```bash
cd frontend
npm install
npm run dev
```

Vite proxy `/api` sang FastAPI ở cổng 8000.

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
191 passed   (Giai đoạn B, 19/10/2026; cũng đạt trên PostgreSQL 16)
```

Nếu không cài được `music21`, bộ đối chiếu music21 bị bỏ qua và số test sẽ ít hơn (ví dụ 113 passed, 1 skipped ở bản v0.4.0 gốc trước khi thêm test CP1).

Alembic đã kiểm tra:

```text
fresh DB: upgrade head → alembic check → downgrade base → upgrade head  PASS
legacy v0.3 local schema: stamp initial → upgrade provenance migration   PASS
```

Runtime vẫn giữ:

```text
8 lessons
26 skills
36 prerequisite edges
24 runtime exercises (L01–L04)
32 runtime review items (L01–L04)
L01-L04: 7 lesson blocks each, trong đó 2 checkpoint blocks
```

Frontend: `cd frontend && npm ci && npm run build` **đạt** (Node 22, kiểm tra ngày 19/10/2026, nhánh `phase-b-frontend`).

## Tài liệu phase

- `docs/CURRICULUM_SOURCE_MATRIX.md`
- `docs/SKILL_GRAPH.md`
- `docs/LESSON_SPECIFICATIONS.md`
- `docs/PHASE_0_4B_IMPLEMENTATION.md`
- `docs/PHASE_1_IMPLEMENTATION.md`
- `docs/PHASE_A_PLAN.md`, `docs/PHASE_A_TRUY_VET_FR.md` (kế hoạch và truy vết FR hiện hành)
- `docs/CP1_*.md` (minh chứng CP1)
- `docs/VERIFICATION_PHASE_1.txt`
- `docs/VERIFICATION_PHASE_0_4B.txt`
- các phase trước vẫn giữ để audit lịch sử.

## Bước tiếp theo

Kế hoạch hiện hành là **Giai đoạn B–F** trong [`docs/PHASE_A_PLAN.md`](docs/PHASE_A_PLAN.md) (thay cho mục "Phase 2 — Interactive Music Layer" cũ). Hướng dẫn cho Claude Code nằm ở [`CLAUDE.md`](CLAUDE.md).
