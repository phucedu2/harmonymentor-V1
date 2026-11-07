# KẾ HOẠCH & PIPELINE TRIỂN KHAI HỆ THỐNG AI, RECOMMENDER & TÍNH NĂNG MỞ RỘNG
**Dự án HarmonyMentor AI (Nền tảng học nhạc lý thích ứng có trợ lý AI)**
**Phiên bản cập nhật:** 03/11/2026 • Chuẩn hóa theo SRS v2.1 & Định hướng Capstone

---

## TỔNG QUAN & NGUYÊN TẮC THIẾT KẾ

Tài liệu này xác định toàn bộ lộ trình và giải pháp kỹ thuật để triển khai hệ thống thông minh cho đồ án HarmonyMentor AI. Tài liệu phân định rạch ròi giữa **Hàm lượng học thuật AI/NLP** (phục vụ tiêu chí chấm điểm của 2 môn AI Fundamental & NLP) và **Kỹ thuật Phần mềm / Công nghệ Âm nhạc tương tác** (phục vụ trải nghiệm người dùng thực chiến và tạo điểm nhấn "WOW" khi bảo vệ trước hội đồng).

### 3 Nguyên tắc cốt lõi:
1. **Làm được thật (Feasible):** Sử dụng các công cụ kinh điển, ổn định (`scikit-learn`, `numpy`, Google Gemini API, Web Audio, Web MIDI API), chạy trơn tru trên cả môi trường SQLite local lẫn PostgreSQL Docker. Tránh các framework trung gian cồng kềnh, dễ vỡ.
2. **Hiểu bản chất để bảo vệ đồ án (Defensible):** Mọi thuật toán (Cosine similarity, KNN k=10, Markov Chain, Logistic Regression, RAG Prompt) đều có công thức minh bạch, sinh viên hiểu rõ từng dòng code để tự tin trả lời chất vấn của hội đồng.
3. **Phân định rõ ranh giới chuyên môn:** 
   - *Tính năng AI:* Trực tiếp giải quyết bài toán gợi ý, dự đoán, xử lý ngôn ngữ tự nhiên và cá nhân hóa.
   - *Tính năng Music Tech / UX:* Nâng tầm sản phẩm từ một bài tập lớn thành một ứng dụng thương mại hoàn chỉnh.

---

## MA TRẬN PHÂN LOẠI TÍNH NĂNG THEO MÔN HỌC & CÔNG NGHỆ

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                       HARMONYMENTOR HỆ THỐNG TỔNG THỂ                       │
├──────────────────────────────────────┬──────────────────────────────────────┤
│    KHỐI 1: HỌC THUẬT AI & NLP        │  KHỐI 2: KỸ THUẬT PHẦN MỀM & TECH    │
│  (Tiêu chí điểm AI & NLP: 4.0 điểm)  │  (Tiêu chí Phần mềm & UX: 6.0 điểm)  │
├──────────────────────────────────────┼──────────────────────────────────────┤
│ 1. Hệ gợi ý lai 3 tầng (AI Fund.)    │ 1. Music Theory Engine (Python thuần)│
│    - Lọc theo luật DAG (Rule-based)  │ 2. Web MIDI API (Cắm đàn thật USB)   │
│    - So khớp nội dung (Cosine NLP)   │ 3. Xuất file MIDI (.mid) & Sheet PDF │
│    - Lọc cộng tác KNN (k=10)         │ 4. So sánh âm thanh lỗi (Audio Diff) │
│ 2. AI Tutor RAG trích dẫn (NLP)      │ 5. Virtual Piano V2 & VexFlow Staff  │
│ 3. Phân tích cảm xúc lời nhạc (NLP)  │ 6. Harmony Lab 9 Styles (Tone.js)    │
│ 4. Dự đoán hợp âm tiếp (Markov/ML)   │ 7. Tap Tempo & Smart Transpose       │
│ 5. Dự đoán nguy cơ quên bài (ML)     │ 8. Docker 4 Services, CI & Middleware│
└──────────────────────────────────────┴──────────────────────────────────────┘
```

---

## HƯỚNG DẪN CHI TIẾT: CƠ CHẾ & PIPELINE XỬ LÝ DỮ LIỆU CỦA AI TỪNG BƯỚC (END-TO-END AI PROCESSING WORKFLOW)

Phần này trả lời trực tiếp cho câu hỏi: *"Dữ liệu đi qua AI như thế nào từ lúc người dùng thao tác đến khi nhận được kết quả?"*. Nhóm sử dụng phần này để trình bày luồng dữ liệu trước hội đồng.

```text
========================================================================================
LUỒNG 1: PIPELINE XỬ LÝ CỦA HỆ GỢI Ý BÀI HỌC (HYBRID RECOMMENDER PIPELINE)
========================================================================================

