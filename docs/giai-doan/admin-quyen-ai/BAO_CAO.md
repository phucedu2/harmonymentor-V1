# Hoàn thiện Admin, PR 4: quyền Admin và công tắc AI (24/11/2026)

Phúc chọn 4A, 7A, 8A. Quyết định ghi ở [ADR-036](../../decisions/ADR-036-quyen-admin-cong-tac-ai-khong-course-module.md).

## Đã làm theo FR

| FR | Nội dung | Chỗ trong app |
|---|---|---|
| FR-ADM-06 | Nâng người học lên Quản trị viên, hạ Quản trị viên khác xuống người học. Không tự đổi vai trò. Có hiệu lực ngay, ghi nhật ký `user.role` | Quản trị → Người dùng, nút "Nâng lên Quản trị" / "Hạ xuống người học" |
| FR-ADM-29, FR-AI-04 | Công tắc AI lưu CSDL (bảng `app_settings`). Tắt thì AI Tutor, nhúng và AI soạn bài đều không gọi Gemini, app chạy bằng luật dự phòng. Khóa API vẫn chỉ ở `.env` | Quản trị → AI soạn bài, thẻ "Công tắc AI" |
| FR-ADM-38 | Ghi nhật ký `ai.switch.on` / `ai.switch.off` | Quản trị → Thống kê, Nhật ký |
| (lệch tài liệu) | Không có bảng course/module, giữ một chuỗi bài theo `sort_key` | ADR-036 mục 3 |

## File

- Backend:
  - `app/db/models.py` (`AppSetting`)
  - `migrations/versions/20261124_app_settings_ai_switch.py`
  - `app/core/ai_switch.py`
  - `app/api/ai_tutor.py`
  - `app/api/ai_recommend.py`
  - `app/admin/router.py`
- Frontend:
  - `src/api.ts`
  - `src/components/admin/UsersTab.tsx`
  - `src/components/admin/AiDraftTab.tsx`
- Test:
  - `tests/test_admin_quyen_ai.py` (5 test mới)
  - `tests/test_ai_gd3_migration.py`: head mới
  - `tests/test_admin_ai_tai_lieu.py`: `/ai/status` có thêm trường

## Kiểm thử

- `pytest -q` (SQLite): **1588 passed, 44 skipped** (skip là test PostgreSQL, CI chạy riêng). CI `--min-passed` nâng 1583 → 1588.
- `npm test`: **313 passed**. `npm run build`: đạt.

## Lưu ý khi gộp

PR #76 cũng thêm migration từ `c7a8b9c0d1e2`. Gộp cả hai PR sẽ ra hai head Alembic. Khi gộp PR thứ hai, phải làm ba việc:
1. Đổi `down_revision` của migration này sang head của PR kia.
2. Sửa test head.
3. Nâng `--min-passed` trong `ci.yml` theo tổng mới.

## Chưa làm

- Không có giới hạn số Admin, không có vai trò trung gian (biên tập viên). Chưa cần cho MVP.
- Công tắc chỉ có một mức bật/tắt cho toàn hệ thống, chưa tách riêng AI Tutor và soạn bài.
