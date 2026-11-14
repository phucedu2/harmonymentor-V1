# ADR-023 · Quản trị: sửa nội dung bài, người dùng, thống kê

Trạng thái: đề xuất (chờ Thắng, Đạt duyệt). Ngày 12/11/2026. Liên quan FR-19, FR-ADM-14, ADR-006.

## Bối cảnh
Bài học nạp từ mã (seed chạy mỗi lần khởi động và ghi đè). Admin cần sửa chữ trong bài mà không sửa mã, có lịch sử, xem trước, khôi phục.

## Quyết định
1. **Lớp ghi đè**: bảng `content_revisions` (kind, lesson_id, target, payload, status draft/published/superseded, ghi chú, người tạo). Seed không đụng bảng này; API học đọc nội dung gốc rồi phủ bản đã xuất bản. Xóa bản ghi = về nội dung gốc.
2. **Chỉ sửa chữ của khối lý thuyết** (title, prompt, note, intro, kicker, paragraphs, items, các trường chữ của terms). Loại khối, mã bài tập, hợp âm, nút mở Harmony Lab bị khóa. Câu hỏi KHÔNG sửa trong Quản trị (giữ ADR-006).
3. **Nháp trước, xuất bản sau**: lưu nháp học sinh không thấy. Mỗi lần lưu, Music Engine (`scan_reply`, không dùng AI) soát mọi nốt/quãng/hợp âm/số La Mã. Có chỗ nghi sai thì chỉ xuất bản khi admin tick xác nhận đã đối chiếu.
4. **Ẩn/hiện bài** qua bảng ghi đè; bài ẩn bị loại khỏi danh sách học, gợi ý và tiến độ của học sinh.
5. **Người dùng**: xem, tìm, khóa/mở khóa. Không đổi vai trò qua web (tạo admin chỉ bằng `ADMIN_EMAILS`/`seed_admin`), không tự khóa mình.
6. **Thống kê**: tính ở backend (loại `is_test`, `is_synthetic`, admin); giao diện vẽ SVG thuần.
7. **Nhật ký** `admin_audit_logs` cho mọi thao tác ghi.

## Hệ quả
Thêm 2 bảng + migration `f4d5e6f7a8b9`. Sửa nội dung bài làm lệch chỉ mục AI Tutor: bản đã sửa chưa vào kho tìm kiếm (chỉ mục dựng từ nội dung gốc). Ghi nhận là giới hạn.
