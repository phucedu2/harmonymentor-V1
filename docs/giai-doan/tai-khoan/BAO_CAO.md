# Báo cáo: luồng tài khoản chuẩn (đăng ký, đăng nhập, quên/đổi mật khẩu, xác minh email)

Ngày 25/11/2026 · nhánh `auth-chuyen-nghiep` (từ `phuc-music` @7967d78) · quyết định: [ADR-040](../../decisions/ADR-040-quen-doi-mat-khau-va-email.md) · hợp đồng API: [ADR-004](../../decisions/ADR-004-hop-dong-xac-thuc.md).

## 1. Đã làm

| Luồng | Backend | Frontend |
|---|---|---|
| Đăng ký | Chặn 1.000 mật khẩu phổ biến, email, tên sản phẩm; email đã có → 202 + thư báo chủ email (bỏ 409); 10 lần/IP/giờ; gửi thư xác minh | Bố cục chia đôi, thước đo Yếu/Khá/Mạnh, bỏ ô nhập lại mật khẩu, màn "Kiểm tra hộp thư" |
| Đăng nhập | `remember` (30 ngày / cookie phiên 1 ngày, trần 90 ngày) | "Quên mật khẩu?" cạnh nhãn, giữ email đã gõ, "Ghi nhớ đăng nhập", đếm ngược khi bị khóa |
| Quên → email → đặt lại | `forgot-password` (luôn 202), `reset-password/check`, `reset-password`; token SHA-256, 30 phút, một lần; thu hồi mọi phiên | `/quen-mat-khau` (gửi lại khóa 60 giây), `/dat-lai-mat-khau#token=…` (xóa token khỏi địa chỉ, no-referrer), màn liên kết hết hạn |
| Đổi mật khẩu | `auth/change-password`, chung bộ đếm khóa đăng nhập, giữ phiên hiện tại, tùy chọn đăng xuất thiết bị khác | Thẻ "Bảo mật" ở Hồ sơ, dòng "Đổi lần cuối" |
| Xác minh email | `verify-email`, `resend-verification` (3/giờ), mức mềm | `/xac-minh-email`, banner ở Hồ sơ |
| Email | `app/email/` (Console/SMTP), 4 mẫu thư tiếng Anh HTML + chữ thuần, logo CID, giờ GMT+7 | |
| Dev | Dịch vụ Mailpit trong docker-compose (http://localhost:8025) | |

Ngoài phạm vi: đăng nhập Google, danh sách thiết bị, OTP, HIBP, đổi email.

## 2. File chính

- Backend: `app/auth/{account.py, rate_limit.py, router.py, service.py, security.py, deps.py, login_limiter.py, schemas.py, data/common_passwords.txt}`, `app/email/`, `app/db/models.py`, `migrations/versions/20261125_auth_password_email.py`, `app/core/config.py`, `app/seed_admin.py`.
- Frontend: `pages/public/{LoginPage, RegisterPage, ForgotPasswordPage, ResetPasswordPage, VerifyEmailPage}.tsx`, `pages/public/auth/*`, `pages/app/profile/SecurityCard.tsx`, `components/ui/PasswordField.tsx`, `auth/authApi.ts`, `auth/AuthProvider.tsx`.
- Test: `backend/tests/test_auth_password.py` (30), `backend/tests/test_pg_auth_reset.py` (2, PostgreSQL), `frontend/tests/authPassword.test.ts` (3), `frontend/e2e-live/{mat-khau, truy-cap}.live.ts` (5).
- Hạ tầng: `docker-compose.yml`, `.env.example`, `.github/workflows/ci.yml`.

## 3. Lệnh đã chạy và kết quả (25/11/2026, container cloud)

| Lệnh | Kết quả |
|---|---|
| `cd backend && pytest -q` (trước khi sửa) | 1630 đạt, 46 bỏ qua |
| `cd backend && pytest -q` (sau khi sửa) | 1660 đạt, 48 bỏ qua (thêm 30 test SQLite, 2 test PostgreSQL bỏ qua khi không có CSDL) |
| `TEST_DATABASE_URL=… pytest -m postgres` (PostgreSQL 16 + pgvector cục bộ) | 27 đạt (25 cũ + 2 mới) |
| `alembic upgrade head && alembic check` (PostgreSQL), `downgrade -1` rồi `upgrade head` | sạch, "No new upgrade operations detected" |
| `cd frontend && npm test` | 326 đạt (22 file) |
| `npx tsc --noEmit -p . && npm run build` | đạt |
| `npx playwright test` (giao diện, không backend) | 25 đạt, 3 bỏ qua (như trước) |
| `E2E_MAILPIT=1 MAILPIT_BIN=… npx playwright test -c playwright.live.config.ts` (backend thật + Mailpit 1.33.1) | 12/12 đạt, gồm luồng quên mật khẩu → mở thư qua API Mailpit → đặt lại → mật khẩu cũ hỏng, mới vào được → đổi mật khẩu trong Hồ sơ |
| axe-core (WCAG 2.0/2.1/2.2 A, AA) trên 8 màn × sáng/tối × 1440px/375px | 0 lỗi mức serious/critical; 0 px cuộn ngang ở 375px |
| Phím Tab ở form đăng nhập | Email (tự focus) → Quên mật khẩu? → Mật khẩu → Hiện → Ghi nhớ → Đăng nhập |

### 3a. Chạy toàn bộ sau khi sửa

- SQLite: `1660 passed, 48 skipped in 110.14s`. CI nâng `--min-passed` 1632 → 1662 (CI có thêm vài test chạy được nhờ biến môi trường của job).
- PostgreSQL: `27 passed, 1681 deselected in 16.82s`. CI nâng mức 25 → 27.
- Job CI `frontend-e2e-live` có thêm dịch vụ Mailpit v1.33.1 và `E2E_MAILPIT=1`; job này không nằm trong 3 check bắt buộc.

Chưa chạy: Docker Compose thật (container cloud không có Docker). Phúc cần chạy `docker compose up --build` một lần trên máy để xác nhận dịch vụ `mailpit` và thư hiện ở http://localhost:8025. Gmail thật chưa thử (khóa ứng dụng chỉ có ở máy Phúc).

## 4. Ảnh

`docs/minh-chung/anh/tai-khoan/`: 8 màn (đăng nhập, đăng nhập lỗi, đăng ký, quên mật khẩu, kiểm tra hộp thư, liên kết hết hạn, đặt mật khẩu mới, Hồ sơ – Bảo mật) × sáng/tối × máy tính/điện thoại = 32 ảnh, cộng ảnh thư "Reset your HarmonyMentor password" trong Mailpit. Brand Sân khấu. Dựng lại: `AUTH_ANH=$(pwd)/../docs/minh-chung/anh/tai-khoan E2E_MAILPIT=1 MAILPIT_BIN=<file mailpit> npx playwright test -c playwright.live.config.ts truy-cap`.

## 5. Giải thích cho nhóm

**Liên kết một lần là gì?** Máy chủ tạo một chuỗi ngẫu nhiên 43 ký tự (256 bit), gửi chuỗi đó trong thư, còn CSDL chỉ lưu SHA-256 của nó. Ví dụ: thư có `…#token=kLOvK74i…`, CSDL lưu `3f9a…` (64 ký tự hex). Ai trộm CSDL cũng không đảo ngược được để lấy liên kết. Dùng xong thì cột `used_at` được điền trong cùng một câu `UPDATE … WHERE used_at IS NULL`, nên 8 người bấm cùng lúc chỉ 1 người thành công (test PostgreSQL chứng minh).

**Vì sao trang quên mật khẩu luôn nói "Nếu email này có tài khoản…"?** Nếu trang nói "email không tồn tại", kẻ xấu thử 1.000 email là biết ai học ở đây. Máy chủ trả lời ngay rồi mới tra email ở chế độ chạy nền, nên email có hay không thì thời gian trả lời như nhau.

**Vì sao đổi mật khẩu thì máy khác bị đăng xuất ngay?** Access token có thêm con số `pwd` = thời điểm đổi mật khẩu gần nhất (mili giây). Đổi mật khẩu là con số trong CSDL thay đổi, mọi token cũ mang số cũ bị từ chối ngay, không đợi hết 30 phút.

5 câu giảng viên có thể hỏi:

1. *"Sao không gửi mật khẩu mới qua email?"* Email đi qua nhiều máy chủ và nằm mãi trong hộp thư; mật khẩu gửi đi là mật khẩu đã lộ. Liên kết một lần thì hết hạn sau 30 phút và vô dụng sau khi dùng. (Thắng trả lời)
2. *"Kẻ xấu biết được email có tài khoản không?"* Quên mật khẩu và đăng nhập thì không. Đăng ký còn kẽ hở hẹp đã ghi trong ADR-040 mục 2, kèm lý do chấp nhận và cách đóng. (Thắng)
3. *"Token nằm sau dấu # để làm gì?"* Phần sau `#` không được trình duyệt gửi lên máy chủ, nên không nằm trong log hay header Referer. (Phúc)
4. *"Mailpit là gì?"* Máy chủ thư giả chạy trong Docker, bắt mọi thư để cả nhóm xem mà không cần tài khoản Gmail. Muốn gửi thật thì đổi 5 biến trong `.env`. (Đạt)
5. *"Truy cập cho người khiếm thị?"* Mọi ô có nhãn thật, lỗi nối bằng `aria-describedby`, lỗi tổng có `role=alert` và nhận focus, nút hiện mật khẩu có `aria-pressed`, axe-core 0 lỗi nặng. (Phúc)

## 6. Việc của từng bạn để kiểm

- **Thắng:** đọc `app/auth/account.py`, `router.py` (4 endpoint mới), migration; xác nhận đổi `/me/password` thành `/auth/change-password` (ADR-040 mục 4) và bỏ `409 EMAIL_TAKEN`. Người kiểm: ______
- **Phúc:** chạy `docker compose up --build`, thử đủ 4 luồng, mở http://localhost:8025; xem ảnh sáng/tối; thử Gmail thật theo README. Người kiểm: ______
- **Đạt:** đọc lời 4 thư tiếng Anh (`backend/app/email/templates/`) và chữ tiếng Việt trên các trang. Người kiểm: ______

## 7. Rủi ro và câu hỏi

1. Đăng ký vẫn phân biệt được email mới với email đã có (đã chấp nhận, ADR-040 mục 2). Muốn đóng hẳn: chuyển sang xác minh email trước khi học.
2. Liên kết trong thư trỏ `http://localhost:5173`, chỉ mở được trên chính máy chạy Docker. Demo cho người ngoài thì phải đặt `FRONTEND_BASE_URL` thành địa chỉ họ mở được.
3. Gmail giới hạn khoảng 500 thư/ngày; đủ cho demo.
