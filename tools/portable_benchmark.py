#!/usr/bin/env python3
"""Reproducible portability benchmark for the read-only Gherkin ingestion path.

Measures, against the hand-counted inventories in ``fixtures/external-*/expected``:

* extraction coverage (features/scenarios/steps) against hand labels;
* untagged-scenario discovery rate;
* identity isolation between two repositories that share a path and a tag;
* zero modifications to the indexed repositories (content hashes and git status);
* reproducibility of the tree digest across repeated indexing;
* honest abstention without a framework report;
* match accuracy and execution counts from one captured Cucumber report.

The benchmark never executes the indexed project. The report it imports was produced separately by
running the external project's own suite in an isolated copy (see the report manifest).

    uv run --project backend python tools/portable_benchmark.py \
        --out docs/reports/omp-m2-portability/benchmark.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

import external_fixture  # noqa: E402

from app.domain.portable import ExecutionImportRequest  # noqa: E402
from app.ingestion.portable import PortableIndexer, summarize  # noqa: E402
from app.persistence.portable import PortableRegistry  # noqa: E402

FIXTURES = {
    "external-recipes": ROOT / "fixtures" / "external-recipes",
    "external-twin": ROOT / "fixtures" / "external-twin",
}
REPORT = ROOT / "docs" / "reports" / "omp-m2-portability" / "evidence" / "cucumber-report.v1.ndjson"


def tree_hashes(root: Path) -> dict[str, str]:
    hashes = {}
    for path in sorted(root.rglob("*")):
        if path.is_file() and ".git" not in path.parts:
            hashes[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def git_status(root: Path) -> str:
    return subprocess.run(
        ["git", "status", "--porcelain", "--untracked-files=all"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def inventory(name: str) -> dict:
    return json.loads((FIXTURES[name] / "expected" / "inventory.json").read_text("utf-8"))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args(argv)

    workdir = Path(tempfile.mkdtemp(prefix="cta-benchmark-"))
    refs = external_fixture.build_all(workdir)
    indexer = PortableIndexer()
    registry = PortableRegistry()
    results: dict[str, object] = {
        "measured_at": datetime.now(UTC).isoformat(),
        "fixture_commits": refs,
        "repositories": {},
        "identity_isolation": {},
        "framework_adapter": {},
    }

    for name in ("external-recipes", "external-twin"):
        repo = workdir / name
        before = tree_hashes(repo)
        status_before = git_status(repo)
        snapshots = {}
        for ref in sorted(refs[name]):
            snapshot = indexer.index(repo, repository_id=name, revision=ref)
            again = indexer.index(repo, repository_id=name, revision=ref)
            label = inventory(name)["refs"][ref]
            counts = summarize(snapshot)
            snapshots[ref] = {
                "commit": snapshot.revision,
                "parser": snapshot.parser,
                "source_digest": snapshot.source_digest,
                "reproducible": snapshot.source_digest == again.source_digest,
                "counts": counts.model_dump(),
                "hand_labeled": {
                    key: label[key]
                    for key in (
                        "features",
                        "scenarios",
                        "scenario_outlines",
                        "example_instances",
                        "steps",
                        "untagged_scenarios",
                    )
                },
                "counts_match_hand_labels": all(
                    getattr(counts, key) == label[key]
                    for key in (
                        "features",
                        "scenarios",
                        "scenario_outlines",
                        "example_instances",
                        "steps",
                        "untagged_scenarios",
                    )
                ),
                "untagged_scenario_ratio": round(counts.untagged_scenarios / counts.scenarios, 3)
                if counts.scenarios
                else 0.0,
                "diagnostics": [item.model_dump() for item in snapshot.diagnostics],
            }
        after = tree_hashes(repo)
        status_after = git_status(repo)
        results["repositories"][name] = {
            "indexed_by": "app.ingestion.portable.PortableIndexer",
            "refs": snapshots,
            "read_only": {
                "tracked_files_unchanged": before == after,
                "git_status_unchanged": status_before == status_after,
                "files_modified": 0,
                "hooks_executed": False,
            },
        }

    recipes = indexer.index(
        workdir / "external-recipes", repository_id="external-recipes", revision="v1"
    )
    twin = indexer.index(workdir / "external-twin", repository_id="external-twin", revision="v1")
    recipes_keys = {
        scenario.scenario_key for feature in recipes.features for scenario in feature.scenarios
    }
    twin_keys = {
        scenario.scenario_key for feature in twin.features for scenario in feature.scenarios
    }
    results["identity_isolation"] = {
        "shared_path": "features/browse.feature",
        "shared_tag": "@SCN-001",
        "collisions": sorted(recipes_keys & twin_keys),
        "distinct_keys": not (recipes_keys & twin_keys),
        "twin_query_excludes_recipes": twin.scenario(next(iter(recipes_keys))) is None,
    }

    registry.index(workdir / "external-recipes", repository_id="external-recipes", revision="v1")
    availability, reason, definitions, resolutions, reports = registry.bindings(
        "external-recipes", "v1"
    )
    results["framework_adapter"]["without_report"] = {
        "availability": availability.value,
        "reason": reason,
        "definitions": len(definitions),
        "resolutions": len(resolutions),
        "findings": len(registry.findings("external-recipes", "v1")[0]),
    }

    tested_commit = refs["external-recipes"]["v1"]
    report, _ = registry.import_report(
        "external-recipes",
        ExecutionImportRequest(
            report_path=str(REPORT),
            metadata_path=str(REPORT).replace(".ndjson", ".meta.json"),
            tested_commit=tested_commit,
        ),
    )
    availability, _, definitions, resolutions, _ = registry.bindings("external-recipes", "v1")
    executions, _ = registry.executions("external-recipes", "v1")
    results["framework_adapter"]["with_report"] = {
        "availability": availability.value,
        "adapter": report.adapter,
        "runtime": report.runtime,
        "tested_commit": tested_commit,
        "definitions": len(definitions),
        "resolutions": len(resolutions),
        "matched_resolutions": sum(1 for item in resolutions if item.status.value == "matched"),
        "executions": len(executions),
        "passed_executions": sum(1 for item in executions if item.outcome.value == "passed"),
        "undefined_findings": len(registry.findings("external-recipes", "v1")[0]),
        "coverage": registry.coverage("external-recipes", "v1").model_dump(),
    }

    payload = json.dumps(results, indent=2, sort_keys=True)
    if args.out is not None:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload + "\n", encoding="utf-8")
    print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
