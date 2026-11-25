# HarmonyMentor — bước 1: pre-review tự động dữ liệu context draft

> Đây là bản rà soát kỹ thuật hỗ trợ người duyệt. Không tự thay thế xác nhận chuyên môn hoặc xác nhận quyền sử dụng. Chưa thay đổi metadata dataset.

## Kết luận chung

- Tổng số mẫu: **16** (train: 12, dev: 2, test: 2)
- `reviewed_by_human=true`: **0**
- `rights_cleared=true`: **0**
- Không mẫu nào được tự động chuyển sang trạng thái đã duyệt.

## Kết quả kiểm tra tự động

- Schema/TutorAnswer: đạt ở lần kiểm tra trước.
- Music Engine claims: đạt ở lần kiểm tra trước.
- Tất cả mẫu vượt giới hạn token ban đầu 1.024; cần rút gọn prompt trước preflight production.
- Hai cặp câu hỏi trùng cần người phụ trách quyết định: `context-001`/`context-003`; `context-002`/`context-006`.

## Phiếu quyết định của người duyệt

| ID | Split | Nhóm | Câu hỏi | Kết quả tự động | Quyết định người duyệt | Ghi chú/chỉnh sửa | Nguồn/quyền |
|---|---|---|---|---|---|---|---|
| `context-001` | train | `roman-major` | Am trong C trưởng là bậc mấy? | Xem trùng | **[Giữ/Sửa/Loại]** |  |  |
| `context-002` | train | `roman-natural` | Hợp âm này là bậc mấy? | Xem trùng | **[Giữ/Sửa/Loại]** |  |  |
| `context-003` | train | `explicit-over-ui` | Am trong C trưởng là bậc mấy? | Xem trùng | **[Giữ/Sửa/Loại]** |  |  |
| `context-004` | train | `explicit-over-ui` | Am trong A thứ tự nhiên là bậc mấy? | Cần đọc chuyên môn | **[Giữ/Sửa/Loại]** |  |  |
| `context-005` | train | `missing-context` | Am trong A thứ là bậc mấy? | Cần đọc chuyên môn | **[Giữ/Sửa/Loại]** |  |  |
| `context-006` | train | `missing-context` | Hợp âm này là bậc mấy? | Xem trùng | **[Giữ/Sửa/Loại]** |  |  |
| `context-007` | train | `outside-selected-scale` | E7 trong A thứ tự nhiên có sai nhạc lý không? | Cần đọc chuyên môn | **[Giữ/Sửa/Loại]** |  |  |
| `context-008` | train | `roman-natural` | Bm7b5 trong A thứ tự nhiên là bậc mấy? | Cần đọc chuyên môn | **[Giữ/Sửa/Loại]** |  |  |
| `context-009` | train | `roman-error-hints` | Trong giọng C trưởng, Am7 mang số La Mã nào? Người học vừa nhập i7 và được chấm chưa đúng. | Cần đọc chuyên môn | **[Giữ/Sửa/Loại]** |  |  |
| `context-010` | train | `roman-error-hints` | Trong giọng C trưởng, Am7 mang số La Mã nào? Người học vừa nhập i7 và được chấm chưa đúng. | Cần đọc chuyên môn | **[Giữ/Sửa/Loại]** |  |  |
| `context-011` | train | `roman-error-hints` | Trong giọng C trưởng, Am7 mang số La Mã nào? Người học vừa nhập i7 và được chấm chưa đúng. | Cần đọc chuyên môn | **[Giữ/Sửa/Loại]** |  |  |
| `context-012` | train | `roman-major` | Dm trong C trưởng là bậc mấy? | Cần đọc chuyên môn | **[Giữ/Sửa/Loại]** |  |  |
| `context-013` | dev | `seventh-alias` | Cmaj7 trong A thứ tự nhiên là bậc mấy? | Cần đọc chuyên môn | **[Giữ/Sửa/Loại]** |  |  |
| `context-014` | dev | `seventh-alias` | Fmaj7 trong A thứ tự nhiên là bậc mấy? | Cần đọc chuyên môn | **[Giữ/Sửa/Loại]** |  |  |
| `context-015` | test | `missing-evidence` | Hãy giải thích cấu trúc fugue theo bài học của mình. | Cần đọc chuyên môn | **[Giữ/Sửa/Loại]** |  |  |
| `context-016` | test | `missing-evidence` | Bài học nói gì về hòa âm tứ độ? | Cần đọc chuyên môn | **[Giữ/Sửa/Loại]** |  |  |

## Điều cần xác nhận trước khi chuyển sang bước 2

1. Người phụ trách xác nhận nội dung các mẫu được giữ là đúng.
2. Người phụ trách xác nhận nguồn `HM-ORIGINAL-CONTEXT-DRAFT-V1` được phép dùng cho training nội bộ.
3. Ghi quyết định cho từng mẫu; không đánh dấu toàn bộ chỉ vì đã duyệt quy trình.
4. Sau khi có quyết định, mới cập nhật metadata và xử lý mẫu trùng.

### Cách phản hồi

```text
context-001: Giữ/Sửa/Loại — ghi chú nếu có
context-002: Giữ/Sửa/Loại — ghi chú nếu có
...
Nguồn/quyền sử dụng: Xác nhận/Chưa xác nhận
```