[Input Người Học]
 ├─ Mục tiêu tự do: "đệm hát pop guitar"
 ├─ Vector kỹ năng hiện tại: V = [0.2, 0.5, 0.0, ..., 0.8] (14 chiều)
 └─ Trạng thái ôn tập: Có thẻ L03 đến hạn (due = 1)
       │
       ▼
[BƯỚC 1: LỌC THEO LUẬT (Rule-based Filter)]
 ├─ Quét đồ thị DAG tiên quyết: Bài L04 cần L02 và L03 (ngưỡng >= 0.60).
 ├─ Kiểm tra: Kỹ năng của L02 đạt 0.65 (Đạt), L03 chỉ đạt 0.40 (Chưa đạt).
 └─ Kết quả Bước 1: Giữ lại [L01, L02, L03, L09, L10]. Loại L04 (chưa đủ điều kiện).
       │
       ▼
[BƯỚC 2: XỬ LÝ NLP & SO KHỚP NỘI DUNG (Content-based Matching)]
 ├─ Embedding mục tiêu: "đệm hát pop guitar" -> Vector E_goal (384 số thực).
 ├─ Cosine Similarity: So sánh E_goal với Vector mô tả từng bài trong kho.
 └─ Kết quả Bước 2: L10 (Vòng Pop) có Cosine = 0.58; L03 có Cosine = 0.42; L09 có Cosine = 0.31.
       │
       ▼
[BƯỚC 3: LỌC CỘNG TÁC BẰNG KNN (Collaborative Filtering)]
 ├─ Tìm láng giềng: Đưa vector 14 chiều V vào mô hình KNN (k=10) trên 2.000 user mô phỏng.
 ├─ Chọn 10 người có trình độ và sở thích gần nhất theo khoảng cách Cosine.
 ├─ Thống kê: Trong 10 người này, 6 người học tốt bài L10 tiếp theo (cf = 0.60); 5 người học L03 (cf = 0.50).
 └─ Kết quả Bước 3: Điểm cf(L10) = 0.60; cf(L03) = 0.50.
       │
       ▼
[BƯỚC 4: TÍNH ĐIỂM TỔNG HỢP & GIẢI THÍCH (Hybrid Scoring & Explainability)]
 ├─ Áp dụng công thức: Điểm = 0.35*Content + 0.25*(1-Mastery) + 0.20*Due + 0.20*CF.
 │   ├─ L10: 0.35*0.58 + 0.25*(1-0.10) + 0.20*0 + 0.20*0.60 = 0.548 (Hạng 1)
 │   └─ L03: 0.35*0.42 + 0.25*(1-0.20) + 0.20*1 + 0.20*0.50 = 0.447 (Hạng 2)
 └─ Bóc tách lý do: L10 có điểm Content và CF cao -> Lý do: "Phù hợp với mục tiêu đệm hát của bạn".
       │
       ▼
[Output Giao Diện]
 Dashboard hiển thị Top 3 bài học kèm nhãn huy hiệu xanh/tím và câu lý do minh bạch.

========================================================================================
LUỒNG 2: PIPELINE XỬ LÝ CỦA TRỢ LÝ AI TUTOR (RAG & GUARDRAIL PIPELINE)
========================================================================================

[Input Người Học]
 Gõ câu hỏi: "Hợp âm C7 khác Cmaj7 như thế nào?" (hoặc bấm "Giải thích lỗi này" từ câu sai)
       │
       ▼
[BƯỚC 1: TRUY XUẤT TRI THỨC BÀI HỌC (RAG Retrieval)]
 ├─ Vector hóa câu hỏi: E_query (384 số thực).
 ├─ Quét 60 chunks bài học trong bộ nhớ: Tính Cosine Similarity(E_query, Chunk).
 ├─ Lọc ngưỡng tự tin: Lấy 4 chunks có điểm cao nhất (ví dụ Chunk L02_Sec3 có điểm 0.72 >= 0.35).
 └─ Kết quả Bước 1: Trích xuất trọn vẹn 4 đoạn lý thuyết về quãng 7 và hợp âm 7.
       │
       ▼
[BƯỚC 2: ĐÓNG GÓI NGỮ CẢNH (Context Assembly)]
 ├─ Ghép: System Prompt (luật sư phạm, không cho đáp án trực tiếp, bắt buộc JSON).
 ├─ Kèm: 4 chunks tri thức vừa tìm được.
 ├─ Kèm: Lịch sử 6 tin nhắn gần nhất từ Redis/DB để nhớ ngữ cảnh.
 └─ Kèm (nếu có): Mã lỗi thực tế từ Music Engine (ví dụ: SEVENTH_QUALITY).
       │
       ▼
