# ADR-025 · AI tóm tắt tài liệu nhạc lý thành bản nháp bài học

Trạng thái: đề xuất (chờ Thắng, Đạt duyệt). Ngày 12/11/2026. Liên quan ADR-023, ADR-006, nguyên tắc 1, 5, 11, SRS 03 Bảng 3.

## Quyết định
1. **Ai dùng**: chỉ Quản trị viên (Đạt). Không có đăng ký admin qua web.
2. **Tải lên**: PDF, DOCX, MD, TXT, tối đa 10 MB. Bắt buộc ghi nguồn (sách, tác giả, năm) và tick "tôi có quyền dùng tài liệu và hiểu nội dung trang được chọn sẽ gửi tới Gemini". Chỉ lưu chữ đã trích theo trang, không lưu tệp gốc. PDF ảnh quét chưa hỗ trợ (cần OCR).
3. **AI chỉ soạn bản nháp**: tóm tắt, diễn đạt lại (không chép nguyên văn), ghi số trang cho từng khối, gợi ý tối đa 10 câu. Tối đa 15 trang và 14.000 ký tự mỗi lần, 20 bản nháp/24 giờ/admin. Tài liệu nằm trong thẻ dữ liệu, prompt dặn bỏ qua mệnh lệnh trong tài liệu. Không gửi email, tên hay mã người dùng.
4. **Music Engine giữ quyền quyết định nhạc lý**: câu "dựng hợp âm/âm giai" chỉ nhận ký hiệu từ AI, đáp án do Engine tính; câu trắc nghiệm bị loại nếu đáp án không nằm trong phương án; ký hiệu Engine không hiểu bị loại. Mọi nốt/hợp âm/quãng/số La Mã trong lời văn được `scan_reply` soát, chỗ lệch gắn cờ, xuất bản khi còn cờ phải tick xác nhận. Soát lại lúc xuất bản.
5. **AI không tự xuất bản**. Chỉ khi Admin bấm xuất bản mới tạo Lesson (mã `AI-xxxxxxxx`, xếp cuối danh sách), khối lý thuyết, câu hỏi phiên bản 1 đã phát hành (ADR-006), nguồn kèm "trang N" và ghi chú "tóm tắt bằng AI, đã được Admin duyệt". Bài đã xuất bản sửa chữ tiếp qua Quản trị bài học (ADR-023); câu hỏi không sửa được (muốn đổi thì tạo bài mới).
6. **AI tắt** (`AI_ENABLED=false` hoặc chưa có khóa): tính năng báo tắt, xem được bản nháp cũ, phần còn lại của Admin vẫn chạy.
7. Nhật ký thao tác cho tải lên, tạo nháp, sửa, xuất bản, từ chối.

## Giới hạn đã biết
- Bài do AI soạn chưa vào kho AI Tutor (chỉ mục dựng thủ công từ nội dung gốc) và chưa có thẻ ôn.
- Engine chỉ soát được khẳng định có dạng nốt/hợp âm/quãng/số La Mã; lời văn khác (lịch sử, thuật ngữ) phải do Admin đọc đối chiếu.
- Độ dài trang của DOCX/MD/TXT là "đoạn" chia theo độ dài (~3.000 ký tự), không phải trang in.
- Chưa thử với Gemini thật; test dùng AI giả.
