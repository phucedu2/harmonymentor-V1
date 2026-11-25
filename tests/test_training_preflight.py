"""CPU-only tests; never load a model, import torch, or access application DB."""
import json
import sys
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts/ai/hm_training"))
sys.path.insert(0, str(ROOT / "backend"))
from training_safety import checked_config, check_mask, preflight_tokenizer, check_collator_labels
from prepare_dataset import read_jsonl, validate, verify_engine
from app.ai.tutor.prompt import SYSTEM

DRAFT = ROOT / "data/hm_training/examples.context.draft.jsonl"


def modern(assistant_only_loss=True, packing=False, max_length=1024): pass

def legacy(packing=False, max_seq_length=1024): pass

def test_config_retains_critical_settings():
    cfg = {"assistant_only_loss": True, "packing": False, "max_length": 1024}
    assert checked_config(modern, cfg) == cfg


def test_missing_assistant_flag_stops():
    with pytest.raises(ValueError, match="assistant_only_loss"):
        checked_config(legacy, {"assistant_only_loss": True, "packing": False, "max_length": 1024})


def test_supported_length_alias():
    def version(assistant_only_loss=True, packing=False, max_seq_length=1024): pass
    assert checked_config(version, {"assistant_only_loss": True, "packing": False, "max_length": 1024})["max_seq_length"] == 1024


@pytest.mark.parametrize("cfg", [{"assistant_only_loss": False, "packing": False}, {"assistant_only_loss": True, "packing": True}])
def test_bad_loss_policy(cfg):
    with pytest.raises(ValueError): checked_config(modern, cfg)


def test_unknown_setting_never_silently_dropped():
    with pytest.raises(ValueError, match="mystery"):
        checked_config(modern, {"assistant_only_loss": True, "packing": False, "mystery": 1})


@pytest.mark.parametrize("ids,mask,limit", [([], [], 10), ([1,2], [], 10), ([1,2], [0,0], 10), ([1,2], [1,1], 10), ([1,2], [0,2], 10), ([1,2,3], [0,1,1], 2)])
def test_mask_invalid_or_truncated_stops(ids, mask, limit):
    with pytest.raises(ValueError): check_mask(ids, mask, limit, "row")


class Tokenizer:
    def __init__(self, mask=None): self.mask = mask if mask is not None else [0,0,1,1]
    def apply_chat_template(self, messages, **kwargs):
        if kwargs.get("add_generation_prompt"): return [10,11]
        assert kwargs["truncation"] is False
        return {"input_ids": [10,11,12,13], "assistant_masks": self.mask}


def test_tokenizer_preflight_records_counts():
    out = preflight_tokenizer(Tokenizer(), [{"messages": [{}, {}, {}]}], 4, "train")
    assert out == [{"tokens": 4, "assistant_tokens": 2}]


def test_tokenizer_rejects_prompt_leakage():
    with pytest.raises(ValueError, match="prefix"):
        preflight_tokenizer(Tokenizer([0,1,1,1]), [{"messages": [{}, {}, {}]}], 4, "train")


class Vector(list):
    def tolist(self): return list(self)


def trainer(labels):
    row = {"input_ids": [10,11,12,13], "assistant_masks": [0,0,1,1]}
    def collator(rows):
        return {"input_ids": [Vector([10,11,12,13])], "labels": [Vector(labels)], "attention_mask": [Vector([1,1,1,1])]}
    return SimpleNamespace(train_dataset=[row], eval_dataset=[row], data_collator=collator)


def test_collator_labels_match_mask():
    assert check_collator_labels(trainer([-100,-100,12,13]), 4) == {"train": 1, "dev": 1}


@pytest.mark.parametrize("labels", [[10,11,12,13], [-100,-100,-100,-100], [-100,-100,99,13]])
def test_collator_rejects_prompt_loss_empty_loss_wrong_targets(labels):
    with pytest.raises(ValueError, match="labels differ"):
        check_collator_labels(trainer(labels), 4)


