"""Supervised QLoRA of Qwen3-4B-Instruct-2507 for HarmonyMentor TutorAnswer JSON.

Run on a CUDA GPU only after prepare_dataset.py. Does NOT train from scratch.
Only the LoRA adapter is saved; the model is downloaded from Hugging Face.
"""
from __future__ import annotations

import argparse
import hashlib
import inspect
import json
import math
import os
import shutil
import re
from datetime import datetime, timezone
from pathlib import Path
from importlib.metadata import version, PackageNotFoundError
from training_safety import (checked_config, preflight_tokenizer, check_collator_labels,
                             preflight_assistant_only, encode_assistant_only, AssistantOnlyCollator)

DEFAULT_MODEL = "unsloth/Qwen3-4B-Instruct-2507-unsloth-bnb-4bit"


def validate_model_selection(model_name: str, revision: str) -> None:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", model_name):
        raise SystemExit("STOP: specify a Hugging Face repository ID, not a local path")
    if not re.fullmatch(r"[0-9a-f]{40}", revision or ""):
        raise SystemExit("STOP: --model-revision must be a full lowercase 40-character commit SHA")


def verify_loaded_identity(model, tokenizer, model_name: str, revision: str) -> None:
    config = getattr(model, "config", None)
    kwargs = getattr(tokenizer, "init_kwargs", {}) or {}
    model_revision = getattr(config, "_commit_hash", None)
    tokenizer_revision = kwargs.get("_commit_hash")
    model_source = getattr(config, "_name_or_path", None)
    tokenizer_source = kwargs.get("name_or_path") or getattr(tokenizer, "name_or_path", None)
    if (model_revision != revision or tokenizer_revision != revision
            or model_source != model_name or tokenizer_source != model_name):
        raise SystemExit("STOP: cannot verify exact repository and revision for both model and tokenizer")


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_split(data_dir: Path, split: str) -> list[dict]:
    path = data_dir / (split + ".jsonl")
    return [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines() if s.strip()]


