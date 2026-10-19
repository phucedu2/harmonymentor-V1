# ADR-004 · Hợp đồng API xác thực giữa frontend và backend

Trạng thái: **Đã chốt** (Giai đoạn B, 19/10/2026). Frontend (nhánh `phase-b-frontend`) và backend (nhánh `phase-b-backend-auth`) đều cài đặt đúng hợp đồng này; muốn đổi thì sửa ADR trước.

## Bối cảnh

SRS mục 7 có `POST /auth/register`, `/auth/login`, `/auth/logout`, `GET/PATCH /me`; NFR-18 yêu cầu access token 30 phút, refresh token 7 ngày, xoay vòng mỗi lần dùng, thu hồi khi đăng xuất. Frontend và backend làm song song nên cần chốt hình dạng request/response trước.

## Quyết định

**Nơi giữ token.** Access token chỉ nằm trong bộ nhớ JS (biến trong `frontend/src/lib/http.ts`), không ghi `localStorage`, để một lỗi XSS không lấy được token dài hạn. Refresh token nằm trong cookie `hm_refresh` do backend đặt: `HttpOnly`, `SameSite=Lax`, `Path=/api/v1/auth`, `Max-Age=604800`, `Secure` khi chạy HTTPS. Khi tải lại trang, frontend gọi `/auth/refresh` để lấy lại phiên.

Vì sao không dùng `localStorage` cho cả hai: đơn giản hơn nhưng refresh token 7 ngày sẽ đọc được bằng JS. Vì frontend gọi API cùng origin (Vite proxy ở dev, reverse proxy ở Docker), cookie hoạt động mà không cần cấu hình CORS credentials.

**Tiền tố** `/api/v1`. Mọi lỗi theo SRS 7.4: `{"error": {"code": "...", "message": "...", "retryable": false}}`; lỗi kiểm tra dữ liệu thêm `"fields": {"password": "..."}`.

| Phương thức | Đường dẫn | Quyền | Body | Thành công |
|---|---|---|---|---|
| POST | `/auth/register` | Công khai | `{email, password, display_name}` | 201 `AuthResponse` + đặt cookie |
| POST | `/auth/login` | Công khai | `{email, password}` | 200 `AuthResponse` + đặt cookie |
| POST | `/auth/refresh` | Cookie | (trống) | 200 `AuthResponse` + cookie mới (cookie cũ bị thu hồi) |
| POST | `/auth/logout` | Cookie | (trống) | 204, thu hồi refresh token, xóa cookie |
| GET | `/me` | Bearer | | 200 `User` |
| PATCH | `/me` | Bearer | `{display_name?, preferred_instrument?}` | 200 `User` |

```jsonc
// AuthResponse
{ "access_token": "eyJ...", "token_type": "bearer", "expires_in": 1800, "user": User }
// User
{ "id": "uuid", "email": "phuc@example.com", "display_name": "Phúc",
  "role": "learner",                 // "learner" | "admin"
  "preferred_instrument": "piano",   // "piano" | "guitar" | "drums" | null
  "goal_text": null }                // sửa qua PUT /me/goal ở Giai đoạn D
```

Mã lỗi frontend đang xử lý:

| HTTP | `code` | Khi nào |
|---|---|---|
| 400 | `VALIDATION_ERROR` | Email sai định dạng; mật khẩu < 8 ký tự hoặc thiếu chữ/số (NFR-19); `preferred_instrument` lạ |
| 401 | `INVALID_CREDENTIALS` | Sai email hoặc mật khẩu (không nói rõ cái nào sai) |
| 401 | `UNAUTHORIZED` | Thiếu, sai hoặc hết hạn access token; refresh token không hợp lệ |
| 403 | `FORBIDDEN` | Người học gọi `/admin/*` |
| 404 | `NOT_FOUND` | Tài nguyên không có hoặc thuộc người khác |
| 409 | `EMAIL_TAKEN` | Email đã đăng ký |
| 429 | `LOGIN_LOCKED` | Lần đăng nhập sai thứ 6 trong 15 phút theo IP/email; kèm header `Retry-After` (giây) |

**Luồng 401.** Khi một request có Bearer bị 401, frontend gọi `/auth/refresh` đúng một lần (các request đồng thời dùng chung lời gọi đó) rồi gửi lại; refresh cũng 401 thì coi như hết phiên và chuyển về `/dang-nhap?next=…`.

**Route giữ công khai.** `/api/v1/engine/*`, `/api/v1/music/*` (Music Engine tất định, không có dữ liệu cá nhân) và danh sách bài học `GET /lessons` (trang chủ dùng để hiện chương trình học, FR-VIS-02) không cần token. Các route có dữ liệu cá nhân (`/learning/*`, `/attempts`, `/lessons/{id}/start|complete`, `/review/*`) lấy `user_id` từ token và bỏ hẳn trường `user_id` client gửi lên (N3).

## Hệ quả

- Frontend đã ngừng gửi `user_id`; trước khi backend xong phần auth, các route đó vẫn dùng mặc định `demo-user` như cũ.
- Nhánh frontend chỉ gộp sau (hoặc cùng lúc) nhánh auth của backend, vì `/app/*` cần đăng nhập.
- Docker (Đạt): dịch vụ `web` phải chuyển `/api` sang `api` cùng origin và trả `index.html` cho mọi đường dẫn khác (SPA).
- Đăng nhập trên nhiều tab cùng lúc có thể làm một tab dùng refresh token vừa bị xoay; tab đó sẽ bị đăng xuất. Chấp nhận ở MVP.
- Refresh token là chuỗi ngẫu nhiên 48 byte, CSDL chỉ lưu SHA-256. Xoay vòng bằng một câu `UPDATE … WHERE revoked_at IS NULL`, nên hai request dùng cùng token thì chỉ một cái thành công.
- Khóa đăng nhập đếm theo cặp IP + email, cửa sổ cố định 15 phút tính từ lần sai đầu. Redis lỗi thì cho đăng nhập tiếp (vẫn kiểm tra mật khẩu) và ghi log, để sự cố Redis không khóa mọi người.
- Thẻ ôn tập là nội dung bài học công khai: người B trả lời thẻ mà B chưa kích hoạt nhận 409 `REVIEW_STATE_NOT_ACTIVE`, không ảnh hưởng lịch ôn của người A. Dữ liệu cá nhân (lịch ôn, lượt làm, tiến độ) luôn lọc theo người trong token.
