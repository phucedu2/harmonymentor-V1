# CP2 · Ánh xạ kỹ năng → mã SRS → nhóm KNN

Trạng thái: **DRAFT, chờ Thắng duyệt cuối cùng** cùng với [ADR-008](decisions/ADR-008-vector-14-nhom.md). Chưa có code. PR-4 và PR-5 chưa được làm.

Phạm vi: đối chiếu với `main` 58a6f52, cập nhật ngày 30/10/2026. Đây là bản thống nhất duy nhất. Claude Doc và file `.md` trong thư mục project chỉ là bản sao sinh ra từ file này.

## 1. Quy ước

| Khái niệm | Định nghĩa |
|---|---|
| `srs_code` | Một trong 10 mã SRS của ADR-003, hoặc `post_mvp`. Đây là **phạm vi MVP**: chỉ kỹ năng có mã khác `post_mvp` mới được cộng Mastery, gợi ý và lộ trình. |
| `group_code` | Một trong 14 nhóm (mục 3). Mỗi nhóm là **một chiều** của vector KNN. |
| Kỹ năng **đã đánh giá** | Có ít nhất một sự kiện mastery được tính, từ lượt làm trong bài học hoặc trong bài kiểm tra đầu vào. Lượt `is_test` không tính. |
| Chiều **đã đánh giá** | Nhóm có ít nhất một kỹ năng MVP đã đánh giá. |
| `value` của một chiều | Trung bình mastery của các kỹ năng MVP **đã đánh giá** trong nhóm. Kỹ năng chưa đánh giá **không** tính là 0. |
| Chiều **chưa đánh giá** | `assessed = false`. `value` để 0 chỉ cho đủ hình dạng mảng, không có nghĩa là mastery bằng 0. |

Hai bất biến:

- Nếu `srs_code` ≠ `post_mvp` thì `group_code` = `srs_code`.
- `group_code` thuộc nhóm 11–14 khi và chỉ khi `srs_code` = `post_mvp`.

## 2. Bảng ánh xạ kỹ năng hiện có

Số câu chỉ đếm câu `published`, chưa `retired`, trong L01–L04 (4 bài đang chạy cho người học).

| # | Kỹ năng | Bài | `srs_code` | `group_code` | Câu chạy | Cộng Mastery MVP | Trạng thái |
|---|---|---|---|---|---|---|---|
| 1 | `pitch.spelling` | L01 | accidentals | 2 `accidentals` | 1 | Có | |
| 2 | `interval.naming` | L01 | intervals | 3 `intervals` | 1 | Có | |
| 3 | `chord.triad_formula` | L01 | triads | 6 `triads` | 1 | Có | |
| 4 | `chord.triad_build` | L01 | triads | 6 `triads` | 3 | Có | |
| 5 | `scale.major` | L02 | major_scales | 4 `major_scales` | 1 | Có | |
| 6 | `chord.seventh_quality` | L02 | seventh_chords | 7 `seventh_chords` | 2 | Có | |
| 7 | `chord.seventh_build` | L02 | seventh_chords | 7 `seventh_chords` | 2 | Có | |
| 8 | `roman.major_seventh` | L02 | diatonic_chords | 8 `diatonic_chords` | 1 | Có | |
| 9 | `function.tonic` | L03 | progressions | 9 `progressions` | 1 | Có | |
| 10 | `function.predominant` | L03 | progressions | 9 `progressions` | 1 | Có | |
| 11 | `function.dominant` | L03 | progressions | 9 `progressions` | 1 | Có | |
| 12 | `function.progression` | L03 | progressions | 9 `progressions` | 3 | Có | |
| 13 | `progression.ii_v_i` | L04 | progressions | 9 `progressions` | 2 | Có | |
| 14 | `voicing.guide_tones` | L04, L08 | post_mvp | 13 `jazz_voicing` | 2 | Không | Thắng chốt 30/10. Xem QA-L04-Q03 |
| 15 | `voicing.voice_leading` | L04, L08 | post_mvp | 13 `jazz_voicing` | 2 | Không | Thắng chốt 30/10 |
| 16 | `voicing.shell` | L08 | post_mvp | 13 `jazz_voicing` | 0 | Không | |
| 17 | `harmony.secondary_dominant.identify` | L05 | post_mvp | 11 `chromatic_harmony` | 0 | Không | |
| 18 | `harmony.secondary_dominant.build` | L05 | post_mvp | 11 `chromatic_harmony` | 0 | Không | |
| 19 | `harmony.secondary_dominant.apply` | L05 | post_mvp | 11 `chromatic_harmony` | 0 | Không | |
| 20 | `scale.parallel_minor` | L06 | post_mvp | 11 `chromatic_harmony` | 0 | Không | **Chờ Thắng xác nhận** (ADR-003 cũ xếp vào `minor_scales`) |
| 21 | `harmony.modal_interchange.identify` | L06 | post_mvp | 11 `chromatic_harmony` | 0 | Không | |
| 22 | `harmony.modal_interchange.apply` | L06 | post_mvp | 11 `chromatic_harmony` | 0 | Không | |
| 23 | `tension.naming` | L07 | post_mvp | 14 `jazz_scales_tensions` | 0 | Không | |
| 24 | `mode.basic` | L07 | post_mvp | 14 `jazz_scales_tensions` | 0 | Không | |
| 25 | `chord_scale.basic` | L07 | post_mvp | 14 `jazz_scales_tensions` | 0 | Không | |
| 26 | `chord_scale.context` | L07 | post_mvp | 14 `jazz_scales_tensions` | 0 | Không | |

