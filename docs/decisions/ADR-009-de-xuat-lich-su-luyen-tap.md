# ADR-009 (đề xuất) · Bảng `practice_attempts` cho lịch sử Luyện tập

Trạng thái: **Đề xuất 31/10/2026**, nhánh `phuc-music` (Draft PR #18). Chờ Thắng duyệt schema (quyết định 9A của Phúc: schema theo ERD tài liệu 04, lệch ERD thì Thắng duyệt). Phúc chọn phương án không thay cho Thắng duyệt. Số ADR-007 và ADR-008 đã dùng ở nhánh CP2 nên đề xuất này lấy số 009.

## Bối cảnh

- Trang Luyện tập (tài liệu 04, Hình 12) trước đây gọi thẳng `/engine/grade/*` và không lưu gì. Phúc yêu cầu (Bước 2) Luyện tập phải ghi lịch sử học.
- ERD tài liệu 04 có `attempts` (lượt làm câu hỏi đã phát hành, gắn `exercise_version_id`) và `mastery_states`, nhưng không có bảng cho câu sinh ngẫu nhiên. Câu Luyện tập không có `exercise_version_id` nên không thể ghi vào `attempts` mà không phá ràng buộc phiên bản bất biến (ADR-006).
- Cách cập nhật mastery cho câu không thuộc ngân hàng câu hỏi chưa được Thắng chốt (L-1, L-2, L-5 còn mở). Vì vậy theo M-5A, Bước 2 chỉ ghi lịch sử, không cập nhật mastery.

## Quyết định đề xuất

1. Thêm bảng `practice_attempts`: `id`, `user_id` (FK `users`), `kind` (`chord|interval|scale|roman`, CHECK), `level` (`de|vua|kho`, có thể rỗng), `question` (JSON, chỉ các trường của đề), `answer` (JSON), `correct`, `primary_error`, `is_test` (mặc định false), `created_at`. Chỉ mục trên `user_id` và `created_at`.
2. Máy chủ tự chấm bằng Music Engine (`grading.grade_*`). Client không gửi đúng/sai; trường lạ trong đề bị bỏ trước khi lưu.
3. `user_id` lấy từ token (nguyên tắc 4); lịch sử người khác không đọc được. Lượt của Admin có `is_test=true` (nguyên tắc 8).
4. **Không** cập nhật `mastery_states`, không tính vào Recommender hay HitRate/Precision@5. Khi Thắng chốt L-1/L-2/L-5, có thể thêm bước đọc bảng này mà không đổi schema.
5. Migration `e5f1a2b3c4d6` nối vào `d3a7f1c2e905` (PR-3), chỉ tạo bảng mới, `downgrade()` chỉ xóa bảng mới.

## API

- `POST /api/v1/practice/attempts` `{kind, level, question, answer}` → kết quả chấm của Engine (`correct`, `expected`, `message_vi`, `errors`, `primary_error`). Đề thiếu trường → 422 `PRACTICE_QUESTION_INVALID`; `kind` lạ → 400 `VALIDATION_ERROR`.
- `GET /api/v1/practice/history?limit=1..100` → `items` (mới nhất trước) và `stats` theo dạng bài (tính trên toàn bộ lượt).

## Phương án khác đã cân nhắc

- **Ghi vào `attempts`**: phải tạo `exercise_version` giả cho mỗi câu ngẫu nhiên, trái ADR-006 và làm bẩn ngân hàng câu hỏi.
- **Chỉ lưu localStorage**: không theo người dùng qua thiết bị, không có `is_test`, không dùng được cho thống kê sau này.
- **Không lưu gì (giữ như cũ)**: trái yêu cầu Bước 2.

## Hệ quả

- Lệch ERD tài liệu 04: thêm 1 bảng. Nếu Thắng duyệt, nhóm đưa bảng vào Bảng 5 khi làm tài liệu bản 2.2.
- Nếu Thắng không duyệt: gỡ commit `feat(practice)` khỏi `phuc-music` là đủ, migration chỉ tạo bảng mới và chưa lên `main`.

## Kiểm chứng

- `backend/tests/test_phuc_music_practice_history.py` (7 test): chấm bằng Engine, client không tự khai đúng/sai, 422/400, 401, cách ly người dùng, `is_test`, không tạo `attempts`.
- `backend/tests/test_phuc_music_practice_migration.py` (2 test): head đúng, metadata khớp migration, downgrade chỉ xóa bảng mới.

| Người ký | Nội dung | Trạng thái |
|---|---|---|
| Thắng | Duyệt schema `practice_attempts` và việc chưa nối mastery | ____ |