[BƯỚC 3: SUY LUẬN BẰNG GOOGLE GEMINI (LLM Inference)]
 ├─ Gọi API Gemini 1.5 Flash -> Trả về chuỗi JSON theo cấu trúc nghiêm ngặt:
 └─ JSON: {
       "explanation": "Cmaj7 dùng quãng 7 trưởng (B), còn C7 dùng quãng 7 thứ (Bb)...",
       "citations": [{"lesson_id": "L02", "section": "Hợp âm 7"}],
       "music_claims": ["Cmaj7 gồm C E G B", "C7 gồm C E G Bb"]
    }
       │
       ▼
[BƯỚC 4: THẨM ĐỊNH SỰ THẬT BẰNG MUSIC ENGINE (Guardrail Validation)]
 ├─ Backend bóc tách mảng `music_claims`:
 │   ├─ Gửi "Cmaj7 gồm C E G B" vào Music Engine -> Engine báo ĐÚNG.
 │   └─ Gửi "C7 gồm C E G Bb" vào Music Engine -> Engine báo ĐÚNG.
 └─ Nếu có claim sai (AI bịa nốt): Hủy câu trả lời AI, thay bằng template câu giải thích chuẩn.
       │
       ▼
[BƯỚC 5: CẬP NHẬT PHIÊN & TRẢ VỀ GIAO DIỆN (Session Update & Display)]
 ├─ Lưu tin nhắn người dùng và câu trả lời vào Redis / CSDL.
 └─ Trả về Frontend: Khung chat nổi hiển thị câu trả lời + Thẻ trích dẫn bài học clickable.
