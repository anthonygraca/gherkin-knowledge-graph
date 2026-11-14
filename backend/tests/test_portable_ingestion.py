"""Portable ingestion: hand-labeled inventory, identity isolation, read-only behaviour, adapter.

Oracle discipline: expected counts and locators come from
``fixtures/external-*/expected/inventory.json`` (hand-counted from the feature files). The report
evidence is a captured artifact; its manifest records the exact commit each report tested.
"""

from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from app.domain.errors import ReportNotApplicable
from app.domain.portable import (
    BindingAvailability,
    ExecutionImportRequest,
    ExecutionOutcome,
    StepMatchStatus,
)
from app.ingestion.cucumber_messages import CucumberMessagesAdapter, CucumberReportError
from app.ingestion.portable import PortableIndexer, summarize
from app.persistence.portable import PortableRegistry

ROOT = Path(__file__).resolve().parents[2]
REPORTS = ROOT / "docs" / "reports" / "omp-m2-portability" / "evidence"
FIXTURE_DIRS = {
    "external-recipes": ROOT / "fixtures" / "external-recipes",
    "external-twin": ROOT / "fixtures" / "external-twin",
}


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=False)
    assert result.returncode == 0, result.stderr
    return result.stdout


def _inventory(fixture: str) -> dict:
    return json.loads((FIXTURE_DIRS[fixture] / "expected" / "inventory.json").read_text("utf-8"))


def _report(ref: str) -> Path:
    return REPORTS / f"cucumber-report.{ref}.ndjson"


def _metadata(ref: str) -> Path:
    return REPORTS / f"cucumber-report.{ref}.meta.json"


@pytest.mark.parametrize(
    ("fixture", "ref"),
    [("external-recipes", "v1"), ("external-recipes", "v2"), ("external-twin", "v1")],
)
def test_hand_labeled_inventory_matches(external_repos, fixture, ref):
    repo = external_repos[fixture]
    snapshot = PortableIndexer().index(repo.path, repository_id=fixture, revision=ref)
    label = _inventory(fixture)["refs"][ref]
    counts = summarize(snapshot)
    assert counts.features == label["features"]
    assert counts.scenarios == label["scenarios"]
    assert counts.scenario_outlines == label["scenario_outlines"]
    assert counts.example_instances == label["example_instances"]
    assert counts.steps == label["steps"]
    assert counts.untagged_scenarios == label["untagged_scenarios"]
    actual = [
        {
            "path": scenario.path,
            "line": scenario.line,
            "name": scenario.name,
            "kind": scenario.kind.value,
            "tags": scenario.tags,
            "step_count": len(scenario.steps),
            "instance_count": len(scenario.instances),
        }
        for feature in snapshot.features
        for scenario in feature.scenarios
    ]
    assert actual == label["scenario_inventory"]
    assert snapshot.diagnostics == []


def test_untagged_scenarios_need_no_cta_metadata(external_repos):
    repo = external_repos["external-recipes"]
    snapshot = PortableIndexer().index(repo.path, repository_id="external-recipes", revision="v1")
    untagged = [
        scenario
        for feature in snapshot.features
        for scenario in feature.scenarios
        if not scenario.tags
    ]
    assert len(untagged) == 3
    published = next(s for s in untagged if s.name == "Published recipes are listed")
    assert published.path == "features/browse.feature"
    assert published.line == 10
    assert published.steps[0].text == 'the catalog contains "Soup" and "Stew"'
    assert published.steps[0].from_background is True
    assert published.scenario_key.startswith("external-recipes:features/browse.feature#")
    # No requirement artifact is manufactured, and the snapshot says so explicitly.
    assert snapshot.annotation_dependency is False
    assert not hasattr(snapshot, "requirements")
    # The one CTA-looking tag present is carried as data, not used as identity.
    tagged = next(s for f in snapshot.features for s in f.scenarios if s.tags)
    assert tagged.tags == ["@SCN-001"]
    assert tagged.scenario_key != "SCN-001"


