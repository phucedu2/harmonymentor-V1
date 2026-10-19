# ADR-002 · Lịch ôn tập Leitner 5 hộp thay cho 1–3–7–14–30

Trạng thái: **Đã chốt** (nhóm xác nhận M2, 18/10/2026). Thực hiện ở Giai đoạn C, người làm: Thắng.

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
