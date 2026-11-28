# ADR-024 · Quiz 10 câu theo kỹ năng (FR-14 rút gọn)

Trạng thái: đề xuất (chờ Thắng, Đạt duyệt). Ngày 12/11/2026. Liên quan FR-14, FR-AI-18, ADR-006, D-3.

## Quyết định
- Quiz là tối đa 10 câu LẤY TỪ NGÂN HÀNG của đúng một kỹ năng, không sinh câu mới bằng AI. FR-AI-18 gốc ("Engine tạo câu, AI viết phương án nhiễu") chuyển sang hướng phát triển.
- Lý do: câu trong ngân hàng đã được Engine kiểm đáp án và nhóm duyệt khi phát hành; câu AI sinh lúc chạy thì chưa ai duyệt, trái nguyên tắc "AI chỉ gợi ý".
- Chọn câu: chưa làm → từng sai → đã đúng; loại câu tự đánh giá, câu retired/ẩn, bài bị ẩn. Mỗi kỹ năng L01–L04 có ≥ 3 câu (ADR-022) nên quiz có thể ngắn hơn 10; giao diện báo số câu có sẵn.
- Nộp từng câu qua `/attempts`, nên mastery cập nhật đúng luật D-3 và lượt làm ghi chung với bài học.
- API `GET /api/v1/practice/quiz?skill_id=&n=` (không trả đáp án); trang `/app/quiz`.
