#!/usr/bin/env python3
"""Generate the repository-wide feature inventory artifact.

Counts and step patterns are parsed from the tracked feature files; classification, execution
status, and exclusion reasons are declared here by hand. The two kinds of information are kept in
separate fields so a reader can tell a parsed count from a review decision.

    uv run --project backend python tools/feature_inventory.py

Writes ``docs/feature-inventory.json`` and ``docs/feature-inventory.md``.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from gherkin.parser import Parser
from gherkin.token_scanner import TokenScanner

ROOT = Path(__file__).resolve().parents[1]
OUT_JSON = ROOT / "docs" / "feature-inventory.json"
OUT_MD = ROOT / "docs" / "feature-inventory.md"
DEFAULT_REPORT = ROOT / "docs" / "reports" / "omp-m2-bdd" / "evidence" / "cucumber-messages.ndjson"

#: Hand-declared disposition per tracked feature file.
DISPOSITIONS: dict[str, dict[str, str]] = {
    "docs/stories/DT-01.feature": {"status": "executed", "reason": ""},
    "docs/stories/DT-02.feature": {"status": "executed", "reason": ""},
    "docs/stories/DT-03.feature": {"status": "executed", "reason": ""},
    "docs/stories/DT-04.feature": {"status": "executed", "reason": ""},
    "docs/stories/DT-05.feature": {"status": "executed", "reason": ""},
    "docs/stories/DT-06.feature": {"status": "executed", "reason": ""},
    "docs/stories/AS-01.feature": {"status": "executed", "reason": ""},
    "docs/stories/AS-02.feature": {"status": "executed", "reason": ""},
    "docs/stories/AS-03.feature": {"status": "executed", "reason": ""},
    "docs/stories/AS-04.feature": {"status": "executed", "reason": ""},
    "docs/stories/AS-05.feature": {"status": "executed", "reason": ""},
    "docs/stories/FT-01.feature": {"status": "executed", "reason": ""},
    "docs/stories/FT-02.feature": {
        "status": "executed-with-superseded-scenario",
        "reason": "SCN-205 asserted the M0 501 contract; AS-01 implemented the endpoint in M1. The "
        "scenario keeps its approved wording and is excluded by @superseded-by-AS-01.",
    },
    "docs/stories/FT-03.feature": {
        "status": "inspection",
        "reason": "Process/governance criteria verified by inspection and analysis per FT-03.md; "
        "they assert document properties, not application behaviour.",
    },
    "docs/stories/SETUP-01.feature": {"status": "executed", "reason": ""},
    "docs/stories/AI-01.feature": {"status": "executed", "reason": ""},
    "docs/stories/AI-05.feature": {"status": "executed", "reason": ""},
    "docs/stories/AI-07.feature": {"status": "executed", "reason": ""},
    "docs/stories/AI-08.feature": {"status": "executed", "reason": ""},
    "docs/stories/AI-09.feature": {"status": "executed", "reason": ""},
    "docs/stories/AI-06.feature": {
        "status": "out-of-scope",
        "reason": "M3 CocoIndex slice; not an M0/M1 acceptance feature and outside the M2 "
        "executable-migration scope.",
    },
    "docs/stories/GT-01.feature": {"status": "executed", "reason": ""},
    "docs/stories/GT-02.feature": {"status": "executed", "reason": ""},
    "docs/stories/GT-03.feature": {"status": "executed", "reason": ""},
    "docs/stories/PG-01.feature": {"status": "executed", "reason": ""},
    "bdd/probes/passing/feature.feature": {
        "status": "probe",
        "reason": "Harness probe executed on demand by GT-01 to prove real assertion reporting.",
    },
    "bdd/probes/undefined/feature.feature": {
        "status": "probe",
        "reason": "GT-01 probe: undefined steps must fail the gate.",
    },
    "bdd/probes/ambiguous/feature.feature": {
        "status": "probe",
        "reason": "GT-01 probe: ambiguous steps must fail the gate.",
    },
    "bdd/probes/failing/feature.feature": {
        "status": "probe",
        "reason": "GT-01 probe: assertion failures must be recorded.",
    },
    "fixtures/external-recipes/tree/features/browse.feature": {
        "status": "external",
        "reason": "Independently developed fixture indexed read-only by the portable path; never "
        "executed by CTA's acceptance suite and never modified.",
    },
    "fixtures/external-recipes/tree/features/publish.feature": {
        "status": "external",
        "reason": "Independently developed fixture indexed read-only by the portable path; never "
        "executed by CTA's acceptance suite and never modified.",
    },
    "fixtures/external-recipes/changes/02-ratings/features/ratings.feature": {
        "status": "external",
        "reason": "Second-revision overlay of the external fixture; used to prove revision "
        "isolation and undefined-step reporting from a real framework report.",
    },
    "fixtures/external-twin/tree/features/browse.feature": {
        "status": "external",
        "reason": "Collision probe: same relative path and @SCN-001 tag as external-recipes.",
    },
    "fixtures/banking-demo/tree/features/withdrawals.feature": {
        "status": "monitored",
        "reason": "Specification of the monitored banking application; executed by that "
        "application's own pytest suite, never by CTA's acceptance suite.",
    },
    "fixtures/banking-demo/tree/features/transfers.feature": {
        "status": "monitored",
        "reason": "Specification of the monitored banking application; executed by that "
        "application's own pytest suite, never by CTA's acceptance suite.",
    },
}

CLASSIFICATIONS = {
    "monitored": "monitored_application_specification",
    "probe": "harness_probe",
    "external": "external_indexed_specification",
}
DEFAULT_CLASSIFICATION = "cta_acceptance_specification"


def tracked_features() -> list[str]:
    output = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "*.feature"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    return sorted(line for line in output.stdout.splitlines() if line)


def parse(path: Path) -> tuple[int, list[str]]:
    document = Parser().parse(TokenScanner(path.read_text(encoding="utf-8")))
    feature = document["feature"]
    scenarios: list[dict] = []

    def collect(children: list[dict], rule: str | None = None) -> None:
        for child in children:
            if "background" in child:
                continue
            if "rule" in child:
                collect(child["rule"].get("children", []), child["rule"].get("name"))
                continue
            scenario = child.get("scenario")
            if scenario is not None:
                scenarios.append({"scenario": scenario, "rule": rule})

    collect(feature.get("children", []))
    patterns: list[str] = []
    for entry in scenarios:
        for step in entry["scenario"].get("steps", []):
            pattern = f"{step['keyword'].strip()} {step['text']}".strip()
            if pattern not in patterns:
                patterns.append(pattern)
    return len(scenarios), patterns


def _excluded_tags() -> set[str]:
    config = (ROOT / "bdd" / "cucumber.mjs").read_text(encoding="utf-8")
    return set(re.findall(r"not\s+(@[\w-]+)", config))


def report_stats(report: Path) -> dict[str, dict[str, int]]:
    """Per feature URI: eligible pickles, attempt completeness, and honest outcome counts."""
    import json

    if not report.exists():
        raise SystemExit(f"acceptance report {report} is missing; run the Cucumber suite first")
    excluded = _excluded_tags()
    documents: set[str] = set()
    pickles: dict[str, dict] = {}
    test_cases: dict[str, dict] = {}
    started: dict[str, str] = {}
    finished: set[str] = set()
    results: dict[str, dict[str, list[str]]] = {}
    for line in report.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        envelope = json.loads(line)
        if "gherkinDocument" in envelope:
            documents.add(envelope["gherkinDocument"]["uri"])
        if "pickle" in envelope:
            pickles[envelope["pickle"]["id"]] = envelope["pickle"]
        if "testCase" in envelope:
            test_cases[envelope["testCase"]["id"]] = envelope["testCase"]
        if "testCaseStarted" in envelope:
            started[envelope["testCaseStarted"]["id"]] = envelope["testCaseStarted"]["testCaseId"]
        if "testCaseFinished" in envelope:
            finished.add(envelope["testCaseFinished"]["testCaseStartedId"])
        if "testStepFinished" in envelope:
            item = envelope["testStepFinished"]
            results.setdefault(item["testCaseStartedId"], {}).setdefault(
                item["testStepId"], []
            ).append(item["testStepResult"]["status"])

    def blank() -> dict[str, int]:
        return {
            "pickles": 0,
            "eligible": 0,
            "cases": 0,
            "started": 0,
            "failed": 0,
            "passed": 0,
            "incomplete": 0,
            "skipped_results": 0,
            "missing_results": 0,
            "duplicate_results": 0,
            "unknown_results": 0,
        }

    stats: dict[str, dict[str, int]] = {uri.lstrip("./"): blank() for uri in documents}
    for pickle in pickles.values():
        row = stats.setdefault(pickle["uri"].lstrip("./"), blank())
        row["pickles"] += 1
        if not any(tag["name"] in excluded for tag in pickle.get("tags", [])):
            row["eligible"] += 1

    orphan_attempts = [
        (attempt_id, case_id)
        for attempt_id, case_id in started.items()
        if case_id not in test_cases or test_cases[case_id].get("pickleId") not in pickles
    ]
    if orphan_attempts:
        raise SystemExit(
            f"{report} contains {len(orphan_attempts)} started attempt(s) that do not resolve to "
            "a known test case and pickle; the report cannot establish execution completeness"
        )
    orphan_results = [key for key in results if key not in started]
    if orphan_results:
        raise SystemExit(
            f"{report} contains {len(orphan_results)} result(s) for unknown attempts; "
            "the report cannot establish execution completeness"
        )

    covered: set[str] = set()
    for case_id, case in test_cases.items():
        pickle = pickles.get(case["pickleId"])
        if pickle is None:
            continue
        uri = pickle["uri"].lstrip("./")
        row = stats.setdefault(uri, blank())
        row["cases"] += 1
        covered.add(pickle["id"])
        attempts = [key for key, value in started.items() if value == case_id]
        if not attempts:
            continue
        row["started"] += 1
        expected = {step["id"] for step in case.get("testSteps", [])}
        for attempt in attempts:
            supplied = results.get(attempt, {})
            missing = expected - supplied.keys()
            unknown = supplied.keys() - expected
            duplicates = sum(1 for statuses in supplied.values() if len(statuses) > 1)
            row["missing_results"] += len(missing)
            row["unknown_results"] += len(unknown)
            row["duplicate_results"] += duplicates
            statuses = [
                statuses[0] for step_id, statuses in supplied.items() if step_id in expected
            ]
            row["skipped_results"] += sum(1 for status in statuses if status == "SKIPPED")
            if attempt not in finished or missing or unknown or duplicates:
                row["incomplete"] += 1
                continue
            if "FAILED" in statuses:
                row["failed"] += 1
            elif all(status == "PASSED" for status in statuses):
                row["passed"] += 1
            else:
                row["incomplete"] += 1

    for pickle in pickles.values():
        if any(tag["name"] in excluded for tag in pickle.get("tags", [])):
            continue
        if pickle["id"] not in covered:
            stats.setdefault(pickle["uri"].lstrip("./"), blank())["incomplete"] += 1
    return stats


def main() -> int:
    files = tracked_features()
    stats = report_stats(DEFAULT_REPORT)
    entries = []
    for name in files:
        disposition = DISPOSITIONS.get(name)
        if disposition is None:
            raise SystemExit(f"{name} has no declared disposition; add one before regenerating")
        scenario_count, patterns = parse(ROOT / name)
        story = Path(name).stem.split(".")[0]
        status = disposition["status"]
        stats_for_file = stats.get(name, {"pickles": 0, "cases": 0, "started": 0, "failed": 0})
        declared_executed = status.startswith("executed")
        if declared_executed and stats_for_file["pickles"] == 0:
            raise SystemExit(f"{name} is declared executed but absent from {DEFAULT_REPORT}")
        if declared_executed and stats_for_file["started"] < stats_for_file["cases"]:
            raise SystemExit(
                f"{name} is declared executed but only {stats_for_file['started']} of "
                f"{stats_for_file['cases']} test cases started"
            )
        if not declared_executed and stats_for_file["started"]:
            raise SystemExit(
                f"{name} is declared not executed but appears as started in the report"
            )
        executed = declared_executed and stats_for_file["cases"] > 0
        complete = (
            executed
            and stats_for_file["eligible"] > 0
            and stats_for_file["cases"] >= stats_for_file["eligible"]
            and stats_for_file["started"] == stats_for_file["cases"]
            and stats_for_file["passed"] == stats_for_file["cases"]
            and stats_for_file["failed"] == 0
            and stats_for_file["incomplete"] == 0
            and stats_for_file["skipped_results"] == 0
            and stats_for_file["missing_results"] == 0
            and stats_for_file["duplicate_results"] == 0
            and stats_for_file["unknown_results"] == 0
        )
        result = (
            "failed"
            if stats_for_file["failed"]
            else "passing"
            if complete
            else "incomplete"
            if executed
            else "on_demand"
            if status == "probe"
            else "not_applicable"
        )
        entries.append(
            {
                "file": name,
                "classification": CLASSIFICATIONS.get(status, DEFAULT_CLASSIFICATION),
                "story_id": story if name.startswith("docs/stories/") else None,
                "scenario_count": scenario_count,
                "unique_step_patterns": patterns,
                "cucumber_status": "executed" if executed else "not_executed",
                "execution_result": result,
                "eligible_scenarios": stats_for_file["eligible"] if executed else 0,
                "executed_scenarios": stats_for_file["started"] if executed else 0,
                "failed_scenarios": stats_for_file["failed"] if executed else 0,
                "incomplete_scenarios": stats_for_file["incomplete"] if executed else 0,
                "skipped_results": stats_for_file["skipped_results"] if executed else 0,
                "missing_results": stats_for_file["missing_results"] if executed else 0,
                "duplicate_results": stats_for_file["duplicate_results"] if executed else 0,
                "unknown_results": stats_for_file["unknown_results"] if executed else 0,
                "report": str(DEFAULT_REPORT.relative_to(ROOT)) if executed else None,
                "migration_status": "complete" if complete else "pending",
                "reason": disposition["reason"],
                "repository_identity": "cta" if name.startswith("docs/") else "banking-demo",
                "ref": str(DEFAULT_REPORT.relative_to(ROOT)) if executed else None,
                "annotation_dependency": name.startswith("fixtures/"),
                "binding_evidence": "cucumber-js 13.3.0 messages" if executed else "not_executed",
                "modification_audit": "read-only input" if name.startswith("fixtures/") else "n/a",
            }
        )
    payload = {
        "generated_by": "tools/feature_inventory.py",
        "notes": [
            "Counts and step patterns are parsed; classification, status, and reasons are declared "
            "in the generator by hand.",
            "Cucumber execution is recorded only for entries with a captured messages report.",
        ],
        "features": entries,
    }
    OUT_JSON.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Feature inventory",
        "",
        "Generated by `tools/feature_inventory.py`; counts are parsed, "
        "classifications are declared.",
        "",
        "| Feature | Classification | Scenarios | Cucumber | Migration | Reason |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for entry in entries:
        lines.append(
            f"| `{entry['file']}` | {entry['classification']} | {entry['scenario_count']} | "
            f"{entry['cucumber_status']} | {entry['migration_status']} | {entry['reason'] or '—'} |"
        )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        f"wrote {OUT_JSON.relative_to(ROOT)} and {OUT_MD.relative_to(ROOT)} ({len(entries)} files)"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
