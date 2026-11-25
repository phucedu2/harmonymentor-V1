# Chuẩn bị QLoRA — chưa chạy training

## Phạm vi đã làm

- Giữ model mặc định `unsloth/Qwen3-4B-Instruct-2507-unsloth-bnb-4bit`.
- Trainer không còn âm thầm bỏ cờ cấu hình không được phiên bản SFTConfig hỗ trợ. Chỉ đổi tên max_length -> max_seq_length khi phiên bản hỗ trợ tên cũ; còn lại dừng và báo lỗi.
- Trước train: kiểm mask assistant từ tokenizer trên toàn bộ train/dev, không chấp nhận mask rỗng/toàn bộ prompt; đối chiếu prefix prompt. Không cắt chuỗi quá giới hạn: dừng để người vận hành xem lại.
- Sau khi SFTTrainer chuẩn bị dữ liệu: kiểm nhãn thực sự từ data_collator, token prompt/padding phải có label -100; chỉ token assistant được tính loss. Đây là kiểm tra fail-closed, có thể yêu cầu chọn chat template tương thích khi dùng tokenizer thật.
- Báo cáo training sẽ ghi phiên bản thư viện, revision model/tokenizer nếu lấy được, và số token qua preflight.
- Validator dùng TutorAnswer của runtime, kiểm cả claim khai báo lẫn claim nhận diện được trong lời trả lời. Claim nhận diện được phải được khai báo. Bộ quét không chứng minh mọi câu văn đều đúng hoặc đúng trọng tâm; người duyệt vẫn cần đọc.
- Prompt dùng chung đã nêu rõ hỗ trợ số La Mã trưởng/thứ tự nhiên.

## Dữ liệu nháp

`examples.context.draft.jsonl`: 16 mẫu, 8 nhóm, chia 12 train / 2 dev / 2 test; các nhóm không giao nhau giữa split. Đây chỉ là bộ thử quy trình, không đại diện đầy đủ các năng lực và không đủ để kết luận chất lượng.

Các trường reviewed_by_human và rights_cleared đều false. Dữ kiện định lượng lấy từ Music Engine; văn bản gợi ý do assistant soạn, chờ người duyệt. Không dùng dữ liệu người học thật. Bộ demo cũ được giữ nguyên.

Đọc `CONTEXT-DRAFT-REVIEW.md` để duyệt bằng ngôn ngữ thông thường: Giữ / Sửa / Loại và lý do. Không cần tự viết JSON. Sau khi có quyết định mới cập nhật metadata từng mẫu; không tự coi sự đồng ý quy trình là duyệt toàn bộ nội dung/quyền sử dụng.

Đã xuất bản thử tại `outputs/hm_dataset_context_draft` bằng `--allow-demo --verify-engine`. Manifest production_ready vẫn false; engine_verified chỉ nói kiểm tra engine đã chạy trong phạm vi nhận diện, không phải đã duyệt lời giảng. Ngưỡng 50 mẫu train đã duyệt và kiểm engine cho production vẫn giữ nguyên; đây là ngưỡng kỹ thuật, không phải đủ chất lượng.

## Cấu hình thử được duyệt (chưa thực thi)

- 4-bit, rank/alpha 16/16, batch 1, gradient accumulation 8.
- Learning rate 1e-4; seed 20261116; max_steps 5; epochs 1.
- Giới hạn ban đầu 1024 token. Prompt dùng chung đầy đủ có thể vượt giới hạn này: CHƯA có tokenizer để đo. Nếu preflight báo quá dài, dừng và đề xuất điều chỉnh length hoặc thiết kế prompt chung; không tự cắt mất đáp án hoặc tăng VRAM budget.
- Dùng môi trường WSL training riêng sau khi được phép cài/tải; không dùng môi trường backend.

Lệnh dự kiến chạy từ thư mục gốc repo trong môi trường training đã sẵn sàng (KHÔNG ĐÃ CHẠY):

```sh
python -B scripts/ai/hm_training/train_qlora.py \
  --data-dir outputs/hm_dataset_context_draft \
  --output outputs/hm_qlora_context_smoke \
  --epochs 1 --max-seq-length 1024 --max-steps 5 \
  --learning-rate 1e-4 --seed 20261116 --allow-demo
```

5 optimizer steps chỉ kiểm pipeline; không kết luận chatbot tốt hơn. Chưa có provider local trong chatbot. Sau lượt smoke còn cần chứng minh tham số adapter thay đổi, lưu/nạp lại và đánh giá model gốc/adapter trên cùng tập độc lập.

## Kiểm thử đã chạy

- 31 test chuẩn bị dataset/training: đạt (mask/collator dùng đối tượng giả lập, không phải tokenizer/model thật).
- Chạy gộp với test Roman thứ tự nhiên và hồi quy fallback: 151 đạt.
- `git diff --check`: đạt.
- Không cài thư viện, tải model, chạy GPU/train, mở database, commit hoặc push.

Các test mock xác nhận logic chặn lỗi; chưa chứng minh tương thích với bộ phiên bản Unsloth/TRL/Qwen sẽ cài. Việc đó bắt buộc được kiểm lại bằng tokenizer và trainer thật trước bước cập nhật trọng số.
