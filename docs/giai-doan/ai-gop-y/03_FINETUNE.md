# GĐ2b góp ý thầy: fine-tune e5-small cho AI Tutor

Ngày 07/11/2026 · nhánh `ai-gop-y/gd2b-fine-tune` (xếp chồng trên `ai-gop-y/gd2-du-lieu`, PR #29) · quyết định ở [ADR-018](../../decisions/ADR-018-fine-tune-e5-ai-tutor.md).

## 1. Kết quả chính

- **Đã fine-tune e5-small trên CPU** (khoảng 15 phút, 3 epoch), chọn epoch 2 theo dev.
  - Trên dev, độ tách câu A khỏi câu B/C (AUC) tăng từ 0,79 lên 0,88.
  - R@1 bộ chuẩn GĐ4 tăng từ 90,0% lên 93,3%.
- **Định tuyến với bản mới** (ngưỡng chọn lại trên dev):

  | Bộ đo | Mô hình | B/C bị trả lời như bài học (≤ 2%) | A bị từ chối sai (≤ 5%) | Đúng luồng |
  |---|---|---|---|---|
  | Dev GĐ1 + GĐ2 (275 câu, dùng để chọn) | gốc → mới | 8,3% → 5,2% | 26,2% → 13,5% | 77,5% → 84,0% |
  | Bộ đo GĐ1 (74 câu) | gốc → mới | 0,0% → **0,0%** | 8,1% → **2,7%** | 93,2% → 97,3% |
  | Test tạm GĐ2 (174 câu) | gốc → mới | 13,3% → **3,3%** | 24,4% → 32,6% | 70,1% → 69,0% |

- **Đọc kết quả thế nào:**
  - Bản mới **đạt cả hai mục tiêu trên bộ đo GĐ1**.
  - Trên test tạm, bản mới giảm 4 lần lỗi nặng nhất (trả lời câu ngoài bài như thể có trong bài), nhưng từ chối sai câu A nhiều hơn.
  - Theo cách chấm của ADR-017 (lỗi trả lời sai nặng gấp đôi), tổng lỗi giảm từ 51,0 xuống 39,2.
  - Chưa đạt mục tiêu trên câu bẩn. **Số chính thức chờ phiếu nhóm.**
- **Nhóm câu gây lỗi nhiều nhất trên test tạm:** "giọng Rê trưởng có mấy dấu thăng giáng", chiếm 10 trong 40 câu A bị đưa sai luồng.
  - Bài L02 dạy dựng âm giai trưởng (G major có F#) nhưng không dạy hóa biểu. Nhãn A của nhóm này có thể sai, nên ghi lại để Astra xem.
  - Nhãn KHÔNG được sửa sau khi đã xem kết quả test.

## 2. Đã làm gì

| Việc | File |
|---|---|
| Script fine-tune (InfoNCE + hinge ngưỡng học được, đóng băng nhúng từ, chọn epoch trên dev, xuất ONNX) | `scripts/ai/gop_y/finetune_e5.py` |
| Thẻ mô hình: lịch sử từng epoch, epoch chọn, SHA-256 file, hash dữ liệu train/dev | `docs/giai-doan/ai-gop-y/gd2b_model_info.json` |
| Tên mô hình đọc từ `model_info.json`; nhiều thư mục mô hình cùng lúc | `backend/app/ai/local_embedder.py` |
| Ngưỡng cho bản mới, chọn trên dev | `backend/app/ai/tutor/router_thresholds.json` |
| Test | `backend/tests/test_ai_gd2_du_lieu.py` (2 test GĐ2b) |
| ADR | `docs/decisions/ADR-018-fine-tune-e5-ai-tutor.md` |

Lịch sử train trên dev:

| Epoch | AUC A vs B/C | Lỗi cân bằng | R@1 GĐ4 | Ghi chú |
|---|---|---|---|---|
| 0 (gốc) | 0,790 | 22,0% | 90,0% | |
| 1 | 0,856 | 16,6% | 93,3% | |
| 2 | **0,885** | **14,4%** | 93,3% | được chọn |
| 3 | 0,863 | 18,7% | 90,0% | bắt đầu quá khớp |

## 3. Dùng thử bản mới

```bash
# File mô hình (470 MB) chưa có trên GitHub: chờ Phúc đồng ý tạo Release. Tạm thời train lại trên máy:
cd backend && pip install onnx && python ../scripts/ai/gop_y/finetune_e5.py --out models/multilingual-e5-small-hm --epochs 3
# Bật cho AI Tutor (mặc định vẫn là bản gốc):
LOCAL_EMBED_DIR=models/multilingual-e5-small-hm uvicorn app.main:app
```

Train lại thì chạy tiếp `hieu_chinh_nguong.py` để ghi ngưỡng cho bản vừa train.

## 4. Giải thích cho nhóm

- **Fine-tune ở đây là gì?** Mô hình gốc đặt câu "triad la gi" và câu "âm giai ngũ cung là gì" gần các đoạn bài như nhau, quanh 0,83. Fine-tune là cho mô hình xem 667 câu đã có nhãn, rồi chỉnh trọng số sao cho câu nằm trong bài được kéo gần đúng đoạn, còn câu ngoài bài bị đẩy xa mọi đoạn. Sau fine-tune, điểm trung bình của câu A là 0,50 và câu B/C là 0,35; hai nhóm đã cách nhau.
- **Vì sao chọn epoch 2 chứ không chọn epoch 3?** Epoch 3 khớp tập train quá mức: lỗi cân bằng trên dev tăng trở lại và R@1 giảm. Chọn epoch theo dev là cách chống quá khớp.
- **Vì sao chưa bật mặc định?** Trên test tạm, bản mới đổi loại lỗi: ít trả lời sai hơn hẳn nhưng từ chối nhiều hơn. Trước CP3, việc đổi mặc định nên để Phúc quyết.

## 5. Rủi ro, việc còn chờ

- **Chờ Phúc:**
  - Tạo GitHub Release chứa mô hình (quyết định 9A).
  - Chọn có bật bản mới làm mặc định không.
- Đo lại trên phiếu nhóm khi có. Nếu bản mới vẫn từ chối sai nhiều: thêm câu học kiểu "hóa biểu / số dấu" vào train (nếu Astra xác nhận đó là nội dung L02), hoặc thử reranker.
- `onnx` chỉ cần khi xuất mô hình, không thêm vào `requirements.txt` của backend.
