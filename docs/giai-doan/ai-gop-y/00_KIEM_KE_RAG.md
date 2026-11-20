# GĐ0. Kiểm kê hệ thống RAG của AI Tutor (trả lời góp ý G4 của thầy)

Ngày chạy: 06/11/2026, nhánh `ai-gop-y/gd0-kiem-ke` tách từ `phuc-music` (7c9408f).
Người làm: Claude. Người duyệt: Phúc (chủ AI Tutor), Thắng (backend), Đạt (nội dung).

Lệnh tái lập (máy cloud, không cần khóa Gemini):

```bash
cd backend
pip install -r requirements.txt sentence-transformers   # sentence-transformers chỉ để đo, chưa vào requirements
python ../scripts/ai/gop_y/gd0_kiem_ke.py --out ../docs/giai-doan/ai-gop-y/gd0_ket_qua.json
python -m pytest -q          # 928 passed, 43 skipped (06/11/2026, trước khi sửa gì)
```

Số liệu thô: [`gd0_ket_qua.json`](gd0_ket_qua.json). Câu dò: `scripts/ai/data/gd0_cau_do_luong.json`
(24 câu Claude soạn, nháp, chưa người duyệt, chỉ để minh họa lỗ hổng, không dùng làm bộ test khóa).

---

## 1. Đã làm gì

- Đọc lại toàn bộ đường đi của một câu hỏi trong code (`api/ai_tutor.py` → `services/ai_tutor_service.py` →
  `ai/tutor/*`) và vẽ lại theo code thật, không theo pipeline trên giấy (mục 2).
- Kiểm kê 45 đoạn của kho: số từ, số token theo bộ tách từ của 2 mô hình nhúng mở, trùng lặp, nguồn, trạng thái
  duyệt, đoạn nhắc trước khái niệm bài sau (mục 3).
- Đo lại truy xuất trên bộ chuẩn GĐ4 (30 câu + 5 câu demo) cho BM25 (đường đang chạy khi không có khóa) và 2 mô
  hình mở chạy CPU, chưa fine-tune (mục 4).
- Chạy đúng hàm `answer_question` của dịch vụ trên 24 câu dò thuộc 5 loại (A/B/C/D/chào hỏi) để xem hôm nay hệ
  thống làm gì với từng loại (mục 5).
- Tìm ra nguyên nhân lỗi đã biết "hỏi C7 khác Cmaj7 lại trích L03" và liệt kê 10 lỗ hổng theo mức ảnh hưởng (mục 6).

## 2. Một câu hỏi đi qua hệ thống thế nào (theo code)

```
Người học gõ câu hỏi (khung chat)
  │  POST /api/v1/chat/message
  ▼
handle_message: lưu tin nhắn người học, lấy 6 tin gần nhất của phiên
  ▼
answer_question
  ├─(1) looks_like_injection? ──có──► trả câu INJECTION, không gọi gì thêm
  ├─(2) classify (TF-IDF ký tự + LogisticRegression, 6 ý định)
  │      out_of_scope và độ tin ≥ 0,5 ──► trả OUT_OF_SCOPE
  ├─(3) retrieve top 4
  │      có khóa: Gemini embedding câu hỏi · cosine với 45 vector đoạn · giữ đoạn ≥ 0,60
  │      KHÔNG khóa (hiện tại): BM25 · giữ đoạn có điểm ≥ 2,0
  │      out_of_scope (độ tin < 0,5) mà không có đoạn ──► OUT_OF_SCOPE
  ├─(4) engine_facts_for: tìm KÝ HIỆU HỢP ÂM trong câu (regex) · gọi get_chord_tones
  ├─(5) không có đoạn VÀ không có dữ kiện ──► UNSURE + gợi ý bài gần nhất
  ├─(6) không có LLM (AI tắt hoặc thiếu khóa) ──► offline_answer: trích nguyên văn đoạn tìm được
  ├─(7) hết ngân sách ngày ──► offline_answer · hết lượt người học ──► 429
  └─(8) gọi Gemini với prompt (luật + đoạn + dữ kiện Engine + 6 tin cũ), JSON schema
         ├─ guardrail: kiểm mọi khẳng định nhạc lý bằng Music Engine, chỉ nhận trích dẫn có trong đoạn đã gửi
         ├─ sai → thử lại 1 lần với lời sửa
         └─ vẫn sai → offline_answer
  ▼
_save: lưu câu trả lời + tool_calls (ý định, điểm truy xuất, dữ kiện Engine, lời gọi LLM)
```