def test_draft_schema_engine_and_prompt_current():
    rows = read_jsonl(DRAFT)
    summary = validate(rows, allow_demo=True)
    assert summary["counts"] == {"train": 12, "dev": 2, "test": 2}
    assert summary["demo_or_unapproved"] == 16
    assert all(r["messages"][0]["content"] == SYSTEM for r in rows)
    assert all('<<<HM_DATA kind="ENGINE_FACTS">>>' in r["messages"][1]["content"] for r in rows)
    verify_engine(rows)


def mutate_answer(edit):
    rows = read_jsonl(DRAFT)[:1]
    answer = json.loads(rows[0]["messages"][-1]["content"])
    edit(answer)
    rows[0]["messages"][-1]["content"] = json.dumps(answer)
    return rows


@pytest.mark.parametrize("edit", [lambda a: a.update(reply="x" * 4001), lambda a: a.update(suggested_actions=["x"]*6)])
def test_runtime_limits_enforced(edit):
    with pytest.raises(ValueError, match="runtime TutorAnswer"):
        validate(mutate_answer(edit), allow_demo=True)


def test_scanned_contradiction_despite_correct_declared():
    rows = mutate_answer(lambda a: a.update(reply="Trong giọng C trưởng, Am là ii."))
    with pytest.raises(ValueError, match="contradicted"):
        verify_engine(rows)


def test_scanned_claim_must_be_declared():
    rows = mutate_answer(lambda a: a.update(engine_claims=[]))
    with pytest.raises(ValueError, match="missing from"):
        verify_engine(rows)


def test_draft_not_approved():
    with pytest.raises(ValueError, match="human review"):
        validate(read_jsonl(DRAFT), allow_demo=False)


def test_draft_groups_do_not_leak():
    rows = read_jsonl(DRAFT)
    rows[1]["group_id"] = rows[0]["group_id"]
    rows[1]["split"] = "test"
    with pytest.raises(ValueError, match="leaks"):
        validate(rows, allow_demo=True)


def test_hint_levels_do_not_emit_answer_claims():
    rows = read_jsonl(DRAFT)
    answers = [json.loads(r["messages"][-1]["content"]) for r in rows]
    hints = [a for a in answers if a["hint_level"] in (1,2)]
    assert len(hints) == 2
    assert all(not a["engine_claims"] and "vi7" not in a["reply"] for a in hints)


class OffsetTokenizer:
    def apply_chat_template(self, messages, **kwargs):
        return "P:" + messages[-1]["content"] + "!"

    def __call__(self, text, **kwargs):
        assert kwargs == {"add_special_tokens": False, "return_offsets_mapping": True}
        return {"input_ids": list(map(ord, text)), "offset_mapping": [(i, i+1) for i in range(len(text))]}

    def decode(self, ids, **kwargs):
        return "".join(map(chr, ids))


def test_offset_labels_decode_exactly_and_ignore_prompt_suffix():
    from training_safety import encode_assistant_only
    row = {"messages": [{"role": "system"}, {"role": "user"}, {"role": "assistant", "content": "đúng"}]}
    item = encode_assistant_only(OffsetTokenizer(), row, 10, "row")
    assert item["labels"] == [-100, -100, *map(ord, "đúng"), -100]
    assert item["assistant_masks"] == [0, 0, 1, 1, 1, 1, 0]
    with pytest.raises(ValueError, match="refusing truncation"):
        encode_assistant_only(OffsetTokenizer(), row, 6, "row")


def test_offset_rejects_boundary_crossing():
    from training_safety import encode_assistant_only

    class Straddles(OffsetTokenizer):
        def __call__(self, text, **kwargs):
            result = super().__call__(text, **kwargs)
            result["offset_mapping"][1] = (1, 3)
            return result

    row = {"messages": [{"role": "system"}, {"role": "user"}, {"role": "assistant", "content": "OK"}]}
    with pytest.raises(ValueError, match="straddles assistant boundary"):
        encode_assistant_only(Straddles(), row, 10, "row")
