"""Model dự đoán "người học có làm đúng câu tiếp theo của kỹ năng này không" (ADR-030).

Học theo quy trình của sách Hands-On ML (Géron, repo ageron/handson-ml3): chia dữ liệu theo người học, pipeline
scikit-learn, chọn tham số bằng GridSearchCV, chấm bằng AUC/Precision/Recall và độ hiệu chỉnh, lưu bằng joblib.
Chỉ là thông tin thêm sau cờ PREDICT_ENABLED: KHÔNG thay mastery EMA, KHÔNG đổi thứ tự gợi ý.
"""