Điểm quan trọng nhất của sơ đồ: **ở bước (8), nếu có đoạn tìm được hoặc có dữ kiện Engine, hệ thống luôn gọi
LLM**. Không có bước nào hỏi "đoạn tìm được có thật sự trả lời câu này không". Thầy lo đúng chỗ này (G1).

## 3. Dữ liệu trong kho

### 3.1 Theo bài

| Bài | Trạng thái | Số khối | Số đoạn | Tổng từ | Từ ít nhất / trung vị / nhiều nhất |
|---|---|---|---|---|---|
| L01 | reviewed | 7 | 16 | 1.150 | 37 / 78 / 96 |
| L02 | reviewed | 7 | 10 | 444 | 9 / 35 / 87 |
| L03 | reviewed | 7 | 9 | 401 | 9 / 35 / 88 |
| L04 | reviewed | 8 | 10 | 524 | 5 / 58 / 88 |
| L05–L08 | source_audited | 0 | 0 | 0 | — |
| **Tổng** | | 29 | **45** | **2.519** | |

L05–L08 có câu bài tập nhưng 0 khối lý thuyết. L09–L12 là nháp nên chunker bỏ qua (đúng thiết kế).
**Không bài nào ở trạng thái `published`** (quyết định 9A: tạm cho `reviewed` vào kho, ghi ADR-017).

### 3.2 Chất lượng đoạn

| Chỉ số | Kết quả | Nhận xét |
|---|---|---|
| Đoạn đúng khoảng 80–100 từ | 15/45 (33%) | Quy tắc "80–100 từ" chỉ đúng cho 1/3 kho |
| Đoạn dưới 60 từ | 22/45 | Phần lớn là đuôi khối hoặc khối ngắn (chú thích ảnh, ví dụ) |
| Đoạn dưới 30 từ | 11/45 | Ví dụ `L04-B04#1` chỉ 5 từ: "Dm7 → G7 → Cmaj7" |
| Đoạn trên 100 từ | 0 | |
| Đoạn rỗng | 0 | |
| Trùng chính xác (cùng hash) | 0 | |
| Gần trùng (Jaccard 5-gram ≥ 0,6 giữa hai khối) | 0 | |
| Token (MiniLM L12): trung vị / lớn nhất | 119 / 195 | **21/45 đoạn vượt 128 token**, phần đuôi bị mô hình bỏ qua |
| Token (e5-small): trung vị / lớn nhất | 121 / 197 | Giới hạn 512, không đoạn nào vượt |
| `max_seq_length` đo thật | MiniLM 128 · e5-small 512 | Xác nhận lý do chọn 2A |

**Nguồn:** mỗi đoạn mang nguồn của **cả bài** (ghép mọi nguồn trong `sources`), không phải nguồn của khối đó. Ví dụ
mọi đoạn L04 đều ghi cùng một chuỗi gồm OMT, Terefenko và sách Trần Khải Hoàn. Như vậy câu trả lời trích một đoạn
L04 cũng "kèm" tên một sách chỉ được tham khảo, dù đoạn đó có thể diễn đạt từ OMT.

**Đoạn nhắc khái niệm mà bài sau mới dạy** (dò bằng từ khóa, cần Đạt xác nhận):

