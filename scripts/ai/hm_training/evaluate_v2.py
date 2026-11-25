"""Offline V2 evaluation: preserve raw predictions and compare metadata separately from prose."""
from __future__ import annotations

import argparse
import json
import os
import socket
from pathlib import Path

from app.ai.tutor.local_qlora import MAX_SEQ, compact, generate
from app.ai.tutor.schema import parse_answer
from prepare_dataset import read_jsonl, sha256
from train_qlora import DEFAULT_MODEL, resolve_offline_snapshot


def offline():
    if ({name for _, name in socket.if_nameindex()} != {'lo'}
            or any(os.getenv(k) != '1' for k in ('HF_HUB_OFFLINE', 'TRANSFORMERS_OFFLINE', 'HF_DATASETS_OFFLINE'))):
        raise SystemExit('STOP: evaluation requires offline flags and an isolated network namespace')


def evaluate(model, tokenizer, rows, path):
    with path.open('x', encoding='utf-8', newline='\n') as report:
        for index, row in enumerate(rows, 1):
            turns = row['messages']
            expected = json.loads(turns[-1]['content'])
            result = generate(model, tokenizer, turns[:-1])
            issues = list(result.issues)
            actual = parse_answer(result.raw) if not {'json','schema','intent','schema_or_evidence'}.intersection(issues) else None
            if actual:
                obj = actual.model_dump()
                for field in ('intent', 'citations', 'engine_claims', 'hint_level'):
                    if obj[field] != expected[field]:
                        issues.append('reference_' + field)
            item = dict(id=row.get('id', index), prompt=turns[1]['content'], raw=result.raw, tokens=result.tokens,
                        parser=actual is not None, validation=list(result.issues), metadata_issues=issues,
                        expected=expected)
            report.write(compact(item) + '\n')
            report.flush()
            print('V2_EVAL', item['id'], item['tokens'], issues, flush=True)


def main():
    ap = argparse.ArgumentParser()
    for k in ('run', 'data', 'snapshot-root', 'smoke-source', 'out'):
        ap.add_argument('--' + k, type=Path, required=True)
    ap.add_argument('--include-test', action='store_true')
    args = ap.parse_args()
    offline()
    if args.out.exists():
        raise SystemExit('STOP: output already exists')
    report = json.loads((args.run / 'training_report.json').read_text(encoding='utf-8'))
    revision = report['verified_local_revision']
    snap = resolve_offline_snapshot(args.snapshot_root, DEFAULT_MODEL, revision)
    adapter = args.run / 'adapter'
    conf = json.loads((adapter / 'adapter_config.json').read_text(encoding='utf-8'))
    if report['base_model'] != DEFAULT_MODEL or Path(conf['base_model_name_or_path']) != snap:
        raise SystemExit('STOP: adapter/base snapshot mismatch')
    rows = {}
    for key in ('dev', 'test') if args.include_test else ('dev',):
        path = args.data / (key + '.jsonl')
        if sha256(path) != report['dataset_manifest']['outputs_sha256'][key]:
            raise SystemExit(f'STOP: {key} snapshot mismatch')
        rows[key] = read_jsonl(path)
    rows['smoke'] = [r for r in read_jsonl(args.smoke_source) if r['split'] == 'dev']
    if len(rows['smoke']) != 5:
        raise SystemExit('STOP: expected five held-out smoke prompts')
    from unsloth import FastLanguageModel
    from peft import PeftModel
    import torch
    if torch.cuda.device_count() != 1 or torch.cuda.mem_get_info()[0] < 9 * 2**30:
        raise SystemExit('STOP: dedicated GPU with 9 GiB free required')
    base, tokenizer = FastLanguageModel.from_pretrained(model_name=str(snap), max_seq_length=MAX_SEQ,
        load_in_4bit=True, local_files_only=True, trust_remote_code=False, token=False,
        use_exact_model_name=True, use_safetensors=True)
    model = PeftModel.from_pretrained(base, str(adapter), is_trainable=False, local_files_only=True)
    FastLanguageModel.for_inference(model)
    model.eval()
    args.out.mkdir(exist_ok=False)
    for split in ('dev', 'smoke', 'test'):
        if split in rows:
            evaluate(model, tokenizer, rows[split], args.out / (split + '.jsonl'))


if __name__ == '__main__':
    main()
