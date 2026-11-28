# GĐ6: đánh giá tổng kết góp ý thầy G1–G7

Ngày 09/11/2026 · nhánh `ai/gd6-danh-gia` (từ `phuc-music`). Bản **khung và số đã đo đến hôm nay**. Phần "người học thật" chưa chạy: cần Phúc, Đạt, Thắng tổ chức (mục 4).

## 1. Điều đã đo và điều chưa đo

| Hạng mục | Số đo | Nguồn | Mức tin |
|---|---|---|---|
| AI Tutor định tuyến, 50 câu Claude soạn thay nhóm (e5 gốc) | Đúng luồng 86%; A bị từ chối sai 13,6%; B/C trả lời như bài 5,9% | [05_TRAIN_LAI_KHO_L05.md](05_TRAIN_LAI_KHO_L05.md) | Tham khảo (mẫu nhỏ ±10 điểm, không phải câu nhóm tự viết) |
| Test tạm 200 câu (không train, không chọn ngưỡng) | e5 gốc: đúng luồng 82,0%; B/C như bài 23,5%; A từ chối sai 4,5% | cùng file | Tham khảo, chưa đạt mục tiêu |
| Đo lại phiếu dev 30 và test 20 trên máy Phúc (09/11) | B/C như bài 10–13%; A từ chối sai 11–17% | báo cáo phiên máy Phúc, chưa commit | Tham khảo |
| RAG trích dẫn bằng Gemini (04/11, trước L05) | Recall@1 93,3% | `docs/minh-chung/CP3_ai_tutor_2026-11-08.md` | Cũ, cần đo lại sau L05 |
| Mục tiêu | B/C trả lời như bài ≤ 2%, A bị từ chối sai ≤ 5% | SRS / ADR-017 | **Chưa đạt trên tập độc lập** |
| Backing track GĐ4 | Test kỹ thuật đạt (Vitest 271); **chưa ai nghe** | PR #38 | Chưa kiểm bằng tai |
| Luyện tập bấm piano GĐ5 | pytest đạt (10 test mới); **chưa thử tay** | PR #39 | Chưa kiểm với người dùng |
| Người học thật dùng thử | **Chưa có** | | Không có số |

Không có chỗ nào trong báo cáo này được viết là "đạt" khi chưa đo. Số tham khảo do Claude soạn câu hỏi phải ghi rõ như vậy khi trình bày với thầy.

## 2. Kết luận trung thực cho từng góp ý

| Góp ý | Trạng thái |
|---|---|
| G1/G3: AI Tutor chỉ trả lời trong bài, biết nói "chưa dạy" | Có cơ chế 4 luồng và ngưỡng; **chưa đạt** mục tiêu lỗi ≤ 2% (đang sửa an toàn ở nhánh riêng) |
| Bổ sung bài L05–L08 | L05 đã phát hành; L06–L08 mới là nháp chờ Đạt duyệt (PR #37), Engine chưa hỗ trợ hợp âm mở rộng và mixolydian |
| Fine-tune mô hình mở | Đã làm (GĐ2b, GĐ2c); lợi ích đến chủ yếu từ dữ liệu và ngưỡng; mặc định vẫn e5 gốc |
| Nhạc cụ mới | Cello và 3 âm sắc guitar có (PR #38); violin và guitar mộc chưa có nguồn CC0 phù hợp |
| Thực hành và học thêm ngoài | Bấm piano và liên kết sách mở có (PR #39); guitar ảo và micro chưa làm |

## 3. Bộ đo chính thức (cần nhóm)

- Đạt, Thắng mỗi người tự viết 10 câu, Phúc 30 câu, theo phiếu có sẵn. Hạn đã dời sang 09/11.
- Chạy: `python scripts/ai/gop_y/danh_gia_dinh_tuyen.py` (Docker, e5 gốc), ghi lệnh, ngày và commit vào bảng kết quả.
- Báo cáo cả hai lỗi: câu ngoài bài bị trả lời như trong bài (nặng, tính ×2) và câu trong bài bị từ chối.

## 4. Thử với người học thật (nếu nhóm thực hiện)

- 5–10 bạn cùng lớp, mỗi bạn làm 1 bài (đề xuất L02) rồi dùng AI Tutor và Luyện tập 15 phút.
- **Phiếu đồng ý** trước khi thu dữ liệu (mẫu trong `gd6/PHIEU_DONG_Y_MAU.md`). Với bạn dưới 18 tuổi cần phụ huynh hoặc thầy cô đồng ý theo quy định nhà trường.
- Chỉ lưu dữ liệu ẩn danh (mã người học), không lưu tên, email, ảnh.
- Đo: tỉ lệ hoàn thành bài, tỉ lệ đáp án đúng lần đầu, số câu AI Tutor trả lời sai hoặc từ chối nhầm (người học báo), điểm hài lòng 1–5 và 2 câu nhận xét.
- Mẫu nhỏ nên báo cáo số tuyệt đối ("7/9 bạn hoàn thành"), không tính phần trăm như một kết luận thống kê.

## 5. Rủi ro khi trình bày

- Số 86% và 93,3% đừng đứng một mình: luôn kèm "câu do Claude soạn" và lỗi B/C còn cao.
- Mô hình fine-tune không tốt hơn rõ rệt nên đừng trình bày là cải tiến lớn.
- Mọi tài liệu học thêm bên ngoài đang nháp, chưa Đạt duyệt.
