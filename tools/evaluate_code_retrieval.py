#!/usr/bin/env python3
"""Evaluate artifact-aware code retrieval against hand-labeled banking cases (AI-07).

The labels live in ``fixtures/banking-demo/expected/code-retrieval.json`` and were hand-checked
from the accepted links and scenario titles. They are never derived from the retriever.

    uv run --project backend python tools/evaluate_code_retrieval.py --out /tmp/ai07-eval.json

Lexical evaluation is offline. ``--cocoindex-fixture`` evaluates the captured CocoIndex response
for the one case it covers. ``--live`` uses the configured CocoIndex project (explicit opt-in).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from app.discovery.cocoindex import (  # noqa: E402
    CocoIndexSearchClient,
    FakeCocoIndexTransport,
)
from app.discovery.code_index import CodeDiscovery, configured_model_version, live_client  # noqa: E402
from app.domain.retrieval import CodeRetrievalRequest, RetrievalMethod  # noqa: E402
from app.ingestion.repository import GitRepository  # noqa: E402
from app.persistence.ingested import IngestedStore  # noqa: E402
from app.settings import load_settings  # noqa: E402

LABELS = ROOT / "fixtures" / "banking-demo" / "expected" / "code-retrieval.json"
CAPTURE = ROOT / "backend" / "tests" / "fixtures" / "cocoindex-search-response.json"


def metrics(ranked: list[str], relevant: set[str]) -> dict[str, float]:
    def recall(k: int) -> float:
        return len(set(ranked[:k]) & relevant) / len(relevant) if relevant else 0.0

    first = next((index for index, item in enumerate(ranked, start=1) if item in relevant), None)
    returned = len(ranked)
    false = len([item for item in ranked if item not in relevant])
    return {
        "recall_at_1": recall(1),
        "recall_at_5": recall(5),
        "precision_at_5": (len(set(ranked[:5]) & relevant) / min(5, returned)) if returned else 0.0,
        "mrr": (1.0 / first) if first else 0.0,
        "false_candidate_rate": (false / returned) if returned else 0.0,
    }


def evaluate(discovery: CodeDiscovery, cases: list[dict], method: RetrievalMethod) -> dict:
    results = []
    for case in cases:
        response = discovery.retrieve(
            CodeRetrievalRequest(
                artifact_id=case["artifact_id"],
                baseline=case["baseline"],
                top_k=5,
                method=method,
            )
        )
        ranked = [hit.artifact_id for hit in response.hits]
        relevant = {item["artifact_id"] for item in case["relevant"]}
        row = {
            "case": case["id"],
            "baseline": case["baseline"],
            "artifact_id": case["artifact_id"],
            "status": response.status.value,
            "ranked": ranked,
            "relevant": sorted(relevant),
            "unresolved": [item.path for item in response.unresolved],
            "latency_ms": round(response.latency_ms, 3),
            "index_binding": response.index_binding,
            **metrics(ranked, relevant),
        }
        results.append(row)
    count = len(results) or 1
    return {
        "method": method.value,
        "model_version": discovery.model_version,
        "cases": results,
        "aggregate": {
            key: round(sum(row[key] for row in results) / count, 4)
            for key in (
                "recall_at_1",
                "recall_at_5",
                "precision_at_5",
                "mrr",
                "false_candidate_rate",
            )
        },
        "mean_latency_ms": round(sum(row["latency_ms"] for row in results) / count, 3),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--cocoindex-fixture", action="store_true")
    parser.add_argument("--live", action="store_true")
    parser.add_argument(
        "--baseline", default=None, help="Restrict evaluation to one baseline (e.g. baseline-a)"
    )
    args = parser.parse_args(argv)

    settings = load_settings()
    store = IngestedStore.from_settings(settings)
    git = GitRepository(settings.fixture_repo)
    labels = json.loads(LABELS.read_text(encoding="utf-8"))
    cases = [case for case in labels["cases"] if args.baseline in (None, case["baseline"])]

    report: dict[str, object] = {
        "fixture": labels["fixture"],
        "labels": str(LABELS.relative_to(ROOT)),
        "cases": len(cases),
        "lexical": evaluate(
            CodeDiscovery(
                repository=store,
                git=git,
                repository_name=settings.fixture,
                model_version="deterministic-token-overlap-v1",
            ),
            cases,
            RetrievalMethod.LEXICAL,
        ),
    }
    if args.cocoindex_fixture:
        discovery = CodeDiscovery(
            repository=store,
            git=git,
            repository_name=settings.fixture,
            client=CocoIndexSearchClient(
                FakeCocoIndexTransport.from_fixture(CAPTURE, project_root=Path("/snapshot"))
            ),
            model_version="cocoindex-code 0.2.43 (captured fixture)",
        )
        report["cocoindex_fixture"] = evaluate(discovery, cases, RetrievalMethod.COCOINDEX)
    if args.live:
        discovery = CodeDiscovery(
            repository=store,
            git=git,
            repository_name=settings.fixture,
            client=live_client(settings),
            model_version=configured_model_version(settings),
            require_live_root=True,
        )
        report["cocoindex_live"] = evaluate(discovery, cases, RetrievalMethod.COCOINDEX)
    payload = json.dumps(report, indent=2, sort_keys=True)
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
