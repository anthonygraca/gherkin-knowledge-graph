"""DT-04 store behaviour: configuration errors, content errors, and commit pinning."""

from __future__ import annotations

import shutil
from datetime import UTC, datetime
from pathlib import Path

import fixturectl
import pytest
from conftest import BuiltFixture

from app.domain.errors import BaselineNotFound, FixtureDataInvalid, FixtureDataMissing
from app.domain.oracle import BaselineCommit, BaselinesManifest
from app.ingestion import GitRepository
from app.persistence.fixtures import load_model
from app.persistence.ingested import IngestedStore
from app.settings import ENV_FIXTURE_REPO, load_settings
from app.version import SCHEMA_VERSION


def test_commit_of_resolves_each_baseline(store: IngestedStore, committed_manifest) -> None:
    for name, commit in committed_manifest.tags.items():
        assert store.commit_of(name) == commit


def test_missing_fixture_repo_is_actionable(fixture_settings, tmp_path: Path) -> None:
    manifest = load_model(fixture_settings.baselines_manifest_path, BaselinesManifest)
    store = IngestedStore(
        repository=GitRepository(tmp_path / "absent"),
        manifest=manifest,
        repository_name="banking-demo",
    )
    with pytest.raises(FixtureDataMissing, match="fixturectl.py build"):
        store.get_artifact("REQ-001", baseline="baseline-a")
    with pytest.raises(FixtureDataMissing, match="fixturectl.py build"):
        store.ingest("banking-demo", "baseline-a")
    with pytest.raises(FixtureDataMissing, match="fixturectl.py build"):
        store.ingest("banking-demo", None)


def test_ingestion_unknown_revision_in_an_existing_repo_is_404(store: IngestedStore) -> None:
    with pytest.raises(BaselineNotFound):
        store.ingest("banking-demo", "no-such-rev")


def test_settings_env_override(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv(ENV_FIXTURE_REPO, str(tmp_path))
    assert load_settings().fixture_repo == tmp_path.resolve()


def test_invalid_repository_content_is_a_fixture_error(
    built_fixture: BuiltFixture, tmp_path: Path
) -> None:
    repo = tmp_path / "repo"
    shutil.copytree(built_fixture.repo, repo)
    (repo / "evidence" / "accepted-links.json").write_text("{ not json", encoding="utf-8")
    fixturectl.git(["add", "-A"], cwd=repo)
    fixturectl.git(["commit", "-q", "-m", "break the link file"], cwd=repo)
    commit = fixturectl.git(["rev-parse", "HEAD"], cwd=repo)

    manifest = BaselinesManifest(
        schema_version=SCHEMA_VERSION,
        fixture="banking-demo",
        generated_by="test",
        commits=[
            BaselineCommit(
                id="broken",
                commit=commit,
                date=datetime.now(UTC),
                message="break the link file",
                tags=["broken"],
            )
        ],
        tags={"broken": commit},
    )
    store = IngestedStore(GitRepository(repo), manifest, "banking-demo")
    with pytest.raises(FixtureDataInvalid):
        store.list_artifacts("broken")
