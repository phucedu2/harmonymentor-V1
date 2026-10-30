# ADR-002 · Lịch ôn tập Leitner 5 hộp thay cho 1–3–7–14–30

Trạng thái: **Đã chốt** (nhóm xác nhận M2, 18/10/2026). **Đã thực hiện 20/10/2026** (nhánh `audit-nguoi-moi-hoc`, chờ Thắng duyệt): dùng lại cột `stage` (= hộp − 1) thay vì thêm cột `leitner_box`, nên không cần migration; API trả thêm `leitner_box`. Hàng đợi giới hạn 20 thẻ theo hạn; ưu tiên kỹ năng yếu (mastery < 0.60) chưa làm vì chưa có mastery EMA.

## Bối cảnh

`backend/app/services/review_scheduler.py` đang dùng `REVIEW_INTERVALS_DAYS = [1, 3, 7, 14, 30]`, trả lời đúng có thể nhảy 2 bậc. SRS 4.6.1 chốt Leitner 5 hộp với khoảng 1, 2, 4, 8, 16 ngày.

## Quyết định

- Hộp 1..5 tương ứng 1, 2, 4, 8, 16 ngày.
- Đúng: lên 1 hộp (tối đa hộp 5). Sai: về hộp 1.
- Hàng đợi mỗi lần tối đa 20 thẻ, xếp theo: quá hạn lâu nhất → thuộc kỹ năng yếu (mastery < 0.60) → hộp thấp hơn.
- Thêm cột `review_states.leitner_box`; migration chuyển `stage` cũ sang hộp (`stage 0→1, 1→2, 2→3, 3→4, 4→5`).

## Ví dụ

Thẻ "G7 gồm những nốt nào?" ở hộp 3 (ôn lại sau 4 ngày). Trả lời đúng → hộp 4, hẹn 8 ngày sau. Trả lời sai → hộp 1, hẹn ngày mai.

## Hệ quả

- `test_review_answer_advances_1_3_7_14_30_schedule` phải viết lại theo lịch mới (đây là thay đổi hành vi có chủ đích, không phải làm hỏng test).
- Trang Tiến độ hiển thị hộp Leitner thay cho số ngày.

## Bổ sung 30/10/2026: ôn trước hạn và thẻ mới (HM-012)

Trạng thái: **Nhóm chốt 30/10/2026** (Phúc chọn phương án A). Thực hiện ở Draft PR #14.

Bối cảnh: rà soát 29/10 tái hiện được lỗi thẻ lên từ hộp 1 tới hộp 5 trong vài giây vì code cũ cho lên hộp cả khi thẻ chưa đến hạn. Thẻ mới cũng đang hẹn sau 1 ngày, trái với tài liệu 04 mục 6.4 (bản 2.1).

Quyết định, theo 04 mục 6.4:
- Thẻ mới vào hộp 1 và đến hạn ngay khi bài được hoàn thành.
- Đúng khi đã đến hạn (kể cả quá hạn): lên một hộp, tối đa hộp 5; hẹn theo khoảng của hộp mới.
- Đúng khi chưa đến hạn: giữ hộp và giữ ngày hẹn cũ.
- Sai (hoặc tự đánh giá "again"), dù đến hạn hay chưa: về hộp 1, hẹn sau 1 ngày.
- Mức "hard" không có trong 04 mục 6.4. Nhóm giữ nó như sau: đúng nhưng chật vật thì giữ hộp; nếu đã đến hạn thì hẹn lại theo khoảng của hộp hiện tại, nếu chưa thì giữ ngày hẹn cũ. "easy" xử lý giống "good" (vẫn chỉ lên 1 hộp).
- Không viết migration: thẻ đã kích hoạt trước bản sửa vẫn giữ ngày hẹn cũ (chậm nhất 1 ngày), chỉ thẻ kích hoạt sau bản sửa mới đến hạn ngay.

Hệ quả: hai test cũ mặc định thẻ mới hẹn sau 1 ngày và ôn liên tiếp vẫn lên hộp nên được viết lại theo luật mới (`test_audit_nguoi_moi.py`, `test_phase1_learning_vertical_slice.py`). Test mới ở `backend/tests/test_hm012_leitner.py`.
