"""Liên kết học thêm bên ngoài cho từng bài (GĐ5, 09/11/2026).

Vì sao có file này: thầy góp ý nên chỉ cho người học nơi học tiếp ngoài HarmonyMentor. Chỉ dùng tài liệu
miễn phí, mở, của trường đại học (sách giáo khoa mở), không giới thiệu khóa có phí. App chỉ hiện liên kết mở tab
mới, không nhúng nội dung, không chép bài.

Claude chọn danh sách và đã kiểm từng địa chỉ còn mở ngày 09/11/2026; mọi mục để `status: "draft"` (ẩn với người
học, như khối nháp) cho tới khi Đạt duyệt nội dung có khớp bài hay không. Duyệt xong thì xóa `status` của mục đó.
"""

from __future__ import annotations

from typing import Any

from .versioning import block_visible

OMT = "Open Music Theory (Gotham và cộng sự, sách mở CC BY-SA 4.0)"
MT21C = "Music Theory for the 21st-Century Classroom (Robert Hutchinson, Đại học Puget Sound, sách mở)"
OMT_URL = "https://viva.pressbooks.pub/openmusictheory/chapter/"
MT21C_URL = "https://musictheory.pugetsound.edu/mt21c/"


def _r(title: str, source: str, url: str, why_vi: str) -> dict[str, Any]:
    return {"title": title, "source": source, "url": url, "language": "en", "free": True,
            "why_vi": why_vi, "status": "draft"}


EXTERNAL_RESOURCES: dict[str, list[dict[str, Any]]] = {
    "L01": [
        _r("The Keyboard and the Grand Staff", OMT, OMT_URL + "the-keyboard-and-grand-staff/",
           "Ôn tên phím đàn và vị trí nốt trên khuông, nền cho phần đếm nửa cung."),
        _r("Intervals", OMT, OMT_URL + "intervals/", "Đếm số quãng và gọi tên P, M, m, A, d như Bài 1."),
        _r("Triads", OMT, OMT_URL + "triads/", "Bốn loại hợp âm ba nốt và cách dựng từ nốt gốc."),
        _r("Intervals", MT21C, MT21C_URL + "Intervals.html", "Cách giải thích thứ hai về quãng, kèm bài tập."),
    ],
    "L02": [
        _r("Major Scales", OMT, OMT_URL + "major-scales/", "Công thức nguyên cung, nửa cung của âm giai trưởng."),
        _r("Seventh Chords", OMT, OMT_URL + "seventh-chords/", "Năm loại hợp âm bảy, gồm maj7, 7, m7, m7b5."),
        _r("Roman Numerals", OMT, OMT_URL + "roman-numerals/", "Ký hiệu số La Mã cho hợp âm trong giọng."),
        _r("Diatonic Chords in Major", MT21C, MT21C_URL + "DiatonicChordsInMajor.html",
           "Bảng hợp âm điệu tính trong giọng trưởng để đối chiếu."),
    ],
    "L03": [
        _r("Harmonic Function", MT21C, MT21C_URL + "HarmonicFunction.html", "Ba chức năng Tonic, Predominant, Dominant."),
        _r("Performing Harmonic Analysis Using the Phrase Model", OMT,
           OMT_URL + "performing-harmonic-analysis-using-the-phrase-model/",
           "Đọc chuỗi hợp âm theo mô hình T → PD → D → T."),
    ],
    "L04": [
        _r("ii–V–I", OMT, OMT_URL + "ii-v-i/", "Vòng ii–V–I trong jazz, đúng chủ đề Bài 4."),
        _r("Jazz Voicings", OMT, OMT_URL + "jazz-voicings/", "Cách bỏ nốt và giữ 3, 7 khi chơi hợp âm jazz."),
        _r("Jazz Chord Voicings", MT21C, MT21C_URL + "JazzChordVoicings.html", "Ví dụ voicing trên piano kèm ký âm."),
    ],
    "L05": [
        _r("Tonicization", OMT, OMT_URL + "tonicization/", "Hợp âm át phụ làm một hợp âm tạm thời thành chủ."),
        _r("Secondary Dominant Chords", MT21C, MT21C_URL + "SecondaryDominants.html",
           "Cách viết và nhận ra V/V, V7/ii, kèm bài tập."),
    ],
}


def resources_for(lesson_id: str) -> list[dict[str, Any]]:
    """Liên kết người học được thấy: mục nháp chỉ hiện khi bật SHOW_DRAFT_CONTENT (giống khối nháp)."""
    return [{k: v for k, v in item.items() if k != "status"} | {"draft": item.get("status") == "draft"}
            for item in EXTERNAL_RESOURCES.get(lesson_id, []) if block_visible(item)]
