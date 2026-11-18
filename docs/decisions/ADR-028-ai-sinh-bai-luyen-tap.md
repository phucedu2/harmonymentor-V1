# ADR-028 · AI sinh bài luyện tập (trắc nghiệm và tự luận) từ tài liệu

Trạng thái: đề xuất (Phúc chọn phương án 18/11/2026, chờ Thắng, Đạt duyệt). Liên quan ADR-025, ADR-024, ADR-006, D-3, nguyên tắc 1, 5, 8.

## Bối cảnh
ADR-025 cho AI tóm tắt tài liệu thành bài nháp kèm tối đa 10 câu (trắc nghiệm, dựng hợp âm, dựng âm giai). Phúc muốn AI tạo cả **bài luyện tập**
bám lý thuyết: trắc nghiệm và tự luận, dùng được ở bài học, Quiz kỹ năng và trang Luyện tập. Trang Luyện tập trước đây chỉ có ô gõ đáp án.

## Quyết định (Phúc trả lời 1B 2A 3C 4A 5A 6A 7A 8A 9A)
1. **Ngân hàng theo kỹ năng (1B)**: câu AI soạn nằm trong bài `AI-xxxxxxxx` khi xuất bản, nên tự vào Quiz kỹ năng; trang Luyện tập có thêm thẻ
   **"Từ tài liệu"** lấy câu của các bài AI đã xuất bản, lọc theo kỹ năng và mức.
2. **Trắc nghiệm ở Luyện tập (2A)**: (a) Music Engine sinh 4 phương án cho 4 dạng sẵn có (quãng, hợp âm, âm giai, số La Mã). Phương án sai là lỗi hay gặp:
   M3/m3, A4/d5, đồng âm C#/Db, loại hợp âm/âm giai khác, hoa/thường số La Mã. Mọi phương án được Engine chấm lại: đúng một phương án qua chấm.
   Chấm bài vẫn bằng đúng hàm Engine như khi gõ chữ, lịch sử ghi `"input": "choice"`. (b) câu AI soạn đã duyệt (mục 1).
3. **Tự luận (3C)**: *tự luận ngắn* (gõ tên quãng, số La Mã, tên hợp âm; dựng hợp âm/âm giai) do Engine chấm, tính mastery. *Câu mở* ("vì sao…")
   có đáp án mẫu và 2–5 ý chấm; người học xem đáp án mẫu, AI nhận xét từng ý nếu AI bật. Câu mở **không ghi lượt làm, không tính mastery,
   không chặn hoàn thành bài, không vào Quiz** (AI chấm không tất định). AI tắt/hết lượt (20 lần/người/ngày): người học tự đối chiếu ý chấm.
   Nhận xét AI qua guardrail Engine; có chỗ Engine thấy sai thì ẩn nhận xét.
4. **Kiểm đáp án (4A)**: câu tính được thì AI ghi `check` (interval, roman, chord_tones, scale, chord_name) và **Engine chọn đáp án**; AI chọn sai thì
   Engine sửa và ghi chú cho Admin; không phương án nào (hoặc nhiều hơn một) qua chấm thì loại câu. Câu Đúng/Sai: nếu `scan_reply` kiểm được mọi
   khẳng định trong câu thì Engine quyết Đúng/Sai. Câu Engine không kiểm được có `needs_review`; **xuất bản bị chặn (409 QUESTIONS_NEED_REVIEW)
   tới khi Admin tick "Đã duyệt" từng câu**. AI không tự đánh dấu đã duyệt (chỉ nhận cờ này từ lượt Admin sửa). Sửa đề/đáp án mẫu thì bỏ dấu duyệt.
5. **Mastery (5A)**: câu tất định AI soạn đi qua `/attempts`, tính theo D-3 như câu trong bài. Luyện tập Engine (mục 2a) vẫn không tính (như cũ).
6. **Kỹ năng (6A)**: chỉ kỹ năng có sẵn; kỹ năng lạ thì loại câu.
7. **Dạng câu (7A)**: thêm Đúng/Sai (`true_false`) và chọn nhiều (`multi_select`, cách nhập `multi_choice`, đúng khi chọn đủ và chỉ các phương án đúng).
8. **Mức và số lượng (8A)**: mỗi câu có `level` nhớ/hiểu/vận dụng (lưu `grader_config.difficulty`), ứng với Dễ/Vừa/Khó ở Luyện tập; mỗi phương án sai
   có lời giải thích, hiện khi người học chọn sai. Bản nháp tối đa 20 câu; nút "AI sinh thêm câu" (10 câu/lần, chọn dạng, bỏ câu trùng).
9. **AI tắt (9A)**: trắc nghiệm Engine vẫn chạy; nút AI báo tắt.

## Hệ quả
- `exact` nhận `unordered` cho danh sách; `music_engine` thêm `identify_interval`, `identify_chord`; chiến lược mới `open_rubric` (coi là tự đánh giá).
- API mới: `POST /admin/ai/drafts/{id}/questions`, `POST /practice/options`, `GET /practice/bank/skills`, `GET /practice/bank`, `POST /practice/open-feedback`.
- Không đổi Music Engine, không migration (thêm giá trị JSON; `practice_attempts.kind` giữ 4 dạng).
- Bản nháp cũ: câu trắc nghiệm cũ không có `check` nên phải duyệt trước khi xuất bản.

## Giới hạn đã biết
- Đếm lượt nhận xét AI giữ trong bộ nhớ tiến trình (khởi động lại thì đếm lại); đủ cho demo, cần bảng riêng nếu chạy nhiều tiến trình.
- Số La Mã chỉ giọng trưởng (giới hạn Engine hiện tại). Câu khái niệm (chức năng, lịch sử) phụ thuộc người duyệt.
- Chưa thử với Gemini thật; test dùng AI giả.
