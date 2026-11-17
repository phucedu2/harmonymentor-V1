# ADR-026: Qdrant làm kho vector mặc định, đường cũ giữ làm dự phòng

Trạng thái: đề xuất (G3, góp ý thầy T3). Phúc chọn phương án này ngày 14/11/2026 (câu 2A). Chờ nhóm duyệt.

## Bối cảnh
AI Tutor hiện giữ vector đoạn bài trong `lesson_embeddings.json` và tính cosine bằng numpy (ADR-017). Thầy yêu cầu dùng cơ sở dữ liệu vector thật, có lọc theo payload, ngưỡng điểm và nạp được thêm tài liệu ngoài bài học.

## Quyết định
- Thêm dịch vụ `qdrant` vào `docker-compose.yml` (dữ liệu ở volume `qdrantdata`, không mở cổng ra máy).
- `QDRANT_URL` rỗng = tắt Qdrant, AI Tutor chạy đường e5 + BM25 như cũ (nguyên tắc `AI_ENABLED=false` vẫn demo được). G4 sẽ nối pipeline chatbot vào Qdrant khi `RAG_ENABLED` và `QDRANT_URL` cùng bật.
- Mô hình nhúng giữ e5-small (384 chiều, CPU). Đổi mô hình khác chiều thì phải `--recreate` (mã báo lỗi rõ nếu quên).
- Payload mỗi điểm: `source` (lessons|corpus), `lesson_id`, `block_id`, `title`, `lang`, `chunk_idx`, `license`, `text`. Có chỉ mục keyword cho `source, lesson_id, lang, block_id`.
- Id điểm = uuid5(nguồn, khóa, số thứ tự, hash nội dung): nạp lại cùng nội dung không nhân đôi; đoạn không còn trong nguồn bị xóa.
- Cấu hình ở `app/core/ai_config.py` (`RagConfig`). Tên biến `QDRANT_TOP_K` / `QDRANT_MIN_SCORE` khác `RAG_TOP_K` / `RAG_MIN_SCORE` của đường Gemini cũ vì hai thang điểm khác nhau.

## Đánh đổi
Thêm một container (~150 MB RAM khi rảnh). Đổi lại lọc theo payload và nạp corpus ngoài bài học. pgvector (đã có trong Postgres) vẫn là lựa chọn thay thế nếu nhóm muốn bớt một dịch vụ.
