"""Deterministic Cucumber report fixture for the M4 BDD self-assurance scenarios.

The report is attributable to one tracked feature at HEAD: its ``source`` envelope contains the
exact feature bytes, so the portable importer's provenance check is real. The scenario document is a
minimal executable probe; the point is the pinned source hash and execution outcome, not the CTA's
own scenario suite.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _git_show(feature: str) -> str:
    result = subprocess.run(
        ["git", "show", f"HEAD:{feature}"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"cannot read HEAD:{feature}: {result.stderr.strip()}")
    return result.stdout


def build_probe_report(state_dir: Path, *, feature: str, failed: bool) -> dict[str, str]:
    source = _git_show(feature)
    scenarios = "1 failed" if failed else "1 passed"
    document = {
        "uri": feature,
        "feature": {
            "location": {"line": 1, "column": 1},
            "language": "en",
            "keyword": "Feature",
            "name": "Probe",
            "description": "",
            "tags": [],
            "children": [
                {
                    "scenario": {
                        "id": "s1",
                        "tags": [],
                        "location": {"line": 2, "column": 3},
                        "keyword": "Scenario",
                        "name": "Probe scenario",
                        "description": "",
                        "steps": [
                            {
                                "id": "st1",
                                "location": {"line": 3, "column": 5},
                                "keyword": "Given ",
                                "keywordType": "Context",
                                "text": "a step",
                            }
                        ],
                        "examples": [],
                    }
                }
            ],
        },
    }
    status = "FAILED" if failed else "PASSED"
    envelopes = [
        {
            "meta": {
                "protocolVersion": "34.2.1",
                "implementation": {"name": "cucumber-js", "version": "13.3.0"},
            }
        },
        {
            "source": {
                "uri": feature,
                "data": source,
                "mediaType": "text/x.cucumber.gherkin+plain",
            }
        },
        {"gherkinDocument": document},
        {
            "pickle": {
                "id": "p1",
                "uri": feature,
                "name": "Probe scenario",
                "language": "en",
                "astNodeIds": ["s1"],
                "location": {"line": 2, "column": 3},
                "steps": [{"id": "ps1", "text": "a step", "astNodeIds": ["st1"]}],
                "tags": [],
            }
        },
        {
            "stepDefinition": {
                "id": "d1",
                "pattern": {"source": "a step", "type": "CUCUMBER_EXPRESSION"},
                "sourceReference": {"uri": "bdd/steps/probe.js", "location": {"line": 1}},
            }
        },
        {
            "testCase": {
                "id": "tc1",
                "pickleId": "p1",
                "testSteps": [{"id": "ts1", "pickleStepId": "ps1", "stepDefinitionIds": ["d1"]}],
            }
        },
        {
            "testCaseStarted": {
                "id": "start1",
                "testCaseId": "tc1",
                "attempt": 0,
                "timestamp": {"seconds": 1},
            }
        },
        {
            "testStepStarted": {
                "testCaseStartedId": "start1",
                "testStepId": "ts1",
                "timestamp": {"seconds": 1},
            }
        },
        {
            "testStepFinished": {
                "testCaseStartedId": "start1",
                "testStepId": "ts1",
                "testStepResult": {"status": status, "duration": {"seconds": 0, "nanos": 1}},
                "timestamp": {"seconds": 2},
            }
        },
        {"testRunFinished": {"success": not failed, "timestamp": {"seconds": 3}}},
    ]
    state_dir.mkdir(parents=True, exist_ok=True)
    report_path = state_dir / f"probe-{'failed' if failed else 'passed'}.ndjson"
    report_path.write_text(
        "\n".join(json.dumps(item) for item in envelopes) + "\n", encoding="utf-8"
    )
    commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=REPO_ROOT, capture_output=True, text=True, check=True
    ).stdout.strip()
    metadata_path = state_dir / f"probe-{'failed' if failed else 'passed'}.meta.json"
    metadata_path.write_text(
        json.dumps({"repository_id": "gherkin-knowledge-graph", "tested_commit": commit}),
        encoding="utf-8",
    )
    return {
        "report": str(report_path),
        "metadata": str(metadata_path),
        "tested_commit": commit,
        "feature": feature,
        "outcome": scenarios,
    }
