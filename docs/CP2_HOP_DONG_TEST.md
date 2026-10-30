# CP2 · Hợp đồng test cho Mastery và KNN

Trạng thái: **DRAFT**, đi cùng [ADR-008](decisions/ADR-008-vector-14-nhom.md) bản 3 và [bảng ánh xạ](CP2_ANH_XA_KY_NANG.md). Chưa có code. Cập nhật 30/10/2026.

Mỗi PR viết test của mình trước, đẩy lên để CI **đỏ có chủ đích**, rồi mới sửa code cho xanh. Test chỉ được đổi kỳ vọng khi ADR đổi. Ca nào phụ thuộc câu đang chờ Thắng thì ghi rõ ở cột "Phụ thuộc".

| Tiền tố | PR | File test |
|---|---|---|
| M | PR-4 | `backend/tests/test_cp2_skill_mapping.py` |
| S | PR-5 | `backend/tests/test_cp2_mastery_scope.py` |
| V | PR-7 | `backend/tests/test_cp2_mastery_vector.py` |
| K | PR-7 | `backend/tests/test_cp2_knn_similarity.py` |
| E | PR-8 | `backend/tests/test_cp2_knn_experiment.py`, kèm báo cáo trong `docs/giai-doan/` |

## M. Mapping (PR-4)

Không khóa cứng số kỹ năng. Tại `main` 58a6f52 bảng có 26 kỹ năng (13 MVP, 13 `post_mvp`), nhưng test so sánh với tập `SKILLS` chứ không so với con số 26.

| Mã | Ca | Mong đợi |
|---|---|---|
| M1 | Tập kỹ năng có ánh xạ so với tập id trong `SKILLS` | Bằng nhau: không thiếu, không thừa |
| M2 | Mỗi kỹ năng trong bảng ánh xạ | Xuất hiện đúng một lần |
| M3 | Miền giá trị | `srs_code` ∈ {10 mã} ∪ {`post_mvp`}, `group_code` ∈ 14 mã |
| M4 | Bất biến 1 | `srs_code` ≠ `post_mvp` ⇒ `group_code` = `srs_code` |
| M5 | Bất biến 2 | `group_code` ∈ nhóm 11–14 ⇔ `srs_code` = `post_mvp` |
| M6 | Mã chưa có kỹ năng | Đúng bằng danh sách khai báo tường minh (hiện là `note_names`, `minor_scales`, `rhythm_basics`, `pop_harmony`) |
| M7 | Tiên quyết | Mọi tiên quyết của kỹ năng MVP đều là kỹ năng MVP. Đồ thị không có chu trình |
| M8 | Tự kiểm: thêm kỹ năng giả chưa ánh xạ | Bộ kiểm báo thiếu |
| M9 | Tự kiểm: thêm dòng ánh xạ trùng | Bộ kiểm báo trùng |
| M10 | Quyết định Thắng 30/10 | `scale.parallel_minor` → `post_mvp`, `chromatic_harmony` |
| M11 | Quyết định Thắng 30/10 | `voicing.guide_tones`, `voicing.voice_leading` → `post_mvp`, `jazz_voicing` |
| M12 | Thứ tự chiều | `GROUP_CODES` đúng 14 phần tử, đúng thứ tự ở mục 3 của bảng ánh xạ |

Migration của PR-4 cũng phải qua `alembic upgrade head` và `alembic check` trên PostgreSQL trong CI.

## S. Phạm vi Mastery (PR-5, gọi qua API)

| Mã | Ca | Mong đợi |
|---|---|---|
| S1 | Làm đúng L04-Q03 (`voicing.guide_tones`) | Lượt làm được ghi, vẫn được tính để hoàn thành bài, **không** tạo dòng mastery |
| S2 | Làm đúng L04-Q01 (`progression.ii_v_i`) lần đầu | Mastery tăng từ 0 lên 0,30 (EMA α = 0,3) |
| S3 | `GET /me/mastery` | Chỉ trả kỹ năng MVP, mỗi kỹ năng kèm `group_code` |
| S4 | Lượt làm `is_test` | Không tạo hoặc đổi mastery |

## V. Vector `(value, assessed)` (PR-7, hàm thuần, không đọc CSDL)

Đầu vào chỉ ghi các kỹ năng đã đánh giá.

| Mã | Đầu vào | Mong đợi |
|---|---|---|
| V1 | Người chưa có dữ liệu: {} | `value` = 14 số 0, `assessed` = 14 giá trị false |
| V2 | `pitch.spelling` = 0, `interval.naming` = 0 | Chiều 2 và 3: `value` 0, `assessed` true. Các chiều khác: `assessed` false |
| V3 | `chord.triad_formula` = 0,51, `chord.triad_build` chưa đánh giá | Chiều 6 = **0,51**, không phải 0,255 |
| V4 | `function.tonic` = 0,30, `function.dominant` = 0,66 | Chiều 9 = 0,48 |
| V5 | Chỉ có `voicing.guide_tones` = 0,9 (`post_mvp`) | Giống V1 |
| V6 | Bất kỳ | Luôn 14 phần tử, theo thứ tự `GROUP_CODES` |
| V7 | Chỉ có lượt `is_test` | Giống V1 |

