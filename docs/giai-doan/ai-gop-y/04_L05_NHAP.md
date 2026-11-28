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

## 5. Phát hành sau khi Đạt duyệt (07/11/2026)

Phúc báo trong thread "Đạt duyệt nhánh L05". Nhánh `ai-gop-y/gd3-l05-phat-hanh`:

- **11 khối L05 bỏ `status: draft`.** Người học thấy bài mà không cần `SHOW_DRAFT_CONTENT`. AI Tutor trích được 9 khối lý thuyết; 2 khối checkpoint vẫn không vào kho vì gắn đề bài tập. Luật "Bạn sẽ học sau ở L05" tự tắt, không sửa code.
- **Đổi nhãn 13 câu "át phụ" từ B sang A:** 8 câu train, 4 câu dev GĐ2, 1 câu `router_dev.json`. Test tạm không có câu L05. Lý do đổi là kho thay đổi, không phải kết quả đo. `tao_du_lieu_gd2.py` đổi nhãn SAU khi chia tập (hàm `relabel`), nên không câu nào đổi tập.
- **Chọn lại ngưỡng trên dev** (vì thêm 9 khối làm điểm truy xuất của mọi câu thay đổi). Bản fine-tune không train lại.

| Bộ đo | Mô hình | B/C bị trả lời như bài học (≤ 2%) | A bị từ chối sai (≤ 5%) | Đúng luồng |
|---|---|---|---|---|
| Dev GĐ1 + GĐ2 (dùng để chọn) | e5 gốc: trước → sau | 8,3% → 12,0% | 26,2% → 21,4% | 77,5% → 78,2% |
| | fine-tune: trước → sau | 5,2% → 5,4% | 13,5% → 16,8% | 84,0% → 82,2% |
| Bộ đo GĐ1 (74 câu) | e5 gốc: trước → sau | 0,0% → 0,0% | 8,1% → 8,1% | 93,2% → 93,2% |
| | fine-tune: trước → sau | 0,0% → 0,0% | 2,7% → 5,4% | 97,3% → 94,6% |
| Test tạm GĐ2 | e5 gốc: trước → sau | 13,3% → 16,7% | 24,4% → 23,3% | 70,1% → 69,5% |
| | fine-tune: trước → sau | 3,3% → 3,3% | 32,6% → 32,6% | 69,0% → 68,4% |

- **Đọc kết quả:** thêm bài làm kho rộng hơn, nên câu ngoài bài dễ "trúng" một đoạn hơn. Với e5 gốc, lỗi trả lời sai trên test tạm tăng 3,4 điểm. Bản fine-tune gần như giữ nguyên. Trên dev GĐ2, 3/4 câu át phụ sau khi đổi nhãn được trả lời bằng bài (bản fine-tune; câu sai: "bạn ơi V/ii nghĩa là gì ạ"). Khi có phiếu nhóm, train lại e5 với kho mới (khoảng 15 phút).
- **Chỉ mục Gemini (`lesson_embeddings.json`) phải dựng lại** bằng khóa Gemini (`python -m app.ai.build_index`). Trước khi dựng lại, chế độ `TUTOR_EMBEDDER=gemini` rơi về BM25. Chế độ mặc định (e5 cục bộ) không cần.
- Số đo: `gd3_l05_bo_do_gd1.*`, `gd3_l05_test_tam.*`.
- **Chế độ BM25** (khi không có mô hình nhúng): ngưỡng mới cao hơn (4,6 → 5,8) vì thêm đoạn làm điểm BM25 dịch lên. Giữ ngưỡng cũ thì trên dev câu B/C bị trả lời như bài học tới 31,5% (ngưỡng mới 19,6%). Hệ quả: câu demo "C7 khác Cmaj7 thế nào?" ở chế độ BM25 được trả bằng Engine (đúng nốt, không trích bài); "Cmaj7 với C7 khác gì nhau?" vẫn trích L02. Ở chế độ mặc định e5 (gốc và fine-tune), cả hai câu đều trả lời bằng bài L02. Test API đổi sang câu thứ hai.
- **Chỉ mục Gemini đã dựng lại** (08/11/2026, trên máy Phúc bằng image Docker backend vì Python trên máy lỗi chứng chỉ SSL): 58 đoạn (trước 45), `gemini-embedding-001`, 768 chiều. Không có chuỗi khóa trong file.
- `pytest -q`: 1004 passed, 43 skipped, 0 failed. CI nâng `--min-passed` lên 1004.
