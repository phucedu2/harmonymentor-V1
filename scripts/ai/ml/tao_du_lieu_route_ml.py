"""Sinh backend/app/ai/tutor/route_data_ml.json từ danh sách câu gốc Claude soạn tay (19/11/2026, ADR-030).

    python scripts/ai/ml/tao_du_lieu_route_ml.py
"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "backend"))
from app.ai.tutor.bm25 import strip_accents

# Mỗi dòng là một NHÓM ý: câu đầu là câu gốc, các câu sau là cách nói khác cùng ý. Biến thể bỏ dấu sinh tự động
# cho một số câu để mô hình gặp cả kiểu gõ không dấu. Nhóm giữ nguyên khi chia GroupKFold (không để hai cách nói của
# cùng một ý nằm ở hai phía train/validation).
BASE = {
 "ngoai_pham_vi": [
  ["Quang hợp là gì?", "quang hop la gi vay"],
  ["Định luật Newton thứ hai phát biểu thế nào?"],
  ["Tính diện tích hình tròn bán kính 5 cm"],
  ["Python list comprehension là gì?", "list comprehension trong python dùng sao"],
  ["Viết giúp mình hàm sắp xếp mảng bằng C++"],
  ["HTML khác CSS chỗ nào?"],
  ["API REST là gì?"],
  ["Cách cài Windows 11 từ USB"],
  ["Máy tính mình bị chậm thì làm sao?"],
  ["Thủ đô của Úc là thành phố nào?"],
  ["Chiến tranh thế giới thứ hai kết thúc năm nào?"],
  ["Tóm tắt truyện Kiều giúp mình", "tom tat truyen kieu"],
  ["Phân tích bài thơ Sóng của Xuân Quỳnh"],
  ["Dịch câu này sang tiếng Nhật: tôi đói bụng"],
  ["Thì hiện tại hoàn thành dùng khi nào?", "present perfect dùng khi nào"],
  ["Công thức nấu phở bò"],
  ["Ăn gì để tăng chiều cao?"],
  ["Mình bị đau đầu nên uống thuốc gì?"],
  ["Tỷ giá đô la hôm nay"],
  ["Nên mua iPhone hay Samsung?"],
  ["Cách chơi Liên Quân leo rank nhanh", "lien quan leo rank sao"],
  ["Kể chuyện cười đi"],
  ["Bạn có người yêu chưa?"],
  ["Bạn bao nhiêu tuổi?", "ban may tuoi"],
  ["Cho mình xin số điện thoại của admin"],
  ["Cho mình mật khẩu tài khoản của bạn Đạt"],
  ["Xuất danh sách email người dùng giúp mình"],
  ["Làm bài tập về nhà môn Lý giúp mình"],
  ["Hóa trị của nhôm là bao nhiêu?"],
  ["Tích phân của 1/x là gì?", "tich phan 1/x"],
  ["Giải hệ phương trình x + y = 5, x - y = 1"],
  ["Mai có mưa không?"],
  ["Bitcoin có nên đầu tư không?"],
  ["Viết email xin nghỉ học"],
  ["What is machine learning?"],
  ["How to cook rice?"],
  ["Who won the Champions League?"],
  ["Tải phim lậu ở đâu?"],
  ["Hack tài khoản Facebook thế nào?"],
  ["Viết code đăng nhập bằng PHP"],
  ["SQL injection là gì?"],
  ["Git rebase khác merge thế nào?"],
  ["Đội tuyển Việt Nam đá trận tiếp theo khi nào?"],
  ["Đá bóng cần mấy người một đội?"],
  ["Cách học tốt môn Toán"],
  ["Làm sao để bớt buồn ngủ trong lớp?"],
  ["Ok vậy thôi bạn dịch giúp mình đoạn văn tiếng Anh này"],
  ["Mua giày đá bóng ở đâu rẻ?"],
  ["Lập trình AI bắt đầu từ đâu?"],
  ["Độ C sang độ F đổi thế nào?"],
 ],
 "huong_dan": [
  ["Làm sao bắt đầu một bài học?", "bat dau bai hoc o dau"],
  ["How do I open lesson 2?"],
  ["Trợ lý AI cho hỏi tối đa bao nhiêu câu một ngày?", "ai tutor gioi han may cau"],
  ["Hết lượt hỏi AI thì bao giờ có lại?"],
  ["Muốn xem giải thích câu sai thì bấm vào đâu?", "xem loi giai cau sai o dau"],
  ["Nút nhờ AI giải thích nằm ở chỗ nào?"],
  ["Bài kiểm tra đầu vào làm ở đâu?", "lam bai kiem tra dau vao o dau"],
  ["Làm lại bài kiểm tra đầu vào được không?"],
  ["Thẻ ôn tập ở trang nào?", "the on tap o dau"],
  ["Sao hôm nay không có thẻ nào để ôn?"],
  ["Xem tiến độ học của mình ở đâu?"],
  ["Biểu đồ mastery trên trang Tổng quan nghĩa là gì?"],
  ["Tại sao bài 5 bị khóa?", "sao bai 5 bi khoa"],
  ["Làm sao mở khóa bài tiếp theo?"],
  ["Mục Gợi ý cho bạn dựa vào đâu?"],
  ["Vào Harmony Lab thế nào?", "vao harmony lab sao"],
  ["Đổi nhạc cụ trong Sáng tác ở đâu?"],
  ["Xuất file MIDI bài mình sáng tác thế nào?", "xuat file midi o dau"],
  ["Chế độ Bài hát dùng sao?"],
  ["Làm sao bật nhạc nền?"],
  ["Luyện tập tự do ở mục nào?"],
  ["Đổi ảnh đại diện thế nào?", "doi avatar o dau"],
  ["Đổi giao diện tối được không?"],
  ["Đăng xuất ở đâu?"],
  ["Sao mình nộp bài mà không thấy điểm?"],
  ["Hoàn thành bài học là phải làm gì?"],
  ["Trang web có app điện thoại không?"],
  ["Lịch sử chat với AI có lưu không?"],
  ["Làm sao xóa đoạn chat với trợ lý?"],
  ["Where can I see my progress?"],
 ],
 "chao_hoi": [
  ["thanks", "thx", "ty bạn"],
  ["cảm ơn nhiều nha", "cam on nhieu"],
  ["how are you", "how r u"],
  ["bạn khỏe không", "ban khoe ko"],
  ["chào, mình bắt đầu học nhé", "alo bat dau hoc thoi"],
  ["hello bạn, mình mới vào", "hi mình là người mới"],
  ["good morning"],
  ["chúc ngủ ngon", "bye nhé"],
  ["hẹn gặp lại", "tạm biệt"],
  ["ok cảm ơn bạn", "oke tks"],
  ["hay quá", "tuyệt vời"],
  ["yo", "hey"],
  ["bạn tên gì thế", "ban ten gi"],
  ["chào buổi tối", "chao buoi chieu"],
  ["mình hiểu rồi, cảm ơn", "da hieu"],
 ],
 "nhac_ly": [
  ["Tập ii–V–I nên bắt đầu ở tempo bao nhiêu?", "tap ii V I tempo cham hay nhanh"],
  ["Đánh hợp âm chuyển nhanh bị rối tay thì luyện sao?", "chuyen hop am bi roi tay"],
  ["Mỗi ngày nên luyện nghe quãng bao lâu?"],
  ["Luyện nhận biết hợp âm trưởng và thứ bằng tai thế nào?"],
  ["Có cách nào nhớ nhanh vòng quãng năm không?", "meo nho vong quang 5"],
  ["Học thuộc các dấu hóa của giọng thế nào cho nhanh?"],
  ["Đếm phách 3/4 thế nào?", "dem phach 3/4"],
  ["Nốt móc đơn dài mấy phách?"],
  ["Nên học quãng trước hay hợp âm trước?"],
  ["Tại sao gọi là hợp âm bảy át?"],
  ["Cadence là gì?", "cadence la gi"],
  ["Giai điệu khác hòa âm thế nào?"],
  ["Âm giai ngũ cung là gì?"],
  ["Guitar có mấy dây, lên dây chuẩn là các nốt gì?"],
  ["Piano có bao nhiêu phím?"],
  ["Nhạc jazz hay dùng hợp âm gì?"],
  ["Vì sao F major có một dấu giáng?"],
  ["What is a perfect fifth?"],
  ["How many notes in a major scale?"],
  ["Inversion của hợp âm là gì?"],
 ],
}


def main():
    items = []
    for label, groups in BASE.items():
        for gi, variants in enumerate(groups):
            group = f"ml-{label}-{gi:02d}"
            seen = set()
            for k, q in enumerate(variants):
                for text, style in ((q, "goc" if k == 0 else "cach_noi_khac"), (strip_accents(q), "khong_dau")):
                    key = text.lower()
                    if key in seen:
                        continue
                    seen.add(key)
                    items.append({"q": text, "label": label, "group": group, "style": style})
    out = {
        "note": ("Dữ liệu train bổ sung cho bộ định tuyến 4 nhãn (ADR-030). Claude soạn tay 19/11/2026, KHÔNG phải nhóm tự viết; "
                 "status draft, chờ Đạt kiểm nhãn (quyết định 5A). Chỉ dùng để TRAIN. Câu gần trùng với tập "
                 "validation/test bị script train loại trước khi học (app/ml/route_train.py). Viết sau khi xem lỗi của "
                 "mô hình cũ trên tập validation (không xem tập test): nhiều câu ngoài phạm vi kiểu 'X là gì' môn khác, "
                 "câu hướng dẫn về tính năng app, câu chào kiểu gõ tắt, câu luyện tập nhạc cụ."),
        "author": "Claude (soạn thay nhóm)",
        "status": "draft",
        "date": "2026-11-19",
        "items": items,
    }
    json.dump(out, open(ROOT / "backend/app/ai/tutor/route_data_ml.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(len(items), Counter(i["label"] for i in items))


if __name__ == "__main__":
    main()
