# CI (GitHub Actions)

File: `.github/workflows/ci.yml`. CI chạy khi mở hoặc cập nhật PR vào `main` (kể cả Draft), khi có push vào `main`, và khi bấm "Run workflow" trong tab Actions. Không cần secret nào.

## Ba job

| Job | Các bước | Đỏ khi |
|---|---|---|
| Backend (SQLite, toàn bộ test) | Python 3.11 → `pip install -r requirements.txt` → `pip freeze` → `python -m compileall` → `pytest -m "not postgres"` → `scripts/ci/kiem_junit.py` | có test sai/lỗi, có test bị skip, hoặc ít hơn 326 test đạt |
| Backend (PostgreSQL 16 + pgvector) | container tạm `pgvector/pgvector:pg16` → tạo CSDL `harmony_ci_migrate` → `alembic upgrade head` → `alembic check` → kiểm tra extension `vector` → `pytest -m postgres` → `kiem_junit.py` → kiểm tra không còn schema `hm_pgtest_*` | migration lỗi, model lệch migration, test HM-010 hoặc migration PR-3 sai, **bị skip**, ít hơn 21 test đạt, hoặc còn schema test sót lại |
| Frontend (npm ci + build) | Node 22 → `npm ci` → `npm run build` (`tsc -b` + `vite build`) | lỗi kiểu TypeScript hoặc lỗi build |

### Vì sao phải đếm skip

Test PostgreSQL tự bỏ qua khi thiếu `TEST_DATABASE_URL` hoặc khi URL không an toàn. Lúc đó pytest vẫn trả mã 0 (đã thử: `9 skipped`, mã thoát 0). Nếu chỉ dựa vào mã thoát, CI sẽ báo xanh dù không test nào chạy. Vì vậy `scripts/ci/kiem_junit.py` đọc file JUnit XML, đếm PASS/FAIL/ERROR/SKIP và báo đỏ khi có skip. Bảng số liệu hiện trong mục "Summary" của mỗi lượt chạy. File XML được lưu thành artifact `junit-backend-*`.

### An toàn CSDL

- Máy chủ PostgreSQL là container do GitHub tạo riêng cho từng lượt chạy, xong thì xóa. Không có CSDL thật hay dữ liệu người dùng nào.
- Hai CSDL tạm: `harmony_ci_migrate` (`DATABASE_URL`, cho migration) và `harmony_test` (`TEST_DATABASE_URL`, cho test). Vì hai CSDL khác nhau và tên CSDL test kết thúc `_test`, lớp bảo vệ trong `backend/tests/pg_test_db.py` (PR-1) cho phép chạy. Nếu ai đặt sai, test bị skip và CI đỏ.
- Mật khẩu `ci_only_not_secret` chỉ dùng cho container tạm này. Không dùng `JWT_SECRET`, `GEMINI_API_KEY` hay khóa thật nào.

## Khi thêm hoặc xóa test

Mức tối thiểu (`--min-passed 326` và `--min-passed 21` trong `ci.yml`) là số test đạt ngày 30/10/2026: 325 sau PR-3 (gồm 6 test sửa sau review; trước PR-3 là 281 và 9) cộng 1 test `test_reset_dev.py`. Khi thêm test thì nâng mức này trong cùng PR, để sau đó lỡ xóa test thì CI đỏ. Mức này không bao giờ được hạ để CI xanh.

## Chạy giống CI trên máy

```bash
cd backend
pytest -q -m "not postgres" --junitxml=../ket-qua-sqlite.xml
python ../scripts/ci/kiem_junit.py ../ket-qua-sqlite.xml --min-passed 326 --title "Backend SQLite"

# Cần PostgreSQL có pgvector, ví dụ: docker run -d -p 55432:5432 -e POSTGRES_USER=hm_ci \
#   -e POSTGRES_PASSWORD=ci_only_not_secret -e POSTGRES_DB=harmony_test pgvector/pgvector:pg16
TEST_DATABASE_URL=postgresql+psycopg://hm_ci:ci_only_not_secret@127.0.0.1:55432/harmony_test \
  pytest -m postgres -v --junitxml=../ket-qua-postgres.xml
python ../scripts/ci/kiem_junit.py ../ket-qua-postgres.xml --min-passed 21 --title "PostgreSQL HM-010 + PR-3"
```

## Bắt buộc CI xanh trước khi gộp (Phúc làm trên GitHub)

CI chỉ báo kết quả. Muốn GitHub **chặn** nút Merge khi CI đỏ thì chủ repo bật quy tắc bảo vệ nhánh. Làm sau khi PR-2 đã gộp, vì GitHub chỉ cho chọn những check đã từng chạy:

1. Repo → **Settings** → **Rules** → **Rulesets** → **New ruleset** → **New branch ruleset** (hoặc **Branches** → **Add branch protection rule**).
2. Target: nhánh `main` (Include default branch).
3. Bật **Require a pull request before merging**.
4. Bật **Require status checks to pass**, thêm 3 check: `Backend (SQLite, toàn bộ test)`, `Backend (PostgreSQL 16 + pgvector, Alembic, HM-010)`, `Frontend (npm ci + build)`.
5. Bật **Block force pushes**. Lưu.

Lưu ý: GitHub chỉ cho bật quy tắc bảo vệ nhánh trên repo riêng tư khi tài khoản có gói GitHub Pro/Team (gói Student Developer Pack có Pro miễn phí). Nếu không bật được, nhóm thống nhất quy ước: không gộp PR khi tab Checks còn đỏ.

## Chi phí

Repo riêng tư dùng phút chạy miễn phí của tài khoản (gói Free: 2.000 phút/tháng). Mỗi lượt khoảng 3 job × 1–3 phút. Push mới lên cùng PR sẽ hủy lượt cũ (`concurrency`).
