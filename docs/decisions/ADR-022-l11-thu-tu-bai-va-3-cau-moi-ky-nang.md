# ADR-022 · Bài L11, thứ tự bài và đủ 3 câu cho mỗi kỹ năng

Trạng thái: **Đề xuất 12/11/2026**, nhánh `claude/project-thread-stuh1j` (Draft PR #49). Phúc chọn hướng Lai (điểm lệch 1) và hướng A (điểm lệch 5) trong báo cáo rà soát; Phúc báo Thắng đã duyệt phạm vi L11 và việc đổi đồ thị kỹ năng nếu cần.

## Quyết định

1. **Thêm bài L11 "Vòng hợp âm Pop"** vào module M3. Pop, đứng trước L06 theo SRS Bảng 7. Chỉ dùng vòng chung (I–V–vi–IV, vi–IV–I–V, I–vi–IV–V), không ghi hợp âm bài hát cụ thể. 6 câu, 6 thẻ, nút "Mở trong Harmony Lab" nạp sẵn vòng I–V–vi–IV qua địa chỉ `?key=C&numerals=I,V,vi,IV`.
2. **Không đổi đồ thị kỹ năng**: L11 dùng lại `function.progression` và `chord.triad_build`. Cách này tránh thêm kỹ năng mới (phải dựng lại vector kỹ năng bằng khóa Gemini). Kỹ năng thêm câu hỏi chỉ làm mastery chắc hơn.
3. **Mỗi kỹ năng của L01–L04 có ít nhất 3 câu độc lập đã phát hành** (SRS 04 mục 6.3: ba câu đúng ngay mới đủ 0,65). Thêm 15 câu, đáp án đều được `tests/test_lesson_l11.py` dựng lại bằng Music Engine. Các lượt làm cũ không đổi vì không sửa câu đã phát hành.
4. **Thứ tự bài giữ theo SRS Bảng 7** (L05 trước L04). Sửa lời văn thay vì đổi thứ tự: bài L05 không còn yêu cầu ii–V–I, và mọi lời nhắc "Lesson N" đổi thành tên bài để số "Bài n" trên màn hình không lệch với lời văn.
5. **L11 chưa vào kho AI Tutor** (`TUTOR_KB_PENDING`): nạp cần dựng lại chỉ mục Gemini và đo lại định tuyến, làm trên máy có khóa. Trong lúc chờ AI Tutor vẫn hỏi đáp được các bài khác.

## Hệ quả

- Số liệu mới: 9 bài, 73 câu đã phát hành, 70 thẻ. CI nâng ngưỡng lên 1225 test.
- Câu L01-Q05 (v6), L05-Q06 (v3), L08-Q04 và Q05 (v3) đổi nội dung nên tăng `version` theo ADR-006.
- Đạt cần xem lại nội dung L11 và 15 câu bổ sung; nội dung đã phát hành theo quyết định 4B của Phúc khi PR gộp.
