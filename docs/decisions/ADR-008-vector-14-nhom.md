# ADR-008 · Nhóm kỹ năng 14 chiều cho KNN, thay phần vector của ADR-003

Trạng thái: **Đề xuất 30/10/2026, chưa có hiệu lực.** Bản này cần Thắng và nhóm duyệt rồi mới làm PR-4 hoặc PR-5. Phúc đã chốt hướng đi (các phương án A ngày 30/10), còn Astra yêu cầu xử lý mâu thuẫn này bằng một quyết định chính thức. Bảng ánh xạ chi tiết vẫn ở trạng thái **DRAFT**.

## Bối cảnh

- **ADR-003** (chốt 18–19/10, theo SRS v1.3) quy định:
  - Cột `skills.srs_code` lấy một trong 10 mã SRS hoặc `post_mvp`.
  - Vector mastery cho KNN có **10 chiều**.
- **Tài liệu 2.1**, bộ tài liệu chính thức từ 23/10:
  - 01 dòng 228 và 04 mục 6.5: mỗi người học là **vector 14 chiều**, mỗi chiều là mastery trung bình của một nhóm `group_code`.
  - 04 dòng 142: bảng `skills` có cột `group_code` với 14 nhóm.
  - Tài liệu 2.1 **không liệt kê** tên 14 nhóm.
- Theo CLAUDE.md, khi tài liệu và code mâu thuẫn thì tài liệu thắng. Vì vậy phần "vector 10 chiều" của ADR-003 phải được thay. Phần "10 mã là phạm vi MVP" thì không mâu thuẫn với tài liệu 2.1 nên được giữ.
- Kiểm tra trên `main` 58a6f52 cho thấy: có 26 kỹ năng, 4 bài đang chạy (L01–L04), và chỉ 13 kỹ năng có câu hỏi chạy được.

## Quyết định đề xuất

### 1. Hai cột, hai vai trò

| Cột | Giá trị | Vai trò |
|---|---|---|
| `skills.srs_code` | 10 mã ADR-003 hoặc `post_mvp` | **Phạm vi MVP**: chỉ kỹ năng có mã khác `post_mvp` mới được tính Mastery, gợi ý và lộ trình. Giữ nguyên như ADR-003 |
| `skills.group_code` | 14 mã bên dưới | **Chiều của vector KNN**, theo tài liệu 2.1 |

Hai cột phải thỏa hai bất biến:
- Nếu `srs_code` khác `post_mvp` thì `group_code` bằng `srs_code`.
- `group_code` thuộc nhóm 11–14 khi và chỉ khi `srs_code` là `post_mvp`.

### 2. 14 nhóm, thứ tự cố định

Danh sách lấy từ bảng nháp ngày 26/10 mà Phúc đã chọn (1A): 10 mã của ADR-003 cộng 4 nhóm theo nhánh.

| Chiều | `group_code` | Kỹ năng hiện có (đề xuất) |
|---|---|---|
| 1 | `note_names` | chưa có |
| 2 | `accidentals` | `pitch.spelling` |
| 3 | `intervals` | `interval.naming` |
| 4 | `major_scales` | `scale.major` |
| 5 | `minor_scales` | **chưa có** (xem mục 3) |
| 6 | `triads` | `chord.triad_formula`, `chord.triad_build` |
| 7 | `seventh_chords` | `chord.seventh_quality`, `chord.seventh_build` |
| 8 | `diatonic_chords` | `roman.major_seventh` |
| 9 | `progressions` | `function.tonic`, `function.predominant`, `function.dominant`, `function.progression`, `progression.ii_v_i` |
| 10 | `rhythm_basics` | chưa có |
| 11 | `chromatic_harmony` | `harmony.secondary_dominant.*` (3), `harmony.modal_interchange.*` (2), `scale.parallel_minor` |
| 12 | `pop_harmony` | chưa có |
| 13 | `jazz_voicing` | `voicing.guide_tones`, `voicing.voice_leading`, `voicing.shell` |
| 14 | `jazz_scales_tensions` | `tension.naming`, `mode.basic`, `chord_scale.basic`, `chord_scale.context` |

Muốn đổi thứ tự hay tên nhóm thì phải có ADR mới, vì dữ liệu mô phỏng và các vector đã lưu phụ thuộc vào thứ tự này.

### 3. `scale.parallel_minor` không đại diện cho `minor_scales`

Kỹ năng này chỉ dạy quan hệ giữa giọng trưởng và giọng thứ cùng tên, dùng làm nền cho modal interchange ở L06. Nó không chứng minh người học dựng được âm giai thứ. Vì vậy:
- Đổi `scale.parallel_minor` sang `srs_code = post_mvp`, nhóm 11 `chromatic_harmony`. Đây là thay đổi so với bảng ánh xạ trong `PHASE_A_PLAN` mục 1.1.
- Mã `minor_scales` vẫn được khai báo nhưng **chưa có kỹ năng**. Chiều 5 luôn ở trạng thái "chưa đánh giá" cho tới khi có kỹ năng âm giai thứ thật, ví dụ `scale.natural_minor`. Kỹ năng đó phải đi qua ticket Astra và Đạt duyệt.

### 4. "Chưa đánh giá" khác "mastery bằng 0"

