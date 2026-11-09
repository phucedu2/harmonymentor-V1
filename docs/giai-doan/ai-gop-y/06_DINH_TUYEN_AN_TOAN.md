# Định tuyến an toàn (09/11/2026)

Mục tiêu: câu B/C (ngoài bài, ngoài phạm vi) bị trả lời như bài học ≤ 2%. Chỉ sửa `backend/app/ai/tutor/router.py`
(+ test `backend/tests/test_ai_router_an_toan.py`). Không đổi ngưỡng, `router_thresholds.json` giữ nguyên.

**Câu hỏi do Claude soạn thay nhóm (phiếu) hoặc do Claude viết (tập dev), nên số dưới đây chỉ là tham khảo, chưa chứng
minh chất lượng với người học thật.**

## Sửa gì

| Luật | Ví dụ câu trước đây sai |
|---|---|
| `later_lesson` so cả câu bỏ dấu; L06 nhận "muon hop am / muon tu giong"; L07 nhận hợp âm 9/11/13 | "Fm trong C truong muon tu dau ra vay" A→B |
| `untaught_concept`: đảo hợp âm, quãng kép, nhịp, trường độ, khóa nhạc, vòng quãng 5, bass khác root, sus → B "không biết"; tự tắt khi kho có đoạn khớp | "dao hop am C lan 1 la sao", "quang 9 la gi" A→B |
| `unknown_terms` mà tầng 1 không chắc nhạc lý (< 0,5) → C | "cho minh link tai nhac lau free" B→C |
| `weak_music_oos`: nghiêng ngoài phạm vi, nhạc lý < 0,5, không ký hiệu → C | "Gợi ý phim hay cuối tuần" A→C |

## Số đo (B/C bị trả lời như bài học)

Chạy 09/11/2026 trong image `hm-phuc-music-api` (Python 3.11, e5-small gốc; bản fine-tune không có trên máy).
"Trước" = `phuc-music` 09b1b8c, "sau" = nhánh `ai/an-toan-dinh-tuyen`.

```bash
cd backend
python ../scripts/ai/gop_y/danh_gia_dinh_tuyen.py --set ../docs/giai-doan/ai-gop-y/phieu-cau-hoi/<phiếu>.json
python ../scripts/ai/gop_y/danh_gia_dinh_tuyen.py                       # bộ GĐ1 (gd4 + gd0)
python ../scripts/ai/gop_y/danh_gia_dinh_tuyen.py --set ../scripts/ai/data/router_dev.json
python ../scripts/ai/gop_y/danh_gia_dinh_tuyen.py --set ../scripts/ai/data/gd2/dev.json
```

| Bộ | bm25 trước → sau | e5 trước → sau | A bị từ chối sai (bm25 / e5) sau |
|---|---|---|---|
| Phiếu dev 30 (Phúc) | 1/15 (6,7%) → **0/15** | 2/15 (13,3%) → **0/15** | 11,1% / 11,1% (không đổi) |
| Phiếu test 20 (Đạt + Thắng) | 2/10 → 1/10 | 1/10 → **0/10** | 1/6 / 1/6 (không đổi) |
| Bộ GĐ1 (74 câu) | 3,5% → 3,5% | 3,5% → 3,5% | 2,7% / 5,4% (không đổi) |
| router_dev | 15,9% → 4,5% | 13,6% → 4,5% | 11,1% / 2,8% (không đổi) |
| gd2/dev | 7,1% → **1,8%** | 14,3% → **1,8%** | 13,8→14,7% / 7,8→8,6% |

Còn lại:
- Bộ GĐ1: 1 câu "Bài hát buồn thường dùng hợp âm gì?" (nhãn B, đoán A). Không sửa vì bộ này giữ làm bộ đo độc lập;
  nhãn cũng đáng bàn (hợp âm thứ L01 đã dạy).
- router_dev: 2 câu nhãn B cũ ("chuyển giọng", "quãng năm song song") nay kho L05 đã dạy, nên A là đúng; nhãn cần sửa.
- Tập test: không xem câu sai để sửa luật (tập khóa).
- Cái giá: 1 câu A trên gd2/dev ("tap ii V I nen bat dau tempo nhanh hay cham") bị từ chối do `weak_music_oos`.

pytest (Docker, toàn bộ): 1012 passed, 43 skipped, 1 failed `test_release_files_match_model_card`. Lỗi này có sẵn trên
máy (hash file `gd2b_model_info.json` trong checkout khác hash trong code, cả ở `hm-phuc-music` chưa sửa), không do thay
đổi này.
