# ADR-008 · Nhóm kỹ năng 14 chiều cho KNN, thay phần vector của ADR-003

Trạng thái: **Đề xuất, chưa có hiệu lực** (cập nhật 30/10/2026, bản 4). Thắng đã chốt bốn điểm: tên 14 nhóm (mục 2), quy ước vector độ dài 0 (mục 3), kỹ năng voicing L04 (mục 5) và `scale.parallel_minor` (mục 6). Các điểm còn phải xin quyết định nằm ở mục "Cần quyết định". Bảng ánh xạ ở [`docs/CP2_ANH_XA_KY_NANG.md`](../CP2_ANH_XA_KY_NANG.md), hợp đồng test ở [`docs/CP2_HOP_DONG_TEST.md`](../CP2_HOP_DONG_TEST.md). Cả hai đều đang ở trạng thái DRAFT. Số 007 đã được PR #16 (logo) dùng.

## Bối cảnh

- **ADR-003** (chốt 18–19/10, theo SRS v1.3): cột `skills.srs_code` lấy một trong 10 mã SRS hoặc `post_mvp`. Vector mastery cho KNN có **10 chiều**.
- **Tài liệu 2.1**, chính thức từ 23/10: 01 dòng 228 và 04 mục 6.5 quy định mỗi người học là một **vector 14 chiều**, mỗi chiều là mastery trung bình của một nhóm `group_code`. 04 dòng 142 quy định bảng `skills` có cột `group_code` với 14 nhóm. Tài liệu không liệt kê tên các nhóm.
- Theo CLAUDE.md, khi tài liệu và code khác nhau thì làm theo tài liệu. Vì vậy phần "vector 10 chiều" của ADR-003 phải được thay. Phần "10 mã là phạm vi MVP" không mâu thuẫn với tài liệu 2.1 nên giữ nguyên.

## Quyết định đề xuất

### 1. Hai cột, hai vai trò

- `skills.srs_code` quyết định **phạm vi MVP**, giữ như ADR-003: chỉ kỹ năng có mã khác `post_mvp` mới được tính Mastery, gợi ý và lộ trình.
- `skills.group_code` gồm 14 nhóm, mỗi nhóm là **một chiều** của vector KNN.

Bảng ánh xạ, hai bất biến giữa hai cột và các quy tắc bao phủ (không thiếu, không trùng, không khóa cứng số lượng kỹ năng) ghi ở `CP2_ANH_XA_KY_NANG.md`, mục 1, 2 và 4.

### 2. 14 nhóm: Thắng đã chốt (30/10)

Gồm 10 mã của ADR-003 cộng 4 nhóm theo nhánh: `chromatic_harmony`, `pop_harmony`, `jazz_voicing`, `jazz_scales_tensions`. Thắng giữ nguyên tên 4 nhóm 11–14. Thứ tự chiều là cố định. Muốn đổi tên hay thứ tự thì phải có ADR mới.

### 3. Vector `(value, assessed)` và độ tương đồng

- Vector được **tính khi cần** từ dữ liệu Mastery, bằng một hàm thuần. Không có bảng hay cột lưu vector. Script mô phỏng (PR-8) dùng chung hàm này.
- `value` của một chiều là trung bình mastery của các kỹ năng MVP **đã đánh giá** trong nhóm. Chiều chưa đánh giá có `assessed = false`. Khi đó `value = 0` chỉ để giữ đủ hình dạng mảng, không mang nghĩa mastery bằng 0.
- Độ tương đồng là cosine theo tài liệu 2.1, chỉ tính trên các chiều mà **cả hai** người cùng `assessed = true`.
- **Vector độ dài 0: Thắng đã chốt (30/10, Q-5 phương án A).** Trên các chiều chung, nếu vector của **ít nhất một** người có độ dài 0 thì cosine không xác định. Khi đó:
  - Không tính cosine và không gán độ tương đồng bằng 1 hay bằng 0.
  - Cặp đó không vào danh sách láng giềng hợp lệ. Lý do được ghi là `zero_norm`.
  - Nếu không còn láng giềng hợp lệ thì dùng phương án dự phòng (mục 4). Mastery hiện có của người học được giữ nguyên và vẫn dùng trong thành phần `(1 − mastery)`.
