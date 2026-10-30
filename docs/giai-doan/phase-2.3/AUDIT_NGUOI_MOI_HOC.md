# Kiểm định HarmonyMentor dưới góc nhìn người mới học (20/10/2026)

Bản kiểm định trên `main` (9b3b42d, đã gộp zip v0.5.3 và Giai đoạn B), từ hai vai: chuyên gia kiểm định web dạy nhạc lý và học sinh chưa biết gì về nhạc. Cách làm: chạy thật backend + frontend, đăng ký tài khoản mới, đi hết Tổng quan → Học → Bài 1 → Luyện tập → Tiến độ → Sáng tác trên máy tính (1366px) và điện thoại (390px), rồi chấm thử từng câu của bài 1–4 qua `grading_service`.

Ảnh chụp trước/sau nằm ở thư mục dự án `harmonymentor/audit/screenshots-truoc/` và `screenshots-sau/`.

## 1. Kết luận ngắn

Nội dung Bài 1 là phần mạnh nhất: đúng nhạc lý, dạy từ con số 0 (đếm nửa cung phím đầu = 0, đếm số quãng nốt đầu = 1, khung chữ cái 1–3–5 trước rồi mới đặt dấu hóa). Phần yếu nằm ở **vòng phản hồi**: chấm điểm, giải thích khi sai, điều kiện hoàn thành bài và lịch ôn. Đây chính là chỗ biến "đọc một trang web" thành "học được", và cũng là chỗ SRS hứa nhiều nhất.

## 2. Lỗ hổng tìm được và cách sửa

Mức: **Nặng** = học sinh học sai hoặc bị chấm sai; **Vừa** = làm người mới bỏ cuộc; **Nhẹ** = khó chịu, chưa làm hỏng việc học.

