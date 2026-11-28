# HM-011 · Hợp đồng API: cách nhập bài làm do phiên bản câu hỏi quyết định

Trạng thái: **bản 2, chờ Thắng duyệt**. Chưa sửa code production. Draft PR #15 hiện chỉ có test, và CI đang đỏ có chủ đích.

| Bản | Ngày | Thay đổi |
|---|---|---|
| 1 | 30/10 | Đề xuất `allowed_input_methods` trong `grader_config`, 422 `INPUT_METHOD_NOT_ALLOWED` |
| 2 | 30/10 | Sửa theo góp ý Astra và quyết định của Phúc (A cả 8 câu). Xem mục 6 "Khác gì bản 1" |

## 1. Lỗi

`POST /api/v1/attempts` nhận `input_method` (`text | choice | piano`) từ client. Khi client gửi `piano`, máy chủ chuyển sang chấm `pitch_class_only` cho mọi câu `music_engine`, tức là bỏ qua phần chính tả. Ví dụ trên `main` 58a6f52: L01-Q04 (dựng D minor) chấm `D E# A` gửi kèm `piano` là **đúng**.

## 2. Quy tắc

### 2.1 Cách nhập nào hợp lệ

Máy chủ suy ra danh sách cách nhập hợp lệ từ **ảnh chụp phiên bản** mà client gửi (`exercise_version_id`). Máy chủ không đọc danh sách này từ bảng `exercises`, cũng không tin client.

| Phiên bản câu hỏi | `allowed_input_methods` |
|---|---|
| Có `options` (mcq, context, applied có lựa chọn) | `["choice"]` |
| Không có `options` | `["text"]` |
| `grader_config.allowed_input_methods` được khai báo | đúng danh sách đã khai báo |

Hiện chỉ L04-Q03 khai báo `["text", "piano"]`. Đây cũng là câu duy nhất có khối piano gửi bài (`L04-B07`). Theo quyết định A của Thắng, câu này được tính điểm khi làm bằng piano.

Vì quy tắc được suy ra từ dữ liệu sẵn có trong ảnh chụp, 47 câu còn lại **không phải tăng version**. Riêng L04-Q03 phải lên v2, vì đổi cách chấm của câu đã phát hành (ADR-006). Đề, đáp án và nguồn của L04-Q03 giữ nguyên.

### 2.2 `POST /api/v1/attempts`

Thứ tự kiểm tra:

1. Phiên bản tồn tại và là bản hiện hành. Nếu không, trả 409 `EXERCISE_VERSION_SUPERSEDED` như PR-3. Nhờ vậy client cũ còn giữ L04-Q03-v1 sẽ tải lại bài, thay vì nhận 422.
2. `input_method` bị bỏ trống thì máy chủ dùng phần tử đầu của `allowed_input_methods`. Câu có `options` thành `choice`, câu không có thành `text`.
3. `input_method` không nằm trong `allowed_input_methods` → **422 `INPUT_METHOD_NOT_ALLOWED`**.
4. Với `choice`: `answer` phải trùng **chính xác** một phần tử của `options`. Nếu không → **422 `ANSWER_NOT_IN_OPTIONS`**.
5. Với `piano`: `answer` là các tên cách nhau bởi khoảng trắng. Mỗi tên phải thuộc đúng 12 tên VirtualPiano gửi: `C C# D D# E F F# G G# A A# B`. Không có quãng tám, không lặp, không rỗng. Sai một trong các điều kiện đó → **422 `INVALID_PIANO_PAYLOAD`**.
6. Chấm bài. `piano` chấm `pitch_class_only`. `text` và `choice` chấm theo `grader_config` như hiện nay, mặc định là `strict_spelling`.

Mọi trường hợp 422 đều **không ghi `attempts`**, không đổi mastery và không tính vào "đã làm đúng" của bài.

Chỉ cần payload piano hợp lệ thì sai cao độ vẫn là một lượt làm **sai** hợp lệ: trả 200, `correct: false`, có ghi lượt. Ví dụ `G B D F#` cho G7.

### 2.3 `GET /api/v1/lessons/{id}`

`ExerciseOut` có thêm trường `allowed_input_methods: list[str]`, tính theo đúng quy tắc 2.1. Frontend chỉ hiện nút "Kiểm tra bằng piano" khi danh sách này có `piano`. Khi nhận 422, frontend hiện thông báo thay vì chấm.

## 3. Test (`backend/tests/test_hm011_input_method.py`, 22 ca)

| Nhóm | Ca | `main` hiện tại | Sau khi sửa |
|---|---|---|---|
| L01-Q04 gõ chữ | `D E# A` gửi kèm `text` hoặc không gửi → sai | đạt | đạt |
| L01-Q04 gửi `piano` | `D E# A` và `D F A` → 422 `INPUT_METHOD_NOT_ALLOWED`, 0 lượt | **đỏ** (200) | đạt |
| L01-Q04 gửi `choice` | → 422 `INPUT_METHOD_NOT_ALLOWED` | **đỏ** | đạt |
| L04-Q01 (mcq) | `choice` hoặc không gửi → chấm bình thường | đạt | đạt |
| L04-Q01 gửi `text` | → 422 `INPUT_METHOD_NOT_ALLOWED` | **đỏ** | đạt |
| L04-Q01 `choice` không thuộc options | `Dm7 G7 Cmaj7`, `dm7-g7-cmaj7`, `ii-V-I`, rỗng → 422 `ANSWER_NOT_IN_OPTIONS` | **đỏ** | đạt |
| API bài học | `allowed_input_methods`: L01-Q04 `["text"]`, L04-Q01 `["choice"]`, L04-Q03 `["text","piano"]` | **đỏ** | đạt |
| L04-Q03 version | khác `L04-Q03-v1` | **đỏ** | đạt |
| L04-Q03 piano hợp lệ | `G B D F`, `F D B G` → đúng | đạt | đạt |
| L04-Q03 piano sai cao độ | `G B D F#` → 200 sai, ghi 1 lượt | đạt | đạt |
| L04-Q03 piano sai định dạng | `G B D E#`, `G B D Gb`, `G4 B4 D5 F5`, `G B D F F`, `G B D H`, rỗng → 422 `INVALID_PIANO_PAYLOAD`, 0 lượt | **đỏ** | đạt |
| L04-Q03 gõ chữ | `G B D E#` gửi kèm `text` hoặc không gửi → sai (vẫn chấm chính tả) | đạt | đạt |

