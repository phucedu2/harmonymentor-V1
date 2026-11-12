# ADR-011 (đề xuất) · Lộ trình đi thẳng theo SRS 2.1 Bảng 7

Trạng thái: **Đề xuất 01/11/2026**, nhánh `phuc-music`. Phúc chọn giữ lộ trình đi thẳng (01/11). Cần nhóm duyệt; nếu chấp nhận thì sửa câu mở đầu SRS 2.1 mục 4.1 trong file `.docx` gốc (repo không tự sửa SRS).

## Bối cảnh

- SRS 2.1 mục 4.1 có hai câu không khớp nhau:
  - "Người học đi từ phần nền tảng, **rẽ vào một trong ba nhánh** (hòa âm chức năng, Pop, Jazz), rồi gặp lại nhau ở bài thực hành."
  - Ngay dưới Bảng 7: "**Thứ tự học là thứ tự trong bảng**, không phải thứ tự mã bài."
- `phuc-music` Bước 2 (commit `05c85f6`) làm theo câu thứ hai: một danh sách 12 bài M1 → M2 → M3 → M4 → M5.
- Hiện chỉ L01–L04 có nội dung chạy được. M2 và M3 mỗi module có một bài chưa có nội dung (L05, L06) và một bài nháp (L11) hoặc không có bài nào khác.

## Quyết định đề xuất

1. **Đi thẳng theo Bảng 7.** "Bài tiếp theo" là bài đầu tiên có câu hỏi mà người học chưa hoàn thành, bỏ qua bài chưa có nội dung. Không khóa bài: người học vẫn mở được bài bất kỳ.
2. **M2, M3, M4 là ba nhóm nội dung, không phải ba lộ trình riêng.** Chưa làm màn chọn nhánh.
3. Đề nghị sửa câu mở đầu SRS 4.1 thành: "Người học đi từ phần nền tảng qua ba module hòa âm chức năng, Pop và Jazz theo thứ tự Bảng 7, rồi tới bài thực hành tích hợp. Người học có thể mở bài bất kỳ, bài không bị khóa."

## Lý do

- **Đồ thị kỹ năng cho phép thứ tự này** (26 kỹ năng, 36 cạnh, không đổi): L05 và L06 chỉ cần kỹ năng của L02–L03, không cần L04; guide tones của L04 là tiền đề của L08, và L08 vẫn đứng sau L04; L09 (âm giai thứ) đứng trước L06, khớp tiền đề `scale.parallel_minor`.
- **Rẽ nhánh lúc này chưa có gì để chọn**: mỗi nhánh mới có 0–1 bài có nội dung. Làm rẽ nhánh cần thêm dữ liệu nhánh người học chọn, màn chọn nhánh, cách tính "bài tiếp theo" và tiến độ theo nhánh.
- **Không khóa bài** nên người muốn học Jazz trước vẫn vào thẳng M4 được; đi thẳng chỉ quyết định gợi ý, không giới hạn người học.

## Hệ quả

- Số "Bài n" là vị trí trong danh sách đang hiện: ii–V–I (L04) là **Bài 6**. Slide, kịch bản demo và tài liệu còn gọi "Bài 4 ii–V–I" cần sửa.
- Mức Luyện tập gợi ý "Khó" mở sau L03 thay vì L04 (`frontend/src/pages/Practice.tsx`), vì mức Khó chỉ dùng kiến thức L01–L02 ở mọi giọng.
- Nếu sau này làm rẽ nhánh: thêm trường "nhánh đã chọn" cho người học và lọc "bài tiếp theo" theo nhánh; thứ tự bài trong mỗi module giữ nguyên, không phải đổi dữ liệu bài.

## Cần duyệt

- Thắng: lộ trình và cách tính "bài tiếp theo" (`learning_service.visible_lessons`, `Learn.tsx`).
- Cả nhóm: câu sửa cho SRS 4.1.
