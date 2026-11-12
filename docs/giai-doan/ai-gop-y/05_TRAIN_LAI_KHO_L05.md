# Train lại bộ định tuyến sau khi L05 vào kho (GĐ2c)

Ngày 08/11/2026 · nhánh `ai/gd2c-train-lai` (từ `phuc-music`) · xem thêm [ADR-018](../../decisions/ADR-018-fine-tune-e5-ai-tutor.md).

## 1. Vì sao làm

Sau khi L05 được phát hành, 50 câu Claude soạn thay Đạt, Thắng, Phúc cho thấy bộ định tuyến còn từ chối nhiều câu trong bài (A bị từ chối sai 22,7% đến 45,5%, mục tiêu ≤ 5%). Các câu hỏng nhiều nhất là câu ngắn, gõ không dấu, hoặc hỏi kiểu đời thường ("hàm tonic là gì", "át phụ là gì vậy").

## 2. Đã làm gì

| Việc | Chi tiết |
|---|---|
| Thêm dữ liệu train | 14 nhóm câu mới trong `scripts/ai/gop_y/gd2_cau_goc.py` (mục "vòng 3"): hàm tonic/dominant/subdominant, hợp âm bảy nửa giảm, so sánh Cmaj7/C7, nửa cung, quãng, đồng âm, át phụ, tonicization, chào kèm lời nói thêm |
| Không đụng bộ đo | Câu mới Claude viết lại bằng lời khác. Đã đối chiếu với 50 câu phiếu: không câu train nào giống ≥ 0,8 (Jaccard 3-gram ký tự). Có vài cặp 0,6–0,75 là câu có sẵn từ trước ("át phụ là gì", "vì sao 3rd và 7th quan trọng") hoặc cùng khuôn đề bài, ghi ở đây để người duyệt biết |
| Sinh lại dữ liệu | `tao_du_lieu_gd2.py`: train 742, dev 206, test tạm 200 câu. Tách theo nhóm nên **dev và test tạm khác bản trước** (không so trực tiếp với số cũ của test tạm) |
| Train lại tầng 1 | Từ dữ liệu mới (tự chạy khi sinh dữ liệu) |
| Train lại e5 | `finetune_e5.py --grad-ckpt --name multilingual-e5-small-hm-gd2c`. Kho đã có 76 đoạn nên lần đầu hết RAM 16 GB; thêm `--grad-ckpt` (checkpoint gradient) thì chạy được, toán học như cũ. 4 epoch, epoch 4 được chọn (AUC dev 0,92) |
| Chọn lại ngưỡng | `hieu_chinh_nguong.py` trên dev mới, cho cả 4 khóa: BM25, e5 gốc, GĐ2b, GĐ2c |

## 3. Kết quả

Số đo 50 câu là **số tham khảo**: câu do Claude soạn thay Đạt, Thắng, Phúc, mẫu nhỏ (1 câu ≈ 2 điểm phần trăm, sai số ±10 điểm). Chưa phải số chính thức.

### 50 câu Claude soạn (trước → sau khi train lại)

| Mô hình | Đúng luồng | B/C trả lời như bài (≤ 2%) | A bị từ chối sai (≤ 5%) |
|---|---|---|---|
| e5 gốc | 72% → **86%** | 0% → 5,9% | 45,5% → **13,6%** |
| e5 GĐ2b (đã đăng Release) | 82% → 80% | 5,9% → 5,9% | 22,7% → 22,7% |
| e5 GĐ2c (mới) | không có → 82% | 5,9% | 18,2% |
| BM25 | 84% → 82% | 0% → 5,9% | 22,7% → 22,7% |

Phần B/C lên 5,9% ở bốn dòng đều do một câu: "Dm7b5 gồm những nốt nào". Nhãn B của câu này **có thể sai**: L02 có dạy ø7 / m7♭5 (khối L02-B05, câu L02-Q05, L02-F06), nên bộ định tuyến xếp vào bài là hợp lý. Theo nguyên tắc cũ, nhãn không được sửa sau khi đã xem kết quả; ghi lại để Đạt/Astra xem. Nếu đổi nhãn thành A thì B/C trả lời như bài về 0% ở cả bốn dòng.

### Bộ đo GĐ1 (74 câu, **đã dùng để chọn ngưỡng nên không độc lập**)

| Mô hình | Đúng luồng | B/C trả lời như bài | A bị từ chối sai |
|---|---|---|---|
| e5 gốc | 94,6% | 3,5% | 5,4% |
| GĐ2b | 96,0% | 0,0% | 5,4% |
| GĐ2c | 97,3% | 0,0% | 2,7% |

### Test tạm GĐ2 mới (200 câu, không dùng để train hay chọn)

| Mô hình | Đúng luồng | B/C trả lời như bài | A bị từ chối sai | Lỗi tổng (sai ×2) |
|---|---|---|---|---|
| e5 gốc | 82,0% | 23,5% | 4,5% | 51,5 |
| GĐ2b | 76,0% | 9,8% | 18,0% | 37,6 |
| GĐ2c | 79,0% | 13,7% | 11,7% | 39,1 |
| BM25 | 79,5% | 17,6% | 10,8% | 46,0 |

## 4. Đọc kết quả thế nào

- **Phần lớn cải thiện đến từ dữ liệu và ngưỡng, không đến từ mô hình mới.** e5 gốc tăng từ 72% lên 86% trên 50 câu chỉ nhờ dữ liệu train tầng 1 và ngưỡng chọn lại.
- **GĐ2c không hơn GĐ2b rõ rệt** trên 50 câu (82% so với 80%, chênh 1 câu) và trên test tạm (79,0% so với 76,0%, lỗi tổng 39,1 so với 37,6). Chưa đủ để đăng thêm một Release 470 MB.
- **Chưa mô hình nào đạt mục tiêu** (B/C ≤ 2%, A ≤ 5%) trên tập độc lập. Lỗi nặng nhất còn lại là câu ngoài bài bị trả lời như trong bài (e5 gốc 23,5% trên test tạm).
- Còn sai: chào kèm lời nói thêm ("chào buổi sáng, hôm nay học gì đây", "cảm ơn nha, hôm nay học vui quá") bị xếp ngoài phạm vi; "xuất file nhạc ra mp3 ở đâu" (D) bị xếp ngoài phạm vi.

## 5. Chưa làm / cần người duyệt

- Mặc định vẫn là e5 gốc. Mô hình GĐ2c chỉ nằm ở máy phát triển (`backend/models/`, không vào git). Muốn dùng phải đăng Release (Claude cloud không tạo được Release) và quyết định mặc định.
- Đạt/Astra duyệt 10% nhãn của 14 nhóm mới. Nhãn B/L05 được tự đổi thành A vì L05 đã vào kho.
- Số chính thức vẫn chờ phiếu do Đạt, Thắng, Phúc tự viết.
- Ngưỡng cho khóa `multilingual-e5-small-hm-gd2b` cũng được chọn lại trên dev mới, nên Release cũ dùng ngưỡng mới này.
