# AI sinh bài luyện tập từ tài liệu (18/11/2026)

Quyết định: [ADR-028](../../decisions/ADR-028-ai-sinh-bai-luyen-tap.md). Nhánh `ai-soan-bai/luyen-tap`, Draft PR vào `phuc-music`.

## Đã làm
| Phần | File |
|---|---|
| Chuẩn hóa câu AI, Engine chọn đáp án, cờ cần duyệt, đặc tả xuất bản | `backend/app/admin/ai_questions.py`, `ai_service.py`, `router.py` |
| Trắc nghiệm Engine ở Luyện tập | `backend/app/services/practice_mcq.py`, `api/practice.py` |
| Ngân hàng "Từ tài liệu", Quiz trả cách nhập | `backend/app/services/quiz_service.py` |
| Câu mở: đáp án mẫu + nhận xét AI | `backend/app/services/open_answer_service.py` |
| Chấm chọn nhiều, quãng, tên hợp âm, lời giải từng phương án | `backend/app/services/grading_service.py` |
| Giao diện | `frontend/src/components/learning/AnswerInputs.tsx`, `pages/Practice.tsx`, `pages/app/QuizPage.tsx`, `components/learning/LessonRunner.tsx`, `components/admin/AiDraftTab.tsx` |
| Test | `backend/tests/test_ai_luyen_tap.py` (19 test), sửa `test_admin_ai_tai_lieu.py` theo luật duyệt mới |

## Kết quả chạy
- `pytest -q`: 1467 đạt, 44 bỏ qua (cần PostgreSQL/khóa), 0 lỗi.
- `npx vitest run`: 282 đạt. `npm run build`: đạt.
- Chạy thật trên trình duyệt (SQLite, AI tắt, bản nháp tạo bằng AI giả): trắc nghiệm quãng, thẻ "Từ tài liệu", bài AI có Đúng/Sai, chọn nhiều,
  tự luận ngắn, câu mở, màn duyệt của Admin. Không có lỗi JavaScript.

## Chưa làm / rủi ro
- Chưa chạy với Gemini thật (chờ hạn mức). Chất lượng câu AI soạn phụ thuộc prompt; Engine chỉ bảo đảm đáp án câu tính được.
- Đếm lượt nhận xét AI trong bộ nhớ (xem ADR-028).