- **Kỹ năng đã đánh giá**: có ít nhất một sự kiện mastery được tính, tức là một lượt làm trong bài học hoặc trong bài kiểm tra đầu vào. Lượt `is_test` không tính.
- **Nhóm đã đánh giá**: có ít nhất một kỹ năng MVP đã đánh giá.
- **Giá trị một chiều** là trung bình mastery của các kỹ năng MVP **đã đánh giá** trong nhóm. Kỹ năng chưa đánh giá không bị tính là 0.
- Vector lưu thành hai mảng 14 phần tử là `value` và `assessed`. Chiều chưa đánh giá có `value = 0` và `assessed = false`, chỉ để đủ hình dạng mảng.
- **KNN**: chỉ tính cosine trên những chiều mà **cả hai** người học cùng `assessed = true`.
  - Hai người có ít hơn **2** chiều chung đã đánh giá thì không được coi là láng giềng của nhau.
  - Nếu tìm được ít hơn 10 láng giềng hợp lệ thì dùng số láng giềng tìm được.
  - Nếu không có láng giềng nào thì xử lý như người học mới (gạch dưới đây).
- **Người học mới** là người chưa có nhóm nào được đánh giá. Theo 04 mục 6.5, với người này hệ thống bỏ tầng cộng tác và dùng công thức `score = 0,55 × content + 0,25 × (1 − mastery) + 0,20 × due`.
- Ở bước lọc theo luật (04 mục 6.5 bước 1) và ở thành phần `(1 − mastery)`, kỹ năng chưa đánh giá vẫn được coi là mastery 0. Nghĩa là kỹ năng đó chưa thành thạo, và chưa đủ điều kiện làm tiên quyết. Sự phân biệt ở mục này chỉ áp dụng cho vector KNN.

### 5. Kỹ năng voicing của L04: chưa quyết

Theo ADR-003, `voicing.guide_tones` và `voicing.voice_leading` là `post_mvp`. Hai kỹ năng này có 4 câu đang chạy ở L04, nên giữ nguyên `post_mvp` nghĩa là chúng không có mastery và không bao giờ được gợi ý. **ADR này không đổi điều đó.** Việc có đưa chúng vào phạm vi MVP hay không cần Thắng quyết định riêng (câu hỏi Q-1 bên dưới).

## Phương án đã cân nhắc

| Phương án | Lý do không chọn |
|---|---|
| Giữ vector 10 chiều, ghi chú là rút gọn so với tài liệu 2.1 | Trái tài liệu chính thức, và báo cáo CP2 sẽ phải giải thích chỗ lệch |
| Cho chiều chưa đánh giá bằng 0 | Người chưa học bị coi giống người học kém, nên KNN ghép sai láng giềng (Astra 30/10) |
| Điền chiều trống bằng trung bình nhóm | Tạo ra dữ liệu không có thật và làm mờ khác biệt giữa người học |
| Ghi `group_code` vào bảng `skills` mà không có `srs_code` | Mất ranh giới phạm vi MVP mà ADR-003 đã chốt |

## Hệ quả

- **PR-4** (chưa làm):
  - Migration thêm `skills.srs_code` và `skills.group_code`, có ràng buộc giá trị hợp lệ.
  - Seed lấy dữ liệu từ `skill_graph.py`.
  - Test kiểm các điều kiện sau:
    - Mọi kỹ năng có đúng một `srs_code` hợp lệ và một `group_code` hợp lệ.
    - Hai bất biến ở mục 1 luôn đúng.
    - Đủ 10 mã SRS và 14 nhóm được khai báo. Mã chưa có kỹ năng được đánh dấu rõ là "chưa có".
    - Mọi tiên quyết của kỹ năng MVP cũng là MVP.
    - Đồ thị tiên quyết không có chu trình.
  - Test **không khóa cứng con số 26**. ADR-003 vẫn còn yêu cầu thêm `note_names`, `minor_scales`, `rhythm_basics`, và việc thêm các kỹ năng đó không được làm hỏng test.
- **PR-5** (chưa làm):
  - Hàm thuần dựng vector `(value, assessed)` từ các sự kiện mastery.
  - Test cho các trường hợp: người chưa học, người đã học một phần, kỹ năng `post_mvp` không ảnh hưởng vector, lượt `is_test` bị loại.
- **Với dữ liệu L01–L04 hiện tại**, chỉ chiều 2, 3, 4, 6, 7, 8, 9 có thể được đánh giá. Mô phỏng 2.000 người học (PR-8) chỉ sinh dữ liệu trên các chiều này, và báo cáo CP2 phải ghi rõ giới hạn đó.
- **ADR-003**: phần vector 10 chiều bị thay bởi ADR này khi được duyệt. Phần phạm vi MVP giữ nguyên, chỉ thêm thay đổi cho `scale.parallel_minor` (mục 3).

## Câu hỏi cần duyệt

- **Q-1 (Thắng)**: Loại `voicing.guide_tones` và `voicing.voice_leading` của L04 khỏi Mastery MVP, đúng như ADR-003 hiện tại, hay đưa vào phạm vi MVP? Nếu đưa vào thì cần thêm một mã SRS, hoặc cho phép nhóm 13 được tính trong MVP.
- **Q-2 (Thắng, Đạt)**: Giữ nguyên tên 4 nhóm 11–14 như bảng nháp ngày 26/10?
- **Q-3 (Thắng)**: Ngưỡng tối thiểu **2** chiều chung đã đánh giá để hai người được coi là láng giềng có hợp lý không? Với dữ liệu L01–L04, tối đa chỉ có 7 chiều.
