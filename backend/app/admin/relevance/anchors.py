"""Câu neo nhạc lý (Việt + Anh) để đo độ gần về nghĩa của một đoạn văn với "nhạc lý và hòa âm".

Chỉ là bản đầu (T1). G6 thay bằng bộ phân loại huấn luyện trên corpus; neo vẫn dùng làm baseline so sánh."""

ANCHORS = [
    "Hợp âm ba nốt gồm nốt gốc, quãng ba và quãng năm. Hợp âm trưởng có quãng ba trưởng, hợp âm thứ có quãng ba thứ.",
    "Quãng được đặt tên theo số chữ cái và số nửa cung: quãng ba trưởng có bốn nửa cung, quãng năm đúng có bảy nửa cung.",
    "Âm giai trưởng gồm bảy bậc theo mẫu cung nguyên, cung nguyên, nửa cung, cung nguyên, cung nguyên, cung nguyên, nửa cung.",
    "Hợp âm bảy thêm quãng bảy vào hợp âm ba: Cmaj7, Dm7, G7 và Bm7b5 là các hợp âm bảy trong giọng Đô trưởng.",
    "Chức năng hòa âm gồm chủ âm, hạ át âm và át âm; tiến trình ii-V-I đưa hợp âm át về chủ.",
    "Số La Mã ghi bậc của hợp âm trong một giọng, chữ hoa cho hợp âm trưởng và chữ thường cho hợp âm thứ.",
    "Dấu thăng nâng nốt lên nửa cung, dấu giáng hạ nốt xuống nửa cung; cùng một phím đàn có thể có hai tên khác nhau.",
    "Khóa nhạc, khuông nhạc, nhịp và phách: nhịp bốn bốn có bốn phách mỗi ô nhịp, tiết tấu được ghi bằng các hình nốt.",
    "Hợp âm mượn từ giọng thứ cùng tên và át âm phụ làm vòng hợp âm pop thêm màu sắc.",
    "Voicing và voice leading: sắp xếp các nốt của hợp âm trên đàn piano sao cho các bè chuyển động mượt.",
    "A major triad is built from a root, a major third and a perfect fifth; a minor triad has a minor third.",
    "An interval is named by its number and quality, counted in letter names and semitones, such as a major third or perfect fifth.",
    "The major scale follows the pattern whole, whole, half, whole, whole, whole, half, and each degree has a harmonic function.",
    "Seventh chords add a seventh above the triad: major seventh, dominant seventh, minor seventh and half-diminished chords.",
    "Harmonic function groups chords into tonic, predominant and dominant, and a ii-V-I progression resolves to the tonic.",
    "Roman numerals label chords by scale degree in a key; uppercase for major chords and lowercase for minor chords.",
    "Key signatures, accidentals and enharmonic spellings: C sharp and D flat are the same pitch with different names.",
    "Modes, chord-scale theory and extended tensions such as ninths and thirteenths are used in jazz harmony.",
    "Secondary dominants and modal interchange borrow chords from other keys to colour a chord progression.",
    "Time signature, tempo and rhythm describe how beats are grouped and subdivided in a measure.",
]