Trên `main`: 16 đỏ, 6 đạt.

## 4. Thay đổi code dự kiến (chỉ làm sau khi được duyệt)

| File | Thay đổi |
|---|---|
| `services/grading_service.py` | Thêm `allowed_input_methods(version)` và `validate_piano_payload(answer)`. `_grading_mode` chỉ trả `pitch_class_only` khi `input_method == "piano"` và cách nhập này đã được cho phép |
| `services/learning_service.py` | `submit_attempt` chạy các bước 2.2.2–2.2.5 trước khi chấm, ném `AttemptRejected(code)` |
| `api/attempts.py` | `AttemptRejected` → `AppError(422, code)` |
| `contracts/learning.py` | `AttemptIn.input_method: Literal[...] \| None = None`, thay cho mặc định `"text"`. `ExerciseOut.allowed_input_methods` |
| `api/lessons.py` | Điền `allowed_input_methods` |
| `content/curriculum_specs.py` | L04-Q03: `grader_config` thêm `"allowed_input_methods": ["text", "piano"]`, `version=2` |
| `frontend/src/api.ts`, `LessonRunner.tsx` | Đọc `allowed_input_methods`, ẩn nút piano khi không được phép, hiện lỗi 422 |
| `.github/workflows/ci.yml` | Nâng `--min-passed` |

Music Engine và schema CSDL **không đổi**. Không có migration.

### Test cũ bị ảnh hưởng

- `test_audit_nguoi_moi.py::test_piano_input_grades_pitch_only_but_typed_input_keeps_spelling` gọi thẳng `grade_payload(..., input_method="piano")` mà không khai quyền. Test này đang ghi lại chính hành vi lỗi. Mình sẽ sửa để test truyền `allowed_input_methods` vào `grader_config`.
- `test_audit_nguoi_moi.py::test_lesson_cannot_be_completed_by_guessing` gửi `"xx"` cho cả câu trắc nghiệm, và sau khi sửa các lượt đó sẽ nhận 422. Mục đích của test (đoán bừa không hoàn thành được bài) vẫn giữ nguyên, vì test không kiểm mã 200 cho các lượt này. Test sẽ vẫn đạt mà không cần sửa.
- Các test khác gửi đáp án đúng nguyên văn trong `options` hoặc chuỗi chữ cho câu không có `options`. Theo quy tắc 2.2.2, các test này vẫn đạt mà không cần sửa. Mình sẽ chạy toàn bộ bộ test để xác nhận.

## 5. Ảnh hưởng dữ liệu cũ

- Bảng `attempts` không lưu `input_method`, nên **không thể** biết lượt cũ nào đã được chấm theo cao độ. Lượt cũ giữ nguyên, không chấm lại.
- Việc lưu `attempts.input_method` để truy vết sẽ làm bằng **migration riêng sau này**, không gộp vào HM-011 khi chưa được duyệt.
- L04-Q03-v1 vẫn được giữ cho lịch sử. Seed lên v2 theo ADR-006. Nếu quên tăng version, `SeedConflictError` sẽ báo lỗi.

## 6. Khác gì bản 1

| Điểm | Bản 1 | Bản 2 |
|---|---|---|
| `text`, `choice` | Luôn hợp lệ với mọi câu | Hợp lệ theo `options` của phiên bản. Sai cách nhập → 422 |
| Thiếu `input_method` | Mặc định `text` | Dùng cách nhập mặc định của câu |
| `choice` không thuộc `options` | Chấm sai | 422 `ANSWER_NOT_IN_OPTIONS` |
| Payload piano | Không kiểm tra | Chỉ nhận 12 tên thăng của VirtualPiano. Sai → 422 `INVALID_PIANO_PAYLOAD` |
| Test L04-Q03 `piano` + `G B D E#` | Kỳ vọng đúng | Kỳ vọng 422. Thêm ca `G B D F` và `F D B G` là đúng |
| `attempts.input_method` | Câu hỏi mở | Migration riêng, làm sau |

## 7. Cần Thắng duyệt

1. Ba mã lỗi 422: `INPUT_METHOD_NOT_ALLOWED`, `ANSWER_NOT_IN_OPTIONS`, `INVALID_PIANO_PAYLOAD`.
2. Quy tắc suy ra cách nhập từ `options`, kèm phần khai báo riêng cho piano.
3. Đổi `AttemptIn.input_method` thành không bắt buộc, mặc định là `None`.
4. L04-Q03 lên v2 với `allowed_input_methods: ["text", "piano"]`.