- Với người học chưa có chiều nào được đánh giá: bỏ tầng cộng tác và dùng công thức người học mới của 04 mục 6.5, `score = 0,55 × content + 0,25 × (1 − mastery) + 0,20 × due`.
- Ở bước lọc theo luật và trong thành phần `(1 − mastery)`, kỹ năng chưa đánh giá vẫn được coi là mastery 0, tức là chưa thành thạo và chưa đủ làm tiên quyết. Sự phân biệt "chưa đánh giá" chỉ áp dụng cho KNN.

### 3b. Giới hạn đã biết: độ phủ kỹ năng trong một nhóm

`value` của một chiều là trung bình trên các kỹ năng **đã đánh giá**, nên hai người có thể cùng `value` ở một nhóm nhưng được đánh giá trên những kỹ năng khác nhau. Ví dụ ở nhóm `progressions`: người X chỉ làm `function.tonic` (0,30), người Y chỉ làm `progression.ii_v_i` (0,30). Cosine thô trên chiều này bằng 1, nhưng bằng chứng về năng lực của hai người không trùng nhau.

- **Không đổi** cách tổng hợp Mastery trong ADR này.
- Mỗi chiều chung được đo thêm **độ trùng kỹ năng**: Jaccard giữa hai tập kỹ năng đã đánh giá trong nhóm. Với X và Y ở trên, Jaccard = 0. Chỉ số này chỉ để báo cáo, chưa dùng để lọc láng giềng.
- Nếu thử nghiệm cho thấy độ trùng thấp đi kèm kết quả kém thì nhóm xem xét một ADR bổ sung. Không tự đổi trước khi có số liệu.

### 4. Tầng cộng tác `cf` (04 mục 6.5, bước 3)

Ngày 28/10 nhóm đã chốt: `cf` là tỷ lệ láng giềng đạt từ 0,60. Bản này làm rõ các chi tiết (Phúc chọn 30/10, chờ Thắng duyệt như một quyết định học thuật, xem mục "Cần quyết định"):

- **Mốc thời gian:** mọi dữ liệu dùng để tính `cf` xảy ra **trước thời điểm gợi ý**. Khi chạy thật, mốc là lúc gọi API. Trong thử nghiệm, mốc là mốc cắt của người được gợi ý. Không có cửa sổ thời gian nào khác.
- **"Học tốt kỹ năng đó ở bước tiếp theo"** được hiểu là: tính đến mốc thời gian, láng giềng có mastery của kỹ năng đó **≥ 0,60** (ngưỡng "đủ để học tiếp").
- **Tử số:** số láng giềng hợp lệ đạt điều kiện trên.
- **Mẫu số:** số láng giềng hợp lệ thực có, **tối đa 10**. Láng giềng chưa từng làm kỹ năng đó vẫn nằm trong mẫu số và được tính là "chưa học tốt".
- **Không có láng giềng hợp lệ:** không tính `cf`, dùng phương án dự phòng.
- `cf` của một bài là trung bình `cf` trên các kỹ năng chưa thành thạo mà bài dạy, theo bước 6.

### 5. Ngưỡng số chiều chung, phương án dự phòng và đặc tả thử nghiệm

Ngưỡng tối thiểu số chiều chung (2, 3 hoặc 4) **chưa chốt**, sẽ chốt sau khi có kết quả thử nghiệm. Ở PR-7, ngưỡng là một tham số trong cấu hình.

**Phương án dự phòng:**

| Mục | Nội dung |
|---|---|
| Dự phòng (a) | Không có láng giềng hợp lệ thì dùng công thức người học mới (bỏ tầng cộng tác) |
| Dự phòng (b) | Hạ ngưỡng dần xuống 1 chiều chung. Nếu vẫn không có láng giềng thì dùng (a) |

**Các phương án so sánh**, theo Bảng 29 của 04 mục 8.4 (cách hiểu "chỉ luật" và "luật + nội dung" chờ Thắng xác nhận):

