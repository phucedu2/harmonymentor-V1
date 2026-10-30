# HarmonyMentor AI — hướng dẫn cho Claude Code

Nền tảng học nhạc lý thích ứng (Học → Luyện tập → Chẩn đoán → Sáng tác → Chơi nhạc), có AI Tutor và Composition Lab. Đồ án nhóm 3 người, bám **bộ tài liệu thiết kế bản 2.1** (`docs/SRS/`: 01 SRS, 02 Đặc tả chức năng và nghiệp vụ, 03 Thiết kế tổng quan, 04 Thiết kế chi tiết; mỗi file có bản `.docx` gốc và bản `.md` để trích dẫn). Hạn nộp **04/12/2026**; CP1 20/10 (Engine + phân loại bài tập), CP2 03/11 (HitRate@5/Precision@5), CP3 10/11 (AI Tutor có trích dẫn).

Phân công: **Thắng** Backend/Engine · **Phúc** Frontend/Audio · **Đạt** AI/NLP/DevOps.

## Đọc trước khi làm

0. `docs/SRS/01..04_*.md`: bộ tài liệu 2.1, nguồn sự thật. Tài liệu khác code thì tài liệu thắng, trừ Music Engine (đổi Engine cần test mới + ADR).
1. `docs/PROMPT_CLAUDE_CODE.md`: prompt chính (vai trò, mâu thuẫn N1–N9, lộ trình Giai đoạn A–F).
2. `docs/giai-doan/phase-A/PHASE_A_PLAN.md`: hiện trạng, quyết định N1–N15, ERD, route, thiết kế, lịch.
3. `docs/giai-doan/phase-A/PHASE_A_TRUY_VET_FR.md`: trạng thái từng FR.
4. `docs/decisions/ADR-*.md`: quyết định đã ghi.

## Lệnh

```bash
# Backend (Python 3.11+)
cd backend && pip install -r requirements.txt
pytest -q                          # 30/10/2026 (HM-012): 337 passed + 21 skipped (21 test PostgreSQL cần TEST_DATABASE_URL)
uvicorn app.main:app --reload      # http://127.0.0.1:8000/docs

# Frontend (Node 22, giống Dockerfile và CI)
cd frontend && npm ci
npm run dev                        # http://localhost:5173, proxy /api → :8000
npm run build                      # phải đạt trước khi gộp

# Toàn bộ hệ thống (Docker)
cp .env.example .env && docker compose up --build   # http://localhost:5173

# Alembic
cd backend && alembic -c alembic.ini upgrade head && alembic -c alembic.ini check
```

CI (`.github/workflows/ci.yml`, xem `docs/CI.md`) chạy trên mọi PR vào `main`: pytest SQLite (0 skip, ≥ 337 đạt), PostgreSQL 16 + pgvector (`alembic upgrade head` + `check`, 21 test HM-010 + migration PR-3, 0 skip), `npm ci && npm run build`. Thêm test mới thì nâng mức `--min-passed` trong `ci.yml`.

## Cấu trúc

```
backend/app/music_engine/   Engine nhạc lý thuần Python, tất định, KHÔNG import DB
backend/app/api/            router FastAPI hiện có (engine, music, lessons, attempts, review, learning)
backend/app/services/       grading_service, learning_service, review_scheduler
backend/app/content/        skill graph, đặc tả bài học, seed (sẽ chuyển sang content/*.yaml, N5)
backend/app/db/             models SQLAlchemy, session, seed
backend/migrations/         Alembic (2 migration gốc, không sửa)
backend/tests/              pytest
content/                    nội dung bài học (đích: YAML + Markdown, FR-ADM-39)
frontend/src/               React 18 + TS + Vite (pages/, components/learning/)
docs/                       SRS, kế hoạch, ADR, minh chứng CP
docs/giai-doan/             báo cáo + kiểm chứng theo từng giai đoạn (mục lục: README.md)
```

Module mới đặt theo SRS 10.4: `backend/app/{auth,learning,recommender,nlp,exercise,ai,composition,admin}/` (N8).

## Nguyên tắc bất biến

1. Music Engine là nguồn sự thật duy nhất về nốt/quãng/hợp âm/giọng. Frontend và LLM không tự tính nhạc lý (ví dụ Ebm7b5 → Eb Gb Bbb Db qua `get_chord_tones`).
2. Đầu ra có cấu trúc của AI qua JSON schema và Music Engine; sai thì thử lại 1 lần rồi dùng dự phòng theo luật.
3. `AI_ENABLED=false` vẫn demo được trọn vòng.
4. Dữ liệu cá nhân lọc theo `user_id` từ token; tài nguyên người khác → 404; `/admin/*` với người học → 403.
5. AI chỉ gợi ý (xem trước → chấp nhận/từ chối), không tự sửa dự án.
6. Sáng tác lưu dạng ký hiệu, thời gian theo phách.
7. Xóa mềm (`deleted_at`) cho nội dung và dự án.
   Phiên bản câu hỏi đã phát hành là bất biến: sửa đề/đáp án/cách chấm/nguồn thì tăng `version` trong `curriculum_specs.q()`, bỏ câu thì `retired=True` (ADR-006).
8. Lượt làm của Admin có `is_test=true`, không tính mastery/thống kê.
9. Người học mô phỏng có `is_synthetic=true`, không đăng nhập, loại khỏi dashboard.
10. Không `TODO`, code giả, dữ liệu cứng để "trông như chạy". Chưa xong thì ghi rõ.
11. Giữ nguyên provenance (nguồn) của từng câu hỏi/thẻ; không chép nguyên bài tập có bản quyền.

## Quy ước làm việc

- Mỗi giai đoạn một nhánh `phase-<chữ>-<ten-ngan>`, commit nhỏ kiểu `feat(auth): …`, gộp vào `main` qua PR khi nhóm duyệt. Không commit `.env` hay API key.
- Đọc file trước khi sửa. Không đổi hành vi Engine nếu không có test mới + ADR.
- Chạy `pytest` và `npm run build` thật, dán kết quả; không chạy được thì ghi "chưa chạy" và lý do.
- Báo cáo triển khai và file kiểm chứng của giai đoạn đặt ở `docs/giai-doan/<giai-doan>/`, thêm một dòng vào `docs/giai-doan/README.md`.
- Quyết định không hiển nhiên ghi `docs/decisions/ADR-xxx.md`. Ghi việc dùng AI vào `docs/AI_USAGE.md`.
- Comment/docstring tiếng Việt, ngắn, giải thích "vì sao". Giao diện tiếng Việt, ký hiệu nhạc quốc tế.
- Cuối mỗi giai đoạn: dừng và báo cáo (đã làm gì theo FR, file, lệnh, kết quả test, giải thích cho nhóm, rủi ro/câu hỏi).