```

### Bảng tóm tắt biến đổi dữ liệu (Data Transformation Matrix)

| Giai đoạn | Dữ liệu đầu vào | Kỹ thuật / Thuật toán xử lý | Dữ liệu đầu ra |
| :--- | :--- | :--- | :--- |
| **Gợi ý - Tầng 1** | Cây tiên quyết + Mastery user | Thuật toán duyệt đồ thị DAG + Lọc ngưỡng ($0.60 / 0.80$) | Danh sách bài học ứng viên hợp lệ |
| **Gợi ý - Tầng 2** | Văn bản mục tiêu tự do | Mô hình Embedding + Cosine Similarity | Vector tương đồng nội dung $\text{content} \in [0, 1]$ |
| **Gợi ý - Tầng 3** | Vector 14 nhóm kỹ năng | K-Nearest Neighbors ($K=10$, metric='cosine') trên 2.000 user | Tỷ lệ thành công cộng đồng $\text{cf} \in [0, 1]$ |
| **Gợi ý - Tổng hợp**| Các điểm thành phần | Công thức trung bình có trọng số ($0.35, 0.25, 0.20, 0.20$) | Top 3-5 bài học đề xuất + Lý do minh bạch |
| **AI Tutor - RAG** | Câu hỏi của học viên | Embedding câu hỏi + Cosine quét chunks ($\text{ngưỡng} \ge 0.35$) | Top 4 đoạn ngữ cảnh lý thuyết chính xác |
| **AI Tutor - LLM** | Prompt ráp ngữ cảnh + Lịch sử | Google Gemini API (Inference có ép kiểu JSON Schema) | Chuỗi JSON: Lời giải thích, trích dẫn, nhạc lý |
| **AI Tutor - Guard**| Mảng khẳng định `music_claims` | Music Theory Engine (Hàm kiểm tra hợp âm và quãng) | Kết quả kiểm duyệt: Chấp thuận hoặc Kích hoạt Fallback |

---

## PHẦN 1: PIPELINE HỆ GỢI Ý BÀI HỌC CỐT LÕI (HYBRID RECOMMENDER)
*(Môn AI Fundamental • Đáp ứng FR-11)*

### 1.1 Biểu diễn vector 14 nhóm kỹ năng (14-Group Feature Vector)
Theo SRS 4.4 và tài liệu Thiết kế chi tiết 6.5, toàn bộ kỹ năng nhạc lý của hệ thống được gom vào 14 nhóm kỹ năng đại diện:
1. `note_reading`: Đọc tên nốt và phím đàn.
2. `interval_calc`: Tính toán quãng và nửa cung.
3. `triad_build`: Cấu tạo hợp âm 3 nốt.
4. `seventh_build`: Cấu tạo hợp âm 7.
5. `scale_major`: Âm giai trưởng.
6. `scale_minor`: Âm giai thứ.
7. `roman_numeral`: Phân tích số La Mã.
8. `cadence`: Các bước kết và tiến trình hòa âm cơ bản.
9. `secondary_dominant`: Hợp âm át phụ.
10. `modal_interchange`: Hợp âm mượn.
11. `jazz_voicing`: Thế bấm Jazz piano (Shell voicing).
12. `voice_leading`: Dẫn giọng và nốt chung.
13. `rhythm_basic`: Tiết tấu, nhịp và phách.
14. `song_form`: Cấu trúc bài hát (Verse/Chorus/Bridge).

- **Biểu diễn người học:** Mỗi người học được đại diện bằng một vector $V \in \mathbb{R}^{14}$, trong đó mỗi phần tử $V_i \in [0.0, 1.0]$ là giá trị trung bình điểm thành thạo (EMA) của các kỹ năng con thuộc nhóm $i$.
- **Khởi tạo:** Người học mới có vector toàn số $0.0$.

### 1.2 Cài đặt thuật toán gợi ý lai 3 tầng (`recommendation_service.py`)
File cài đặt: `backend/app/services/recommendation_service.py`

#### Tầng 1: Lọc theo luật sư phạm (Rule-based Filtering)
- **Đầu vào:** Danh sách 12 bài học, đồ thị tiên quyết (DAG).
- **Điều kiện loại trừ:**
  - Loại bỏ bài học nếu tất cả kỹ năng trong bài đã đạt ngưỡng thành thạo ($\ge 0.80$).
  - Loại bỏ bài học nếu có bất kỳ kỹ năng tiên quyết nào chưa đạt ngưỡng đủ điều kiện học tiếp ($< 0.60$).
- **Đầu ra:** Danh sách các bài học ứng viên hợp lệ.

#### Tầng 2: So khớp nội dung theo mục tiêu (Content-based Matching)
- **Đầu vào:** Văn bản mục tiêu của người học (ví dụ: *"Học đệm hát pop trên đàn guitar"*).
- **Xử lý:**
  - Chuyển văn bản mục tiêu thành vector embedding $E_{goal}$ bằng mô hình embedding (sử dụng Gemini `text-embedding-004` hoặc `all-MiniLM-L6-v2` 384 chiều).
  - Tính độ tương đồng Cosine giữa $E_{goal}$ và vector mô tả nội dung của từng bài học $E_{lesson}$:
    $$\text{content} = \frac{E_{goal} \cdot E_{lesson}}{\|E_{goal}\| \|E_{lesson}\|}$$
- **Đầu ra:** Điểm $\text{content} \in [0.0, 1.0]$ cho từng bài học.

#### Tầng 3: Lọc cộng tác dựa trên láng giềng (Collaborative Filtering với KNN)
- **Thuật toán:** K-Nearest Neighbors với $K=10$, sử dụng độ đo khoảng cách Cosine từ thư viện `sklearn.neighbors.NearestNeighbors`:
  ```python
  knn = NearestNeighbors(n_neighbors=10, metric='cosine')
  knn.fit(X_synthetic_matrix) # Ma trận dữ liệu người học mô phỏng
  ```
- **Xử lý:**
  - Đưa vector 14 chiều của người học hiện tại vào mô hình để tìm ra 10 người học có trình độ và thiên hướng tương đồng nhất.
  - Điểm cộng tác $\text{cf}$ của một bài học là tỷ lệ phần trăm số người trong 10 láng giềng này đã hoàn thành tốt bài học đó ở bước tiếp theo.
- **Đầu ra:** Điểm $\text{cf} \in [0.0, 1.0]$.

#### Công thức điểm tổng hợp (Hybrid Scoring Formula)
Với mỗi bài học ứng viên:
$$\text{Score} = 0.35 \times \text{content} + 0.25 \times (1 - \text{mastery}) + 0.20 \times \text{due} + 0.20 \times \text{cf}$$
- Trong đó:
  - $\text{mastery}$: Điểm thành thạo hiện tại của các kỹ năng trong bài.
  - $\text{due} = 1$ nếu bài có thẻ flashcard đến hạn ôn tập, ngược lại bằng $0$.
  - Nếu là người học mới chưa có lịch sử, bỏ tầng 3 và gộp trọng số sang tầng nội dung: $\text{Score} = 0.55 \times \text{content} + 0.25 \times (1 - \text{mastery}) + 0.20 \times \text{due}$.

#### Sinh lý do gợi ý minh bạch (Explainability)
Hệ thống chọn lý do dựa trên thành phần đóng góp điểm cao nhất:
- Nếu điểm `content` chiếm ưu thế: *"Rất phù hợp với mục tiêu 'đệm hát pop' của bạn."*
- Nếu điểm `due` chiếm ưu thế: *"Đã đến lịch ôn tập để không quên kiến thức."*
- Nếu điểm `1 - mastery` chiếm ưu thế: *"Giúp bạn củng cố kỹ năng còn yếu."*
- Nếu điểm `cf` chiếm ưu thế: *"Được nhiều người học có trình độ tương đương lựa chọn tiếp theo."*

### 1.3 Script sinh dữ liệu mô phỏng & Đánh giá Offline
Tệp thực thi: `scripts/ai/evaluate_recommender.py`
- **Tạo 2.000 hồ sơ người học mô phỏng (Synthetic Learners):** Phân bổ đều theo 4 chân dung học tập: Pop, Guitar, Jazz, Newbie.
- **Phương pháp kiểm thử (Offline Evaluation):**
  - Giữ lại 20% lịch sử tương tác cuối của 2.000 người học làm tập Test.
  - Chạy mô hình gợi ý trên 80% lịch sử đầu và so sánh Top-5 bài đề xuất với bài học thực tế người học đã chọn.
  - Tính toán hai thước đo kinh điển: **`HitRate@5`** và **`Precision@5`**.
- **Đối sánh 3 phương án để đưa vào báo cáo và slide:**
  1. *Chỉ lọc theo luật (Rule-only)*.
  2. *Luật + So khớp nội dung (Rule + Content)*.
  3. *Hệ gợi ý lai 3 tầng (Rule + Content + KNN)*.

---

## PHẦN 2: PIPELINE TRỢ LÝ AI TUTOR CỐT LÕI (RAG CHATBOT)
*(Môn NLP • Đáp ứng FR-12, FR-13)*

### 2.1 Chuẩn bị tri thức bài học (Lesson Knowledge Chunks)
- Trích xuất lý thuyết trực tiếp từ `backend/app/content/curriculum_specs.py`.
- Quy cách phân đoạn: Mỗi đoạn dài 80–120 từ, kèm metadata: `chunk_id`, `lesson_id`, `section_title`, `text`.
- Vector hóa sẵn và lưu vào `backend/app/content/lesson_embeddings.json`. Tìm kiếm Cosine Similarity diễn ra trong bộ nhớ cực nhanh dưới 5 ms.

### 2.2 Bộ truy xuất tài liệu (RAG Retriever) & Ngưỡng tự tin
Khi người học đặt câu hỏi:
1. Vector hóa câu hỏi của người học.
2. Tính độ tương đồng Cosine giữa vector câu hỏi và các chunks bài học.
3. Lấy Top 4 chunks có điểm tương đồng cao nhất.
4. **Cơ chế lọc ngưỡng tự tin:** Nếu chunk cao nhất có độ tương đồng $< 0.35$, hệ thống chủ động phản hồi câu an toàn, không để mô hình bịa đặt kiến thức ngoài chương trình.

### 2.3 Gọi Google Gemini API với JSON Schema chặt chẽ
Tệp thực thi: `backend/app/services/ai_tutor_service.py`
- Sử dụng mô hình `gemini-1.5-flash` hoặc `gemini-2.0-flash` thông qua API Key.
- Yêu cầu cấu trúc JSON đầu ra bắt buộc:
```json
{
  "intent": "ask_concept | explain_error | greeting",
  "explanation": "Lời giải thích sư phạm, thân thiện, mang tính gợi mở, không đưa đáp án trực tiếp",
  "citations": [
    {
      "lesson_id": "L01",
      "section": "Quãng 3 trưởng và quãng 3 thứ"
    }
  ],
  "music_claims": [
    "Hợp âm C major gồm 3 nốt C, E, G",
    "Quãng 3 trưởng gồm 4 nửa cung"
  ]
}
```

### 2.4 Cơ chế kiểm tra chéo với Music Engine (Guardrail)
- Backend duyệt mảng `music_claims`: Tách các khẳng định về nốt, quãng, hợp âm và gửi vào các hàm thẩm định của `Music Engine`.
- Nếu AI bịa đặt nhạc lý sai lệch: Tự động thay thế bằng câu giải thích chuẩn xác định nghĩa sẵn trong từ điển mã lỗi (`backend/app/music_engine/errors.py`).

### 2.5 Bộ nhớ phiên hội thoại (Sliding Window Memory)
- Lưu trữ 6 tin nhắn gần nhất (3 lượt hỏi - 3 lượt đáp) cho mỗi `session_id`.
- Nối vào ngữ cảnh đàm thoại để AI hiểu đại từ thay thế và ngữ cảnh trao đổi liền mạch.

### 2.6 Tính năng "Giải thích câu trả lời sai" (Explain Error Flow)
Khi làm sai câu hỏi:
- Người học bấm **"Giải thích lỗi này"**.
- Backend gửi mã lỗi thực tế (`SEVENTH_QUALITY`, `WRONG_ROOT`...) kèm đề bài vào prompt để AI Tutor tạo gợi ý gợi mở mức độ 1 giúp người học tự sửa.

---

## PHẦN 3: CÁC TÍNH NĂNG AI & NLP MỞ RỘNG (NÂNG CAO HỌC THUẬT)
*(Các tính năng nâng cao khẳng định năng lực chuyên sâu về AI & Machine Learning)*

```text
┌─────────────────────────────────────────────────────────────┐
│              CÁC TÍNH NĂNG AI & NLP MỞ RỘNG                 │
├──────────────────────────────┬──────────────────────────────┤
│       MÔN NLP MỞ RỘNG        │   MÔN AI FUNDAMENTAL MỞ RỘNG │
├──────────────────────────────┼──────────────────────────────┤
│ 1. Lyrics-to-Harmony         │ 3. Next-Chord Predictor      │
│    (Phân tích cảm xúc lời)   │    (Mô hình Markov Chain)    │
│ 2. Semantic Search bài học   │ 4. Retention Predictor       │
│    (Tìm kiếm bằng ngữ nghĩa) │    (Mô hình phân loại ML)    │
└──────────────────────────────┴──────────────────────────────┘
```

### 3.1 Phân tích cảm xúc lời bài hát để gợi ý hòa âm (Lyrics-to-Harmony) — *Môn NLP*
- **Ý nghĩa bài toán:** Người học viết một đoạn thơ hoặc lời bài hát tiếng Việt, hệ thống dùng NLP để phân tích cảm xúc và tự động đề xuất vòng hòa âm phù hợp.
- **Quy trình kỹ thuật:**
  1. *Sentiment & Mood Analysis:* Dùng prompt chuyên dụng phân loại cảm xúc văn bản: *U sầu / Hoài niệm / Tươi sáng / Kịch tính / Lãng mạn*.
  2. *Tone & Rhythm Mapping:* Cảm xúc buồn $\rightarrow$ Gợi ý Tone thứ (A minor / D minor) với tempo chậm (Ballad 70–80 BPM); Cảm xúc vui tươi $\rightarrow$ Gợi ý Tone trưởng (C major / G major) với tempo nhanh (Pop 100–120 BPM).
  3. *Harmonic Progression:* Tự động điền vòng hợp âm tương ứng vào Harmony Lab để người dùng nghe thử.
- **Giá trị học thuật:** Kết hợp hoàn hảo giữa **Xử lý ngôn ngữ tự nhiên (NLP Text Analysis)** và **Công nghệ âm nhạc**.

### 3.2 Tìm kiếm bài học bằng ngôn ngữ tự nhiên (Semantic Search) — *Môn NLP*
- **Ý nghĩa bài toán:** Người học không nhớ tên bài học, chỉ nhớ nhu cầu cụ thể (ví dụ: *"làm sao để chuyển đoạn nghe bất ngờ?"* hoặc *"hợp âm nào nghe buồn như nhạc indie?"*).
- **Quy trình kỹ thuật:**
  1. Chuyển câu truy vấn tự do thành vector embedding.
  2. Quét toàn bộ kho tri thức bài học để tính Cosine Similarity.
  3. Trả về đúng khối bài học (ví dụ: L05 Hợp âm át phụ hoặc L06 Hợp âm mượn).
- **Giá trị học thuật:** Trực tiếp áp dụng kiến thức **Vector Spaces & Semantic Information Retrieval**.

### 3.3 Dự đoán hợp âm tiếp theo (Next-Chord Predictor) — *Môn AI Fundamental*
- **Ý nghĩa bài toán:** Hỗ trợ người dùng trong Harmony Lab tương tự như tính năng đoán từ tiếp theo trên bàn phím điện thoại.
- **Quy trình kỹ thuật:**
  1. Xây dựng **Mô hình chuỗi Markov (Markov Chain)** hoặc **Decision Tree** trên tập dữ liệu 500 vòng hợp âm chuẩn của các ca khúc phổ biến.
  2. Khi người dùng chọn hợp âm `C` rồi đến `Am`, mô hình tính toán phân phối xác suất chuyển trạng thái $P(\text{Chord}_{t+1} \mid \text{Chord}_t)$:
     - `F`: 45% (vòng phổ thông Pop).
     - `Dm`: 30% (vòng $ii-V$).
     - `Em`: 15% (vòng cổ điển).
  3. Hiển thị thanh gợi ý trực quan phía trên ô nhịp tiếp theo.
- **Giá trị học thuật:** Minh chứng xuất sắc cho **Mô hình học máy xác suất (Probabilistic Graphical Models)** của môn AI Fundamental.

### 3.4 Mô hình dự đoán nguy cơ quên bài (Knowledge Retention Predictor) — *Môn AI Fundamental*
- **Ý nghĩa bài toán:** Phát hiện sớm các kỹ năng mà người học có nguy cơ quên cao để đưa vào lịch ôn tập chủ động.
- **Quy trình kỹ thuật:**
  1. Dùng thuật toán **Học có giám sát (Supervised Learning - Logistic Regression hoặc Random Forest)** trong `scikit-learn`.
  2. Đặc trưng đầu vào (Features):
     - Số ngày trôi qua từ lần luyện tập gần nhất ($x_1$).
     - Điểm thành thạo EMA hiện tại ($x_2$).
     - Tỷ lệ câu sai trong lịch sử ($x_3$).
     - Thời gian phản hồi trung bình `response_time_ms` ($x_4$).
  3. Nhãn mục tiêu (Target): $y \in \{0, 1\}$ (1: Quên kiến thức / Trả lời sai ở lần ôn tới).
  4. Hệ thống cảnh báo khi xác suất quên $> 0.65$ và tự động ghim thẻ lên đầu danh sách ôn tập.
- **Giá trị học thuật:** Giúp đồ án có đầy đủ cả hai nhánh kinh điển: **Supervised Learning (Classification)** và **Unsupervised/Neighborhood Learning (KNN)**.

---

## PHẦN 4: CÁC TÍNH NĂNG KỸ THUẬT PHẦN MỀM & CÔNG NGHỆ ÂM NHẠC MỞ RỘNG (TẠO ĐIỂM NHẤN "WOW")
*(Khẳng định chất lượng sản phẩm phần mềm thực chiến, tương tác cao)*

### 4.1 Hỗ trợ Web MIDI API (Cắm đàn Piano điện/Organ thật vào máy tính)
- **Cơ chế:** Tích hợp `navigator.requestMIDIAccess()` trực tiếp trên trình duyệt Chrome/Edge.
- **Trải nghiệm:** Người học cắm cáp USB từ đàn piano điện vào máy tính. Khi bấm phím đàn thật bên ngoài:
  - Phím trên `VirtualPiano` trên web phát sáng tương ứng.
  - Tự động nhận diện hợp âm/quãng và gửi lên server chấm điểm.
- **Độ phức tạp:** Rất thấp (khoảng 40 dòng JavaScript/TypeScript), nhưng mang lại hiệu ứng trình diễn cực kỳ ấn tượng trong buổi bảo vệ.

### 4.2 Xuất bản sáng tác ra file MIDI (.mid) & Sheet nhạc PDF
- **Cơ chế:** 
  - Tại Harmony Lab, bổ sung nút **"Xuất file MIDI (.mid)"** sử dụng thư viện `midi-writer-js` (frontend) hoặc `mido` (backend).
  - Bổ sung nút **"In bản nhạc PDF"** xuất từ SVG khuông nhạc VexFlow.
- **Trải nghiệm:** Người dùng có thể kéo file `.mid` vừa sáng tác vào các phần mềm hòa âm chuyên nghiệp (FL Studio, Ableton Live, GarageBand) hoặc in ra giấy để tập đàn.

### 4.3 Nghe đối chiếu lỗi sai âm thanh (Audio Error Diff)
- **Cơ chế:** Khi người học làm sai một hợp âm (ví dụ `G B D F#` thay vì `G B D F`):
  - Giao diện cung cấp 2 nút nghe: **"Âm thanh bạn đã chọn"** (nghe chói gắt, sai luật) và **"Âm thanh chuẩn"** (nghe êm ái, đúng tính chất hòa âm).