| Phương án | Cách xếp hạng |
|---|---|
| P1. Chỉ lọc theo luật | Các bài qua bước 1, xếp theo thứ tự bài trong chương trình |
| P2. Luật + nội dung | Công thức người học mới 0,55 / 0,25 / 0,20 |
| P3. Đủ 3 tầng | Công thức đầy đủ 0,35 / 0,25 / 0,20 / 0,20. Chạy 6 cấu hình: 3 ngưỡng × 2 phương án dự phòng |
| P0. Độ phổ biến (mốc phụ) | Các bài qua bước 1, xếp theo số người bắt đầu bài trong dữ liệu huấn luyện |

**Dữ liệu và chống rò rỉ:**

- 2.000 người học mô phỏng của PR-8 (`is_synthetic = true`), trên 7 chiều có thể đánh giá. Seed cố định và được ghi lại.
- Với mỗi người được gợi ý, tách lịch sử **theo thời gian**: 80% lượt làm đầu để huấn luyện, 20% lượt làm cuối giữ lại. Thời điểm của lượt đầu tiên trong phần giữ lại là **mốc cắt** của người đó.
- Mastery, vector, Leitner và tiến độ bài của người được gợi ý chỉ tính từ dữ liệu **trước mốc cắt**.
- Vector và `cf` của láng giềng cũng chỉ tính từ dữ liệu **trước mốc cắt của người được gợi ý**.
- Bộ sinh hành vi mô phỏng **không được** gọi bộ gợi ý đang được đánh giá (04 mục 6.5, "Cách sinh dữ liệu mô phỏng").

**Đơn vị đánh giá: bài** (Phúc chọn 30/10, chờ Thắng xác nhận).

- 04 mục 6.5 viết: "so với bài họ thực sự học tiếp". Bản 3 lại đo theo kỹ năng có mastery dưới 0,60. Hai cách này khác nhau ở hai điểm. Thứ nhất, hệ thống gợi ý **bài** chứ không gợi ý kỹ năng. Thứ hai, một bài dạy nhiều kỹ năng, nên đo theo kỹ năng sẽ tính trúng cả khi người học không mở bài được gợi ý.
- Để khớp SRS: một bài trong danh sách gợi ý được tính là **trúng** khi người học **bắt đầu** bài đó trong phần giữ lại (có lượt làm đầu tiên của bài, hoặc `lesson_progress` chuyển sang `started`), và trước mốc cắt họ chưa bắt đầu bài đó.
- Chỉ số theo kỹ năng của bản 3 được giữ lại như **chỉ số chẩn đoán**, không dùng để chọn cấu hình.

**Khi số bài đủ điều kiện ít hơn 5:**

- Hệ thống chỉ trả về số bài thực có. Không lặp bài, không bỏ qua tiên quyết, kèm lý do `few_eligible`. Danh sách rỗng vẫn hợp lệ. Bước 7 của 04 ("lấy 3–5 bài") được hiểu là **tối đa** 5 bài.
- Gọi `n` là độ dài danh sách thực trả về.
- **Precision@k chính** = số bài trúng trong top k ÷ min(k, n). Đây là cách tính phù hợp với việc SRS cho phép trả 3–5 bài.
- **Precision@k phụ** = số bài trúng trong top k ÷ k. Đây là cách chuẩn trong tài liệu truy hồi thông tin.
- **HitRate@k** = tỷ lệ người có ít nhất 1 bài trúng trong top k.
- Danh sách rỗng được tính là **trượt** khi tính HitRate và **bị loại** khỏi Precision chính. Số người nhận danh sách rỗng được báo cáo riêng.
- Ví dụ: 3 bài đủ điều kiện, gợi ý L02, L03, L04, người học bắt đầu L03. Kết quả: HitRate@5 = 1, Precision@5 chính = 1/3, Precision@5 phụ = 1/5.

**Bão hòa ở @5.** Ở bước 1, chỉ bài có kỹ năng MVP mới được gợi ý. Hiện chỉ có 4 bài như vậy (L01–L04). Danh sách gợi ý có tối đa 4 bài, nên HitRate@5 của mọi phương án gần như bằng HitRate của "gợi ý tất cả". Vì vậy báo cáo thêm:

- HitRate và Precision ở **@1** và **@3** (đã chọn ngày 28/10).
- **MRR**: trung bình của 1 ÷ thứ hạng của bài trúng đầu tiên, tính trong top 5. Nếu không trúng thì bằng 0.
- Báo cáo CP2 ghi rõ rằng với 4 bài, @5 gần như không phân biệt được các phương án.

