# Phát hành L06–L08 và liên kết sách mở (09/11/2026)

> **Đính chính 10/11/2026:** mục dưới nói "người học thấy" là SAI. Bài vẫn hiện "Sắp có" vì seed chỉ nạp câu hỏi cho L01–L04. Đã sửa ở [15_MO_KHOA_L05_L06_L08.md](15_MO_KHOA_L05_L06_L08.md).

**Quyết định:** Phúc báo Thắng và Đạt đã duyệt, chọn "Gộp #36–#42 theo đề xuất". Đã gộp #36–#42 vào `phuc-music` (main không đổi).

## Đã làm
- Bỏ `status: draft` ở 27 khối lý thuyết L06 (hợp âm mượn), L07 (tension, chord-scale), L08 (shell voicing): người học thấy.
- Bỏ `status: draft` ở cả 15 liên kết sách mở L01–L05 (báo cáo GĐ5 ghi nhầm 16). Mục thêm sau vẫn phải để `draft` chờ duyệt.
- `engine_query.py`: nhận "tang" không dấu (Thắng đồng ý), trừ "tăng dần/tốc/cường"; giữ cách đọc "hợp âm tăng của C" và chặn sus/half-diminished.

## Chưa làm: nạp L06–L08 vào kho AI Tutor
Thử nạp thì 19 test đỏ, trong đó có lỗi thật:
- Câu hóa học "hoa tri cua sat la may" bị kéo vào luồng A (lẽ ra C).
- "Cmaj7 khác C7 thế nào" trích L08 thay vì L02 (bài dạy hợp âm bảy).
- Luật "bạn sẽ học sau ở bài L06–L08" tắt, nên các nhãn B về hợp âm mượn, tension, voicing phải gán lại thành A.

Vì vậy `TUTOR_KB_PENDING = {L06, L07, L08}` (`content/draft_l06_l08.py`) giữ ba bài ngoài kho. Khi nạp cần làm như L05: gán lại nhãn, chọn lại ngưỡng, đo lại, dựng lại chỉ mục Gemini trên máy Phúc.

## Kiểm thử
pytest 1091 đạt, 44 bỏ qua (CI `--min-passed` 1091). Vitest 271, `npm run build` đạt (sau khi gộp #42).
Chưa thử bằng tay trên trình duyệt.
