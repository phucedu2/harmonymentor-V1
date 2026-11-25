from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

from prepare_dataset import read_jsonl, sha256, validate, verify_engine
from app.ai.tutor.local_qlora import BLOCK, CLAIM, evidence, validate_output


def question(row):
    return next((s for k, s in BLOCK.findall(row['messages'][1]['content']) if k == 'QUESTION'), '')


def normalized(text):
    return re.sub(r'\s+', ' ', text.casefold()).strip()


def factkeys(row):
    return {(f['tool'], json.dumps(f['args'], sort_keys=True, ensure_ascii=False))
            for f in evidence(row['messages'][1]['content'], 'ENGINE_FACTS', CLAIM)
            if f['tool'] == 'get_roman_numeral'}


def main():
    p = argparse.ArgumentParser()
    for name in ('candidates', 'candidate-manifest', 'baseline-dir', 'baseline-report'):
        p.add_argument('--' + name, required=True, type=Path)
    args = p.parse_args()
    rows = read_jsonl(args.candidates)
    summary = validate(rows, True)
    verify_engine(rows)
    manifest = json.loads(args.candidate_manifest.read_text(encoding='utf-8'))
    if manifest['input_sha256'] != sha256(args.candidates) or manifest['production_ready'] is not False:
        raise SystemExit('candidate provenance mismatch')
    prior = json.loads(args.baseline_report.read_text(encoding='utf-8'))['dataset_manifest']
    baseline = {}
    for split in ('train', 'dev', 'test'):
        path = args.baseline_dir / (split + '.jsonl')
        if sha256(path) != prior['outputs_sha256'][split]:
            raise SystemExit(f'baseline {split} hash mismatch')
        baseline[split] = read_jsonl(path)
    problems = []
    for row in rows:
        _, issues = validate_output(row['messages'][-1]['content'], row['messages'][1]['content'])
        if issues:
            problems.append({'id': row['id'], 'issues': issues})
    comparisons = []
    for row in rows:
        # Candidate train vs historical holdouts; candidate dev vs all historical splits.
        targets = ('dev', 'test') if row['split'] == 'train' else ('train', 'dev', 'test')
        q = normalized(question(row))
        keys = factkeys(row)
        for split in targets:
            for index, old in enumerate(baseline[split], 1):
                oldq = normalized(question(old))
                score = SequenceMatcher(None, q, oldq).ratio() if q and oldq else 0
                overlap = bool(keys & factkeys(old))
                if (q and q == oldq) or score >= 0.82 or overlap:
                    comparisons.append({'candidate_id': row['id'], 'baseline_split': split,
                                        'baseline_row': index, 'same_question': bool(q and q == oldq),
                                        'similarity': round(score, 3), 'same_engine_fact': overlap})
    print(json.dumps({'candidate_counts': summary['counts'], 'unreviewed': summary['demo_or_unapproved'],
                      'categories': dict(Counter((r['split'] + ':' + r['category']) for r in rows)),
                      'candidate_validation_errors': problems,
                      'possible_overlap_flags': comparisons,
                      'note': 'Flags indicate potential overlap; same fact or similarity alone does not prove leakage. Baseline dev/test may already have been inspected, so design a fresh untouched holdout.',
                      'baseline_counts': {k: len(v) for k, v in baseline.items()},
                      'candidate_sha256': sha256(args.candidates),
                      'production_ready': False}, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
