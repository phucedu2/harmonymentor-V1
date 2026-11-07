# ADR-018 · Fine-tune e5-small cho định tuyến AI Tutor

Trạng thái: **Đề xuất 07/11/2026**, chờ nhóm duyệt qua Draft PR GĐ2b (nhánh `ai-gop-y/gd2b-fine-tune`). Căn cứ: góp ý thầy G6, quyết định GĐ2 6A–9A (Phúc, 07/11/2026), báo cáo `docs/giai-doan/ai-gop-y/03_FINETUNE.md`.

## Bối cảnh

- Với e5-small gốc, điểm cosine bị nén.
  - Trên dev GĐ2, câu A trung bình 0,857 còn câu B/C trung bình 0,826. AUC tách hai nhóm chỉ 0,79.
  - Vì vậy không có ngưỡng nào đạt cả hai mục tiêu của ADR-017. Thêm luật cũng không sửa được.
- Thầy góp ý G6: nhóm nên tự fine-tune một mô hình mở.
- Nhóm không có GPU riêng. Gemini bản miễn phí không cho fine-tune.

## Quyết định

1. **Fine-tune `intfloat/multilingual-e5-small`**, cùng bản cố định 614241f, trên CPU, seed 20261107. Script: `scripts/ai/gop_y/finetune_e5.py`.
   - Đóng băng lớp nhúng từ, chỉ chỉnh 12 lớp transformer.
   - Hàm mất mát có hai phần:
     - InfoNCE để câu A/D chọn đúng đoạn.
     - Hinge có ngưỡng học được để điểm cao nhất của câu B/C/D/G nằm dưới điểm câu A.
   - Chỉ train trên `gd2/train.json`. Epoch được chọn trên `gd2/dev.json`: lỗi cân bằng thấp nhất, với điều kiện R@1 bộ chuẩn GĐ4 không thấp hơn bản gốc. Không đụng `test_tam.json`.
2. **Mô hình mang tên riêng** `multilingual-e5-small-hm-gd2b`, ghi trong `model_info.json`.
   - Router tra ngưỡng theo tên nên không dùng nhầm ngưỡng của bản gốc.
   - Ngưỡng cho cả hai bản do `hieu_chinh_nguong.py` chọn trên dev và ghi chung vào một file.
3. **Đổi mô hình chỉ bằng `LOCAL_EMBED_DIR`.** Mặc định vẫn là bản gốc cho tới khi Phúc quyết.
   - Lý do: trên test tạm, bản mới giảm mạnh lỗi trả lời sai nhưng tăng lỗi từ chối sai. CP3 ngày 10/11 cần ổn định.
4. **File mô hình 470 MB không vào git.**
   - Đề xuất đăng làm file đính kèm của GitHub Release trong repo nhóm, có SHA-256 (ghi trong `gd2b_model_info.json`).
   - Dockerfile sẽ tải từ đó. **Release chỉ tạo khi Phúc đồng ý** (quyết định 9A).

## Phương án đã cân nhắc

- **Chỉ train lại tầng 1.** Đã làm ở GĐ2, nhưng không đủ: lỗi nằm ở điểm truy xuất, không nằm ở nhãn câu.
- **Reranker cross-encoder.** Chính xác hơn nhưng mỗi câu phải chạy thêm một mô hình, ảnh Docker nặng hơn. Để lại nếu bản fine-tune vẫn chưa đủ.
- **Fine-tune LLM sinh trả lời.** Không có GPU; Gemini miễn phí không cho phép. Lỗi cần sửa nằm ở định tuyến, không ở câu chữ trả lời.
- **Train 3 epoch và lấy epoch cuối.** Epoch 3 làm R@1 tụt về 90% và lỗi cân bằng tăng, nên chọn theo dev là cần thiết.

## Hệ quả

- Trên dev, bản mới tốt hơn ở mọi chỉ số.
- Trên bộ đo GĐ1, bản mới đạt cả hai mục tiêu.
- Trên test tạm, bản mới trả lời sai ít hơn (13,3% → 3,3%) nhưng từ chối sai nhiều hơn (24,4% → 32,6%). Số chính thức chờ phiếu nhóm.
- Train lại khoảng 15 phút trên CPU 4 nhân; ra cùng kết quả khi cùng seed và cùng dữ liệu, sai số nhỏ do phép tính số thực.
- Khi đổi dữ liệu train hoặc kho bài thì phải train lại, chọn lại ngưỡng và tạo Release mới.

## Kiểm chứng

- `backend/tests/test_ai_gd2_du_lieu.py`:
  - Bản fine-tune có hàng ngưỡng riêng.
  - Cùng bản gốc cố định.
  - R@1 không giảm.
  - Script chỉ train trên tập train.
- Báo cáo và số đo: `docs/giai-doan/ai-gop-y/03_FINETUNE.md`, `gd2b_test_tam.*`, `gd2b_bo_do_gd1.*`, `gd2b_model_info.json`.
