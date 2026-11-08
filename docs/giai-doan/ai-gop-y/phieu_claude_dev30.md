# Đo định tuyến trên phiếu Claude soạn (phieu_claude_dev30)

Chạy 08/11/2026: `python ../scripts/ai/gop_y/danh_gia_dinh_tuyen.py --set <phiếu>` trong image backend (Docker), code `phuc-music` 39d5ae3, mô hình e5 gốc (bản fine-tune GĐ2b không có trên máy).

**Câu hỏi do Claude soạn thay nhóm, không phải test do nhóm tự viết. Số dưới đây chỉ là tham khảo, chưa chứng minh chất lượng với người học thật.**

### bm25

Đúng luồng 90.0% · B/C bị trả lời như bài học 0.0% (mục tiêu ≤ 2%) · A bị từ chối sai 11.1% (mục tiêu ≤ 5%) · A trả lời bằng Engine thay vì bài 11.1%

| thật \ đoán | A | B | C | D | G | recall |
|---|---|---|---|---|---|---|
| **A** | 7 | 2 | 0 | 0 | 0 | 78% |
| **B** | 0 | 9 | 0 | 0 | 0 | 100% |
| **C** | 0 | 1 | 5 | 0 | 0 | 83% |
| **D** | 0 | 0 | 0 | 3 | 0 | 100% |
| **G** | 0 | 0 | 0 | 0 | 3 | 100% |
| precision | 100% | 75% | 100% | 100% | 100% | |

Câu sai luồng:

- A→B (no_lesson_hit): hop am tang cua C la gi
- C→B (unknown_terms): cho minh link tai nhac lau free
- A→B (below_threshold_engine): quang tu C len A la quang gi

### embedding:multilingual-e5-small

Đúng luồng 83.3% · B/C bị trả lời như bài học 0.0% (mục tiêu ≤ 2%) · A bị từ chối sai 33.3% (mục tiêu ≤ 5%) · A trả lời bằng Engine thay vì bài 11.1%

| thật \ đoán | A | B | C | D | G | recall |
|---|---|---|---|---|---|---|
| **A** | 5 | 4 | 0 | 0 | 0 | 56% |
| **B** | 0 | 9 | 0 | 0 | 0 | 100% |
| **C** | 0 | 1 | 5 | 0 | 0 | 83% |
| **D** | 0 | 0 | 0 | 3 | 0 | 100% |
| **G** | 0 | 0 | 0 | 0 | 3 | 100% |
| precision | 100% | 64% | 100% | 100% | 100% | |

Câu sai luồng:

- A→B (no_lesson_hit): quang 5 dung la bao nhieu nua cung
- A→B (no_lesson_hit): hop am tang cua C la gi
- A→B (no_lesson_hit): ii V I trong C la nhung hop am nao
- C→B (unknown_terms): cho minh link tai nhac lau free
- A→B (below_threshold_engine): quang tu C len A la quang gi
