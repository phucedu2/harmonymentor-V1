"""Run with python -m unittest discover -s tests -v (no ML packages needed)."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "ai" / "hm_training"))
from prepare_dataset import prepare, read_jsonl, validate


class PrepareDatasetTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.demo = ROOT / "data" / "hm_training" / "examples.demo.jsonl"

    def test_demo_requires_explicit_flag(self):
        with self.assertRaisesRegex(ValueError, "human review"):
            validate(read_jsonl(self.demo), allow_demo=False)

    def test_demo_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out"
            manifest = prepare(self.demo, out, allow_demo=True)
            self.assertEqual(manifest["counts"], {"train": 4, "dev": 1, "test": 1})
            self.assertFalse(manifest["production_ready"])
            self.assertEqual(len(read_jsonl(out / "train.jsonl")), 4)
            self.assertTrue((out / "manifest.json").exists())

    def test_no_cross_split_group_leak(self):
        rows = read_jsonl(self.demo)
        rows[1]["group_id"] = rows[0]["group_id"]
        rows[1]["split"] = "test"
        with self.assertRaisesRegex(ValueError, "leaks"):
            validate(rows, allow_demo=True)

    def test_reject_fabricated_citation(self):
        rows = read_jsonl(self.demo)
        ans = json.loads(rows[0]["messages"][-1]["content"])
        ans["citations"][0]["block_id"] = "L99-FAKE"
        rows[0]["messages"][-1]["content"] = json.dumps(ans)
        with self.assertRaisesRegex(ValueError, "fabricated"):
            validate(rows, allow_demo=True)

    def test_reject_ai_self_verified(self):
        rows = read_jsonl(self.demo)
        ans = json.loads(rows[0]["messages"][-1]["content"])
        ans["engine_claims"][0]["verified"] = True
        rows[0]["messages"][-1]["content"] = json.dumps(ans)
        with self.assertRaisesRegex(ValueError, "self-declare"):
            validate(rows, allow_demo=True)


if __name__ == "__main__":
    unittest.main()
