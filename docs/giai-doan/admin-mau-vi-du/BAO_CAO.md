# Admin: mẫu câu hỏi và khối ví dụ (FR-ADM-30, 35..37), 25/11/2026

## Đã làm
- **Mẫu câu có tham số** (`backend/app/admin/question_templates.py`): nốt hợp âm, nốt âm giai, tên quãng, số La Mã. Xem trước (không ghi gì) rồi lưu thành câu thật; Engine dựng đề, đáp án, lời giải; tổ hợp không dựng được bị loại kèm lý do; lưu lại không nhân đôi. Giao diện: nút "Tạo câu từ mẫu" (`TemplatesPanel.tsx`).
- **Khối ví dụ** (`backend/app/admin/example_blocks.py`, `ExamplesPanel.tsx`): ví dụ hợp âm, ví dụ âm giai (Engine tính nốt, người học bấm nghe bằng Web Audio), ví dụ nghe mp3/wav ≤ 5 MB, bắt buộc nguồn và giấy phép. Người học xem ở `ExampleBlocks.tsx`.
- Bảng `media_files` (migration `b2c3d4e5f6a8`, guard ở `session.py`), route phát `/api/v1/media/{id}`.
- Khối ví dụ hợp âm/âm giai vào kho AI Tutor. ADR-038.
- Sửa khối ví dụ tại chỗ (`PUT /lessons/{id}/examples/{block}`: Engine tính lại nốt, nhật ký giá trị cũ); xóa khối ví dụ nghe xóa luôn file âm thanh, không để file mồ côi.

## Kiểm chứng
pytest 1631 đạt + 44 bỏ qua; Vitest 313; `npm run build` đạt. Trình duyệt thật (AI giả): tạo bài, thêm ba loại ví dụ (ký hiệu sai và thiếu giấy phép bị từ chối đúng), tạo 4 câu từ mẫu, màn người học hiện đủ khối và trình phát phục vụ file `audio/wav`.

## Chưa làm
- Mẫu cho câu nhiều lựa chọn; mẫu do Admin tự định nghĩa.
- Nút nghe chưa kiểm bằng loa thật (chạy ở trình duyệt không có thiết bị âm thanh).
