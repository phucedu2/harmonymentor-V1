# ADR-014 · Embedding Gemini thay MiniLM, lưu vector trong file JSON kèm hash

Trạng thái: **Đã chọn mô hình** (Q-B, Thắng và Đạt duyệt 04/11/2026, Phúc báo trong thread). Phần lưu trữ (mục 3) **Thắng duyệt 04/11/2026** cùng các migration GĐ1–GĐ2 (tin nhắn "Thắng duyệt hết" Phúc gửi trong thread). Có hiệu lực.

## Bối cảnh

04 ERD ghi `lesson_chunks.embedding vector(384)` và `users.goal_embedding vector(384)` cho MiniLM chạy cục bộ. Đề pipeline cấm cài PyTorch/sentence-transformers và cấm dựng microservice, nên MiniLM không chạy được trong backend. GĐ0 đã xác nhận bằng `models.list` rằng `gemini-embedding-001` và `gemini-embedding-2` có sẵn với khóa của nhóm.

## Quyết định

1. **Mô hình:** `gemini-embedding-001`, rút còn 768 chiều (`output_dimensionality`), tác vụ `RETRIEVAL_DOCUMENT` cho nội dung và `RETRIEVAL_QUERY` cho câu hỏi/mục tiêu. Gemini trả vector chưa chuẩn hóa khi rút chiều, nên backend chuẩn hóa mọi vector về độ dài 1 (`app/ai/embedder.py`).
2. **Biến môi trường:** `EMBEDDING_MODEL`, `EMBEDDING_DIM` (tên theo 03 Bảng cấu hình). Đổi mô hình thì phải chạy lại hai lệnh dựng vector và hiệu chỉnh lại `RAG_MIN_SCORE`.
3. **Lưu trữ:** nội dung công khai (26 mô tả kỹ năng, 45 đoạn bài học) được tính sẵn và commit trong `app/content/skill_embeddings.json`, `app/content/lesson_embeddings.json`, mỗi mục kèm `hash` của văn bản và tên mô hình. Không tạo bảng `lesson_chunks` với `vector(384)`:
   - kho chỉ vài chục đoạn, cosine trong bộ nhớ dưới 1 ms;
   - file đi cùng commit nội dung, nên phiên bản vector luôn khớp phiên bản bài;
   - retriever chỉ dùng vector khi hash và mô hình khớp nội dung hiện tại; lệch thì cả lượt dùng BM25 (không trộn vector cũ với mới);
   - test `test_index_file_matches_current_chunks` báo khi sửa bài mà quên dựng lại.
   Vector mục tiêu người học (dữ liệu cá nhân) lưu ở `users.goal_embedding` dạng JSON kèm `goal_embedding_model` (migration GĐ2, đã duyệt Q-E).
4. **Dự phòng:** AI tắt, thiếu khóa hoặc Gemini lỗi: hệ gợi ý cho content = 0 (đề GĐ2), AI Tutor truy xuất bằng BM25 cục bộ.

## Hệ quả

- Không cần pgvector cho GĐ2–GĐ3. Khi kho vượt vài nghìn đoạn mới cần xét lại (bảng + chỉ mục HNSW như 04).
- Cosine của Gemini bị nén (mô tả kỹ năng 0,59–0,78; câu hỏi trong và ngoài phạm vi sát nhau quanh 0,60), nên ngưỡng phải đo, không lấy 0,35 của MiniLM. Số đo ở báo cáo ai-gd3 mục C.
- Gửi cho Gemini chỉ văn bản bài học công khai, mô tả kỹ năng, mục tiêu học và câu hỏi (03 Bảng 3).

## Cách làm lại

```bash
cd backend && AI_ENABLED=1 GEMINI_API_KEY=... python -m app.ai.build_skill_embeddings
cd backend && AI_ENABLED=1 GEMINI_API_KEY=... python -m app.ai.build_index
```
