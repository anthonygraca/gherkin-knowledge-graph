"""Retrieval snapshot planning, publication, and candidate combination (AI-03)."""

from __future__ import annotations

import json
import os
import tempfile
import threading
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

from app.domain.enums import ArtifactType
from app.domain.errors import (
    InvalidRequest,
    MixedIndexContext,
    RetrievalSnapshotNotFound,
    RetrievalUnavailable,
)
from app.domain.models import TraceCandidate
from app.domain.ports import ArtifactRepository, CandidateDiscovery
from app.domain.retrieval_lifecycle import (
    BatchProvenance,
    CombinedCandidatesResponse,
    CombineRequest,
    ContentChangePlan,
    IndexRefreshObservation,
    ManifestListResponse,
    RetrievalArtifact,
    RetrievalConfig,
    RetrievalManifest,
    SnapshotBoundBatch,
    config_digest,
    corpus_cache_key,
    snapshot_binding,
)
from app.ingestion.repository import GitRepository
from app.version import SCHEMA_VERSION

DEFAULT_CONFIG = RetrievalConfig(
    provider="cocoindex",
    model_id="cocoindex-configured",
    model_version="not_available",
    weights_digest="not_available",
    runtime="cocoindex",
    formatting_version="ai03-corpus-snapshot-v1",
)


class IndexRefreshAdapter(Protocol):
    """Optional backend hook. CTA publishes the manifest; the backend may report observations."""

    def refresh(
        self,
        *,
        baseline: str,
        commit: str,
        plan: ContentChangePlan,
        config: RetrievalConfig,
    ) -> IndexRefreshObservation: ...


