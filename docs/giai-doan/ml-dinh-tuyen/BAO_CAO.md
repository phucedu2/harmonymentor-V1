# Train lại bộ phân loại câu hỏi AI Tutor theo quy trình học máy (ADR-030)

Ngày chạy: 19/11/2026. Nhánh `claude/project-thread-maj4ji` (tách từ `phuc-music` 53cebaf), Draft PR #68 vào `phuc-music`.
Số đo máy sinh: [`DO_LUONG.json`](DO_LUONG.json) (lần 2, đang dùng) và [`DO_LUONG_lan1.json`](DO_LUONG_lan1.json) (lần 1).
Đo cả luồng AI Tutor: `e2e_*.md`.

## 1. Kết luận

**AI Tutor giờ chạy model "công thức cũ, học trên dữ liệu đã bỏ câu rò"**: cùng thuật toán và tham số với model cũ,
nhưng bỏ 325 câu train gần trùng với câu dùng để chấm. Trên tập test: macro-F1 0,894 → 0,910, accuracy 94,4% → 95,4%.
Đo cả luồng AI Tutor thì không kém đi chỗ nào (bảng mục 3). Đây là quyết định của nhóm (Phúc chọn 2B), vì khoảng tin
cậy của mức tăng chạm số 0 nên số liệu một mình chưa đủ để khẳng định model mới hơn hẳn.

Ba phát hiện đáng nói khi bảo vệ:

1. Model cũ đã học trên **325 câu gần trùng** với câu chấm (rò dữ liệu), nên điểm cũ đẹp hơn thực tế.
2. **262 câu Claude soạn thêm làm model kém đi** trên test (lần 1), vì Claude viết sau khi xem lỗi trên validation.
   Đó là học vẹt theo tập validation do người gây ra. Nhóm quyết bỏ chúng khỏi train (1A), giữ file làm minh chứng.
3. Model "xịn" hơn (TF-IDF + vector e5, chọn tham số bằng GridSearchCV) đúng luồng nhiều hơn nhưng **từ chối nhầm câu
   bài học nhiều hơn** (6,3% so với 4,5%, vượt mục tiêu 5%). Với người mới học, bị từ chối câu nhạc lý là lỗi nặng,
   nên model này chỉ giữ làm thí nghiệm, không chạy thật.

## 2. Đã làm

| Bước trong handson-ml3 | Trong dự án |
|---|---|
| Ch.2 chia train/test, không nhìn test | 3 tập cố định trong `route_train.splits()`: train 862 câu, validation 368, test 306 |
| Ch.2 làm sạch dữ liệu | `remove_leaks()`: bỏ câu trùng/gần trùng giữa các tập (train bỏ 325, val bỏ 33, test bỏ 25 câu lặp) |
| Ch.2 Pipeline + lưu model | `Pipeline(TF-IDF/E5Features → LogisticRegression)`, lưu `joblib`, sha256 trong `manifest.json` |
| Ch.2 GridSearchCV | 3 lưới tham số, `GroupKFold(5)`: các cách nói của cùng một ý luôn cùng một phía |
| Ch.3 Precision/Recall/F1, ma trận nhầm lẫn | `evaluate()`: từng nhãn, macro-F1, danh sách câu sai |
| Ch.2 khoảng tin cậy trên test | `bootstrap_diff()`: 2000 lần bốc lại câu test |
| Ch.4 đường học | `learning_curve` của model chạy thật |

| Tập | nhac_ly | huong_dan | chao_hoi | ngoai_pham_vi | Nguồn (đều do Claude soạn, chưa nhóm kiểm) |
|---|---|---|---|---|---|
| train | 533 | 123 | 80 | 126 | route_data, route_data_gd2 (đã bỏ câu rò) |
| validation | 224 | 50 | 40 | 54 | route_data.dev, router_dev, gd2/dev, phieu_Phuc_dev (Claude điền) |
| test | 222 | 31 | 20 | 33 | gd2/test_tam, phiếu Đạt + Thắng (Claude điền), câu dò GĐ0, eval/cases (bỏ câu tấn công) |

## 3. Kết quả lần 2 (lệnh `cd backend && python -m app.ml.route_train --jobs 4`, 19/11/2026, scikit-learn 1.9.1)

