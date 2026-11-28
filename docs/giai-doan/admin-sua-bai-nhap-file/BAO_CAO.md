# Hoàn thiện Admin, nhóm 1: sửa bài/khối và nhập nội dung từ file (25/11/2026)

Phúc chọn 3A, 4A, 5A ngày 25/11/2026. Xây trên phuc-music sau khi gộp #75–#78.

## Đã làm theo FR

| FR | Nội dung | Chỗ trong app |
|---|---|---|
| FR-ADM-14 | Sửa tên và mục tiêu của MỌI bài. Bài gốc (L01…) lưu vào cột `lessons.admin_meta` để seed khởi động lại không ghi đè; có nút "Về tên gốc". Bài M-/AI- ghi thẳng cột | Bài học → mở bài → "Sửa tên và mục tiêu bài" |
| FR-ADM-14 | Xóa và đổi thứ tự từng khối, chỉ bài M-/AI- (bài gốc bị seed dựng lại khối mỗi lần khởi động). Mã khối không tái dùng sau khi xóa; nội dung khối xóa vẫn nằm trong nhật ký | Bài học → mở bài → ↑ ↓ Xóa khối |
| FR-ADM-39 | Nhập file `.yaml`/`.json` gồm bài, khối, câu luyện tập, nguồn. Có "Kiểm thử" (không ghi) và "Nhập". Nhập lại cùng mã thì cập nhật; câu đổi đề/đáp án thì tăng version (ADR-006). Engine kiểm đáp án; sai một chỗ thì không ghi gì và báo đủ vị trí lỗi. Bài mới ẩn tới khi bật. Câu có trong CSDL mà file không còn thì chỉ báo, không tự bỏ | Bài học → "Nhập nội dung từ file", nút "Tải file mẫu" |

Migration `f0a1b2c3d4e5` thêm `lessons.admin_meta`. Thêm PyYAML (`safe_load`) vào requirements.

## Kiểm thử
- `pytest -q`: 1617 passed, 44 skipped. 6 test mới ở `tests/test_admin_sua_bai_nhap_file.py`.
- `npm test`: 313 passed. `npm run build`: đạt.
- Chạy app thật bằng Playwright (AI giả): nhập file sai bị chặn đúng chỗ, nhập đúng, nhập lại không trùng, đổi thứ tự/xóa khối, sửa tên, về tên gốc. Bài gốc không hiện nút xóa khối.

## Chưa làm
- Sửa câu hỏi của bài gốc qua web (câu 5A: sửa qua PR file nội dung).
- Nhập file chưa hỗ trợ thẻ ôn, mẫu bài tập, khối ví dụ (làm ở nhóm sau).
