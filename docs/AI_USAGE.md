# Nhật ký sử dụng AI

Giảng viên cho phép dùng AI để viết code với điều kiện ghi rõ. Mỗi dòng ghi: giai đoạn, công cụ, AI đã làm gì, nhóm đã kiểm tra gì.

| Ngày | Giai đoạn | Công cụ | AI đã làm | Nhóm kiểm tra | Người kiểm |
|---|---|---|---|---|---|
| trước 18/10 | v0.2 → v0.4.0 | Trợ lý AI (theo các tài liệu `docs/PHASE_*`) | Music Engine, CSDL học tập, bài L01–L04, LessonRunner | Test tự động (113 passed) | (nhóm bổ sung) |
| 18/10 | CP1 | Claude Code | `docs/CP1_*.md`, `backend/_cp1/*.py`, `backend/tests/test_cp1_evidence.py` (9 test mới, không đổi hành vi Engine) | `pytest` 167 passed; ví dụ trong tài liệu chạy lại được | (điền) |
| 18/10 | A | Claude Code | Chạy test/build, `docs/PHASE_A_PLAN.md`, `docs/PHASE_A_TRUY_VET_FR.md`, ADR-001..003, `CLAUDE.md`, sửa README | Đọc và duyệt quyết định N10–N15, lịch, thiết kế | (điền) |

Nguyên tắc nhóm: không gộp code AI viết khi chưa có người trong nhóm đọc diff và giải thích lại được.