## K. Độ tương đồng và láng giềng (PR-7, hàm thuần)

Ví dụ dùng chung (số trong ngoặc là chiều):

- A = {(2) 0,30; (3) 0,51; (6) 0,66}
- B = {(2) 0,30; (3) 0,51; (6) 0,66; (7) 0,51; (9) 0,30}
- C = {(2) 0,66; (3) 0,30; (4) 0,51; (6) 0,30; (7) 0,83}
- Z = {(2) 0; (3) 0}, tức là đã đánh giá nhưng toàn 0

| Mã | Ca | Mong đợi | Phụ thuộc |
|---|---|---|---|
| K1 | Các cặp có số chiều chung khác nhau | A–B: chung {2, 3, 6}, tương đồng 1,0000. B–C: chung {2, 3, 6, 7}, tương đồng 0,8324. A–C: chung {2, 3, 6}, tương đồng 0,7894. Mỗi cặp chỉ dùng chiều chung của riêng cặp đó | |
| K2 | Z–Z: cả hai toàn 0 trên chiều chung | **Không so sánh được**, lý do `zero_norm`. Không trả về số nào, không có trong danh sách láng giềng | Q-5 |
| K3 | Z–A: một bên toàn 0 trên chiều chung {2, 3} | **Không so sánh được**, lý do `zero_norm`. Không có trong danh sách láng giềng | Q-5 |
| K4 | Số chiều chung nhỏ hơn ngưỡng | Không phải láng giềng. Ngưỡng là tham số; test chạy với ngưỡng 2, 3 và 4 | |
| K5 | Không còn láng giềng hợp lệ (gồm trường hợp mọi ứng viên bị loại vì K2, K3 hoặc K4) | Đi vào nhánh dự phòng, trả lý do `no_valid_neighbors`, vẫn đủ 5 gợi ý | |
| K6 | Người chưa có chiều nào được đánh giá | Không tìm láng giềng. Dùng công thức người học mới 0,55/0,25/0,20 | |
| K7 | Người `is_synthetic` | Vẫn có vector và được dùng trong mô phỏng | |
| K8 | Giới hạn đã biết (ADR-008 mục 3b): X = {`function.tonic` 0,30}, Y = {`progression.ii_v_i` 0,30} | Trên chiều 9: tương đồng 1,0000 (hành vi hiện tại, được ghi nhận có chủ đích) **và** độ trùng kỹ năng = 0 | |
| K9 | Độ trùng kỹ năng: X' = {`function.tonic`, `function.dominant`}, Y' = {`function.tonic`, `progression.ii_v_i`} | Jaccard chiều 9 = 1/3 | |
| K10 | Tất định | Cùng đầu vào thì cùng danh sách láng giềng, cùng thứ tự | |

Nếu Thắng không đồng ý Q-5 thì K2 và K3 đổi kỳ vọng theo quyết định của Thắng, các ca khác giữ nguyên.

## E. Thử nghiệm KNN (PR-8)

| Mã | Ca | Mong đợi |
|---|---|---|
| E1 | Chống rò rỉ, người được gợi ý | Mọi lượt làm dùng để tính mastery, vector và Leitner của người đó đều xảy ra trước mốc cắt |
| E2 | Chống rò rỉ, láng giềng | Mọi lượt làm dùng để tính vector láng giềng đều xảy ra trước mốc cắt của người được gợi ý |
| E3 | Tách dữ liệu | Phần giữ lại đúng 20% lượt cuối của mỗi người (làm tròn xuống, tối thiểu 1). Phần huấn luyện và phần giữ lại không giao nhau |
| E4 | Mô phỏng độc lập | Chính sách sinh hành vi không gọi bộ gợi ý đang được đánh giá |
| E5 | Tái lập | Cùng seed thì cùng bảng kết quả |
| E6 | Mốc so sánh | Mốc chính (công thức người học mới) và mốc độ phổ biến chạy trên cùng cách tách dữ liệu, cùng seed |
| E7 | Vector toàn 0 | Không người nào có vector toàn 0 xuất hiện trong danh sách láng giềng. Những người này luôn đi vào nhánh dự phòng |
| E8 | Không có láng giềng | Tỷ lệ phải dùng dự phòng được báo cáo, tách theo lý do (`zero_norm`, `no_valid_neighbors`, chưa có chiều nào được đánh giá), và mọi người vẫn đủ 5 gợi ý |
| E9 | Hiệu năng | Gợi ý cho một người khi so với 2.000 người: p95 ≤ 200 ms trên máy CI. Thời gian chạy toàn bộ được ghi lại để tham khảo |
| E10 | Báo cáo | 6 cấu hình + 2 mốc so sánh × (HitRate@5, Precision@5 kèm khoảng tin cậy bootstrap 95%, độ phủ láng giềng, số láng giềng trung bình, tỷ lệ dự phòng, phân bố độ trùng kỹ năng), tách theo chân dung, kèm lệnh chạy và seed |

Định nghĩa "trúng", cách tách theo mốc cắt và hai mốc so sánh: xem ADR-008 mục 4.
