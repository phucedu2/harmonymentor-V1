# CP2 · Hợp đồng test cho Mastery và hệ gợi ý

Trạng thái: **DRAFT**, đi cùng [ADR-008](decisions/ADR-008-vector-14-nhom.md) bản 4 và [bảng ánh xạ](CP2_ANH_XA_KY_NANG.md). Chưa có code, chưa đổi schema. Cập nhật 30/10/2026.

Quy trình cho mỗi PR: viết test trước, đẩy lên để CI **đỏ có chủ đích**, rồi mới sửa code cho xanh. Chỉ được đổi kỳ vọng của test khi ADR đổi. Cột "Phụ thuộc" ghi mã quyết định trong ADR-008, mục "Cần quyết định". Nếu Thắng chọn khác thì sửa ca đó, các ca còn lại giữ nguyên.

| Tiền tố | PR | File test |
|---|---|---|
| M | PR-4 | `backend/tests/test_cp2_skill_mapping.py` |
| S | PR-5, PR-5b | `backend/tests/test_cp2_mastery_ema.py` (hàm thuần), `backend/tests/test_cp2_mastery_scope.py` (qua API) |
| V | PR-7 | `backend/tests/test_cp2_mastery_vector.py` |
| K, C, R | PR-7 | `backend/tests/test_cp2_knn_similarity.py`, `test_cp2_cf.py`, `test_cp2_recommend_list.py` |
| E | PR-8 | `backend/tests/test_cp2_knn_experiment.py`, kèm báo cáo trong `docs/giai-doan/` |

## 0. Schema: cái gì đã có, cái gì phải thêm

Đã đối chiếu `backend/app/db/models.py` (`main` 58a6f52) với 04 mục 2.

| Trường | Có trong 04 | Có trong code | Ai thêm |
|---|---|---|---|
| `skills.group_code` | có | không | PR-4 |
| `skills.srs_code` | không (lấy từ ADR-003) | không | PR-4 |
| `skills.ready_threshold` (0,6), `skills.mastery_threshold` (0,8) | có | không | PR-4 |
| Bảng `mastery_states` (`user_id`, `skill_id`, `score`, `attempts_count`, `last_error_code`, `updated_at`) | có | không | PR-5 |
| `attempts.is_test` | có | không | PR-5 |
| `attempts.input_method` | có | không | Migration riêng (HM-011), ngoài các PR CP2 |
| Cờ "đúng sau gợi ý" (`hint_used`) | không | không | **Chưa thêm.** Chưa có API gợi ý cho câu bài tập. Khi có thì làm ticket riêng |
| "Làm lại" | không cần cột | suy ra được từ `attempts` (`user_id`, phiên bản → `exercise_id`, `created_at`) | Không cần migration |
| `users.is_synthetic` | có | có | Đã có |
| Bài kiểm tra đầu vào `/placement/*` | có | không | PR-5b tự đặc tả phần lưu trữ |

## M. Mapping (PR-4)

Không khóa cứng số kỹ năng. Tại `main` 58a6f52 có 26 kỹ năng (13 MVP, 13 `post_mvp`). Test so với tập `SKILLS`, không so với con số 26.

| Mã | Ca | Mong đợi |
|---|---|---|
| M1 | Tập kỹ năng có ánh xạ so với tập id trong `SKILLS` | Bằng nhau, không thiếu, không thừa |
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
| M12 | Thứ tự chiều | `GROUP_CODES` có đúng 14 phần tử, theo thứ tự ở mục 3 của bảng ánh xạ |
| M13 | Ngưỡng | Mọi kỹ năng sau seed có `ready_threshold` = 0,6 và `mastery_threshold` = 0,8. Ràng buộc 0 < ready < mastery ≤ 1 |

Migration của PR-4 phải qua `alembic upgrade head` và `alembic check` trên PostgreSQL trong CI.

## S. Mastery EMA (PR-5, PR-5b)

Công thức theo 04 mục 6.3: `mới = cũ + 0,3 × (kết_quả − cũ)`. `kết_quả` bằng 1 khi đúng ngay, bằng 0,5 khi đúng sau gợi ý hoặc sau khi làm lại, bằng 0 khi sai. Cách hiểu "làm lại" xem D-3.

**Hàm thuần** (`test_cp2_mastery_ema.py`). So sánh với sai số 1e-9. Các số làm tròn chỉ để dễ đọc.

