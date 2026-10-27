# PR-3 (HM-003): Báo cáo triển khai bảo vệ phiên bản câu hỏi

| Mục | Giá trị |
|---|---|
| Ngày | 27/10/2026 |
| Baseline | `main` = `f0d3dac1f7b11b9c9bb7236d14a3c74f0762c782` |
| Branch | `claude/project-thread-3z96i1` (branch được giao cho phiên làm việc; Phúc chọn 3A) |
| Draft PR | https://github.com/phucedu2/harmonymentor-V1/pull/11 (**không gộp**; chờ nhóm duyệt) |
| Thiết kế | `PR3_DESIGN_REVIEW.md` (thư mục chung của dự án), phê duyệt có điều kiện của Astra, ADR-006 |
| Quyết định | 8 câu thiết kế + 7 câu triển khai, Phúc chọn A hết (27/10, 07:15 và 08:52) |

Các commit (theo thứ tự review):

| SHA | Nội dung |
|---|---|
| `d19840f` | feat(db): model, migration `d3a7f1c2e905`, ảnh chụp git, trigger, lưới ORM |
| `f189ee7` | feat(content): seed không ghi đè, `SeedConflictError`, `SHOW_DRAFT_CONTENT` |
| `eb95130` | feat(learning): chấm theo phiên bản, 409, ẩn nháp, ẩn câu xóa mềm và bản thiếu ảnh chụp |
| `d1e79d8` | feat(frontend): tải lại bài khi gặp 409, không tự nộp lại |
| `f7876f8` | test(pr3): 50 test mới, nâng mức CI |
| `20bbd88` | docs(pr3): ADR-006, quy tắc sửa câu, số test, tiến độ, nhật ký AI, ảnh |
| (commit này) | docs(pr3): báo cáo triển khai |

---

## 1. Kết quả theo yêu cầu của Astra