def test_same_tag_and_path_in_two_repositories_never_collide(external_repos):
    indexer = PortableIndexer()
    first = indexer.index(
        external_repos["external-recipes"].path, repository_id="external-recipes", revision="v1"
    )
    second = indexer.index(
        external_repos["external-twin"].path, repository_id="external-twin", revision="v1"
    )
    first_keys = {
        scenario.scenario_key for feature in first.features for scenario in feature.scenarios
    }
    second_keys = {
        scenario.scenario_key for feature in second.features for scenario in feature.scenarios
    }
    assert first_keys & second_keys == set()
    tag_a = next(s for f in first.features for s in f.scenarios if "@SCN-001" in s.tags)
    tag_b = next(s for f in second.features for s in f.scenarios if "@SCN-001" in s.tags)
    assert tag_a.path == tag_b.path == "features/browse.feature"
    assert tag_a.scenario_key != tag_b.scenario_key
    assert first.scenario(tag_b.scenario_key) is None
    assert second.scenario(tag_a.scenario_key) is None

    registry = PortableRegistry()
    registry.index(external_repos["external-recipes"].path, repository_id="external-recipes")
    registry.index(external_repos["external-twin"].path, repository_id="external-twin")
    queried = registry.snapshot("external-twin", "v1")
    assert {s.scenario_key for f in queried.features for s in f.scenarios} == second_keys


def _tree_hashes(repo: Path) -> dict[str, str]:
    hashes = {}
    for path in sorted(repo.rglob("*")):
        if path.is_file() and ".git" not in path.parts:
            hashes[str(path.relative_to(repo))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def test_indexing_is_read_only(external_repos):
    repo = external_repos["external-recipes"].path
    before = _tree_hashes(repo)
    status_before = _git(repo, "status", "--porcelain", "--untracked-files=all")
    head_before = _git(repo, "rev-parse", "HEAD").strip()
    PortableIndexer().index(repo, repository_id="external-recipes", revision="v1")
    after = _tree_hashes(repo)
    assert after == before
    assert _git(repo, "status", "--porcelain", "--untracked-files=all") == status_before
    assert _git(repo, "rev-parse", "HEAD").strip() == head_before


def test_reindex_is_deterministic(external_repos):
    registry = PortableRegistry()
    first = registry.index(
        external_repos["external-recipes"].path, repository_id="external-recipes", revision="v1"
    )
    second = registry.index(
        external_repos["external-recipes"].path, repository_id="external-recipes", revision="v1"
    )
    assert first == second
    assert first.files_modified == 0
    assert first.hooks_executed is False
    snapshot = registry.snapshot("external-recipes", "v1")
    assert snapshot.indexed_at == registry.snapshot("external-recipes", "v1").indexed_at


def _make_repo(
    tmp_path: Path, files: dict[str, str], symlinks: dict[str, str] | None = None
) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "--quiet", "-b", "main")
    _git(repo, "config", "user.name", "Test")
    _git(repo, "config", "user.email", "test@example.invalid")
    for name, content in files.items():
        target = repo / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    for name, target in (symlinks or {}).items():
        (repo / name).symlink_to(target)
    _git(repo, "add", "-A")
    _git(repo, "commit", "--quiet", "-m", "fixture")
    return repo


def test_invalid_gherkin_is_diagnosed_and_valid_files_survive(tmp_path):
    repo = _make_repo(
        tmp_path,
        {
            "features/good.feature": "Feature: Good\n  Scenario: fine\n    Given a step\n",
            "features/bad.feature": (
                'Feature: Bad\n  Scenario: broken\n    Given a step\n      """\n'
                "      never closed\n"
            ),
        },
    )
    snapshot = PortableIndexer().index(repo, repository_id="local-probe")
    assert [feature.path for feature in snapshot.features] == ["features/good.feature"]
    assert [(d.path, d.code) for d in snapshot.diagnostics] == [
        ("features/bad.feature", "invalid-gherkin")
    ]
    assert snapshot.diagnostics[0].line is not None


def test_symlinked_feature_is_refused(tmp_path):
    repo = _make_repo(
        tmp_path,
        {
            "features/real.feature": "Feature: Real\n  Scenario: fine\n    Given a step\n",
            "elsewhere/target.feature": "Feature: Target\n  Scenario: fine\n    Given a step\n",
        },
        symlinks={"features/linked.feature": "elsewhere/target.feature"},
    )
    snapshot = PortableIndexer().index(repo, repository_id="local-probe")
    assert [feature.path for feature in snapshot.features] == [
        "elsewhere/target.feature",
        "features/real.feature",
    ]
    assert [(d.path, d.code) for d in snapshot.diagnostics] == [
        ("features/linked.feature", "symlink")
    ]


