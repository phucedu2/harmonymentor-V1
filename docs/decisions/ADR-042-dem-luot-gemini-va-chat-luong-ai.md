# ADR-042: Đếm đúng lượt Gemini, xử lý 429 theo phút, bảng chất lượng AI soạn bài

- Trạng thái: Đề xuất (Phúc yêu cầu 28/11/2026 khi ôn bảo vệ; chờ nhóm duyệt PR)
- Liên quan: ADR-033 mục V5 (bộ đếm chung), ADR-028/029 (AI soạn bài), ADR-041

## Bối cảnh

Khi soạn câu hỏi ôn bảo vệ (tài liệu "Ôn bảo vệ: AI soạn bài trong Admin"), nhóm thấy ba điểm hội đồng dễ bắt:

1. **Số trên màn hình thấp hơn số Google tính.** AI Studio báo 507/500 lượt/ngày của Flash Lite trong khi app còn báo dư.
   Nguyên nhân: soạn bài ghi 1 lượt trước mỗi lần `generate`, nhưng `GeminiProvider.generate` có thể gọi HTTP 2 lần
   (mô hình chính lỗi 429/503/hết giờ → mô hình dự phòng). Tutor đếm mỗi tin nhắn là 1 lượt dù vòng soạn lại gọi 2 lần
   (tối đa 4 lần HTTP).
2. **429 theo phút bị coi là hết lượt ngày.** Gói miễn phí: Flash Lite 15 lượt/phút, 500 lượt/ngày; mô hình dự phòng
   3.6 Flash chỉ 5 lượt/phút, 20 lượt/ngày. Việc nền soạn tài liệu dài gọi liên tục, chạm 15/phút, Gemini trả 429. App
   chuyển ngay sang mô hình dự phòng (đốt lượt hiếm), rồi tạm dừng việc với lý do `quota` ("đợi sau 15:00").
3. **Không có số đo chất lượng thật.** Bộ 41 ca chỉ kiểm bộ lọc, Gemini thật mới chạy 1 tài liệu. Dữ liệu để đo (câu
   bị loại, Engine sửa, người sửa) có trong bản nháp nhưng không hiển thị, và một phần mất khi người duyệt lưu bản sửa.

## Quyết định

### 1. Đếm mọi lần gọi HTTP thật
- `LLMUnavailable` mang `attempts` (số lần gọi HTTP đã tốn) và `scope` (`minute` | `day` | None, đọc từ tên hạn mức
  trong lỗi 429, ví dụ `GenerateRequestsPerDayPerProjectPerModel-FreeTier`). `LLMResult.attempts` đã có từ trước.
- Soạn bài (`ai_service.call_json`): vẫn ghi 1 lượt **trước** khi gọi (lượt đã tính dù lỗi), sau đó ghi thêm
  `attempts − 1` lượt (`what = "<việc>:retry"`), cả khi thành công lẫn khi lỗi.
- Tutor: mỗi yêu cầu (`handle_message`, `explain_attempt`) bọc provider trong `CallCounter`; tin nhắn trả lời lưu
  `tool_calls.gemini_http`. `budget.used("tutor")` cộng `gemini_http`; tin cũ không có trường này vẫn tính 1 như trước.
- Hạn mức **mỗi học sinh** (`AI_DAILY_QUOTA`) giữ nguyên: đếm theo **lượt hỏi**, vì học sinh không biết và không nên
  bị trừ vì vòng soạn lại của hệ thống.
- Giới hạn còn lại: `budget.require` kiểm trước lần gọi, nên một lần `generate` có thể vượt phần soạn bài thêm tối đa 2
  lượt (chính + dự phòng, hoặc 2 lần cùng mô hình sau 429). Vì vậy khuyên đặt `GEMINI_DAILY_BUDGET` ≤ 450 khi trần thật 500.

### 2. Soạn bài giãn lượt gọi và chờ khi 429 theo phút
- `get_provider(cfg, authoring=True)` (chỉ provider của Admin) bật `min_interval_s = 4,5` (≤ 13,3 lượt/phút, dưới 15)
  và `rate_wait_s = 30`. Mốc thời gian gọi gần nhất dùng chung trong tiến trình theo mô hình.
- Gặp 429 không phải theo ngày: chờ 30 giây, gọi lại **cùng mô hình** một lần; vẫn 429 thì báo `rate_limited/minute`,
  **không** chuyển mô hình dự phòng. 429 theo ngày thì chuyển mô hình dự phòng như cũ (hạn mức tính theo mô hình).
- Việc nền (`ai_job.run_job`): nhận `rate_limited/minute` thì chờ thêm 60 giây rồi làm lại phần đó đúng 1 lần; lần hai
  vẫn bị thì tạm dừng với lý do mới `rate_minute`. `rate_limited/day` vẫn tạm dừng `quota`.
- Tutor giữ nguyên (không chờ, chuyển dự phòng ngay) vì học sinh đang ngồi chờ và hết giờ là 8 giây.
- Lỗi khi soạn một bản nháp (không qua việc nền) trả mã riêng: `AI_RATE_MINUTE` ("đợi khoảng 1 phút"), `AI_RATE_DAY`
  ("sau 15:00 giờ Việt Nam"), `AI_UNAVAILABLE` như cũ.

### 3. Bảng chất lượng AI theo phiên bản prompt
- Lúc soạn (bản nháp đơn, từng phần của việc nền, "soạn thêm câu"), chụp `content.ai_stats` = {câu AI giữ, câu bị loại
  (Engine hoặc trùng), câu Engine sửa đáp án, câu cần duyệt}. `update_draft` giữ nguyên số chụp này.
- `GET /api/v1/admin/ai/quality` gộp theo `prompt_version`: số bản nháp, đã xuất bản, bị từ chối, các tỉ lệ
  "qua Engine", "Engine sửa đáp án", "người sửa" (cờ `edited`), "người bỏ" (số chụp − số câu hiện tại), mô hình đã dùng.
  Bản nháp trước ADR-042 không có số chụp: tính trên bản hiện tại và đếm riêng ở `without_snapshot`.
- Tab AI soạn bài có mục thu gọn "Chất lượng AI soạn bài", chỉ tải khi mở.

## Hệ quả

- Số "còn … lượt" trên Admin giờ gần với AI Studio hơn (vẫn có thể lệch do các nơi gọi Gemini khác: nhúng câu hỏi và
  chấm câu tự luận mở không đi qua bộ đếm này, vì dùng hạn mức riêng hoặc mô hình nhúng có trần 1000/ngày).
- Việc nền chậm hơn: tối thiểu 4,5 giây giữa hai lần gọi. Một phần thường 1–3 lần gọi, nên thêm vài giây mỗi phần.
- Số đo chất lượng dùng được khi bảo vệ: "trên N bản nháp thật, X% câu AI qua Engine, Engine sửa Y%, người duyệt sửa Z%".
- Không đổi Music Engine, không đổi lược đồ CSDL (số chụp nằm trong cột JSON `content` đã có).

## Kiểm chứng

`backend/tests/test_adr042_dem_luot_gemini.py` (21 test): client Gemini giả kiểm số lần gọi khi chuyển mô hình dự
phòng, 429 theo phút/ngày, giãn cách; `call_json` ghi đủ lượt; Tutor ghi `gemini_http`; việc nền chờ rồi làm tiếp hoặc dừng
`rate_minute`; bảng chất lượng sau khi người duyệt bỏ và sửa câu; học sinh gọi API bảng → 403.
