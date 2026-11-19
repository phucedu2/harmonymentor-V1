# Model dự đoán làm đúng câu tiếp theo (19/11/2026)

Nhánh `claude/project-thread-yysz49` từ `phuc-music` (53cebaf), Draft PR vào `phuc-music`. Quyết định: [ADR-030](../../decisions/ADR-030-model-du-doan-dung-cau-tiep.md).

> Mọi số dưới đây đo trên **người học mô phỏng**: chưa chứng minh chất lượng với người học thật.

## 1. Đã làm

| Phần | File |
|---|---|
| Đặc trưng không rò rỉ (13 số + 15 nhóm) | `backend/app/ml/correctness/features.py` |
| Nguồn dữ liệu: mô phỏng (kèm trần lý thuyết) và xuất lịch sử thật đã thay mã | `backend/app/ml/correctness/dataset.py` |
| Train: chia theo người, GridSearchCV, baseline, độ hiệu chỉnh, đường học, độ quan trọng | `backend/app/ml/correctness/train.py` |
| Model đã train + manifest | `backend/models/correctness/` |
| Phục vụ + API sau cờ | `backend/app/ml/correctness/predictor.py`, `backend/app/api/ai_predict.py` |
| Test (15) | `backend/tests/test_ml_du_doan_dung.py` |
| Notebook giải thích (đã chạy, có biểu đồ) | `notebooks/du_doan_dung_cau_tiep.ipynb` |
| Số đo đầy đủ | `docs/giai-doan/ml-du-doan/KET_QUA.json` |

Đây là thử nghiệm tự train ngoài danh sách FR Giai đoạn 1; không đổi FR nào đang chạy.

## 2. Kết quả

Lệnh: `cd backend && python -m app.ml.correctness.train` (19/11/2026 07:26 UTC, Python 3.13, scikit-learn 1.9.1, 44 giây).
2.000 người mô phỏng, 160.770 lượt (làm bài + ôn). Train 1.600 người / 128.003 lượt, test 400 người / 32.767 lượt. Tỷ lệ đúng 56%.

| Cách đoán (trên tập test) | AUC | Log loss | ECE | Precision | Recall |
|---|---|---|---|---|---|
| Hằng số (tỷ lệ đúng chung) | 0,500 | 0,684 | 0,004 | 0,566 | 1,000 |
| Tỷ lệ đúng trước đó của kỹ năng | 0,526 | 0,740 | 0,127 | 0,566 | 0,568 |
| Mastery EMA của app | 0,597 | 2,370 | 0,316 | 0,667 | 0,228 |
| **Logistic Regression** (C=10) | 0,623 | 0,662 | 0,005 | 0,624 | 0,758 |
| **HistGradientBoosting** (lr 0,05, sâu 3, 150 cây) — model chọn | **0,624** | **0,661** | 0,005 | 0,624 | 0,765 |
| Trần lý thuyết (biết xác suất thật của mô phỏng) | 0,681 | 0,631 | 0,005 | | |

Đọc bảng:
- Model hơn EMA 0,027 AUC, tức lấy lại khoảng 32% khoảng cách từ EMA tới trần. Phần còn lại là may rủi của từng lượt, không model nào đoán được.
- EMA xếp hạng khá (AUC 0,597) nhưng không dùng làm xác suất được: điểm 0 sau một lượt sai không có nghĩa "chắc chắn sai", nên ECE 0,316.
- Precision/Recall ở ngưỡng 0,5. Model hay đoán "sẽ đúng": trong 4.301 lượt sai của notebook (600 người) chỉ bắt được 1.645 (38%).
- Kiểm chéo và test gần nhau (0,629 và 0,624), train 0,633: không học vẹt với 128.000 dòng.
- Đường học: với 4.266 dòng train AUC train 0,705 nhưng validation 0,616 (học vẹt); từ 85.000 dòng hai đường gặp nhau. Nghĩa là vài trăm lượt thật của nhóm chưa đủ để train model tin được.
- Đặc trưng quan trọng nhất (hoán vị trên test): số lượt đã làm kỹ năng (giảm AUC 0,082 khi xáo trộn), tỷ lệ đúng chung của người học (0,015), EMA (0,002). Lý do: bộ mô phỏng tăng năng lực sau MỖI lượt, nên số lượt mang gần hết thông tin.

