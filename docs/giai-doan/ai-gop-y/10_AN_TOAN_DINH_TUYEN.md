# Định tuyến an toàn: khái niệm chưa dạy không được trả lời như đã dạy (09/11/2026)

**Vì sao:** thầy dặn câu hỏi về thứ chưa dạy mà bị trả lời như bài học là lỗi nặng (tính gấp đôi lỗi từ chối nhầm). Mục tiêu: B/C bị trả lời như bài ≤ 2%, A bị từ chối nhầm ≤ 5%.

**Đã làm** (`backend/app/ai/tutor/router.py`, luật tất định, không đổi mô hình):
- `_UNTAUGHT`: ba khái niệm không bài nào dạy (thế đảo, quãng kép/quãng 9+, vòng quãng 5) → luồng B "chưa dạy". Luật tự tắt khi kho bài có đoạn nhắc tới khái niệm (`marker`).
- `later_lesson` khớp cả khi gõ không dấu ("muon hop am"); thêm mẫu L06 "mượn từ/nốt", L07 `#9`, `b9`, `maj9`.

**Số đo (e5 gốc, 50 câu phiếu tham khảo):** B/C trả lời như bài 12% → 0%; A bị từ chối nhầm 13,3% giữ nguyên (chưa đạt ≤ 5%). Bộ GĐ1 mặc định và bộ `test_tam` 200 câu không đổi.

**Giới hạn cần nói thật:**
- Các luật viết sau khi thấy lỗi trên chính 50 câu phiếu, nên 0% KHÔNG phải kết quả độc lập. Trên `test_tam` (câu chưa dùng để viết luật) e5 gốc vẫn còn khoảng 23,5% B/C trả lời như bài.
- Còn sót chủ yếu: hợp âm 6, chuyển/dịch giọng, cadence, gam thứ giai điệu/hòa âm, quan hệ La thứ–Đô trưởng. Một số có thể là nhãn sai (ví dụ dim7 có thể đã dạy ở L02) nên cần Đạt xác nhận trước khi thêm luật, tránh khớp riêng cho bộ đo.
- Cách bền hơn là thêm bài dạy các khái niệm này hoặc train lại với dữ liệu mới (GĐ2c), không phải thêm regex.

**Test:** `backend/tests/test_ai_an_toan_dinh_tuyen.py` (14). pytest cục bộ 1018 đạt, 43 bỏ qua; CI `--min-passed` nâng lên 1018.