**Tiêu chí báo cáo** cho mỗi phương án và cấu hình:

- HitRate, Precision chính và Precision phụ ở @1, @3, @5, cùng MRR, kèm khoảng tin cậy bootstrap 95%.
- Tỷ lệ người có ít nhất 1 láng giềng hợp lệ, và số láng giềng hợp lệ trung bình.
- Tỷ lệ phải dùng dự phòng, tách theo lý do: `zero_norm`, `no_valid_neighbors`, chưa có chiều nào được đánh giá.
- Tỷ lệ `few_eligible` và tỷ lệ danh sách rỗng.
- Phân bố độ trùng kỹ năng (mục 3b).
- Mọi chỉ số đều tách theo chân dung người học. Không đặt ngưỡng "đạt" cứng.

**Kiểm tra bắt buộc trong lần chạy:**

- Người có vector toàn 0 không bao giờ xuất hiện trong danh sách láng giềng.
- Người không có láng giềng hợp lệ vẫn nhận gợi ý từ nhánh dự phòng, theo đúng các quy tắc `few_eligible` ở trên.
- Hiệu năng: gợi ý cho một người, so với cả 2.000 người, đạt p95 ≤ 200 ms trên máy CI. Thời gian chạy toàn bộ chỉ ghi lại để tham khảo.

**Cách chốt:** nhóm duyệt bảng kết quả, kèm lệnh chạy và seed, rồi mới ghi ngưỡng và phương án dự phòng vào một ADR bổ sung. Nếu chưa có kết quả trước CP2, báo cáo CP2 ghi rõ cấu hình đang dùng chỉ là tạm thời.

### 6. Kỹ năng voicing của L04: Thắng đã chốt (30/10)

`voicing.guide_tones` và `voicing.voice_leading` giữ `post_mvp`, **không cộng Mastery trước CP2**. Các câu thuộc hai kỹ năng này, gồm cả L04-Q03, vẫn được chấm và vẫn tính để hoàn thành bài. Vấn đề học thuật của L04-Q03 được ghi ở mục QA-L04-Q03 trong `CP2_ANH_XA_KY_NANG.md`. Không đổi `skill_id`, phiên bản hay lịch sử bài làm.

### 7. `scale.parallel_minor`: Thắng đã chốt (30/10)

Chuyển kỹ năng này sang `post_mvp`, nhóm 11 `chromatic_harmony`, vì nó không chứng minh được việc dựng âm giai thứ. Mã `minor_scales` vẫn được khai báo nhưng chưa có kỹ năng nào cho tới khi có kỹ năng âm giai thứ thật qua ticket Astra. Thay đổi này đã được ghi ở phần bổ sung của ADR-003.

## Phương án đã cân nhắc

| Phương án | Lý do không chọn |
|---|---|
| Giữ vector 10 chiều và ghi là bản rút gọn | Trái tài liệu chính thức |
| Coi chiều chưa đánh giá là 0 | Người chưa học bị coi giống người học kém, KNN ghép sai láng giềng |
| Điền chiều trống bằng trung bình nhóm | Tạo ra dữ liệu không có thật |
| Đổi sang 1 − trung bình độ lệch thay cho cosine | Lệch khỏi tài liệu 2.1 |
| Lưu vector thành bảng | Thêm migration không cần thiết. Tính khi cần là đủ nhanh với 2.000 người |
| Cả hai vector bằng 0 thì độ tương đồng là 1 (bản 2) | Cosine không xác định, tạo láng giềng giả |
| Một bên bằng 0 thì độ tương đồng là 0 (bản 2) | Vẫn gán số cho một đại lượng không xác định |
| Đổi ngay sang vector theo kỹ năng để xử lý mục 3b | Lệch khỏi tài liệu 2.1 khi chưa có số liệu |
| Đánh giá theo kỹ năng (bản 3) | SRS đánh giá theo bài người học thực sự học tiếp |
| Luôn trả đủ 5 bài | Phải lặp bài hoặc bỏ qua tiên quyết khi có ít hơn 5 bài đủ điều kiện |
| Chỉ báo @5 | Với 4 bài, @5 bị bão hòa |

