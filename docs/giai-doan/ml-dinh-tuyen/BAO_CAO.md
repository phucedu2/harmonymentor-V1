# Train lại bộ phân loại câu hỏi AI Tutor theo quy trình học máy (ADR-030)

Ngày chạy: 19/11/2026. Nhánh `claude/project-thread-maj4ji` (tách từ `phuc-music` 53cebaf), Draft PR vào `phuc-music`.
Số đo máy sinh: [`DO_LUONG.json`](DO_LUONG.json). Đo cả luồng: `e2e_{old,new}_{default,test_tam}.md`.

## 1. Kết luận

**Model mới KHÔNG thắng model cũ, nên chưa bật.** App vẫn chạy y như trước. Cái nhóm có thêm là một quy trình train và
chấm đúng chuẩn, chạy lại bằng một lệnh, cùng ba phát hiện đáng nói khi bảo vệ:

1. Model cũ đã học trên **325 câu gần trùng** với câu dùng để chấm (rò dữ liệu), nên điểm cũ đẹp hơn thực tế.
2. Model "xịn" hơn (TF-IDF + vector e5, chọn tham số bằng GridSearchCV) đạt rất cao trên tập validation (0,966) nhưng
   xuống 0,882 trên tập test. Chênh lệch với model cũ nằm trong khoảng may rủi, nên không kết luận được là tốt hơn.
3. 262 câu Claude soạn thêm làm model **kém đi** trên test, vì Claude viết sau khi xem lỗi trên validation. Đó là học
   vẹt theo tập validation do người gây ra, đúng bài học chương 2 của sách.

## 2. Đã làm

| Bước trong handson-ml3 | Trong dự án |
|---|---|
| Ch.2 chia train/test, không nhìn test | 3 tập cố định trong `route_train.splits()`: train 982 câu, validation 368, test 306 (bảng dưới) |
| Ch.2 làm sạch dữ liệu | `remove_leaks()`: bỏ câu trùng/gần trùng giữa các tập (train bỏ 325, val bỏ 33, test bỏ 25 câu trùng trong tập) |
| Ch.2 Pipeline + lưu model | `Pipeline(TF-IDF/E5Features → LogisticRegression)`, lưu `joblib`, sha256 trong `manifest.json` |
| Ch.2 GridSearchCV | 3 lưới tham số, `GroupKFold(5)`: các cách nói của cùng một ý luôn cùng một phía |
| Ch.3 Precision/Recall/F1, ma trận nhầm lẫn | `evaluate()`: cho từng nhãn, macro-F1, danh sách câu sai |
| Ch.2 khoảng tin cậy trên test | `bootstrap_diff()`: 2000 lần bốc lại câu test |
| Ch.4 đường học | `learning_curve` của model thắng |

| Tập | nhac_ly | huong_dan | chao_hoi | ngoai_pham_vi | Nguồn (đều do Claude soạn, chưa nhóm kiểm) |
|---|---|---|---|---|---|
| train | 554 | 159 | 93 | 176 | route_data, route_data_gd2, route_data_ml (mới, 262 câu) |
| validation | 224 | 50 | 40 | 54 | route_data.dev, router_dev, gd2/dev, phieu_Phuc_dev (Claude điền) |
| test | 222 | 31 | 20 | 33 | gd2/test_tam, phiếu Đạt + Thắng (Claude điền), câu dò GĐ0, eval/cases (bỏ câu tấn công) |

## 3. Kết quả (lệnh `cd backend && python -m app.ml.route_train --jobs 4`, 19/11/2026, scikit-learn 1.9.1)

