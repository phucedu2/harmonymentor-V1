# Demo AI 10/11/2026: báo cáo triển khai

Nhánh `ai/demo-1011` (xếp chồng trên `ai/gd4-danh-gia`), Draft PR #25 vào `phuc-music`. Không merge.
Đề: prompt "Triển khai ưu tiên cho demo AI ngày 10/11/2026" (Thắng, 04/11/2026), Phúc trả lời 9 câu làm rõ (1A, 2A "Thắng và Đạt đều duyệt", 3 bật mạng, 4A–9A).

## 0. Tóm tắt

| Việc | Trạng thái | Sẵn sàng demo? |
|---|---|---|
| A. 6 câu bài tập mới | **Đã phát hành 04/11** (Thắng + Đạt duyệt) | Có |
| B. Rà 5 mô tả kỹ năng | 4 bản sửa Đạt duyệt đã ghi, 3 vector tính lại; `roman.major_seventh` giữ nguyên (ADR-016) | Có |
| C. AI Tutor RAG | Đã có từ GĐ3; thêm 5 câu vàng, kiểm khẳng định quãng trong lời AI | Có, nhưng Gemini free tier hay quá giờ |
| D. 2 kịch bản E2E | Chạy trên giao diện thật, có video + 7 ảnh | Có |

Kiểm thử: pytest SQLite **917 đạt** (sau khi phát hành và ADR-016) (`-m "not postgres and not live"`), PostgreSQL 16 cục bộ: 13 test HM-010 + `/recommend` đạt (12 test migration cần pgvector, máy này không có, CI có). CI `--min-passed` 928 / 25 (sau khi thêm kiểm số La Mã).

## 1. Nhiệm vụ A: 6 câu mới

Commit `feat(content): 6 câu nháp demo 10/11…`. File: `backend/app/content/curriculum_specs.py`, `source_registry.py` (thêm MT21C), test `backend/tests/test_demo1011_cau_nhap.py` (32 test).

| Id | Kỹ năng | Đề (tóm tắt) | Đáp án | Engine kiểm |
|---|---|---|---|---|
| L01-Q07 | pitch.spelling | M3 đi lên từ D | F# | `identify_interval(D,F#)=M3`; D–Gb = d4 |
| L01-Q08 | pitch.spelling | m3 đi lên từ A | C | `identify_interval(A,C)=m3`; A–B# = A2 |
| L02-Q07 | chord.seventh_quality | Hợp âm bảy bậc V của G trưởng | D7 | `get_chord_tones(D7)=D F# A C`, `roman_numeral(G,D7)=V7` |
| L02-Q08 | chord.seventh_build | Dựng Fmaj7 | F A C E | `get_chord_tones(Fmaj7)` |
| L02-Q09 | roman.major_seventh | D7 trong G trưởng | V7 | `roman_numeral(G,D7)` |
| L02-Q10 | roman.major_seventh | Am7 trong C trưởng | vi7 | `roman_numeral(C,Am7)` |

- Câu chữ tự viết, không chép nguồn. Nguồn: MT21C §1.5, §5.1, §8.1, §8.3 (mở được 04/11) + OMT v2 (máy kiểm bị trang này trả 403 nên chưa mở lại hôm nay; locator lấy từ đợt 0.4B).
- Chấm: trắc nghiệm so khớp đúng phương án, phân biệt hoa thường; Gb và B# (đồng âm) bị chấm sai; Fmaj7 thiếu nốt (MISSING_TONE), thừa nốt (EXTRA_TONE), Eb (SEVENTH_QUALITY), E# hoặc Fb (ENHARMONIC_SPELLING) đều sai; `V7`/`vi7` đúng, khoảng trắng hai đầu được bỏ qua; `v7`, `VI7`, `V⁷`, `V 7`, `vi` sai.
- Khi còn nháp: không hiện với người học, không bắt buộc để hoàn thành bài, gửi bài trả 404. Người đã hoàn thành L01/L02 giữ nguyên trạng thái (logic có sẵn từ PR-3).
- **Mô phỏng sau phát hành** (cho hiện bản nháp trong test, không đổi nguồn): ba câu độc lập đúng lần đầu đưa `pitch.spelling`, `chord.seventh_quality`, `chord.seventh_build`, `roman.major_seventh` lên 0,657 = 1 − 0,7³. Người mới bỏ placement đi L01 → gợi ý L02 → L02 → gợi ý L03 → L03 → gợi ý L04 qua API thật. Không hạ ngưỡng 0,60/0,80.
- Test cũ phải sửa: bộ PR-3 nay chỉ dùng câu đã phát hành; id nháp giả trong test đổi `L02-Q07` → `L02-Q99` (trùng id mới); test migration chấp nhận seed thêm đúng 6 bản nháp.

