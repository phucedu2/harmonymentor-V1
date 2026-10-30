# CP2 · Ánh xạ kỹ năng → mã SRS → nhóm KNN

Trạng thái: **DRAFT**, đi cùng [ADR-008](decisions/ADR-008-vector-14-nhom.md) bản 4. Bảng ánh xạ đã có đủ quyết định của Thắng (30/10). Chưa có code. PR-4, PR-5, PR-7 và PR-8 chưa được làm. Hợp đồng test nằm ở [`CP2_HOP_DONG_TEST.md`](CP2_HOP_DONG_TEST.md).

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
| 20 | `scale.parallel_minor` | L06 | post_mvp | 11 `chromatic_harmony` | 0 | Không | Thắng chốt 30/10 (ADR-003 cũ xếp vào `minor_scales`) |
| 21 | `harmony.modal_interchange.identify` | L06 | post_mvp | 11 `chromatic_harmony` | 0 | Không | |
| 22 | `harmony.modal_interchange.apply` | L06 | post_mvp | 11 `chromatic_harmony` | 0 | Không | |
| 23 | `tension.naming` | L07 | post_mvp | 14 `jazz_scales_tensions` | 0 | Không | |
| 24 | `mode.basic` | L07 | post_mvp | 14 `jazz_scales_tensions` | 0 | Không | |
| 25 | `chord_scale.basic` | L07 | post_mvp | 14 `jazz_scales_tensions` | 0 | Không | |
| 26 | `chord_scale.context` | L07 | post_mvp | 14 `jazz_scales_tensions` | 0 | Không | |

Tổng: 26 kỹ năng, 13 MVP, 13 `post_mvp`. Con số này chỉ để đối chiếu, test không khóa cứng (mục 4).

Quyết định của Thắng (30/10): `scale.parallel_minor` chuyển sang `post_mvp`, nhóm 11. Hai kỹ năng `voicing.guide_tones` và `voicing.voice_leading` của L04 giữ `post_mvp` và không cộng Mastery trước CP2. Các câu của hai kỹ năng này, trong đó có L04-Q03, vẫn được chấm và vẫn được dùng để xét hoàn thành bài.

Cột thứ ba của `SKILLS` trong `skill_graph.py` (`foundation`, `harmony`, `jazz_core`, `piano`, `chromatic_harmony`, `jazz`) là "domain" cũ. Nó **không phải** `group_code`.

## 3. 14 chiều của vector KNN

Thứ tự các chiều là cố định. Muốn đổi thứ tự hay tên chiều thì phải có ADR mới. Thắng đã chốt giữ nguyên tên 4 nhóm 11–14 (30/10).

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

## 5. Đặc tả test

Đã tách sang [`CP2_HOP_DONG_TEST.md`](CP2_HOP_DONG_TEST.md). Mỗi test có mã, PR phụ trách và file test: M (PR-4, mapping), S (PR-5, phạm vi Mastery), V và K (PR-7, vector và láng giềng), E (PR-8, thử nghiệm).

## 6. Mục QA

### QA-L04-Q03: câu dựng G7 đầy đủ đang gắn `voicing.guide_tones`

- **Hiện trạng:** đề bài là "Dựng G7 đầy đủ; đây là bài chord inventory, chưa phải voicing". Đáp án là G–B–D–F. Câu này gắn `skill_id = voicing.guide_tones`.
- **Vấn đề học thuật:** câu này kiểm tra việc dựng hợp âm bảy, gần với `chord.seventh_build` hơn là guide tones. Chính đề bài cũng ghi "chưa phải voicing".
- **Ảnh hưởng hiện tại:** không ảnh hưởng tới Mastery, vì `voicing.guide_tones` là `post_mvp`. Có ảnh hưởng nếu sau này kỹ năng voicing được đưa vào MVP, hoặc khi thống kê theo kỹ năng.
- **Không làm:** không đổi `skill_id`, `ExerciseVersion` hay lịch sử bài làm.
- **Hướng để Astra và nhóm cân nhắc:** (1) đổi kỹ năng của câu sang `chord.seventh_build`, bằng phiên bản mới theo ADR-006; hoặc (2) giữ nguyên kỹ năng và sửa đề để thật sự kiểm tra guide tones. Cách nào cũng phải qua ticket Astra.

## 7. Trạng thái quyết định

Bảng ánh xạ không còn điểm nào chờ quyết định. Thắng đã chốt ngày 30/10: tên 4 nhóm 11–14, `scale.parallel_minor`, kỹ năng voicing L04, và quy ước vector độ dài 0 (Q-5, phương án A).

Các điểm còn chờ (D-1..D-3, R-1..R-4) thuộc về Mastery và hệ gợi ý, không thuộc bảng ánh xạ. Xem ADR-008, mục "Cần quyết định".
