# Tài liệu theo giai đoạn

Thư mục này gom báo cáo triển khai (`PHASE_*`), nhật ký kiểm chứng (`VERIFICATION_*`) và các bản kiểm định gắn với từng giai đoạn. Mỗi giai đoạn một thư mục con, nên báo cáo và bằng chứng của cùng một đợt việc nằm cạnh nhau.

Tên file giữ nguyên như lúc viết, chỉ đổi chỗ (30/10/2026, theo góp ý của thầy), nên `git log --follow <file>` vẫn xem được toàn bộ lịch sử.

Các giai đoạn 0.2 → 2.3 là lộ trình của bản code gốc (zip v0.1.0 → v0.5.3), viết theo SRS v1.3. Từ 23/10/2026 nguồn sự thật là bộ tài liệu bản 2.1 trong [`docs/SRS/`](../SRS/), nên số liệu và mã FR trong các file dưới đây là lịch sử, không phải trạng thái hiện tại.

| Giai đoạn | Phiên bản | Nội dung | File |
|---|---|---|---|
| [phase-0.2](phase-0.2/) | v0.1.0 | Ổn định chấm điểm và khung học tập | [PHASE_0_2_IMPLEMENTATION.md](phase-0.2/PHASE_0_2_IMPLEMENTATION.md) |
| [phase-0.3-0.4](phase-0.3-0.4/) | v0.3.0-dev | Khung ứng dụng, cơ sở dữ liệu, hợp đồng học tập | [PHASE_0_3_0_4_IMPLEMENTATION.md](phase-0.3-0.4/PHASE_0_3_0_4_IMPLEMENTATION.md), [VERIFICATION_PHASE_0_3_0_4.txt](phase-0.3-0.4/VERIFICATION_PHASE_0_3_0_4.txt) |
| [phase-0.4B](phase-0.4B/) | v0.3.1-dev | Kiểm toán nguồn giáo trình, đặc tả nội dung | [PHASE_0_4B_IMPLEMENTATION.md](phase-0.4B/PHASE_0_4B_IMPLEMENTATION.md), [VERIFICATION_PHASE_0_4B.txt](phase-0.4B/VERIFICATION_PHASE_0_4B.txt) |
| [phase-1](phase-1/) | v0.4.0-dev | Lát cắt dọc nền tảng học tập | [PHASE_1_IMPLEMENTATION.md](phase-1/PHASE_1_IMPLEMENTATION.md), [VERIFICATION_PHASE_1.txt](phase-1/VERIFICATION_PHASE_1.txt) |
| [phase-A](phase-A/) | v0.4.0 | Giai đoạn A: ổn định nền, kế hoạch B–F, truy vết FR theo SRS v1.3 | [PHASE_A_PLAN.md](phase-A/PHASE_A_PLAN.md), [PHASE_A_TRUY_VET_FR.md](phase-A/PHASE_A_TRUY_VET_FR.md) |
| [phase-2](phase-2/) | v0.5.0-dev | Lớp âm nhạc tương tác (piano, ký âm, âm thanh) | [PHASE_2_IMPLEMENTATION.md](phase-2/PHASE_2_IMPLEMENTATION.md), [VERIFICATION_PHASE_2.txt](phase-2/VERIFICATION_PHASE_2.txt), [BEGINNER_CONTENT_AUDIT_PHASE_2.md](phase-2/BEGINNER_CONTENT_AUDIT_PHASE_2.md) |
| [phase-2.1](phase-2.1/) | v0.5.1-dev | Sửa lỗi ký âm làm trắng trang | [PHASE_2_1_NOTATION_HOTFIX.md](phase-2.1/PHASE_2_1_NOTATION_HOTFIX.md), [VERIFICATION_PHASE_2_1_HOTFIX.txt](phase-2.1/VERIFICATION_PHASE_2_1_HOTFIX.txt) |
| [phase-2.2](phase-2.2/) | v0.5.2-dev | Viết lại Bài 1 cho người mới bắt đầu | [PHASE_2_2_LESSON1_PEDAGOGY_REWRITE.md](phase-2.2/PHASE_2_2_LESSON1_PEDAGOGY_REWRITE.md), [VERIFICATION_PHASE_2_2.txt](phase-2.2/VERIFICATION_PHASE_2_2.txt) |
| [phase-2.3](phase-2.3/) | v0.5.3-dev | Bài 1 nhiều giọng; kiểm định dưới góc nhìn người mới học (20/10, sau khi gộp Giai đoạn B) | [PHASE_2_3_MULTIKEY_LESSON1.md](phase-2.3/PHASE_2_3_MULTIKEY_LESSON1.md), [VERIFICATION_PHASE_2_3.txt](phase-2.3/VERIFICATION_PHASE_2_3.txt), [AUDIT_NGUOI_MOI_HOC.md](phase-2.3/AUDIT_NGUOI_MOI_HOC.md) |
| [phuc-music](../phuc-music/) | v0.5.4-dev | Gộp khu học v0.5.3 vào nền main, xưởng sáng tác (Bước 0–4), backing track ban nhạc thật (02/11) | [00_KHAO_SAT.md](../phuc-music/00_KHAO_SAT.md), [01_NHAT_KY_GOP.md](../phuc-music/01_NHAT_KY_GOP.md), [BAO_CAO_BUOC_1.md](../phuc-music/BAO_CAO_BUOC_1.md), [BAO_CAO_BUOC_2.md](../phuc-music/BAO_CAO_BUOC_2.md), [BAO_CAO_BUOC_3.md](../phuc-music/BAO_CAO_BUOC_3.md), [BAO_CAO_BUOC_4.md](../phuc-music/BAO_CAO_BUOC_4.md), [BAO_CAO_BACKING_TRACK.md](../phuc-music/BAO_CAO_BACKING_TRACK.md) |
| [ai-gd0](ai-gd0/) | v0.5.4-dev | Pipeline AI của giảng viên, GĐ0: kiểm hiện trạng, mô phỏng mở khóa L01–L04, kiểm Gemini, kế hoạch GĐ1–GĐ4 (04/11) | [KE_HOACH_AI.md](ai-gd0/KE_HOACH_AI.md), [mo_phong_mo_khoa_2026-11-04.md](ai-gd0/mo_phong_mo_khoa_2026-11-04.md) |
| [ai-gd1](ai-gd1/) | v0.5.4-dev | Pipeline AI GĐ1: ánh xạ kỹ năng ADR-008, mastery EMA, luật ôn 2A, bài kiểm tra đầu vào (04/11) | [BAO_CAO.md](ai-gd1/BAO_CAO.md), [nguoi_mau_2026-11-04.md](ai-gd1/nguoi_mau_2026-11-04.md) |
| [ai-gd2](ai-gd2/) | v0.5.4-dev | Pipeline AI GĐ2: hệ gợi ý 3 tầng (luật, nội dung Gemini/TF-IDF, KNN chiều chung), G-3 ba danh sách, mục tiêu học, thẻ Dashboard (04/11) | [BAO_CAO.md](ai-gd2/BAO_CAO.md) |
| [ai-gd3](ai-gd3/) | v0.5.4-dev | Pipeline AI GĐ3: AI Tutor có trích dẫn (RAG Gemini + BM25), kiểm Music Engine, chống prompt injection, giải thích lỗi 3 mức, khung chat nổi (04/11) | [BAO_CAO.md](ai-gd3/BAO_CAO.md) |
| [ai-gd4](ai-gd4/) | v0.5.4-dev | Pipeline AI GĐ4: thực nghiệm hệ gợi ý (2.000 người mô phỏng, P0–P3) và AI Tutor (bộ chuẩn 30 câu, Gemini so với BM25, chặn, guardrail, độ trễ) (04/11) | [BAO_CAO_THUC_NGHIEM.md](ai-gd4/BAO_CAO_THUC_NGHIEM.md) |
| [demo-1011](demo-1011/) | v0.5.4-dev | Demo AI 10/11: 6 câu nháp gỡ lộ trình L02–L04, 5 câu vàng AI Tutor, kiểm quãng trong lời AI, 2 kịch bản E2E trên giao diện thật. |
| [wow-ui-thu-nghiem](wow-ui-thu-nghiem/) | 0.5.4-dev | Thử nghiệm trang chủ "wow": cuộn GSAP + âm thanh, Đồng & Gỉ (gộp vào phuc-music 04/11) | [BAO_CAO_WOW_UI.md](wow-ui-thu-nghiem/BAO_CAO_WOW_UI.md) |
| [ai-gop-y](ai-gop-y/) | v0.5.4-dev | Góp ý thầy G1–G7, GĐ0: kiểm kê kho RAG, đo lại BM25 / MiniLM / e5-small, 10 lỗ hổng định tuyến (06/11) | [00_KIEM_KE_RAG.md](ai-gop-y/00_KIEM_KE_RAG.md) |
| [ai-gop-y](ai-gop-y/) | v0.5.4-dev | Góp ý thầy G1/G3, GĐ1: AI Tutor định tuyến 4 luồng (trong bài / ngoài bài theo Music Engine hoặc "không biết" / từ chối / hướng dẫn sử dụng), e5-small cục bộ, ngưỡng do script chọn, ADR-017 (06/11) | [01_DINH_TUYEN.md](ai-gop-y/01_DINH_TUYEN.md) |
| [ai-gop-y](ai-gop-y/) | v0.5.4-dev | Góp ý thầy GĐ2: dữ liệu AI Tutor 1.011 câu (train/dev/test tạm, Claude viết đóng vai người học, tách theo nhóm), train lại tầng 1, sửa luật định tuyến, nguồn theo khối (07/11) | [02_DU_LIEU.md](ai-gop-y/02_DU_LIEU.md) |
| [ai-gop-y](ai-gop-y/) | v0.5.4-dev | Góp ý thầy G6, GĐ2b: fine-tune e5-small trên CPU (AUC tách A khỏi B/C 0,79 → 0,88), ngưỡng riêng, ADR-018; chưa bật mặc định (07/11) | [03_FINETUNE.md](ai-gop-y/03_FINETUNE.md) |
| [ai-gop-y](ai-gop-y/) | v0.5.4-dev | Góp ý thầy G2, GĐ3: nháp lý thuyết L05 Secondary Dominants (11 khối, đối chiếu Music Engine bằng test, ẩn tới khi Astra/Đạt duyệt) (07/11) | [04_L05_NHAP.md](ai-gop-y/04_L05_NHAP.md) |

## Quy ước cho giai đoạn sau

- Mỗi giai đoạn mới (ví dụ `gd2-goi-y`) tạo thư mục `docs/giai-doan/<tên giai đoạn>/`, đặt báo cáo triển khai và file kiểm chứng của giai đoạn đó vào đây, rồi thêm một dòng vào bảng trên.
- Báo cáo PR vẫn ở [`docs/bao-cao/`](../bao-cao/), ảnh và minh chứng chấm điểm ở [`docs/minh-chung/`](../minh-chung/), quyết định ở [`docs/decisions/`](../decisions/).
- Đặc tả dùng chung cho nhiều giai đoạn (`SKILL_GRAPH.md`, `LESSON_SPECIFICATIONS.md`, `CURRICULUM_SOURCE_MATRIX.md`) và minh chứng mốc chấm (`CP1_*.md`) giữ ở `docs/`.
