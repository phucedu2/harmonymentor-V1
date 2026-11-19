# ADR-030: Model dự đoán học sinh làm đúng câu tiếp theo

- Ngày: 19/11/2026
- Trạng thái: đề xuất (Draft PR vào `phuc-music`, chờ Thắng duyệt phần backend, Đạt đọc phần đánh giá)
- Người quyết định phạm vi: Phúc (chọn 1A 2A 3A 4A ngày 19/11/2026)

## Bối cảnh

Nhóm muốn có một model tự train, áp quy trình của sách Hands-On ML (repo `ageron/handson-ml3`), để hỗ trợ hệ gợi ý.
Bài toán chọn: trước mỗi lượt làm/ôn, đoán xác suất người học làm đúng. App chưa có lịch sử của người học thật,
nên dữ liệu train là người học mô phỏng của `scripts/ai/sim/nguoi_mo_phong.py` (đã dùng cho đánh giá gợi ý GĐ4).

## Quyết định

1. **Dữ liệu (1A).** Train trên 2.000 người mô phỏng, seed 20261119. Luôn so với baseline "xác suất = mastery EMA"
   và với **trần lý thuyết** (xác suất thật bộ mô phỏng dùng để tung kết quả). Có lệnh xuất lịch sử thật
   (`python -m app.ml.correctness.dataset --out …`), thay user_id bằng mã băm, bỏ `is_test` và `is_synthetic`,
   để train lại khi đủ dữ liệu thật. File xuất nằm ở `data/correctness/` (đã gitignore).
2. **Đặc trưng.** 13 đặc trưng số + one-hot 14 `group_code` (và "khac"), tính CHỈ từ lượt trước
   (`features.UserState`). EMA trong đặc trưng tái dựng theo đúng `app.ai.mastery` (D-3, L-3, luật ôn 2A),
   chưa tính bài kiểm tra đầu vào. Cùng một lớp dùng cho train và cho API nên hai bên tính giống nhau.
3. **Model (2A).** Hai pipeline scikit-learn: StandardScaler + LogisticRegression, và HistGradientBoosting.
   GridSearchCV với GroupKFold 5 phần theo người học; tập test 20% người học tách bằng GroupShuffleSplit, chỉ chấm một lần.
   Chọn model theo AUC kiểm chéo, không theo test. `early_stopping=False` để chạy lại ra cùng số.
4. **Lưu.** `backend/models/correctness/model.joblib` (khoảng 49 KB) + `manifest.json` (phiên bản đặc trưng, sklearn,
   mã băm dữ liệu, số đo). Đổi thứ tự hay ý nghĩa đặc trưng thì tăng `FEATURE_VERSION`; API từ chối model lệch phiên bản.
5. **Dùng trong app (3A).** `GET /api/v1/me/predictions` sau cờ `PREDICT_ENABLED` (mặc định tắt → 404
   `PREDICT_DISABLED`; thiếu/hỏng model → 503 `PREDICT_MODEL_UNAVAILABLE`). Chỉ đọc lịch sử của người trong token.
   Mastery EMA, ba mức yếu/đủ/thành thạo và hệ gợi ý **không đổi** và không đọc kết quả này.
6. **Tài liệu (4A).** `notebooks/du_doan_dung_cau_tiep.ipynb` giải thích 10 bước, báo cáo ở `docs/giai-doan/ml-du-doan/`.
7. Không thêm TensorFlow/PyTorch. Không gửi gì cho Gemini.

## Hệ quả

- Số đo (19/11/2026, `cd backend && python -m app.ml.correctness.train`): AUC test 0,624 (HistGradientBoosting),
  0,623 (Logistic Regression), so với EMA 0,597 và trần 0,681: model lấy lại khoảng 32% khoảng cách giữa EMA và trần.
  Xác suất được hiệu chỉnh tốt (ECE 0,005; EMA dùng làm xác suất lệch 0,316).
  **Chưa chứng minh chất lượng với người học thật.**
- Đặc trưng mạnh nhất là số lượt đã làm kỹ năng, vì bộ mô phỏng cho năng lực tăng sau mỗi lượt. Model học quy luật
  của bộ mô phỏng; với dữ liệu thật thứ tự này có thể khác.
- Model train bằng scikit-learn 1.9.1; image Docker cài bản mới nhất lúc build. Lệch bản chính/phụ thì ghi cảnh báo;
  không nạp được thì API trả 503, app vẫn chạy. Cách sửa: train lại (khoảng 45 giây).
- Ý tưởng dùng sau (chưa làm, cần quyết riêng): chọn câu "vừa sức" 60–80% trong Luyện tập, hoặc thêm xác suất vào điểm gợi ý.
