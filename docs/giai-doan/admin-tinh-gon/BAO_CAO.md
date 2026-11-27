# Tinh gọn Admin và lời giải tự sinh (27/11/2026)

Phúc giao sau khi thử AI soạn bài với Gemini thật. Phúc chọn 1A–6A và 8A; câu 7 (hạn mức thật) Phúc tự xem trên AI Studio.
Quyết định ghi ở [ADR-041](../../decisions/ADR-041-tinh-gon-admin-loi-giai-engine.md) và phần bổ sung của ADR-036.

## Đã làm

| Yêu cầu | Kết quả | File chính |
|---|---|---|
| 1. Bỏ "Nâng lên Quản trị" | Gỡ nút nâng/hạ và trường `role` của `PATCH /admin/users/{id}` (gửi `role` → 400). Khóa/mở khóa giữ nguyên. | `admin/router.py`, `UsersTab.tsx` |
| 2. Tab Kỹ năng & nguồn | Bỏ tab. Kỹ năng thành mục "Nâng cao" thu gọn cuối tab Bài học (AI chỉ gán được kỹ năng có sẵn nên vẫn cần). Bỏ mục Nguồn khỏi giao diện; file nhập bài tự khai nguồn bằng `title`. | `SkillsSection.tsx`, `LessonsTab.tsx`, `content_import.py`, `skill_admin.py` |
| 3/6. Hạn mức Gemini | Trả lời trong thread. Dòng hiển thị: "soạn bài còn X/12 · AI Tutor còn Y/18 · đặt lại lúc 15:00", hết lượt thì nói rõ vẫn làm được gì. | `AiDraftTab.tsx` |
| 4. Duyệt | Câu admin tạo bằng form: không tick (như cũ). Câu AI admin đã sửa: tự tính đã duyệt (nhãn "Bạn đã sửa"), vẫn cần lời giải. Câu AI chưa sửa mà Engine không kiểm được: vẫn tick. | `ai_questions.py`, `AiDraftTab.tsx` |
| 5. Lời giải tự sinh | Music Engine viết lời giải còn thiếu cho câu tính được và lời chỉ chỗ sai cho từng phương án sai. Câu khái niệm: Gemini viết trong cùng lần soạn. Form câu hỏi bỏ trống lời giải được. | `ai_explain.py` (mới), `ai_questions.py`, `ExercisesPanel.tsx` |
| 7. Bản nháp cũ thiếu lời giải | Nút "Tự điền lời giải" (`POST /admin/ai/drafts/{id}/fill-explanations`), không gọi Gemini. | `ai_service.py`, `router.py`, `AiDraftTab.tsx` |
| Lỗi phát hiện thêm | Câu "quãng 2 trưởng → quãng kép nào?" Engine ra M2; nay ra **M9** (sửa bộ đối chiếu, không đổi Engine). | `ai_questions.compound_check` |

## Kiểm chứng

- Chữ Engine viết qua guardrail: 456 mẫu, 0 chỗ bị báo sai.
- Test mới: `tests/test_admin_tinh_gon_loi_giai.py` (quãng kép đơn/MCQ/4 cặp nốt, không đổi khi đề hỏi quãng đơn, duyệt theo người sửa
  và AI không tự gắn cờ sửa, nút tự điền không gọi AI và giữ lời giải AI), thêm test ở `test_admin_quyen_ai.py`,
  `test_admin_bai_hoc.py`, `test_admin_sua_bai_nhap_file.py`, `test_ai_soan_bai_dot4.py`, `test_ai_luyen_tap.py`.
- Kết quả chạy: xem mô tả PR.
- Ảnh chụp (app thật, AI giả, dữ liệu demo): `/mnt/project-files/admin-tinh-gon/02..10*.png`.

## Chưa làm / rủi ro

- Chưa thử với Gemini thật (khóa chỉ ở máy Phúc). Bản nháp đã soạn trước PR này cần bấm "Tự điền lời giải".
- Lời giải Engine viết theo mẫu, khô hơn lời giáo viên; lời giải AI có sẵn được giữ.
- Mục Nguồn chỉ bỏ khỏi giao diện; API và dữ liệu nguồn giữ nguyên.
- Câu Đúng/Sai: Engine chỉ viết lời giải khi đã quyết được câu đúng hay sai.
