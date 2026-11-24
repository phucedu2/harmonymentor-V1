# ADR-034: AI soạn bài áp góp ý trong zip "ai-ra-soat" của thầy (đợt 4)

- Trạng thái: Đề xuất (Phúc chốt 7A, 8A, 9A ngày 23/11/2026, chờ Phúc duyệt Draft PR vào `phuc-music`)
- Ngày: 23/11/2026
- Liên quan: ADR-033 (đợt 3), ADR-028 (câu luyện tập), ADR-018 (không fine-tune LLM)
- Báo cáo: `docs/giai-doan/ai-soan-bai-dot4/BAO_CAO.md`

## Bối cảnh

Thầy gửi bộ rà soát `ai-ra-soat.zip` (gap G-01..G-33). Phúc giới hạn phạm vi luồng này vào **AI soạn bài**. Phần
AI Tutor và fine-tune Qwen3-4B (G-17) do Thắng phụ trách. Lần chạy Gemini thật ngày 23/11 (PR #73) cho thấy thêm
hai vấn đề: 3/6 câu không có lời giải nhưng vẫn qua mà không cần duyệt, và AI chỉ soạn 8 câu, giữ lại 6 (dưới mức 10).

## Quyết định

1. **Câu thiếu lời giải phải duyệt (8A).** `normalize_question` thêm ghi chú `EXPLANATION_NOTE` cho mọi câu không phải
   câu mở mà không có `explanation`, kể cả câu Engine đã kiểm. Lý do: thiếu lời giải thì câu chỉ chấm điểm chứ không dạy.
   Câu mở đã có rubric riêng nên không cần.
2. **Thiếu câu thì gọi bù đúng 1 lần (9A).** Bản nháp có ít hơn `MIN_QUESTIONS` = 10 câu hợp lệ thì
   `ai_service.top_up_questions` gọi Gemini thêm một lần, dùng lời nhắc "sinh thêm câu", và tính vào hạn mức soạn bài.
   - Câu bù đi qua đúng cửa kiểm như câu thường. Luồng chạy nền có thêm bước chống trùng với các câu đã có.
   - Câu AI chép lại y nguyên thì bỏ, không ghi lý do.
   - Nếu vẫn thiếu, hoặc hết hạn mức, hoặc lượt gọi bù lỗi, thì vẫn tạo bản nháp và gắn cờ `few_questions`. Cờ tự gỡ
     khi Quản trị viên sửa tay hoặc bấm "AI sinh thêm câu" đến đủ 10 câu.
   - Không gọi lần thứ hai, vì hạn mức chỉ có 12 lượt mỗi ngày.
3. **Lệnh chèn: cảnh báo, không chặn (7A, G-28 áp cho soạn bài).** Cổng tải lên vốn đã bỏ các dòng giống lệnh điều khiển
   AI. Đợt này thêm hai cờ:
   - `injection_stripped`: tài liệu có dòng đã bị lọc.
   - `injection_echo`: chữ trong khối hoặc câu của bài nháp có dạng lệnh hoặc lộ khóa. Bộ mẫu ở đây hẹp hơn bộ mẫu của
     Tutor, vì mẫu "quên … quy tắc" của Tutor bắt nhầm câu nhạc lý như "đừng quên quy tắc bè".
   - Mỗi cờ phải được tick "Đã đối chiếu" thì mới xuất bản được, giống các cờ của ADR-033.
4. **finish_reason (G-25).** `LLMResult.finish_reason` đọc từ Gemini. Nếu JSON hỏng vì `MAX_TOKENS`, lần thử lại sẽ
   nhắc AI viết ngắn hơn, thay cho câu nhắc "JSON hợp lệ" (câu đó không giúp được vì lần sau vẫn bị cắt). Lỗi báo cho
   Admin cũng nói rõ là bị cắt.
5. **Mã phiên bản lời nhắc (G-26).** `prompt_version` là băm của system, schema và lời nhắc gọi bù, nên không cần nhớ
   tăng số tay. Mã được ghi vào bản nháp và nhật ký `ai.draft.create`, để sau này so tỷ lệ duyệt và sửa giữa các phiên bản.
6. **Chạy đánh giá tái lập (G-25).** `GeminiProvider` nhận `temperature` và `seed`. Mặc định giữ 0,2 và không seed,
   nên Tutor không đổi. `danh_gia_ai_soan_bai.py --live` đặt temperature 0, seed 7.

## Không làm trong ADR này

- Cấu hình thinking và ghim phiên bản `google-genai`: cần thử Gemini thật trên máy Phúc trước.
- G-21..G-24, G-27, G-29, G-32, G-33 (AI Tutor) và G-17..G-20 (Qwen): ngoài phạm vi, do Thắng phụ trách.
- G-03, chấm 10–20 bản nháp theo 5 tiêu chí và tính κ: chờ Phúc chốt tài liệu thử và người chấm.

## Hệ quả

- Bản nháp mới có thể tốn 2 lượt Gemini thay vì 1, nếu AI soạn thiếu câu.
- Các test cũ dựng FakeProvider theo kịch bản "mỗi bản nháp 1 lượt gọi". `tests/conftest.py` tắt gọi bù mặc định;
  test về gọi bù gắn `@pytest.mark.top_up`.
