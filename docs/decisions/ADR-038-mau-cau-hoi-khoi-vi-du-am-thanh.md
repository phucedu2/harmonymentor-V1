# ADR-038: Mẫu câu hỏi có tham số, khối ví dụ hợp âm/âm giai/âm thanh, lưu file âm thanh trong CSDL

- Trạng thái: Đề xuất (Phúc chọn 7A, 8A ngày 25/11/2026; chờ nhóm duyệt PR)
- Liên quan: ADR-006 (phiên bản câu bất biến), ADR-035; FR-ADM-30, FR-ADM-35..37

## Bối cảnh
Admin soạn từng câu bằng form (PR #77) nên tạo 20 câu "Hợp âm X gồm những nốt nào?" rất chậm. Bài tự tạo chỉ có khối chữ, chưa có ví dụ nghe được.

## Quyết định
1. **Mẫu câu có tham số** (`admin/question_templates.py`): bốn mẫu cố định trong code (nốt của hợp âm, nốt của âm giai, tên quãng, số La Mã trong giọng). Admin điền danh sách tham số, máy sinh tích Descartes (tối đa 30 câu, mỗi ô tối đa 12 giá trị), **xem trước rồi mới lưu**. Đề, đáp án và lời giải đều do Music Engine dựng; không có AI, không có đáp án gõ tay (nguyên tắc 1). Tổ hợp Engine không dựng được (ví dụ F#7 trong giọng C) bị loại và nêu lý do. Câu lưu đi qua đúng đường `_normalize` + `_insert_exercise` của form soạn câu nên là câu bình thường, phiên bản 1 bất biến (ADR-006). Câu có đề trùng đề đã có trong bài thì bỏ, nên lưu lại cùng mẫu không nhân đôi.
2. **Ba loại khối ví dụ** chỉ cho bài M-/AI-: `example_chord` và `example_scale` (Engine tính các nốt lúc lưu; giao diện chỉ hiển thị và phát bằng Web Audio), `example_audio` (mp3/wav tối đa 5 MB). Khối ví dụ hợp âm/âm giai có đoạn mô tả do Engine dựng nên vào kho AI Tutor như khối lý thuyết. Muốn đổi thì xóa khối rồi thêm lại.
3. **File âm thanh lưu trong CSDL** (bảng `media_files`, migration `b2c3d4e5f6a8`), phát qua `GET /api/v1/media/{id}`. Lý do: sao lưu cùng dữ liệu, không thêm ổ đĩa cho Docker; 5 MB mỗi file là đủ cho ví dụ ngắn. Kiểm đuôi file **và** byte đầu (RIFF/WAVE, ID3 hoặc khung MPEG) để không nhận file đổi tên. **Nguồn và giấy phép bắt buộc** (nguyên tắc 11: không đưa nội dung có bản quyền vào mà không rõ nguồn); hiển thị dưới trình phát cho người học.
4. Đường phát công khai theo mã ngẫu nhiên 32 ký tự hex, vì thẻ `<audio>` không gửi được token. Chấp nhận được với âm thanh ví dụ bài học (nội dung vốn dành cho người học); không dùng cho dữ liệu cá nhân.

## Hệ quả
- Xóa khối ví dụ nghe xóa luôn file; sửa khối ví dụ tại chỗ, chỉ đổi chữ với ví dụ nghe (đổi file thì xóa khối rồi thêm lại).
- Chưa có mẫu cho câu nhiều lựa chọn, thêm mẫu mới phải sửa code.
