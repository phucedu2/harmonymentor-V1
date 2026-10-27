# Báo cáo PR-2: CI kiểm thử tự động (GitHub Actions)

Ngày: 27/10/2026. Người yêu cầu: Phúc. Người viết: Claude Code (cần Thắng và Phúc kiểm).

## 1. Nhánh, commit, PR

| Mục | Giá trị |
|---|---|
| Gốc | `main` = `9babc11` (merge PR #8, HM-010) |
| Nhánh | `claude/project-thread-aii440`. Hệ thống làm việc của Claude bắt dùng tên này, nên nhánh không theo quy ước `gd<số>-...` của nhóm |
| Draft PR | https://github.com/phucedu2/harmonymentor-V1/pull/9 (Draft, chưa gộp) |
| PR phụ chứng minh CI đỏ | https://github.com/phucedu2/harmonymentor-V1/pull/10 (đã đóng, không gộp) |
| Commit | `0320b7d` workflow + script · `6cd7c7f` nâng phiên bản action · `a423e28` tài liệu · commit cuối thêm file báo cáo này và nâng `upload-artifact` lên v6 (SHA ghi ở mô tả PR #9) |

## 2. Quyết định của Phúc (27/10, chọn A cả 8 câu)

1. Chứng minh test PostgreSQL chạy thật bằng cách đọc file JUnit trong CI. Code test không bị sửa.
2. Job SQLite không cho phép skip.
3. Phạm vi PostgreSQL: Alembic upgrade + check và 9 test HM-010. Chưa chạy cả bộ 281 test trên PostgreSQL.
4. Chứng minh CI đỏ bằng một PR phụ, sau đó đóng PR này.
5. Dùng Python 3.11 và Node 22. Giữ nguyên `requirements.txt`, nhưng in `pip freeze` ra log.
6. Kiểm tra cú pháp bằng `compileall` và `tsc`. Chưa thêm lint.
7. CI chạy khi có PR vào `main`, khi push vào `main` và khi bấm chạy tay. Không dùng Redis, không build Docker.
8. Cập nhật tài liệu kèm theo và viết hướng dẫn bật bắt buộc CI xanh.

## 3. File đã thay đổi

| File | Nội dung |
|---|---|
| `.github/workflows/ci.yml` (mới) | 3 job: `backend-sqlite`, `backend-postgres`, `frontend` |
| `scripts/ci/kiem_junit.py` (mới) | Đếm PASS/FAIL/ERROR/SKIP trong JUnit XML. Có skip hoặc thiếu test thì CI đỏ. Bảng số liệu ghi vào mục Summary của lượt chạy |
| `docs/CI.md` (mới) | Cách CI hoạt động, an toàn CSDL, cách chạy giống CI trên máy, hướng dẫn bật bắt buộc CI xanh |
| `docs/TIEN_DO.md` (mới) | Tiến độ phiên việc PR-2 |
| `docs/bao-cao/PR2_CI_REPORT.md` (mới) | Báo cáo này |
| `CLAUDE.md`, `README.md` | Số test thật (220 → 281 + 9), Node 22, trỏ sang `docs/CI.md` |
| `docs/AI_USAGE.md` | Thêm dòng PR-2 |

**Không sửa:** code ứng dụng, test, Music Engine, migration, schema, giao diện. Chức năng người học không đổi.

## 4. CI làm gì

| Job | Bước | Đỏ khi |
|---|---|---|
| Backend (SQLite, toàn bộ test) | cài thư viện → `pip freeze` → `python -m compileall app tests migrations ../scripts` → `pytest -m "not postgres"` → `kiem_junit.py --min-passed 281` | có test sai hoặc lỗi, có skip, hoặc ít hơn 281 test đạt |
| Backend (PostgreSQL 16 + pgvector, Alembic, HM-010) | service `pgvector/pgvector:pg16` → tạo `harmony_ci_migrate` → `alembic upgrade head` → `alembic check` → kiểm tra `alembic_version` và extension `vector` → `pytest -m postgres` → `kiem_junit.py --min-passed 9` → kiểm tra không còn schema `hm_pgtest_*` | migration lỗi, model lệch migration, test sai, **bị skip**, ít hơn 9 test đạt, hoặc còn schema test sót lại |
| Frontend (npm ci + build) | Node 22 → `npm ci` → `npm run build` (`tsc -b` + `vite build`) | lỗi kiểu TypeScript hoặc lỗi build |

**Vì sao phải có `kiem_junit.py`:** test HM-010 tự bỏ qua khi thiếu `TEST_DATABASE_URL`. Khi cả 9 test bị bỏ qua, pytest vẫn trả mã 0 nên CI vẫn xanh. Lượt đỏ ở mục 6 cho thấy đúng điều này: bước pytest báo *success* với `9 skipped`, và chỉ bước kiểm số test mới bắt được lỗi.

**An toàn CSDL:**
- Máy chủ PostgreSQL là container tạm do GitHub tạo cho mỗi lượt chạy và xóa khi xong.
- Có hai CSDL tạm: `harmony_ci_migrate` đóng vai CSDL của app (`DATABASE_URL`), `harmony_test` dùng cho test (`TEST_DATABASE_URL`). Vì vậy lớp bảo vệ của PR-1 được kiểm thật: tên CSDL test phải kết thúc `_test` và phải khác `DATABASE_URL`.
- Mật khẩu `ci_only_not_secret` chỉ dùng cho container tạm này. CI không dùng secret, khóa JWT hay khóa Gemini nào.

## 5. Kết quả GitHub Actions thật: PR #9

Lượt 1, commit `0320b7d`: https://github.com/phucedu2/harmonymentor-V1/actions/runs/40451279330. **Kết quả: success, cả 3 job xanh**, thời gian chạy khoảng 55 giây.

| Job | Kết quả | Trích log |
|---|---|---|
| Backend SQLite | success | `281 passed, 9 deselected, 1 warning in 17.81s` · `Backend SQLite: tổng 281, PASS 281, FAIL 0, ERROR 0, SKIP 0` |
| Backend PostgreSQL | success | `starting PostgreSQL 16.15` · `alembic check`: `No new upgrade operations detected.` · `version_num b2c4e6f80a13` · `collected 290 items / 281 deselected / 9 selected` · `9 passed, 281 deselected, 1 warning in 2.93s` · `PostgreSQL HM-010: tổng 9, PASS 9, FAIL 0, ERROR 0, SKIP 0` |
| Frontend | success | `npm ci` 7 giây, `npm run build` 12 giây, không lỗi |

**Tổng số test backend: 290 PASS, 0 FAIL, 0 SKIP** (281 trên SQLite và 9 trên PostgreSQL). Python 3.11.17, pytest 9.1.1, Node 22.

### Bằng chứng 9 test đồng thời PostgreSQL đã chạy (log lượt 1)

```
tests/test_hm010_lesson_progress_concurrency.py::test_tables_live_only_in_the_isolated_schema PASSED [ 11%]
tests/test_hm010_lesson_progress_concurrency.py::test_isolated_schema_refuses_existing_schema PASSED [ 22%]
tests/test_hm010_lesson_progress_concurrency.py::test_service_start_lesson_concurrent_creates_single_row PASSED [ 33%]
tests/test_hm010_lesson_progress_concurrency.py::test_api_start_lesson_10_concurrent_requests_all_200 PASSED [ 44%]
tests/test_hm010_lesson_progress_concurrency.py::test_start_lesson_keeps_completed_lesson_unchanged PASSED [ 55%]
tests/test_hm010_lesson_progress_concurrency.py::test_complete_lesson_concurrent_without_start_is_safe PASSED [ 66%]
tests/test_hm010_lesson_progress_concurrency.py::test_complete_not_mastered_10_concurrent_all_409_and_leaves_nothing PASSED [ 77%]
tests/test_hm010_lesson_progress_concurrency.py::test_start_and_complete_concurrently_end_completed_single_row PASSED [ 88%]
tests/test_hm010_lesson_progress_concurrency.py::test_complete_lesson_again_keeps_original_completed_at PASSED [100%]
================= 9 passed, 281 deselected, 1 warning in 2.93s =================
PostgreSQL HM-010: tổng 9, PASS 9, FAIL 0, ERROR 0, SKIP 0
```

Sau khi test chạy xong, bước "Không còn schema test sót lại" đạt, tức 0 schema `hm_pgtest_*` còn lại. File JUnit được lưu thành artifact `junit-backend-postgres` của lượt chạy.

Lượt 3, commit `a423e28`, đã nâng phiên bản các action: https://github.com/phucedu2/harmonymentor-V1/actions/runs/40451537294. **Kết quả: success, cả 3 job xanh.** Trích log: `Backend SQLite: tổng 281, PASS 281, FAIL 0, ERROR 0, SKIP 0`. Bước kiểm số test của job PostgreSQL (0 skip, ít nhất 9 đạt) và bước kiểm schema sót lại đều đạt. Lượt chạy của commit cuối (commit thêm báo cáo này) xem ở tab Checks của PR #9.

## 6. Chứng minh lỗi làm CI đỏ: PR phụ #10

Commit `ad901c6` trên nhánh `ci-chung-minh-do` cố ý gây ba lỗi, mỗi lỗi nhắm một job. Lượt chạy: https://github.com/phucedu2/harmonymentor-V1/actions/runs/40451333477. **Kết quả: failure, cả 3 job đỏ.**

| Lỗi cố ý | Job | Bước đỏ | Trích log |
|---|---|---|---|
| Thêm test `assert 1 + 1 == 3` | Backend SQLite | Chạy pytest, Kiểm số test | `FAILED tests/test_ci_chung_minh_do.py::test_co_y_sai` · `1 failed, 281 passed` · `KHÔNG ĐẠT: có test thất bại hoặc lỗi` |
| Bỏ `TEST_DATABASE_URL` | Backend PostgreSQL | **Chỉ** bước Kiểm số test (bước pytest vẫn xanh) | `9 skipped, 282 deselected` · `KHÔNG ĐẠT: có 9 test bị skip (CI không chấp nhận skip); chỉ 0 test đạt, cần ít nhất 9` |
| `const coYSai: number = "khong phai so"` | Frontend | npm run build | `src/ciChungMinhDo.ts(2,14): error TS2322: Type 'string' is not assignable to type 'number'.` |

PR #10 đã được đóng và không gộp. Lịch sử PR #9 không có commit lỗi nào.

## 7. Kiểm thử cục bộ trước khi push (máy cloud, 27/10/2026)

- `pytest -q -m "not postgres"`: 281 passed, 9 deselected (Python 3.11).
- `pgvector/pgvector:pg16` qua Docker: `alembic upgrade head` chạy 4 migration, `alembic check` báo "No new upgrade operations detected", có `vector 0.8.7`. `pytest -m postgres`: 9 passed, sau khi chạy còn 0 schema `hm_pgtest_*`.
- `kiem_junit.py` báo đỏ đúng trong 3 tình huống: thiếu `TEST_DATABASE_URL` (9 skip), `TEST_DATABASE_URL` trùng `DATABASE_URL` (lớp bảo vệ PR-1 làm test bị skip), thiếu file XML.
- `npm ci && npm run build`: đạt.

## 8. Vấn đề còn tồn đọng

1. **Nhánh `ci-chung-minh-do` chưa xóa được.** Proxy của máy cloud chặn lệnh xóa nhánh từ xa, và công cụ GitHub của Claude không có thao tác xóa nhánh. Phúc mở PR #10 rồi bấm "Delete branch" là xong.
2. **Chưa bắt buộc CI xanh trước khi gộp.** CI mới chỉ báo kết quả. Phúc cần bật quy tắc bảo vệ nhánh `main` sau khi gộp PR-2 (các bước ở `docs/CI.md`). Repo riêng tư cần GitHub Pro/Team, Student Pack có Pro miễn phí. Nếu không bật được, nhóm thống nhất không gộp khi CI đỏ.
3. **`requirements.txt` ghi `>=`.** Khi một thư viện ra bản mới, CI có thể đỏ dù code không đổi. Log có `pip freeze` để truy vết. Đề xuất khóa phiên bản trong một PR riêng.
4. **Cảnh báo `httpx`/`starlette.testclient` deprecated** (1 warning trong pytest). Không làm CI đỏ. Sẽ xử lý khi khóa phiên bản thư viện.
5. **Mức `--min-passed` là số cố định (281 và 9).** Thêm test thì phải nâng mức này trong cùng PR, không bao giờ hạ.
6. **Chưa làm** (ngoài phạm vi PR-2 theo quyết định ở mục 2): chạy cả bộ 281 test với app trên PostgreSQL, lint (ruff), build Docker, Playwright (GĐ5).
7. **Cảnh báo về Node.js 20 của các action.** Commit `6cd7c7f` nâng checkout lên v5, setup-python lên v6, setup-node lên v5 và hết cảnh báo cho ba action này. `upload-artifact@v5` vẫn còn cảnh báo, nên commit cuối nâng tiếp lên v6. Kết quả xem ở tab Checks của PR #9.

## 9. Việc của từng bạn để kiểm

- **Thắng:** đọc `ci.yml` và `kiem_junit.py`, mở log lượt chạy ở mục 5 và đối chiếu số test. Kiểm rằng CSDL test và CSDL migration là hai CSDL khác nhau.
- **Phúc:** mở PR #10 xem 3 job đỏ đúng lý do, xóa nhánh `ci-chung-minh-do`, sau khi gộp PR-2 thì bật quy tắc bảo vệ nhánh.
- **Đạt:** không có phần nội dung. Ghi nhận rằng từ nay mọi PR nội dung cũng phải qua CI.

| Người kiểm | Ngày | Chữ ký |
|---|---|---|
| Thắng | | |
| Phúc | | |
| Đạt | | |
