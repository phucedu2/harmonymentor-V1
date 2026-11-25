from __future__ import annotations
import argparse, json
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path
from prepare_roman_synthetic import make
from prepare_dataset import read_jsonl, sha256, verify_engine
from audit_roman_candidates import question, normalized, factkeys
from app.ai.tutor.local_qlora import compact

# Untouched by model inference/training. Synthetic; requires human/rights review.
CASES = [
    ('Cmaj7 trong G trưởng là bậc mấy?', 'roman'),
    ('Em7 trong D trưởng là bậc mấy?', 'roman'),
    ('C7 trong F trưởng là bậc mấy?', 'roman'),
    ('Gm7 trong F trưởng là bậc mấy?', 'roman'),
    ('Bm7 trong G trưởng là bậc mấy?', 'roman'),
    ('Fmaj7 là bậc mấy?', 'missing_key'),
    ('A7 trong D là bậc mấy?', 'missing_mode'),
    ('Dm7 trong A thứ là bậc mấy?', 'missing_minor'),
]

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--out', type=Path, required=True)
    p.add_argument('--candidates', type=Path, required=True)
    p.add_argument('--baseline-dir', type=Path, required=True)
    p.add_argument('--baseline-report', type=Path, required=True)
    a = p.parse_args()
    manifest = json.loads(a.baseline_report.read_text(encoding='utf-8'))['dataset_manifest']
    reference = []
    for split in ('train', 'dev', 'test'):
        path = a.baseline_dir / (split + '.jsonl')
        if sha256(path) != manifest['outputs_sha256'][split]:
            raise ValueError('baseline hash mismatch: ' + split)
        reference.extend(('baseline-' + split, i, r) for i, r in enumerate(read_jsonl(path), 1))
    reference.extend(('candidate-' + r['split'], i, r) for i, r in enumerate(read_jsonl(a.candidates), 1))
    rows = [make('holdout', i, q, kind) for i, (q, kind) in enumerate(CASES, 1)]
    verify_engine(rows)
    flags = []
    for row in rows:
        q = normalized(question(row)); keys = factkeys(row)
        for source, index, other in reference:
            otherq = normalized(question(other))
            same = bool(q and q == otherq)
            overlap = bool(keys & factkeys(other))
            ratio = SequenceMatcher(None, q, otherq).ratio() if q and otherq else 0
            if same or overlap:
                raise ValueError(f"exact question or Engine fact overlap: {row['id']} {source} row {index}")
            if ratio >= 0.82:
                flags.append({'id': row['id'], 'reference': source, 'row': index, 'similarity': round(ratio, 3)})
    a.out.mkdir(parents=False, exist_ok=False)
    file = a.out / 'untouched_holdout.jsonl'
    with file.open('x', encoding='utf-8', newline='\n') as f:
        for row in rows:
            f.write(compact(row) + '\n')
    report = {'count': len(rows), 'categories': dict(Counter(r['category'] for r in rows)),
              'input_sha256': sha256(file), 'candidate_sha256': sha256(a.candidates),
              'baseline_hashes': manifest['outputs_sha256'], 'similarity_flags': flags,
              'status': 'synthetic_unreviewed_not_evaluated', 'production_ready': False,
              'limitation': 'Not a representative statistical evaluation; heuristic checks do not guarantee independence.'}
    with (a.out / 'manifest.json').open('x', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