| Yêu cầu | Kết quả | Bằng chứng |
|---|---|---|
| 1. Nối migration vào HEAD hiện tại | `d3a7f1c2e905` có `down_revision = "b2c4e6f80a13"`. Sau khi thêm, chỉ có một head | `logs/00-alembic-heads-history-truoc.log`: trước đó `b2c4e6f80a13 (head)`, lịch sử 4 migration; `alembic heads` sau đó: `d3a7f1c2e905 (head)` |
| 2. D-1..D-4 | Phúc xác nhận thay nhóm (1A). Chỗ ký ghi trong ADR-006 | D-1: provenance nằm trong ảnh chụp, sửa thì tăng version (2A). D-2: đếm sai theo câu (có test). D-3: 24 bản `published` là dữ liệu kế thừa chưa qua duyệt mới. D-4: ADR-006 |
| 3A. Migration an toàn | Không sửa migration cũ. Không xóa, sửa hay thêm dòng nào: chỉ thêm cột rồi điền giá trị | Test `test_upgrade_keeps_every_row_and_restores_only_existing_versions` (SQLite + PostgreSQL) so từng dòng attempts, exercise_versions và exercises trước và sau |
| Chỉ khôi phục bản thật sự có trong CSDL | File git có 38 ảnh chụp, nhưng migration chỉ cập nhật dòng đang có. CSDL kế thừa có 33 dòng thì vẫn 33 dòng; 6 bản `L01-Q0x-v2` không có trong CSDL nên không được tạo | Cùng test trên: `L01-Q02-v2` không xuất hiện |
| Kiểm bản hiện hành khớp nguồn trước khi suy luận | Bản mới nhất phải khớp đề, lựa chọn, loại câu và cách chấm trên `exercises`, cộng với đáp án, cấu hình chấm, lời giải và danh tính câu so với git. Không khớp thì `missing` | `test_current_version_not_matching_source_is_marked_missing` |
| Không bịa đề bài | `missing` → các cột đề để `NULL`; CHECK `ck_exercise_versions_snapshot` cho phép đúng trường hợp này | `L01-Q01-v1` (bản giả lập có từ trước repo) → `missing` |
| Bản hiện hành thiếu ảnh chụp không được hiển thị hay chấm | `current_version()` trả `None`, không lùi về bản cũ hơn. API ẩn câu và trả 404 khi nộp. Seed báo `SEED_SNAPSHOT_MISSING` | `test_missing_snapshot_current_version_is_hidden_and_not_graded`, test migration tương ứng |
| Thử migration trên PostgreSQL có dữ liệu kế thừa và có bản sao lưu | Đã làm ở mục 3. `pg_dump` trước khi upgrade, đã khôi phục thử thành công từ bản sao lưu | `logs/10..14` |
| Không coi downgrade là đường lùi | `downgrade()` từ chối chạy, kèm hướng dẫn khôi phục bản sao lưu. Chỉ thử trên CSDL tạm, không phải CSDL cần giữ | `test_downgrade_is_refused`, `logs/14-khoi-phuc-tu-ban-sao.log` |
| 3B. Ảnh chụp đủ trường quyết định nghĩa | 8 trường: kind, prompt, options, grading_strategy, answer_key, grader_config, explanation, provenance | `app/content/versioning.py` |
| Seed idempotent | Seed 3 lần không đổi id, hash hay `created_at` của phiên bản nào. Trên CSDL kế thừa, seed 2 lần vẫn 33 dòng | `test_seed_three_times_changes_nothing`, `test_seed_after_upgrade_is_idempotent` |
| Lệch nội dung → `SeedConflictError` + rollback toàn bộ | Đã kiểm với cả 8 trường. Rollback cả bản sao đề trên `exercises` | `test_changing_published_version_without_bump_fails_and_rolls_back[8 trường]` |
| Không tự tăng version | Có xung đột thì không tạo phiên bản nào | `test_conflicts_never_auto_create_versions` |
| Không đổi `skill_id`, `lesson_id` | Seed báo `SEED_IDENTITY_CHANGED`. ORM và trigger PostgreSQL cũng chặn | `test_identity_change_is_rejected`, `test_orm_guard_blocks_edits_and_deletes`, test trigger |
| Kiểm cả đường sửa qua ORM và SQL trực tiếp | ORM: listener `before_update`/`before_delete`. PostgreSQL: 2 trigger. Giới hạn ở mục 6 | `test_postgres_trigger_blocks_direct_sql` (7 câu SQL) |
| 3C. Draft mặc định ẩn | `SHOW_DRAFT_CONTENT` mặc định `0`. Test chỉ bật khi cần (monkeypatch). Production mà bật thì API không khởi động | `test_draft_hidden_by_default_and_not_required_for_completion`, `test_production_refuses_draft_flag`, chạy thật `APP_ENV=production SHOW_DRAFT_CONTENT=1` → RuntimeError |
| Draft và câu retired không làm sai điều kiện hoàn thành | Chỉ tính câu đang hiện | `test_draft_hidden_...`, `test_retired_exercise_is_soft_deleted_and_history_kept` |
| 3D. GET lesson lấy đề từ bản hiện hành | `lessons.py` đọc `version.prompt`, `version.options`, ... | `test_attempt_on_superseded_version_returns_409` (đề v5) |
| Chấm bằng `version.grading_strategy` | `learning_service.submit_attempt` | `test_old_rubric_version_keeps_meaning_after_exact_version` |
| 409 `EXERCISE_VERSION_SUPERSEDED` | Có `fields.current_version_id`. Lượt bị từ chối không được lưu | `test_attempt_on_superseded_version_returns_409` |
| Frontend báo tiếng Việt, tải lại, không tự nộp lại | Thẻ câu hỏi có key là `version_id`, nên đáp án cũ bị xóa | Kịch bản trình duyệt ở mục 4 |
| Lượt cũ giữ kết quả và liên kết | Không chấm lại (5A). FK vẫn trỏ đúng bản cũ | Mục 3, bảng chấm lại |
| Người đã hoàn thành trước khi có câu hoặc bản mới | Vẫn `completed`, giữ `completed_at`. Bài đang học thì phải làm câu mới | `test_completed_lesson_stays_completed_when_question_added`, `test_started_lesson_must_answer_new_question`, `test_correct_on_old_version_still_counts_after_new_version` |

---

## 2. Danh sách file thay đổi

`git diff --stat f0d3dac..HEAD`: 31 file, +4391/−71 (chưa tính báo cáo này).

