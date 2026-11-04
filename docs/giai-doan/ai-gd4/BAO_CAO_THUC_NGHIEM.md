# Báo cáo GĐ4 pipeline AI: thực nghiệm hệ gợi ý và AI Tutor

Nhánh `ai/gd4-danh-gia`, xếp chồng trên `ai/gd3-tutor` (PR #23). Draft PR vào `phuc-music`, không merge. Ngày chạy: 04/11/2026, máy cloud.
Số liệu dưới đây lấy nguyên từ ba file JSON cùng thư mục; không có số nào gõ tay. Mục nào chưa đo ghi **NOT EVALUATED**.

## Tóm tắt cho nhóm

1. **AI Tutor (RAG)** chạy tốt trên bộ chuẩn 30 câu. Truy xuất bằng Gemini đạt Recall@1 93,3% (BM25: 56,7%). Có nghỉ 5 giây giữa các câu thì 30/30 câu trả lời được, đều trích dẫn đúng bài, không câu nào còn khẳng định sai Engine, p95 1,7 s. Câu ngoài phạm vi và câu tấn công bị chặn 100%, không chặn nhầm câu khái niệm nào.
2. **Gói Gemini miễn phí không chịu được gọi liên tục.** Gửi 30 câu sát nhau thì 7 câu rơi về dự phòng (429/503), p95 lên 5,3 s. Đây là giới hạn hạ tầng, không phải lỗi logic, nhưng ảnh hưởng buổi demo (mục 2.6).
3. **Hệ gợi ý: kết quả mô phỏng KHÔNG ủng hộ cấu hình hiện tại.** Luật tiên quyết loại 97% danh sách, nên P1, P2 và cả 6 cấu hình P3 chỉ đạt HitRate@1 2,8%, thua xa P0 phổ biến (96,7%). Nguyên nhân là cấu trúc: kỹ năng chỉ có 1 câu hỏi thì làm đúng ngay lần đầu cũng chỉ lên mastery 0,30, dưới ngưỡng sẵn sàng 0,60. Phải ôn đúng thêm ít nhất 2 ngày nữa mới mở được bài sau (mục 1.6). Đây là câu hỏi cho Thắng; mình **không** tự đổi ngưỡng hay luật.
4. Với 4 bài học được, số liệu mô phỏng chỉ chứng minh thuật toán chạy đúng như thiết kế. Nó không chứng minh hệ gợi ý tốt với người thật (mục 3).

---

## 1. Hệ gợi ý (`scripts/ai/evaluate_recommender.py`)

### 1.1 Dữ liệu

| Mục | Giá trị |
|---|---|
| Bộ sinh | `scripts/ai/sim/nguoi_mo_phong.py`, **không import** bộ gợi ý, dịch vụ hay CSDL (test `test_simulator_does_not_import_recommender_or_services` kiểm bằng AST và `sys.modules`) |
| Số người | 2.000 (Pop 500, Guitar 500, Jazz 500, Newbie 500) |
| Seed | `20261104`; tất định kể cả khi `PYTHONHASHSEED` khác (test `test_simulator_deterministic_across_hash_seeds`) |
| Bài | Chỉ L01–L04: bài `reviewed`/`published` có câu đang chạy trong ứng dụng. L05–L08 chưa có câu hỏi chạy nên không ai "học" được |
| Sự kiện/người | trung bình 99,8, trung vị 104; trung bình 3,44 lượt bắt đầu bài |
| Mô hình người | năng lực ẩn θ theo kỹ năng; P(đúng) = 0,15 + 0,8θ + nhiễu; khoảng 80% chọn bài theo tiên quyết (θ ≥ 0,6), 20% chọn theo sở thích chân dung; ôn Leitner 1/2/4/8/16 ngày; 2–6 lượt mỗi buổi, tối đa 3 lần/câu/ngày |
| Mastery khi đánh giá | đúng luật GĐ1: EMA α = 0,3 từ 0, D-3 (1 / 0 / 0,5 / đúng lặp không cộng), ôn 2A tối đa 1 lượt tính/kỹ năng/ngày VN |
| Vector mục tiêu | 4 câu mục tiêu của 4 chân dung, nhúng sẵn bằng `gemini-embedding-001` (`scripts/ai/data/persona_goal_vectors.json`); vector kỹ năng là file GĐ2. Script đánh giá không gọi mạng |

### 1.2 Chia dữ liệu

- Mỗi người: mốc cắt là thời điểm của sự kiện thứ ⌊0,8·n⌋ (theo thời gian).
- Chỉ dùng sự kiện **trước** mốc, kể cả dữ liệu của láng giềng. Script quét mọi sự kiện của 2.000 người theo thời gian và gợi ý cho từng người đúng lúc tới mốc của họ, nên vector láng giềng là trạng thái lúc đó, không phải trạng thái cuối.
- **Đáp án chính** (G-3): các bài người đó bắt đầu lần đầu sau mốc. Danh sách chính bỏ bài đã bắt đầu trước mốc, tương ứng mục "Bài nên học tiếp".
- **Đáp án phụ**: mọi bài có hoạt động sau mốc; danh sách phụ không lọc.
- 1.605/2.000 người không bắt đầu bài mới nào sau mốc (đa số đã mở cả 4 bài trước mốc), nên bị loại khỏi chỉ số chính. Còn **395 người được đánh giá**.

### 1.3 Phương án so sánh

| Mã | Nội dung |
|---|---|
| P0 | Phổ biến: xếp bài theo số lượt bắt đầu của mọi người trước thời điểm đó, không lọc luật |
| P1 | Chỉ luật: các bài qua bước lọc (`rule_filter`), theo thứ tự chương trình |
| P2 | Luật + nội dung: `recommend` không láng giềng, tức công thức người mới 0,55/0,25/0,20 |
| P3-s{2,3,4}{a,b} | Đủ 3 tầng (0,35/0,25/0,20/0,20), KNN k = 10 với số chiều chung tối thiểu 2/3/4 × dự phòng a/b (6 cấu hình ADR-008) |
| P2-bo-tien-quyet | **Chỉ để phân tích độ nhạy**, không phải đề xuất: P2 khi bỏ điều kiện tiên quyết ở bước lọc |

### 1.4 Lệnh

```bash
cd backend && python ../scripts/ai/evaluate_recommender.py --n 2000 --seed 20261104 \
    --out ../docs/giai-doan/ai-gd4/ket_qua_goi_y.json      # 17 s, không gọi mạng
```

### 1.5 Kết quả (395 người, CI 95% bootstrap 1.000 lần)

| Phương án | HitRate@1 | CI95 | HitRate@3 | HitRate@5 | Precision@1 | Precision@3 | MRR | CI95 MRR | Danh sách chính rỗng |
|---|---|---|---|---|---|---|---|---|---|
| P0 | 0,967 | [0,947; 0,982] | 1,000 | 1,000 | 0,967 | 0,333 | 0,983 | [0,973; 0,992] | 0% |
| P1 | 0,028 | [0,013; 0,046] | 0,028 | 0,028 | 0,028 | 0,009 | 0,028 | [0,013; 0,046] | 97,0% |
| P2 | 0,028 | [0,013; 0,046] | 0,028 | 0,028 | 0,028 | 0,009 | 0,028 | [0,013; 0,046] | 97,0% |
| P3 (cả 6 cấu hình) | 0,028 | [0,013; 0,046] | 0,028 | 0,028 | 0,028 | 0,009 | 0,028 | [0,013; 0,046] | 97,0% |
| P2-bo-tien-quyet | 0,846 | [0,810; 0,881] | 1,000 | 1,000 | 0,846 | 0,333 | 0,921 | [0,903; 0,940] | 0% |

Chỉ số phụ (mọi bài có hoạt động sau mốc, danh sách không lọc):

| Phương án | HitRate@1 (phụ) | HitRate@3 (phụ) | Precision@3 (phụ) |
|---|---|---|---|
| P0 | 0,028 | 0,744 | 0,300 |
| P1 | 0,028 | 0,106 | 0,036 |
| P2 | 0,101 | 0,106 | 0,036 |
| P3-s2a / s2b | 0,101 | 0,106 | 0,036 |
| P3-s3a / s3b | 0,096 | 0,106 | 0,036 |
| P3-s4a / s4b | 0,091 | 0,106 | 0,036 |
| P2-bo-tien-quyet | 0,514 | 0,944 | 0,451 |

Theo chân dung (HitRate@1 chính):

| Phương án | Pop (108) | Guitar (101) | Jazz (49) | Newbie (137) |
|---|---|---|---|---|
| P0 | 1,000 | 1,000 | 1,000 | 0,905 |
| P1 = P2 = P3 | 0,019 | 0,040 | 0,061 | 0,015 |
| P2-bo-tien-quyet | 1,000 | 1,000 | 0,959 | 0,569 |

Láng giềng (P3):
- Với số chiều chung 2 hoặc 3, có láng giềng ở 99,75% lượt (cách a). Với 4 chiều, cách a không có láng giềng hợp lệ ở 8,6% lượt.
- Cách b luôn tìm được láng giềng: với s4b có 33/395 lượt phải hạ xuống 3 chiều và 1 lượt xuống 1 chiều.
- Tỷ lệ `few_eligible` (< 5 bài qua lọc) là 100% ở mọi cấu hình, vì chỉ có 4 bài.

### 1.6 Đọc kết quả

**Vì sao P1, P2 và P3 bằng nhau và gần 0.** Ở 384/395 người (97%), bài họ thật sự bắt đầu sau mốc bị bước lọc loại với lý do `prereq_not_ready` (trường `truth_lesson_filter_reason` trong JSON). Khi bài đúng đã bị loại thì cách chấm điểm (nội dung, CF) không còn gì để xếp. Vì vậy 6 cấu hình ADR-008 không phân biệt được với nhau trên bộ dữ liệu này.

**Vì sao bị loại.** Đây là phép tính, không phải nhiễu mô phỏng. Số câu đang chạy theo kỹ năng ở L01–L04: `interval.naming`, `chord.triad_formula`, `pitch.spelling`, `scale.major`, `roman.major_seventh` và 3 kỹ năng `function.*` mỗi kỹ năng **1 câu**; `chord.triad_build` và `function.progression` 3 câu; còn lại 2 câu. Với EMA từ 0, α = 0,3 và D-3 (mỗi câu chỉ tính lần đúng đầu), một kỹ năng 1 câu:

- đúng ngay lần đầu: 0,3 × 1 = **0,30**;
- sau 1 lượt ôn đúng được tính: 0,51; sau 2 lượt: **0,657** (lượt ôn chỉ tính khi đến hạn, tối đa 1 lần/ngày, theo 2A).

Ví dụ: L02 cần `pitch.spelling` ≥ 0,60, mà kỹ năng này chỉ có 1 câu ở L01. Người học xong L01 phải chờ ít nhất 2 ngày ôn đúng nữa thì hệ gợi ý mới mở L02. Trong khoảng đó người mô phỏng (và rất có thể người thật) đã tự sang L02. Tương tự, L03 cần `roman.major_seventh` (1 câu), L04 cần `function.progression` và hai kỹ năng hợp âm 7.

**P0 gần tuyệt đối là do bộ dữ liệu, không phải do P0 giỏi.** Chỉ có 4 bài với thứ tự chương trình cố định, và 80% người mô phỏng đi theo thứ tự đó. Vì vậy "bài phổ biến nhất chưa học" gần như luôn là bài kế tiếp. HitRate@3 và @5 bão hòa (= 1) ở mọi phương án có danh sách khác rỗng, vì danh sách chính chỉ còn 1–3 bài. Precision@3 tối đa là 1/3 vì mỗi người chỉ có 1 bài đáp án chính.

**Độ nhạy.** Chỉ bỏ điều kiện tiên quyết (giữ nguyên cách chấm P2) là HitRate@1 lên 0,846 và MRR 0,921. Mức này vẫn thấp hơn P0, chủ yếu do Newbie (0,569): công thức người mới đẩy bài có kỹ năng gần mục tiêu lên trước bài kế tiếp. Kết quả độ nhạy này **không** phải đề xuất bỏ tiên quyết. Nó chỉ cho thấy phần lớn chênh lệch đến từ bước lọc, không đến từ trọng số.

**Câu hỏi cho Thắng (không tự làm):**
- (a) Giữ ngưỡng sẵn sàng 0,60 cho tiên quyết, nhưng chỉ áp dụng khi kỹ năng tiên quyết đã có ≥ 2 câu?
- (b) Đợi HM-013 (M19, thêm 19 câu độc lập) rồi chạy lại?
- (c) Dùng ngưỡng riêng cho bước lọc tiên quyết?

Mình nghiêng về (b) rồi chạy lại script này, vì nó không đổi luật mà sửa đúng gốc là thiếu câu. P-2 (ngưỡng / trọng số chính thức) nên chờ lần chạy đó.

### 1.7 Ca thất bại tiêu biểu (lấy từ lần chạy thử 200 người khi gỡ lỗi script)

- **Guitar, đã bắt đầu L01–L03, sau mốc bắt đầu L04.** Mastery lúc mốc: `function.progression` 0,51, `chord.seventh_quality` 0,41 (ngưỡng 0,60). L04 bị loại, danh sách chính rỗng, nên cả P1–P3 trượt.
- **Jazz, đã bắt đầu L01 và L04 (đi tắt theo sở thích), sau mốc bắt đầu L02.** `pitch.spelling` 0,15 < 0,60, nên L02 bị loại dù người này đang học L04.

---

## 2. AI Tutor và RAG (`scripts/ai/evaluate_rag.py`)

### 2.1 Bộ chuẩn

`scripts/ai/data/rag_gold.json` gồm:
- 30 câu khái niệm (G01–G30, phủ L01–L04), mỗi câu có khối đúng (`blocks`) và đáp án tham chiếu;
- 10 câu ngoài phạm vi;
- 10 câu tấn công (prompt injection, đòi lộ system prompt, đòi đáp án);
- 20 câu trả lời cài sẵn để thử guardrail (11 có lỗi nhạc lý, 9 đúng).

**Bộ chuẩn do Claude soạn và duyệt, chưa có người duyệt độc lập.** Đạt sẽ lấy mẫu 10 câu (12A). 10 câu có nội dung nhạc lý đã được kiểm bằng Music Engine: 10/10 khớp (`gold_engine_checked`, test `test_rag_gold_blocks_exist_and_engine_answers_match`).

### 2.2 Lệnh

```bash
cd backend && python ../scripts/ai/evaluate_rag.py                       # phần không gọi mạng: BM25, chặn, guardrail
cd backend && AI_ENABLED=1 GEMINI_API_KEY=... python ../scripts/ai/evaluate_rag.py --live --pause 5 \
    --out ../docs/giai-doan/ai-gd4/ket_qua_rag.json
cd backend && AI_ENABLED=1 GEMINI_API_KEY=... python ../scripts/ai/evaluate_rag.py --live \
    --out ../docs/giai-doan/ai-gd4/ket_qua_rag_goi_lien_tuc.json
```

Cấu hình khi chạy: `gemini-embedding-001`, LLM `gemini-3.5-flash-lite` (thử lại bằng `gemini-3.6-flash`), `RAG_MIN_SCORE` 0,60, top_k 4.

### 2.3 Truy xuất (30 câu khái niệm)

| | Recall@1 | Recall@4 | MRR |
|---|---|---|---|
| BM25 (khi AI tắt) | 56,7% | 90,0% | 0,708 |
| Gemini embedding | **93,3%** | **100%** | **0,967** |

Với Gemini, 30/30 câu khái niệm có đoạn vượt ngưỡng 0,60. Hai câu không đứng hạng 1 (G09, G15) đều đứng hạng 2. BM25 trượt hoàn toàn ở 3 câu (G09, G15, G17), là các câu diễn đạt bằng từ không có trong bài.

### 2.4 Chặn câu ngoài phạm vi và câu tấn công

Đo bằng đúng luồng dịch vụ `answer_question`, dùng một LLM giả ghi lại lời gọi. "Bị chặn" nghĩa là không có lời gọi LLM nào và route là từ chối hoặc chưa chắc.

| Chế độ | Ngoài phạm vi bị từ chối | Tấn công bị từ chối | Câu khái niệm bị chặn nhầm |
|---|---|---|---|
| Có embedding (AI bật) | **100%** | **100%** | 0% |
| Chỉ BM25 (AI tắt) | 60% | 90% | 0% |

Chế độ BM25 yếu với câu ngoài phạm vi viết theo cách mới, vì BM25 không tách được bằng điểm số. Mình **không** chỉnh bộ phân loại theo bộ test này, để tránh khớp đề. Khi AI tắt, câu lọt qua chỉ nhận trích đoạn bài học gần nhất, không có LLM nào được gọi, nên rủi ro là trả lời lạc đề, không phải lộ dữ liệu.

### 2.5 Guardrail (20 câu cài sẵn)

Bắt được **11/11** câu có lỗi, **0** báo nhầm trên 9 câu đúng.

### 2.6 Trả lời đầy đủ bằng Gemini thật (30 câu)

| Chỉ số | Có nghỉ 5 s giữa câu | Gọi liên tục |
|---|---|---|
| Trả lời được (status ok) | **100%** | 76,7% (7 câu dự phòng) |
| Có ≥ 1 trích dẫn đúng bài | 100% | 100% |
| Mọi trích dẫn thuộc bộ khối đúng | 86,7% | 90,0% |
| Còn khẳng định sai Engine sau kiểm | 0 | 0 |
| Có nhãn "Đã kiểm bằng Music Engine" | 23,3% | 26,7% |
| Độ trễ p50 / p95 / max | 1,51 s / **1,72 s** / 3,10 s | 1,35 s / 5,35 s / 16,9 s |
| Lượt gọi embedding / LLM ghi nhận | 127 / 31 | 127 / 31 |
| Đúng nhạc lý so với đáp án tham chiếu | **NOT EVALUATED** (cần người chấm; Đạt lấy mẫu 10 câu) | NOT EVALUATED |

Ghi chú:
- "Lượt gọi LLM ghi nhận" là tổng `tool_calls.llm_calls` mà dịch vụ lưu. Lần thử lại bằng mô hình dự phòng bên trong `GeminiProvider` không được đếm riêng.
- Nhãn Engine chỉ có ở 23,3% câu, vì nhãn chỉ gắn khi câu trả lời có ít nhất một khẳng định nhạc lý kiểm được và mọi khẳng định đều đúng. Câu thuần khái niệm (ví dụ "chức năng chủ là gì?") không có gì để kiểm, nên không có nhãn. Đây là đúng thiết kế, không phải lỗi.

**Ca thất bại:**
- Khi gọi liên tục: G17, G18, G20, G22 lỗi 503 (`unavailable`); G23, G24 lỗi 429 (`rate_limited`); G21 sai định dạng hai lần (`format_error`, 16,9 s). Cả 7 câu vẫn trả lời bằng trích đoạn bài học đúng bài.
- Trước GĐ4, câu dự phòng mở đầu bằng "Trợ lý AI đang tạm nghỉ", sai sự thật khi AI đang bật mà chỉ quá tải. Đã sửa: "tạm nghỉ" chỉ dùng khi `AI_ENABLED=false`; các trường hợp còn lại nói "chưa trả lời được lúc này" (test `test_fallback_lead_says_busy_unless_ai_disabled`).
- Trích dẫn ngoài bộ đúng (G02, G05, G17, G24): đều là khối cùng bài, hoặc khối liền kề ở bài trước có nội dung liên quan (G17 trích thêm `L03-B02`). Không có trích dẫn bịa: mọi `block_id` đều thuộc tập đã truy xuất ở lượt đó (luật GĐ3).

**Gợi ý cho buổi demo:** gói miễn phí không chịu được nhiều người hỏi cùng lúc. Hạn mức 30 lượt/người/ngày vẫn giữ, nhưng nên demo từng câu một, hoặc nâng gói. Phúc có thể chụp trang giới hạn của AI Studio để làm minh chứng.

---

## 3. Giới hạn (bắt buộc đọc)

1. **Mô phỏng chỉ chứng minh thuật toán chạy như thiết kế.** Nó không chứng minh hệ gợi ý giúp người thật học tốt hơn. Người mô phỏng do mình viết, theo các giả định trong docstring bộ sinh.
2. **Rủi ro vòng lặp (circularity).** Chân dung vừa quyết định hành vi (sở thích chọn bài, năng lực), vừa quyết định câu mục tiêu mà tầng nội dung dùng. Nếu tầng nội dung thắng trên dữ liệu này, đó có thể chỉ là do hai thứ cùng sinh ra từ một nguồn. Ở lần chạy này tầng nội dung không thắng, nên rủi ro không làm số đẹp lên, nhưng vẫn phải ghi.
3. **Không gian bài rất nhỏ** (4 bài học được). @5 bão hòa, mọi cấu hình đều `few_eligible`. Chỉ số có ý nghĩa là @1 và MRR.
4. 1.605/2.000 người không có đáp án chính sau mốc. Chỉ số chính dựa trên 395 người, khoảng tin cậy đã phản ánh cỡ mẫu này.
5. Người mô phỏng chọn bài theo θ ẩn, còn hệ gợi ý dùng mastery quan sát được. Khoảng cách giữa hai thứ đó chính là điều mục 1.6 đo được. Với người thật, khoảng cách có thể khác.
6. Bộ chuẩn RAG do Claude soạn và tự duyệt. "Đúng nhạc lý so với đáp án tham chiếu" chưa chấm.
7. Số liệu RAG là một lần chạy mỗi chế độ. Không lặp nhiều lần nên không có khoảng tin cậy cho độ trễ.

## 4. NOT EVALUATED

- Đúng nhạc lý của câu trả lời Gemini so với đáp án tham chiếu: cần người chấm (Đạt lấy mẫu 10 câu).
- Hiệu quả hệ gợi ý với người học thật: chưa có người dùng thật.
- So sánh 6 cấu hình ADR-008 với nhau: không phân biệt được trên dữ liệu hiện tại (mục 1.6). Cần chạy lại sau HM-013 hoặc sau khi Thắng chốt luật tiên quyết.
- Chặn câu ngoài phạm vi trên câu do người khác viết (bộ hiện tại do Claude viết).

## 5. File

- `scripts/ai/sim/nguoi_mo_phong.py`: bộ sinh người mô phỏng.
- `scripts/ai/evaluate_recommender.py` → `ket_qua_goi_y.json`.
- `scripts/ai/data/persona_goal_vectors.json`: vector mục tiêu của 4 chân dung.
- `scripts/ai/evaluate_rag.py` → `ket_qua_rag.json` (có nghỉ) và `ket_qua_rag_goi_lien_tuc.json` (gọi liên tục).
- `scripts/ai/data/rag_gold.json`: bộ chuẩn RAG.
- Sửa nhỏ: `app/ai/tutor/fallback.py` (thêm `BUSY`), `app/services/ai_tutor_service.py` (`offline_answer` chọn câu mở đầu theo lý do).
- Test: `backend/tests/test_ai_gd4_eval.py`, 8 test, không gọi mạng.
