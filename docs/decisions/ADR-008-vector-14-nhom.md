# ADR-008 · Nhóm kỹ năng 14 chiều cho KNN, thay phần vector của ADR-003

Trạng thái: **Đề xuất, chưa có hiệu lực** (cập nhật 30/10/2026, bản 3). Astra đã chấp nhận hướng thiết kế. Thắng đã chốt ba điểm: tên 14 nhóm (mục 2), kỹ năng voicing L04 (mục 5) và `scale.parallel_minor` (mục 6). Còn **một câu chờ Thắng**: quy ước cho vector độ dài 0 (mục 3, Q-5). Bảng ánh xạ ở [`docs/CP2_ANH_XA_KY_NANG.md`](../CP2_ANH_XA_KY_NANG.md), hợp đồng test ở [`docs/CP2_HOP_DONG_TEST.md`](../CP2_HOP_DONG_TEST.md). Cả hai đều đang ở trạng thái DRAFT. Số 007 đã được PR #16 (logo) dùng.

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

- Vector được **tính khi cần** từ dữ liệu Mastery, bằng một hàm thuần. Không có bảng hay cột lưu vector, nên không có migration nào ngoài phạm vi PR-4. Script mô phỏng (PR-8) dùng chung hàm này.
- `value` của một chiều là trung bình mastery của các kỹ năng MVP **đã đánh giá** trong nhóm. Chiều chưa đánh giá có `assessed = false`. Khi đó `value = 0` chỉ để giữ đủ hình dạng mảng, không mang nghĩa mastery bằng 0.
- Độ tương đồng là cosine theo tài liệu 2.1, chỉ tính trên các chiều mà **cả hai** người cùng `assessed = true`.
- **Vector độ dài 0 (đề xuất của Astra, chờ Thắng, Q-5).** Trên các chiều chung, nếu vector của **ít nhất một** người có độ dài 0 thì cosine không xác định về mặt toán học. Khi đó cặp này được coi là **không đủ bằng chứng để so sánh**: không gán số nào cho độ tương đồng, loại cặp khỏi danh sách láng giềng và ghi lý do `zero_norm`. Nếu sau khi loại không còn láng giềng hợp lệ thì dùng phương án dự phòng ở mục 4. Quy ước này thay quy ước của bản 2 ("cả hai bằng 0 thì độ tương đồng là 1, một bên bằng 0 thì độ tương đồng là 0"). Lý do: gán 1 tạo ra láng giềng giả giữa những người cùng chưa làm đúng câu nào, còn gán 0 thì vẫn giữ một cặp không so sánh được trong danh sách xếp hạng.
- Với người học chưa có chiều nào được đánh giá: bỏ tầng cộng tác và dùng công thức người học mới của 04 mục 6.5, `score = 0,55 × content + 0,25 × (1 − mastery) + 0,20 × due`.
- Ở bước lọc theo luật và trong thành phần `(1 − mastery)`, kỹ năng chưa đánh giá vẫn được coi là mastery 0, tức là chưa thành thạo và chưa đủ làm tiên quyết. Sự phân biệt "chưa đánh giá" chỉ áp dụng cho KNN.

### 3b. Giới hạn đã biết: độ phủ kỹ năng trong một nhóm

`value` của một chiều là trung bình trên các kỹ năng **đã đánh giá**. Vì vậy hai người có thể cùng `value` ở một nhóm nhưng được đánh giá trên những kỹ năng khác nhau. Ví dụ ở nhóm `progressions`: người X chỉ làm `function.tonic` (0,30), người Y chỉ làm `progression.ii_v_i` (0,30). Trên chiều này hai người trông giống nhau, nhưng bằng chứng về năng lực thì không trùng nhau.

- **Không đổi** cách tổng hợp Mastery trong ADR này.
- Mỗi chiều chung được đo thêm **độ trùng kỹ năng**: Jaccard giữa hai tập kỹ năng đã đánh giá trong nhóm đó. Với X và Y ở trên, Jaccard = 0. Chỉ số này chỉ để báo cáo và phân tích, chưa dùng để lọc láng giềng.
- Thử nghiệm ở mục 4 báo cáo phân bố độ trùng của các cặp láng giềng được chọn. Nếu độ trùng thấp đi kèm với HitRate thấp thì nhóm sẽ xem xét một ADR bổ sung (chẳng hạn ngưỡng độ trùng tối thiểu, hoặc dùng vector theo kỹ năng). Không tự đổi trước khi có số liệu.

