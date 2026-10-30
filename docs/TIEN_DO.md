# Tiến độ

File này ghi lại việc đã xong, việc đang dở, lệnh để chạy lại và việc tiếp theo. Cập nhật sau mỗi phiên việc. Lịch sử trước 27/10/2026 xem `docs/AI_USAGE.md` và các báo cáo trong `docs/giai-doan/`.

## 30/10/2026: logo chính thức "Cuộn I–IV–V–I"

**Đã xong** (nhánh `claude/project-thread-82ijft`, PR vào `main`, chưa gộp)
- Thay logo ♪ bằng logo nhóm chọn (ADR-007): `frontend/src/components/brand/HarmonyMentorLogo.tsx`, `Logo.tsx` giữ nguyên prop `to`.
- Favicon SVG/ICO, apple-touch-icon, icon 192/512, `site.webmanifest` trong `frontend/public/`; tiêu đề tab "Harmony Mentor".
- `docs/thuong-hieu/`: BRAND_NOTE, file logo SVG, script dựng lại. Ảnh trước/sau trong `docs/minh-chung/anh/logo-*.png`.

**Việc tiếp theo**
- Nhóm quyết có đổi các chữ "HarmonyMentor" còn lại sang "Harmony Mentor" không, và khi nào áp bảng màu Đồng & Gỉ cho toàn app.

**Lệnh chạy lại**
```bash
cd frontend && npm ci && npm run build
cd docs/thuong-hieu/_nguon && npm install && bash build.sh   # dựng lại logo (cần Python: fonttools, cairosvg, pillow)
```

## 30/10/2026: gom tài liệu phase vào `docs/giai-doan/`

**Đã xong** (nhánh `claude/project-thread-ng2frm`, PR vào `main`, chưa gộp)
- Theo góp ý của thầy: 10 file `PHASE_*.md`, 7 file `VERIFICATION_PHASE_*.txt` và 2 bản kiểm định chuyển bằng `git mv` vào `docs/giai-doan/<giai đoạn>/`, giữ nguyên tên. Mục lục `docs/giai-doan/README.md`.
- Sửa mọi đường dẫn cũ trong CLAUDE.md, README, AI_USAGE, ADR-003, `docs/prompts/`, `PROMPT_CLAUDE_CODE.md`, 1 test backend và 2 comment frontend. Không đổi code chạy.

**Việc tiếp theo**
- Giai đoạn mới đặt báo cáo + kiểm chứng vào `docs/giai-doan/<giai đoạn>/` và thêm một dòng vào mục lục.

## 27/10/2026: PR-3, bảo vệ phiên bản câu hỏi (HM-003)

**Đã xong** (nhánh `claude/project-thread-3z96i1`, Draft PR, chưa gộp)
- Migration `d3a7f1c2e905` (nối vào `b2c4e6f80a13`): ảnh chụp đề/lựa chọn/loại câu/cách chấm trên `exercise_versions`, `status` draft/published, `content_hash`, `snapshot_origin`, `exercises.deleted_at`; khôi phục ảnh chụp bản cũ từ git khi khớp nguồn; trigger PostgreSQL; `downgrade` từ chối chạy.
- Seed không ghi đè, không tự tăng version, báo `SeedConflictError` và rollback; `q(status=, retired=)`; `SHOW_DRAFT_CONTENT`.
- Chấm theo ảnh chụp của phiên bản; nộp vào bản cũ trả 409 `EXERCISE_VERSION_SUPERSEDED`; frontend tải lại bài.
- 50 test mới: 38 chạy trên SQLite, 12 chỉ chạy trên PostgreSQL (bị bỏ qua khi không có TEST_DATABASE_URL). ADR-006. Báo cáo `docs/bao-cao/PR3_IMPLEMENTATION_REPORT.md`.

**Đang dở / chờ**
- Nhóm duyệt Draft PR. Thắng ký D-2, D-4; Đạt ký D-1, D-3 (ADR-006).
- SQLite dev cũ (`backend/harmonymentor_dev.db`) thiếu cột mới: xóa file để tạo lại. CSDL Docker: `alembic upgrade head` tự chạy khi khởi động; nên `pg_dump` trước.

**Lệnh chạy lại**
```bash
cd backend && pytest -q                                   # 325 passed, 21 skipped
TEST_DATABASE_URL=postgresql+psycopg://hm_ci:ci_only_not_secret@127.0.0.1:5432/harmony_test pytest -m postgres   # 21 passed
alembic -c alembic.ini upgrade head && alembic -c alembic.ini check
cd frontend && npm ci && npm run build
```

**Việc tiếp theo**
- PR-4 (14 nhóm kỹ năng + 12 bài), PR-5 (mastery EMA đọc `attempts.correct` đã lưu, không chấm lại), PR-6 (câu nháp `status="draft"`).

## 27/10/2026: PR-2, CI GitHub Actions

**Đã xong**
- `.github/workflows/ci.yml` có 3 job: backend SQLite (281 test, 0 skip), backend PostgreSQL 16 + pgvector (`alembic upgrade head` + `alembic check` + 9 test đồng thời HM-010, 0 skip), frontend (`npm ci` + `npm run build`). Chi tiết ở `docs/CI.md`.
- `scripts/ci/kiem_junit.py`: báo đỏ khi có skip, vì pytest trả mã 0 khi mọi test bị skip.
- Đã chứng minh CI báo đỏ bằng một PR phụ (#10), sau đó đã đóng PR này.
- Báo cáo: `docs/bao-cao/PR2_CI_REPORT.md`.

**Đang dở / chờ**
- Chờ Phúc và Astra duyệt PR #9 (Draft). Chưa gộp.
- Sau khi gộp, Phúc bật "Require status checks" cho `main` (hướng dẫn trong `docs/CI.md`).

**Lệnh chạy lại**
```bash
cd backend && pytest -q -m "not postgres"        # 281 passed
TEST_DATABASE_URL=postgresql+psycopg://hm_ci:ci_only_not_secret@127.0.0.1:55432/harmony_test pytest -m postgres   # 9 passed
cd frontend && npm ci && npm run build
```

**Việc tiếp theo (chờ Phúc duyệt từng PR)**
- PR-3 trở đi theo kế hoạch sửa đổi 26/10: ExerciseVersion (HM-003), mastery EMA, hệ gợi ý CP2.
