# ADR-036: Nâng/hạ quyền Admin qua web, công tắc AI lưu CSDL, không có bảng course/module

- Trạng thái: Đề xuất (Phúc chọn 4A, 7A, 8A ngày 24/11/2026; chờ nhóm duyệt PR)
- Liên quan: FR-ADM-06, FR-ADM-29, FR-ADM-38, FR-AI-04; ADR-035 (bài học do Admin tạo)

## Bối cảnh

1. Trước đây chỉ đổi được vai trò bằng lệnh/CSDL. Tài liệu 2.1 có FR quản lý người dùng nhưng không nói rõ ai được cấp quyền Quản trị.
2. Muốn bật/tắt AI phải sửa `.env` rồi khởi động lại máy chủ. Lúc demo, hết hạn mức Gemini, hoặc Gemini lỗi 503 thì không tắt nhanh được.
3. Tài liệu 2.1 mô tả cấp khóa học/mô-đun (course/module) phía trên bài học. App hiện chỉ có một chuỗi bài L01–L08 sắp theo thứ tự.

## Quyết định

### 1. Đổi vai trò qua web (7A), ĐÃ GỠ ngày 27/11/2026

> **Bổ sung 27/11/2026 (Phúc chọn 1A, ADR-041):** gỡ cả nút "Nâng lên Quản trị"/"Hạ xuống người học" lẫn trường `role` của
> `PATCH /admin/users/{id}`. Gửi `role` nay bị từ chối 400 (`extra="forbid"`), không ghi nhật ký `user.role` nữa.
> Lý do: dự án chỉ có vài Quản trị viên cố định, cấp quyền qua web thêm rủi ro (lỡ tay, chiếm quyền) mà không cần cho demo.
> Quản trị viên chỉ tạo bằng `python -m app.seed_admin`. Khóa/mở khóa tài khoản giữ nguyên. Phần dưới giữ để truy vết.

- `PATCH /api/v1/admin/users/{id}` nhận `{"role": "admin" | "learner"}`, có thể kèm `is_active`.
- Admin **không** tự đổi vai trò của mình (409 `CANNOT_CHANGE_OWN_ROLE`). Vì vậy luôn còn ít nhất một Admin: người đang thao tác.
- Mỗi lần đổi ghi nhật ký `user.role` với `detail = {from, to}`.
- `require_admin` đọc vai trò từ CSDL ở mỗi yêu cầu, nên đổi vai trò có hiệu lực ngay, kể cả với token cũ.
- Tài khoản mô phỏng không có email nên không đổi được (404), giống luật khóa tài khoản.

### 2. Công tắc AI trong CSDL (8A)
- Bảng mới `app_settings(key, value JSON, updated_by, updated_at)`, khóa `ai_enabled` = `{"on": bool}`. Migration `e9f0a1b2c3d4`.
- AI chỉ chạy khi cả hai điều kiện đúng: `.env` sẵn sàng (`AI_ENABLED=true` và có khóa Gemini) **và** công tắc đang bật.
- **Khóa API chỉ nằm trong `.env`**, không bao giờ lưu CSDL hay trả về qua API.
- Công tắc chặn bốn chỗ gọi Gemini:
  - provider của AI Tutor;
  - bộ nhúng Gemini của AI Tutor;
  - provider soạn bài của Admin;
  - bộ nhúng gợi ý.
  Khi tắt, mọi luồng dùng dự phòng theo luật đã có (nguyên tắc 3: `AI_ENABLED=false` vẫn demo được).
- `app/core/ai_switch.py` đệm giá trị 5 giây để không truy vấn CSDL ở mỗi yêu cầu. Máy chủ đổi công tắc thì xóa đệm ngay. Đọc CSDL lỗi thì coi là bật, để `.env` quyết định như trước, tránh tắt nhầm AI.
- Mỗi lần đổi ghi nhật ký `ai.switch.on` hoặc `ai.switch.off`. `GET /admin/ai/status` trả `{enabled, env_ready, switch_on}`.

### 3. Không tạo bảng course/module (4A)
- Giữ một chuỗi bài duy nhất, sắp theo `sort_key` (ADR-035). Kỹ năng và tiên quyết (PR #77) đảm nhận vai trò nhóm nội dung.
- Lý do: còn 10 ngày đến hạn 04/12. Thêm cấp course/module phải đổi ERD, Recommender, tiến độ, trang học và cả dữ liệu đã phát hành, rủi ro vượt lợi ích cho MVP.
- Đây là **điểm lệch so với tài liệu 2.1**, ghi vào báo cáo nộp. Nếu làm sau MVP: thêm bảng `courses` và `modules`, thêm cột `module_id` có thể rỗng vào `lessons`, không phá dữ liệu cũ.

## Hệ quả

- Một Admin có thể cấp quyền cho người khác mà không cần vào CSDL. Rủi ro: Admin cấp nhầm. Giảm rủi ro bằng hộp xác nhận và nhật ký.
- Hai Admin có thể hạ quyền lẫn nhau. Chấp nhận, vì nhóm chỉ có 3 người và có nhật ký.
- Đang có việc soạn bài chạy nền mà tắt công tắc: việc đó đã giữ provider nên chạy hết lượt hiện tại. Từ lần gọi sau, AI không còn chạy.
