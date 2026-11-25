# ADR-035: Quản trị viên tạo, xóa, sắp xếp bài và soạn câu luyện tập bằng form

- Trạng thái: Đề xuất (chờ Phúc duyệt PR)
- Ngày: 24/11/2026
- Liên quan: FR-ADM-13, 15, 16, 24–29; ADR-006 (phiên bản câu hỏi bất biến); ADR-023 (lớp bản sửa); ADR-033 (bài AI ẩn tới khi hiện)
- Người quyết: Phúc chọn 1A (phạm vi) và 5A (câu thủ công qua form, Engine kiểm, sửa tăng version)

## Bối cảnh

Khu Admin trước đây chỉ sửa được chữ khối lý thuyết, ẩn/hiện bài và soạn bài bằng AI. Chưa tạo bài tay, chưa xóa
hay sắp xếp bài, chưa thêm/sửa câu luyện tập. Có một ràng buộc lớn: seed chạy lại **mỗi lần khởi động**. Nó ghi lại
`order_index` của bài L01…L12 và bật lại câu hỏi seed (`deleted_at = None`). Sửa thẳng vào các cột đó thì lần khởi động
sau sẽ mất hết.

## Quyết định

1. **Thứ tự bài nằm ở cột mới `lessons.sort_key`**, xóa mềm ở cột mới `lessons.deleted_at` (migration `d8e9f0a1b2c3`).
   Seed không ghi hai cột này. Bài sắp theo `coalesce(sort_key, order_index*10)`; mỗi lần sắp xếp, `sort_key` được đặt
   theo bước 10 cho mọi bài chưa xóa, nên bài seed mới thêm về sau vẫn chen vào đúng chỗ.
2. **Bài đã xóa được tính là "ẩn"** trong `hidden_lesson_ids`. Như vậy mọi nơi đang lọc bài ẩn (lộ trình, quiz, gợi ý,
   kho AI Tutor, thống kê) cũng lọc luôn bài đã xóa, không phải sửa từng chỗ. Trang bài trả 404, kể cả với Quản trị
   viên. Bài khôi phục được.
3. **Bài mới tạo ở trạng thái ẩn**, giống bài AI (ADR-033): Quản trị viên thêm câu, xem trước rồi bấm hiện.
4. **Form câu hỏi dùng đúng bộ chuẩn hóa của AI soạn bài** (`ai_questions.normalize_question`), có 7 loại câu và 3
   mức độ khó (nhớ/hiểu/vận dụng, FR-ADM-29). Music Engine tính đáp án và đề phải khớp ký hiệu. Câu (trừ câu mở) phải
   có lời giải. Khác AI: Engine tính khác đáp án người soạn thì **từ chối và nói rõ**, không tự sửa giúp.
5. **Sửa câu thêm phiên bản mới** (version + 1, ADR-006). Lưu mà không đổi gì thì không thêm phiên bản. Bỏ câu là
   xóa mềm; lượt làm cũ giữ nguyên.
6. **Form câu hỏi và nút thêm khối chỉ mở cho bài M-… (Quản trị viên tạo) và AI-…**. Câu của bài seed vẫn đổi qua
   `curriculum_specs` vì seed sẽ ghi đè mọi câu sửa tay. Chữ khối lý thuyết của bài seed vẫn sửa được qua lớp bản sửa
   (ADR-023). Xóa và sắp xếp dùng được cho mọi bài.

## Hệ quả

- Đúng nguyên tắc 7 (xóa mềm) và 1 (Engine là nguồn sự thật): frontend chỉ gửi ký hiệu và hiện đáp án Engine trả về.
- CSDL SQLite cũ (tạo bằng `create_all`) cần `alembic -c alembic.ini upgrade head`; Docker tự chạy bước này lúc khởi
  động. App báo lỗi rõ nếu thiếu cột.
- Chưa làm: bài M-… chưa vào kho AI Tutor (kho hiện chỉ nạp bài AI). Chưa có xóa/sắp xếp khối trong bài. Chưa sửa câu
  bài seed qua web.