| File | Thay đổi |
|---|---|
| `backend/migrations/versions/20261027_pr3_exercise_version_snapshot.py` | Mới: thêm cột, CHECK, khôi phục ảnh chụp, trigger, downgrade từ chối |
| `backend/migrations/data/pr3_anh_chup_lich_su.json` | Mới: 38 ảnh chụp trích từ commit `3a809e4`, `5cd49d4`, `5c31dc4`, `f0d3dac`, có SHA-256 chuẩn hóa (không phụ thuộc CRLF trên Windows) |
| `backend/migrations/env.py` | Nhận kết nối có sẵn (để test migration chạy trong schema tạm) |
| `backend/app/content/versioning.py` | Mới: ảnh chụp, mã băm, phiên bản hiện hành, `SeedConflictError` |
| `backend/app/db/models.py` | Cột mới, CHECK, lưới ORM |
| `backend/app/db/session.py` | Báo rõ cách sửa khi file SQLite dev cũ thiếu cột |
| `backend/app/content/seed_data.py` | Viết lại `_upsert_exercises`, kiểm câu biến mất, rollback |
| `backend/app/content/curriculum_specs.py` | `q()` thêm `status`, `retired`. **Không đổi nội dung câu nào** |
| `backend/app/core/config.py`, `backend/app/main.py`, `.env.example` | `SHOW_DRAFT_CONTENT`, chặn khi production, seed xung đột thì dừng khởi động |
| `backend/app/services/learning_service.py`, `backend/app/api/lessons.py`, `backend/app/api/attempts.py` | Phiên bản hiện hành, 409, chấm theo ảnh chụp |
| `frontend/src/components/learning/LessonRunner.tsx`, `frontend/src/pages/Learn.tsx` | Xử lý 409 |
| `backend/tests/test_pr3_exercise_version.py` | 31 test SQLite |
| `backend/tests/test_pr3_migration.py`, `backend/tests/fixtures/pr3_csdl_ke_thua.json` | 7 test SQLite + 12 test PostgreSQL. Fixture là bản sao CSDL kế thừa dựng bằng code cũ |
| `.github/workflows/ci.yml` | `--min-passed` 281 → 319 và 9 → 21. **Tên job không đổi**, nên ruleset `bao-ve-main` vẫn khớp |
| `docs/decisions/ADR-006-phien-ban-bai-tap.md`, `docs/LESSON_SPECIFICATIONS.md`, `docs/CI.md`, `docs/TIEN_DO.md`, `docs/AI_USAGE.md`, `CLAUDE.md`, `README.md`, `docs/minh-chung/anh/pr3-409-*.png` | Tài liệu |

**Không sửa:** Music Engine, 4 migration cũ, nội dung và đáp án câu hỏi, id phiên bản, flashcard, mastery, gợi ý, AI.

---

## 3. Migration trên CSDL kế thừa (PostgreSQL 16 + pgvector)

Chạy ngày 27/10/2026 trong container cloud, PostgreSQL 16 có cài `postgresql-16-pgvector`. Script nằm ở `repro/legacy_build.py` và `repro/legacy_verify.py`; log nằm ở `logs/`.

**Cách dựng dữ liệu kế thừa** (giống một máy đã chạy app từ 20/10):
1. `alembic upgrade b2c4e6f80a13`.
2. Seed bằng **code commit 5cd49d4**. Tạo 5 lượt làm, trong đó có `L03-Q05-v1` (rubric) đúng và sai, `L04-Q06-v1` (rubric).
3. Seed lại bằng **code main f0d3dac**. Lúc này `L03-Q05`, `L04-Q06` thành trắc nghiệm `exact`; tạo thêm 2 lượt làm.
4. Thêm tay `L01-Q01-v1` cùng một lượt làm, giả lập bản có từ trước repo.
5. `pg_dump` ra `harmony_legacy_truoc_pr3.sql` (107 KB).

**Trước migration** (`logs/10-truoc-migration.log`): revision `b2c4e6f80a13`; 8 lượt làm; 33 phiên bản; 24 câu. `exercises.grading_strategy` của `L03-Q05` và `L04-Q06` đã là `exact`.

**Upgrade** (`logs/11-upgrade-check.log`): `upgrade b2c4e6f80a13 -> d3a7f1c2e905`; `alembic check`: "No new upgrade operations detected."

**Sau migration** (`logs/12-sau-migration.log`):

| Kết quả | Số liệu |
|---|---|
| Revision | `d3a7f1c2e905` |
| Lượt làm | 8 (không đổi) |
| Phiên bản `git_history` / `missing` | 32 / 1 (`L01-Q01-v1`) |
| `L03-Q05-v1` | `rubric`, đề gốc, không có lựa chọn |
| `L03-Q05-v2` | `exact`, 4 lựa chọn |

