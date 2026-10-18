# ADR-001 · Ánh xạ bảng hiện có sang lược đồ SRS 8.2

Trạng thái: **Đề xuất** (Giai đoạn A, 18/10/2026). Người duyệt: Thắng.

## Bối cảnh

Code v0.4.0 có 15 bảng và 2 migration Alembic, thiết kế quanh bài học có phiên bản bài tập (`exercise_versions`) và nguồn tham chiếu từng câu (provenance). SRS 8.2 đề xuất khoảng 25 bảng với tên khác (ví dụ `exercise_attempts`, `flashcards`).

## Phương án

1. Đổi tên toàn bộ cho khớp SRS. Bị loại vì phải viết lại migration, service, test và dữ liệu đã seed, rủi ro cao, không thêm giá trị chấm điểm.
2. **Giữ bảng hiện có, thêm migration cộng thêm, ghi bảng ánh xạ.** Được chọn.

## Quyết định

| SRS 8.2 | Code | Ghi chú |
|---|---|---|
| users | `users` | Thêm cột: email (unique), hashed_password, role, goal_text, goal_embedding vector(384), preferred_instrument, is_active, is_synthetic. Khóa chính giữ dạng chuỗi; người dùng mới dùng UUID |
| courses, modules | (mới) | `lessons.module_id` FK, nullable trong lúc chuyển |
| lessons | `lessons` + `lesson_blocks` | `body_md` của SRS tương ứng các block; thêm `deleted_at`, `source_file` |
| lesson_chunks | (mới) | vector(384), chỉ mục HNSW |
| skills, skill_prerequisites | `skills`, `skill_prerequisites` | Thêm `srs_code` (10 mã SRS 4.3 hoặc `post_mvp`), `embedding`, `mastery_threshold` |
| exercise_templates | (mới) | `type` theo SRS 4.9, `params`, `grading_mode`, `difficulty` |
| exercises | `exercises` + `exercise_versions` | Thêm `exercise_type`, `template_id`, `grading_mode`, `difficulty`, `deleted_at`. Đáp án và cấu hình chấm vẫn ở `exercise_versions` để lượt làm cũ không đổi nghĩa |
| exercise_attempts | `attempts` + `attempt_errors` | Thêm `used_hint`, `instrument`, `attempt_no`, `is_test` |
| flashcards | `review_items` | `front`/`back` giữ dạng chữ; thêm trường JSON cho thẻ có piano/audio khi cần |
| review_states | `review_states` | Thêm `leitner_box` (ADR-002); cột `stage`, `interval_days` bỏ dần |
| mastery_states, chat_sessions, chat_messages, quizzes, quiz_items, recommendation_logs, composition_projects, chord_events, note_events, drum_events, drum_patterns, ai_suggestions | (mới) | Theo đúng SRS 8.2 |
| (không có trong SRS) | `source_works`, `lesson_sources`, `lesson_progress`, `review_attempts` | Giữ: phục vụ nguồn tham chiếu, tiến độ bài học, lịch sử ôn |
| (không có trong SRS) | `refresh_tokens` (mới) | Lưu refresh token đã xoay vòng để thu hồi (NFR-18) |

## Hệ quả

- Hai migration cũ không bị sửa; mỗi giai đoạn thêm migration mới, `alembic check` phải sạch.
- Khi bảo vệ, nhóm trình bày bảng này để giải thích vì sao tên bảng khác SRS.
