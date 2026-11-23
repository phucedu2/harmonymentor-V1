# AI soạn bài đợt 4: góp ý trong zip "ai-ra-soat" của thầy

Ngày 23/11/2026. Nhánh `claude/ai-soan-bai-dot4`, tách từ `phuc-music` 51c11b0. Quyết định: ADR-034.
Phạm vi do Phúc chốt: **chỉ AI soạn bài**. AI Tutor và fine-tune Qwen do Thắng phụ trách.

## 1. Đối chiếu các gap trong zip với AI soạn bài

Zip được viết trên code trước PR #72, nên một số mục đã xong từ trước.

| Gap / mục | Nội dung | Trạng thái |
|---|---|---|
| 03 §7 (copy_rate) | Đo tỷ lệ chép nguyên văn | **Đã có từ PR #72**: cờ `verbatim`, chuỗi ≥ 12 từ |
| 03 §7, G-03 (bám nguồn) | Ý trong bài có thật ở trang nguồn không | **Đã có từ PR #72**: `low_grounding`, `wrong_page` (TF-IDF/e5) |
| 04 B3 / G-24 (soạn bài) | Hạn mức đếm theo từng lượt gọi | **Đã có từ PR #72**: `budget.py`, mỗi lượt gọi đều tính, kể cả lượt lỗi |
| 04 (kho Tutor) | Bài AI soạn vào kho AI Tutor | **Đã có từ PR #72**: `ai_index.sync_lesson` |
| G-28 (soạn bài) | Lệnh chèn trong tài liệu | **Làm đợt này**: cờ `injection_stripped`, `injection_echo` |
| G-25 | finish_reason, temperature/seed | **Làm đợt này**. Thinking config và ghim SDK để sau (cần thử thật) |
| G-26 | PROMPT_VERSION | **Làm đợt này**: `prompt_version` trong bản nháp và nhật ký |
| Live 23/11 | 3/6 câu không lời giải, 8 câu < 10 | **Làm đợt này**: 8A bắt duyệt, 9A gọi bù 1 lần + cờ `few_questions` |
| G-03 | 10–20 bản nháp Gemini thật, chấm 5 tiêu chí, κ | **Chờ Phúc** chốt bộ tài liệu thử và người chấm (câu 13, 14) |
| G-11 | Dùng quyết định duyệt/sửa của Admin làm nhãn | **Để sau**: `prompt_version` là bước đầu để so được |
| G-02 | Ghi rõ "AI có train" và "AI gọi LLM" | Đưa vào báo cáo cuối: soạn bài = gọi Gemini, không train |
| G-17..G-20 | Fine-tune Qwen3-4B | Ngoài phạm vi (Thắng) |

## 2. Thay đổi

- `backend/app/admin/ai_questions.py`: `EXPLANATION_NOTE`. Câu không phải câu mở mà thiếu lời giải thì `needs_review`.
- `backend/app/admin/ai_service.py`:
  - `MIN_QUESTIONS`, `top_up_questions`, `refresh_shortfall`, `mark_injection`, `prompt_version`.
  - `call_json` nhận biết `MAX_TOKENS`.
  - Sửa tay và "AI sinh thêm câu" đều tính lại cờ thiếu câu.
- `backend/app/admin/ai_job.py`: gọi bù có chống trùng với trang web, ghi bước `top_up` vào nhật ký, thêm mã lời nhắc.
- `backend/app/admin/ai_review.py`: thêm cờ `few_questions`, `injection_stripped`, `injection_echo`.
- `backend/app/ai/tutor/llm.py`: `LLMResult.finish_reason`; `GeminiProvider(temperature, seed)`, giá trị mặc định không đổi.
- `scripts/ai/danh_gia_ai_soan_bai.py`: `--live` chạy với temperature 0, seed 7, và in mã lời nhắc.
- Frontend:
  - Cờ của câu hỏi hiện "(câu N)".
  - Kiểu `question_shortfall` và `prompt_version`.
- Test:
  - `tests/test_ai_soan_bai_dot4.py`: 10 test mới.
  - `tests/conftest.py`: tắt gọi bù trong các test cũ.
  - Fixture cũ thêm lời giải.

## 3. Kiểm chứng

- `pytest -q`: **1583 passed, 44 skipped**. CI nâng `--min-passed` lên 1583.
- `npm test`: 313/313 đạt. `npm run build`: đạt.
- **Chưa chạy với Gemini thật.** Cần chạy trên máy Phúc:
  `docker compose exec api python ../scripts/ai/danh_gia_ai_soan_bai.py --live`.
  Kỳ vọng: không còn câu thiếu lời giải lọt qua mà không cần duyệt. Nếu thiếu câu thì trong nhật ký có bước `top_up`.

## 4. Rủi ro

- Gọi bù tốn thêm 1 trong 12 lượt soạn bài mỗi ngày, khi AI soạn thiếu câu.
- Bộ mẫu `injection_echo` hẹp nên có thể bỏ sót biến thể. Đây chỉ là lớp cảnh báo, người duyệt vẫn đọc bài.
