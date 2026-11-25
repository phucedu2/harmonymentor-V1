from __future__ import annotations
import argparse
import json
from pathlib import Path

from prepare_dataset import prepare, validate, verify_engine
from app.ai.tutor.engine_query import engine_answer
from app.ai.tutor.local_qlora import compact, validate_output
from app.ai.tutor.prompt import block

# Synthetic, deliberately unreviewed examples, never merged into approved datasets.
TRAIN = [
    ('Dm7 trong C trưởng là bậc mấy? Hãy ghi bằng số Ả Rập.', 'roman'),
    ('G7 trong C trưởng là bậc mấy? Cho mình số bậc.', 'roman'),
    ('Am7 trong C trưởng là bậc mấy? Đừng bỏ hậu tố hợp âm.', 'roman'),
    ('Em7 trong G trưởng là bậc mấy? Hãy ghi bằng chữ số Ả Rập.', 'roman'),
    ('Bm7 trong A trưởng là bậc mấy? Hãy nói số bậc.', 'roman'),
    ('Fmaj7 trong D thứ tự nhiên có số La Mã là gì?', 'roman'),
    ('Dm7 là bậc mấy?', 'missing_key'),
    ('G7 trong C là bậc mấy?', 'missing_mode'),
    ('Em trong A thứ là bậc mấy?', 'missing_minor'),
]
DEV = [
    ('A7 trong D trưởng là bậc mấy? Ghi bậc bằng số Ả Rập nhé.', 'roman'),
    ('Bm7 trong D trưởng là bậc mấy? Cho biết số bậc.', 'roman'),
    ('Gmaj7 trong E thứ tự nhiên là bậc mấy? Hãy ghi đầy đủ số La Mã và chất hợp âm.', 'roman'),
    ('Fmaj7 trong C là bậc mấy?', 'missing_mode'),
    ('Am7 trong E thứ là bậc mấy? Để xác định, bạn cần biết thêm thông tin gì?', 'missing_minor'),
]
SYSTEM = 'Bạn là trợ giảng âm nhạc. Chỉ trả lời theo dữ kiện được cung cấp; không tự đoán.'


def make(split, index, question, kind):
    result = engine_answer(question)
    facts = [{k: f[k] for k in ('tool', 'args', 'result')} for f in result.facts
             if f.get('tool') == 'get_roman_numeral']
    if kind == 'roman':
        if len(facts) != 1:
            raise ValueError(f'{split}-{index}: expected exactly one Roman fact: {facts}, {result.unknown}')
        numeral = facts[0]['result']
        if 'Ả Rập' in question:
            ordinal = {'I': 1, 'II': 2, 'III': 3, 'IV': 4, 'V': 5, 'VI': 6, 'VII': 7}
            import re
            root = re.match(r'(?:VII|III|VI|IV|II|V|I)', numeral.upper())
            if not root or root.group(0) not in ordinal:
                raise ValueError(f'{split}-{index}: unsupported Roman degree {numeral}')
            reply = f"Theo Music Engine, bậc {ordinal[root.group(0)]} là {numeral}."
        else:
            reply = 'Theo Music Engine, bậc là ' + numeral + '.'
        claims = facts
    else:
        if facts:
            raise ValueError(f'{split}-{index}: missing context unexpectedly produced Roman fact')
        reply = {'missing_key': 'Bạn cho mình biết giọng và dạng giọng (trưởng hoặc thứ) được không?',
                 'missing_mode': 'Bạn muốn xét giọng trưởng hay thứ? Nếu là thứ, bạn cho biết dạng thứ nhé.',
                 'missing_minor': 'Bạn muốn xét giọng thứ tự nhiên, thứ hòa thanh hay thứ giai điệu?'}[kind]
        claims = []
    user = '\n\n'.join(['MODE: chat', block('LESSON_CHUNKS', '[]'),
                         block('ENGINE_FACTS', json.dumps(facts, ensure_ascii=False)), block('QUESTION', question)])
    answer = dict(reply=reply, citations=[], engine_claims=claims, hint_level=0, suggested_actions=[], intent='concept')
    ident = f'roman-synth-{split}-{index:02}'
    row = dict(id=ident, group_id=ident, split=split, source_id='HM-SYNTHETIC-UNREVIEWED',
               reviewed_by_human=False, rights_cleared=False, allowed_block_ids=[],
               review_status='pending_human_review', category=kind,
               messages=[dict(role='system', content=SYSTEM), dict(role='user', content=user),
                         dict(role='assistant', content=compact(answer))])
    parsed, issues = validate_output(row['messages'][-1]['content'], user)
    if parsed is None or issues:
        raise ValueError(f'{ident}: validator rejected target {issues}')
    return row


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    rows = [make(split, i, q, kind) for split, items in [('train', TRAIN), ('dev', DEV)]
            for i, (q, kind) in enumerate(items, 1)]
    # Pair-disjoint between splits, in addition to exact-prompt and group checks.
    keys = {}
    for row in rows:
        facts = [f for f in engine_answer(row['messages'][1]['content'].split('kind="QUESTION">>>\n')[-1].split('\n<<<HM_END>>>')[0]).facts
                 if f.get('tool') == 'get_roman_numeral']
        for fact in facts:
            key = (fact['args'].get('key'), fact['args'].get('chord'), fact['args'].get('mode', 'major'))
            if key in keys and keys[key] != row['split']:
                raise ValueError(f'cross-split chord/key/mode leakage: {key}')
            keys[key] = row['split']
    validate(rows, True)
    verify_engine(rows)
    args.out.mkdir(parents=False, exist_ok=False)
    src = args.out / 'synthetic_candidates.jsonl'
    with src.open('x', encoding='utf-8', newline='\n') as f:
        for row in rows:
            f.write(compact(row) + '\n')
    summary = prepare(src, args.out / 'dataset', True, True)
    assert summary['production_ready'] is False
    print(json.dumps({'counts': summary['counts'], 'production_ready': False,
                      'input_sha256': summary['input_sha256'], 'outputs_sha256': summary['outputs_sha256']}))

if __name__ == '__main__':
    main()