def resolve_offline_snapshot(root, repo, revision):
    cache = root.resolve() / "cache"
    snap = cache / ("models--" + repo.replace("/", "--")) / "snapshots" / revision
    manifest = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    report = json.loads((root / "verification-report.json").read_text(encoding="utf-8"))
    entries = {x["path"]: x for x in manifest}
    if (report["repository"] != repo or report["revision"] != revision or Path(report["snapshot"]) != snap
            or snap.resolve() != snap or len(entries) != len(manifest)
            or set(entries) != {p.name for p in snap.iterdir()}
            or not {"model.safetensors", "config.json", "tokenizer_config.json"} <= set(entries)):
        raise SystemExit("STOP: snapshot identity mismatch")
    for name, item in entries.items():
        path = (snap / name).resolve(strict=True)
        if not path.is_relative_to(cache) or path.stat().st_size != item["size"] or item["lastCommit"]["id"] != revision:
            raise SystemExit("STOP: snapshot file metadata mismatch")
        lfs = item.get("lfs")
        digest = hashlib.sha256() if lfs else hashlib.sha1(f'blob {item["size"]}\0'.encode())
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(2**22), b""):
                digest.update(block)
        if digest.hexdigest() != (lfs["oid"] if lfs else item["oid"]):
            raise SystemExit("STOP: snapshot checksum mismatch")
    for name in ("config.json", "tokenizer_config.json"):
        if json.loads((snap / name).read_text(encoding="utf-8")).get("auto_map"):
            raise SystemExit("STOP: custom loader map in snapshot")
    return snap


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--model-revision", required=True, help="Full immutable Hugging Face commit SHA")
    parser.add_argument("--epochs", type=float, default=2.0)
    parser.add_argument("--max-seq-length", type=int, default=1024)
    parser.add_argument("--max-steps", type=int, default=-1)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--seed", type=int, default=20261116)
    parser.add_argument("--allow-demo", action="store_true", help="one-off GPU training smoke test only")
    parser.add_argument("--smoke-no-save", action="store_true", help="do not save adapter/checkpoints for an isolated smoke test")
    parser.add_argument("--verified-snapshot-root", type=Path)
    args = parser.parse_args()
    validate_model_selection(args.model, args.model_revision)

    if args.allow_demo != args.smoke_no_save:
        raise SystemExit("STOP: demo is restricted to the one-step, no-save smoke test")
    if args.output.exists():
        raise SystemExit("STOP: output already exists; choose a fresh directory")
    manifest_path = args.data_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if set(manifest["outputs_sha256"]) != {"train", "dev", "test"}:
        raise SystemExit("STOP: incomplete split hashes")
    for split, digest in manifest["outputs_sha256"].items():
        if file_hash(args.data_dir / (split + ".jsonl")) != digest:
            raise SystemExit(f"STOP: {split}.jsonl changed after dataset validation")
    if not manifest.get("production_ready") and not args.allow_demo:
        raise SystemExit("STOP: dataset unapproved or too small (min 50 reviewed examples). Demo: --allow-demo")
    train_rows = read_split(args.data_dir, "train")
    dev_rows = read_split(args.data_dir, "dev")
    if not train_rows or not dev_rows:
        raise SystemExit("Both train and dev must be non-empty")

    snap = None
    if args.verified_snapshot_root:
        snap = resolve_offline_snapshot(args.verified_snapshot_root, args.model, args.model_revision)
    if args.smoke_no_save:
        import socket
        if (not args.allow_demo or args.max_steps != 1 or args.output.exists()
                or manifest.get("production_ready") is not False or not args.verified_snapshot_root
                or os.getenv("HF_HUB_OFFLINE") != "1"
                or {name for _, name in socket.if_nameindex()} != {"lo"}
                or shutil.disk_usage(args.output.parent).free < 20 * 2**30):
            raise SystemExit("STOP: smoke requires isolated offline demo, one step and fresh output")
        train_rows = train_rows[:1]
    elif args.verified_snapshot_root is None and os.getenv("HF_HUB_OFFLINE") == "1":
        raise SystemExit("STOP: offline full training requires --verified-snapshot-root")

    try:
        import torch
        from datasets import Dataset
        from unsloth import FastLanguageModel, is_bfloat16_supported
        from trl import SFTConfig, SFTTrainer
    except ImportError as exc:
        raise SystemExit("Install GPU packages via Unsloth official instructions first") from exc
    if not torch.cuda.is_available():
        raise SystemExit("CUDA GPU unavailable. Use Colab/Kaggle/NVIDIA GPU; CPU RAG still works without GPU")

    if snap is not None:
        if torch.cuda.device_count() != 1 or torch.cuda.mem_get_info()[0] < 9 * 2**30:
            raise SystemExit("STOP: smoke needs one GPU with at least 9 GiB free VRAM")
        from transformers import AutoTokenizer
        verified_tok = AutoTokenizer.from_pretrained(str(snap), local_files_only=True, trust_remote_code=False, token=False)
        verified_rows = [encode_assistant_only(verified_tok, row, args.max_seq_length, "offline preflight")
                         for row in train_rows + dev_rows]
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=str(snap) if snap is not None else args.model, max_seq_length=args.max_seq_length, dtype=None,
        load_in_4bit=True, revision=args.model_revision, trust_remote_code=False,
        **({"local_files_only": True, "token": False, "use_exact_model_name": True, "use_safetensors": True} if snap else {}),
    )
    if snap is None:
        verify_loaded_identity(model, tokenizer, args.model, args.model_revision)
    elif [encode_assistant_only(tokenizer, row, args.max_seq_length, "loaded tokenizer")
          for row in train_rows + dev_rows] != verified_rows:
        raise SystemExit("STOP: loaded tokenizer differs from verified snapshot")
    mask_report = {
        "train": preflight_assistant_only(tokenizer, train_rows, args.max_seq_length, "train"),
        "dev": preflight_assistant_only(tokenizer, dev_rows, args.max_seq_length, "dev"),
    }
    train_encoded = [encode_assistant_only(tokenizer, row, args.max_seq_length, f"train[{i}]") for i, row in enumerate(train_rows)]
    dev_encoded = [encode_assistant_only(tokenizer, row, args.max_seq_length, f"dev[{i}]") for i, row in enumerate(dev_rows)]
    model = FastLanguageModel.get_peft_model(
        model, r=16,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_alpha=16, lora_dropout=0, bias="none",
        use_gradient_checkpointing="unsloth", random_state=args.seed,
    )
    args.output.mkdir(parents=True, exist_ok=False)
    cfg = {
        "output_dir": str(args.output / "checkpoints"),
        "num_train_epochs": args.epochs,
        "per_device_train_batch_size": 1,
        "per_device_eval_batch_size": 1,
        "gradient_accumulation_steps": 8,
        "learning_rate": args.learning_rate,
        "warmup_ratio": 0.05,
        "weight_decay": 0.01,
        "lr_scheduler_type": "cosine",
        "optim": "adamw_8bit",
        "logging_steps": 2,
        "eval_strategy": "epoch",
        "save_strategy": "epoch",
        "save_total_limit": 2,
        "load_best_model_at_end": True,
        "metric_for_best_model": "eval_loss",
        "greater_is_better": False,
        "fp16": not is_bfloat16_supported(),
        "bf16": is_bfloat16_supported(),
        "report_to": "none",
        "seed": args.seed,
        "assistant_only_loss": False,
        "pretokenized_assistant_only": True,
        "packing": False,
        "remove_unused_columns": False,
        "dataset_kwargs": {"skip_prepare_dataset": True},
        "max_length": args.max_seq_length,
    }
    if args.max_steps > 0:
        cfg["max_steps"] = args.max_steps
    if args.smoke_no_save:
        for key in ("save_total_limit", "metric_for_best_model", "greater_is_better", "warmup_ratio"):
            cfg.pop(key)
        cfg.update(save_strategy="no", eval_strategy="no", load_best_model_at_end=False,
                   gradient_accumulation_steps=1, warmup_steps=0,
                   lr_scheduler_type="constant",
                   logging_steps=1, dataloader_num_workers=0)
    if "warmup_ratio" in cfg and "warmup_ratio" not in inspect.signature(SFTConfig).parameters:
        # TRL 1.14.2 exposes warmup_steps but not warmup_ratio; the 50-row
        # production run is intentionally given one warm-up optimizer step.
        cfg.pop("warmup_ratio")
        cfg["warmup_steps"] = 1
    cfg = checked_config(SFTConfig, cfg)
    training_args = SFTConfig(**cfg)
    trainer_kwargs = {
        "model": model,
        "train_dataset": Dataset.from_list(train_encoded),
        "eval_dataset": Dataset.from_list(dev_encoded),
        "args": training_args,
        "data_collator": AssistantOnlyCollator(tokenizer),
    }
    if "processing_class" in inspect.signature(SFTTrainer).parameters:
        trainer_kwargs["processing_class"] = tokenizer
    else:
        trainer_kwargs["tokenizer"] = tokenizer
    if args.smoke_no_save:
        from transformers import TrainerCallback

        class OneStep(TrainerCallback):
            def on_step_begin(self, args, state, control, **kwargs):
                if state.global_step != 0 or state.max_steps != 1:
                    raise RuntimeError("STOP: unexpected optimizer step")
                return control

            def on_step_end(self, args, state, control, **kwargs):
                control.should_training_stop = True
                control.should_save = False
                control.should_evaluate = False
                return control

        trainer_kwargs["callbacks"] = [OneStep()]
    trainer = SFTTrainer(**trainer_kwargs)
    if list(trainer.train_dataset) != train_encoded or list(trainer.eval_dataset) != dev_encoded:
        raise SystemExit("STOP: trainer changed pretokenized examples")
    collator_report = check_collator_labels(trainer, args.max_seq_length)
    if args.smoke_no_save:
        batch = next(iter(trainer.get_train_dataloader()))
        expected = train_encoded[0]
        if (trainer.args.max_steps != 1 or trainer.args.gradient_accumulation_steps != 1
                or any(batch[key].tolist() != [expected[key]] for key in ("input_ids", "labels"))):
            raise SystemExit("STOP: smoke dataloader/config mismatch")
    result = trainer.train()
    if args.smoke_no_save and (trainer.state.global_step != 1 or not math.isfinite(result.training_loss)):
        raise SystemExit("STOP: invalid smoke result")
    dev_metrics = {} if args.smoke_no_save else trainer.evaluate()
    if args.smoke_no_save:
        from evaluate_v2 import evaluate, offline
        offline()
        FastLanguageModel.for_inference(trainer.model)
        trainer.model.eval()
        evaluate(trainer.model, tokenizer, dev_rows, args.output / "smoke_predictions.jsonl")
    adapter_dir = args.output / "adapter"
    if not args.smoke_no_save:
        trainer.model.save_pretrained(adapter_dir)
        tokenizer.save_pretrained(adapter_dir)

    library_versions = {}
    for name in ("torch", "transformers", "trl", "peft", "unsloth", "datasets", "bitsandbytes"):
        try:
            library_versions[name] = version(name)
        except PackageNotFoundError:
            library_versions[name] = "unknown"
    report = {
        "assistant_mask_preflight": mask_report,
        "collator_label_preflight": collator_report,
        "library_versions": library_versions,
        "resolved_model_revision": getattr(model.config, "_commit_hash", None),
        "resolved_tokenizer_revision": getattr(tokenizer, "init_kwargs", {}).get("_commit_hash"),
        "base_model": args.model,
        "train_examples": len(train_rows),
        "dev_examples": len(dev_rows),
        "dataset_manifest": manifest,
        "train_loss": result.training_loss,
        "dev_metrics": dev_metrics,
        "seed": args.seed,
        "hyperparameters": vars(args) | {"data_dir": str(args.data_dir), "output": str(args.output)},
        "cuda_device": torch.cuda.get_device_name(0),
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "optimizer_steps": trainer.state.global_step,
        "verified_local_revision": args.model_revision if snap else None,
        "adapter_saved": not args.smoke_no_save,
        "warning": "Demo-only smoke test. Not suitable for release." if args.smoke_no_save or not manifest.get("production_ready") else None,
    }
    (args.output / "training_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    if not args.smoke_no_save:
        print("Saved LoRA adapter to", adapter_dir)
    print("Training report:", args.output / "training_report.json")


if __name__ == "__main__":
    main()
