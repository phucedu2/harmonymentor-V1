# Nhận diện nốt nhạc từ micro (19/11/2026, ADR-030)

Nhánh `nhan-dien-not-micro` (tách từ `phuc-music` tại 53cebaf), Draft PR vào `phuc-music`.

## 1. Đã làm

| Phần | File chính |
|---|---|
| Engine đổi Hz → nốt + cent | `backend/app/music_engine/pitch.py` (`note_from_frequency`), `backend/app/api/engine.py` |
| Luyện tập nhận `input: "micro"` | `backend/app/services/practice_service.py`, `backend/app/contracts/practice.py` |
| YIN + ổn định nốt + nghe micro | `frontend/src/audio/pitch/yin.ts`, `stabilizer.ts`, `micListener.ts` |
| Model chạy trên trình duyệt | `frontend/src/audio/pitch/features.ts`, `frontend/public/models/pitch_mlp.json` |
| Giao diện "Đàn bằng micro" | `frontend/src/components/music/MicNoteInput.tsx`, `frontend/src/pages/Practice.tsx` |
| Dữ liệu, train, đánh giá | `scripts/ai/pitch/dac_trung.py`, `du_lieu.py`, `train.py` → `KET_QUA_MODEL.md` |
| Thử trên giao diện thật | `scripts/e2e/micro_nhan_dien_not.cjs`, ảnh ở `anh/` |

## 2. Lệnh đã chạy và kết quả (19/11/2026, container cloud)

```bash
cd backend && pytest -q                                   # xem mô tả PR (số thật)
cd frontend && npm test && npm run build
python scripts/ai/pitch/du_lieu.py --out /tmp/pitch_data.npz            # 33.935 khung, ~2 phút
python scripts/ai/pitch/train.py --data /tmp/pitch_data.npz --report docs/giai-doan/nhan-dien-not-micro/KET_QUA_MODEL.md \
  --export frontend/public/models/pitch_mlp.json --fixture frontend/src/audio/pitch/__fixtures__/parity.json   # ~1 phút
# backend :8000 + vite :5173
OUT=docs/giai-doan/nhan-dien-not-micro/anh node scripts/e2e/micro_nhan_dien_not.cjs
```

Kịch bản giao diện thật thay micro bằng luồng phát **mẫu piano thu thật** (Salamander), nên cả chuỗi
micro → YIN/model → Engine → chấm đều chạy như trên máy người học:

| Kịch bản | Kết quả |
|---|---|
| Máy tính 1280 px: đàn sai 1 nốt, rồi câu khác đàn đúng | Nghe đúng 6/6 nốt, chấm "Chưa đúng" rồi "Đúng cao độ" |
| Điện thoại 390 px: như trên | Nghe đúng 6/6 nốt, chấm đúng |
| Có tiếng ù điện 50 Hz, chỉ YIN | Không nghe được nốt nào |
| Có tiếng ù điện 50 Hz, Kết hợp | Nghe đúng 6/6 nốt, chấm đúng |

Model trên bộ test giữ riêng: xem `KET_QUA_MODEL.md` (kết hợp 96,9%, YIN 59,8%, model 96,5%).
**Chưa chứng minh chất lượng với micro thật của người học.**

## 3. Giải thích cho nhóm

**YIN là gì?** Một nốt nhạc là sóng lặp lại. Nốt A4 lặp 440 lần mỗi giây. YIN thử dịch sóng đi τ mẫu rồi so với chính nó:
dịch đúng một chu kỳ thì hai bản gần trùng nhau. Ví dụ ở 48.000 mẫu/giây, A4 trùng khi dịch τ ≈ 109 mẫu → 48000 / 109 ≈ 440 Hz.

**Vì sao cần model?** Khi phòng ồn hoặc có tiếng ù, đường so sánh của YIN không xuống đủ thấp nên YIN "không dám trả lời".
Model MLP nhìn cả đường cong YIN (181 điểm) và phổ tần số (73 ô) rồi học từ 27.000 ví dụ có đáp án, nên vẫn đoán được.

**Học từ handson-ml3 những gì:**
- Ch.2: chia train/test theo *bản thu* (`GroupShuffleSplit`). Nếu chia ngẫu nhiên, bản thêm nhiễu của cùng một tiếng
  đàn nằm ở cả hai bên, điểm test sẽ cao giả.
- Ch.2/7: `GridSearchCV` thử 6 bộ tham số (lớp ẩn 64/128/128+64, alpha 0,0001/0,01) với `GroupKFold` 4 phần.
- Ch.3: độ chính xác, ma trận nhầm lẫn 12 nốt, tỉ lệ nhầm quãng tám.
- Ch.4: train 99,9% so với test 96,5%, chênh nhỏ nên không học vẹt nặng.
- Ch.10: MLP. Trình duyệt tự tính `ReLU(W·x + b)` rồi softmax, khoảng 40.000 phép nhân mỗi khung.
- Thử tổng quát: giấu hẳn cello khi train, model vẫn đúng 91,9% với cello.

**Một lỗi tìm được khi thử thật:** lúc đầu model chưa có lớp "không có nốt", nên giữa hai nốt nó "nghe" tiếng ù ra nốt
D3. Đã thêm 3.000 khung ù/ồn có nhãn 0. Sau đó tỉ lệ báo nhầm khi không có nốt là 0,0% trên 560 khung test.

### 5 câu giảng viên có thể hỏi

1. *Model có tự đặt tên nốt không?* Không. Model chỉ ra Hz; Music Engine đặt tên và chấm (Thắng trả lời).
2. *Sao biết model không học vẹt?* Chia theo bản thu, so train/test, giấu hẳn một nhạc cụ (Đạt trả lời).
3. *Có gửi giọng người học lên máy chủ không?* Không, chỉ gửi một con số Hz mỗi nốt (Phúc trả lời).
4. *Sao không dùng TensorFlow?* Model nhỏ, scikit-learn đủ; trình duyệt tự tính, không cần thêm thư viện 10 MB (Đạt).
5. *Đánh hợp âm cùng lúc được không?* Chưa: cần nhận diện đa âm, khó hơn nhiều, để Hướng phát triển (Thắng).

## 4. Việc để kiểm

- **Phúc:** mở Luyện tập → Dựng hợp âm → "Đàn bằng micro", đàn piano/guitar thật hoặc hát; thử 3 bộ nhận diện. Người kiểm: ______
- **Thắng:** đọc `note_from_frequency` và test; quyết định có nhận thay đổi Engine (ADR-030). Người kiểm: ______
- **Đạt:** đọc `train.py`, `KET_QUA_MODEL.md`; thu giọng thật của nhóm để train lại. Người kiểm: ______

## 5. Rủi ro và câu hỏi

1. Tài liệu 2.1 ghi micro ngoài phạm vi. Đề xuất: sửa SRS mục Phạm vi + nâng FR-COM-ADV-07 lên Giai đoạn 1 sau khi nhóm đồng ý.
2. Giọng hát chỉ có dữ liệu tổng hợp (83,5%). Đề xuất: mỗi bạn hát 20 nốt, chạy lại `du_lieu.py` + `train.py`.
3. Ù điện dạng răng cưa đủ dải (khác dữ liệu train) vẫn làm model nghe sai khi thử: đây là "dữ liệu thật khác dữ liệu train".
   Đề xuất: thu 1 phút tiếng phòng ở máy từng bạn để thêm vào lớp "không có nốt".