**Bằng chứng bản cũ chấm rubric vẫn giữ đúng nghĩa khi đã có bản mới chấm exact** (`logs/13-kiem-sau-migration.log`). Mỗi lượt làm được chấm lại theo ảnh chụp của chính phiên bản nó đã làm:

```
L01-Q01-v1  origin=missing -> không chấm lại (không có đề gốc); kết quả đã lưu correct=True giữ nguyên
L03-Q05-v1  strategy=rubric answer='Vì chức năng phụ thuộc ngữ cảnh'  lưu=True  chấm_lại=True  KHỚP
L03-Q05-v1  strategy=rubric answer='không biết'                       lưu=False chấm_lại=False KHỚP
L04-Q06-v1  strategy=rubric answer='mỗi nốt di chuyển ít nhất'        lưu=True  chấm_lại=True  KHỚP
L01-Q01-v4  strategy=exact  answer='M3'                               lưu=True  chấm_lại=True  KHỚP
L01-Q05-v4  strategy=rubric answer='không'                            lưu=True  chấm_lại=True  KHỚP
L03-Q05-v2  strategy=exact  answer='Vì chức năng phụ thuộc vào giọng…' lưu=True  chấm_lại=True  KHỚP
L01-Q05-v5  strategy=exact  answer='Không'                            lưu=True  chấm_lại=True  KHỚP
Nộp vào L03-Q05-v1 -> EXERCISE_VERSION_SUPERSEDED current = L03-Q05-v2
```

Đối chiếu: trước PR-3, cùng câu trả lời đúng ấy gửi lại vào v1 bị chấm **sai** (`INCORRECT_ANSWER`), vì code cũ dùng `exercises.grading_strategy = exact` (mục 2.3 của bản thiết kế).

**Seed sau migration:** chạy 2 lần, số phiên bản 33 → 33, không có bản `seed` nào được tạo thêm.

**Trigger chặn SQL trực tiếp** (cùng log):

| Câu lệnh | Kết quả |
|---|---|
| `UPDATE … SET prompt` trên `L03-Q05-v1` | `EXERCISE_VERSION_IMMUTABLE` |
| `UPDATE … SET answer_key` trên `L01-Q01-v4` | bị chặn |
| `published` → `draft` | bị chặn |
| `DELETE` bản đã phát hành | bị chặn |
| Đổi `skill_id` của `L03-Q05` | `EXERCISE_IDENTITY_IMMUTABLE` |

**Đường lùi** (`logs/14-khoi-phuc-tu-ban-sao.log`): khôi phục bản `pg_dump` vào một CSDL mới được revision `b2c4e6f80a13`, 8 lượt làm, 33 phiên bản, giống trước migration. `alembic downgrade -1` (chạy trên CSDL thử nghiệm) báo: "không hỗ trợ downgrade vì sẽ xóa ảnh chụp… khôi phục CSDL từ bản sao lưu".

Fixture `tests/fixtures/pr3_csdl_ke_thua.json` là bản sao đúng của CSDL kế thừa này, để CI chạy lại cùng kịch bản trên SQLite và PostgreSQL.

---

## 4. Kiểm trên trình duyệt (luồng 409)

Backend thật (SQLite tạm) + Vite, Playwright, tài khoản đăng ký mới. Log: `logs/30-trinh-duyet-409.log`; ảnh: `docs/minh-chung/anh/pr3-409-{truoc,sau}-{may-tinh,dien-thoai}.png`.

1. Mở Bài 1, tới câu kiểm tra nhanh "Đọc một quãng mới". Đề v4: "Quãng từ F lên A là gì?"
2. Trong lúc trang đang mở, phát hành `L01-Q01-v5` vào CSDL. Ở lượt điện thoại, phát hành tiếp v6.
3. Chọn M3, bấm "Kiểm tra" → `POST /attempts` trả **409** `EXERCISE_VERSION_SUPERSEDED`.
4. Màn hình hiện: "Câu hỏi vừa được cập nhật nên bài đã tải lại đề mới. Câu trả lời trước chưa được chấm, hãy đọc lại đề và trả lời lại." Đề đổi thành "(Bản 5) …" (điện thoại: "(Bản 6) …"), không còn lựa chọn nào được chọn sẵn.
5. Người học tự chọn lại và nộp → 200 trên v5/v6.
6. Trong CSDL chỉ có `L01-Q01-v5: 1`, `L01-Q01-v6: 1`. Lượt bị 409 không được lưu và không được tự nộp lại.