def test_bindings_are_unknown_without_a_report(external_repos):
    registry = PortableRegistry()
    registry.index(
        external_repos["external-recipes"].path, repository_id="external-recipes", revision="v1"
    )
    availability, reason, definitions, resolutions, reports = registry.bindings(
        "external-recipes", "v1"
    )
    assert availability is BindingAvailability.NOT_AVAILABLE
    assert "unknown, not undefined" in reason
    assert definitions == [] and resolutions == [] and reports == []
    findings, tested_commit = registry.findings("external-recipes", "v1")
    assert findings == [] and tested_commit is None


def test_imported_report_links_matches_and_executions(external_repos):
    registry = PortableRegistry()
    registry.index(
        external_repos["external-recipes"].path, repository_id="external-recipes", revision="v1"
    )
    request = ExecutionImportRequest(
        report_path=str(_report("v1")),
        metadata_path=str(_metadata("v1")),
        tested_commit=external_repos["external-recipes"].tags["v1"],
    )
    report, already = registry.import_report("external-recipes", request)
    assert already is False
    assert report.runtime.startswith("cucumber-js 13.3.0")
    assert len(report.step_definitions) == 13
    assert {definition.source_path for definition in report.step_definitions} == {
        "steps/browse_steps.js",
        "steps/publish_steps.js",
    }

    availability, _, definitions, resolutions, reports = registry.bindings("external-recipes", "v1")
    assert availability is BindingAvailability.AVAILABLE
    assert len(definitions) == 13
    assert len(resolutions) == 23
    assert {resolution.status for resolution in resolutions} == {StepMatchStatus.MATCHED}
    assert all(len(resolution.definition_keys) == 1 for resolution in resolutions)

    executions, _ = registry.executions("external-recipes", "v1")
    assert len(executions) == 5
    assert {execution.outcome for execution in executions} == {ExecutionOutcome.PASSED}
    assert all(
        execution.tested_commit == external_repos["external-recipes"].tags["v1"]
        for execution in executions
    )
    assert [len(execution.steps) for execution in executions] == [3, 4, 4, 6, 6] or sorted(
        len(execution.steps) for execution in executions
    ) == [3, 4, 4, 6, 6]

    coverage = registry.coverage("external-recipes", "v1")
    assert coverage.scenarios_total == 4
    assert coverage.scenarios_executed == 4
    assert coverage.scenarios_without_execution == 0
    assert coverage.steps_total == 15
    assert coverage.steps_executed == 15

    relations = registry.relations("external-recipes", "v1")
    kinds = {relation.relation.value for relation in relations}
    assert {
        "HAS_STEP",
        "EXPANDS_TO",
        "MATCHES_DEFINITION",
        "HAS_STEP_EXECUTION",
        "EXECUTED_DEFINITION",
    } <= kinds
    assert all(
        relation.origin.value in {"extracted", "matched", "observed"} for relation in relations
    )

    findings, tested_commit = registry.findings("external-recipes", "v1")
    assert findings == []
    assert tested_commit == external_repos["external-recipes"].tags["v1"]


def test_undefined_steps_require_framework_evidence(external_repos):
    registry = PortableRegistry()
    registry.index(external_repos["external-recipes"].path, repository_id="external-recipes")
    report, _ = registry.import_report(
        "external-recipes",
        ExecutionImportRequest(
            report_path=str(_report("v2")),
            metadata_path=str(_metadata("v2")),
            tested_commit=external_repos["external-recipes"].tags["v2"],
        ),
    )
    undefined = [item for item in report.resolutions if item.status is StepMatchStatus.UNDEFINED]
    assert len(undefined) == 4
    assert {item.scenario_key.split("#")[0] for item in undefined} == {
        "external-recipes:features/ratings.feature"
    }

    executions, _ = registry.executions("external-recipes", "v2")
    ratings = next(execution for execution in executions if "ratings" in execution.feature_path)
    assert ratings.outcome is ExecutionOutcome.UNDEFINED

    findings, _ = registry.findings("external-recipes", "v2")
    assert {finding.finding_type.value for finding in findings} == {"undefined_step"}
    assert len(findings) == 4
    assert all(finding.rule_id.value == "RULE-UNDEFINED-STEP" for finding in findings)
    assert all(
        finding.artifact_keys[0].startswith("external-recipes:features/ratings.feature#")
        for finding in findings
    )


