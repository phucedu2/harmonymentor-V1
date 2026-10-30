# ADR-008 · Nhóm kỹ năng 14 chiều cho KNN, thay phần vector của ADR-003

Trạng thái: **Đề xuất, chưa có hiệu lực** (cập nhật 30/10/2026, bản 2). Astra đã chấp nhận hướng thiết kế. Bản này còn chờ Thắng duyệt cuối cùng trước khi làm PR-4 và PR-5. Bảng ánh xạ chi tiết và đặc tả test nằm ở [`docs/CP2_ANH_XA_KY_NANG.md`](../CP2_ANH_XA_KY_NANG.md), cũng đang ở trạng thái DRAFT. Số 007 đã được PR #16 (logo) dùng.

## Bối cảnh

- **ADR-003** (chốt 18–19/10, theo SRS v1.3): cột `skills.srs_code` lấy một trong 10 mã SRS hoặc `post_mvp`. Vector mastery cho KNN có **10 chiều**.
- **Tài liệu 2.1**, chính thức từ 23/10: 01 dòng 228 và 04 mục 6.5 quy định mỗi người học là một **vector 14 chiều**, mỗi chiều là mastery trung bình của một nhóm `group_code`. 04 dòng 142 quy định bảng `skills` có cột `group_code` với 14 nhóm. Tài liệu không liệt kê tên các nhóm.
- Theo CLAUDE.md, khi tài liệu và code khác nhau thì làm theo tài liệu. Vì vậy phần "vector 10 chiều" của ADR-003 phải được thay. Phần "10 mã là phạm vi MVP" không mâu thuẫn với tài liệu 2.1 nên giữ nguyên.

## Quyết định đề xuất

### 1. Hai cột, hai vai trò

- `skills.srs_code` quyết định **phạm vi MVP**, giữ như ADR-003: chỉ kỹ năng có mã khác `post_mvp` mới được tính Mastery, gợi ý và lộ trình.
- `skills.group_code` gồm 14 nhóm, mỗi nhóm là **một chiều** của vector KNN.

Bảng ánh xạ, hai bất biến giữa hai cột và các quy tắc bao phủ (không thiếu, không trùng, không khóa cứng số lượng kỹ năng) ghi ở `CP2_ANH_XA_KY_NANG.md`, mục 1, 2 và 4.

### 2. 14 nhóm

Gồm 10 mã của ADR-003 cộng 4 nhóm theo nhánh: `chromatic_harmony`, `pop_harmony`, `jazz_voicing`, `jazz_scales_tensions`. Nguồn là bảng nháp ngày 26/10 mà Phúc đã chọn. Thứ tự chiều là cố định. Tên 4 nhóm 11–14 **chờ Thắng xác nhận**.

### 3. Vector `(value, assessed)`

- Vector được **tính khi cần** từ dữ liệu Mastery của PR-5, bằng một hàm thuần. Không có bảng hay cột lưu vector, nên không có migration nào ngoài phạm vi PR-4. Script mô phỏng (PR-8) dùng chung hàm này.
- `value` của một chiều là trung bình mastery của các kỹ năng MVP **đã đánh giá** trong nhóm. Chiều chưa đánh giá có `assessed = false`. Khi đó `value = 0` chỉ để giữ đủ hình dạng mảng, không mang nghĩa mastery bằng 0.
- Độ tương đồng là cosine, chỉ tính trên các chiều mà **cả hai** người cùng `assessed = true`. Nếu trên các chiều chung cả hai đều toàn 0 thì độ tương đồng là 1. Nếu chỉ một bên toàn 0 thì độ tương đồng là 0. Quy ước này giữ nguyên cosine theo tài liệu 2.1 và lấp chỗ cosine không xác định khi vector có độ dài 0.
- Với người học chưa có chiều nào được đánh giá: bỏ tầng cộng tác và dùng công thức người học mới của 04 mục 6.5, `score = 0,55 × content + 0,25 × (1 − mastery) + 0,20 × due`.
- Ở bước lọc theo luật và trong thành phần `(1 − mastery)`, kỹ năng chưa đánh giá vẫn được coi là mastery 0, tức là chưa thành thạo và chưa đủ làm tiên quyết. Sự phân biệt "chưa đánh giá" chỉ áp dụng cho KNN.

### 4. Ngưỡng số chiều chung và phương án dự phòng: **chưa chốt**

Ngưỡng tối thiểu số chiều chung để hai người được coi là láng giềng sẽ chỉ được chốt sau khi có kết quả thử nghiệm. Ở PR-5 và PR-7, ngưỡng là một tham số trong cấu hình.

