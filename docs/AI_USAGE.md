# Nhật ký sử dụng AI

Giảng viên cho phép dùng AI để viết code với điều kiện ghi rõ. Mỗi dòng ghi: giai đoạn, công cụ, AI đã làm gì, nhóm đã kiểm tra gì.

| Ngày | Giai đoạn | Công cụ | AI đã làm | Nhóm kiểm tra | Người kiểm |
|---|---|---|---|---|---|
| trước 18/10 | v0.2 → v0.4.0 | Trợ lý AI (theo các tài liệu `docs/PHASE_*`) | Music Engine, CSDL học tập, bài L01–L04, LessonRunner | Test tự động (113 passed) | (nhóm bổ sung) |
| 18/10 | CP1 | Claude Code | `docs/CP1_*.md`, `backend/_cp1/*.py`, `backend/tests/test_cp1_evidence.py` (9 test mới, không đổi hành vi Engine) | `pytest` 167 passed; ví dụ trong tài liệu chạy lại được | (điền) |
| 18/10 | A | Claude Code | Chạy test/build, `docs/PHASE_A_PLAN.md`, `docs/PHASE_A_TRUY_VET_FR.md`, ADR-001..003, `CLAUDE.md`, sửa README | Nhóm đọc và duyệt N10–N15, khung 12 bài, thiết kế, lịch (19/10) | (điền) |
| 19/10 | B (frontend) | Claude Code | Tailwind + React Router + TanStack Query, trang chủ, đăng nhập/đăng ký, route bảo vệ, layout `/app`, hồ sơ, đổi tên Composition Lab, ADR-004; prompt Giai đoạn B cho Thắng và Đạt | `npm run build` đạt; 24 kịch bản trình duyệt (Playwright, auth giả lập theo ADR-004) đạt | (Phúc điền) |
| 19/10 | B (backend) | Claude Code | `backend/app/auth/`, `core/errors.py`, migration users + refresh_tokens, bỏ `user_id` từ client (N3), `seed_admin`, 18 test xác thực/phân quyền, sửa 3 file test cũ sang token | `pytest` 185 passed; 15 kịch bản trình duyệt với backend thật đạt | (Thắng điền) |
| 19/10 | B (DevOps) | Claude Code | Dockerfile api/web, nginx, docker-compose 4 dịch vụ, `.env.example` theo SRS 10.3, migration pgvector, middleware X-Response-Time/X-Request-ID/log JSON, CORS, `/health`, `scripts/p95.py`, 6 test | `pytest` 191 passed; `docker compose up` 4 dịch vụ healthy, 15 kịch bản trình duyệt qua nginx đạt | (Đạt điền) |
| 20/10 | Gộp v0.5.3 | Claude Code | Đưa mã zip v0.5.3-dev (Phase 2.3: piano/âm thanh/ký âm, Bài 1 nhiều giọng) lên nền v0.4.0 rồi gộp với `main` (Giai đoạn B); sửa test sang token và mã bài `v4`; `Practice` dùng `VirtualPiano`, `Piano.tsx` SVG giữ cho trang chủ; `tsconfig` lib ES2021 và 2 lỗi kiểu TS để `npm run build` đạt; tạo lại `package-lock.json` | `pytest` 220 passed; `npm run build` đạt; chạy thử Bài 1 trong trình duyệt với đăng nhập thật | (Phúc điền) |
| 20/10 | Kiểm định người mới học (v0.5.4) | Claude Code | Chạy thử web bằng tài khoản học sinh mới, viết `docs/AUDIT_NGUOI_MOI_HOC.md`; sửa chấm điểm (bỏ chấm theo từ khóa ở bài 1–4, chuẩn hóa dấu nối, tên Đô–Rê–Mi, piano chỉ chấm cao độ, nối `grading_mode`/`root_position_only`), lời giải sau 2 lần sai, hoàn thành bài cần đúng mọi câu, Leitner 1-2-4-8-16 (ADR-002), thẻ ôn tự đánh giá, bài học chia bước, Luyện tập theo mức Dễ/Vừa/Khó, Việt hóa giao diện; 39 test mới, sửa 4 test cũ theo hành vi mới | `pytest` 259 passed (SQLite); `npm run build` đạt; chụp màn hình trước/sau | (Phúc, Thắng điền) |

Nguyên tắc nhóm: không gộp code AI viết khi chưa có người trong nhóm đọc diff và giải thích lại được.