| Model | CV macro-F1 | Validation macro-F1 | Test macro-F1 | Test accuracy | Chênh với model cũ trên test (CI 95%) |
|---|---|---|---|---|---|
| **Model cũ đang chạy** (TF-IDF 2–4, C=10, có câu rò) | – | 0,904 | 0,894 | 94,4% | mốc |
| TF-IDF, GridSearch (n-gram 1–5, C=30, balanced) | 0,838 | 0,922 | 0,842 | 91,5% | −0,053 [−0,100; −0,012] **kém hơn rõ** |
| e5-small + LogReg (C=10, balanced) | 0,864 | 0,894 | – | – | không chấm test (thua validation) |
| **TF-IDF + e5** (thắng validation) | 0,880 | **0,966** | 0,882 | 93,1% | −0,012 [−0,050; +0,028] không khác biệt |
| Công thức cũ, dữ liệu cũ **đã bỏ câu rò** | – | 0,903 | 0,910 | 95,4% | +0,017 [0,000; +0,040] sát ranh giới |
| Công thức cũ, dữ liệu đã bỏ câu rò **+ câu Claude mới** | – | 0,924 | 0,869 | 93,1% | −0,025 [−0,060; +0,007] |

Từng nhãn trên test (precision / recall), model cũ → TF-IDF + e5:

| Nhãn | Model cũ | TF-IDF + e5 |
|---|---|---|
| nhac_ly (222) | 0,978 / 0,978 | 0,991 / **0,946** |
| huong_dan (31) | 0,813 / 0,839 | 0,788 / 0,839 |
| chao_hoi (20) | 0,947 / 0,900 | 0,905 / 0,950 |
| ngoai_pham_vi (33) | 0,849 / 0,849 | **0,750** / 0,909 |

Model mới bắt câu ngoài phạm vi nhiều hơn nhưng đổi lại gán nhầm 7 câu nhạc lý thành "ngoài phạm vi", ví dụ
"quang tu F len B la quang gi", "Tension 9, 11, 13 là gì?". Với người học, bị từ chối câu nhạc lý tệ hơn nhiều.

**Đo cả luồng AI Tutor** (`scripts/ai/gop_y/danh_gia_dinh_tuyen.py`, retriever e5 như khi chạy thật):

| Bộ đo | Model | Đúng luồng | B/C bị trả lời như bài học | Câu bài học bị từ chối sai |
|---|---|---|---|---|
| 74 câu mặc định | cũ | 96,0% | 3,5% | 2,7% |
| 74 câu mặc định | TF-IDF + e5 | 96,0% | 3,5% | 5,4% |
| 200 câu test tạm | cũ | 86,0% | 7,8% | 4,5% |
| 200 câu test tạm | TF-IDF + e5 | 85,0% | 7,8% | 7,2% |

**Đường học** của model thắng (macro-F1, CV theo nhóm): train 78 câu → 0,62; 361 → 0,82; 785 → 0,88; điểm trên phần học
luôn 1,00. Hai đường còn cách xa và đường CV vẫn đi lên: model đang học thuộc, **thêm dữ liệu thật còn giúp được**.

## 4. Giải thích cho nhóm

**Ví dụ nhỏ về rò dữ liệu.** Train có câu "hợp âm F gồm những nốt nào", test có "hop am F gom nhung not nao". Bỏ dấu đi
thì gần như một câu. Model chỉ cần nhớ là đúng, nên điểm test cao mà không chứng minh được model hiểu câu mới. Script
đã tìm ra 325 câu như vậy trong dữ liệu train cũ.

**Validation và test khác nhau thế nào.** Validation để chọn (chọn tham số, chọn model, sửa dữ liệu). Test để chấm một lần
cuối. Ở đây Claude xem lỗi trên validation rồi soạn thêm câu "vá" đúng những lỗi đó, nên validation tăng vọt (0,904 →
0,966) còn test lại giảm. Nếu chỉ báo điểm validation thì sẽ tưởng model mới tốt hơn hẳn.

**Khoảng tin cậy.** Test chỉ có 20 câu chào hỏi: sai thêm 1 câu là recall nhãn đó tụt 5%. Bốc lại ngẫu nhiên 306 câu test
2000 lần, tính chênh lệch mỗi lần, lấy khoảng giữa 95%. Khoảng chứa số 0 nghĩa là chưa chắc model nào hơn.

**Vì sao F1 macro.** 222/306 câu test là nhạc lý. Model đoán "nhạc lý" cho mọi câu cũng đúng 72,5%, nên accuracy dễ đánh lừa.
Macro-F1 lấy trung bình 4 nhãn ngang nhau, nhãn ít câu cũng được tính đủ.

