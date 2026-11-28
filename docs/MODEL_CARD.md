# Model card: bộ phân loại "liên quan nhạc lý" (G6, góp ý thầy T6)

| | |
|---|---|
| Tên / phiên bản | `hm-relevance` 1.0.0 (xem `backend/models/relevance/manifest.json`) |
| Việc làm | Cho một đoạn chữ, trả xác suất 0..1 là nội dung nhạc lý/hòa âm. Dùng ở cổng upload Admin (G2) với ngưỡng LOW 0,35 / HIGH 0,60. |
| Hai biến thể | `tfidf`: TF-IDF n-gram ký tự (2–4, bỏ dấu) + hồi quy logistic, chỉ cần chữ. `e5`: hồi quy logistic trên vector multilingual-e5-small (mô hình nhúng đã dùng cho AI Tutor). |
| Huấn luyện | scikit-learn, CPU, 17 giây. `python -m app.ml.relevance_train` (chạy trong `backend/`). Không dùng GPU, không tinh chỉnh LLM. |
| Lưu trữ | JSON thuần (không pickle). `manifest.json` ghi phiên bản, SHA-256 từng tệp, SHA-256 dữ liệu, số đo. Sai hash thì từ chối nạp và cổng lùi về bộ chấm hybrid (có cảnh báo trong log). |
| Bật | `RELEVANCE_SCORER=classifier` (mặc định vẫn `hybrid`), `RELEVANCE_MODEL=auto|tfidf|e5`. |

## Dữ liệu
333 mẫu (204 liên quan, 129 không), chia 31 nhóm chủ đề.
- **Dương (nhạc lý):** 48 đoạn viết tay trong `data/relevance/handwritten.jsonl` (8 nhóm: nốt, quãng, thang âm, hợp âm, giọng và chức năng, nhịp, tiếng Anh, ký hiệu...) cộng 156 cặp câu liên tiếp lấy từ các bài đã phát hành của dự án (nhóm theo bài).
- **Âm:** 129 đoạn viết tay: 14 lĩnh vực lạc đề (nấu ăn, bóng đá, tin tức, lập trình...) và 15 mẫu **âm nhạc nhưng không phải nhạc lý** (lời bài hát, tiểu sử ca sĩ, quảng cáo nhạc cụ) để mô hình không học "có chữ nhạc là đúng".
- Không dùng tài liệu có bản quyền. Nhãn do Claude soạn, **chưa có người thứ hai kiểm nhãn** (nhờ Đạt).

## Số đo
Kiểm chéo 5 phần **theo nhóm chủ đề** (cả nhóm nằm ở phía kiểm tra, nên đo khả năng gặp chủ đề lạ):

| Bộ chấm | AUC | Accuracy | Precision | Recall |
|---|---|---|---|---|
| `tfidf` | 0,990 | 0,931 | 0,979 | 0,907 |
| `e5` | 0,997 | 0,973 | 0,976 | 0,980 |
| `hybrid` (G2, không huấn luyện) | 0,995 | 0,961 | 1,000 | 0,936 |

Trên 16 tài liệu thử của cổng G2 (`eval/cases.jsonl`, không nằm trong tập huấn luyện; trùng lớn nhất 0,42 Jaccard 3-gram, ngưỡng chặn 0,8):

| Bộ chấm | Precision nhận | Recall không bị từ chối | Lạc đề bị từ chối |
|---|---|---|---|
| `tfidf` | 100% | 100% | 100% (8/8) |
| `e5` | 100% | 100% | 87,5% (2 tài liệu rơi vào "chờ duyệt" thay vì từ chối) |
| `hybrid` | 100% | 100% | 100% |

## Kết luận trung thực
- Bộ phân loại **không vượt rõ** bộ chấm hybrid: AUC chênh 0,002 trên 333 mẫu là nằm trong nhiễu. Lý do giữ nó: tự huấn luyện được, có phiên bản và hash, giải thích được số đo, `tfidf` chạy không cần mô hình nhúng.
- Vì vậy **mặc định giữ hybrid**; classifier là tùy chọn bật bằng cấu hình, đến khi Đạt kiểm nhãn và nhóm bổ sung dữ liệu thật.

## Hạn chế
- Dữ liệu nhỏ, tiếng Việt là chính, nhãn một người soạn. Số đo có thể lạc quan hơn thực tế.
- `tfidf` học theo chữ nên có thể bị lừa bởi văn bản nhồi từ khóa nhạc lý; cổng G2 vẫn có lớp chặn chỉ dẫn chèn và từ vựng ở ngoài.
- Adapter/reranker (tinh chỉnh bộ mã hóa) **chưa làm**: notebook `notebooks/colab_finetune_relevance.ipynb` chỉ quét siêu tham số đầu logistic trên e5 đóng băng, **chưa chạy**. Tinh chỉnh bộ mã hóa cần thêm mã suy luận ở backend.
- Phạm vi đúng: lọc thô tài liệu upload. Không phải bộ kiểm duyệt nội dung, không kiểm đúng sai nhạc lý (việc đó do Music Engine và Đạt duyệt).

## Dùng lại
```powershell
cd backend
python -m app.ai.local_embedder download      # lần đầu, cho biến thể e5
python -m app.ml.relevance_train               # huấn luyện lại, ghi models/relevance + docs/giai-doan/gop-y-thay/G6_DO_LUONG.json
$env:RELEVANCE_SCORER="classifier"; python -m pytest tests/test_g6_classifier.py -q
```
