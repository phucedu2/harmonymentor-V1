# Đo định tuyến trên phiếu Claude soạn (phieu_claude_test20)

Chạy 08/11/2026: `python ../scripts/ai/gop_y/danh_gia_dinh_tuyen.py --set <phiếu>` trong image backend (Docker), code `phuc-music` 39d5ae3, mô hình e5 gốc (bản fine-tune GĐ2b không có trên máy).

**Câu hỏi do Claude soạn thay nhóm, không phải test do nhóm tự viết. Số dưới đây chỉ là tham khảo, chưa chứng minh chất lượng với người học thật.**

### bm25

Đúng luồng 80.0% · B/C bị trả lời như bài học 20.0% (mục tiêu ≤ 2%) · A bị từ chối sai 16.7% (mục tiêu ≤ 5%) · A trả lời bằng Engine thay vì bài 16.7%

| thật \ đoán | A | B | C | D | G | recall |
|---|---|---|---|---|---|---|
| **A** | 4 | 2 | 0 | 0 | 0 | 67% |
| **B** | 2 | 4 | 0 | 0 | 0 | 67% |
| **C** | 0 | 0 | 4 | 0 | 0 | 100% |
| **D** | 0 | 0 | 0 | 2 | 0 | 100% |
| **G** | 0 | 0 | 0 | 0 | 2 | 100% |
| precision | 67% | 67% | 100% | 100% | 100% | |

Câu sai luồng:

- A→B (below_threshold_engine): hop am Bm7b5 gom nhung not nao, la bac may trong do truong
- B→A (lesson_hit): am giai la thu tu nhien co dau thang dau giang ko
- B→A (lesson_hit): dao hop am C lan 1 la sao, viet C/E ha
- A→B (no_lesson_hit): D truong triad co nhung not nao

### embedding:multilingual-e5-small

Đúng luồng 90.0% · B/C bị trả lời như bài học 0.0% (mục tiêu ≤ 2%) · A bị từ chối sai 33.3% (mục tiêu ≤ 5%) · A trả lời bằng Engine thay vì bài 0.0%

| thật \ đoán | A | B | C | D | G | recall |
|---|---|---|---|---|---|---|
| **A** | 4 | 2 | 0 | 0 | 0 | 67% |
| **B** | 0 | 6 | 0 | 0 | 0 | 100% |
| **C** | 0 | 0 | 4 | 0 | 0 | 100% |
| **D** | 0 | 0 | 0 | 2 | 0 | 100% |
| **G** | 0 | 0 | 0 | 0 | 2 | 100% |
| precision | 100% | 75% | 100% | 100% | 100% | |

Câu sai luồng:

- A→B (no_lesson_hit): e voi f cach nhau may nua cung vay
- A→B (no_lesson_hit): D truong triad co nhung not nao
