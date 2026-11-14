"""AI-05: independent metric vectors for candidate evaluation."""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location(
    "evaluate_candidates", ROOT / "tools" / "evaluate_candidates.py"
)
module = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(module)


def test_metric_vector_is_computed_independently() -> None:
    returned = [
        ("SCN-001", "CODE-001", "implemented_by"),
        ("SCN-001", "TEST-001", "exercised_by"),
    ]
    positives = set(returned)
    negatives = set()
    result = module.metrics(returned, positives, negatives)
    assert result == {
        "recall_at_1": 0.5,
        "recall_at_5": 1.0,
        "recall_at_10": 1.0,
        "precision_at_5": 1.0,
        "mrr": 1.0,
        "false_candidate_rate": 0.0,
    }


def test_negative_candidate_is_counted_false() -> None:
    positive = ("SCN-002", "CODE-002", "implemented_by")
    negative = ("SCN-002", "CODE-001", "implemented_by")
    result = module.metrics([negative, positive], {positive}, {negative})
    assert result["false_candidate_rate"] == 0.5
    assert result["recall_at_1"] == 0.0
    assert result["mrr"] == 0.5


def test_dataset_is_read_once_for_validation_and_hash(tmp_path, monkeypatch) -> None:
    import json

    path = tmp_path / "labels.json"
    first = json.dumps(
        {
            "provider": "fake",
            "model_version": "v1",
            "schema_version": "1",
            "fixture": "x",
            "candidates": [],
        }
    ).encode()
    second = json.dumps(
        {
            "provider": "fake",
            "model_version": "v2",
            "schema_version": "1",
            "fixture": "x",
            "candidates": [],
        }
    ).encode()
    path.write_bytes(first)
    calls = {"count": 0}

    def fake_read(self):
        calls["count"] += 1
        return first if calls["count"] == 1 else second

    monkeypatch.setattr(Path, "read_bytes", fake_read)
    payload, digest = module.dataset_snapshot(path)
    assert calls["count"] == 1
    assert payload["model_version"] == "v1"
    assert digest.endswith(__import__("hashlib").sha256(first).hexdigest())
