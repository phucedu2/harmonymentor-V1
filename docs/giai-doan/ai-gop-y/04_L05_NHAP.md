# GĐ3 góp ý thầy G2: nháp lý thuyết L05 (Secondary Dominants)

Ngày 07/11/2026 · nhánh `ai-gop-y/gd3-l05` (xếp chồng trên GĐ2b, PR #30) · Claude soạn, **chờ Astra/Đạt duyệt**.

## 1. Kết quả

- L05 trước đây chỉ có 6 câu hỏi và 8 thẻ ôn, chưa có phần lý thuyết. Nay có **11 khối nháp**:
  - 9 khối lý thuyết: dẫn nhập, át phụ là gì, thuật ngữ, dựng V7/x hai bước, năm át phụ trong C major, ví dụ tiến trình, nghe trước/sau, tonicization và modulation, ghi nhớ.
  - 2 checkpoint nối câu có sẵn L05-Q02 và L05-Q06.
- **Mọi hợp âm và nốt đã đối chiếu Music Engine bằng test**, không kiểm bằng mắt:
  - Năm át phụ: A7, B7, C7, D7, E7, mỗi hợp âm cách chord đích đúng quãng 5.
  - Nốt từng hợp âm.
  - "Nốt ngoài key" của từng át phụ.
  - Số La Mã của tiến trình ví dụ.
- **Nháp không lộ ra ngoài:**
  - Người học không thấy (status `draft`, chỉ hiện khi bật `SHOW_DRAFT_CONTENT`).
  - AI Tutor không trích. Câu hỏi về át phụ vẫn đi luồng B với nhãn "Bạn sẽ học sau ở L05".
  - Khi duyệt xong và bỏ status `draft`, nội dung tự vào kho. Luật "bài sau" của L05 cũng tự tắt, không phải sửa code.

## 2. Phiếu duyệt cho Astra/Đạt

| # | Cần xem | Khối |
|---|---|---|
| 1 | Định nghĩa át phụ, chord đích, tonicization, modulation có đúng mức nhập môn và khớp nguồn OMT "Tonicization" không | B02, B03, B08 |
| 2 | Cách dựng hai bước (lên quãng 5 đúng rồi dựng dominant seventh) | B04 |
| 3 | Câu "hợp âm giảm không làm tonic tạm thời được" (không có V7/vii°) | B03, B05 |
| 4 | Câu về Bb trong C7 (quãng 7 đi xuống A) | B05 |
| 5 | Ví dụ I → V7/ii → ii7 → V7 → I và phần nghe ở 72 BPM | B06, B07 |
| 6 | Văn phong (xưng "bạn", thuật ngữ Anh kèm tiếng Việt) giống L03/L04 | tất cả |
| 7 | Nguồn: bài đã có 4 nguồn (OMT, Fank, Khải Hoàn Ch.2, Terefenko Ch.13). Cần chốt khối nào theo nguồn nào | tất cả |

Duyệt xong thì bỏ `"status": DRAFT` ở từng khối trong `backend/app/content/draft_specs.py`, hoặc chuyển khối sang `curriculum_specs.py`. Sau đó chạy `python -m app.ai.build_index` bằng khóa Gemini nếu dùng chế độ Gemini.

## 3. File và kiểm thử

- `backend/app/content/draft_specs.py`: `L05_DRAFT_BLOCKS`, `DRAFT_LESSON_BLOCKS`. Hàm `blocks_with_drafts` dùng khối nháp khi bài chưa có khối phát hành.
- `backend/tests/test_ai_gd3_l05.py`: 11 test, gồm đối chiếu Engine, tình trạng nháp, ngoài kho AI Tutor, checkpoint trỏ đúng câu.
- `pytest -q`: 1002 passed, 43 skipped. CI nâng `--min-passed` lên 1002.

## 4. Chưa làm

- L06–L08 chưa soạn. Phúc cho phép làm GĐ3 "nếu kịp" trong ngày; ưu tiên L05 cho CP3.
- Chưa chụp ảnh giao diện của bài nháp.
