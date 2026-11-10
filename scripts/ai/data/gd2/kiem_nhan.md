# Kiểm nhãn tự động GĐ2

Sinh bởi `scripts/ai/gop_y/tao_du_lieu_gd2.py`. Claude viết 07/11/2026, đóng vai người học (quyết định GĐ2 2A), không dùng Gemini (4A). KHÔNG phải tập test chính thức: số chính thức lấy trên phiếu do Đạt/Thắng/Phúc viết (1A).

| Tập | Câu | Nhóm | Theo luồng | Theo kiểu |
|---|---|---|---|---|
| train | 742 | 85 | {'A': 521, 'B': 71, 'C': 65, 'D': 63, 'G': 22} | {'chu_thuong': 43, 'go_tat': 50, 'goc': 288, 'khong_dau': 93, 'khong_dau_go_tat': 70, 'loi_go': 89, 'loi_goi': 109} |
| dev | 206 | 32 | {'A': 118, 'B': 35, 'C': 19, 'D': 21, 'G': 13} | {'chu_thuong': 26, 'go_tat': 19, 'goc': 46, 'khong_dau': 26, 'khong_dau_go_tat': 36, 'loi_go': 31, 'loi_goi': 22} |
| test_tam | 200 | 28 | {'A': 111, 'B': 38, 'C': 13, 'D': 23, 'G': 15} | {'chu_thuong': 14, 'go_tat': 19, 'goc': 64, 'khong_dau': 20, 'khong_dau_go_tat': 25, 'loi_go': 30, 'loi_goi': 28} |

Lệch nhãn cần người xem: 0


Câu gốc bị bỏ vì trùng/gần trùng tập khác: 64

- train: hợp âm ba nốt dựng như thế nào
- train: seventh chord là gì
- train: tại sao E với F chỉ cách nhau nửa cung
- train: C lên E là quãng mấy
- train: D lên A là quãng mấy
- train: voice leading là gì
- train: hợp âm Em gồm những nốt nào
- train: hợp âm F gồm những nốt nào
- train: hợp âm Gm gồm những nốt nào
- train: hợp âm F#m gồm những nốt nào
- train: hợp âm 7sus4 là gì
- train: tension 9 11 13 là gì
- train: giọng song song là gì
- train: âm giai A thứ hòa âm gồm những nốt nào
- train: âm giai E thứ hòa âm gồm những nốt nào
- train: âm giai D thứ hòa âm gồm những nốt nào
- train: âm giai C thứ hòa âm gồm những nốt nào
- train: modal interchange là gì
- train: mượn hợp âm từ giọng thứ là sao
- train: Csus4 gồm những nốt nào
- train: Dsus4 gồm những nốt nào
- train: Gsus4 gồm những nốt nào
- train: Asus4 gồm những nốt nào
- train: Esus4 gồm những nốt nào
- train: mode dorian là gì
- train: tritone substitution là gì
- train: secondary dominant là gì
- train: nhịp 6/8 đếm thế nào
- train: nốt móc đơn dài mấy phách
- train: khóa Fa đọc nốt thế nào
- train: bạn nghĩ gì về chính trị
- train: piano điện yamaha giá bao nhiêu
- train: bài hát nào đang hot trên tiktok
- train: tải nhạc mp3 miễn phí ở đâu
- train: Sơn Tùng sinh năm bao nhiêu
- train: làm sao giảm cân nhanh
- train: viết giúp mình email xin nghỉ học
- train: viết code python sắp xếp mảng
- train: dịch câu này sang tiếng anh: tôi đi học
- train: bài kiểm tra đầu vào là gì
- train: làm lại bài kiểm tra đầu vào được không
- train: tải bài sáng tác về máy được không
- train: trợ lý AI này trả lời được những gì
- train: cảm ơn đã giải thích
- train: chúc ngủ ngon
- train: good morning
- train: xin chào
- train: chào bạn nha
- train: hello
- train: hi
- train: tạm biệt
- train: chào buổi sáng
- train: chào AI
- dev: C# với Db có phải cùng một phím không
- dev: hợp âm chủ của một giọng là gì
- dev: concert BlackPink ở Hà Nội bao giờ
- dev: mở bài học ở đâu
- test_tam: giữa B và C có phím đen không
- test_tam: dấu chấm dôi làm nốt dài thêm bao nhiêu
- test_tam: làm sao để ngủ ngon hơn
- test_tam: lịch sử chiến tranh thế giới thứ hai
- test_tam: kể chuyện cười đi
- test_tam: bạn có người yêu chưa
- test_tam: hẹn gặp lại