def test_report_for_a_different_revision_is_rejected(external_repos):
    registry = PortableRegistry()
    registry.index(
        external_repos["external-recipes"].path, repository_id="external-recipes", revision="v1"
    )
    with pytest.raises(ReportNotApplicable, match="refusing to relabel a run"):
        registry.import_report(
            "external-recipes",
            ExecutionImportRequest(
                report_path=str(_report("v2")),
                metadata_path=str(_metadata("v2")),
                tested_commit=external_repos["external-recipes"].tags["v1"],
            ),
        )


def test_reimport_is_idempotent(external_repos):
    registry = PortableRegistry()
    registry.index(
        external_repos["external-recipes"].path, repository_id="external-recipes", revision="v1"
    )
    request = ExecutionImportRequest(
        report_path=str(_report("v1")),
        metadata_path=str(_metadata("v1")),
        tested_commit=external_repos["external-recipes"].tags["v1"],
    )
    first, _ = registry.import_report("external-recipes", request)
    second, already = registry.import_report("external-recipes", request)
    assert already is True
    assert first.report_digest == second.report_digest
    assert [e.execution_key for e in first.executions] == [
        e.execution_key for e in second.executions
    ]
    assert len(registry.executions("external-recipes", "v1")[0]) == 5


def test_malformed_report_is_rejected(tmp_path):
    broken = tmp_path / "broken.ndjson"
    broken.write_text('{"meta": {"protocolVersion": "34.2.1"}}\nnot json\n', encoding="utf-8")
    with pytest.raises(CucumberReportError, match="not valid JSON"):
        CucumberMessagesAdapter().parse(broken, repository_id="probe", tested_commit="0" * 40)


def test_revision_isolation_keeps_outline_and_scenario_records_apart(external_repos):
    registry = PortableRegistry()
    registry.index(
        external_repos["external-recipes"].path, repository_id="external-recipes", revision="v1"
    )
    registry.index(
        external_repos["external-recipes"].path, repository_id="external-recipes", revision="v2"
    )
    v1 = registry.snapshot("external-recipes", "v1")
    v2 = registry.snapshot("external-recipes", "v2")
    assert len(v1.features) == 2 and len(v2.features) == 3
    assert all("ratings" not in feature.path for feature in v1.features)
    outline = next(
        scenario for feature in v1.features for scenario in feature.scenarios if scenario.instances
    )
    assert [instance.example_values["term"] for instance in outline.instances] == ["soup", "toast"]
    assert outline.instances[0].instance_key.endswith("/EX-1")
    assert outline.instances[0].name == "Search by <term> [soup/Hits]"


def test_copy_of_fixture_tree_has_no_cta_markers():
    for name, directory in FIXTURE_DIRS.items():
        tree = directory / "tree"
        markers = []
        for path in tree.rglob("*"):
            if not path.is_file():
                continue
            text = path.read_text("utf-8")
            for marker in (
                "# cta:artifact",
                "requirements/",
                "accepted-links.json",
                "cta:artifact",
            ):
                if marker in text:
                    markers.append((name, str(path.relative_to(directory)), marker))
        assert markers == []


def test_feature_paths_with_spaces_are_indexable_and_queryable(tmp_path):
    repo = _make_repo(
        tmp_path,
        {
            "features/user login.feature": (
                "Feature: Space paths\n  Scenario: A path with spaces\n    Given a step\n"
            )
        },
    )
    registry = PortableRegistry()
    summary = registry.index(repo, repository_id="space-probe", revision="HEAD")
    assert summary.counts.features == 1
    snapshot = registry.snapshot("space-probe", summary.revision)
    scenario = snapshot.features[0].scenarios[0]
    assert scenario.path == "features/user login.feature"
    assert " " in scenario.scenario_key
    assert snapshot.scenario(scenario.scenario_key).name == "A path with spaces"
