# ADR-040 · Quên mật khẩu, đổi mật khẩu, xác minh email và gửi email

Trạng thái: **Đề xuất** (25/11/2026, nhánh `auth-chuyen-nghiep`). Phúc chốt 12 câu hỏi làm rõ (đều phương án A) và chọn A cho cách đăng ký. Chờ Thắng (backend) và Đạt duyệt qua Draft PR.

Bổ sung cho [ADR-004](ADR-004-hop-dong-xac-thuc.md) (hợp đồng xác thực). Chuẩn tham chiếu: OWASP ASVS 4 chương V2 (Authentication) và V3 (Session), OWASP Forgot Password Cheat Sheet, NIST SP 800-63B mục 5.1.1, WCAG 2.2 AA.

## Bối cảnh

Trước ADR này, người dùng quên mật khẩu thì mất tài khoản: không có quên mật khẩu, đổi mật khẩu, gửi email hay xác minh email. Đăng ký trả `409 EMAIL_TAKEN`, nên ai cũng dò được một email đã có tài khoản hay chưa. Web chỉ chạy bằng Docker trên máy cá nhân của nhóm.

Nguyên tắc vàng: **hệ thống không bao giờ gửi mật khẩu qua email.** Thư chỉ chứa một liên kết dùng một lần để người dùng tự đặt mật khẩu mới.

## Quyết định

### 1. Liên kết dùng một lần (đặt lại mật khẩu, xác minh email)

- Token gốc 32 byte ngẫu nhiên (`secrets.token_urlsafe(32)`, 256 bit). CSDL chỉ lưu SHA-256 (`password_reset_tokens`, `email_verification_tokens`). Ai đọc được CSDL cũng không dùng được liên kết.
- Thời hạn: đặt lại mật khẩu 30 phút, xác minh email 24 giờ. Mỗi lần tạo liên kết mới thì mọi liên kết cũ chưa dùng của người đó hết hiệu lực.
- Dùng liên kết bằng **một câu `UPDATE … WHERE used_at IS NULL … RETURNING`**, giống `rotate_refresh_token`. Hai request song song với cùng liên kết chỉ một cái thắng. Test PostgreSQL `test_pg_auth_reset.py` thả 8 luồng cùng lúc: đúng 1 lượt trả 200, 7 lượt trả 400.
- Kiểm tra mật khẩu mới (yếu, trùng mật khẩu cũ) **trước** khi đốt liên kết, để gõ sai không làm hỏng liên kết.
- **Token nằm sau dấu `#`** (`/dat-lai-mat-khau#token=…`, Phúc chọn 2A). Trình duyệt không bao giờ gửi phần sau `#` lên máy chủ, nên token không lọt vào log nginx/Vite hay header Referer. Trang đọc token, xóa khỏi thanh địa chỉ bằng `history.replaceState`, và đặt `<meta name="referrer" content="no-referrer">`.
- Bấm liên kết chỉ mở trang; trang kiểm tra token bằng **POST** `/auth/reset-password/check`. Máy quét thư (Gmail, Outlook) tự mở liên kết bằng GET nên không thể "dùng mất" liên kết của người dùng.

### 2. Không cho biết email có tài khoản hay không

| Endpoint | Cách làm |
|---|---|
| `POST /auth/forgot-password` | Luôn 202 cùng một câu "Nếu email này có tài khoản…". Việc tra người dùng, tạo token, gửi thư chạy trong `BackgroundTasks` **sau khi** đã trả lời, nên thời gian phản hồi như nhau. Bỏ qua lặng lẽ email lạ, người học mô phỏng (`is_synthetic`), tài khoản bị khóa (`is_active=false`), tài khoản không có mật khẩu. |
| `POST /auth/login` | Giữ như ADR-004: cùng lỗi `INVALID_CREDENTIALS`, so với `DUMMY_HASH` khi email không tồn tại. |
| `POST /auth/register` | Bỏ `409 EMAIL_TAKEN`. Email đã có tài khoản: trả **202** "Hãy kiểm tra hộp thư", không cấp phiên, và gửi cho **chủ email** thư "You already have a HarmonyMentor account" (đăng nhập hoặc đặt lại mật khẩu). Cả hai nhánh đều băm bcrypt để thời gian gần như nhau. |
| `POST /auth/reset-password/check` | Chỉ trả email đã che (`p***@gmail.com`) cho người đang cầm liên kết hợp lệ. |