### 4. Ngưỡng số chiều chung, phương án dự phòng và đặc tả thử nghiệm: **chưa chốt**

Ngưỡng tối thiểu số chiều chung để hai người được coi là láng giềng chỉ được chốt sau khi có kết quả thử nghiệm. Ở PR-7, ngưỡng là một tham số trong cấu hình.

**Biến thử:**

| Mục | Nội dung |
|---|---|
| Ngưỡng | 2, 3 hoặc 4 chiều chung |
| Dự phòng (a) | Không có láng giềng hợp lệ thì dùng công thức người học mới (bỏ tầng cộng tác) |
| Dự phòng (b) | Hạ ngưỡng dần xuống 1 chiều chung. Nếu vẫn không có láng giềng thì dùng (a) |
| Tổng | 3 ngưỡng × 2 phương án dự phòng = 6 cấu hình, cộng 2 mốc so sánh |

**Dữ liệu và chống rò rỉ:**

- 2.000 người học mô phỏng của PR-8 (`is_synthetic = true`), trên 7 chiều có thể đánh giá. Seed cố định và được ghi lại.
- Với mỗi người được gợi ý, tách lịch sử **theo thời gian**: 80% lượt làm đầu dùng để huấn luyện, 20% lượt làm cuối được giữ lại. Thời điểm của lượt đầu tiên trong phần giữ lại gọi là **mốc cắt** của người đó.
- Mastery, vector và Leitner của người được gợi ý chỉ tính từ các lượt làm **trước mốc cắt**.
- Vector của mọi láng giềng cũng chỉ tính từ các lượt làm **trước mốc cắt của người được gợi ý**. Như vậy không có thông tin nào từ "tương lai" của người đó lọt vào qua láng giềng.
- Chính sách sinh hành vi của người mô phỏng **không được** gọi bộ gợi ý đang được đánh giá. Nếu không, kết quả sẽ tự xác nhận chính nó.

**Thế nào là "trúng":** một mục gợi ý trong top 5 được tính là trúng khi kỹ năng của nó được làm trong phần giữ lại, trong lúc mastery của kỹ năng đó tại mốc cắt còn dưới 0,60. HitRate@5 là tỷ lệ người có ít nhất 1 mục trúng. Precision@5 là số mục trúng chia cho 5.

**Mốc so sánh (không dùng lọc cộng tác):**

1. **Mốc chính:** công thức người học mới 0,55/0,25/0,20 áp dụng cho mọi người.
2. **Độ phổ biến:** gợi ý các kỹ năng được nhiều người làm nhất trong dữ liệu huấn luyện, sau khi lọc theo luật tiên quyết.

**Tiêu chí báo cáo** cho mỗi cấu hình và mốc so sánh: HitRate@5 và Precision@5 kèm khoảng tin cậy bootstrap 95%; tỷ lệ người có ít nhất 1 láng giềng hợp lệ; số láng giềng hợp lệ trung bình; tỷ lệ phải dùng dự phòng, tách theo lý do (`zero_norm`, `no_valid_neighbors`, chưa có chiều nào được đánh giá); phân bố độ trùng kỹ năng (mục 3b). Mọi chỉ số đều tách theo chân dung người học. Không đặt ngưỡng "đạt" cứng.

**Kiểm tra bắt buộc trong lần chạy:**

- Người có vector toàn 0 trên mọi chiều đã đánh giá không bao giờ xuất hiện trong danh sách láng giềng, và luôn đi vào nhánh dự phòng.
- Người không có láng giềng hợp lệ vẫn nhận đủ 5 gợi ý từ nhánh dự phòng.
- Hiệu năng: đo thời gian gợi ý cho một người bằng cách so trực tiếp với cả 2.000 người. Mục tiêu p95 ≤ 200 ms trên máy CI. Thời gian chạy toàn bộ đánh giá chỉ ghi lại để tham khảo.

**Cách chốt:** nhóm duyệt bảng kết quả (6 cấu hình + 2 mốc so sánh × tiêu chí, kèm lệnh chạy và seed) rồi mới ghi ngưỡng và phương án dự phòng vào một ADR bổ sung. Không chốt theo cảm tính. Nếu chưa có kết quả trước CP2, báo cáo CP2 ghi rõ cấu hình đang dùng chỉ là tạm thời.

### 5. Kỹ năng voicing của L04: Thắng đã chốt (30/10)

