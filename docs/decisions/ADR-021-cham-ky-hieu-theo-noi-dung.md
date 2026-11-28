# ADR-021 · Chấm câu gõ ký hiệu theo nội dung, không theo chuỗi gõ

Trạng thái: **Có hiệu lực 12/11/2026**, Phúc chốt (rà soát 11/11, RS-01 và RS-02, câu 16 đồng ý). Thắng cần đọc vì đổi `grading_service.py`.

## Bối cảnh

Rà soát 11/11/2026 chạy 105 cách gõ trên 20 câu: 44 ca lệch. Hai nhóm lỗi:

- RS-01 (sai được chấm đúng): bộ chấm hạ chữ hoa/thường mọi câu `exact` không có `case_sensitive`, nên `GM7-C7-FMAJ7` (G trưởng bảy) bằng `Gm7-C7-Fmaj7`, `V7/II` bằng `V7/ii`, `FM` bằng `Fm`, `DM7` bằng `Dm7`.
- RS-02 (đúng bị chấm sai): `E 7`, `Mi 7`, `F thứ`, `F minor`, `La giáng`, `G, B, F`, `Si và Fa`, `T - S - D - T`, `1 3b 5`, `khong`; câu dựng nốt bằng Engine văng lỗi 422 với `GBD`, `G/B/D`, `G. B. D`.

## Quyết định

1. Thêm `services/answer_match.py`. Câu `exact` có đáp án là ký hiệu hợp âm hoặc số La Mã được đọc về dạng chuẩn (gốc, phẩm chất) rồi so; tên nốt không phân biệt hoa/thường và nhận Đô–Rê–Mi, `thứ/minor/min`, `thăng/giáng`, `△`, `ø`; phẩm chất giữ `M` khác `m`; số La Mã giữ hoa/thường; `V/x` được nhận như `V7/x`. Không đổi đồng âm: `A#` khác `Bb`.
2. Câu rubric có đáp án là danh sách nốt so theo tập nốt (mọi dấu tách, Đô–Rê–Mi); đáp án là chuỗi chức năng nhận `S/SD/Hạ át` là Predominant và `Chủ` là Tonic.
3. Công thức `1-b3-5` nhận `3b`; đáp án chữ nhận gõ không dấu.
4. Câu có `case_sensitive: true` (trắc nghiệm chọn đúng phương án) giữ nguyên so chuỗi đúng.
5. `_split_notes` nhận `GBD` viết liền (chỉ khi toàn chữ hoa), `/ + .` và dấu chấm cuối. Số La Mã chấm bằng Engine nhận `iim7` như `ii7` (tiền xử lý ở `grading_service`, Engine không đổi). `V 7` có khoảng trắng vẫn sai theo quyết định demo 10/11.

## Phiên bản câu hỏi

Chỉ đổi bộ chấm, không đổi đề, đáp án hay `grader_config` của câu nào, nên không tăng `version` (ADR-006). Lượt làm cũ vẫn chấm lại cho kết quả như cũ hoặc đúng hơn.

## Không làm

`m3 + P5` (tên quãng thay vì công thức), `secondary dominant` (tên loại thay vì hợp âm), `iv` cho câu hỏi hợp âm Fm: nhập nhằng về nhạc lý, giữ là sai. `B D G` và `G Cb D` bấm bằng piano vẫn đúng theo thiết kế (đảo hợp âm, phím đàn không mang chính tả).

Test: `backend/tests/test_cham_bai_ra_soat.py` (63 ca).