class RetrievalLifecycle:
    """Content-addressed manifests over source/test artifacts, published atomically."""

    def __init__(
        self,
        repository: ArtifactRepository,
        git: GitRepository,
        store_dir: Path,
        *,
        repository_name: str,
        default_config: RetrievalConfig = DEFAULT_CONFIG,
        clock: Callable[[], float] | None = None,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._repository = repository
        self._git = git
        self._store_dir = store_dir
        self._repository_name = repository_name
        self._default_config = default_config
        self._clock = clock or (lambda: __import__("time").perf_counter())
        self._now = now or (lambda: datetime.now(UTC))
        self._lock = threading.RLock()
        self._snapshots = store_dir / "snapshots"
        self._baselines = store_dir / "baselines"
        self._snapshots.mkdir(parents=True, exist_ok=True)
        self._baselines.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------------------- planning

    def plan(self, baseline: str, previous_baseline: str | None = None) -> ContentChangePlan:
        canonical, commit = self._resolve(baseline)
        current = self._eligibles(canonical)
        if previous_baseline is None:
            previous_commit = None
            previous: dict[str, RetrievalArtifact] = {}
        else:
            previous_canonical, previous_commit = self._resolve(previous_baseline)
            previous = {
                artifact.artifact_id: artifact for artifact in self._eligibles(previous_canonical)
            }
        current_map = {artifact.artifact_id: artifact for artifact in current}
        changed = sorted(
            artifact_id
            for artifact_id in current_map.keys() & previous.keys()
            if current_map[artifact_id].content_hash != previous[artifact_id].content_hash
        )
        added = sorted(current_map.keys() - previous.keys())
        removed = sorted(previous.keys() - current_map.keys())
        unchanged = sorted(
            artifact_id
            for artifact_id in current_map.keys() & previous.keys()
            if current_map[artifact_id].content_hash == previous[artifact_id].content_hash
        )
        return ContentChangePlan(
            repository=self._repository_name,
            baseline=canonical,
            previous_baseline=previous_baseline,
            commit=commit,
            previous_commit=previous_commit,
            changed=changed,
            added=added,
            removed=removed,
            unchanged=unchanged,
            changed_artifacts=[current_map[key] for key in changed],
            unchanged_artifacts=[current_map[key] for key in unchanged],
        )

    # ------------------------------------------------------------- publication

    def refresh(
        self,
        baseline: str,
        *,
        previous_baseline: str | None = None,
        config: RetrievalConfig | None = None,
        adapter: IndexRefreshAdapter | None = None,
    ) -> RetrievalManifest:
        with self._lock:
            # The timed phase covers baseline resolution, configuration/corpus/key construction,
            # previous-manifest lookup, planning, and adapter execution. Atomic publication writes
            # are excluded. An exact-binding cache hit returns the original publication
            # observation instead of re-measuring it.
            started = self._clock()
            canonical, commit = self._resolve(baseline)
            selected = config or self._default_config
            digest = config_digest(selected)
            artifacts = self._eligibles(canonical)
            cache_key = corpus_cache_key(
                repository=self._repository_name,
                config_digest_value=digest,
                artifacts=artifacts,
            )
            binding = snapshot_binding(
                repository=self._repository_name,
                commit=commit,
                cache_key=cache_key,
                config_digest_value=digest,
            )
            existing = self._read_snapshot(binding)
            if existing is not None:
                # Exact-binding cache hit: return the original publication observation, including
                # its historical elapsed_ms and counts. Do not pretend this request re-measured it.
                return existing
            plan = self.plan(canonical, previous_baseline)
            previous = (
                self.manifest_for(previous_baseline) if previous_baseline is not None else None
            )
            observation: IndexRefreshObservation | None = None
            reused = (
                previous is not None
                and previous.config_digest == digest
                and previous.corpus_cache_key == cache_key
                and not plan.changed
                and not plan.added
                and not plan.removed
            )
            if not reused and adapter is not None:
                try:
                    observation = adapter.refresh(
                        baseline=canonical,
                        commit=commit,
                        plan=plan,
                        config=selected,
                    )
                except RetrievalUnavailable:
                    raise
                except Exception as exc:  # noqa: BLE001 - backend failures are typed
                    raise RetrievalUnavailable(
                        f"Retrieval refresh adapter {type(adapter).__name__} failed for "
                        f"{canonical} ({commit[:12]}): {exc}. No snapshot was published."
                    ) from exc
            elapsed_ms = max(0.0, (self._clock() - started) * 1_000.0)
            items_embedded = observation.items_embedded if observation is not None else None
            availability = (
                observation.items_embedded_availability
                if observation is not None and observation.items_embedded is not None
                else "not_available"
            )
            manifest = RetrievalManifest(
                schema_version=SCHEMA_VERSION,
                repository=self._repository_name,
                baseline=canonical,
                commit=commit,
                config=selected,
                config_digest=digest,
                corpus_cache_key=cache_key,
                snapshot_binding=binding,
                artifacts=artifacts,
                changed=plan.changed,
                added=plan.added,
                removed=plan.removed,
                unchanged=plan.unchanged,
                changed_count=len(plan.changed),
                added_count=len(plan.added),
                removed_count=len(plan.removed),
                unchanged_count=len(plan.unchanged),
                items_embedded=items_embedded,
                items_embedded_availability=availability,
                elapsed_ms=round(elapsed_ms, 3),
                previous_snapshot_binding=(
                    previous.snapshot_binding if previous is not None else None
                ),
                reused=reused,
                published_at=self._now(),
                backend_observation=observation,
            )
            self._publish(manifest)
            return manifest

    # ----------------------------------------------------------------- reads

    def manifest_for(self, baseline: str) -> RetrievalManifest:
        canonical = self._repository.resolve_baseline(baseline)
        pointer = self._baselines / f"{_safe_name(canonical)}.json"
        if not pointer.is_file():
            raise RetrievalSnapshotNotFound(
                f"No retrieval snapshot is published for baseline {canonical!r}."
            )
        try:
            payload = json.loads(pointer.read_text("utf-8"))
            binding = payload["snapshot_binding"]
        except Exception as exc:  # noqa: BLE001 - a corrupt pointer is not a usable snapshot
            raise RetrievalSnapshotNotFound(
                f"Retrieval snapshot pointer for {canonical!r} is corrupt."
            ) from exc
        manifest = self._read_snapshot_file(
            self._snapshots / f"{_safe_name(binding)}.json",
            expected_binding=binding,
            expected_baseline=canonical,
        )
        if manifest is None:
            raise RetrievalSnapshotNotFound(
                f"Retrieval snapshot {binding} referenced by {canonical} is missing."
            )
        return manifest

    def get(self, snapshot_binding_value: str) -> RetrievalManifest:
        manifest = self._read_snapshot(snapshot_binding_value)
        if manifest is None:
            raise RetrievalSnapshotNotFound(
                f"No retrieval snapshot {snapshot_binding_value!r} is published."
            )
        return manifest

    def manifests(self) -> ManifestListResponse:
        manifests = [
            self._read_snapshot_file(path, expected_binding=_binding_from_filename(path))
            for path in sorted(self._snapshots.glob("*.json"))
        ]
        published = [manifest for manifest in manifests if manifest is not None]
        published.sort(key=lambda item: (item.published_at, item.snapshot_binding))
        return ManifestListResponse(schema_version=SCHEMA_VERSION, manifests=published)

    # -------------------------------------------------------------- combine

    def bind(
        self,
        manifest: RetrievalManifest,
        provider: CandidateDiscovery,
        artifact_id: str,
        *,
        top_k: int = 5,
    ) -> SnapshotBoundBatch:
        """Adapt one provider response to the manifest's CTA snapshot binding.

        The provider's own index identity is retained at the batch level. Candidates carry the
        CTA binding because that is the only identity the combination service may mix; the
        adaptation is explicit, validated, and never a silent rewrite of provider provenance.
        """
        if provider.provider_name != manifest.config.provider:
            raise InvalidRequest(
                f"Provider {provider.provider_name!r} does not match the snapshot "
                f"configuration provider {manifest.config.provider!r}."
            )
        if manifest.config.model_version not in ("not_available", provider.model_version):
            raise RetrievalUnavailable(
                f"Provider model {provider.model_version!r} does not match the snapshot "
                f"configuration model {manifest.config.model_version!r}."
            )
        provider_candidates = provider.discover(
            artifact_id,
            top_k=top_k,
            baseline=manifest.baseline,
        )
        provider_bindings = {candidate.index_revision for candidate in provider_candidates}
        if len(provider_bindings) > 1:
            raise MixedIndexContext(
                "Provider returned candidates from more than one index revision: "
                + ", ".join(sorted(provider_bindings))
            )
        if provider_bindings and provider.index_revision not in provider_bindings:
            raise MixedIndexContext(
                f"Provider identity {provider.index_revision!r} does not match its candidate "
                "index revisions."
            )
        bound = [
            candidate.model_copy(update={"index_revision": manifest.snapshot_binding})
            for candidate in provider_candidates
        ]
        return SnapshotBoundBatch(
            snapshot_binding=manifest.snapshot_binding,
            provider=provider.provider_name,
            provider_index_revision=provider.index_revision,
            model_version=provider.model_version,
            candidates=bound,
        )

    def combine(self, request: CombineRequest) -> CombinedCandidatesResponse:
        candidates: list[TraceCandidate] = []
        provenance: list[BatchProvenance] = []
        for batch in request.batches:
            if batch.snapshot_binding != request.snapshot_binding:
                raise MixedIndexContext(
                    f"Batch is bound to {batch.snapshot_binding!r}, not "
                    f"{request.snapshot_binding!r}; refusing to combine mixed index contexts."
                )
            for candidate in batch.candidates:
                if candidate.index_revision != request.snapshot_binding:
                    raise MixedIndexContext(
                        f"Candidate {candidate.source_id}->{candidate.target_id} is bound to "
                        f"{candidate.index_revision!r}, not {request.snapshot_binding!r}; "
                        "refusing to combine mixed index contexts."
                    )
                candidates.append(candidate)
            provenance.append(
                BatchProvenance(
                    snapshot_binding=batch.snapshot_binding,
                    provider=batch.provider,
                    provider_index_revision=batch.provider_index_revision,
                    model_version=batch.model_version,
                )
            )
        ordered = sorted(
            candidates,
            key=lambda candidate: (-candidate.score, candidate.target_id, candidate.source_id),
        )
        ranked = [
            candidate.model_copy(update={"rank": rank})
            for rank, candidate in enumerate(ordered, start=1)
        ]
        return CombinedCandidatesResponse(
            schema_version=SCHEMA_VERSION,
            snapshot_binding=request.snapshot_binding,
            provenance=provenance,
            candidates=ranked,
        )

    # ------------------------------------------------------------- internals

    def _resolve(self, baseline: str) -> tuple[str, str]:
        canonical = self._repository.resolve_baseline(baseline)
        return canonical, self._repository.commit_of(canonical)

    def _eligibles(self, baseline: str) -> list[RetrievalArtifact]:
        artifacts = [
            artifact
            for artifact in self._repository.list_artifacts(baseline)
            if artifact.artifact_type in (ArtifactType.SOURCE, ArtifactType.TEST)
        ]
        return [
            RetrievalArtifact(
                artifact_id=artifact.artifact_id,
                artifact_type=artifact.artifact_type.value,
                locator=artifact.locator,
                revision=artifact.revision,
                content_hash=artifact.content_hash,
            )
            for artifact in sorted(artifacts, key=lambda item: item.artifact_id)
        ]

    def _publish(self, manifest: RetrievalManifest) -> None:
        snapshot_path = self._snapshots / f"{_safe_name(manifest.snapshot_binding)}.json"
        snapshot_existed = snapshot_path.exists()
        if not snapshot_existed:
            _atomic_write(snapshot_path, manifest.model_dump_json(indent=2) + "\n")
        pointer = self._baselines / f"{_safe_name(manifest.baseline)}.json"
        try:
            _atomic_write(
                pointer,
                json.dumps(
                    {
                        "snapshot_binding": manifest.snapshot_binding,
                        "config_digest": manifest.config_digest,
                    },
                    indent=2,
                )
                + "\n",
            )
        except Exception as exc:  # noqa: BLE001 - publication failure is a typed storage error
            if not snapshot_existed:
                try:
                    snapshot_path.unlink()
                except OSError as cleanup_exc:
                    raise RetrievalUnavailable(
                        "Retrieval publication failed and the uncommitted snapshot could not be "
                        f"rolled back; the publication state is indeterminate: {cleanup_exc}"
                    ) from cleanup_exc
            raise RetrievalUnavailable(
                f"Retrieval publication failed for {manifest.baseline!r} and was rolled back: {exc}"
            ) from exc

    def _read_snapshot(self, binding: str) -> RetrievalManifest | None:
        path = self._snapshots / f"{_safe_name(binding)}.json"
        return self._read_snapshot_file(path, expected_binding=binding) if path.is_file() else None

    def _read_snapshot_file(
        self,
        path: Path,
        *,
        expected_binding: str | None = None,
        expected_baseline: str | None = None,
    ) -> RetrievalManifest | None:
        if not path.is_file():
            return None
        try:
            manifest = RetrievalManifest.model_validate_json(path.read_text("utf-8"))
        except Exception as exc:  # noqa: BLE001 - a corrupt cache entry is not a usable snapshot
            raise RetrievalSnapshotNotFound(
                f"Retrieval snapshot {path.name} is corrupt and will not be served: {exc}"
            ) from exc
        return self._verify_manifest(
            manifest,
            expected_binding=expected_binding,
            expected_baseline=expected_baseline,
        )

    def _verify_manifest(
        self,
        manifest: RetrievalManifest,
        *,
        expected_binding: str | None = None,
        expected_baseline: str | None = None,
    ) -> RetrievalManifest:
        expected_config = config_digest(manifest.config)
        if manifest.config_digest != expected_config:
            raise RetrievalSnapshotNotFound(
                f"Retrieval snapshot {manifest.snapshot_binding} has a configuration digest "
                "that does not match its stored configuration."
            )
        expected_cache = corpus_cache_key(
            repository=self._repository_name,
            config_digest_value=expected_config,
            artifacts=manifest.artifacts,
        )
        if manifest.corpus_cache_key != expected_cache:
            raise RetrievalSnapshotNotFound(
                f"Retrieval snapshot {manifest.snapshot_binding} has a corpus cache key that "
                "does not match its stored artifacts and configuration."
            )
        expected_identity = snapshot_binding(
            repository=self._repository_name,
            commit=manifest.commit,
            cache_key=expected_cache,
            config_digest_value=expected_config,
        )
        if manifest.snapshot_binding != expected_identity:
            raise RetrievalSnapshotNotFound(
                f"Retrieval snapshot {manifest.snapshot_binding} has a binding that does not "
                "match its stored commit, artifacts, and configuration."
            )
        if expected_binding is not None and manifest.snapshot_binding != expected_binding:
            raise RetrievalSnapshotNotFound(
                f"Retrieval snapshot file does not contain the requested binding "
                f"{expected_binding!r}."
            )
        if expected_baseline is not None and manifest.baseline != expected_baseline:
            raise RetrievalSnapshotNotFound(
                f"Retrieval snapshot {manifest.snapshot_binding} belongs to baseline "
                f"{manifest.baseline!r}, not {expected_baseline!r}."
            )
        return manifest


def _safe_name(value: str) -> str:
    return value.replace(":", "-").replace("/", "-")


def _binding_from_filename(path: Path) -> str | None:
    prefix = "snapshot-sha256-"
    stem = path.stem
    if not stem.startswith(prefix):
        return None
    return f"snapshot:sha256:{stem[len(prefix) :]}"


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


__all__ = ["DEFAULT_CONFIG", "IndexRefreshAdapter", "RetrievalLifecycle"]