| Mã | Ca | Mong đợi | Phụ thuộc |
|---|---|---|---|
| S1 | Đúng ngay, từ 0 | 0,30 | |
| S2 | 5 lần đúng ngay liên tiếp, từ 0, trên 5 câu khác nhau | 0,30 → 0,51 → 0,657 → 0,7599 → 0,83193 | |
| S3 | Đúng ngay, từ 0,50 | 0,65 (ví dụ của 04) | |
| S4 | Sai, từ 0,65 | 0,455 (ví dụ của 04) | |
| S5 | Làm lại: sai câu Q rồi đúng câu Q, từ 0 | Sau lượt sai: 0. Sau lượt đúng (kết quả 0,5): 0,15 | D-3 |
| S6 | Làm lại qua hai phiên bản: sai Q ở v1, đúng Q ở v2 | Lượt đúng có kết quả 0,5 | D-3 |
| S7 | Đúng lặp lại: đúng Q rồi lại đúng Q, từ 0 | 0,30 rồi giữ nguyên 0,30 (chống cày điểm) | D-3 |
| S8 | Ngưỡng 0,60 (đủ để học tiếp) | 0,51 chưa đủ, 0,657 đủ. Đúng bằng 0,60 thì tính là đủ (≥). Ngưỡng đọc từ `skills.ready_threshold` | |
| S9 | Ngưỡng 0,80 (thành thạo) | 0,7599 chưa, 0,83193 rồi. Đúng bằng 0,80 thì tính là thành thạo. Ngưỡng đọc từ `skills.mastery_threshold` | |
| S10 | Kỹ năng yếu (04 Bảng 19) | Điểm 0,455 với `attempts_count` = 5 là yếu. Cùng điểm đó với `attempts_count` = 4 thì chưa xếp là yếu | |

**Qua API** (`test_cp2_mastery_scope.py`):

| Mã | Ca | Mong đợi |
|---|---|---|
| S11 | Làm đúng L04-Q03 (`voicing.guide_tones`, `post_mvp`) | Lượt làm được ghi và vẫn tính để hoàn thành bài, nhưng **không** tạo dòng `mastery_states` |
| S12 | Làm đúng L04-Q01 (`progression.ii_v_i`) lần đầu | `mastery_states.score` = 0,30, `attempts_count` = 1 |
| S13 | Lượt làm của Admin (`is_test = true`) | Lượt làm được ghi với `is_test = true`. Mastery không đổi |
| S14 | `GET /me/mastery` | Chỉ trả kỹ năng MVP, kèm `group_code`. Không thấy mastery của người khác |
| S15 | (PR-5b) Làm đúng một kỹ năng trong bài kiểm tra đầu vào | Mastery của kỹ năng đó được đặt bằng 0,65 |

Ca "đúng sau gợi ý thì kết quả 0,5" **chưa viết**, vì chưa có API gợi ý cho câu bài tập. Đây là khoảng trống đã ghi nhận. Không dùng test bị skip để đánh dấu ca này.

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

| Mã | Ca | Mong đợi |
|---|---|---|
| K1 | Các cặp có số chiều chung khác nhau | A–B: chung {2, 3, 6}, tương đồng 1,0000. B–C: chung {2, 3, 6, 7}, tương đồng 0,8324. A–C: chung {2, 3, 6}, tương đồng 0,7894. Mỗi cặp chỉ dùng chiều chung của riêng cặp đó |
| K2 | Z–Z: cả hai toàn 0 trên chiều chung | Không tính cosine, không trả về số nào. Lý do `zero_norm`. Không vào danh sách láng giềng (Thắng đã chốt Q-5) |
| K3 | Z–A: một bên toàn 0 trên chiều chung {2, 3} | Như K2 (Thắng đã chốt Q-5) |
| K4 | Số chiều chung nhỏ hơn ngưỡng | Không phải láng giềng. Ngưỡng là tham số, test chạy với ngưỡng 2, 3 và 4 |
| K5 | Không còn láng giềng hợp lệ (gồm trường hợp mọi ứng viên bị loại vì K2, K3 hoặc K4) | Đi vào nhánh dự phòng, lý do `no_valid_neighbors`. Mastery hiện có giữ nguyên và vẫn dùng trong `(1 − mastery)`. Độ dài danh sách tuân theo R1–R3, **không** bắt buộc đủ 5 bài |
| K6 | Người chưa có chiều nào được đánh giá | Không tìm láng giềng. Dùng công thức người học mới 0,55 / 0,25 / 0,20 |
| K7 | Người `is_synthetic` | Vẫn có vector và được dùng trong mô phỏng |
| K8 | Giới hạn đã biết (ADR-008 mục 3b): X = {`function.tonic` 0,30}, Y = {`progression.ii_v_i` 0,30} | Chỉ có 1 chiều chung (chiều 9). Cosine thô trên chiều này bằng 1,0000, nhưng X–Y **không phải láng giềng hợp lệ** với mọi ngưỡng đang thử (2, 3, 4). Độ trùng kỹ năng trên chiều 9 bằng 0 |
| K9 | Độ trùng kỹ năng: X' = {`function.tonic`, `function.dominant`}, Y' = {`function.tonic`, `progression.ii_v_i`} | Jaccard chiều 9 = 1/3 |
| K10 | Tất định | Cùng đầu vào thì cùng danh sách láng giềng, cùng thứ tự |

## C. Thành phần `cf` (PR-7, hàm thuần)

Định nghĩa ở ADR-008 mục 4. Mọi ca trong bảng này phụ thuộc **D-2**.

