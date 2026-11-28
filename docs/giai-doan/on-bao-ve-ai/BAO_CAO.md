# Ôn bảo vệ AI soạn bài: sửa điểm yếu hội đồng dễ hỏi (ADR-042), 28/11/2026

Phúc nhờ đặt câu hỏi khó nhất hội đồng (thầy cô CNTT + âm nhạc) có thể hỏi về AI soạn bài trong Admin, soạn câu trả lời,
rồi sửa ngay các điểm yếu thật. Bộ 22 câu hỏi (3 mức) nằm trong Claude Doc "Ôn bảo vệ: AI soạn bài trong Admin".

## Đã sửa

| # | Điểm yếu | Sửa | File |
|---|---|---|---|
| W1 | Bộ đếm lượt thấp hơn số Google tính (AI Studio 507/500) | Đếm mọi lần gọi HTTP: lần lỗi, mô hình dự phòng, vòng soạn lại của Tutor | `ai/tutor/llm.py`, `ai/budget.py`, `admin/ai_service.py`, `services/ai_tutor_service.py` |
| W2 | 429 theo phút làm dừng việc như hết lượt ngày, đốt mô hình dự phòng | Soạn bài giãn 4,5 giây/lần gọi; 429 theo phút chờ 30 giây thử lại cùng mô hình; việc nền chờ thêm 60 giây làm lại phần đó; lý do dừng mới `rate_minute`; mã lỗi `AI_RATE_MINUTE`/`AI_RATE_DAY` | `ai/tutor/llm.py`, `admin/ai_job.py`, `admin/router.py`, `AiDraftTab.tsx` |
| W4 | Không có số đo chất lượng AI thật | `content.ai_stats` chụp lúc soạn; `GET /admin/ai/quality`; mục "Chất lượng AI soạn bài" trong tab AI soạn bài | `admin/ai_service.py`, `admin/router.py`, `AiDraftTab.tsx`, `api.ts` |

Chưa làm: W3 (chạy Gemini thật trên 3–5 tài liệu, cần máy Phúc), W5 (dịch nguyên đoạn từ sách tiếng Anh không bị bắt: ghi là giới hạn).

## Kiểm chứng

- `pytest -q`: 1693 đạt + 46 bỏ qua (21 test mới trong `tests/test_adr042_dem_luot_gemini.py`; sửa 1 test cũ cho 429 theo ngày).
- Vitest 327 (thêm `ratePct`), `npm run build` đạt.
- Chạy app với AI giả, tạo bản nháp, bỏ 1 câu, sửa 1 câu: bảng hiện 1 bản nháp, 3 câu AI giữ, qua Engine 33%, người sửa 1, người bỏ 1 (ảnh `bang-chat-luong-ai.png`; giờ đặt lại hiện 08:00 vì máy thử chạy giờ UTC, máy Việt Nam hiện 15:00).
- Chưa thử với Gemini thật.
