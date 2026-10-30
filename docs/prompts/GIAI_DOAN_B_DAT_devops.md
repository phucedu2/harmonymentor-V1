# Prompt Claude Code · Giai đoạn B · Đạt (DevOps: Docker, Redis, middleware)

Dán toàn bộ khối dưới vào Claude Code, chạy ở thư mục gốc repo sau khi `git pull` nhánh `main`.

```text
Bạn là kỹ sư DevOps/backend cho dự án HarmonyMentor AI. Tôi là Đạt, phụ trách AI/NLP/DevOps.

ĐỌC TRƯỚC: CLAUDE.md, docs/giai-doan/phase-A/PHASE_A_PLAN.md (mục 1 N15, mục 5), docs/decisions/ADR-004-hop-dong-xac-thuc.md,
docker-compose.yml, backend/app/main.py, backend/app/core/config.py, frontend/vite.config.ts.

NHÁNH: tạo `phase-b-devops` từ main. Commit nhỏ kiểu `feat(devops): ...`. Không commit .env hay API key.

PHÂN VIỆC GIAI ĐOẠN B: Thắng làm xác thực + định dạng lỗi chung SRS 7.4 (`backend/app/core/errors.py`) + bộ đếm khóa
đăng nhập; Phúc làm frontend. Bạn KHÔNG sửa các phần đó, chỉ cung cấp hạ tầng để chúng chạy.

VIỆC CẦN LÀM (SRS 10.2, NFR hiệu năng/vận hành, N15):
1. Docker Compose 4 service: `db` (image pgvector/pgvector:pg16, healthcheck pg_isready), `redis` (redis:7-alpine,
   healthcheck), `api` (Dockerfile ở backend/, Python 3.11-slim, chạy `alembic upgrade head` rồi uvicorn, depends_on db+redis
   healthy), `web` (Dockerfile ở frontend/: build Vite rồi phục vụ bằng nginx). nginx: chuyển `/api/` sang `api:8000`
   CÙNG ORIGIN (cookie refresh của ADR-004 cần điều này) và `try_files $uri /index.html` cho mọi đường dẫn khác (SPA,
   ví dụ tải lại /app/ho-so không được 404). Tên service và cổng theo SRS 10.2; nếu khác thì ghi lý do (N15).
2. `.env.example` ở gốc: DATABASE_URL, REDIS_URL, JWT_SECRET (giá trị mẫu rõ là giả), COOKIE_SECURE=false, CORS_ORIGINS,
   AI_ENABLED=false, GEMINI_API_KEY= (để trống). Compose đọc `.env`; README hướng dẫn `cp .env.example .env`.
3. Migration Alembic MỚI tạo `CREATE EXTENSION IF NOT EXISTS vector` (bỏ qua khi dialect là sqlite để test vẫn chạy).
   Phối hợp với Thắng nếu cả hai cùng thêm migration (tránh 2 head: `alembic heads` chỉ được 1).
4. Middleware trong `backend/app/core/middleware.py`: header `X-Response-Time` (ms) cho mọi response; log cấu trúc JSON
   một dòng mỗi request (method, path, status, duration_ms, request_id) KHÔNG ghi body/token/mật khẩu; header `X-Request-ID`.
   Script `scripts/p95.py` đọc log và in p95 theo route (để làm bảng p95 cuối kỳ).
5. CORS theo env `CORS_ORIGINS` (danh sách phân tách dấu phẩy, mặc định rỗng vì frontend gọi cùng origin).
6. `/health` trả trạng thái db và redis (200 khi cả hai sống, 503 kèm tên phần lỗi).
7. Test pytest: có X-Response-Time và X-Request-ID; log không chứa chuỗi mật khẩu khi gọi /api/v1/auth/login
   (bỏ qua test này nếu nhánh của Thắng chưa gộp, ghi rõ); /health 503 khi Redis tắt (dùng mock).
8. Cập nhật README (chạy bằng Docker từ máy sạch: `cp .env.example .env && docker compose up --build`, mở
   http://localhost:<cổng web>), `docs/AI_USAGE.md` (thêm 1 dòng).

KIỂM TRA: `docker compose up --build` trên máy bạn, mở trang chủ thấy chương trình học; `curl -i localhost:<cổng>/api/v1/lessons`
có X-Response-Time; `cd backend && pytest -q` (dán số passed thật). Không chạy được Docker thì ghi "chưa chạy" và lý do.

KHÔNG: đưa API key thật vào repo; mở cổng Postgres/Redis ra ngoài khi không cần (chỉ cần cho dev thì ghi chú);
thêm dịch vụ ngoài 4 service trên.
CUỐI GIAI ĐOẠN: dừng và báo cáo theo mẫu trong docs/PROMPT_CLAUDE_CODE.md, mở PR vào main.
```