Ví dụ: người T có 4 láng giềng hợp lệ. Tại mốc thời gian, mastery của kỹ năng s của từng láng giềng là N1 = 0,66, N2 = 0,60, N3 = 0,51, còn N4 chưa từng làm s.

| Mã | Ca | Mong đợi |
|---|---|---|
| C1 | Ví dụ trên | `cf(s)` = 2/4 = 0,50. N2 đạt đúng 0,60 nên được tính là "học tốt" |
| C2 | Láng giềng chưa làm kỹ năng | N4 vẫn nằm trong mẫu số. Nếu bỏ N4 khỏi danh sách láng giềng thì `cf` = 2/3 |
| C3 | Có hơn 10 láng giềng hợp lệ | Chỉ dùng 10 láng giềng có độ tương đồng cao nhất. Mẫu số bằng 10 |
| C4 | Dữ liệu sau mốc | N3 đạt 0,66 sau mốc thời gian thì vẫn tính là 0,51, `cf` không đổi |
| C5 | Không có láng giềng hợp lệ | Không tính `cf`. Dùng phương án dự phòng (K5) |
| C6 | Cặp bị loại vì `zero_norm` | Không nằm trong mẫu số |
| C7 | `cf` của bài | Bằng trung bình `cf` trên các kỹ năng **chưa thành thạo** (< 0,80) mà bài dạy. Kỹ năng đã từ 0,80 trở lên không được tính |

## R. Danh sách gợi ý (PR-7, qua API hoặc hàm thuần)

Các ca này phụ thuộc **R-1**.

| Mã | Ca | Mong đợi |
|---|---|---|
| R1 | Có ít hơn 5 bài đủ điều kiện (ví dụ 3 bài) | Trả đúng 3 bài, không lặp bài, lý do `few_eligible` |
| R2 | Có bài mà kỹ năng tiên quyết dưới 0,60 | Bài đó không bao giờ có trong danh sách, kể cả khi danh sách đang thiếu |
| R3 | Không có bài nào đủ điều kiện | Danh sách rỗng, lý do `few_eligible`, mã 200 |
| R4 | Bài có mọi kỹ năng đã từ 0,80 trở lên, hoặc bài chỉ dạy kỹ năng `post_mvp` | Không được gợi ý |

## E. Thử nghiệm (PR-8)

| Mã | Ca | Mong đợi | Phụ thuộc |
|---|---|---|---|
| E1 | Chống rò rỉ, người được gợi ý | Mọi dữ liệu dùng để tính mastery, vector, Leitner và tiến độ bài đều xảy ra trước mốc cắt | |
| E2 | Chống rò rỉ, láng giềng | Mọi dữ liệu dùng để tính vector và `cf` của láng giềng đều xảy ra trước mốc cắt của người được gợi ý | |
| E3 | Tách dữ liệu | Phần giữ lại là đúng 20% lượt cuối của mỗi người (làm tròn xuống, tối thiểu 1). Hai phần không giao nhau | |
| E4 | Bộ sinh độc lập | Bộ sinh hành vi không gọi bộ gợi ý đang được đánh giá | |
| E5 | Tái lập | Cùng seed thì cùng bảng kết quả | |
| E6 | Các phương án | P0–P3 chạy trên cùng cách tách dữ liệu và cùng seed. P3 chạy đủ 6 cấu hình | R-3 |
| E7 | Định nghĩa "trúng" | Ví dụ: người học đã bắt đầu L02 trước mốc cắt và làm tiếp L02 trong phần giữ lại. Gợi ý L02 **không** trúng. Bắt đầu L03 lần đầu trong phần giữ lại: gợi ý L03 trúng | D-1 |
| E8 | Cách tính chỉ số | Gợi ý [L02, L03, L04], chỉ L03 trúng: HitRate@5 = 1, Precision@5 chính = 1/3, Precision@5 phụ = 1/5, MRR = 1/2, HitRate@1 = 0 | R-2, R-4 |
| E9 | Danh sách rỗng | Tính là trượt khi tính HitRate, bị loại khỏi Precision chính, được đếm và báo cáo riêng | R-2 |
| E10 | Vector toàn 0 và không có láng giềng | Không người nào có vector toàn 0 xuất hiện trong danh sách láng giềng. Tỷ lệ dùng dự phòng được báo cáo, tách theo lý do. Độ dài danh sách theo R1–R3 | |
| E11 | Hiệu năng | Gợi ý cho một người khi so với 2.000 người: p95 ≤ 200 ms trên máy CI. Thời gian chạy toàn bộ được ghi lại | |
| E12 | Báo cáo | P0–P3 × (HitRate, Precision chính và phụ ở @1, @3, @5, MRR, kèm khoảng tin cậy bootstrap 95%; độ phủ láng giềng; số láng giềng trung bình; tỷ lệ dự phòng theo lý do; tỷ lệ `few_eligible` và tỷ lệ danh sách rỗng; độ trùng kỹ năng), tách theo chân dung, kèm lệnh chạy và seed. Ghi rõ rằng @5 bị bão hòa khi chỉ có 4 bài | R-4 |
