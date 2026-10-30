# Prompt Claude Code · Giai đoạn B · Thắng (Backend: xác thực và quyền)

Dán toàn bộ khối dưới vào Claude Code, chạy ở thư mục gốc repo sau khi `git pull` nhánh `main`.

```text
Bạn là kỹ sư backend FastAPI/SQLAlchemy cho dự án HarmonyMentor AI. Tôi là Thắng, phụ trách Backend/Engine.

ĐỌC TRƯỚC: CLAUDE.md, docs/giai-doan/phase-A/PHASE_A_PLAN.md (mục 1 N3, N13; mục 5), docs/decisions/ADR-001-anh-xa-csdl.md,
docs/decisions/ADR-004-hop-dong-xac-thuc.md (HỢP ĐỒNG API, frontend đã viết theo đúng file này),
backend/app/main.py, backend/app/core/config.py, backend/app/db/models.py, backend/app/api/*.py, backend/app/contracts/learning.py.

NHÁNH: tạo `phase-b-backend-auth` từ main. Commit nhỏ kiểu `feat(auth): ...`. Không commit .env.

VIỆC CẦN LÀM (FR-AUTH-01..07, 09, 10; NFR-18, NFR-19; N3):
1. Định dạng lỗi chung SRS 7.4 trong `backend/app/core/errors.py`: lớp `AppError(status, code, message, retryable=False, fields=None)`
   + exception handler trả `{"error": {code, message, retryable, fields?}}`. Đổi handler RequestValidationError sang
   400 `VALIDATION_ERROR` có `fields`. Giữ nguyên format lỗi của Music Engine (test cũ phụ thuộc).
2. Migration Alembic MỚI (không sửa 2 migration cũ): thêm vào `users` các cột email (unique, lowercase), hashed_password,
   role ('learner'|'admin', mặc định learner), preferred_instrument (null|'piano'|'guitar'|'drums'), goal_text, is_active,
   is_synthetic (mặc định false); bảng `refresh_tokens` (id, user_id FK, token_hash, expires_at, revoked_at, created_at).
   Cột goal_embedding vector(384) để Giai đoạn D. Người dùng `demo-user` cũ giữ nguyên (email null). `alembic check` phải sạch.
3. Module `backend/app/auth/` (SRS 10.4): bcrypt (thư viện `bcrypt`), JWT HS256 (`PyJWT`), secret từ env `JWT_SECRET`
   (bắt buộc khi không phải môi trường test). Access token 30 phút, refresh token 7 ngày, chỉ lưu HASH của refresh token.
   Endpoint đúng ADR-004: POST /api/v1/auth/register|login|refresh|logout, GET/PATCH /api/v1/me.
   Refresh token qua cookie `hm_refresh` (HttpOnly, SameSite=Lax, Path=/api/v1/auth, Max-Age 7 ngày, Secure theo env
   COOKIE_SECURE). Mỗi lần refresh: thu hồi token cũ, cấp token mới. Logout: thu hồi + xóa cookie, trả 204.
   Mật khẩu ≥ 8 ký tự, có chữ và số. Email trùng → 409 EMAIL_TAKEN. Sai mật khẩu → 401 INVALID_CREDENTIALS (không lộ email có tồn tại không).
4. Khóa đăng nhập: 5 lần sai trong 15 phút theo cặp IP + email → lần thứ 6 trả 429 LOGIN_LOCKED kèm header Retry-After.
   Viết interface `LoginAttemptStore` với 2 bản: Redis (env REDIS_URL, thư viện `redis`) và bộ nhớ trong (dùng khi
   REDIS_URL trống và trong test). Đạt sẽ thêm service Redis vào Docker Compose.
5. Phụ thuộc `get_current_user` (Bearer) và `require_admin` (403 FORBIDDEN). Thêm router `/api/v1/admin/ping` tối thiểu
   để test 403/200 (trang quản trị thật làm ở Giai đoạn F).
6. N3: BỎ `user_id` do client gửi ở MỌI endpoint có dữ liệu cá nhân (`/learning/overview`, `/attempts`,
   `/lessons/{id}/start|complete`, `/review/due`, `/review/{id}/answer`); lấy từ token. Các route này giờ cần đăng nhập (401).
   GIỮ CÔNG KHAI: `/api/v1/engine/*`, `/api/v1/music/*`, `GET /api/v1/lessons` và `GET /api/v1/lessons/{id}` (trang chủ dùng).
   Cập nhật test cũ đang gửi user_id: tạo người dùng test + token qua fixture, không xóa test.
7. `python -m app.seed_admin --email ... --password ...` tạo hoặc nâng quyền admin (không in mật khẩu ra log).
8. Test pytest mới: đăng ký/đăng nhập/refresh xoay vòng (token cũ dùng lại → 401)/logout thu hồi; token hết hạn → 401;
   mật khẩu yếu → 400; email trùng → 409; lần sai thứ 6 → 429; người học gọi /admin/* → 403; người A đọc dữ liệu của
   người B (attempt, review) → 404; route công khai vẫn 200 khi không có token.
9. Cập nhật `backend/requirements.txt`, `.env.example` (JWT_SECRET, COOKIE_SECURE, REDIS_URL; không có giá trị thật),
   README phần chạy backend, `docs/AI_USAGE.md` (thêm 1 dòng), và đổi trạng thái ADR-004 thành "Đã chốt" nếu bạn giữ
   nguyên hợp đồng. Nếu PHẢI đổi hợp đồng, sửa ADR-004 trước và báo Phúc (frontend đang dùng nó).

KIỂM TRA: `cd backend && pytest -q` (dán số passed thật), `alembic -c alembic.ini upgrade head && alembic -c alembic.ini check`.
Chạy thử với frontend: `cd frontend && npm run dev`, đăng ký → vào /app → tải lại trang vẫn đăng nhập → đăng xuất.

KHÔNG: đổi hành vi Music Engine; lưu token thô vào DB; dùng localStorage; thêm thư viện ngoài bcrypt, PyJWT, redis.
CUỐI GIAI ĐOẠN: dừng và báo cáo theo mẫu trong docs/PROMPT_CLAUDE_CODE.md, mở PR vào main, ghi rõ PR frontend
`phase-b-frontend` cần gộp cùng lúc hoặc ngay sau.
```
