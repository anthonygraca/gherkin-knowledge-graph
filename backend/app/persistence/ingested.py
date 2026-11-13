"""In-process store over the ingested fixture repository.

The store ingests a revision on first use and caches it by resolved commit. It implements the same
``ArtifactRepository`` port as the M0 mock, so consumers did not change; the precomputed thread
replay is gone and threads are assembled from parsed repository data.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from app.domain.api import ThreadResponse
from app.domain.enums import ArtifactType, ReviewState
from app.domain.errors import (
    ArtifactNotFound,
    BaselineNotFound,
    FixtureDataInvalid,
    FixtureDataMissing,
    InvalidRequest,
    ThreadNotFound,
)
from app.domain.models import Artifact, TraceLink, VerificationEvidence
from app.domain.oracle import BaselinesManifest
from app.ingestion import GitRepository, IngestedRevision, IngestionError, ingest_revision
from app.ingestion.thread import assemble_thread
from app.persistence.fixtures import load_model, require_supported_schema_version
from app.settings import Settings


@dataclass
class IngestedStore:
    """Facts parsed from the configured repository, cached by commit."""

    repository: GitRepository
    manifest: BaselinesManifest
    repository_name: str
    _cache: dict[str, IngestedRevision] = field(default_factory=dict)

    @classmethod
    def from_settings(cls, settings: Settings) -> IngestedStore:
        manifest = load_model(settings.baselines_manifest_path, BaselinesManifest)
        require_supported_schema_version(manifest.schema_version, settings.baselines_manifest_path)
        return cls(
            repository=GitRepository(settings.fixture_repo),
            manifest=manifest,
            repository_name=settings.fixture,
        )

    # --------------------------------------------------- ArtifactRepository port

    def baselines(self) -> list[str]:
        return [tag for commit in self.manifest.commits for tag in commit.tags]

    def resolve_baseline(self, baseline: str | None) -> str:
        if baseline is None:
            return self.baselines()[-1]
        if baseline in self.manifest.tags:
            return baseline
        for name, commit in self.manifest.tags.items():
            if commit == baseline:
                return name
        known = ", ".join(f"{name} ({commit})" for name, commit in self.manifest.tags.items())
        raise BaselineNotFound(f"Unknown baseline '{baseline}'. Known baselines: {known}")

    def commit_of(self, baseline: str) -> str:
        return self.manifest.tags[self.resolve_baseline(baseline)]

    def get_artifact(self, artifact_id: str, *, baseline: str | None = None) -> Artifact:
        canonical, revision = self._revision(baseline)
        artifact = revision.artifact(artifact_id)
        if artifact is None:
            known = ", ".join(item.artifact_id for item in revision.artifacts)
            raise ArtifactNotFound(
                f"No artifact '{artifact_id}' at baseline '{canonical}'. Known artifacts: {known}"
            )
        return artifact

    def list_artifacts(self, baseline: str) -> list[Artifact]:
        return list(self._revision(baseline)[1].artifacts)

    def list_links(
        self, baseline: str, *, review_state: ReviewState | None = None
    ) -> list[TraceLink]:
        revision = self._revision(baseline)[1]
        links = [*revision.accepted_links, *revision.proposed_links]
        if review_state is not None:
            links = [link for link in links if link.review_state is review_state]
        return sorted(links, key=lambda link: link.link_id)

    def list_evidence(self, baseline: str) -> list[VerificationEvidence]:
        return list(self._revision(baseline)[1].evidence)

    def changed_artifacts(self, baseline: str, previous: str) -> list[str]:
        current = {
            artifact.artifact_id: artifact.content_hash
            for artifact in self._revision(baseline)[1].artifacts
        }
        before = {
            artifact.artifact_id: artifact.content_hash
            for artifact in self._revision(previous)[1].artifacts
        }
        return sorted(
            artifact_id
            for artifact_id in current.keys() | before.keys()
            if current.get(artifact_id) != before.get(artifact_id)
        )

    # ------------------------------------------- fixture-facing read helpers

    def baseline_commits(self) -> dict[str, str]:
        """Fixture addition used by ``/health``: baseline name -> resolved commit SHA."""
        return dict(self.manifest.tags)

    def label_of(self, commit: str) -> str:
        return next((name for name, value in self.manifest.tags.items() if value == commit), commit)

    def thread(self, root_id: str, *, baseline: str | None = None) -> ThreadResponse:
        canonical, revision = self._revision(baseline)
        artifact = revision.artifact(root_id)
        if artifact is None:
            raise ArtifactNotFound(f"No artifact '{root_id}' at baseline '{canonical}'.")
        if artifact.artifact_type is not ArtifactType.REQUIREMENT:
            raise ThreadNotFound(
                f"No thread materialized for '{root_id}' at baseline '{canonical}'. "
                f"M1 materializes threads for requirement roots only."
            )
        return assemble_thread(
            root_id=root_id,
            baseline=canonical,
            artifacts=revision.artifacts,
            accepted_links=revision.accepted_links,
            proposed_links=revision.proposed_links,
            evidence=revision.evidence,
        )

    def ingest(self, repository_name: str, revision: str | None) -> IngestedRevision:
        """Ingest one revision of the configured repository (``POST /api/ingestion/run``)."""
        if repository_name != self.repository_name:
            raise InvalidRequest(
                f"Repository {repository_name!r} is not configured; this build serves "
                f"{self.repository_name!r}."
            )
        self._require_repository()
        try:
            commit = self.repository.resolve(revision)
        except IngestionError as exc:
            raise BaselineNotFound(f"Unknown revision {revision!r}: {exc}") from exc
        return self._ingest(commit)

    # ------------------------------------------------------------- internals

    def _revision(self, baseline: str | None) -> tuple[str, IngestedRevision]:
        canonical = self.resolve_baseline(baseline)
        return canonical, self._ingest(self.manifest.tags[canonical])

    def _ingest(self, commit: str) -> IngestedRevision:
        cached = self._cache.get(commit)
        if cached is not None:
            return cached
        self._require_repository()
        try:
            revision = ingest_revision(
                self.repository, commit, repository_name=self.repository_name
            )
        except IngestionError as exc:
            raise FixtureDataInvalid(str(exc)) from exc
        self._cache[commit] = revision
        return revision

    def _require_repository(self) -> None:
        if not self.repository.root.is_dir():
            raise FixtureDataMissing(
                f"Fixture repository '{self.repository.root}' is missing. Run "
                f"'uv run --project backend python tools/fixturectl.py build' from the repository "
                f"root, or set CTA_FIXTURE_REPO."
            )
