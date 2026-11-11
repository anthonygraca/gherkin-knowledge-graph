"""Shared fixtures for the offline test suite.

Rules for this suite (see AGENTS.md):

* No network, no model download, no GPU, no external service, no Docker.
* Expectations come from hand-labeled oracle files, never from the output of the code under
  test — that would be a tautology, not a test.
* Generated fixture files are treated as inputs; one test (``test_fixture_drift.py``) proves
  they are still what the generator produces.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS_DIR = REPO_ROOT / "tools"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

import fixturectl  # noqa: E402 — tools/ is added to sys.path above

from app.domain.oracle import BaselinesManifest, FixtureSnapshot  # noqa: E402
from app.main import create_app  # noqa: E402
from app.persistence.fixtures import load_model  # noqa: E402
from app.persistence.store import FixtureStore  # noqa: E402
from app.settings import Settings  # noqa: E402

FIXTURE_NAME = "banking-demo"
FIXTURE_DIR = REPO_ROOT / "fixtures" / FIXTURE_NAME
EXPECTED_DIR = FIXTURE_DIR / "expected"
API_DIR = REPO_ROOT / "fixtures" / "api-responses"


@dataclass(frozen=True)
class FixtureTestRun:
    """Outcome of running the fixture repository's own test suite at one tag."""

    exit_code: int
    passed: int
    failed: list[str]
    output: str


@dataclass(frozen=True)
class BuiltFixture:
    """A freshly generated (never committed) fixture repository plus its manifest."""

    repo: Path
    manifest: BaselinesManifest

    def commit(self, commit_id: str) -> str:
        return next(commit.commit for commit in self.manifest.commits if commit.id == commit_id)

    def tag(self, name: str) -> str:
        return self.manifest.tags[name]

    def git(self, args: list[str]) -> str:
        return fixturectl.git(args, cwd=self.repo)

    def blob_sha256(self, revision: str, path: str) -> str:
        return (
            f"sha256:{hashlib.sha256(fixturectl.git_blob(self.repo, revision, path)).hexdigest()}"
        )

    def changed_paths(self, older: str, newer: str) -> list[str]:
        return sorted(self.git(["diff", "--name-only", older, newer]).splitlines())

    def run_fixture_tests(self, tag: str, workdir: Path) -> FixtureTestRun:
        """Check the tag out into a worktree and run the fixture's own pytest suite there."""
        worktree = workdir / f"worktree-{tag}"
        self.git(["worktree", "add", "--detach", str(worktree), tag])
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--tb=no"],
                cwd=worktree,
                capture_output=True,
                text=True,
                check=False,
            )
        finally:
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(worktree)],
                cwd=self.repo,
                capture_output=True,
                check=False,
            )
        failed = [
            line[len("FAILED ") :].split(" - ")[0].strip()
            for line in result.stdout.splitlines()
            if line.startswith("FAILED ")
        ]
        passed_match = re.search(r"(\d+) passed", result.stdout)
        return FixtureTestRun(
            exit_code=result.returncode,
            passed=int(passed_match.group(1)) if passed_match else 0,
            failed=failed,
            output=result.stdout,
        )


@pytest.fixture(scope="session")
def fixture_settings() -> Settings:
    return Settings(repo_root=REPO_ROOT, fixtures_dir=REPO_ROOT / "fixtures")


@pytest.fixture(scope="session")
def committed_manifest() -> BaselinesManifest:
    return load_model(EXPECTED_DIR / "baselines.json", BaselinesManifest)


@pytest.fixture(scope="session")
def snapshot() -> FixtureSnapshot:
    return load_model(API_DIR / "snapshot.json", FixtureSnapshot)


@pytest.fixture(scope="session")
def built_fixture(tmp_path_factory: pytest.TempPathFactory) -> BuiltFixture:
    """Build the fixture history from scratch so the committed SHAs are never assumed."""
    destination = tmp_path_factory.mktemp("fixture-build") / "repo"
    return BuiltFixture(repo=destination, manifest=fixturectl.build_repo(FIXTURE_DIR, destination))


@pytest.fixture(scope="session")
def store(fixture_settings: Settings) -> FixtureStore:
    return FixtureStore.from_settings(fixture_settings)


@pytest.fixture(scope="session")
def client(fixture_settings: Settings) -> TestClient:
    return TestClient(create_app(fixture_settings))