**Kế hoạch thử** (chạy sau PR-8, khi đã có dữ liệu mô phỏng):

| Mục | Nội dung |
|---|---|
| Dữ liệu | 2.000 người học mô phỏng của PR-8, dùng cùng seed, trên 7 chiều có thể đánh giá. Giữ lại 20% lịch sử cuối của mỗi người để đánh giá |
| Biến thử | Ngưỡng 2, 3, 4 chiều chung × hai phương án dự phòng (a) và (b) bên dưới, tổng cộng 6 cấu hình |
| Dự phòng (a) | Không có láng giềng hợp lệ thì dùng công thức người học mới (bỏ tầng cộng tác) |
| Dự phòng (b) | Hạ ngưỡng dần xuống 1 chiều chung. Nếu vẫn không có láng giềng thì dùng (a) |
| Tiêu chí | HitRate@5 và Precision@5 trên phần giữ lại; tỷ lệ người học có ít nhất 1 láng giềng hợp lệ; số láng giềng hợp lệ trung bình; tỷ lệ phải dùng dự phòng |
| Báo cáo | Một bảng 6 cấu hình × tiêu chí, có tách theo chân dung người học, kèm lệnh chạy và seed |
| Cách chốt | Nhóm duyệt bảng rồi mới ghi ngưỡng và phương án dự phòng vào một ADR bổ sung. Không chốt theo cảm tính |

Nếu chưa có kết quả trước CP2, báo cáo CP2 ghi rõ cấu hình đang dùng chỉ là tạm thời.

### 5. Kỹ năng voicing của L04: Thắng đã chốt

`voicing.guide_tones` và `voicing.voice_leading` giữ `post_mvp`, **không cộng Mastery trước CP2**. Các câu thuộc hai kỹ năng này, gồm cả L04-Q03, vẫn được chấm và vẫn tính để hoàn thành bài. Vấn đề học thuật của L04-Q03 được ghi riêng thành mục QA-L04-Q03 trong `CP2_ANH_XA_KY_NANG.md`. Không đổi kỹ năng, phiên bản hay lịch sử bài làm.

### 6. `scale.parallel_minor`: chờ Thắng xác nhận

Đề xuất chuyển kỹ năng này sang `post_mvp`, nhóm 11, vì nó không chứng minh được việc dựng âm giai thứ. Mã `minor_scales` vẫn được khai báo nhưng chưa có kỹ năng nào cho tới khi có kỹ năng âm giai thứ thật qua ticket Astra. Đây là thay đổi so với `PHASE_A_PLAN` mục 1.1.

## Phương án đã cân nhắc

| Phương án | Lý do không chọn |
|---|---|
| Giữ vector 10 chiều và ghi là bản rút gọn | Trái tài liệu chính thức |
| Coi chiều chưa đánh giá là 0 | Người chưa học bị coi giống người học kém, KNN sẽ ghép sai láng giềng |
| Điền chiều trống bằng trung bình nhóm | Tạo ra dữ liệu không có thật |
| Đổi sang 1 − trung bình độ lệch thay cho cosine | Lệch khỏi tài liệu 2.1. Quy ước cho vector độ dài 0 đã đủ để xử lý trường hợp cosine không xác định |
| Lưu vector thành bảng | Phải thêm migration ngoài PR-4. Tính khi cần là đủ nhanh với 2.000 người học |

## Hệ quả

- **PR-4** (chưa làm): thêm `skills.srs_code` và `skills.group_code` kèm ràng buộc giá trị. Seed từ `skill_graph.py`. Test theo mục 4 và 5A của file ánh xạ.
- **PR-5** (chưa làm): hàm thuần dựng vector, test theo mục 5B và 5D.
- **PR-7** (chưa làm): độ tương đồng, láng giềng và phương án dự phòng, test theo mục 5C. Ngưỡng là tham số.
- **PR-8** (chưa làm): mô phỏng và chạy kế hoạch thử ở mục 4.
- **ADR-003**: khi ADR-008 được duyệt, phần vector 10 chiều bị thay thế. Phần phạm vi MVP giữ nguyên, trừ thay đổi `scale.parallel_minor` nếu Thắng xác nhận.

## Câu hỏi còn chờ Thắng

- **Q-2**: Tên 4 nhóm 11–14.
- **Q-3**: Có duyệt kế hoạch thử ngưỡng 2/3/4 cùng hai phương án dự phòng (a) và (b) ở mục 4 không?
- **Q-4**: Có chuyển `scale.parallel_minor` sang `post_mvp`, nhóm 11 không?

Q-1 (kỹ năng voicing L04) đã được Thắng chốt ngày 30/10, xem mục 5.
