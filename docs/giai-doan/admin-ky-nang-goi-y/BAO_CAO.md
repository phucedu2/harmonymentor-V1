# Hoàn thiện Admin, nhóm 2: kỹ năng tự tạo vào gợi ý, bài tự tạo vào AI Tutor, ngưỡng thành thạo (25/11/2026)

Phúc chọn 9A. Quyết định ở [ADR-037](../../decisions/ADR-037-ky-nang-tu-tao-vao-goi-y-tutor-nguong.md). Nhánh `claude/admin-ky-nang-goi-y`, xây trên nhóm 1 (#79).

## Đã làm theo FR
| FR | Nội dung | Chỗ trong app |
|---|---|---|
| FR-ADM-18..20 (mở rộng) | Kỹ năng tự tạo chọn nhóm gợi ý khi thêm, đổi nhóm sau. Làm đúng câu của kỹ năng đó thì có mastery và vào vector gợi ý | Kỹ năng & nguồn → Thêm kỹ năng / ô "Nhóm gợi ý" |
| FR-ADM-23 | Đặt ngưỡng sẵn sàng/thành thạo riêng cho mọi kỹ năng; seed không ghi đè; có nhật ký | Kỹ năng & nguồn → "Lưu ngưỡng" |
| (việc dở) | Bài M- đang hiện vào kho AI Tutor, ẩn/xóa thì gỡ | tự động khi bấm hiện/ẩn/xóa |
| (lỗi cũ) | Bài AI/M- sửa chữ rồi xuất bản: Tutor đọc chữ mới ngay | tự động |

## Kiểm thử
- `pytest -q`: 1621 passed, 44 skipped (4 test mới ở `tests/test_admin_ky_nang_goi_y.py`; CI `--min-passed` nâng 1617 → 1621).
- `npm test`: 313 passed. `npm run build`: đạt.
- Phát hiện khi chạy cả bộ: test của mình để lại mastery của kỹ năng tự tạo làm vỡ 7 test gợi ý ở file khác. Chỉ do thiếu dọn dẹp trong test, đã sửa; ngoài đời thật không xóa được kỹ năng đã có câu hỏi nên không xảy ra.

## Chưa làm
- Câu của bài M- chưa vào ngân hàng "Từ tài liệu" ở trang Luyện tập.
- Kỹ năng tự tạo chưa có mô tả/embedding nên điểm "nội dung" của hệ gợi ý bằng 0.
- Mô hình dự đoán làm đúng xếp kỹ năng tự tạo vào nhóm "khac" cho tới khi huấn luyện lại.