`voicing.guide_tones` và `voicing.voice_leading` giữ `post_mvp`, **không cộng Mastery trước CP2**. Các câu thuộc hai kỹ năng này, gồm cả L04-Q03, vẫn được chấm và vẫn tính để hoàn thành bài. Vấn đề học thuật của L04-Q03 được ghi riêng thành mục QA-L04-Q03 trong `CP2_ANH_XA_KY_NANG.md`. Không đổi kỹ năng, phiên bản hay lịch sử bài làm.

### 6. `scale.parallel_minor`: Thắng đã chốt (30/10)

Chuyển kỹ năng này sang `post_mvp`, nhóm 11 `chromatic_harmony`, vì nó không chứng minh được việc dựng âm giai thứ. Mã `minor_scales` vẫn được khai báo nhưng chưa có kỹ năng nào cho tới khi có kỹ năng âm giai thứ thật qua ticket Astra. Đây là thay đổi so với `PHASE_A_PLAN` mục 1.1, đã ghi phần bổ sung trong ADR-003.

## Phương án đã cân nhắc

| Phương án | Lý do không chọn |
|---|---|
| Giữ vector 10 chiều và ghi là bản rút gọn | Trái tài liệu chính thức |
| Coi chiều chưa đánh giá là 0 | Người chưa học bị coi giống người học kém, KNN sẽ ghép sai láng giềng |
| Điền chiều trống bằng trung bình nhóm | Tạo ra dữ liệu không có thật |
| Đổi sang 1 − trung bình độ lệch thay cho cosine | Lệch khỏi tài liệu 2.1 |
| Lưu vector thành bảng | Phải thêm migration ngoài PR-4. Tính khi cần là đủ nhanh với 2.000 người học |
| Cả hai vector bằng 0 thì độ tương đồng là 1 (bản 2) | Cosine không xác định. Hai người cùng chưa làm đúng câu nào bị coi là giống hệt nhau, tạo láng giềng giả |
| Một bên bằng 0 thì độ tương đồng là 0 (bản 2) | Vẫn là một con số gán cho đại lượng không xác định. Cặp này nằm cuối danh sách nhưng vẫn có thể được chọn khi thiếu láng giềng |
| Đổi ngay sang vector theo kỹ năng để xử lý mục 3b | Lệch khỏi tài liệu 2.1 khi chưa có số liệu cho thấy cần đổi |

## Hệ quả và phạm vi PR

| PR | Phạm vi | Test (mã trong `CP2_HOP_DONG_TEST.md`) |
|---|---|---|
| **#17** (bản này) | Chỉ tài liệu: ADR-008, bảng ánh xạ, hợp đồng test, phần bổ sung của ADR-003. Không code, không migration | Không có |
| **PR-4** (chưa làm) | Migration thêm `skills.srs_code` và `skills.group_code` kèm ràng buộc giá trị. Seed từ `skill_graph.py` | M1–M12 |
| **PR-5** (chưa làm) | Mastery EMA, chỉ cho kỹ năng MVP | S1–S4 |
| **PR-7** (chưa làm) | Hàm dựng vector, độ tương đồng, láng giềng, phương án dự phòng. Ngưỡng là tham số | V1–V7, K1–K10 |
| **PR-8** (chưa làm) | Mô phỏng 2.000 người và chạy thử nghiệm ở mục 4 | E1–E10 |

Không PR nào ở trên được triển khai hay merge khi chưa được duyệt. ADR-003: khi ADR-008 được duyệt, phần vector 10 chiều bị thay thế. Phần phạm vi MVP giữ nguyên, trừ `scale.parallel_minor` (mục 6).

## Câu hỏi còn chờ Thắng

- **Q-5**: Có đồng ý quy ước ở mục 3 không: trên các chiều chung, chỉ cần một bên có vector độ dài 0 thì cặp đó là "không đủ bằng chứng", bị loại khỏi danh sách láng giềng và chuyển sang dự phòng nếu không còn láng giềng nào? Đây là câu duy nhất chặn PR-7. PR-4 và PR-5 không phụ thuộc vào câu này.

Đã chốt ngày 30/10: Q-1 (kỹ năng voicing L04, mục 5), Q-2 (tên 4 nhóm 11–14, mục 2), Q-4 (`scale.parallel_minor`, mục 6). Đặc tả thử nghiệm ở mục 4 (Q-3 cũ) gửi kèm hợp đồng test để nhóm duyệt cùng. Ngưỡng chỉ chốt sau khi có kết quả.