- **Trải nghiệm:** Giúp người học dùng đôi tai để cảm nhận lỗi sai thay vì chỉ đọc thông báo chữ khô khan.

### 4.4 Tiện ích thông minh: Tap Tempo & Smart Transpose
- **Tap Tempo:** Người dùng nhấp phím cách (`Spacebar`) 4 lần theo nhịp điệu bài hát đang ấp ủ, hệ thống tự động tính toán ra giá trị BPM chính xác cho dự án.
- **Smart Transpose:** Nút chuyển giọng bài hát tăng/giảm nửa cung thông minh (giữ nguyên cấu trúc hòa âm) để phù hợp với tông giọng của từng người hát.

---

## PHẦN 5: GIAO DIỆN FRONTEND TINH GỌN (REACT / TAILWIND)

Triển khai hai thành phần trực quan trên frontend:

### 5.1 Khung trợ lý ảo nổi (`FloatingTutorDrawer.tsx`)
- Biểu tượng nút tròn cố định ở góc dưới bên phải màn hình tại các trang học tập (`/app/*`).
- Bấm vào sẽ mở ngăn trượt (Drawer) chứa khung hội thoại:
  - Danh sách tin nhắn phân biệt rõ người gửi (Người học / AI Tutor).
  - Thẻ trích dẫn bài học (Citations): Hiển thị mã bài và mục bài học có liên kết clickable để mở nhanh bài học tham chiếu.
  - Trạng thái chờ trả lời (Loading skeleton) mượt mà dưới 2 giây.

