# ADR-027: Pipeline chatbot nhiều bước và câu lạc đề trả lời ngắn

Trạng thái: đề xuất (G4, góp ý thầy T3). Phần "lạc đề trả lời ngắn" là quyết định của Phúc ngày 14/11/2026. Chờ nhóm (đặc biệt Thắng, người đọc ADR-020) duyệt.

## Quyết định
1. Logic `answer_question` được tách thành 22 Node trong `services/ai_pipeline.py` (sơ đồ: `docs/AI_PIPELINE.md`). Luật định tuyến A/B/C/D/G, ngưỡng và câu trả lời viết sẵn của ADR-017/020 giữ nguyên; toàn bộ test cũ vẫn đạt (chỉ hai test sửa vì câu lạc đề nay gọi AI).
2. **Sửa ADR-020 một điểm**: câu ngoài âm nhạc không còn chỉ bị từ chối. Khi có AI, chatbot trả lời tối đa 2 câu (máy chủ tự cắt, tối đa 280 ký tự) rồi nối câu dẫn về nhạc lý. Giữ từ chối cứng cho: nhóm cấm (bản quyền, tải lậu, mua bán, tấn công), tiêm lệnh, AI tắt/hết hạn mức/lỗi. `OFFTOPIC_MODE=refuse` trả về hành vi cũ.
3. `RAG_STRICT_GROUNDING` (mặc định tắt) cho phép chọn "mình không biết + gợi ý bài" khi truy xuất không đủ tin cậy, thay cho kiến thức chung của Gemini (ADR-020). Mặc định vẫn là ADR-020.
4. `RAG_ENABLED` bật truy xuất qua Qdrant (ADR-026). Điểm là cosine e5 như đường cũ nên ngưỡng giữ nguyên; Qdrant lỗi hoặc chưa nạp thì tự lùi về đường cũ.

## Hệ quả
- Câu lạc đề tốn một lượt Gemini (vẫn tính hạn mức; hết hạn mức thì trả lời từ chối cũ, không báo lỗi).
- Giới hạn tốc độ nằm trong bộ nhớ từng tiến trình (CHAT_RATE_LIMIT_PER_MIN, mặc định 20/phút).
