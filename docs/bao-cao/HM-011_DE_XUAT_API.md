# HM-011 · Đề xuất hợp đồng API: quyền nhập bằng piano theo phiên bản câu hỏi

Trạng thái: **chờ Thắng duyệt**. Chưa sửa code production. Draft PR này chỉ có test, viết trước để CI đỏ có chủ đích (Phúc chốt phương án A ngày 30/10/2026).

## 1. Lỗi

`POST /api/v1/attempts` nhận `input_method` từ client (`text | choice | piano`). Khi giá trị là `piano`, `grading_service._grading_mode` chuyển sang `pitch_class_only` cho mọi câu `music_engine`, bất kể câu đó có khối piano hay không. Hậu quả: chỉ cần tự gửi `"input_method": "piano"` là chính tả không còn được chấm.

Tái hiện trên `main` 58a6f52:

```bash
curl -X POST /api/v1/attempts -H "Authorization: Bearer …" \
  -d '{"exercise_version_id": "L01-Q04-v4", "answer": "D E# A", "input_method": "piano"}'
# → 200, "correct": true   (gửi "text" → "correct": false)
```

`L01-Q04` (dựng D minor) là câu dạy chính tả, nên `D E# A` phải sai. Lượt sai này còn được tính là "đã làm đúng" để hoàn thành bài và cộng vào mastery.

## 2. Test viết trước (`backend/tests/test_hm011_input_method.py`)

| Test | Hiện tại | Sau khi sửa |
|---|---|---|
| `D E# A` trên L01-Q04 gửi `text` hoặc không gửi `input_method` thì sai | đạt | đạt |
| `D E# A` gửi `piano` trên L01-Q04 → 422 `INPUT_METHOD_NOT_ALLOWED` | **đỏ** (200, đúng) | đạt |
| Lượt bị từ chối không ghi `attempts` | **đỏ** (ghi 1 lượt) | đạt |
| Đáp án đúng `D F A` gửi `piano` vẫn bị từ chối, vì quyền do câu hỏi quyết định, không phụ thuộc đáp án | **đỏ** | đạt |
| `GET /lessons/{id}` trả `allowed_input_methods` cho từng câu: L01-Q04 không có `piano`, L04-Q03 có | **đỏ** (thiếu trường) | đạt |
| L04-Q03 (câu duy nhất có khối piano gửi bài) đã tăng version, chấm cao độ khi nhập piano (`G B D E#` đúng) nhưng gõ chữ thì vẫn chấm chính tả | **đỏ** | đạt |

## 3. Hợp đồng đề xuất

### 3.1 Lưu quyền ở đâu

Quyền được lưu trong `grader_config` của **ảnh chụp phiên bản** (`exercise_versions.grader_config`, cột JSON):

```json
{"kind": "build_chord", "symbol": "G7", "allowed_input_methods": ["text", "piano"]}
```

Lý do chọn chỗ này:
- Quyền nhập là một phần của "cách chấm", nên theo ADR-006 đổi quyền phải tăng `version`. Lượt làm cũ vẫn trỏ về đúng bản đã chấm chúng.
- Không cần migration: cột JSON đã có, và trigger bất biến của PR-3 đã bảo vệ ảnh chụp.
- Máy chủ đọc quyền từ chính phiên bản mà client gửi `exercise_version_id`, không đọc từ bảng `exercises` hay từ client.

Mặc định khi thiếu khóa này: chỉ nhập bằng chữ. `text` và `choice` luôn được nhận và luôn chấm chính tả, vì hai cách này không đổi cách chấm. Riêng `piano` là quyền đặc biệt và phải được khai báo.

### 3.2 `POST /api/v1/attempts`

| Trường hợp | Kết quả |
|---|---|
| `input_method` ∈ {`text`, `choice`} hoặc bỏ trống | Chấm như cũ, `grading_mode` lấy từ `grader_config` (mặc định `strict_spelling`) |
| `input_method = piano` và phiên bản có `piano` trong `allowed_input_methods` | Chấm `pitch_class_only` |
| `input_method = piano` nhưng phiên bản không cho phép | **422** `{"error": {"code": "INPUT_METHOD_NOT_ALLOWED", …}}`. Không ghi `attempts`, không đổi mastery |

Thứ tự kiểm tra là: phiên bản tồn tại và là bản hiện hành (409 `EXERCISE_VERSION_SUPERSEDED` như PR-3), sau đó mới kiểm quyền nhập. Nhờ vậy client cũ đang giữ L04-Q03-v1 sẽ nhận 409 và tải lại bài, không nhận 422.

### 3.3 `GET /api/v1/lessons/{id}`

`ExerciseOut` có thêm `allowed_input_methods: list[str]`, luôn có `"text"`, và có `"piano"` khi phiên bản cho phép. Frontend chỉ hiện nút "Kiểm tra bằng piano" khi danh sách có `piano`, và hiện thông báo khi nhận 422.

### 3.4 Thay đổi code dự kiến (sau khi duyệt)

| File | Thay đổi |
|---|---|
| `services/grading_service.py` | `_grading_mode` nhận `grader_config` + `input_method` và chỉ trả `pitch_class_only` khi `piano` ∈ `allowed_input_methods` |
| `services/learning_service.py` | `submit_attempt` kiểm quyền trước khi chấm, ném `InputMethodNotAllowed` |
| `api/attempts.py` | Đổi lỗi đó thành `AppError(422, "INPUT_METHOD_NOT_ALLOWED")` |
| `contracts/learning.py`, `api/lessons.py` | Thêm `allowed_input_methods` vào `ExerciseOut` |
| `content/curriculum_specs.py` | L04-Q03: thêm `"allowed_input_methods": ["text", "piano"]`, `version=2`. Đề, đáp án và nguồn giữ nguyên |
| `frontend/.../LessonRunner.tsx`, `api.ts` | Ẩn nút piano khi không được phép, xử lý 422 |
| `tests/test_audit_nguoi_moi.py::test_piano_input_grades_pitch_only_but_typed_input_keeps_spelling` | Test đơn vị này đang gọi `grade_payload` với `piano` mà không khai quyền, tức là ghi lại đúng hành vi lỗi. Sẽ sửa để truyền `allowed_input_methods` |

Music Engine và schema CSDL không đổi.

## 4. Ảnh hưởng dữ liệu cũ

- Bảng `attempts` không lưu `input_method`, nên **không xác định được** lượt cũ nào đã được chấm theo cao độ. Theo quyết định 30/10, lượt cũ giữ nguyên, không chấm lại.
- L04-Q03-v1 vẫn tồn tại để giữ lịch sử. Lượt làm cũ trỏ v1 không bị ảnh hưởng.
- Seed lên v2 cho L04-Q03 theo đúng quy trình ADR-006 (`SeedConflictError` sẽ báo nếu quên tăng version).

## 5. Câu hỏi cho Thắng

1. Đồng ý lưu quyền trong `grader_config` của phiên bản (đề xuất), hay muốn tách thành cột riêng `exercise_versions.allowed_input_methods` (phải có migration)?
2. Mã 422 `INPUT_METHOD_NOT_ALLOWED` có ổn không, hay dùng 403?
3. Có muốn thêm cột `attempts.input_method` (migration nhỏ) để lần sau truy vết được lượt nào đã chấm theo cao độ không? Không bắt buộc để sửa HM-011.
4. Việc L04-Q03 lên v2 chỉ đổi cách chấm, không đổi nhạc lý. Bước này có cần ticket Astra không, hay Thắng duyệt là đủ?