### 5.2 Thẻ bài học gợi ý trên Dashboard (`RecommendedLessons.tsx`)
- Tích hợp trực tiếp vào trang `frontend/src/pages/Dashboard.tsx`.
- Hiển thị danh sách 3 bài học được gợi ý nhiều điểm nhất.
- Mỗi bài học đi kèm một huy hiệu (Badge) nêu rõ lý do: *"Theo mục tiêu"*, *"Cần ôn tập"*, *"Phù hợp trình độ"*.

---

## PHẦN 6: KẾ HOẠCH HÀNH ĐỘNG THEO 2 GIAI ĐOẠN

### Giai đoạn 1: Tập trung 100% Lõi AI/NLP cho mốc kiểm tra 10/11/2026
*Mục tiêu: Đạt điểm tối đa cho 2 môn AI Fundamental & NLP theo đúng cam kết SRS.*

| Ngày | Phụ trách | Nhiệm vụ kỹ thuật chi tiết | Sản phẩm bàn giao (Deliverable) |
| :--- | :--- | :--- | :--- |
| **04/11** | **Đạt** | Viết module `recommendation_service.py` (3 tầng: Luật + Cosine Goal + KNN 14 chiều). | Service vượt qua unit test với dữ liệu thử nghiệm. |
| **05/11** | **Đạt** | Viết script `scripts/ai/evaluate_recommender.py` sinh 2.000 user mô phỏng và đo HitRate@5 / Precision@5. | Bảng số liệu đối sánh 3 phương án gợi ý cho slide báo cáo. |
| **06/11** | **Thắng** | Xây dựng API `GET /api/v1/recommend` và `PUT /api/v1/me/goal` trong FastAPI. | API trả về danh sách 3 bài học kèm lý do theo chuẩn JSON. |
| **07/11** | **Đạt** | Viết module RAG `ai_tutor_service.py`: phân đoạn bài học, tính embedding và gọi Gemini sinh JSON. | Hàm hỏi đáp trả về câu trả lời có trích dẫn đúng bài học. |
| **08/11** | **Thắng & Phúc** | Thắng tạo router `/api/v1/chat/message`. Phúc dựng giao diện `FloatingTutorDrawer.tsx` trên React. | Người học có thể chat và nhận câu trả lời trực tiếp trên giao diện web. |
| **09/11** | **Cả nhóm** | Tích hợp nút "Giải thích lỗi này" vào bài tập. Chạy kiểm thử chéo toàn hệ thống. | Luồng học $\rightarrow$ làm bài sai $\rightarrow$ AI giải thích hoạt động trơn tru. |
| **10/11** | **Cả nhóm** | Rà soát tiêu chí đánh giá, hoàn thiện tài liệu minh chứng cho mốc kiểm tra Giai đoạn 1. | Hoàn thành mốc Giai đoạn 1, tự tin đạt điểm xuất sắc ($\ge 9.0/10$). |