| Đoạn | Nhắc tới | Bài dạy |
|---|---|---|
| L01-B01#1, L01-B08#1, L01-B12#1 | âm giai | L02 |
| L02-B05#1, L02-B05#2 | chức năng | L03 |
| L03-B07#1 | ii–V–I | L04 |
| L04-B02#3 | shell voicing | L08 |

Phần lớn là nhắc trước có chủ ý ("bài sau sẽ học"). Rủi ro chỉ ở chỗ truy xuất có thể chọn đoạn nhắc trước thay
cho đoạn dạy chính.

## 4. Đo lại truy xuất

Bộ chuẩn GĐ4: 30 câu khái niệm + 5 câu demo 10/11, Claude soạn, chưa người duyệt độc lập. Một câu "trúng" khi khối
đúng nằm trong danh sách (đã bỏ trùng khối).

| Cách tìm | Recall@1 | Recall@4 | MRR | Ghi chú |
|---|---|---|---|---|
| BM25 (đang chạy khi không có khóa) | **51,4%** | 85,7% | 0,686 | |
| MiniLM L12 (đúng tài liệu 2.1, chưa fine-tune) | 45,7% | 88,6% | 0,648 | Kém cả BM25 vì cắt 128 token |
| **multilingual-e5-small** (chưa fine-tune, CPU) | **85,7%** | **97,1%** | **0,910** | Tính vector 45 đoạn hết 0,96 giây |
| Gemini embedding (GĐ4, 04/11, 30 câu) | 93,3% | 100% | — | Chưa đo lại trong phiên này vì máy cloud không có khóa |

Trên 4 câu dò luồng A viết kiểu người học thật (không dấu, tiếng Anh, viết tắt), cả ba cách đều kém (e5-small
R@1 0/4, R@4 3/4). Bộ chuẩn GĐ4 dễ hơn thực tế vì câu hỏi chép gần nguyên từ đoạn bài.

**Tách câu trong bài với câu ngoài bài bằng một ngưỡng điểm có được không?**

| Mô hình | Điểm cao nhất: A (trung vị) | B | C | D | Ngưỡng tách tốt nhất | Giữ đúng A | Loại đúng B/C/D/G |
|---|---|---|---|---|---|---|---|
| MiniLM L12 | 0,609 | 0,380 | 0,219 | 0,283 | 0,451 | 92,3% | 90,0% |
| e5-small | 0,873 | 0,835 | 0,792 | 0,810 | 0,845 | 92,3% | 90,0% |
| BM25 (ngưỡng hiện tại 2,0) | 7,52 | | | | | 97,4% | **chỉ loại 16,7%** |

Ngưỡng trên được chọn ngay trên chính các câu này nên là số lạc quan. Kể cả vậy, một ngưỡng đơn không đạt được mục
tiêu của GĐ1 (trả lời nhầm B/C ≤ 2%, từ chối nhầm A ≤ 5%). Điểm của e5-small bị nén trong khoảng 0,73–0,92, giống
hiện tượng đã thấy ở Gemini (0,59–0,78). Vì vậy GĐ1 cần bộ định tuyến 2 tầng, và GĐ2b fine-tune bằng contrastive
loss có mục tiêu rõ ràng: kéo giãn khoảng cách giữa câu trong bài và câu ngoài bài.

## 5. Hôm nay hệ thống làm gì với từng loại câu (không khóa, BM25)

Chạy đúng `answer_question`, LLM giả ghi lại mỗi lần được gọi. "Gọi LLM" nghĩa là nếu có khóa thì Gemini sẽ được hỏi
và tự viết câu trả lời.

| Loại câu (số câu) | Gọi LLM | Từ chối đúng | Ghi chú |
|---|---|---|---|
| A trong bài (39) | 38 | 1 "không biết" nhầm | "cmaj7 la gi" bị trả "không biết" |
| B nhạc lý bài chưa dạy (8) | **6** | 2 | Csus4, E–Bb, Rê trưởng, C9: đều gửi LLM kèm đoạn không liên quan |
| C ngoài phạm vi (4) | **2** | 2 | "Sơn Tùng sinh năm bao nhiêu", "mua đàn piano điện" lọt tới LLM |
| D hướng dẫn sử dụng (6) | **5** | 0 | "Làm sao đổi mật khẩu" bị coi là **tấn công** |
| Chào hỏi (2) | 1 | | "Chào bạn" bị từ chối như câu ngoài phạm vi |