**Đã phát hành 04/11/2026** (Phúc báo "Thắng và Đạt duyệt"): bỏ `status="draft"` ở 6 dòng. Seed tự chuyển draft → published, không tạo phiên bản mới. L01 nay có 8 câu, L02 có 10 câu. Test GĐ1 dùng roman.major_seventh làm ví dụ 2A đổi số kỳ vọng (0,657 → 0,7599 → 0,832) vì kỹ năng nay có 3 câu; luật 2A không đổi.

## 2. Nhiệm vụ C: AI Tutor RAG

Đã có từ GĐ3 (#23): kho 45 đoạn có id và nguồn, retriever Gemini + BM25 dự phòng, Gemini có schema, claim kiểm bằng Music Engine, sai thì soạn lại 1 lần rồi dự phòng, API `/chat/*`, khung chat, nút "Giải thích lỗi này" kiểm quyền ở backend.

Thêm trong đợt này (commit `feat(ai-tutor): 5 câu vàng…`):
- `scripts/ai/data/rag_gold.json` mục `demo_1011`: 5 câu của Thắng, mỗi câu có đáp án tham chiếu, khối trích dẫn, nguồn, claim Engine, 2 mẫu trả lời sai.
- Guardrail quét thêm câu khẳng định quãng trong lời văn ("D–Gb là M3", "A–C là quãng 3 thứ") bằng `identify_interval`. Câu phủ định ("không phải M3") không bị hiểu nhầm. Bộ cài lỗi GĐ4: kết quả không đổi (11 bắt, 0 báo nhầm).
- Test `backend/tests/test_demo1011_tutor_gold.py` (44 test, FakeProvider): đáp án tham chiếu có nhãn "Đã kiểm bằng Music Engine" và trích dẫn; 9/10 mẫu sai bị bác và **không tới người học** (trả dự phòng); câu không có claim kiểm được thì không có nhãn.
- Test live `backend/tests/test_demo1011_live.py` (RUN_LIVE=1). Chạy 04/11 17:20 UTC:

| Câu | Kết quả |
|---|---|
| D01 C7 vs Cmaj7 | Dự phòng (Gemini quá 15 s), trả từ bài, claim Engine đúng |
| D02 D–F# vs D–Gb | Dự phòng (503), trả đoạn L01-B04 |
| D03 V7 trong G | Gemini trả lời "chưa chắc, bài chưa có", **không trích dẫn** → test đỏ |
| D04 ii–V–I trong C | Dự phòng (503), trả đoạn L04-B03 |
| D05 G–B–D–F# | Gemini trả lời, trích L02-B05, G7 = G B D F đã kiểm |

Không có khẳng định sai nào lọt tới người học. Đo riêng: `gemini-3.5-flash-lite` mất 25 s cho một yêu cầu rỗng, `gemini-3.6-flash` 9 s.

## 3. Nhiệm vụ B: mô tả kỹ năng

Cập nhật 04/11: Đạt duyệt 4 bản sửa dưới đây; đã ghi vào `skill_descriptions.json` và tính lại vector bằng Gemini (`function.tonic`, `progression.ii_v_i`, `chord.seventh_quality`; `harmony.secondary_dominant.identify` là post_mvp nên không có vector). 10 vector khác giữ nguyên. Mô tả `roman.major_seventh` giữ nguyên vì nay `Imaj7` được chấm đúng (ADR-016).

`approved` trong `skill_descriptions.json` là do Claude ghi theo lời Phúc báo, chưa có văn bản của Đạt. Đối chiếu MT21C §9.4, §17.2, §19.1, §8.1, §8.3 (mở được 04/11) và OMT v2 (locator đợt 0.4B, chưa mở lại):

| Kỹ năng | Vấn đề | Bản sửa đề xuất (chờ Đạt) |
|---|---|---|
| function.tonic | Gộp I, iii, vi là "chủ". MT21C §9.4: chỉ I là tonic; vi, iii là *tonic prolongation*, thường đi tiếp tới tiền át; vi còn đứng sau V trong kết ngắt. | "Nhận ra chức năng chủ: hợp âm I ổn định, là nơi câu nhạc nghỉ và kết. vi và iii chung hai nốt với I nên có lúc kéo dài vùng chủ, nhưng không phải lúc nào cũng mang chức năng chủ." |
| harmony.secondary_dominant.identify | "mượn tạm" dễ nhầm với hợp âm mượn (mode mixture); "hợp âm bảy át" bỏ sót triad trưởng. MT21C §17.2: át phụ là triad trưởng hoặc hợp âm bảy át đi tới hợp âm khác I (tonicization); §19.1: mượn = lấy từ giọng thứ cùng tên. | "Nhận diện hợp âm át phụ như V/V, V/ii, V/vi: triad trưởng hoặc hợp âm bảy át đi tới một hợp âm khác I, làm hợp âm đó tạm nghe như chủ. Khác với hợp âm mượn từ giọng thứ cùng tên." |
| progression.ii_v_i | "quan trọng nhất của jazz": không có nguồn nào trong registry nói vậy. | "Nhận diện và dựng tiến trình ii–V–I với hợp âm bảy trong giọng trưởng, ví dụ Dm7–G7–Cmaj7 trong C trưởng: tiền át, át, rồi về chủ. Gặp nhiều trong jazz, cũng có trong pop và bossa nova." |
| chord.seventh_quality | "màu sắc mềm mại" là cảm nhận chủ quan. | "Phân biệt năm loại hợp âm bảy maj7, 7 (át), m7, m7b5 (ø7), dim7 theo triad bên dưới và quãng 7 tính từ nốt gốc." |
| roman.major_seventh | Mô tả và bài L02 viết `Imaj7`, `IVmaj7`; **Music Engine trả `IM7`, `IVM7`** (giống MT21C §8.3). Người gõ `Imaj7` như bài dạy sẽ bị chấm sai. Hiện chưa câu nào hỏi Imaj7/IVmaj7 nên chưa ai gặp. | Cần chọn một quy ước (câu hỏi Q-B1 dưới đây) rồi mới viết lại. |

Sửa xong thì chạy lại `python -m app.ai.build_skill_embeddings` (gọi Gemini, 26 mô tả) và test hash `test_ai_gd2_embedder_content.py`.

## 4. Nhiệm vụ D: 2 kịch bản trên giao diện thật

Script `scripts/e2e/demo_1011.cjs` (Playwright), đáp án lấy từ `scripts/e2e/dap_an_demo_1011.py`. Minh chứng: `docs/minh-chung/anh/demo-1011/01..07*.png`, video `docs/minh-chung/video/demo-1011-goi-y-va-giai-thich-loi.webm`.

Môi trường: backend uvicorn + CSDL SQLite test mới (alembic head), frontend Vite, `AI_ENABLED=1`, khóa Gemini chỉ trong biến môi trường, `SHOW_DRAFT_CONTENT=1` (lúc chạy 6 câu còn là nháp; nay đã phát hành nên không cần cờ này).

1. Recommender: đăng ký → bỏ placement → gợi ý "Bắt đầu từ nền tảng: Bài 1" → làm đủ 8 câu L01 trên giao diện → hoàn thành → gợi ý **Bài 2, "Củng cố kỹ năng yếu", lý do "Giúp bạn củng cố 'Dựng hợp âm bảy'…"**, mở "Vì sao gợi ý bài này?" → bấm "Mở bài" → L02 mở; `recommendation_logs.clicked_lesson_id = L02`.
2. AI Tutor: trong L02 gõ `G B D F#` cho "Dựng G7" → Engine: "Bạn đang dùng quãng 7 trưởng thay vì quãng 7 thứ (F# → F)" (SEVENTH_QUALITY) → "Giải thích lỗi này" → Gemini thật (6,5 s, 1.062 token vào, 170 ra), gợi ý mức 1/3, trích dẫn [L02] "4. Giải mã maj7, m7, 7, ø7…", không lộ đáp án. Lần chạy đầu Gemini quá 15 s, app trả dự phòng từ bài học (đúng thiết kế).

Lệnh: xem đầu file script; tóm tắt: chạy backend với `DATABASE_URL=sqlite:///…/e2e.db SHOW_DRAFT_CONTENT=1`, `npm run dev`, rồi `OUT=… VID=… ANS=… node scripts/e2e/demo_1011.cjs`.

Test CI không gọi mạng tương ứng: `test_demo1011_cau_nhap.py::test_new_learner_without_placement_walks_l01_to_l04` (API), `test_demo1011_tutor_gold.py` (FakeProvider), `test_pg_recommend.py` (PostgreSQL).

## 5. Việc làm theo các câu đã duyệt (C1–C9)

- C3 (R1/R2): đã sửa trước đó trên GĐ2.
- C4: giữ thuật toán CF, đổi câu chữ: nhãn "Người cùng trình độ đã vững", câu "Phần lớn người học có trình độ giống bạn hiện đã vững 'X'." Chữ "(dữ liệu mô phỏng)" đã có ở chân thẻ. Câu chữ vẫn chờ Đạt/Astra xem.
- C7: ADR-008 (P-1, D-2, R-1, Q-D, Q-E) và ADR-014 mục 3 ghi "có hiệu lực" theo tin "Thắng duyệt hết"; P-2 vẫn mở.
- C8: thêm `test_pg_recommend.py` (4 test, chạy trong job PostgreSQL).
- C6 (Đạt xác nhận bằng văn bản 26 mô tả + 12 kỹ năng placement) vẫn chưa có.

## 6. Lỗi và rủi ro chưa xử lý

1. ~~Khẳng định số La Mã chưa được kiểm.~~ Đã xử lý 04/11 (Thắng duyệt): guardrail có thêm `get_roman_numeral`; "V7 trong G trưởng là G7" nay bị bác (ADR-015 cập nhật). Cả 10/10 mẫu sai của 5 câu vàng bị bác.
2. ~~D03 không trả lời được.~~ Đã xử lý 04/11 (Đạt duyệt): L02-B08 thêm "trong G major, bậc V là D nên V7 = D7 (D–F#–A–C)", tính lại vector 45 đoạn. Chạy live lần 2: 5/5 câu vàng đạt (3 Gemini trả lời, 2 dự phòng do quá giờ/503; D03 nay trích đúng L02-B08 với D7 = D F# A C đã kiểm).
3. **Gemini free tier**: 3/5 câu live và 1/2 lần giải thích lỗi rơi vào dự phòng (quá 15 s hoặc 503). Demo vẫn chạy (dự phòng đúng thiết kế), nhưng muốn trình diễn câu trả lời của AI ổn định thì nên dùng khóa trả phí hoặc đổi `GEMINI_MODEL` sang mô hình nhanh hơn trong `.env` lúc demo.
4. ~~Quy ước `Imaj7` (bài) và `IM7` (Engine) lệch nhau.~~ Đã xử lý: chấm nhận cả hai (ADR-016).
5. Trang OMT trả 403 cho máy kiểm; nguồn OMT trong 6 câu là locator cũ, chưa mở lại.

## 7. Không tuyên bố

Không có số liệu nào cho thấy mô hình giúp học tốt hơn. Kết quả trên chỉ chứng minh luồng kỹ thuật chạy. Không làm Lyrics-to-Harmony, Markov, Retention Predictor.

## 8. Câu hỏi còn mở

- ~~Q-A1~~ Thắng + Đạt duyệt, đã phát hành.
- ~~Q-B1~~ Phúc giao Claude chọn: chấm nhận cả hai, ADR-016.
- ~~Q-B2~~ Đạt duyệt, đã ghi.
- ~~Q-C1~~ Thắng duyệt, đã thêm.
- ~~Q-C2~~ Đạt duyệt, đã thêm.
