# HarmonyMentor — Bước 5: trạng thái sau phê duyệt HM6-01–04

**Ngày:** 2026-11-23  
**Quyết định đã nhận:** Người dùng xác nhận `HM6-01–04: Giữ, cho phép dùng nội bộ`.

## Đã ghi nhận

- HM6-01–HM6-04 đã được đánh dấu `reviewed_by_human: true`, `rights_cleared: true` và phạm vi `internal_training_only` trong artifact riêng.
- Đã tạo JSONL riêng:

<localFile name="examples.step6-HM6-01-04.internal.jsonl" path="F:\HarmonyMentor\harmonymentor-V1\data\hm_training\examples.step6-HM6-01-04.internal.jsonl" />

- SHA-256 JSONL: `a8ccfa6de78a3b862cc536453c11e312925688e1eed27187f002a668d3e7746a`.

## Kiểm định

- Schema riêng: đạt 4/4 mẫu train.
- Gộp kiểm tra với bộ nháp hiện có: **50 train / 2 dev / 2 test**, 28 group.
- Music Engine: đạt.
- So khớp prompt gần nhất dưới ngưỡng trùng lặp đã đặt; HM6-04 gần nhất 0.75 với một mẫu train, dưới ngưỡng 0.80.
- Tokenizer offline, giới hạn 1.024 token:
  - HM6-01: 497 token, assistant mask 66.
  - HM6-02: 506 token, assistant mask 71.
  - HM6-03: 480 token, assistant mask 61.
  - HM6-04: 540 token, assistant mask 87.
- Không cắt token.

## Cổng production hiện vẫn chưa đạt

Khi gộp cả bộ hiện có, preflight production vẫn chặn vì **46 mẫu train còn lại chưa có human review/rights clearance**. Chế độ `--allow-demo` chỉ được phép cho smoke test, không được dùng để coi dataset là production-ready.

Do đó:

- Đã đủ số lượng tối thiểu 50 mẫu train về mặt số học.
- Chỉ có 4 mẫu mới được duyệt nội bộ.
- Chưa chạy full training.
- Chưa chuyển dataset gộp sang production-ready.
- Chưa đánh dấu 34 mẫu dự phòng là được phép dùng.
- Không thay đổi dữ liệu nguồn cũ.