## 6. Lỗ hổng, xếp theo mức ảnh hưởng

| # | Mức | Lỗ hổng | Câu thật minh họa | Sửa ở |
|---|---|---|---|---|
| 1 | Nghiêm trọng | Không khóa thì truy xuất bằng BM25: R@1 51,4%. Đây cũng là **nguyên nhân lỗi "C7 vs Cmaj7 trích L03"**: BM25 xếp `L03-B07` (đoạn Ghi nhớ của L03 nhắc nhiều ký hiệu hợp âm) lên đầu, đoạn dạy đúng `L02-B05` không vào top 4 | "C7 khác Cmaj7 ở điểm nào?" → L03-B07, L03-B03, L02-B02, L03-B02 | GĐ1: e5-small làm mặc định (quyết định 1A, 2A) |
| 2 | Nghiêm trọng | Câu nhạc lý bài chưa dạy luôn đi tới LLM kèm đoạn không liên quan, nên LLM phải tự trả lời bằng kiến thức chung | "Csus4 gồm những nốt nào?" → gửi kèm đoạn hợp âm ba L01-B08 | GĐ1: luồng B khuôn viết sẵn (5A) |
| 3 | Nghiêm trọng | Ngưỡng BM25 2,0 gần như không lọc: 83% câu B/C/D/chào hỏi vẫn có "đoạn liên quan" | "Mua đàn piano điện loại nào rẻ mà tốt?" → L03-B01, L04-B01 | GĐ1: định tuyến 2 tầng |
| 4 | Cao | Dữ kiện Engine chỉ tra ký hiệu hợp âm; regex bỏ sót `sus4`, `9`; không tra quãng, âm giai, số La Mã | "Quãng từ E lên Bb là quãng gì?" → không có dữ kiện | GĐ1: mở rộng 4 công cụ |
| 5 | Cao | Không có kho hướng dẫn sử dụng; câu hỏi cách dùng web bị gửi LLM kèm đoạn nhạc lý | "Đổi nhạc cụ trong mục Sáng tác ở đâu?" → L01-B01, L01-B05 | GĐ1: luồng D, `content/help/` (10A) |
| 6 | Cao | Lọc tấn công bắt nhầm từ "mật khẩu" | "Làm sao đổi mật khẩu tài khoản?" → trả câu từ chối tấn công | GĐ1: chỉ chặn khi xin khóa/mật khẩu của hệ thống |
| 7 | Trung bình | Hai phần ba số đoạn không đúng 80–100 từ; 11 đoạn dưới 30 từ chỉ có ký hiệu, dễ "hút" câu hỏi có ký hiệu | `L03-B04#1` "Cmaj7 → Dm7 → G7 → Cmaj7 = T → PD → D → T" | GĐ2: gộp khối ngắn vào khối kề, metadata khái niệm |
| 8 | Trung bình | Nguồn gắn theo bài, không theo khối; câu trả lời có thể ghi tên sách chỉ được tham khảo | mọi đoạn L04 | GĐ2: nguồn theo khối |
| 9 | Trung bình | Bộ chuẩn GĐ4 dễ hơn thực tế (câu chép gần nguyên đoạn) và không có câu B/D/chào hỏi; chưa ai ngoài Claude viết | 4 câu dò kiểu người học: e5 R@1 0/4 | GĐ1–GĐ2: bộ chuẩn viết tay (11A) |
| 10 | Thấp | Chào hỏi bị từ chối như câu ngoài phạm vi | "Chào bạn" | GĐ1: nhãn chào hỏi |

## 7. Việc cần người duyệt

