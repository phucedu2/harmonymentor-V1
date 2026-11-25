"""Prepare original synthetic V2 candidates; never self-approve them."""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from prepare_dataset import prepare, read_jsonl, sha256, validate, verify_engine
from app.ai.tutor.local_qlora import compact, validate_output
from app.ai.tutor.prompt import block

SAMPLES = (
    ('ground', 'Theo giáo trình, pedal point được giải thích thế nào?', 'Mình chưa có đoạn học liệu về nốt trì tục. Bạn gửi đoạn bài liên quan để mình giải thích theo giáo trình nhé.'),
    ('ground', 'Tóm tắt phần giáo trình nói về chuỗi quãng tám song song.', 'Mình chưa có trích đoạn giáo trình về quãng tám song song, nên chưa thể tóm tắt. Bạn gửi đoạn bài cần xem giúp mình nhé.'),
    ('ground', 'Bài học của mình định nghĩa nhịp hemiola ra sao?', 'Mình chưa có học liệu về hemiola trong ngữ cảnh này. Bạn gửi đoạn có định nghĩa để mình giải thích đúng theo bài nhé.'),
    ('ground', 'Giáo trình nhận xét thế nào về cách dùng bass kiểu Alberti?', 'Mình chưa có trích đoạn về bass Alberti nên chưa thể nói giáo trình nhận xét thế nào. Bạn có thể gửi phần đó không?'),
    ('context', 'Gm7 là hợp âm bậc mấy vậy?', 'Bạn đang xét giọng nào và dạng giọng nào? Mình cần biết giọng trước khi xác định bậc của Gm7.'),
    ('context', 'Trong E trưởng thì hợp âm này mang số La Mã nào?', 'Mình biết giọng là E trưởng, nhưng chưa thấy ký hiệu hợp âm. Bạn gửi ký hiệu để mình xác định bậc nhé.'),
    ('context', 'Tính quãng đi lên bắt đầu từ nốt B♭.', 'Bạn cho mình biết nốt đích nhé. Chỉ có nốt B♭ thì chưa đủ để xác định quãng.'),
    ('context', 'Dựng âm giai thứ tự nhiên giúp mình.', 'Bạn muốn dựng âm giai thứ tự nhiên bắt đầu từ nốt nào? Mình cần nốt chủ để tiếp tục.'),
    ('context', 'Trong B thứ, hợp âm Em mang số La Mã nào?', 'Bạn muốn xét B thứ tự nhiên, thứ hòa thanh hay thứ giai điệu? Mình cần biết dạng giọng thứ để không phân tích nhầm.'),
    ('scope', 'Tính giúp mình tiền điện tháng này.', 'Mình hỗ trợ nhạc lý và âm nhạc, không tính hóa đơn điện. Nếu bạn đang học nhạc, bạn có thể hỏi mình về nhịp hoặc quãng nhé.'),
    ('scope', 'Bạn giải giúp mình bài hình học về đường tròn được không?', 'Mình không giải bài hình học. Bạn có thể hỏi mình về đọc nhạc, hợp âm hoặc âm giai nhé.'),
    ('scope', 'Soạn giúp mình nội quy cho chung cư.', 'Mình không hỗ trợ soạn nội quy chung cư; vai trò của mình là giúp bạn học nhạc lý và âm nhạc.'),
    ('scope', 'Bạn gợi ý cách chọn thẻ tín dụng nhé.', 'Mình không tư vấn chọn thẻ tín dụng. Nếu bạn có câu hỏi về nhạc lý hoặc cách luyện tập, mình có thể hỗ trợ.'),
)


def write_jsonl(path, rows):
    with path.open('x', encoding='utf-8', newline='\n') as f:
        for row in rows:
            f.write(compact(row) + '\n')


def main():
    ap = argparse.ArgumentParser()
    for p in ('approved-source', 'approved-manifest', 'smoke-source', 'out'):
        ap.add_argument('--' + p, required=True, type=Path)
    a = ap.parse_args()
    original = read_jsonl(a.approved_source)
    manifest = json.loads(a.approved_manifest.read_text(encoding='utf-8'))
    assert manifest['production_ready'] and sha256(a.approved_source) == manifest['input_sha256']
    assert validate(original, False)['counts'] == {'train': 50, 'dev': 14, 'test': 2}
    smoke = read_jsonl(a.smoke_source)
    held = [r for r in smoke if r['split'] == 'dev']
    assert [r['id'].removeprefix('s14-dev-') for r in held] == ['engine', 'citation', 'grounding', 'context', 'scope']
    system = original[0]['messages'][0]['content']
    candidates = []
    for n, (kind, q, reply) in enumerate(SAMPLES, 1):
        ident = f'v2-negative-{n:02}'
        user = '\n\n'.join(['MODE: ' + ('chat' if kind != 'scope' else 'general_music'),
                            block('LESSON_CHUNKS', '[]'), block('ENGINE_FACTS', '[]'), block('QUESTION', q)])
        answer = dict(reply=reply, citations=[], engine_claims=[], hint_level=0, suggested_actions=[],
                      intent='out_of_scope' if kind == 'scope' else 'concept')
        candidates.append(dict(id=ident, group_id=ident, split='train', source_id='HM-V2-ORIGINAL-SYNTHETIC',
                               reviewed_by_human=False, rights_cleared=False, allowed_block_ids=[],
                               review_status='pending_user_approval', category=kind,
                               messages=[dict(role='system', content=system), dict(role='user', content=user),
                                         dict(role='assistant', content=compact(answer))]))
    # The prepared smoke set contains only one entirely synthetic training target.
    smoke_rows = candidates[:1] + held
    for rows in (original + candidates, smoke_rows):
        validate(rows, True)
        verify_engine(rows)
        for r in rows:
            m = r['messages']
            parsed, issues = validate_output(m[-1]['content'], m[1]['content'])
            if not parsed or issues:
                raise ValueError(f"{r['id']}: strict output validation failed: {issues}")
    a.out.mkdir(exist_ok=False)
    write_jsonl(a.out / 'candidate_additions.jsonl', candidates)
    write_jsonl(a.out / 'candidate_combined.jsonl', original + candidates)
    write_jsonl(a.out / 'smoke_source.jsonl', smoke_rows)
    # Candidate is intentionally not exported with a full-training manifest.
    smoke_summary = prepare(a.out / 'smoke_source.jsonl', a.out / 'smoke_data', True, True)
    assert smoke_summary['production_ready'] is False
    print(json.dumps(dict(candidates=len(candidates), categories=Counter(r['category'] for r in candidates),
                          smoke=smoke_summary['counts'], full_training_ready=False), ensure_ascii=False))


if __name__ == '__main__':
    main()