## Cần quyết định

Thắng đã chốt ngày 30/10: tên nhóm 11–14 (Q-2), `scale.parallel_minor` (Q-4), kỹ năng voicing L04 (Q-1), vector độ dài 0 (Q-5). Không hỏi lại các điểm này.

Các điểm dưới đây Phúc đã chọn ngày 30/10 và cần Thắng duyệt.

**A. Quyết định học thuật**

| Mã | Điểm cần quyết | Đề xuất | Chặn |
|---|---|---|---|
| D-1 | Đơn vị đánh giá | Bài: trúng khi người học bắt đầu bài trong phần giữ lại. Chỉ số theo kỹ năng chỉ để chẩn đoán | PR-8 |
| D-2 | Cách hiểu `cf` | Mục 4: mastery ≥ 0,60 tính đến mốc thời gian; mẫu số là số láng giềng hợp lệ thực có, tối đa 10; láng giềng chưa làm kỹ năng thì tính là chưa học tốt | PR-7 |
| D-3 | "Làm lại" trong EMA (04 mục 6.3) | Đúng sau khi đã có lượt sai trên cùng `exercise_id`, ở mọi phiên bản, thì kết quả bằng 0,5. Đúng lặp lại sau khi đã đúng thì không cộng thêm (chống cày điểm). Trường hợp "sau gợi ý" chờ có tính năng gợi ý cho câu bài tập (hợp đồng test mục S) | PR-5 |

**B. Diễn giải hoặc thay đổi yêu cầu SRS**

| Mã | Điểm cần quyết | Đề xuất | Chặn |
|---|---|---|---|
| R-1 | Bước 7 "lấy 3–5 bài" | Hiểu là tối đa 5 bài. Có ít bài đủ điều kiện hơn thì trả ít hơn, kèm lý do `few_eligible` | PR-7 |
| R-2 | Mẫu số Precision@5 | Chính: min(5, n). Phụ: 5. Danh sách rỗng bị loại khỏi Precision chính và được báo cáo riêng | PR-8 |
| R-3 | Bảng 29: cách hiểu "chỉ luật" và "luật + nội dung" | P1: xếp theo thứ tự chương trình. P2: công thức người học mới. P0 độ phổ biến là mốc phụ | PR-8 |
| R-4 | Chỉ số ngoài SRS | Thêm @1, @3 và MRR vì @5 bão hòa với 4 bài | PR-8 |

Ngưỡng số chiều chung (2/3/4) chưa phải là câu hỏi lúc này. Nó sẽ chốt sau khi có kết quả thử nghiệm.

## Hệ quả và phạm vi PR

| PR | Phạm vi | Test (mã trong `CP2_HOP_DONG_TEST.md`) |
|---|---|---|
| **#17** (bản này) | Chỉ tài liệu: ADR-008, bảng ánh xạ, hợp đồng test, phần bổ sung của ADR-003. Không code, không schema, không dữ liệu | Không có |
| **PR-4** (chưa làm) | Migration thêm `skills.srs_code`, `group_code`, `ready_threshold` (mặc định 0,6), `mastery_threshold` (mặc định 0,8), kèm ràng buộc giá trị. Seed từ `skill_graph.py` | M1–M13 |
| **PR-5** (chưa làm) | Bảng `mastery_states`, cột `attempts.is_test`, EMA chỉ cho kỹ năng MVP | S1–S14 |
| **PR-5b** (chưa làm) | Bài kiểm tra đầu vào, đặt mastery 0,65 | S15 |
| **PR-7** (chưa làm) | Vector, độ tương đồng, láng giềng, `cf`, phương án dự phòng, `few_eligible`. Ngưỡng là tham số | V1–V7, K1–K10, C1–C7, R1–R4 |
| **PR-8** (chưa làm) | Mô phỏng 2.000 người, chạy P0–P3 | E1–E12 |

`attempts.input_method` là một migration riêng, ngoài các PR trên (đã chốt cho HM-011). Không PR nào ở trên được triển khai hay merge khi chưa được duyệt. ADR-003: khi ADR-008 được duyệt, phần vector 10 chiều bị thay thế. Phần phạm vi MVP giữ nguyên, trừ `scale.parallel_minor` (mục 7).
