"""Ánh xạ kỹ năng → srs_code, group_code theo docs/CP2_ANH_XA_KY_NANG.md (ADR-008).

Vì sao để trong code thay vì chỉ trong tài liệu: seed, mastery và hệ gợi ý cùng đọc một bảng, và
test nhóm M khẳng định bảng này khớp đúng tập kỹ năng trong skill_graph.SKILLS.
"""

from __future__ import annotations

from collections import Counter
from typing import Iterable

# Đổi bảng thì tăng phiên bản: vector KNN tính với bản khác nhau không so sánh được với nhau.
SKILL_GROUP_MAP_VERSION = "2026-10-30.adr008-b4"
POST_MVP = "post_mvp"

# Thứ tự cố định = thứ tự chiều của vector 14 chiều (ADR-008 mục 3). 10 mã đầu là mã SRS.
GROUP_CODES: tuple[str, ...] = (
    "note_names", "accidentals", "intervals", "major_scales", "minor_scales", "triads",
    "seventh_chords", "diatonic_chords", "progressions", "rhythm_basics",
    "chromatic_harmony", "pop_harmony", "jazz_voicing", "jazz_scales_tensions",
)
SRS_CODES: tuple[str, ...] = GROUP_CODES[:10]
# Nhóm chưa có kỹ năng nào; có kỹ năng mới thì gỡ khỏi đây (test M6 báo nếu quên).
GROUPS_WITHOUT_SKILLS: tuple[str, ...] = ("note_names", "minor_scales", "rhythm_basics", "pop_harmony")

MAPPING_ROWS: list[tuple[str, str, str]] = [
    ("pitch.spelling", "accidentals", "accidentals"),
    ("interval.naming", "intervals", "intervals"),
    ("chord.triad_formula", "triads", "triads"),
    ("chord.triad_build", "triads", "triads"),
    ("scale.major", "major_scales", "major_scales"),
    ("chord.seventh_quality", "seventh_chords", "seventh_chords"),
    ("chord.seventh_build", "seventh_chords", "seventh_chords"),
    ("roman.major_seventh", "diatonic_chords", "diatonic_chords"),
    ("function.tonic", "progressions", "progressions"),
    ("function.predominant", "progressions", "progressions"),
    ("function.dominant", "progressions", "progressions"),
    ("function.progression", "progressions", "progressions"),
    ("progression.ii_v_i", "progressions", "progressions"),
    # Thắng chốt 30/10: voicing L04 là post_mvp (vẫn chấm, vẫn tính hoàn thành bài, không cộng mastery).
    ("voicing.guide_tones", POST_MVP, "jazz_voicing"),
    ("voicing.voice_leading", POST_MVP, "jazz_voicing"),
    ("voicing.shell", POST_MVP, "jazz_voicing"),
    ("harmony.secondary_dominant.identify", POST_MVP, "chromatic_harmony"),
    ("harmony.secondary_dominant.build", POST_MVP, "chromatic_harmony"),
    ("harmony.secondary_dominant.apply", POST_MVP, "chromatic_harmony"),
    ("scale.parallel_minor", POST_MVP, "chromatic_harmony"),
    ("harmony.modal_interchange.identify", POST_MVP, "chromatic_harmony"),
    ("harmony.modal_interchange.apply", POST_MVP, "chromatic_harmony"),
    ("tension.naming", POST_MVP, "jazz_scales_tensions"),
    ("mode.basic", POST_MVP, "jazz_scales_tensions"),
    ("chord_scale.basic", POST_MVP, "jazz_scales_tensions"),
    ("chord_scale.context", POST_MVP, "jazz_scales_tensions"),
]
SKILL_MAPPING: dict[str, tuple[str, str]] = {skill: (srs, group) for skill, srs, group in MAPPING_ROWS}


# Kỹ năng Quản trị viên tự thêm (ADR-037, Phúc 9A 25/11/2026): chọn một trong 10 nhóm MVP nên tính mastery và vào vector
# gợi ý như kỹ năng gốc. Bảng gốc ở trên bất biến; phần này đọc từ cột skills.srs_code/group_code, nhớ tạm 30 giây để
# `is_mvp` (gọi theo từng dòng mastery) không truy vấn CSDL mỗi lần. Admin đổi thì `reload_custom_mapping()` làm mới ngay.
CUSTOM_PREFIX = "custom."
CUSTOM_TTL_SECONDS = 30.0
_custom: dict[str, tuple[str, str]] = {}
_custom_at = float("-inf")


def reload_custom_mapping() -> None:
    global _custom, _custom_at
    import time

    _custom_at = time.monotonic()
    try:
        from sqlalchemy import select

        from ..db.models import Skill
        from ..db.session import SessionLocal

        with SessionLocal() as db:
            rows = db.execute(select(Skill.id, Skill.srs_code, Skill.group_code).where(Skill.id.like(CUSTOM_PREFIX + "%"))).all()
        # Chỉ nhận kỹ năng có nhóm MVP hợp lệ và group = srs (quy tắc validate_mapping); dòng khác coi như "ngoài hệ gợi ý".
        _custom = {sid: (srs, grp) for sid, srs, grp in rows if srs in SRS_CODES and grp == srs}
    except Exception:   # noqa: BLE001 - CSDL chưa sẵn sàng (lệnh dựng chỉ mục, test thuần): giữ bảng cũ, thử lại sau TTL
        pass


def custom_mapping() -> dict[str, tuple[str, str]]:
    import time

    if time.monotonic() - _custom_at > CUSTOM_TTL_SECONDS:
        reload_custom_mapping()
    return _custom


def mapping_of(skill_id: str) -> tuple[str, str] | None:
    """(srs_code, group_code) của kỹ năng gốc hoặc kỹ năng tự thêm đã có nhóm; None nếu không có trong bảng nào."""
    entry = SKILL_MAPPING.get(skill_id)
    if entry is None and skill_id.startswith(CUSTOM_PREFIX):
        entry = custom_mapping().get(skill_id)
    return entry


def is_mvp(skill_id: str) -> bool:
    entry = mapping_of(skill_id)
    return entry is not None and entry[0] != POST_MVP


def validate_mapping(skill_ids: Iterable[str], rows: list[tuple[str, str, str]]) -> list[str]:
    """Trả danh sách lỗi (rỗng = hợp lệ). Dùng cho test M8/M9 và để seed từ chối bảng hỏng."""
    errors: list[str] = []
    wanted = set(skill_ids)
    counts = Counter(row[0] for row in rows)
    errors += [f"kỹ năng trùng trong bảng ánh xạ: {s}" for s, n in counts.items() if n > 1]
    errors += [f"kỹ năng chưa có ánh xạ: {s}" for s in sorted(wanted - set(counts))]
    errors += [f"ánh xạ trỏ tới kỹ năng không tồn tại: {s}" for s in sorted(set(counts) - wanted)]
    for skill, srs, group in rows:
        if srs not in SRS_CODES and srs != POST_MVP:
            errors.append(f"{skill}: srs_code lạ {srs}")
        if group not in GROUP_CODES:
            errors.append(f"{skill}: group_code lạ {group}")
        if srs != POST_MVP and group != srs:
            errors.append(f"{skill}: kỹ năng MVP phải có group_code = srs_code")
        if (group in GROUP_CODES[10:]) != (srs == POST_MVP):
            errors.append(f"{skill}: nhóm 11–14 khi và chỉ khi post_mvp")
    return errors
