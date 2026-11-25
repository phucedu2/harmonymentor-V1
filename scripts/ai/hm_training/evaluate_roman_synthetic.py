from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from evaluate_v2 import evaluate, offline
from prepare_dataset import read_jsonl, sha256, validate, verify_engine
from train_qlora import DEFAULT_MODEL, resolve_offline_snapshot
from app.ai.tutor.local_qlora import MAX_SEQ, validate_output


def main():
    p = argparse.ArgumentParser()
    for arg in ('source', 'dataset', 'run', 'snapshot-root', 'out'):
        p.add_argument('--' + arg, required=True, type=Path)
    a = p.parse_args()
    offline()
    if a.out.exists() or not a.out.parent.is_dir() or shutil.disk_usage(a.out.parent).free < 2 * 2**30:
        raise SystemExit('STOP: fresh output and at least 2 GiB free disk required')
    rows = read_jsonl(a.source)
    summary = validate(rows, True)
    if (summary['counts'] != {'train': 9, 'dev': 5} or summary['demo_or_unapproved'] != len(rows)
            or summary['source_ids'] != ['HM-SYNTHETIC-UNREVIEWED']):
        raise SystemExit('STOP: unexpected or non-synthetic input')
    manifest = json.loads((a.dataset / 'manifest.json').read_text(encoding='utf-8'))
    if manifest['production_ready'] is not False or manifest['input_sha256'] != sha256(a.source):
        raise SystemExit('STOP: synthetic source manifest mismatch')
    for split in ('train', 'dev', 'test'):
        if sha256(a.dataset / (split + '.jsonl')) != manifest['outputs_sha256'][split]:
            raise SystemExit('STOP: split hash mismatch')
    verify_engine(rows)
    for r in rows:
        parsed, issues = validate_output(r['messages'][-1]['content'], r['messages'][1]['content'])
        if parsed is None or issues:
            raise SystemExit('STOP: synthetic reference failed strict validation')
    report = json.loads((a.run / 'training_report.json').read_text(encoding='utf-8'))
    revision = report['verified_local_revision']
    snap = resolve_offline_snapshot(a.snapshot_root, DEFAULT_MODEL, revision)
    adapter = a.run / 'adapter'
    conf = json.loads((adapter / 'adapter_config.json').read_text(encoding='utf-8'))
    if report['base_model'] != DEFAULT_MODEL or Path(conf['base_model_name_or_path']) != snap:
        raise SystemExit('STOP: adapter/base snapshot mismatch')
    weight = adapter / 'adapter_model.safetensors'
    provenance = {'base_model': DEFAULT_MODEL, 'revision': revision,
                  'adapter_sha256': sha256(weight), 'adapter_config_sha256': sha256(adapter / 'adapter_config.json'),
                  'source_sha256': sha256(a.source), 'synthetic_dev_count': 5,
                  'training_performed': False, 'network_namespace': 'loopback-only'}
    from unsloth import FastLanguageModel
    from peft import PeftModel
    import torch
    if not torch.cuda.is_available() or torch.cuda.device_count() != 1 or torch.cuda.mem_get_info()[0] < 9 * 2**30:
        raise SystemExit('STOP: single CUDA GPU with at least 9 GiB free required')
    base, tokenizer = FastLanguageModel.from_pretrained(model_name=str(snap), max_seq_length=MAX_SEQ,
        load_in_4bit=True, local_files_only=True, trust_remote_code=False, token=False,
        use_exact_model_name=True, use_safetensors=True)
    model = PeftModel.from_pretrained(base, str(adapter), is_trainable=False, local_files_only=True)
    FastLanguageModel.for_inference(model)
    model.eval()
    a.out.mkdir(exist_ok=False)
    (a.out / 'provenance.json').write_text(json.dumps(provenance, indent=2), encoding='utf-8')
    evaluate(model, tokenizer, [r for r in rows if r['split'] == 'dev'], a.out / 'synthetic_dev.jsonl')
    print('RESULTS', a.out, flush=True)

if __name__ == '__main__':
    main()
