"""Runtime settings.

Offline by default: M0 configures no remote endpoint of any kind. The only tunables are
filesystem locations and the default discovery provider name, all overridable by
environment variable for tests and packaging.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_FIXTURE = "banking-demo"

ENV_REPO_ROOT = "CTA_REPO_ROOT"
ENV_FIXTURES_DIR = "CTA_FIXTURES_DIR"
ENV_FIXTURE = "CTA_FIXTURE"
ENV_DISCOVERY_PROVIDER = "CTA_DISCOVERY_PROVIDER"


def default_repo_root() -> Path:
    """Repository root assuming the documented monorepo layout (backend/app/settings.py)."""
    return Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Settings:
    repo_root: Path
    fixtures_dir: Path
    fixture: str = DEFAULT_FIXTURE
    discovery_provider: str = "fake"

    @property
    def fixture_dir(self) -> Path:
        return self.fixtures_dir / self.fixture

    @property
    def expected_dir(self) -> Path:
        return self.fixture_dir / "expected"

    @property
    def candidate_index_path(self) -> Path:
        return self.expected_dir / "candidate-links.json"

    @property
    def baselines_manifest_path(self) -> Path:
        return self.expected_dir / "baselines.json"

    @property
    def api_responses_dir(self) -> Path:
        return self.fixtures_dir / "api-responses"

    @property
    def snapshot_path(self) -> Path:
        return self.api_responses_dir / "snapshot.json"


def load_settings() -> Settings:
    repo_root = Path(os.environ.get(ENV_REPO_ROOT, default_repo_root())).resolve()
    fixtures_dir = Path(os.environ.get(ENV_FIXTURES_DIR, repo_root / "fixtures")).resolve()
    return Settings(
        repo_root=repo_root,
        fixtures_dir=fixtures_dir,
        fixture=os.environ.get(ENV_FIXTURE, DEFAULT_FIXTURE),
        discovery_provider=os.environ.get(ENV_DISCOVERY_PROVIDER, "fake"),
    )