## 3. Lệnh chạy lại

```bash
cd backend
pip install -r requirements.txt
python -m app.ml.correctness.train                 # train lại trên mô phỏng, ghi model + KET_QUA.json
pytest -q tests/test_ml_du_doan_dung.py            # 15 test
PREDICT_ENABLED=1 uvicorn app.main:app --reload    # rồi GET /api/v1/me/predictions với token người học
# Khi có dữ liệu thật (trên máy có CSDL, ví dụ trong container api):
python -m app.ml.correctness.dataset --out ../data/correctness/that.jsonl
python -m app.ml.correctness.train --data ../data/correctness/that.jsonl
```

Kết quả test (19/11/2026, cloud, Python 3.13): `pytest -q tests/test_ml_du_doan_dung.py` → 15 passed.
`pytest -q` toàn bộ → 1492 passed, 46 skipped, 1 failed. Test hỏng là `test_g5_eval.py::test_chatbot_va_cong_nhac_ly_khong_hoi_quy_so_voi_baseline` (groundedness 94,5 so với baseline 100); hỏng y hệt trên `phuc-music` khi chưa có thay đổi này, không liên quan model.

## 4. Giải thích cho nhóm

**Model làm gì?** Trước khi bạn trả lời một câu Quãng, model nhìn lịch sử của bạn (đã làm Quãng mấy lần, đúng bao nhiêu, mastery bao nhiêu, lâu chưa làm...) và nói "khả năng đúng 72%".

**Ví dụ số.** Người A: làm Quãng 2 lần (sai rồi đúng), EMA 0,15. Người B: làm Quãng 8 lần, EMA 0,55. Model cho B xác suất cao hơn vì vừa luyện nhiều hơn vừa có EMA cao hơn. Endpoint trả ví dụ `{"skill_id": "interval.naming", "probability": 0.71, "band": "vua_suc", "ema": 0.55, "attempts": 8}`.

**Vì sao chia theo người học?** Nếu lượt 5 của A nằm ở train và lượt 6 của A nằm ở test, model "quen" A và số đo đẹp giả. Chia theo người thì test toàn người model chưa gặp, đúng với người dùng mới.

**AUC là gì?** Bốc một lượt đúng và một lượt sai bất kỳ; AUC là xác suất model cho lượt đúng điểm cao hơn. 0,5 là tung đồng xu.

**5 câu giảng viên có thể hỏi**
1. *Dữ liệu ở đâu ra?* Người học mô phỏng có seed cố định; đã có lệnh xuất dữ liệu thật để train lại. (Thắng)
2. *Model có học lại công thức của bộ mô phỏng không?* Có, nên nhóm đo thêm trần lý thuyết và ghi rõ chưa chứng minh với người thật. (Đạt)
3. *Sao không dùng deep learning?* Dữ liệu dạng bảng, 28 cột; cây tăng cường và hồi quy logistic là lựa chọn chuẩn, chạy CPU, giải thích được. (Thắng)
4. *Làm sao biết không học vẹt?* So AUC train, kiểm chéo, test và đường học (mục 2). (Đạt)
5. *Model có đổi gì trong app không?* Không. Chỉ thêm một API sau cờ, mặc định tắt; mastery và gợi ý giữ nguyên. (Phúc)

## 5. Việc của từng bạn để kiểm

- Thắng: đọc `features.py` (EMA tái dựng khớp `app.ai.mastery`), `predictor.py`, `ai_predict.py`, ADR-030. Người kiểm: ______
- Đạt: đọc mục 2 và notebook, kiểm câu "chưa chứng minh chất lượng với người học thật" có ở mọi chỗ báo số. Người kiểm: ______
- Phúc: chạy notebook trên máy, thử API với `PREDICT_ENABLED=1`. Người kiểm: ______

## 6. Rủi ro và câu hỏi

1. Model hiện chỉ hơn EMA một chút (0,624 so với 0,597). Đề xuất: giữ ở mức minh họa quy trình ML, chưa dùng để đổi gợi ý.
2. Lệch phiên bản scikit-learn giữa máy train và image Docker: có cảnh báo và trả 503 nếu không nạp được. Đề xuất: khi demo, train lại trong container nếu thấy cảnh báo.
3. Dùng xác suất để chọn câu "vừa sức" ở Luyện tập: cần quyết riêng và chờ dữ liệu thật.
