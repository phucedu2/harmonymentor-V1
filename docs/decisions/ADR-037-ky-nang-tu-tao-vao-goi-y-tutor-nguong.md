# ADR-037: Kỹ năng tự tạo vào mastery và hệ gợi ý, bài tự tạo vào kho AI Tutor, ngưỡng thành thạo theo kỹ năng

- Trạng thái: Đề xuất (Phúc chọn 9A ngày 25/11/2026; chờ nhóm duyệt PR)
- Liên quan: ADR-008 (bảng ánh xạ kỹ năng), ADR-033 (kho AI Tutor), ADR-035/036; FR-ADM-18..23

## Bối cảnh
PR #77 cho Admin thêm kỹ năng `custom.…`, nhưng bảng ánh xạ ADR-008 là hằng số trong code nên `is_mvp()` luôn trả sai cho kỹ năng lạ: làm đúng câu của kỹ năng đó không tạo mastery và không vào vector gợi ý. Bài do Admin tạo (M-…) cũng không vào kho AI Tutor, nên học sinh hỏi về bài đó thì Tutor "không biết".

## Quyết định
1. **Kỹ năng tự tạo phải chọn một trong 10 nhóm MVP** (`note_names`…`rhythm_basics`). Lưu vào `skills.srs_code = group_code` (đúng quy tắc `validate_mapping`: kỹ năng MVP có group = srs). Chọn nhóm hậu MVP bị từ chối.
2. **Bảng ánh xạ gốc vẫn bất biến.** `skill_mapping.mapping_of/is_mvp` tra bảng gốc trước; id bắt đầu bằng `custom.` thì tra thêm từ CSDL, nhớ tạm 30 giây (`is_mvp` được gọi theo từng dòng mastery). Admin tạo/đổi nhóm/xóa thì làm mới ngay trong tiến trình đó; tiến trình khác thấy trong tối đa 30 giây. Kỹ năng tự tạo cũ chưa có nhóm vẫn "ngoài hệ gợi ý" cho tới khi Admin chọn nhóm.
3. **Vector gợi ý 14 chiều không đổi.** Kỹ năng tự tạo cộng vào chiều của nhóm đã chọn như kỹ năng gốc. Đổi nhóm làm đổi chiều, vector tính lại ở lần gợi ý sau (ghi nhật ký `skill.update` với nhóm cũ → mới). Kỹ năng tự tạo chưa có mô tả/embedding nên điểm "nội dung" của nó bằng 0 (hệ gợi ý theo láng giềng vẫn dùng được).
4. **Ngưỡng sẵn sàng/thành thạo theo kỹ năng (FR-ADM-23)** sửa được cho mọi kỹ năng, kể cả gốc, với điều kiện 0 < sẵn sàng < thành thạo ≤ 1. Seed chỉ điền ngưỡng khi trống nên không ghi đè. Mỗi lần đổi ghi nhật ký `skill.thresholds` (giá trị cũ, mới). Đây là điểm lệch nhẹ với ghi chú cũ "đổi ngưỡng phải qua nhóm": Phúc chọn làm FR-23 nên Admin được đổi, có nhật ký để truy lại.
5. **Bài M- đang hiện vào kho AI Tutor** giống bài AI: hiện thì nạp, ẩn/xóa thì gỡ (Qdrant khi bật, đường dự phòng BM25/e5 đọc thẳng CSDL). Nguồn trích dẫn lấy từ nguồn gắn với bài, bài chưa có nguồn thì ghi "Giáo trình do Quản trị viên soạn".
6. **Tutor đọc chữ đã sửa.** Kho đọc payload hiệu lực (bản sửa đã xuất bản, ADR-023) thay vì chữ gốc, và nạp lại ngay khi xuất bản/khôi phục khối của bài AI/M-. Trước đây bài AI sửa chữ rồi xuất bản thì Tutor giữ chữ cũ tới lần hiện/ẩn sau.

## Hệ quả
- Admin chọn sai nhóm thì kỹ năng kéo mastery của nhóm đó lên/xuống: nhóm phải do người hiểu nhạc lý chọn; có nhật ký và đổi lại được.
- Ngân hàng "Từ tài liệu" ở trang Luyện tập vẫn chỉ lấy câu của bài AI; câu của bài M- chưa vào đó (chưa làm).
- Mô hình dự đoán làm đúng (ADR-031) gọi `group_of()` theo bảng gốc: kỹ năng tự tạo rơi vào nhóm "khac" cho tới khi huấn luyện lại.
