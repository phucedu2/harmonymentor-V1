"""Fail-closed training checks; imports no GPU packages or application services."""
from __future__ import annotations
import inspect


def checked_config(config_class, cfg):
    params = inspect.signature(config_class).parameters
    result = dict(cfg)
    if "max_length" not in params and "max_seq_length" in params:
        result["max_seq_length"] = result.pop("max_length")
    pretokenized = result.pop("pretokenized_assistant_only", False)
    missing = sorted(set(result) - set(params))
    if missing:
        raise ValueError("STOP: SFTConfig cannot honor settings: " + ", ".join(missing))
    if pretokenized:
        if result.get("assistant_only_loss") is not False:
            raise ValueError("STOP: pretokenized mode must disable trainer remasking")
    elif result.get("assistant_only_loss") is not True:
        raise ValueError("STOP: assistant-only loss is required")
    if result.get("packing") is not False:
        raise ValueError("STOP: unpacked examples are required")
    return result


def check_mask(ids, mask, max_length, label):
    if not ids or len(ids) != len(mask) or any(x not in (0, 1) for x in mask):
        raise ValueError(f"STOP: {label}: missing or invalid assistant mask")
    if not any(mask) or all(mask):
        raise ValueError(f"STOP: {label}: mask must cover assistant only, not zero/all tokens")
    if len(ids) > max_length:
        raise ValueError(f"STOP: {label}: {len(ids)} tokens exceed {max_length}; refusing truncation")


def preflight_tokenizer(tokenizer, rows, max_length, split):
    counts = []
    for index, row in enumerate(rows):
        encoded = tokenizer.apply_chat_template(
            row["messages"], tokenize=True, add_generation_prompt=False,
            return_dict=True, return_assistant_tokens_mask=True, truncation=False,
        )
        ids, mask = encoded.get("input_ids", []), encoded.get("assistant_masks", [])
        check_mask(ids, mask, max_length, f"{split}[{index}]")
        prefix = tokenizer.apply_chat_template(row["messages"][:-1], tokenize=True,
                                               add_generation_prompt=True)
        if ids[:len(prefix)] != prefix or any(mask[:len(prefix)]):
            raise ValueError(f"STOP: {split}[{index}]: assistant mask/prompt prefix mismatch")
        counts.append({"tokens": len(ids), "assistant_tokens": sum(mask)})
    return counts


def check_collator_labels(trainer, max_length):
    counts = {}
    for split, dataset in (("train", trainer.train_dataset), ("dev", trainer.eval_dataset)):
        if dataset is None or len(dataset) == 0:
            raise ValueError(f"STOP: empty prepared {split} dataset")
        for index, row in enumerate(dataset):
            ids, mask = row.get("input_ids", []), row.get("assistant_masks", [])
            check_mask(ids, mask, max_length, f"prepared {split}[{index}]")
            batch = trainer.data_collator([row])
            labels = batch["labels"][0].tolist()
            input_ids = batch["input_ids"][0].tolist()
            attention = batch.get("attention_mask")
            attention = attention[0].tolist() if attention is not None else [1] * len(labels)
            active = [(token, target) for token, target, attend in zip(input_ids, labels, attention) if attend]
            if len(active) != len(ids) or [t for t, _ in active] != list(ids):
                raise ValueError(f"STOP: collator changed token alignment for {split}[{index}]")
            expected = [token if keep else -100 for token, keep in zip(ids, mask)]
            if [target for _, target in active] != expected:
                raise ValueError(f"STOP: collator loss labels differ from assistant mask for {split}[{index}]")
            if any(target != -100 for target, attend in zip(labels, attention) if not attend):
                raise ValueError("STOP: padding must not contribute to loss")
        counts[split] = len(dataset)
    return counts


class AssistantOnlyCollator:
    """Pad pre-tokenized examples whose labels already mask the prompt."""
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer

    def __call__(self, features):
        import torch
        ids = [f["input_ids"] for f in features]
        labels = [f["labels"] for f in features]
        batch = self.tokenizer.pad({"input_ids": ids}, padding=True, return_tensors="pt")
        max_len = batch["input_ids"].shape[1]
        if self.tokenizer.padding_side == "left":
            padded = [[-100] * (max_len - len(x)) + x for x in labels]
        else:
            padded = [x + [-100] * (max_len - len(x)) for x in labels]
        batch["labels"] = torch.tensor(padded, dtype=torch.long)
        return batch


def encode_assistant_only(tokenizer, row, max_length, label):
    """Render the canonical train/inference template and supervise JSON + EOS only."""
    import sys
    from pathlib import Path
    backend = Path(__file__).resolve().parents[3] / "backend"
    if str(backend) not in sys.path:
        sys.path.insert(0, str(backend))
    from app.ai.tutor.local_qlora import encode
    return encode(tokenizer, row, max_length, label)


def preflight_assistant_only(tokenizer, rows, max_length, split):
    report = []
    for index, row in enumerate(rows):
        item = encode_assistant_only(tokenizer, row, max_length, f"{split}[{index}]")
        report.append({"tokens": len(item["input_ids"]), "assistant_tokens": sum(x != -100 for x in item["labels"])})
    return report
