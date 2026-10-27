# Tiến độ

File này ghi lại việc đã xong, việc đang dở, lệnh để chạy lại và việc tiếp theo. Cập nhật sau mỗi phiên việc. Lịch sử trước 27/10/2026 xem `docs/AI_USAGE.md` và các báo cáo `docs/PHASE_*`.

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
