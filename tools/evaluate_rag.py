#!/usr/bin/env python3
"""Evidence-grounded retrieval benchmark (AI-09 / PR 4).

Combines the AI-07 code-retrieval comparison (A lexical vs B CocoIndex) with an offline
authoritative-graph answer comparison (C) and a hybrid variant (D: graph answer + lexical semantic
candidates). A/B metrics come from a prior ``evaluate_code_retrieval.py`` capture so both methods
use identical labels/snapshots; C/D are evaluated here against hand-labeled answer cases.

    uv run --project backend python tools/evaluate_rag.py \
        --code-eval docs/reports/omp-cocoindex-pr2/evidence/live-eval-baseline-a.json \
        --out docs/reports/omp-cocoindex-pr4/evidence/rag-benchmark.json

It does not close M4 and does not claim a general retrieval improvement.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(ROOT / "backend"))

from app.discovery.code_index import CodeDiscovery  # noqa: E402
from app.domain.answers import AnswerRequest  # noqa: E402
from app.graphrag.context import AnswerService  # noqa: E402
from app.ingestion.repository import GitRepository  # noqa: E402
from app.persistence.ingested import IngestedStore  # noqa: E402
from app.settings import load_settings  # noqa: E402

ANSWERS = ROOT / "fixtures" / "banking-demo" / "expected" / "evidence-answers.json"
CODE_LABELS = ROOT / "fixtures" / "banking-demo" / "expected" / "code-retrieval.json"


def _sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _digest(value) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def answer_claims_match(case: dict, answer: str) -> bool:
    """Every expected claim is present and no forbidden claim appears."""
    lowered = answer.lower()
    return all(
        token.lower() in lowered for token in case.get("required_answer_tokens", [])
    ) and not any(token.lower() in lowered for token in case.get("forbidden_answer_tokens", []))


def evaluate_answers(store: IngestedStore, *, hybrid: bool, method: str) -> dict:
    labels = json.loads(ANSWERS.read_text(encoding="utf-8"))
    code_labels = json.loads(CODE_LABELS.read_text(encoding="utf-8"))
    relevant_by_case = {
        (case["baseline"], case["artifact_id"]): {item["artifact_id"] for item in case["relevant"]}
        for case in code_labels["cases"]
    }
    git = GitRepository(store.repository.root)
    code = (
        CodeDiscovery(
            repository=store,
            git=git,
            repository_name=labels["fixture"],
            model_version="deterministic-token-overlap-v1",
        )
        if hybrid
        else None
    )
    rows = []
    for case in labels["cases"]:
        started = time.perf_counter()
        response = AnswerService(store, code_discovery=code).answer(
            AnswerRequest(
                requirement_id=case["requirement_id"],
                baseline=case["baseline"],
                include_semantic_candidates=hybrid,
            )
        )
        latency_ms = (time.perf_counter() - started) * 1000.0
        accepted = sorted(link.link_id for link in response.accepted_links)
        proposed = sorted(link.link_id for link in response.proposed_links)
        evidence = sorted(row.evidence_id for row in response.evidence)
        findings = {finding.finding_type.value for finding in response.findings}
        actual_paths = [
            {
                "artifact_ids": path.artifact_ids,
                "link_ids": path.link_ids,
                "evidence_ids": path.evidence_ids,
                "review_state": path.review_state,
            }
            for path in response.graph_paths
        ]
        expected_paths = [{**path, "review_state": "accepted"} for path in case.get("paths", [])]
        allowed_artifacts = {artifact.artifact_id for artifact in response.artifacts}
        allowed_artifacts.add(case["requirement_id"])
        allowed_artifacts.update(hit.artifact_id for hit in response.semantic_candidates)
        allowed_artifacts.update(
            artifact_id for finding in response.findings for artifact_id in finding.artifact_ids
        )
        allowed_artifacts.update(
            endpoint
            for link in (*response.accepted_links, *response.proposed_links)
            for endpoint in (link.source_id, link.target_id)
        )
        citation_ok = (
            set(response.references.artifact_ids) <= allowed_artifacts
            and set(response.references.link_ids) <= set(accepted) | set(proposed)
            and set(response.references.evidence_ids)
            <= {row.evidence_id for row in response.evidence}
            and set(response.references.finding_ids)
            <= {finding.finding_id for finding in response.findings}
        )
        revisions_ok = all(
            artifact.revision == response.revision for artifact in response.artifacts
        )
        claims_ok = answer_claims_match(case, response.answer)
        candidates = response.semantic_candidates
        scenarios = {
            artifact_id
            for path in response.graph_paths
            for artifact_id in path.artifact_ids
            if artifact_id.startswith("SCN")
        }
        relevant_candidates: set[str] = set()
        for scenario in scenarios:
            relevant_candidates.update(relevant_by_case.get((case["baseline"], scenario), set()))
        if hybrid and candidates:
            semantic_false = len(
                [hit for hit in candidates if hit.artifact_id not in relevant_candidates]
            )
            semantic_false_rate = round(semantic_false / len(candidates), 4)
        else:
            semantic_false_rate = 0.0
        row = {
            "case": case["id"],
            "status": response.status.value,
            "status_ok": response.status.value == case["status"],
            "accepted_links_ok": accepted == sorted(case["accepted_links"]),
            "proposed_links_ok": proposed == sorted(case["proposed_links"]),
            "evidence_ok": evidence == sorted(case["evidence"]),
            "findings_ok": findings == set(case["findings"]),
            "forbidden_findings_ok": not (set(case["forbidden_findings"]) & findings),
            "paths_ok": actual_paths == expected_paths,
            "citation_ok": citation_ok,
            "revisions_ok": revisions_ok,
            "claims_ok": claims_ok,
            "semantic_candidates": len(candidates),
            "semantic_false_candidate_rate": semantic_false_rate,
            "revision": response.revision,
            "artifact_digest": _digest([a.model_dump(mode="json") for a in response.artifacts]),
            "link_digest": _digest(
                [
                    link.model_dump(mode="json")
                    for link in (*response.accepted_links, *response.proposed_links)
                ]
            ),
            "evidence_digest": _digest([e.model_dump(mode="json") for e in response.evidence]),
            "finding_digest": _digest([f.model_dump(mode="json") for f in response.findings]),
            "latency_ms": round(latency_ms, 3),
        }
        rows.append(row)
    keys = [
        "status_ok",
        "accepted_links_ok",
        "proposed_links_ok",
        "evidence_ok",
        "findings_ok",
        "forbidden_findings_ok",
        "paths_ok",
        "citation_ok",
        "revisions_ok",
        "claims_ok",
    ]
    count = len(rows)
    return {
        "method": method,
        "cases": rows,
        "aggregate": {key: round(sum(1 for row in rows if row[key]) / count, 4) for key in keys},
        "mean_latency_ms": round(sum(row["latency_ms"] for row in rows) / count, 3),
        "stored_proposal_mismatch_rate": 0.0
        if all(row["proposed_links_ok"] for row in rows)
        else 1.0,
        "unsupported_claim_rate": round(
            1.0 - sum(1 for row in rows if row["claims_ok"]) / count, 4
        ),
        "forbidden_finding_violation_rate": round(
            1.0 - sum(1 for row in rows if row["forbidden_findings_ok"]) / count, 4
        ),
        "semantic_false_candidate_rate": round(
            sum(row["semantic_false_candidate_rate"] for row in rows) / count, 4
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--code-eval", type=Path, default=None)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    settings = load_settings()
    store = IngestedStore.from_settings(settings)
    code_eval = None
    if args.code_eval is not None:
        code_eval = json.loads(args.code_eval.read_text(encoding="utf-8"))

    report = {
        "schema_version": "1",
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "fixture": settings.fixture,
        "inputs": {
            "code_labels": {
                "path": str(CODE_LABELS.relative_to(ROOT)),
                "sha256": _sha(CODE_LABELS),
            },
            "answer_labels": {"path": str(ANSWERS.relative_to(ROOT)), "sha256": _sha(ANSWERS)},
            "code_eval": None
            if args.code_eval is None
            else {"path": str(args.code_eval), "sha256": _sha(args.code_eval)},
        },
        "A_B_code_retrieval": None
        if code_eval is None
        else {
            "lexical": code_eval.get("lexical"),
            "cocoindex_live": code_eval.get("cocoindex_live"),
        },
        "baselines": store.baseline_commits(),
        "implementation_hashes": {
            "app/domain/answers.py": _sha(ROOT / "backend/app/domain/answers.py"),
            "app/graphrag/context.py": _sha(ROOT / "backend/app/graphrag/context.py"),
            "tools/evaluate_rag.py": _sha(ROOT / "tools/evaluate_rag.py"),
        },
        "C_graph_answers": evaluate_answers(store, hybrid=False, method="accepted_graph"),
        "D_hybrid_answers": evaluate_answers(
            store, hybrid=True, method="graph_plus_lexical_candidates"
        ),
        "limitations": [
            "C and D receive accepted-graph information that A/B do not; compare them separately.",
            "Answer labels are hand-derived from the M1/M2 fixture oracle.",
            "This benchmark does not close M4 and makes no general retrieval-quality claim.",
        ],
    }
    payload = json.dumps(report, indent=2, sort_keys=True)
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
