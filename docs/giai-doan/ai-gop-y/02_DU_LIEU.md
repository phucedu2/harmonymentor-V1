# GĐ2 góp ý thầy: dữ liệu train / dev / test tạm cho AI Tutor

Ngày 07/11/2026 · nhánh `ai-gop-y/gd2-du-lieu` (từ `phuc-music` 6ff7478) · Phúc chọn 1A–10A, 12A (11: làm hết GĐ2, GĐ2b, nếu kịp GĐ3 trong ngày). Câu hỏi làm rõ: `/mnt/project-files/harmonymentor-ai-gop-y/CAU_HOI_LAM_RO_GD2.md`.

## 1. Kết quả chính

- **Có bộ dữ liệu 1.011 câu** (667 train, 170 dev, 174 test tạm) cho đủ 5 luồng A/B/C/D/G.
  - Claude viết, đóng vai người học thật: câu không dấu, gõ tắt ("ko", "fai", "mik"), lỗi gõ, chữ thường, thêm "ad ơi … ạ".
  - Không dùng Gemini (4A).
  - **Đây không phải tập test chính thức (1A).** Số chính thức lấy trên phiếu do Đạt, Thắng và Phúc tự viết: `PHIEU_CAU_HOI_GD2.xlsx`.
- **Tách theo nhóm mẫu.** Một mẫu câu, kể cả mọi biến thể của nó, chỉ nằm ở một tập.
  - Không câu nào trùng hay gần trùng giữa các tập mới và các tập cũ: train/dev GĐ1, bộ chuẩn GĐ4, câu dò GĐ0, cách hỏi mẫu của kho hướng dẫn.
  - Có 63 câu gốc bị bỏ vì trùng (danh sách trong `kiem_nhan.md`).
- **Câu "bẩn" của người học làm lộ điểm yếu mà bộ đo cũ không thấy.** Trên test tạm, bộ định tuyến GĐ1 với e5 từ chối sai 27,9% câu A.
- **Sau GĐ2** (train lại tầng 1, sửa 3 luật, chọn lại ngưỡng trên dev):

  | Bộ đo | Cách tìm | B/C bị trả lời như bài học (≤ 2%) | A bị từ chối sai (≤ 5%) | Đúng luồng |
  |---|---|---|---|---|
  | Test tạm GĐ2 (174 câu) | e5, trước → sau | 11,7% → 13,3% | 27,9% → 24,4% | 69,0% → 70,1% |
  | Test tạm GĐ2 | BM25, trước → sau | 21,7% → 26,7% | 14,0% → 7,0% | 74,7% → 80,5% |
  | Bộ đo GĐ1 (74 câu) | e5, trước → sau | 3,5% → **0,0%** | 10,8% → 8,1% | → 93,2% |
  | Bộ đo GĐ1 | BM25, trước → sau | 3,5% → 3,5% | 5,4% → **2,7%** | → 93,2% |

  **Mục tiêu vẫn chưa đạt**, nhất là trên câu bẩn. Nguyên nhân chính nằm ở mô hình nhúng chứ không ở luật:
  - Trên test tạm, 19 câu A bị từ chối vì không đoạn nào đủ điểm. Đa số là câu không dấu, ví dụ "triad la gi" hay "ø7 la hop am gi".
  - Có 8 câu B lọt sang A vì điểm cao.

  Trên dev, e5 gốc chỉ tách được câu A khỏi câu B/C với AUC 0,79. Việc này để GĐ2b (fine-tune) xử lý, xem `03_FINETUNE.md`.

## 2. Đã làm gì

| Việc | File | Ghi chú |
|---|---|---|
| Câu gốc ~470 câu, 5 luồng, theo nhóm mẫu | `scripts/ai/gop_y/gd2_cau_goc.py` | Nhãn theo sư phạm (kho có dạy hay không), không chép từ luật router. A có mã bài, D có mục hướng dẫn, B có bài L05–L08 nếu thuộc bài sau |
| Sinh biến thể + tách tập + kiểm nhãn | `scripts/ai/gop_y/tao_du_lieu_gd2.py` | Tất định (seed 20261107). Train lấy câu gốc + 2 biến thể; dev và test lấy 2 dạng mỗi câu |
| Dữ liệu | `scripts/ai/data/gd2/{train,dev,test_tam}.json`, `kiem_nhan.md` | Câu B có kèm dữ kiện Music Engine (hoặc "Engine không tính được") để người duyệt xem |
| Tầng 1 học thêm câu GĐ2 | `backend/app/ai/tutor/route_data_gd2.json`, `route_classifier.py` | Gộp với `route_data.json`. `ROUTE_GD2=0` tắt để đo "trước/sau" |
| Sửa luật "bài sau" | `router.py` | Luật so chữ thường, nhưng mẫu số La Mã lại viết hoa, nên "V7/V", "V/ii" không bao giờ khớp L05. Thêm bVII/bVI/bIII (L06) và "tension" số ít (L07) |
| Sửa luật "thuật ngữ lạ" | `router.py` | Không bắt nhầm cách gõ của người học: (1) từ trong câu train luồng A là từ đã biết ("ko", "fai", "vs"); (2) lỗi gõ gần một từ đã biết ("enharmonci", "cug"); (3) ký hiệu quãng m3, P5, d5, A4. Vẫn bắt "pentatonic", "fugue", "ostinato" |
| Nguồn theo khối (GĐ0 lỗ hổng 8) | `chunker.py` | Mỗi đoạn chỉ ghi các nguồn của bài cùng chủ đề với khối, ví dụ đoạn về quãng không còn ghi chương Triads. Không trùng chủ đề nào thì giữ nguồn cả bài. Bảng chủ đề là **nháp, chờ Đạt duyệt** |
| Hash đoạn bỏ phần nguồn | `chunker.py`, `build_index.py rehash` | Nguồn không được nhúng nên đổi nguồn không làm vector cũ sai. `rehash` chỉ đổi hash khi hash cũ khớp đúng văn bản cũ (45/45 đoạn), không gọi Gemini |
| Ngưỡng chọn lại trên dev GĐ1 + dev GĐ2 (275 câu) | `router_thresholds.json`, `hieu_chinh_nguong.py` | `--dev` nhận nhiều file. Ngưỡng ứng viên lấy 40 phân vị của điểm thật, nếu dò hết thì hàng chục triệu lượt |
| Test | `backend/tests/test_ai_gd2_du_lieu.py` | 23 test: cỡ tập, nhãn trỏ đúng bài/trang, tách theo nhóm, train tầng 1 không chứa câu dev/test, các luật, nguồn theo khối, tên mô hình |

