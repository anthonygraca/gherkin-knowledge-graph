#!/usr/bin/env python3
"""Evaluate a CandidateDiscovery provider against the labeled fixture index (AI-05).

Labels live in ``fixtures/banking-demo/expected/candidate-links.json``. Metrics are measurements,
never expected values in rule tests. The fake provider path is offline.

    uv run --project backend python tools/evaluate_candidates.py \
        --out docs/reports/ai-05/evidence/candidate-benchmark.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.discovery.fake import FakeCandidateDiscovery  # noqa: E402
from app.domain.oracle import CandidateIndexFile  # noqa: E402

DATASET = ROOT / "fixtures" / "banking-demo" / "expected" / "candidate-links.json"


def dataset_snapshot(path: Path) -> tuple[dict, str]:
    """Read the dataset once; validation and the recorded hash use the same bytes."""
    payload = path.read_bytes()
    return json.loads(payload), "sha256:" + hashlib.sha256(payload).hexdigest()


def metrics(returned: list[tuple[str, str, str]], positives: set, negatives: set) -> dict:
    def recall(k):
        found = {row for row in returned[:k] if row in positives}
        return len(found) / len(positives) if positives else 0.0

    positive_hits = [index for index, row in enumerate(returned, 1) if row in positives]
    count = len(returned)
    return {
        "recall_at_1": round(recall(1), 4),
        "recall_at_5": round(recall(5), 4),
        "recall_at_10": round(recall(10), 4),
        "precision_at_5": round(
            len([row for row in returned[:5] if row in positives]) / min(5, count), 4
        )
        if count
        else 0.0,
        "mrr": round(1.0 / positive_hits[0], 4) if positive_hits else 0.0,
        "false_candidate_rate": round(len([row for row in returned if row in negatives]) / count, 4)
        if count
        else 0.0,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--dataset", type=Path, default=DATASET)
    args = parser.parse_args(argv)

    payload, dataset_hash = dataset_snapshot(args.dataset)
    index = CandidateIndexFile.model_validate(payload)
    provider = FakeCandidateDiscovery(index)
    labels: dict[str, dict[str, set]] = {}
    for candidate in index.candidates:
        bucket = labels.setdefault(candidate.source_id, {"positive": set(), "negative": set()})
        key = (candidate.source_id, candidate.target_id, candidate.proposed_relation_type.value)
        bucket[candidate.label].add(key)
    sources = []
    for artifact_id in sorted(labels):
        candidates = provider.discover(artifact_id, top_k=10)
        returned = [
            (candidate.source_id, candidate.target_id, candidate.proposed_relation_type.value)
            for candidate in candidates
        ]
        row = {
            "artifact_id": artifact_id,
            "returned": returned,
            "labels": {
                "positive": sorted(labels[artifact_id]["positive"]),
                "negative": sorted(labels[artifact_id]["negative"]),
            },
            **metrics(
                returned,
                labels[artifact_id]["positive"],
                labels[artifact_id]["negative"],
            ),
        }
        sources.append(row)
    keys = (
        "recall_at_1",
        "recall_at_5",
        "recall_at_10",
        "precision_at_5",
        "mrr",
        "false_candidate_rate",
    )
    report = {
        "schema_version": "1",
        "provider": provider.provider_name,
        "model_version": provider.model_version,
        "index_revision": provider.index_revision,
        "dataset": (
            str(args.dataset.relative_to(ROOT))
            if args.dataset.resolve().is_relative_to(ROOT)
            else str(args.dataset)
        ),
        "dataset_sha256": dataset_hash,
        "sources": sources,
        "aggregate": {
            key: round(sum(row[key] for row in sources) / len(sources), 4) for key in keys
        },
        "limitations": [
            "Five hand-labeled candidate pairs are a harness check, not a general retrieval claim.",
            "Scores are fixture labels, not model measurements.",
        ],
    }
    output = json.dumps(report, indent=2, sort_keys=True)
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output + "\n", encoding="utf-8")
    print(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