### Giai đoạn 2: Phát triển Tính năng AI mở rộng & Music Tech "WOW" (11/11 – 04/12/2026)
*Mục tiêu: Hoàn thiện sản phẩm đỉnh cao để bảo vệ trước Hội đồng tốt nghiệp.*

| Tuần | Phụ trách | Nhiệm vụ kỹ thuật mở rộng | Giá trị gia tăng cho đồ án |
| :--- | :--- | :--- | :--- |
| **Tuần 1 (11–17/11)** | **Phúc** | Tích hợp **Web MIDI API** (kết nối đàn thật) và tiện ích **Tap Tempo**. | Tạo điểm nhấn tương tác trực tiếp cực mạnh khi demo. |
| **Tuần 2 (18–24/11)** | **Thắng** | Triển khai tính năng **Xuất file MIDI (.mid)** và in Sheet PDF từ Harmony Lab. | Đưa sản phẩm vào ứng dụng thực tế cho nhạc sĩ/sinh viên. |
| **Tuần 3 (25/11–01/12)**| **Đạt** | Triển khai tính năng **Lyrics-to-Harmony** (NLP phân tích lời thơ/nhạc) và **Next-Chord Predictor**. | Nâng tầm học thuật môn AI và NLP lên mức xuất sắc toàn diện. |
| **Tuần 4 (02–04/12)** | **Cả nhóm** | Đóng gói Docker hoàn chỉnh, tổng duyệt kịch bản demo 15 phút, sẵn sàng bảo vệ. | Tự tin đạt điểm Thủ khoa / Á khoa đồ án cuối khóa. |
