# ADR-039: Nghe nốt qua micro khi có tạp âm

Trạng thái: đề xuất (chờ Thắng/Đạt đọc). Ngày: 2026-11-25. Mở rộng ADR-032.

## Bối cảnh
Phúc yêu cầu chế độ "Đàn bằng micro" nghe được nốt cả khi phòng có tạp âm, với piano thật và piano ảo phát qua loa laptop. Phúc chọn: mọi loại tạp âm, SNR ≥ ~6 dB, đúng ≥ 90% và nốt ma ≤ 2%, một nốt một lúc, test bằng tạp âm tổng hợp, model < 500 KB, có nút đo nền, phòng quá ồn thì cảnh báo và không chấm sai.

## Quyết định
1. Một đường xử lý duy nhất `frontend/src/audio/pitch/pipeline.ts` dùng chung cho trình duyệt và bộ đo: lọc trầm 70 Hz → ngưỡng thích nghi theo nền ồn (+ nút "Đo nền ồn") → nhận diện → bỏ phiếu 5/7.
2. Train lại MLP với tạp âm tổng hợp 4 loại + piano qua loa; lớp "không có nốt" gồm quạt/người nói/gõ bàn (nhạc nền không vào lớp 0 vì là nốt thật). Model 207 KB.
3. Bộ nhận diện mặc định: "Model AI" (YIN trước thì giọng nói bị nghe thành nốt).
4. Đo bằng bộ kiểm riêng (`luong_thu_on.py` + `danh_gia_micro.ts`) trên các bản thu giữ riêng. Chỉ số: đúng tên nốt, nốt ma/số nốt.
5. Không đổi Music Engine; máy chủ vẫn chỉ nhận Hz. Giữ tắt noiseSuppression/echoCancellation (chưa đo trên micro thật).

## Hệ quả
- Đạt mục tiêu trong mô phỏng cho quạt, người nói, gõ bàn (SNR ≥ 6 dB: 91,7% đúng, 1,7% nốt ma). **Không đạt với nhạc nền** (70% nốt ma); hướng dẫn người học tắt nhạc. Số liệu: docs/giai-doan/nhan-dien-not-micro/BAO_CAO_TAP_AM.md.
- Chưa thử micro/phòng thật. Số đo là mô phỏng.
- Độ trễ ≈ 210 ms. Model train không dùng bản thu giữ riêng (để kiểm chứng được).
- Mâu thuẫn tài liệu 2.1 (micro ngoài phạm vi) vẫn chờ nhóm, như ADR-032.