---

## 5. Kết quả test, build, CI (chạy thật 27/10/2026)

| Lệnh | Kết quả |
|---|---|
| `cd backend && pytest -q` (không có `TEST_DATABASE_URL`) | **319 passed, 21 skipped** |
| `pytest -q -m "not postgres"` + `kiem_junit.py --min-passed 319` | tổng 319, PASS 319, SKIP 0 |
| `pytest -m postgres` (PostgreSQL 16 + pgvector) + `kiem_junit.py --min-passed 21` | tổng 21, PASS 21, SKIP 0; không còn schema `hm_pgtest_*` |
| `pytest -q` có `TEST_DATABASE_URL` | **340 passed** |
| `alembic upgrade head && alembic check` trên SQLite trống, PostgreSQL trống và CSDL kế thừa | đạt, "No new upgrade operations detected." |
| `python -m compileall -q app tests migrations ../scripts` | đạt |
| `npm ci && npm run build` | đạt (chỉ có cảnh báo kích thước chunk như trước) |
| Khởi động uvicorn trên PostgreSQL đã migrate, `GET /api/v1/lessons/L03` | 200, phiên bản `L03-Q04-v2` (rubric), `L03-Q05-v2` (exact) |
| GitHub Actions trên PR #11 | xem tab Checks của PR; kết quả sẽ được cập nhật vào thread |

50 test mới:

| File | Số test | Chạy ở đâu |
|---|---|---|
| `test_pr3_exercise_version.py` | 31 | SQLite |
| `test_pr3_migration.py` | 7 | SQLite: 5 kịch bản kế thừa, mã băm migration = mã băm ứng dụng, file ảnh chụp bị sửa thì dừng |
| `test_pr3_migration.py` | 12 | PostgreSQL: 5 kịch bản kế thừa, 7 câu SQL bị trigger chặn |

---

## 6. Giới hạn chưa xử lý

- **SQLite và CSDL tạo bằng `create_all`** (`AUTO_CREATE_SCHEMA=1`, dev/test) không có trigger, chỉ có lưới ORM. SQL viết tay trên SQLite vẫn sửa được phiên bản. Docker dùng Alembic nên có trigger.
- **Superuser PostgreSQL** vẫn tắt được trigger. Đây là lớp chống lỗi, không phải chống phá hoại.
- **Flashcard (`review_items`) và `lesson_blocks`** vẫn bị ghi đè tại chỗ (ngoài phạm vi theo 8A). Cần xem lại ở GĐ3 (trích dẫn `L0x-Byy`) và GĐ4.
- **Phiên bản `missing`** không bao giờ được điền lại. Muốn câu hiện lại thì phát hành version mới.
- **File SQLite dev cũ** (`backend/harmonymentor_dev.db`) thiếu cột mới. API báo rõ cách sửa là xóa file để tạo lại.
- **`attempts.is_test`** chưa có (thuộc PR-5). Hiện "đã có lượt làm" nghĩa là có bất kỳ dòng `attempts` nào.
- **`docs/HOP_DONG_API.md`** chưa tồn tại trong repo. Mã lỗi mới được ghi ở ADR-006 và mô tả PR. Nên tạo file này khi làm PR-5.
- **FK cascade** `exercise_versions → exercises` (`ondelete="CASCADE"`) giữ nguyên. Xóa cứng bị trigger, ORM và FK của `attempts` chặn, nhưng Admin ở GĐ4 vẫn phải dùng xóa mềm.

## 7. Kế hoạch rollback an toàn

1. **Trước khi gộp hay triển khai:** chụp bản sao lưu bằng `docker compose exec db pg_dump -U harmony harmony > truoc_pr3.sql`.
2. **Gộp PR-3:** container `api` tự chạy `alembic upgrade head` khi khởi động. Nếu seed báo `SeedConflictError`, API không lên; đọc log để biết id câu cần tăng version.
3. **Nếu phải quay lại:**
   - dừng `api`;
   - khôi phục `truoc_pr3.sql` vào CSDL mới;
   - triển khai lại code `f0d3dac`.
   **Không chạy `alembic downgrade`**: lệnh này cố ý báo lỗi.