**Rủi ro còn lại đã chấp nhận (Phúc chọn A trên thẻ quyết định, 25/11).** Email mới thì vẫn đăng nhập ngay để giữ luồng tới bài kiểm tra đầu vào (UC-06), nên người dò vẫn phân biệt được "tạo được tài khoản" với "phải kiểm tra hộp thư". Kẽ hở này hẹp hơn 409 nhiều: mỗi lần dò email chưa có tài khoản là **tạo thật** một tài khoản, mỗi lần dò email đã có tài khoản thì chủ email nhận thư cảnh báo, và đăng ký bị giới hạn 10 lần/IP/giờ. Muốn đóng hẳn thì chuyển sang "xác minh email trước rồi mới vào học" (phương án C trên thẻ). Đổi lại, người mới phải mở thư trước khi học.

### 3. Đổi/đặt lại mật khẩu làm mọi phiên cũ chết ngay

- Cột `users.password_changed_at` (làm tròn tới mili giây). Access token mang thêm claim `pwd` = mốc này tính bằng mili giây lúc cấp token. `get_current_user` từ chối token có `pwd` khác mốc hiện tại.
- **Lệch so với đề bài (so `iat < password_changed_at`):** `iat` của JWT chỉ chính xác tới giây. Token cấp cùng giây với lần đổi mật khẩu sẽ lọt qua; test thực tế đã bắt được trường hợp này (thiết bị B vẫn gọi được `/me`). So bằng `pwd` thì chính xác, và không phụ thuộc đồng hồ.
- Đặt lại mật khẩu: thu hồi **mọi** refresh token, xóa khóa đăng nhập của email đó trên **mọi IP**, điền `email_verified_at` nếu đang trống (11A: mở được thư tức là sở hữu email), gửi thư "Your password was changed". Không tự đăng nhập; frontend chuyển tới `/dang-nhap?da-dat-lai=1`.
- `seed_admin` đặt lại mật khẩu cũng cập nhật `password_changed_at`.

### 4. Đổi mật khẩu khi đang đăng nhập

- **Lệch so với đề bài (đường dẫn):** dùng `POST /api/v1/auth/change-password` thay cho `/api/v1/me/password`. Cookie `hm_refresh` chỉ gửi kèm `/api/v1/auth/*` (ADR-004, để cookie không đi theo mọi request). Muốn giữ đúng phiên hiện tại thì máy chủ phải đọc được cookie đó. Mở rộng `Path` của cookie cho cả `/api/v1` thì rộng hơn mức cần, nên đổi đường dẫn là phương án an toàn hơn.
- Sai mật khẩu hiện tại: 400 `fields.current_password`, **tính vào cùng bộ đếm với đăng nhập** (10A). 5 lần sai trong 15 phút thì cả đổi mật khẩu lẫn đăng nhập đều trả 429. Kẻ chiếm được phiên không đoán mật khẩu cũ vô hạn được.
- `sign_out_others=true` (mặc định): thu hồi mọi refresh token rồi cấp phiên mới cho thiết bị đang dùng (giữ kiểu "ghi nhớ" của phiên cũ). `false`: chỉ xoay phiên hiện tại; thiết bị khác mất access token (do `pwd`) nhưng tự lấy lại bằng refresh token.

### 5. Mật khẩu (4A)

Giữ 3 quy tắc cũ (≥ 8 ký tự, có chữ, có số; NFR-19, để không lệch SRS), giữ chặn > 72 byte (bcrypt), thêm:

- Chặn 1.000 mật khẩu phổ biến nhất: 1.000 dòng đầu `SecLists/Passwords/Common-Credentials/10k-most-common.txt` (giấy phép MIT), chữ thường, lưu cục bộ ở `backend/app/auth/data/common_passwords.txt` và bản sao giống hệt ở `frontend/src/auth/common-passwords.txt` (pytest kiểm hai file khớp). Không gọi dịch vụ ngoài như HIBP. Lưu ý: chỉ 12 trong 1.000 mật khẩu đó qua được 3 quy tắc cũ (ví dụ `password1`, `abcd1234`, `passw0rd`), nên danh sách chủ yếu chặn những mật khẩu kiểu này.
- Chặn mật khẩu chứa phần trước `@` của email (khi phần đó dài ≥ 4 ký tự) hoặc chứa chữ `harmonymentor`.
- Mật khẩu mới phải khác mật khẩu hiện tại.
- Thước đo độ mạnh (Yếu/Khá/Mạnh) tự viết (5A), không thêm thư viện: độ dài, số loại ký tự, trừ điểm chuỗi lặp/liên tiếp. Chỉ để gợi ý; điều kiện bắt buộc vẫn là danh sách trên.
- Bỏ ô "Nhập lại mật khẩu" vì đã có nút hiện mật khẩu (cách Google/Stripe làm).

### 6. Giới hạn tần suất

Module `app/auth/rate_limit.py`, cửa sổ cố định, Redis khi có `REDIS_URL` (khóa `rl:*`), không có thì bộ nhớ trong. Redis lỗi thì cho qua và ghi log (giống khóa đăng nhập).

| Việc | Giới hạn |
|---|---|
| Quên mật khẩu | 3 / email / giờ và 10 / IP / giờ |
| Đăng ký | 10 / IP / giờ (`REGISTER_PER_IP_HOUR`) |
| Gửi lại thư xác minh | 3 / người / giờ |
| Kiểm tra liên kết, đặt lại, xác minh | 30 / IP / giờ (phòng thêm; token 256 bit không dò được) |

Hệ quả: kẻ xấu có thể tiêu hết 3 lượt/giờ quên mật khẩu của một email người khác. Chấp nhận, vì đổi lại chặn được việc dùng hệ thống để spam hộp thư người khác.

### 7. Xác minh email mức "mềm" (A7)

Chưa xác minh vẫn học bình thường, chỉ hiện banner ở Hồ sơ có nút "Gửi lại thư". Tài khoản có email trước migration được coi là đã xác minh. Admin tạo bằng `seed_admin` cũng vậy (12A).

### 8. Ghi nhớ đăng nhập (A8, 3A)

`refresh_tokens.remember` + `session_started_at`. Có tick: cookie `Max-Age` 30 ngày, refresh token gia hạn trượt 30 ngày. Không tick: cookie phiên (không `Max-Age`, mất khi đóng trình duyệt), refresh 1 ngày. Cả hai có trần tuyệt đối 90 ngày tính từ lúc đăng nhập; xoay vòng không kéo dài trần này. Client cũ không gửi `remember` thì mặc định `true` (giữ hành vi cookie lâu dài như trước). `JWT_REFRESH_DAYS` không còn dùng.

### 9. Gửi email

- `app/email/`: giao diện `EmailSender.send(OutgoingEmail)`. `ConsoleSender` (test) giữ thư trong bộ nhớ để test đọc lại và **chỉ ghi log người nhận đã che + tiêu đề**, không ghi nội dung (thư chứa liên kết). `SmtpSender` dùng `smtplib`, bật STARTTLS ở cổng 587, dùng chung cho Mailpit và Gmail.
- Mặc định khi chạy Docker là Mailpit (8A): `EMAIL_BACKEND=smtp`, `SMTP_HOST=mailpit`, xem thư ở http://localhost:8025. Gmail thật: `smtp.gmail.com:587` + Mật khẩu ứng dụng 16 ký tự (7A: Gmail riêng của dự án), hướng dẫn ở README mục "Cấu hình gửi email".
- `SMTP_PASSWORD` không hiện trong `repr(settings)`. `APP_ENV=production` mà `EMAIL_BACKEND=console` thì API từ chối khởi động.
- Lỗi SMTP trong `BackgroundTasks` chỉ ghi log, không làm hỏng request đã trả lời.
- Mẫu thư Jinja2 (tự thoát HTML nên tên người dùng không chèn được mã), HTML dạng bảng + CSS inline + bản chữ thuần, tiếng Anh, có logo nhúng CID (6A: Gmail không tải được ảnh từ `localhost`), nút lớn, liên kết dự phòng dạng chữ. Giờ trong thư đổi mật khẩu theo GMT+7 (ví dụ `25 Nov 2026, 5:39 PM (GMT+7)`), dùng độ lệch cố định vì Việt Nam không có giờ mùa hè. Màu thư lấy từ token "Sân khấu" sáng; ứng dụng email không đọc được biến CSS nên giá trị nằm ở `render.PALETTE`, và test so với `brands.css`.

