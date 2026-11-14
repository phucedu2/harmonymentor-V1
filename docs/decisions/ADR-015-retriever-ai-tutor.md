# ADR-015 (đề xuất) · Retriever và AI Tutor: truy xuất, kiểm Music Engine, dự phòng

Trạng thái: **Đề xuất 04/11/2026**, chờ **Thắng** (backend) và **Đạt** (AI/NLP) duyệt. Nhánh `ai/gd3-tutor`. Kế hoạch gốc: kế hoạch AI Tutor 02/11 (Phúc trả lời 10 câu, 7A).

Cập nhật 04/11/2026 (demo 10/11, Thắng duyệt, Phúc báo trong thread): thêm công cụ thứ tư `get_roman_numeral(key, chord)` vào guardrail. Khẳng định "<số La Mã> trong/của <giọng trưởng> là <hợp âm>" (hai chiều) được kiểm: hợp âm thuận giọng so số La Mã Engine; hợp âm ngoài giọng mà số La Mã là một bậc thuận giọng → contradicted; còn lại (V/V, giọng thứ) → unsupported, không bao giờ verified. `maj7` = `M7` theo ADR-016. Các phần khác của ADR này vẫn là đề xuất.

## Quyết định

### 1. Kho kiến thức
Chỉ khối lời giảng của bài đã phát hành (L01–L04). Bỏ khối bài tập (có `exercise_id`), khối nháp, bài nháp L09–L12. Chia theo khối, 80–100 từ, không cắt giữa câu, không ghép hai khối. Mỗi đoạn có `chunk_id = block_id#n`, nguồn (tác phẩm · vị trí) và hash.

### 2. Truy xuất
Cosine trên vector Gemini, top_k 4, ngưỡng `RAG_MIN_SCORE = 0,60` (đề ghi 0,35 cho MiniLM; đã đo lại, xem báo cáo mục C). Dự phòng BM25 cục bộ có bỏ hư từ tiếng Việt và thêm bản bỏ dấu. BM25 **không** phân biệt được câu ngoài phạm vi, nên ở chế độ dự phòng việc chặn ngoài phạm vi dựa vào bộ phân loại ý định.

### 3. Ý định
TF-IDF n-gram ký tự 2–4 + LogisticRegression (7A), huấn luyện từ `intent_data.json` (Claude soạn, 135 câu train, 30 câu test). Câu ngoài phạm vi (xác suất ≥ 0,5) bị từ chối **trước** khi gọi embedding hay LLM, nên không tốn lượt.

### 4. Gọi Gemini
`gemini-3.5-flash-lite`, hết giờ 15 giây, thử lại 1 lần khi 429/503 bằng `gemini-3.6-flash`, không thử lại khi hết giờ (người học đã chờ 15 giây). Đầu ra JSON theo schema 04 Bảng 13 qua `response_json_schema`; schema không có trường `verified`.

### 5. Kiểm câu trả lời (máy chủ, không tin AI)
- Định dạng sai, trích dẫn có `block_id` không truy xuất ở lượt đó, hoặc khẳng định nhạc lý mâu thuẫn Music Engine: soạn lại **đúng 1 lần** kèm dữ kiện Engine đúng.
- Lần 2: trích dẫn lạ thì bỏ trích dẫn đó; mâu thuẫn Engine hoặc sai định dạng thì dùng câu viết sẵn.
- Tiêu đề trích dẫn lấy từ kho, không lấy chữ AI viết.
- Guardrail quét cả `engine_claims` AI khai lẫn reply: "ký hiệu + dãy nốt", "âm giai + dãy nốt", tên nốt tiếng Việt (Đô Mi Sol, thăng/giáng). Nhãn "Đã kiểm bằng Music Engine" chỉ khi có ít nhất một khẳng định và tất cả verified.
- Thay function calling bằng **tra trước**: máy chủ tìm ký hiệu hợp âm trong câu hỏi, gọi `get_chord_tones`, đưa kết quả vào prompt và ghi vào `tool_calls` (TC-12). Lý do: một lượt gọi LLM thay vì hai, và AI không chọn được công cụ sai.

### 6. Chống prompt injection (NFR-08)
Ba lớp: (a) bộ lọc mẫu tấn công rõ ràng trước LLM; (b) lệnh chỉ ở system_instruction, mọi dữ liệu (đoạn bài, lịch sử, dữ kiện Engine, câu hỏi) nằm trong khối đánh dấu, chuỗi đánh dấu trong dữ liệu bị vô hiệu hóa; (c) chuỗi canh gác trong system prompt, xuất hiện trong reply thì chặn ngay, không cho soạn lại.

### 7. Giải thích lượt làm sai
Đường dẫn theo 04: `POST /chat/explain-attempt` (đề ghi `/tutor/explain-attempt`; tài liệu thắng). Chủ lượt làm mới gọi được (khác thì 404). Mã lỗi đọc từ CSDL, client không gửi được. Gửi cho Gemini: đề bài, mã lỗi, tên kỹ năng, đoạn bài của kỹ năng. **Không gửi** đáp án, câu trả lời của học sinh, chi tiết lỗi. Mức 1→3 tự tăng theo số lần hỏi; mức 1–2 kiểm lộ đáp án (dãy nốt, chuỗi đáp án) rồi soạn lại/dự phòng; mức 3 mới có dữ kiện Engine của đề và lời giải đã duyệt.

### 8. Hạn mức
`AI_DAILY_QUOTA = 30` lượt gọi LLM / người / ngày VN (429, tin nhắn vẫn lưu); câu bị từ chối và câu trả lời dự phòng không tốn lượt. `AI_GLOBAL_DAILY_BUDGET` cho cả hệ thống, vượt thì dùng câu viết sẵn.

### 9. Lưu trữ
`chat_sessions`, `chat_messages`, `chat_feedback` đúng cột 04 Bảng 7 (migration `e3c4d5e6f7a8`, chỉ thêm). `tool_calls` (JSON) ghi đường đi (llm/out_of_scope/unsure/ai_off…), số lần gọi LLM, mô hình, cách truy xuất, đoạn đã dùng, dữ kiện Engine.

## Chưa làm (ghi rõ, không giả)
- `quiz` luôn null: quiz_items cần Music Engine sinh đáp án (04 Bảng 7), để giai đoạn sau.
- Chưa có công cụ `roman_numeral`, `secondary_dominant` trong `music_engine/tools.py`, nên câu như "ii–V–I trong C gồm Dm7 G7 Cmaj7" chưa được kiểm (không gắn nhãn).
- Bộ phân loại ý định học từ 135 câu do Claude soạn; độ chính xác 30/30 trên tập test nhỏ, cần đo trên câu hỏi thật ở GĐ4.
