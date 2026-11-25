# Admin: tạo/xóa/sắp xếp bài và soạn câu luyện tập (24/11/2026)

Phúc chọn 1A và 5A (24/11). Đây là PR 2 trong 4 PR hoàn thiện khu Admin. Quyết định thiết kế ghi ở
[ADR-035](../../decisions/ADR-035-admin-tao-xoa-sap-xep-bai-va-cau-hoi.md).

| FR | Làm gì | Ở đâu |
|---|---|---|
| FR-ADM-13 | Tạo bài: tên, mục tiêu, khối lý thuyết đầu tiên; bài mới ẩn tới khi bấm hiện; thêm khối lý thuyết | tab Bài học → "Tạo bài mới" |
| FR-ADM-15 | Xóa mềm bài, khôi phục được (mục "Bài đã xóa") | trong bài → "Xóa bài này" |
| FR-ADM-16 | Sắp xếp bài bằng nút ↑ ↓; giữ qua lần khởi động sau (seed không ghi đè) | danh sách bài |
| FR-ADM-24–28 | Thêm/sửa/bỏ câu: trắc nghiệm, đúng/sai, chọn nhiều, tự luận ngắn, dựng hợp âm, dựng âm giai, tự luận mở; lời giải bắt buộc | trong bài → "Câu luyện tập" |
| FR-ADM-29 | Độ khó nhớ/hiểu/vận dụng (lưu `grader_config.difficulty`, quiz đã dùng) | form câu |

Music Engine tính đáp án. Ví dụ đã thử trên trình duyệt: chọn "m3" cho câu C lên E thì bị từ chối với thông báo "Bạn
chọn “m3”, Engine tính là “M3”". Câu Ebm7b5 thì Engine dựng Eb Gb Bbb Db. Sửa câu thì thêm phiên bản 2, bản 1 vẫn giữ
để chấm lại lượt cũ (ADR-006).

## Kiểm chứng

- `pytest -q` (SQLite): 1595 passed, 44 skipped (thêm 12 test ở `tests/test_admin_bai_hoc.py`, sửa head trong
  `test_ai_gd3_migration.py`).
- `alembic upgrade head` → `alembic check` ("No new upgrade operations detected") → `downgrade -1` đều chạy được trên SQLite.
- `npm run build` đạt; Vitest 313/313.
- Trình duyệt (Playwright, app thật): đổi chỗ bài 1 ↔ 2 rồi đổi lại; tạo bài; thêm câu sai đáp án bị từ chối; sửa thì
  lưu được; thêm câu dựng hợp âm; sửa độ khó thành phiên bản 2; hiện; xóa; khôi phục.

## Chưa làm

Bài M-… chưa vào kho AI Tutor. Chưa xóa hoặc sắp xếp khối trong một bài. Câu của bài seed chưa sửa được qua web (vẫn
đổi qua `curriculum_specs`).