Quyết định của Thắng (30/10): hai kỹ năng `voicing.guide_tones` và `voicing.voice_leading` của L04 giữ `post_mvp` và không cộng Mastery trước CP2. Các câu của hai kỹ năng này, trong đó có L04-Q03, vẫn được chấm và vẫn được dùng để xét hoàn thành bài.

Cột thứ ba của `SKILLS` trong `skill_graph.py` (`foundation`, `harmony`, `jazz_core`, `piano`, `chromatic_harmony`, `jazz`) là "domain" cũ. Nó **không phải** `group_code`.

## 3. 14 chiều của vector KNN

Thứ tự các chiều là cố định. Muốn đổi thứ tự hay tên chiều thì phải có ADR mới. Tên 4 nhóm 11–14 **đang chờ Thắng xác nhận**.

| Chiều | `group_code` | Kỹ năng MVP | Có thể được đánh giá với dữ liệu L01–L04 |
|---|---|---|---|
| 1 | `note_names` | chưa có kỹ năng | không |
| 2 | `accidentals` | `pitch.spelling` | có |
| 3 | `intervals` | `interval.naming` | có |
| 4 | `major_scales` | `scale.major` | có |
| 5 | `minor_scales` | chưa có kỹ năng (cần kỹ năng âm giai thứ thật, qua ticket Astra) | không |
| 6 | `triads` | `chord.triad_formula`, `chord.triad_build` | có |
| 7 | `seventh_chords` | `chord.seventh_quality`, `chord.seventh_build` | có |
| 8 | `diatonic_chords` | `roman.major_seventh` | có |
| 9 | `progressions` | `function.tonic`, `function.predominant`, `function.dominant`, `function.progression`, `progression.ii_v_i` | có |
| 10 | `rhythm_basics` | chưa có kỹ năng | không |
| 11 | `chromatic_harmony` | không có kỹ năng MVP | không |
| 12 | `pop_harmony` | không có kỹ năng MVP | không |
| 13 | `jazz_voicing` | không có kỹ năng MVP | không |
| 14 | `jazz_scales_tensions` | không có kỹ năng MVP | không |

