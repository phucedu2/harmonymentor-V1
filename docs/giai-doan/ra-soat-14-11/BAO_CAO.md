# Sửa lỗi rà soát còn lại (RS-04, 07, 08, 11, 17, 19, 20, 27, 28, 29), 14/11/2026

Nhánh `claude/project-thread-stuh1j`, đích `phuc-music`. Phúc chốt: Đạt và Thắng đã duyệt, thực thi.

| Mã | Trạng thái | Đã làm | File chính |
|---|---|---|---|
| RS-27 | Xong | Câu xin tư vấn học ("nên học bài nào tiếp") trả lời từ hệ gợi ý, không gọi AI, nhãn "Gợi ý theo tiến độ của bạn" | `services/ai_tutor_service.py` |
| RS-07 | Xong | AI tắt thì nói "chưa tìm thấy trong bài học", không còn câu "tạm nghỉ" kèm bài lạc đề | `ai/tutor/fallback.py` |
| RS-28 | **Một phần** | Không gợi ý "bài gần nhất" khi điểm khớp dưới ngưỡng xám. Phần đoán lại dấu cho câu gõ không dấu đã thử rồi **bỏ**: nó làm câu "hoa tri cua sat la may" (hóa học) thành câu nhạc lý và phá test an toàn định tuyến | `ai/tutor/router.py` |
| RS-29 | Xong | Gemini chờ tối đa 8 giây, thử lại 1 lần (cả khi hết giờ), log ghi mô hình, lần thử, lý do, mã HTTP, loại lỗi; không ghi nội dung lỗi hay câu hỏi | `ai/tutor/llm.py`, `.env.example` |
| RS-19 | Xong | Dấu câu cuối ("Rê.", "La,") không làm lỗi tên nốt | `services/grading_service.py` |
| RS-20 | Xong | HM-011: cách nhập do phiên bản câu hỏi quyết định; `piano` chỉ nhận 12 tên VirtualPiano; 3 mã 422; L04-Q03 lên v2 (ADR-006). 22 test của PR #15 xanh | `services/grading_service.py`, `learning_service.py`, `api/attempts.py` |
| RS-17 | Xong, không migration | Đổi máy thì mở lại ở bước có câu đầu tiên chưa đúng, theo tiến độ máy chủ | `frontend/src/lib/resumeStep.ts` |
| RS-04 | Nháp | 10 câu mới cho 6 kỹ năng còn dưới 3 câu (L05, L06, L07), `status=draft`, đáp án đã chấm thử bằng Engine/bộ chấm | `content/curriculum_specs.py` |
| RS-11 | Nháp | 5 khối nghe "vòng hợp âm quen thuộc" cho L02–L06, `status=draft` (ẩn với người học). Chỉ nói về dạng vòng, không khẳng định bài hát cụ thể nào | `content/draft_specs.py` |
| RS-08 | **Chưa làm** | Đề xuất bên dưới, cần Thắng chốt số | |

## RS-08: đề xuất chờ Thắng

Kiểm tra đầu vào đặt kỹ năng lên 0,65 khi đúng một câu (`PLACEMENT_SCORE`). 6/12 câu là trắc nghiệm nên đoán trúng cũng được 0,65, vượt ngưỡng 0,6 mở bài. Đề xuất: câu trắc nghiệm đúng chỉ đặt 0,45 (dưới ngưỡng), câu gõ chữ đúng giữ 0,65. Đổi số này thay đổi gợi ý và khóa bài của mọi người học, nên chưa sửa. Cần Thắng chọn con số và chạy lại bộ đánh giá gợi ý.

## Cần Đạt duyệt trước khi phát hành

10 câu RS-04 (đổi `status` thành `published` từng câu, ID mới nên không cần tăng version) và 5 khối RS-11 (bỏ `"status": "draft"` trong payload). Câu RS-04 mới cũng cần nạp vào kho AI Tutor nếu muốn AI trích.

## Kiểm chứng

- `pytest -q`: 1297 passed, 44 skipped (PostgreSQL cần `TEST_DATABASE_URL`, chưa chạy ở máy này).
- `npm test`: 277 passed. `npm run build`: đạt.
- Chưa thử Gemini thật cho RS-27, RS-28, RS-29 (khóa ở máy Phúc); các test dùng AI giả.