**Đã thử nhưng không giữ** (GĐ0 lỗ hổng 7): gộp đoạn đuôi ngắn hơn 30 từ vào đoạn trước, và thêm tiêu đề khối trước làm ngữ cảnh tìm kiếm cho khối ngắn. R@1 của e5 trên bộ chuẩn GĐ4 giảm từ 90,0% xuống 83,3% (G22, G25 sai thêm), nên đã bỏ. Đoạn ngắn hút câu hỏi chỉ là giả thuyết của GĐ0; số đo không ủng hộ.

Một luật khác cũng đã thử và **không giữ**: trả lời luồng A cho mọi câu có dữ kiện Engine thuộc loại kho đã dạy, kể cả khi không có đoạn bài ở vùng xám. Trên dev, e5 trả lời sai câu B/C tăng từ 8,3% lên 9,3% mà không giảm từ chối sai.

Hệ quả cần biết: khi chạy BM25 (không có mô hình e5), câu rất ngắn như "Cmaj7 là gì?" được trả bằng dữ kiện Engine (luồng B, nhãn "Ngoài bài học") thay vì trả từ bài. Nốt vẫn đúng, chỉ nhãn chưa đúng. Test quota trong `test_ai_gd3_tutor_api.py` đổi sang câu "Cmaj7 với C7 khác gì nhau?" vì test này cần một câu gọi LLM.

## 3. Lệnh và kết quả

```bash
cd backend
python ../scripts/ai/gop_y/tao_du_lieu_gd2.py              # sinh lại dữ liệu (tất định)
python ../scripts/ai/gop_y/kiem_trung_du_lieu.py           # 0 cặp trùng giữa các tập
python ../scripts/ai/gop_y/hieu_chinh_nguong.py            # chọn ngưỡng trên dev GĐ1 + GĐ2
python ../scripts/ai/gop_y/danh_gia_dinh_tuyen.py --set ../scripts/ai/data/gd2/test_tam.json
python -m app.ai.build_index rehash
pytest -q
```

- Đo chi tiết (ma trận nhầm lẫn, từng câu sai): `gd2_test_tam.md`, `gd2_bo_do_gd1.md` (cùng thư mục, kèm bản `.json`).
- Kết quả pytest ghi trong mô tả PR.

## 4. Giải thích cho nhóm

- **Vì sao tách theo nhóm mẫu?** Nếu "hợp âm Em gồm nốt nào" nằm ở train còn "hợp âm F gồm nốt nào" nằm ở test, mô hình chỉ cần nhớ mẫu câu là làm đúng, và số đo sẽ đẹp giả. Tách theo nhóm buộc mô hình gặp kiểu câu thật sự mới.
- **Vì sao điểm trên test tạm thấp hơn bộ đo cũ?** Bộ cũ phần lớn là câu có dấu, viết gọn gàng. Người học thật gõ không dấu và gõ tắt; mô hình nhúng gốc chấm thấp những câu đó.
- **Vì sao không "chỉnh luật cho hết lỗi"?** Ba luật sửa ở đây là lỗi thật: chữ hoa và chữ thường không khớp, và bắt nhầm cách gõ của người học. Các lỗi còn lại do điểm nhúng không tách được câu A khỏi câu B, nên phải sửa ở mô hình (GĐ2b). Nếu cứ thêm luật cho tới khi test tạm đẹp, thì đó chính là học tủ đề thi.

## 5. Rủi ro, việc còn chờ

- Số chính thức chờ phiếu của nhóm. Hạn 10 câu mỗi người là 08/11.
  - Khi có: chạy `kiem_trung_du_lieu.py --test <phiếu>` rồi `danh_gia_dinh_tuyen.py --set <phiếu>`.
  - Phiếu dev của Phúc thêm vào `--dev`.
- Nhãn do Claude gán. Theo 5A cần Astra hoặc nhóm xem ngẫu nhiên 10% số câu: lấy 10% câu gốc trong `scripts/ai/data/gd2/*.json`.
- Bảng chủ đề cho nguồn theo khối chờ Đạt duyệt.
- File vector Gemini (`lesson_embeddings.json`) chỉ được đổi hash, không được tính lại, vì văn bản không đổi. Lần tới sửa nội dung bài thì phải chạy `build_index` bằng khóa Gemini trên máy Phúc.
