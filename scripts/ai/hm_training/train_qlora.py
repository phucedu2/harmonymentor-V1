"""Supervised QLoRA of Qwen3-4B-Instruct-2507 for HarmonyMentor TutorAnswer JSON.

Run on a CUDA GPU only after prepare_dataset.py. Does NOT train from scratch.
Only the LoRA adapter is saved; the model is downloaded from Hugging Face.
"""
from __future__ import annotations

import argparse
import hashlib
import inspect
import json
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_MODEL = "unsloth/Qwen3-4B-Instruct-2507-unsloth-bnb-4bit"


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_split(data_dir: Path, split: str) -> list[dict]:
    path = data_dir / (split + ".jsonl")
    return [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines() if s.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--epochs", type=float, default=2.0)
    parser.add_argument("--max-seq-length", type=int, default=1024)
    parser.add_argument("--max-steps", type=int, default=-1)
    parser.add_argument("--learning-rate", type=float, default=1e-4)
    parser.add_argument("--seed", type=int, default=20261116)
    parser.add_argument("--allow-demo", action="store_true", help="one-off GPU training smoke test only")
    args = parser.parse_args()

    manifest_path = args.data_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for split, digest in manifest["outputs_sha256"].items():
        if file_hash(args.data_dir / (split + ".jsonl")) != digest:
            raise SystemExit(f"STOP: {split}.jsonl changed after dataset validation")
    if not manifest.get("production_ready") and not args.allow_demo:
        raise SystemExit("STOP: dataset unapproved or too small (min 50 reviewed examples). Demo: --allow-demo")
    train_rows = read_split(args.data_dir, "train")
    dev_rows = read_split(args.data_dir, "dev")
    if not train_rows or not dev_rows:
        raise SystemExit("Both train and dev must be non-empty")

    try:
        import torch
        from datasets import Dataset
        from unsloth import FastLanguageModel, is_bfloat16_supported
        from trl import SFTConfig, SFTTrainer
    except ImportError as exc:
        raise SystemExit("Install GPU packages via Unsloth official instructions first") from exc
    if not torch.cuda.is_available():
        raise SystemExit("CUDA GPU unavailable. Use Colab/Kaggle/NVIDIA GPU; CPU RAG still works without GPU")

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=args.model, max_seq_length=args.max_seq_length, dtype=None,
        load_in_4bit=True,
    )
    model = FastLanguageModel.get_peft_model(
        model, r=16,
        target_modules=["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"],
        lora_alpha=16, lora_dropout=0, bias="none",
        use_gradient_checkpointing="unsloth", random_state=args.seed,
    )
    args.output.mkdir(parents=True, exist_ok=True)
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
        "assistant_only_loss": True,
        "packing": False,
        "max_length": args.max_seq_length,
    }
    if args.max_steps > 0:
        cfg["max_steps"] = args.max_steps
    signature = inspect.signature(SFTConfig).parameters
    if "max_length" not in signature and "max_seq_length" in signature:
        cfg["max_seq_length"] = cfg.pop("max_length")
    cfg = {k: v for k, v in cfg.items() if k in signature}
    training_args = SFTConfig(**cfg)
    trainer_kwargs = {
        "model": model,
        "train_dataset": Dataset.from_list(train_rows),
        "eval_dataset": Dataset.from_list(dev_rows),
        "args": training_args,
    }
    if "processing_class" in inspect.signature(SFTTrainer).parameters:
        trainer_kwargs["processing_class"] = tokenizer
    else:
        trainer_kwargs["tokenizer"] = tokenizer
    trainer = SFTTrainer(**trainer_kwargs)
    result = trainer.train()
    dev_metrics = trainer.evaluate()
    adapter_dir = args.output / "adapter"
    trainer.model.save_pretrained(adapter_dir)
    tokenizer.save_pretrained(adapter_dir)

    report = {
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
        "warning": "Demo-only adapter. Not suitable for release." if not manifest.get("production_ready") else None,
    }
    (args.output / "training_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )
    print("Saved LoRA adapter to", adapter_dir)
    print("Training report:", args.output / "training_report.json")


if __name__ == "__main__":
    main()
