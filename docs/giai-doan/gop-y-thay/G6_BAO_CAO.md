# G6 (T6): bộ phân loại liên quan nhạc lý tự huấn luyện

Ngày làm: 15/11/2026. Nhánh `gop-y-thay/g6-tu-train` (xếp trên G5). Chi tiết mô hình: [`docs/MODEL_CARD.md`](../../MODEL_CARD.md). Số đo máy sinh: [`G6_DO_LUONG.json`](G6_DO_LUONG.json).

## Đã làm
- Huấn luyện hai mô hình trên CPU (17 giây): TF-IDF + hồi quy logistic, và hồi quy logistic trên vector e5-small. Dữ liệu 333 mẫu, `data/relevance/handwritten.jsonl` (177 mẫu viết tay) cộng 156 cặp câu từ các bài đã phát hành.
- Suy luận **thuần Python** (không cần sklearn lúc chạy), mô hình là JSON có SHA-256 trong `manifest.json`, sai hash thì không nạp.
- Công tắc `RELEVANCE_SCORER=classifier` thay bộ chấm của cổng G2; thiếu hoặc hỏng mô hình thì tự lùi về hybrid và ghi cảnh báo.
- Notebook Colab tùy chọn (`notebooks/colab_finetune_relevance.ipynb`): **chưa chạy**, chỉ quét siêu tham số đầu logistic.
- 9 test mới (`tests/test_g6_classifier.py`): khớp scikit-learn tới 1e-5 (giá trị vàng lưu trong `tests/fixtures`), manifest, sai hash, lùi về hybrid, chạy cổng với 14 tài liệu thử có nhãn, không rò dữ liệu.

## Kết quả
Kiểm chéo theo nhóm chủ đề: AUC tfidf 0,990, e5 0,997, hybrid G2 0,995. Trên 14 tài liệu thử G2 có nhãn: cả ba bộ chấm đều 100% precision/recall; e5 để 2 tài liệu lạc đề ở "chờ duyệt" thay vì từ chối.

## Điều cần nói thẳng
1. **Không chứng minh được classifier tốt hơn hybrid.** Chênh lệch nằm trong nhiễu của 333 mẫu. Mặc định vẫn hybrid.
2. Nhãn và dữ liệu do Claude soạn, chưa ai kiểm. Cần Đạt rà (đặc biệt các mẫu "âm nhạc nhưng không phải nhạc lý").
3. Chưa làm adapter/reranker tinh chỉnh bộ mã hóa (cần Colab và mã suy luận mới).
4. `--min-passed` trong `ci.yml` bị sửa ở nhiều PR chồng nhau; khi gộp thì giữ số lớn nhất.

## Kiểm chứng
`pytest -q` (backend): 1385 passed, 44 skipped (PostgreSQL và Qdrant chạy trong CI). `ci.yml --min-passed 1386`.
