"""Honesty of the Cucumber adapter: hook failures, skipped runs, and report provenance."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from app.domain.errors import ReportNotApplicable
from app.domain.portable import ExecutionImportRequest, ExecutionOutcome
from app.persistence.portable import PortableRegistry

FEATURE = "Feature: Probe\n  Scenario: One\n    Given a step\n"


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def _repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "--quiet", "-b", "main")
    _git(repo, "config", "user.name", "Probe")
    _git(repo, "config", "user.email", "probe@example.invalid")
    (repo / "features").mkdir()
    (repo / "features" / "a.feature").write_text(FEATURE, encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "--quiet", "-m", "probe")
    return repo


def _envelopes(*, hook_status: str | None, step_status: str, success: bool) -> list[dict]:
    document = {
        "uri": "features/a.feature",
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
                        "name": "One",
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
    test_steps = [{"id": "ts1", "pickleStepId": "ps1", "stepDefinitionIds": ["d1"]}]
    finished = [
        {
            "testStepFinished": {
                "testCaseStartedId": "start1",
                "testStepId": "ts1",
                "testStepResult": {"status": step_status, "duration": {"seconds": 0, "nanos": 1}},
                "timestamp": {"seconds": 2},
            }
        }
    ]
    if hook_status is not None:
        test_steps.append({"id": "hook1", "hookId": "h1"})
        finished.append(
            {
                "testStepFinished": {
                    "testCaseStartedId": "start1",
                    "testStepId": "hook1",
                    "testStepResult": {
                        "status": hook_status,
                        "duration": {"seconds": 0, "nanos": 1},
                    },
                    "timestamp": {"seconds": 3},
                }
            }
        )
    return [
        {
            "meta": {
                "protocolVersion": "34.2.1",
                "implementation": {"name": "cucumber-js", "version": "13.3.0"},
            }
        },
        {
            "source": {
                "uri": "features/a.feature",
                "data": FEATURE,
                "mediaType": "text/x.cucumber.gherkin+plain",
            }
        },
        {"gherkinDocument": document},
        {
            "pickle": {
                "id": "p1",
                "uri": "features/a.feature",
                "name": "One",
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
                "sourceReference": {"uri": "steps/a.js", "location": {"line": 1}},
            }
        },
        {"testCase": {"id": "tc1", "pickleId": "p1", "testSteps": test_steps}},
        {
            "testCaseStarted": {
                "id": "start1",
                "testCaseId": "tc1",
                "attempt": 0,
                "timestamp": {"seconds": 1},
            }
        },
        *[
            {
                "testStepStarted": {
                    "testCaseStartedId": "start1",
                    "testStepId": step["id"],
                    "timestamp": {"seconds": 1},
                }
            }
            for step in test_steps
        ],
        *finished,
        {"testRunFinished": {"success": success, "timestamp": {"seconds": 4}}},
    ]


def _write(tmp_path: Path, name: str, envelopes: list[dict]) -> Path:
    path = tmp_path / f"{name}.ndjson"
    path.write_text("\n".join(json.dumps(item) for item in envelopes) + "\n", encoding="utf-8")
    return path


def _metadata(tmp_path: Path, commit: str, repository_id: str = "probe") -> Path:
    path = tmp_path / "report.meta.json"
    path.write_text(
        json.dumps({"repository_id": repository_id, "tested_commit": commit}), encoding="utf-8"
    )
    return path


def _import(tmp_path: Path, repo: Path, *, hook_status, step_status, success):
    registry = PortableRegistry()
    commit = registry.index(repo, repository_id="probe", revision="HEAD").revision
    report_path = _write(
        tmp_path,
        f"report-{hook_status}-{step_status}",
        _envelopes(hook_status=hook_status, step_status=step_status, success=success),
    )
    report, _ = registry.import_report(
        "probe",
        ExecutionImportRequest(
            report_path=str(report_path),
            metadata_path=str(_metadata(tmp_path, commit)),
            tested_commit=commit,
        ),
    )
    return registry, report, commit


def test_hook_failure_fails_the_scenario(tmp_path):
    repo = _repo(tmp_path)
    _, report, _ = _import(
        tmp_path, repo, hook_status="FAILED", step_status="PASSED", success=False
    )
    assert report.executions[0].outcome is ExecutionOutcome.FAILED
    assert report.executions[0].steps[0].outcome is ExecutionOutcome.PASSED


def test_skipped_run_is_not_observed_execution(tmp_path):
    repo = _repo(tmp_path)
    registry, report, commit = _import(
        tmp_path, repo, hook_status=None, step_status="SKIPPED", success=True
    )
    assert report.executions[0].outcome is ExecutionOutcome.SKIPPED
    coverage = registry.coverage("probe", commit)
    assert coverage.steps_executed == 0
    assert coverage.scenarios_executed == 0
    relations = registry.relations("probe", commit)
    assert not [
        relation for relation in relations if relation.relation.value == "EXECUTED_DEFINITION"
    ]
    assert not [
        relation for relation in relations if relation.relation.value == "HAS_STEP_EXECUTION"
    ]


def test_report_without_provenance_is_rejected(tmp_path):
    repo = _repo(tmp_path)
    registry = PortableRegistry()
    commit = registry.index(repo, repository_id="probe", revision="HEAD").revision
    report_path = _write(
        tmp_path, "noprovenance", _envelopes(hook_status=None, step_status="PASSED", success=True)
    )
    with pytest.raises(ReportNotApplicable, match="metadata"):
        registry.import_report(
            "probe",
            ExecutionImportRequest(
                report_path=str(report_path), metadata_path="", tested_commit=commit
            ),
        )


def test_same_report_cannot_be_rebased_onto_another_commit(tmp_path):
    repo = _repo(tmp_path)
    registry, report, commit = _import(
        tmp_path, repo, hook_status=None, step_status="PASSED", success=True
    )
    _git(repo, "commit", "--quiet", "--allow-empty", "-m", "evidence only")
    second = registry.index(repo, repository_id="probe", revision="HEAD").revision
    assert second != commit
    with pytest.raises(ReportNotApplicable, match="already attributed"):
        registry.import_report(
            "probe",
            ExecutionImportRequest(
                report_path=report.report_uri,
                metadata_path=str(_metadata(tmp_path, second)),
                tested_commit=second,
            ),
        )
