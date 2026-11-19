# ADR-030: Train lại tầng 1 định tuyến AI Tutor theo quy trình học máy chuẩn

- Ngày: 19/11/2026
- Trạng thái: đề xuất (Draft PR vào `phuc-music`, chờ nhóm duyệt)
- Người đề xuất: Claude Code theo yêu cầu của Phúc (chọn 1 đồng ý, 2A, 5A)

## Bối cảnh

Tầng 1 của bộ định tuyến (ADR-017, `route_classifier.py`) đoán 4 nhãn `nhac_ly / huong_dan / chao_hoi / ngoai_pham_vi`
bằng TF-IDF n-gram ký tự + Logistic Regression. Model đó train lại mỗi lần khởi động, tham số chọn tay (C = 10), không có
tập test tách riêng, không kiểm câu train có gần trùng câu đo hay không. Phúc muốn áp quy trình của sách
*Hands-On Machine Learning* (repo `ageron/handson-ml3`, chương 2–4) để model có số đo bảo vệ được trước giảng viên.

## Quyết định

1. Script `backend/app/ml/route_train.py` làm trọn quy trình: chia 3 tập cố định (train / validation / test), loại câu
   train gần trùng validation/test (Jaccard 3-gram ≥ 0,8, cùng ngưỡng `kiem_trung_du_lieu.py`), `GridSearchCV` với
   `GroupKFold(5)` chọn tham số cho 3 cách biểu diễn câu (TF-IDF, vector e5-small, gộp cả hai), chọn model thắng chỉ
   bằng validation, chấm test **một lần**, kèm khoảng tin cậy 95% (bootstrap 2000 lần) cho chênh lệch với model cũ,
   đường học (learning curve), ma trận nhầm lẫn.
2. Model lưu bằng `joblib` ở `backend/models/route/`, `manifest.json` ghi sha256, phiên bản scikit-learn, cờ `enabled`.
   `route_classifier.model()` chỉ nạp khi: manifest bật, sha256 khớp, cùng phiên bản scikit-learn, và (nếu model cần e5)
   máy có e5 gốc và không dùng bản e5 tinh chỉnh. Thiếu điều kiện nào thì dùng model cũ như trước.
   `ROUTE_MODEL=old` ép model cũ, `ROUTE_MODEL=new` nạp model mới cả khi chưa bật (chỉ để đo).
3. Luật bật: model mới chỉ bật khi macro-F1 hơn model cũ **cả trên validation lẫn test**.
4. Không thêm TensorFlow/PyTorch vào image; chỉ scikit-learn và onnxruntime đã có.

## Kết quả lần chạy 19/11/2026 (chi tiết: `docs/giai-doan/ml-dinh-tuyen/BAO_CAO.md`)

Model thắng trên validation là TF-IDF + e5 (macro-F1 0,966 so với 0,904 của model cũ), nhưng trên test chỉ đạt 0,882 so
với 0,894 (khoảng tin cậy của chênh lệch [−0,050; +0,028] chứa 0). Đo cả luồng AI Tutor trên 200 câu test tạm: đúng
luồng 85,0% so với 86,0%, câu bài học bị từ chối sai 7,2% so với 4,5%. **Vì vậy `enabled = false`: app vẫn chạy model cũ,
hành vi không đổi.**

## Hệ quả

- Hành vi AI Tutor hiện tại không đổi (test `test_mac_dinh_giu_model_cu_khi_manifest_chua_bat`).
- Có công cụ train/đo lặp lại được: khi nhóm có tập test tự viết, chạy lại một lệnh là biết model mới có đáng bật không.
- File joblib gắn với phiên bản scikit-learn; Docker cài phiên bản khác thì tự lùi về model cũ (có cảnh báo trong log),
  không hỏng. Muốn dùng model mới trên Docker phải train lại bằng đúng phiên bản trong image.
- Dữ liệu `route_data_ml.json` do Claude soạn, chưa ai kiểm; số đo cho thấy nó làm model kém đi trên test (mục 4 báo cáo).