| Model | Validation macro-F1 | Test macro-F1 | Test accuracy | Chênh với model cũ trên test (CI 95%) |
|---|---|---|---|---|
| Model cũ trước PR (có câu rò) | 0,904 | 0,894 | 94,4% | mốc |
| **Công thức cũ, đã bỏ câu rò (đang chạy)** | 0,903 | **0,910** | **95,4%** | +0,017 [0,000; +0,040] |
| Công thức cũ + 262 câu Claude soạn | 0,924 | 0,869 | 93,1% | −0,025 [−0,060; +0,007] |
| TF-IDF, GridSearch (n-gram 1–5, C=30, balanced) | 0,898 | 0,890 | 93,5% | −0,003 [−0,035; +0,031] |
| e5-small + LogReg (C=30, balanced) | 0,880 | 0,826 | 90,8% | −0,068 [−0,145; +0,007] |
| TF-IDF + e5, GridSearch (thắng validation) | 0,920 | 0,907 | 94,4% | +0,013 [−0,028; +0,057] |

Lần 1 (khi còn 262 câu Claude soạn trong train): TF-IDF + e5 đạt validation 0,966 nhưng test chỉ 0,882 (`DO_LUONG_lan1.json`).

Từng nhãn trên test (precision / recall), model cũ → model đang chạy:

| Nhãn | Model cũ | Đang chạy |
|---|---|---|
| nhac_ly (222) | 0,978 / 0,978 | 0,982 / 0,982 |
| huong_dan (31) | 0,813 / 0,839 | 0,844 / 0,871 |
| chao_hoi (20) | 0,947 / 0,900 | 0,947 / 0,900 |
| ngoai_pham_vi (33) | 0,849 / 0,849 | 0,879 / 0,879 |

**Đo cả luồng AI Tutor** (`scripts/ai/gop_y/danh_gia_dinh_tuyen.py`, retriever e5 như khi chạy thật):

| Bộ đo | Model | Đúng luồng | B/C bị trả lời như bài học | Câu bài học bị từ chối sai |
|---|---|---|---|---|
| 74 câu mặc định | cũ | 96,0% | 3,5% | 2,7% |
| 74 câu mặc định | **đang chạy** | **97,3%** | 3,5% | 2,7% |
| 74 câu mặc định | TF-IDF + e5 | 96,0% | 3,5% | 5,4% |
| 200 câu test tạm | cũ | 86,0% | 7,8% | 4,5% |
| 200 câu test tạm | **đang chạy** | 86,0% | 7,8% | 4,5% |
| 200 câu test tạm | TF-IDF + e5 | 88,0% | 7,8% | 6,3% |

Chú ý: model cũ đã học câu gần trùng với 200 câu test tạm, nên số của model cũ ở dòng đó lạc quan.
"B/C bị trả lời như bài học" vẫn 7,8% (mục tiêu ≤ 2%): lỗi này nằm ở tầng 2 (điểm truy xuất + luật), tầng 1 không sửa được.

**Đường học** của model đang chạy (macro-F1, CV theo nhóm): train 68 câu → 0,43; 316 → 0,69; 689 → 0,78; điểm trên phần
học luôn 1,00. Hai đường cách xa và đường CV còn đi lên: model đang học thuộc, **thêm dữ liệu thật còn giúp được**.

## 4. Giải thích cho nhóm

**Ví dụ nhỏ về rò dữ liệu.** Train có câu "hợp âm F gồm những nốt nào", test có "hop am F gom nhung not nao". Bỏ dấu đi
thì gần như một câu. Model chỉ cần nhớ là đúng, nên điểm test cao mà không chứng minh được model hiểu câu mới.

**Validation và test khác nhau thế nào.** Validation để chọn (tham số, model, sửa dữ liệu). Test để chấm một lần cuối.
Lần 1, Claude xem lỗi trên validation rồi soạn câu "vá" đúng những lỗi đó: validation tăng vọt (0,904 → 0,966) còn test
giảm (0,894 → 0,882). Nếu chỉ báo điểm validation thì sẽ tưởng model mới tốt hơn hẳn.

**Khoảng tin cậy.** Test chỉ có 20 câu chào hỏi: sai thêm 1 câu là recall nhãn đó tụt 5%. Bốc lại ngẫu nhiên 306 câu test
2000 lần, tính chênh lệch mỗi lần, lấy khoảng giữa 95%. Khoảng chứa (hoặc chạm) số 0 nghĩa là chưa chắc model nào hơn.

**Vì sao macro-F1.** 222/306 câu test là nhạc lý. Model đoán "nhạc lý" cho mọi câu cũng đúng 72,5%, nên accuracy dễ đánh lừa.
Macro-F1 lấy trung bình 4 nhãn ngang nhau, nhãn ít câu cũng được tính đủ.