Với dữ liệu hiện có, tối đa **7/14 chiều** có thể được đánh giá (2, 3, 4, 6, 7, 8, 9). Mô phỏng ở PR-8 chỉ sinh dữ liệu trên 7 chiều này.

**Độ phủ câu hỏi:** với EMA α = 0,3, một kỹ năng cần ít nhất 3 câu thì mastery mới vượt 0,60. Trong 13 kỹ năng MVP đang chạy, chỉ `chord.triad_build` và `function.progression` có đủ 3 câu (rủi ro HM-013). Câu bổ sung đi theo ticket Astra.

## 4. Quy tắc bao phủ mapping

Các quy tắc này phải đúng dù số kỹ năng tăng hay giảm, nên test **không khóa cứng con số 26**:

1. Tập kỹ năng có ánh xạ **bằng đúng** tập id trong `SKILLS`. Không kỹ năng nào thiếu ánh xạ, và không có ánh xạ nào trỏ tới kỹ năng không tồn tại.
2. Mỗi kỹ năng xuất hiện **đúng một lần** trong bảng ánh xạ, không có dòng trùng.
3. `srs_code` thuộc {10 mã} ∪ {`post_mvp`}. `group_code` thuộc 14 mã.
4. Hai bất biến ở mục 1 luôn đúng.
5. Danh sách 10 mã SRS và 14 nhóm được khai báo đầy đủ. Mã chưa có kỹ năng nào phải nằm trong danh sách "chưa có kỹ năng" được khai báo tường minh. Hiện danh sách này gồm `note_names`, `minor_scales`, `rhythm_basics`, `pop_harmony`. Có kỹ năng mới cho mã nào thì phải gỡ mã đó khỏi danh sách.
6. Mọi tiên quyết của một kỹ năng MVP cũng phải là kỹ năng MVP. Hiện điều này đúng.
7. Đồ thị tiên quyết không có chu trình.

## 5. Đặc tả test (viết trước, đỏ trước, xanh sau)

### A. Mapping (`tests/test_cp2_skill_mapping.py`)

Gồm 7 quy tắc ở mục 4, cộng thêm 2 ca kiểm tra chính bộ kiểm:

- Thêm vào `SKILLS` một kỹ năng giả mà chưa có ánh xạ: bộ kiểm phải báo thiếu.
- Thêm một dòng ánh xạ trùng: bộ kiểm phải báo trùng.

### B. Vector `(value, assessed)` (`tests/test_cp2_mastery_vector.py`, hàm thuần, không đọc CSDL)

| Ca | Đầu vào (mastery theo kỹ năng, chỉ ghi kỹ năng đã đánh giá) | Kết quả mong đợi |
|---|---|---|
| B1. Người chưa có dữ liệu | {} | `value` = 14 số 0, `assessed` = 14 giá trị false |
| B2. Đã đánh giá nhưng toàn 0 | `pitch.spelling` = 0, `interval.naming` = 0 | Chiều 2 và 3: `value` 0, `assessed` true. Các chiều khác: `assessed` false |
| B3. Chỉ lấy trung bình kỹ năng đã đánh giá | `chord.triad_formula` = 0,51, `chord.triad_build` chưa đánh giá | Chiều 6 = **0,51**, không phải 0,255 |
| B4. Trung bình nhiều kỹ năng | `function.tonic` = 0,30, `function.dominant` = 0,66 | Chiều 9 = 0,48 |
| B5. Kỹ năng `post_mvp` bị bỏ qua | `voicing.guide_tones` = 0,9 | Vector giống ca B1 |
| B6. Độ dài và thứ tự | bất kỳ | Luôn 14 phần tử, theo thứ tự `GROUP_CODES` |
| B7. Lượt `is_test` | chỉ có lượt `is_test` | Giống ca B1 |

### C. Độ tương đồng và láng giềng (`tests/test_cp2_knn_similarity.py`, hàm thuần)