4. **Code quay lại `f0d3dac` mà CSDL vẫn ở `d3a7f1c2e905`:** app cũ vẫn chạy (chỉ thừa cột), nhưng seed cũ sẽ bị trigger chặn khi ghi đè phiên bản. Vì vậy phải khôi phục bản sao lưu, không chạy code cũ trên CSDL mới.

## 8. Việc của từng bạn để kiểm

- **Thắng:** đọc migration (mục 3), seed (`_upsert_exercises`), lưới ORM, CI. Ký D-2, D-4. Người kiểm: ________
- **Phúc:** mở lại kịch bản 409 trên máy, xem 4 ảnh. Người kiểm: ________
- **Đạt:** đọc quy tắc sửa câu trong `docs/LESSON_SPECIFICATIONS.md`. Ký D-1, D-3 (24 bản `published` là dữ liệu kế thừa chưa qua duyệt mới). Người kiểm: ________
- **Astra:** duyệt tổng thể Draft PR #11. **Không gộp** trước khi nhóm ký.

## 9. Bổ sung sau review (27/10/2026)

Astra duyệt PR #11 trên commit `1e654fb`, kết luận phần cốt lõi HM-003 đạt và yêu cầu sửa 2 lỗi về tiến độ học trước khi gộp. Phúc chọn A cả 6 câu làm rõ.

| # | Lỗi | Cách sửa | Test |
|---|---|---|---|
| 1 | `learning_overview()`: `exercise_count` chỉ đếm câu đang hiện, nhưng `attempted_exercises`, `correct_exercises`, hai danh sách id và `practice_progress_percent` vẫn đếm câu đã retired hoặc bị ẩn, nên phần trăm có thể vượt 100% (ví dụ 6/5 = 120%) | Số đếm theo câu chỉ tính câu có phiên bản hiện hành (cùng quy tắc `current_version`, nên khi bật `SHOW_DRAFT_CONTENT` thì câu nháp cũng tính). Đúng ở bản cũ của câu còn hợp lệ vẫn tính (6A). `attempt_count`, `correct_attempt_count` giữ là lịch sử, đếm mọi lượt. Bài đã hoàn thành vẫn 100% | `test_overview_counts_only_visible_exercises_after_retire`: làm 6 câu L01 (7 lượt), retired L01-Q06 và nâng L01-Q01 lên v5, tổng còn 5 → 5/5 câu, 100%, 7 lượt; người làm 1 câu hợp lệ → 20% |
| 2 | `complete_lesson()`: bài có 0 câu hợp lệ thì danh sách câu còn thiếu rỗng nên vẫn được đánh dấu hoàn thành và kích hoạt thẻ ôn | Bài chưa hoàn thành mà không có câu hợp lệ: rollback, trả `409 LESSON_HAS_NO_EXERCISES` ("Bài này hiện chưa có câu hỏi nào để làm, nên chưa thể hoàn thành."). Không tạo completed, không tạo thẻ ôn. Bài đã hoàn thành trước đó: vẫn 200, giữ `completed_at` và thẻ ôn | `test_complete_rejected_when_lesson_has_no_visible_exercises` × 4 (bài chưa có câu L05, toàn nháp, toàn retired, bản hiện hành missing); `test_completed_lesson_keeps_completed_at_and_reviews_when_no_exercises_left` |

Frontend không cần sửa: `LessonRunner` đã hiện `message` của lỗi khi bấm "Hoàn thành".

Không đụng migration `d3a7f1c2e905`, versioning, ảnh chụp, seed, Music Engine, Mastery hay Recommender.

**Kết quả chạy thật:**

- Trước khi sửa: 6/6 test mới **đỏ** khi chạy với logic cũ.
- Sau khi sửa:
  - `pytest -q` cho 325 passed, 21 skipped.
  - `pytest -m postgres` với `TEST_DATABASE_URL` cho 21 passed.
  - Cả bộ chạy trên PostgreSQL cho 346 passed.
  - `npm run build` đạt.
- Mức CI nâng 319 → 325 (SQLite); PostgreSQL giữ 21.

**Giới hạn:** 6 test mới chạy trên SQLite, vì chúng dùng chung bộ dựng CSDL tạm của `test_pr3_exercise_version.py`. Logic sửa chỉ là lọc trong Python, không có câu SQL riêng theo CSDL.