**Vì sao số phân loại cao mà chọn model đơn giản.** Model chỉ là tầng 1; điều người học cảm nhận là cả luồng trả lời.
TF-IDF + e5 bắt câu ngoài phạm vi tốt hơn nhưng cũng hay gán nhầm câu nhạc lý thành "ngoài phạm vi" (ví dụ
"quang tu F len B la quang gi"), nên đo cả luồng mới thấy nó từ chối nhầm nhiều hơn.

```python
# Cốt lõi của script (rút gọn)
pipe = Pipeline([("vec", FeatureUnion([("tfidf", TfidfVectorizer(analyzer="char_wb")), ("e5", E5Features())])),
                 ("clf", LogisticRegression())])
gs = GridSearchCV(pipe, {"clf__C": [10, 30]}, cv=GroupKFold(5), scoring="f1_macro")
gs.fit(cau_train, nhan_train, groups=nhom)                          # chọn tham số chỉ trên train
f1_val = f1_score(nhan_val, gs.predict(cau_val), average="macro")   # chọn model
# ... chọn xong mới chấm test một lần
```

**5 câu giảng viên có thể hỏi**

| Câu hỏi | Trả lời gợi ý | Ai trả lời |
|---|---|---|
| Model mới khác model cũ chỗ nào? | Cùng thuật toán, cùng tham số; chỉ bỏ 325 câu train gần trùng câu chấm. Số đo giờ trung thực hơn | Thắng |
| Làm sao biết không rò dữ liệu? | Hàm `remove_leaks` và test `test_chia_du_lieu_khong_ro_cau_gan_trung` chạy trong CI | Thắng |
| GroupKFold khác KFold chỗ nào? | Các cách nói của cùng một ý (có dấu, không dấu, gõ tắt) luôn nằm cùng một phía, không "nhìn bài" của nhau | Đạt |
| Sao không dùng model e5, validation cao hơn? | Đo cả luồng thì nó từ chối nhầm câu bài học 6,3%, vượt mục tiêu 5% | Đạt |
| Dữ liệu ai viết? | Claude soạn, ghi rõ trong file; số chính thức cần tập test nhóm tự viết | Phúc |

## 5. Việc của từng bạn để kiểm

- **Thắng**: đọc `route_classifier._load_trained` (điều kiện nạp joblib), chạy `pytest -q tests/test_ml_route_train.py`.
- **Đạt**: rà nhãn `backend/app/ai/tutor/route_data_ml.json` (262 câu, status draft, hiện KHÔNG dùng để train).
- **Phúc**: đọc mục 4 để thuyết trình; sau khi gộp, thử vài câu trên AI Tutor (Docker build lại `api`).

Người kiểm: Thắng ☐ · Phúc ☐ · Đạt ☐

## 6. Kiểm chứng

- `cd backend && python -m app.ml.route_train --jobs 4`: chạy khoảng 1 phút trên cloud 4 nhân, ghi `DO_LUONG.json` và `backend/models/route/`.
- `cd backend && ROUTE_MODEL=old|auto|experiment python ../scripts/ai/gop_y/danh_gia_dinh_tuyen.py [--set ../scripts/ai/data/gd2/test_tam.json] --out ...`
- `cd backend && pytest -q`: **1492 passed, 44 skipped** (19/11/2026, máy cloud có e5; 44 skip là test PostgreSQL/Qdrant chạy ở CI). 11 test mới trong `tests/test_ml_route_train.py`. `ci.yml --min-passed` 1481 → 1492.
- Frontend không đổi nên không chạy `npm run build`.

Kết quả trên dữ liệu do Claude soạn, chưa chứng minh chất lượng với người học thật.

## 7. Rủi ro

1. File joblib gắn với scikit-learn 1.9.1. Docker cài bản khác thì app tự dùng model cũ (an toàn, có cảnh báo trong log);
   muốn dùng model mới thì chạy lại `python -m app.ml.route_train` trong image rồi commit.
2. Mức tăng +0,017 nằm sát ranh giới khoảng tin cậy. Khi nhóm có tập test tự viết, chạy lại một lệnh để xác nhận.
3. Các ngưỡng tầng 2 (`router_thresholds.json`) được chọn với xác suất của model cũ; model đang chạy cùng công thức nên
   xác suất gần giống, và đo cả luồng không kém đi, nên chưa chỉnh ngưỡng.