| # | Lỗ hổng (bằng chứng) | Mức | FR | Đã sửa |
|---|---|---|---|---|
| 1 | Câu "F# và Gb có luôn cùng tên?" gõ `không biết` → **Đúng**; câu "vì sao chức năng phụ thuộc ngữ cảnh" gõ `tôi không hiểu context` → **Đúng** (chấm `contains_any` theo từ khóa) | Nặng | FR-EX-03 | 3 câu tự luận ở bài 1–4 đổi sang nút chọn (L01-Q05, L03-Q05, L04-Q06). Bộ chấm từ khóa từ chối câu chứa "không biết/không hiểu/idk…" |
| 2 | Đáp án đúng bị chấm Sai vì khác dấu nối: `1 b3 5`, `Gm7 C7 Fmaj7`, `T → PD → D → T`, `B-F`, `F → E` | Nặng | FR-EX-03 | Chuẩn hóa chuỗi (`sequence`) và không xét thứ tự (`unordered`) cho cặp guide tone. Có test chứng minh đáp án sai vẫn bị chấm sai |
| 3 | Làm sai chỉ thấy "Chưa đúng; hãy nhớ lại khái niệm" và mã thô `INCORRECT_ANSWER`, dù mỗi câu đã có sẵn lời giải trong dữ liệu | Nặng | FR-EX-07, FR-ERR-05 | API trả `explanation` khi đúng hoặc sau 2 lần sai; giao diện hiện "Giải thích: …", bỏ mã lỗi thô |
| 4 | Gõ bừa đủ 6 câu là được "Hoàn thành bài" và kích hoạt thẻ ôn | Nặng | FR-LRN-05 | Hoàn thành cần mọi câu đúng ít nhất 1 lần; backend trả 409 `LESSON_NOT_MASTERED`; trang hoàn thành liệt kê câu còn thiếu, bấm để tới câu đó |
| 5 | Lịch ôn 1-3-7-14-30, nhóm đã chốt Leitner 1-2-4-8-16 (ADR-002); "easy" nhảy 2 hộp | Vừa | FR-FL-07, FR-FL-04 | Leitner 5 hộp, đúng lên 1 hộp, sai về hộp 1; hàng đợi tối đa 20 thẻ; giao diện hiện "hộp 2/5" |
| 6 | Thẻ ôn ý mở cũng chấm theo từ khóa (cùng lỗi #1) | Vừa | FR-FL-01 | Thẻ ý mở thành thẻ tự đánh giá: lật thẻ → "Mình đã nhớ đúng / Mình chưa nhớ". Thẻ gõ đáp án sai thì hiện đáp án |
| 7 | Piano gửi tên thăng: chọn Eb trên phím thì nộp D# và bị chấm sai chính tả | Vừa | FR-MUS-13 | Bài nộp bằng piano chấm `pitch_class_only` (phím không mang chính tả); bài gõ chữ vẫn chấm chính tả |
| 8 | `grading_service` bỏ qua `grading_mode`, `root_position_only` trong cấu hình câu hỏi | Vừa | FR-EX-14 | Đã nối, có test |
| 9 | Bài 1 là một trang ~10.000px gồm 14 khối, không mục lục | Vừa | NFR học tập | Chia 17 bước có nút Tiếp/Trước, mục lục, nhớ bước đang học |
| 10 | Luyện tập ra đề ngẫu nhiên cả `Ab7`, `m7b5`, `dim7`, `A4` cho người vừa vào | Vừa | FR-EX-11 | Mức Dễ/Vừa/Khó bám nội dung bài; mức gợi ý theo bài đã hoàn thành |
| 11 | Chữ của lập trình viên trên giao diện: "vertical slice", "source_audited", "Phase 2 adds…", "prototype v0.1.0", "ReviewState… database", "bản MVP", "Giai đoạn F (18/11–24/11)" | Vừa | – | Viết lại bằng lời cho người học; test chặn các cụm này quay lại |
| 12 | Thẻ ôn và đáp án trắc nghiệm bằng tiếng Anh ("Build F major", "B stays; F moves to E") | Nhẹ | – | Việt hóa, thuật ngữ tiếng Anh để trong ngoặc |
| 13 | Học sinh Việt Nam quen Đô–Rê–Mi, gõ `Rê Fa La` thì lỗi "Không đọc được tên nốt" | Nhẹ | – | Bài học hiểu Đô–Rê–Mi (kể cả "Fa thăng", "Si giáng"); Engine vẫn kiểm dấu hóa |
| 14 | Danh sách bài để "Học ngay" cho cả bài 2–4 khi bài 1 chưa xong | Nhẹ | – | Chỉ bài chưa xong đầu tiên là "Học ngay", bài sau ghi "Nên học sau Bài N" (vẫn mở được) |

Câu hỏi đổi nội dung được phát hành phiên bản mới (L01-Q03/Q05 → v5, L03-Q04/Q05, L04-Q02/Q04/Q05/Q06 → v2) để lượt làm cũ vẫn trỏ đúng phiên bản đã chấm chúng.

## 3. Chưa sửa (ngoài phạm vi đã chốt, ghi lại cho nhóm)

- **Kiểm tra đầu vào và mục tiêu người học** (mô hình chương trình: "Người học (mục tiêu + kiểm tra đầu vào)"). Hiện ai cũng bắt đầu từ Bài 1; người đã biết đàn phải đi lại từ đầu. Nên gắn với Recommender ở CP2.
- **Frontend tự tính nhạc lý** ở `theory/lesson1Theory.ts` (dựng quãng/hợp âm cho phần khám phá Bài 1). Trái nguyên tắc bất biến số 1 trong `CLAUDE.md`. Kết quả hiện đúng, nhưng nên chuyển sang gọi Engine.
- **Trang Luyện tập** gọi thẳng `/engine/grade/*`: không lưu lượt làm, không tính mastery, chưa hiểu Đô–Rê–Mi.
- **Ưu tiên thẻ của kỹ năng yếu** trong hàng đợi ôn (ADR-002) cần mastery EMA, chưa có.
- **Bài 5–8** vẫn chỉ có đặc tả (Đạt soạn). Trong đó 2 câu hỏi (L07-Q06, L08-Q06) còn chấm theo từ khóa, nên đổi sang nút chọn trước khi đưa vào chạy; 13 thẻ ôn ý mở sẽ tự thành thẻ tự đánh giá.
- Lời giải trong dữ liệu bài 2–4 còn trộn tiếng Anh ("Harmonic function là quan hệ hành vi…"); cần Đạt biên tập lại giọng văn cho người mới.

## 4. Kiểm chứng

- `cd backend && pytest -q`: **259 passed** (220 cũ + 39 mới trong `tests/test_audit_nguoi_moi.py`), chạy trên SQLite. 4 test cũ sửa theo hành vi mới có chủ đích: hoàn thành bài phải trả lời đúng trước (`answer_lesson_correctly`), lịch ôn 2 ngày thay cho 3.
- `cd frontend && npm run build`: đạt.
- Chạy thử trong trình duyệt (Playwright) với backend thật: đăng ký, Bài 1 từng bước, sai 2 lần thấy lời giải, nút hoàn thành bị khóa khi chưa đúng đủ, Luyện tập mức Dễ, ôn thẻ tự đánh giá và thẻ gõ đáp án. Không tràn ngang ở 390px. Không có lỗi console ngoài 401 lúc chưa đăng nhập.

## 5. Trình bày lại vấn đề, thách thức góc nhìn ban đầu

Đề bài ban đầu là "tìm lỗ hổng của trang web rồi sửa". Cách đặt vấn đề đó ngầm coi HarmonyMentor là **một trang web có lỗi**, và việc cần làm là vá cho đủ tính năng theo SRS. Nhìn từ phía người học, vấn đề khác hẳn:

1. **Sản phẩm không thiếu tính năng, nó thiếu một vòng học khép kín.** Bài 1 có piano, khuông nhạc, âm thanh, 24 giọng, luyện ngẫu nhiên. Nhưng trước bản sửa này, học sinh có thể đi qua tất cả mà không cần hiểu gì: gõ bừa vẫn "hoàn thành", sai không được giải thích, ôn tập chấm nhầm. Thêm piano hay AI Tutor lúc đó chỉ làm trang web đẹp hơn, không làm người học giỏi hơn. Câu hỏi đúng không phải "còn thiếu FR nào" mà là "**bằng chứng nào cho thấy học sinh đã học được?**".
2. **Bảng truy vết FR đang nói quá.** `PHASE_A_TRUY_VET_FR.md` ghi FR-EX-07 (Giải thích) và FR-EX-05 (Phản hồi sai) là "Có", trong khi người học chưa từng nhìn thấy lời giải. Đếm FR theo "code có tồn tại" khác với "người dùng nhận được". Nếu nhóm báo cáo CP2/CP3 bằng con số FR, giảng viên chỉ cần ngồi thử 5 phút là thấy khoảng cách này.
3. **"Nhiều nội dung" đang là rủi ro, không phải điểm mạnh.** 14 khối mỗi bài, 8 bài, 12 bài cam kết, cộng Harmony Lab, Composition, chatbot. Với người mới, một bài 10.000px là lý do bỏ cuộc. Một bài ngắn có vòng phản hồi chặt dạy được nhiều hơn ba bài dài không có nó. Mục tiêu "≥12 bài" nên được đo bằng tỉ lệ học sinh hoàn thành bài, không phải bằng số bài.
4. **AI Tutor (CP3) không vá được lỗ hổng sư phạm.** Nếu bộ chấm tất định còn chấm "không biết" là đúng, chatbot sẽ giải thích rất hay cho một kết quả sai. Thứ tự đúng là: chấm đúng → giải thích đúng lúc → luật qua bài → rồi mới đến AI. Bản sửa này làm ba bước đầu.
5. **Recommender (CP2) cần dữ liệu sạch hơn là thuật toán hay hơn.** HitRate@5 tính trên lượt làm bài. Trước bản sửa, một lượt "đúng" có thể là đoán mò và một lượt "sai" có thể là đáp án đúng viết khác dấu. Dữ liệu đó đưa vào recommender sẽ cho số đẹp nhưng vô nghĩa.

Tóm lại: thay vì hỏi "trang web của tôi còn lỗi gì", nên hỏi "**một học sinh chưa biết gì, sau 20 phút với Bài 1, có dựng đúng được hợp âm Eb trưởng không, và hệ thống của mình có biết điều đó không?**". Mọi quyết định tiếp theo (thêm bài, thêm AI, thêm sáng tác) nên được đo bằng câu hỏi này.