Độ tương đồng là cosine, chỉ tính trên các chiều mà **cả hai** người cùng `assessed = true`. Quy ước cho vector độ dài 0 trên các chiều chung: nếu cả hai đều toàn 0 thì độ tương đồng là 1. Nếu chỉ một bên toàn 0 thì độ tương đồng là 0.

Ví dụ dùng chung cho các ca dưới đây (số trong ngoặc là chiều):

- A = {(2) 0,30; (3) 0,51; (6) 0,66}
- B = {(2) 0,30; (3) 0,51; (6) 0,66; (7) 0,51; (9) 0,30}
- C = {(2) 0,66; (3) 0,30; (4) 0,51; (6) 0,30; (7) 0,83}

| Ca | Mong đợi |
|---|---|
| C1. Hai cặp có số chiều chung khác nhau | A–B: chung {2, 3, 6}, tương đồng 1,0000. B–C: chung {2, 3, 6, 7}, tương đồng 0,8324. A–C: chung {2, 3, 6}, tương đồng 0,7894. Mỗi cặp chỉ dùng chiều chung của riêng cặp đó |
| C2. Cả hai toàn 0 trên chiều chung | Tương đồng 1 |
| C3. Một bên toàn 0 | Tương đồng 0 |
| C4. Số chiều chung nhỏ hơn ngưỡng | Không được tính là láng giềng. Ngưỡng là tham số, **chưa chốt** (ADR-008 mục 4) |
| C5. Không có láng giềng hợp lệ nào | Đi vào nhánh dự phòng (ADR-008 mục 4), và trả lý do `no_valid_neighbors` |
| C6. Người học chưa có chiều nào được đánh giá | Không tìm láng giềng. Dùng công thức người học mới của tài liệu 04 mục 6.5 |
| C7. Người `is_synthetic` | Vẫn có vector, dùng cho mô phỏng |

### D. Phạm vi Mastery (`tests/test_cp2_mastery_scope.py`, gọi qua API)

1. Làm đúng L04-Q03 (`voicing.guide_tones`): lượt làm được ghi và vẫn được tính để hoàn thành bài, nhưng **không** tạo dòng mastery.
2. Làm đúng L04-Q01 (`progression.ii_v_i`): mastery tăng từ 0 lên 0,30.
3. `GET /me/mastery` chỉ trả kỹ năng MVP, kèm `group_code`.

## 6. Mục QA

### QA-L04-Q03: câu dựng G7 đầy đủ đang gắn `voicing.guide_tones`

- **Hiện trạng:** đề bài là "Dựng G7 đầy đủ; đây là bài chord inventory, chưa phải voicing". Đáp án là G–B–D–F. Câu này gắn `skill_id = voicing.guide_tones`.
- **Vấn đề học thuật:** câu này kiểm tra việc dựng hợp âm bảy, gần với `chord.seventh_build` hơn là guide tones. Chính đề bài cũng ghi "chưa phải voicing".
- **Ảnh hưởng hiện tại:** không ảnh hưởng tới Mastery, vì `voicing.guide_tones` là `post_mvp`. Có ảnh hưởng nếu sau này kỹ năng voicing được đưa vào MVP, hoặc khi thống kê theo kỹ năng.
- **Không làm:** không đổi `skill_id`, `ExerciseVersion` hay lịch sử bài làm.
- **Hướng để Astra và nhóm cân nhắc:** (1) đổi kỹ năng của câu sang `chord.seventh_build`, bằng phiên bản mới theo ADR-006; hoặc (2) giữ nguyên kỹ năng và sửa đề để thật sự kiểm tra guide tones. Cách nào cũng phải qua ticket Astra.

## 7. Còn chờ Thắng

1. Tên 4 nhóm 11–14.
2. Chuyển `scale.parallel_minor` sang `post_mvp`, nhóm 11.
3. Duyệt kế hoạch thử ngưỡng và phương án dự phòng trong ADR-008 mục 4. Ngưỡng chỉ chốt sau khi có kết quả thử.