```python
# Cốt lõi của script (rút gọn)
pipe = Pipeline([("vec", FeatureUnion([("tfidf", TfidfVectorizer(analyzer="char_wb")), ("e5", E5Features())])),
                 ("clf", LogisticRegression())])
gs = GridSearchCV(pipe, {"clf__C": [10, 30]}, cv=GroupKFold(5), scoring="f1_macro")
gs.fit(cau_train, nhan_train, groups=nhom)        # chọn tham số chỉ trên train
f1_val = f1_score(nhan_val, gs.predict(cau_val), average="macro")   # chọn model
# ... chọn xong mới chấm test một lần
```

**5 câu giảng viên có thể hỏi**

| Câu hỏi | Trả lời gợi ý | Ai trả lời |
|---|---|---|
| Sao không dùng model mới khi validation cao hơn hẳn? | Validation đã bị dùng để sửa dữ liệu nên lạc quan; test và đo cả luồng đều không hơn, khoảng tin cậy chứa 0 | Thắng |
| Làm sao biết không rò dữ liệu? | Hàm `remove_leaks` và test `test_chia_du_lieu_khong_ro_cau_gan_trung` chạy trong CI | Thắng |
| GroupKFold khác KFold chỗ nào? | Các cách nói của cùng một ý (có dấu, không dấu, gõ tắt) luôn nằm cùng một phía, không thể "nhìn bài" của nhau | Đạt |
| Vì sao không dùng mạng nơ-ron? | 1000 câu là quá ít; e5 đã là mạng nơ-ron train sẵn, mình chỉ train phần Logistic Regression phía trên | Đạt |
| Dữ liệu ai viết? | Claude soạn, ghi rõ trong file; số chính thức cần tập test nhóm tự viết | Phúc |

## 5. Việc của từng bạn để kiểm

- **Thắng**: đọc `route_classifier._load_trained` (điều kiện nạp joblib), chạy `pytest -q tests/test_ml_route_train.py`.
- **Đạt**: rà nhãn `backend/app/ai/tutor/route_data_ml.json` (262 câu, status draft), đặc biệt các câu nhạc cụ/luyện tập gán `nhac_ly`.
- **Phúc**: đọc mục 4 để thuyết trình; quyết định câu ở mục 7.

Người kiểm: Thắng ☐ · Phúc ☐ · Đạt ☐

## 6. Kiểm chứng

- `cd backend && python -m app.ml.route_train --jobs 4`: chạy 57 giây trên cloud 4 nhân, ghi `DO_LUONG.json` và `backend/models/route/`.
- `cd backend && ROUTE_MODEL=old|new python ../scripts/ai/gop_y/danh_gia_dinh_tuyen.py [--set ../scripts/ai/data/gd2/test_tam.json] --out ...`
- `cd backend && pytest -q`: **1492 passed, 44 skipped** (19/11/2026, máy cloud có e5; 44 skip là test PostgreSQL/Qdrant chạy ở CI). 11 test mới trong `tests/test_ml_route_train.py`. `ci.yml --min-passed` 1481 → 1492.
- Frontend không đổi nên không chạy `npm run build`.

Kết quả trên dữ liệu do Claude soạn, chưa chứng minh chất lượng với người học thật.

## 7. Rủi ro và câu cần nhóm quyết

1. **Có giữ 262 câu Claude soạn không?** Số đo cho thấy chúng làm model kém đi trên test. Gợi ý: giữ file làm minh chứng
   "học vẹt theo validation" nhưng bỏ khỏi train ở lần chạy sau (A), hoặc giữ nguyên và chờ Đạt sửa nhãn (B).
2. **Có bật "công thức cũ + bỏ câu rò" không?** Nó nhỉnh hơn model cũ 0,017 trên test nhưng khoảng tin cậy chạm 0, và mình
   chỉ thấy nó sau khi đã nhìn test. Gợi ý: không bật, chờ tập test do nhóm tự viết rồi chạy lại.
3. File joblib gắn với scikit-learn 1.9.1; Docker cài bản khác sẽ tự dùng model cũ (an toàn, có cảnh báo trong log).
