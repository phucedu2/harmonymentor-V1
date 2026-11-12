# Phiếu dev 30 câu của Phúc (09/11/2026)

**Nguồn:** Phúc tự viết 30 câu hỏi và nhãn luồng, nộp 09/11. Phúc chọn: "Lẹ", "Á" là C; "ê", "How r u twin" là G. Cột đáp án chuẩn (`tra_loi`) do **Claude viết theo yêu cầu của Phúc**, `tra_loi_status: draft`, chưa ai duyệt. Cột `ai_09_11` giữ nguyên câu AI Tutor trả lời trên máy Phúc ngày 09/11 làm bằng chứng. File: `phieu-cau-hoi/phieu_Phuc_dev.json`.

Đây là **tập dev**: Claude được đọc, nên số đo dưới đây **không độc lập**. Số chính thức chờ 20 câu test khóa của Đạt và Thắng.

## Phát hiện từ phiếu

1. **Gemini luôn hỏng trên máy Phúc** (cả 12 câu A là câu dự phòng): Avast "HTTPS scanning" thay chứng chỉ Google, container Linux từ chối (`SSL: CERTIFICATE_VERIFY_FAILED`). Phúc đã thêm ngoại lệ `generativelanguage.googleapis.com` (09/11). Không phải lỗi code.
2. **Lỗi nhạc lý thật, đã sửa:** "hợp âm B diminished" ra B trưởng (B D# F#) vì `engine_query.py` chỉ đọc chữ trưởng/thứ. Nay đọc thêm giảm/diminished/dim, tăng/augmented/aug; gặp half-diminished, sus, maj, bảy… thì không đoán là hợp âm trưởng. Không đổi Music Engine. Test: `backend/tests/test_ai_engine_query_chat_luong.py` (10). **Chờ Thắng duyệt** vì đụng `engine_query.py`. Chưa nhận "tang" không dấu (dễ trùng chữ khác).
3. **Truy xuất lấy sai đoạn** ở vài câu A (đo dưới đây). Chưa sửa: Phúc chọn đo trước, duyệt cách sửa sau.

## Định tuyến (luồng đúng), sau PR #41

| Mô hình | Đúng luồng | B/C trả lời như bài | A bị từ chối nhầm |
|---|---|---|---|
| e5 gốc (mặc định) | 90,0% | 0% | 0% |
| BM25 | 73,3% | 0% | 41,7% |
| e5-hm-gd2b | 83,3% | 0% | 16,7% |
| e5-hm-gd2c | 83,3% | 0% | 16,7% |

Sai còn lại ở e5 gốc: "Lẹ", "Á" ra B ("không biết") thay vì C (không nặng: không trả lời như bài); "How r u twin" ra C thay vì G. 9 câu B dài kiểu sách giáo khoa đều đúng luồng nhưng dễ hơn câu học sinh thật; Phúc sẽ thêm 3–4 câu B ngắn.

## Truy xuất (12 câu A, đoạn chuẩn do Claude gán)

| Mô hình | R@1 | R@4 |
|---|---|---|
| e5 gốc | 4/12 | 9/12 |
| BM25 | 6/12 | 8/12 |
| e5-hm-gd2b | 7/12 | 9/12 |
| e5-hm-gd2c | 5/12 | 10/12 |

R@1 chấm chặt một đoạn; một số "sai" vẫn đúng ý (P04–P06 lấy đoạn "Tóm tắt" L01-B13 cũng có công thức triad, P12 lấy L04-B03 "Xây ii–V–I"). Sai thật: P01 "perfetc" → đoạn "24 giọng" (gõ sai chữ), P08 "quang 8" → âm giai trưởng, P11 "tonic va dominant" → L05 thay vì L03-B02.

Lệnh đo (trong `backend/`): `python ../scripts/ai/gop_y/danh_gia_dinh_tuyen.py --set ../docs/giai-doan/ai-gop-y/phieu-cau-hoi/phieu_Phuc_dev.json`.

## Thay đổi khác
- Mẫu phiếu chính: `phieu-cau-hoi/PHIEU_TU_VIET_CAU_HOI.md` (mẫu Phúc đã điền), thay `PHIEU_NHOM_TU_VIET.md`. `phieu_md_sang_json.py` đọc được STT dạng P01/Đ01/T01.
- pytest 1050 đạt, 43 bỏ qua; CI `--min-passed` 1050.