| Ai | Việc | Hạn |
|---|---|---|
| Phúc | Đọc báo cáo, đồng ý cho sang GĐ1 | 07/11 |
| Đạt | Xác nhận bảng "đoạn nhắc khái niệm bài sau" (mục 3.2) là có chủ ý hay cần sửa | 08/11 |
| Đạt, Thắng, Phúc | Mỗi bạn viết trước 10 câu cho bộ test (quyết định 11A, phiếu nhập sẽ gửi ở GĐ1) | 08/11 |
| Thắng | Biết trước: GĐ1 thêm `sentence-transformers` hoặc `onnxruntime` vào backend và Docker (quyết định 4A) | 08/11 |

## 8. Giải thích cho nhóm

Hãy tưởng tượng AI Tutor như một bạn trực thư viện. Có người hỏi thì bạn ấy chạy vào kho lấy ra 4 trang sách "giống
câu hỏi nhất", đưa cho Gemini đọc rồi trả lời. Hiện tại, khi không có khóa Gemini, bạn trực thư viện chọn trang bằng
cách **đếm chữ trùng** (BM25). Hỏi "C7 khác Cmaj7 ở điểm nào?" thì bạn ấy lấy trang có nhiều chữ "C7", "Cmaj7" nhất,
đó là trang Ghi nhớ của bài L03, chứ không phải trang L02 giải thích hai hợp âm này. Đếm chữ chỉ đúng khoảng 1 trên
2 lần (51,4%). Đổi sang một mô hình **hiểu nghĩa câu** (e5-small, chạy ngay trên máy, không cần Internet) thì đúng
6 trên 7 lần (85,7%).

Vấn đề thứ hai: bạn trực thư viện **luôn** mang ra 4 trang, kể cả khi kho không có trang nào trả lời được. Hỏi
"Csus4 gồm nốt gì?" (chưa bài nào dạy) thì bạn ấy vẫn mang trang về hợp âm ba, và Gemini sẽ phải tự đoán. GĐ1 sửa
đúng chỗ này. Câu nhạc lý mà kho không có thì để Music Engine tính (Csus4 = C, F, G) và gắn nhãn "Ngoài bài học".
Câu không liên quan thì trả lời "mình không biết". Câu hỏi cách dùng web thì tra kho hướng dẫn riêng.

Câu giảng viên có thể hỏi:

1. *"Sao không dùng MiniLM như tài liệu ghi?"* (Phúc) Vì đã đo thật: MiniLM chỉ đọc 128 token, mà 21/45 đoạn dài hơn
   nên bị cắt đuôi, kết quả R@1 chỉ 45,7%. e5-small đọc được 512 token, đạt 85,7%.
2. *"85,7% đo trên bộ nào, ai viết?"* (Phúc) Trên 35 câu Claude soạn ở GĐ4, chưa có người duyệt độc lập. Bộ câu do
   nhóm tự viết tay sẽ có ở GĐ1–GĐ2 và được khóa lại trước khi fine-tune.
3. *"Sao không chỉ đặt ngưỡng điểm cho câu ngoài bài?"* (Thắng) Đã thử: điểm của câu trong bài và ngoài bài chồng
   lên nhau (0,79–0,92 so với 0,73–0,88), ngưỡng tốt nhất vẫn sai khoảng 1/10 câu. Cần bộ phân loại riêng và fine-tune.
4. *"Lỗi trích dẫn sai bài do đâu?"* (Phúc) Do BM25 đếm chữ trùng; đã chạy lại và tái hiện được (mục 6, lỗ hổng 1).
5. *"Kho có bao nhiêu dữ liệu?"* (Đạt) 45 đoạn, 2.519 từ, từ 4 bài L01–L04 ở trạng thái reviewed. L05–L08 chưa có
   lý thuyết, sẽ soạn ở GĐ3.

Kết quả trên dữ liệu do Claude soạn, chưa chứng minh chất lượng với người học thật.