### 10. Log

Không bao giờ ghi token, mật khẩu hay URL có token. Sự kiện bảo mật ghi vào logger `app.security` với `user_id` + IP: `password_reset_requested`, `password_reset_completed`, `password_changed`, `password_change_wrong_current`, `email_verified`. Test `test_no_token_or_password_in_logs` chạy cả luồng rồi kiểm `caplog` không chứa token, mật khẩu, access token hay email đầy đủ.

## Các mối đe dọa đã chặn

| Mối đe dọa | Cách chặn | Test |
|---|---|---|
| Dò email có tài khoản (quên mật khẩu, đăng nhập) | Cùng câu, cùng mã, việc thật chạy nền | `test_forgot_same_answer_for_existing_and_unknown_email`, E2E email lạ |
| Dò email qua đăng ký | 202 + thư báo chủ email + 10/IP/giờ (còn kẽ hở hẹp, xem mục 2) | `test_register_existing_email_sends_notice_not_error` |
| Lộ CSDL → dùng lại liên kết | Chỉ lưu SHA-256 | `test_only_hash_is_stored` |
| Dùng liên kết hai lần / song song | `UPDATE` có điều kiện | `test_parallel_resets_with_same_link_only_one_succeeds` (PostgreSQL, 8 luồng) |
| Liên kết cũ bị đánh cắp | Hết hạn 30 phút, liên kết mới hủy liên kết cũ, đổi mật khẩu hủy mọi liên kết | `test_new_reset_link_invalidates_old_one`, `test_expired_token_is_rejected` |
| Token lọt qua log/Referer/lịch sử | Token sau `#`, `replaceState`, `no-referrer`, không log URL | E2E kiểm địa chỉ và thẻ meta; `test_no_token_or_password_in_logs` |
| Máy quét thư dùng mất liên kết | Kiểm tra bằng POST | (thiết kế) |
| Kẻ chiếm phiên đổi mật khẩu | Phải nhập mật khẩu hiện tại, chung bộ đếm khóa | `test_change_password_wrong_current_counts_toward_lock` |
| Phiên cũ còn sống sau khi đổi/đặt lại | Claim `pwd`, thu hồi refresh token | `test_reset_full_flow_revokes_everything`, `test_change_password_signs_out_others_and_keeps_current` |
| Spam hộp thư người khác | Giới hạn tần suất theo email và IP | `test_forgot_rate_limits_per_email_and_per_ip` |
| Mật khẩu dễ đoán | Danh sách 1.000 + email + tên sản phẩm | `test_common_passwords_in_sync_and_enforced` |
| Chèn HTML vào thư qua tên hiển thị | Jinja2 tự thoát | `test_email_has_html_text_and_inline_logo` |
| Chạy production mà thư không đi | Chặn khởi động | `test_production_refuses_console_email` |

## Ngoài phạm vi lần này

Đăng nhập Google, danh sách thiết bị đang đăng nhập, mã OTP 6 số, kiểm tra HIBP, đổi email. Web chạy trên máy cá nhân nên liên kết trong thư chỉ mở được trên chính máy chạy Docker (`FRONTEND_BASE_URL`).

## Hệ quả

- 1 migration `c3d4e5f6a7b9` (2 bảng, 4 cột). `alembic check` sạch trên PostgreSQL.
- Docker thêm dịch vụ `mailpit` (cổng 8025 chỉ mở cho máy đang chạy).
- Test cũ đổi theo hành vi mới: `test_auth.py` (đăng ký trùng → 202), `test_pr3_exercise_version.py` (production cần `email_backend="smtp"`), `test_ai_gd3_migration.py` (head mới), live E2E `tai-khoan.live.ts` (bỏ ô nhập lại mật khẩu).
- CI: job "Frontend (Playwright + backend thật)" có thêm service Mailpit và chạy luồng quên/đổi mật khẩu đầu cuối; job này không nằm trong 3 check bắt buộc.
