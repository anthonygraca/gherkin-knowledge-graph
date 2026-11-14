"""Repository-scoped API and CLI: pinned revisions, honest unknown states, isolation."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.persistence.portable import PortableRegistry

REPORTS = (
    Path(__file__).resolve().parents[2] / "docs" / "reports" / "omp-m2-portability" / "evidence"
)


@pytest.fixture(autouse=True)
def _fresh_registry(client):
    """Each test starts with no indexed repositories: state must never leak between tests."""
    client.app.state.portable = PortableRegistry()
    yield


def _index(client, external_repos, fixture: str, ref: str) -> dict:
    response = client.post(
        "/api/repositories/index",
        json={"path": str(external_repos[fixture].path), "repository_id": fixture, "revision": ref},
    )
    assert response.status_code == 200, response.text
    return response.json()


def test_index_and_query_untagged_scenarios(client, external_repos):
    summary = _index(client, external_repos, "external-recipes", "v1")
    assert summary["repository_id"] == "external-recipes"
    assert summary["revision"] == external_repos["external-recipes"].tags["v1"]
    assert summary["counts"] == {
        "features": 2,
        "scenarios": 4,
        "scenario_outlines": 1,
        "example_instances": 2,
        "steps": 15,
        "untagged_scenarios": 3,
        "diagnostics": 0,
    }
    assert summary["files_modified"] == 0
    assert summary["hooks_executed"] is False

    listing = client.get("/api/repositories").json()
    assert [item["repository_id"] for item in listing["repositories"]] == ["external-recipes"]

    scenarios = client.get(
        "/api/repositories/external-recipes/scenarios",
        params={"revision": "v1", "tag": "SCN-001"},
    ).json()
    assert len(scenarios["scenarios"]) == 1
    tagged = scenarios["scenarios"][0]
    assert tagged["tags"] == ["@SCN-001"]
    assert tagged["path"] == "features/browse.feature"
    assert tagged["line"] == 16

    untagged = client.get(
        "/api/repositories/external-recipes/scenarios",
        params={"revision": "v1", "path": "features/publish.feature"},
    ).json()
    assert [scenario["tags"] for scenario in untagged["scenarios"]] == [[]]

    one = client.get(
        "/api/repositories/external-recipes/scenario",
        params={"revision": "v1", "scenario_key": tagged["scenario_key"]},
    ).json()
    assert [step["text"] for step in one["steps"]] == [
        'the catalog contains "Soup" and "Stew"',
        'a draft recipe "Pie"',
        "the visitor opens the catalog",
        'the catalog does not show "Pie"',
    ]

    steps = client.get(
        "/api/repositories/external-recipes/steps",
        params={"revision": "v1", "text": "searches"},
    ).json()
    assert {step["text"] for step in steps["steps"]} == {'the visitor searches for "<term>"'}


def test_bindings_are_not_available_until_a_report_is_imported(client, external_repos):
    _index(client, external_repos, "external-recipes", "v1")
    bindings = client.get(
        "/api/repositories/external-recipes/bindings", params={"revision": "v1"}
    ).json()
    assert bindings["availability"] == "not_available"
    assert bindings["step_definitions"] == []
    assert bindings["resolutions"] == []
    assert "unknown, not undefined" in bindings["reason"]

    unresolved = client.get(
        "/api/repositories/external-recipes/unresolved-steps", params={"revision": "v1"}
    ).json()
    assert unresolved["availability"] == "not_available"
    assert unresolved["resolutions"] == []

    findings = client.get(
        "/api/repositories/external-recipes/executable-findings", params={"revision": "v1"}
    ).json()
    assert findings["findings"] == []


def test_report_import_populates_matches_and_executions(client, external_repos):
    _index(client, external_repos, "external-recipes", "v1")
    commit = external_repos["external-recipes"].tags["v1"]
    imported = client.post(
        "/api/repositories/external-recipes/reports",
        json={
            "report_path": str(REPORTS / "cucumber-report.v1.ndjson"),
            "metadata_path": str(REPORTS / "cucumber-report.v1.meta.json"),
            "tested_commit": commit,
        },
    )
    assert imported.status_code == 200, imported.text
    body = imported.json()
    assert body["imported"] is True
    assert body["execution_count"] == 5
    assert body["step_definition_count"] == 13
    assert body["tested_commit"] == commit

    again = client.post(
        "/api/repositories/external-recipes/reports",
        json={
            "report_path": str(REPORTS / "cucumber-report.v1.ndjson"),
            "metadata_path": str(REPORTS / "cucumber-report.v1.meta.json"),
            "tested_commit": commit,
        },
    ).json()
    assert again["imported"] is False
    assert again["report_digest"] == body["report_digest"]

    bindings = client.get(
        "/api/repositories/external-recipes/bindings", params={"revision": "v1"}
    ).json()
    assert bindings["availability"] == "available"
    assert len(bindings["step_definitions"]) == 13
    assert {definition["source_path"] for definition in bindings["step_definitions"]} == {
        "steps/browse_steps.js",
        "steps/publish_steps.js",
    }
    assert {resolution["status"] for resolution in bindings["resolutions"]} == {"matched"}

    executions = client.get(
        "/api/repositories/external-recipes/executions", params={"revision": "v1"}
    ).json()
    assert len(executions["executions"]) == 5
    assert {item["outcome"] for item in executions["executions"]} == {"passed"}
    assert executions["coverage"]["scenarios_executed"] == 4
    assert executions["coverage"]["scenarios_without_execution"] == 0
    assert executions["reports"][0]["tested_commit"] == commit

    relations = client.get(
        "/api/repositories/external-recipes/relations", params={"revision": "v1"}
    ).json()
    assert {relation["relation"] for relation in relations["relations"]} >= {
        "HAS_STEP",
        "EXPANDS_TO",
        "MATCHES_DEFINITION",
        "HAS_STEP_EXECUTION",
        "EXECUTED_DEFINITION",
    }
    assert {relation["origin"] for relation in relations["relations"]} <= {
        "extracted",
        "matched",
        "observed",
    }


def test_undefined_steps_are_reported_only_with_a_report(client, external_repos):
    _index(client, external_repos, "external-recipes", "v2")
    commit = external_repos["external-recipes"].tags["v2"]
    client.post(
        "/api/repositories/external-recipes/reports",
        json={
            "report_path": str(REPORTS / "cucumber-report.v2.ndjson"),
            "metadata_path": str(REPORTS / "cucumber-report.v2.meta.json"),
            "tested_commit": commit,
        },
    )
    unresolved = client.get(
        "/api/repositories/external-recipes/unresolved-steps", params={"revision": "v2"}
    ).json()
    assert unresolved["availability"] == "available"
    assert len(unresolved["resolutions"]) == 4
    assert {resolution["status"] for resolution in unresolved["resolutions"]} == {"undefined"}

    findings = client.get(
        "/api/repositories/external-recipes/executable-findings", params={"revision": "v2"}
    ).json()
    assert findings["tested_commit"] == commit
    assert len(findings["findings"]) == 4
    assert {finding["finding_type"] for finding in findings["findings"]} == {"undefined_step"}
    assert all(finding["rule_id"] == "RULE-UNDEFINED-STEP" for finding in findings["findings"])


def test_errors_are_honest(client, external_repos):
    _index(client, external_repos, "external-recipes", "v1")
    commit = external_repos["external-recipes"].tags["v1"]

    unknown_repo = client.get("/api/repositories/never-indexed/scenarios")
    assert unknown_repo.status_code == 404
    assert unknown_repo.json()["code"] == "repository-not-indexed"

    unknown_scenario = client.get(
        "/api/repositories/external-recipes/scenario",
        params={
            "revision": "v1",
            "scenario_key": "external-recipes:features/browse.feature#SCN-L999",
        },
    )
    assert unknown_scenario.status_code == 404
    assert unknown_scenario.json()["code"] == "scenario-not-found"

    mismatch = client.post(
        "/api/repositories/external-recipes/reports",
        json={
            "report_path": str(REPORTS / "cucumber-report.v2.ndjson"),
            "metadata_path": str(REPORTS / "cucumber-report.v2.meta.json"),
            "tested_commit": commit,
        },
    )
    assert mismatch.status_code == 400
    assert mismatch.json()["code"] == "report-not-applicable"

    other_revision = client.get(
        "/api/repositories/external-recipes/scenarios", params={"revision": "v2"}
    )
    assert other_revision.status_code == 404


def test_cli_prints_json_and_never_invents_bindings(external_repos, capsys):
    from app.cli import main

    path = external_repos["external-recipes"].path
    exit_code = main(["scenarios", str(path), "--repo-id", "external-recipes", "--ref", "v1"])
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert len(payload["scenarios"]) == 4
    assert payload["repository_id"] == "external-recipes"

    exit_code = main(["definitions", str(path), "--repo-id", "external-recipes", "--ref", "v1"])
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["availability"] == "not_available"
    assert payload["resolutions"] == []

    exit_code = main(["findings", str(path), "--repo-id", "external-recipes", "--ref", "v1"])
    assert exit_code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["findings"] == []
    assert payload["tested_commit"] is None


def test_cli_reports_failure_on_unknown_ref(external_repos, capsys):
    from app.cli import main

    exit_code = main(
        ["scenarios", str(external_repos["external-twin"].path), "--repo-id", "twin", "--ref", "v9"]
    )
    assert exit_code == 2
    error = json.loads(capsys.readouterr().err)
    assert error["error"]


def test_execution_provenance_is_revision_scoped(client, external_repos):
    _index(client, external_repos, "external-recipes", "v1")
    _index(client, external_repos, "external-recipes", "v2")
    v1 = external_repos["external-recipes"].tags["v1"]
    v2 = external_repos["external-recipes"].tags["v2"]
    for report, commit in (("v1", v1), ("v2", v2)):
        response = client.post(
            "/api/repositories/external-recipes/reports",
            json={
                "report_path": str(REPORTS / f"cucumber-report.{report}.ndjson"),
                "metadata_path": str(REPORTS / f"cucumber-report.{report}.meta.json"),
                "tested_commit": commit,
            },
        )
        assert response.status_code == 200, response.text
    first = client.get(
        "/api/repositories/external-recipes/executions", params={"revision": "v1"}
    ).json()
    second = client.get(
        "/api/repositories/external-recipes/executions", params={"revision": "v2"}
    ).json()
    assert [item["tested_commit"] for item in first["reports"]] == [v1]
    assert [item["tested_commit"] for item in second["reports"]] == [v2]
    assert {item["tested_commit"] for item in first["executions"]} == {v1}
    assert {item["tested_commit"] for item in second["executions"]} == {v2}
