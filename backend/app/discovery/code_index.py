"""Artifact-aware code discovery over one immutable Git snapshot (AI-07 / PR 2).

The authoritative CTA store owns artifact identity, revisions, and content hashes. This module
reads that store plus committed blobs and produces either:

* deterministic lexical code hits over the same eligible artifact files, or
* CocoIndex Code hits normalized through the approved AI-06 adapter and mapped back to canonical
  artifacts.

Nothing here writes. A result is a proposal view; accepted links, review state, evidence, and
findings are untouched.
"""

from __future__ import annotations

import hashlib
import re
import subprocess
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from app.discovery.cocoindex import (
    COCOINDEX_PROVIDER,
    SUPPORTED_SERVER_VERSIONS,
    CocoIndexHit,
    CocoIndexSearchClient,
    CocoIndexUnavailableError,
)
from app.domain.enums import ArtifactType, RelationType
from app.domain.errors import InvalidRequest
from app.domain.models import Artifact, TraceCandidate
from app.domain.ports import ArtifactRepository
from app.domain.retrieval import (
    CodeRetrievalRequest,
    CodeRetrievalResponse,
    RetrievalHit,
    RetrievalMethod,
    RetrievalStatus,
    UnresolvedHit,
)
from app.ingestion.repository import GitRepository

QUERY_TEMPLATE = "ai07-code-query-v1"
LEXICAL_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]*")
STOPWORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "are",
        "as",
        "at",
        "be",
        "by",
        "for",
        "from",
        "in",
        "is",
        "it",
        "of",
        "on",
        "or",
        "that",
        "the",
        "to",
        "with",
    }
)


class SnapshotError(Exception):
    """The requested snapshot cannot be bound honestly."""


class CrossBaselineError(SnapshotError):
    """A configured CocoIndex project root is not checked out at the requested commit."""


def _digest(payload: bytes) -> str:
    return f"sha256:{hashlib.sha256(payload).hexdigest()}"


def _tokens(text: str) -> list[str]:
    tokens: list[str] = []
    for match in LEXICAL_TOKEN_RE.findall(text):
        split = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", match).lower().split()
        tokens.extend(part for part in split if part and part not in STOPWORDS)
    return tokens


@dataclass(frozen=True)
class CodeSnapshot:
    repository: str
    commit: str
    root: Path
    index_binding: str
    files: dict[str, bytes]
    artifacts_by_path: dict[str, Artifact]
    skipped: tuple[str, ...] = ()

    @classmethod
    def build(
        cls,
        repository_port: ArtifactRepository,
        git: GitRepository,
        *,
        repository_name: str,
        baseline: str,
    ) -> CodeSnapshot:
        commit = repository_port.commit_of(baseline)
        artifacts = [
            artifact
            for artifact in repository_port.list_artifacts(baseline)
            if artifact.artifact_type in (ArtifactType.SOURCE, ArtifactType.TEST)
        ]
        files: dict[str, bytes] = {}
        by_path: dict[str, Artifact] = {}
        skipped: list[str] = []
        for artifact in artifacts:
            path = artifact.locator.split("#", 1)[0]
            try:
                blob = git.read_blob(commit, path)
                blob.decode("utf-8")
            except (Exception, UnicodeDecodeError):
                skipped.append(path)
                continue
            if _digest(blob) != artifact.content_hash:
                raise SnapshotError(
                    f"{path} at {commit} hashes {_digest(blob)}, but the artifact record says "
                    f"{artifact.content_hash}; refusing to bind mismatched content"
                )
            if artifact.revision != commit:
                raise SnapshotError(
                    f"{artifact.artifact_id} carries revision {artifact.revision}, not {commit}"
                )
            files[path] = blob
            by_path[path] = artifact
        if not files:
            raise SnapshotError(f"no readable source/test artifacts at {baseline}")
        canonical = "\0".join(f"{path}\0{_digest(files[path])}" for path in sorted(files))
        binding = _digest(f"{repository_name}\0{commit}\0{canonical}".encode())
        return cls(
            repository=repository_name,
            commit=commit,
            root=git.root,
            index_binding=f"snapshot:{binding}",
            files=files,
            artifacts_by_path=by_path,
            skipped=tuple(sorted(skipped)),
        )

    def validate_project_root(self, root: Path) -> None:
        """A configured live project must be checked out at this exact commit and content."""
        result = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=False,
        )
        actual = result.stdout.strip()
        if result.returncode != 0 or actual != self.commit:
            raise CrossBaselineError(
                f"configured CocoIndex root {root} is at {actual or 'unknown'}, not the requested "
                f"commit {self.commit}; refusing cross-baseline retrieval"
            )
        dirty = subprocess.run(
            ["git", "-C", str(root), "status", "--porcelain", "--untracked-files=no"],
            capture_output=True,
            text=True,
            check=False,
        )
        if dirty.returncode != 0 or dirty.stdout.strip():
            raise CrossBaselineError(
                f"configured CocoIndex root {root} has tracked working-tree changes; refusing to "
                "attribute them to the requested commit"
            )
        for path, committed in self.files.items():
            target = root / path
            if not target.is_file() or _digest(target.read_bytes()) != _digest(committed):
                raise CrossBaselineError(
                    f"configured CocoIndex root {root} has different content for {path} than "
                    f"{self.commit}; refusing cross-baseline retrieval"
                )


@dataclass(frozen=True)
class _Mapped:
    artifact: Artifact
    hit: CocoIndexHit
    relation_type: RelationType


def map_hits(
    snapshot: CodeSnapshot,
    hits: Sequence[CocoIndexHit],
    *,
    relation_types: set[RelationType] | None,
) -> tuple[list[_Mapped], list[UnresolvedHit]]:
    mapped: dict[str, _Mapped] = {}
    unresolved: list[UnresolvedHit] = []
    for hit in hits:
        artifact = snapshot.artifacts_by_path.get(hit.path)
        if artifact is None:
            unresolved.append(
                UnresolvedHit(
                    path=hit.path,
                    start_line=hit.start_line,
                    end_line=hit.end_line,
                    raw_score=hit.score,
                    reason="path is not a source/test artifact at this revision",
                )
            )
            continue
        blob = snapshot.files.get(hit.path)
        if blob is None or _digest(blob) != artifact.content_hash:
            unresolved.append(
                UnresolvedHit(
                    path=hit.path,
                    start_line=hit.start_line,
                    end_line=hit.end_line,
                    raw_score=hit.score,
                    reason="hit content does not match the authoritative artifact hash",
                )
            )
            continue
        text = blob.decode("utf-8")
        # Split on LF only, preserving every other byte (CR, U+2028) and the delimiters of
        # non-final lines. The only normalization applied is a single trailing LF.
        parts = text.split("\n")
        if text.endswith("\n"):
            raw_lines = [part + "\n" for part in parts[:-1]]
        else:
            raw_lines = [part + "\n" for part in parts[:-1]] + [parts[-1]]
        line_count = len(raw_lines)
        if hit.end_line > line_count or hit.start_line < 1:
            unresolved.append(
                UnresolvedHit(
                    path=hit.path,
                    start_line=hit.start_line,
                    end_line=hit.end_line,
                    raw_score=hit.score,
                    reason=f"line range exceeds the {line_count} lines at this revision",
                )
            )
            continue
        committed_chunk = "".join(raw_lines[hit.start_line - 1 : hit.end_line])

        def strip_one_lf(value: str) -> str:
            return value[:-1] if value.endswith("\n") else value

        if strip_one_lf(hit.content) != strip_one_lf(committed_chunk):
            unresolved.append(
                UnresolvedHit(
                    path=hit.path,
                    start_line=hit.start_line,
                    end_line=hit.end_line,
                    raw_score=hit.score,
                    reason="hit content does not match the committed lines at this revision",
                )
            )
            continue
        relation = (
            RelationType.IMPLEMENTED_BY
            if artifact.artifact_type is ArtifactType.SOURCE
            else RelationType.EXERCISED_BY
        )
        if relation_types is not None and relation not in relation_types:
            continue
        current = mapped.get(artifact.artifact_id)
        if current is None or hit.score > current.hit.score:
            mapped[artifact.artifact_id] = _Mapped(
                artifact=artifact, hit=hit, relation_type=relation
            )
    return sorted(
        mapped.values(), key=lambda item: (-item.hit.score, item.artifact.artifact_id)
    ), unresolved


@dataclass(frozen=True)
class LexicalResult:
    hits: list[RetrievalHit]
    latency_ms: float


class LexicalCodeIndex:
    """Deterministic token-overlap baseline over the same snapshot and eligible files."""

    def __init__(self, snapshot: CodeSnapshot) -> None:
        self._snapshot = snapshot
        self._documents = {
            path: _tokens(blob.decode("utf-8")) for path, blob in snapshot.files.items()
        }

    def search(
        self, query: str, *, top_k: int, relation_types: set[RelationType] | None
    ) -> LexicalResult:
        started = time.monotonic()
        query_tokens = set(_tokens(query))
        if not query_tokens:
            return LexicalResult(hits=[], latency_ms=0.0)
        scored: list[tuple[float, str]] = []
        for path, tokens in self._documents.items():
            overlap = query_tokens.intersection(tokens)
            if not overlap:
                continue
            scored.append((len(overlap) / len(query_tokens), path))
        scored.sort(key=lambda item: (-item[0], item[1]))
        hits: list[RetrievalHit] = []
        for score, path in scored:
            if len(hits) >= top_k:
                break
            artifact = self._snapshot.artifacts_by_path[path]
            relation = (
                RelationType.IMPLEMENTED_BY
                if artifact.artifact_type is ArtifactType.SOURCE
                else RelationType.EXERCISED_BY
            )
            if relation_types is not None and relation not in relation_types:
                continue
            lines = self._best_window(path, query_tokens)
            hits.append(
                RetrievalHit(
                    rank=len(hits) + 1,
                    score=min(1.0, max(0.0, score)),
                    raw_score=score,
                    artifact_id=artifact.artifact_id,
                    relation_type=relation,
                    path=path,
                    start_line=lines[0],
                    end_line=lines[1],
                    revision=artifact.revision,
                    content_hash=artifact.content_hash,
                    method=RetrievalMethod.LEXICAL,
                )
            )
        return LexicalResult(hits=hits, latency_ms=(time.monotonic() - started) * 1000.0)

    def _best_window(self, path: str, query_tokens: set[str]) -> tuple[int, int]:
        text_lines = self._snapshot.files[path].decode("utf-8").splitlines()
        best_line, best_score = 1, -1
        for number, line in enumerate(text_lines, start=1):
            score = len(query_tokens.intersection(_tokens(line)))
            if score > best_score:
                best_line, best_score = number, score
        return max(1, best_line - 2), min(len(text_lines), best_line + 2)


def build_query(artifact: Artifact) -> str:
    """Stable query template over authoritative artifact text."""
    return f"{QUERY_TEMPLATE}: {artifact.title}"


@dataclass
class CodeDiscovery:
    """CocoIndex/lexical discovery service. Read-only; proposals only."""

    repository: ArtifactRepository
    git: GitRepository
    repository_name: str
    client: CocoIndexSearchClient | None = None
    model_version: str = "not-configured"
    require_live_root: bool = False
    clock: Callable[[], float] = time.monotonic
    _snapshots: dict[str, CodeSnapshot] = field(default_factory=dict)

    # ------------------------------------------------------------------ snapshots

    def snapshot(self, baseline: str) -> CodeSnapshot:
        canonical = self.repository.resolve_baseline(baseline)
        cached = self._snapshots.get(canonical)
        if cached is not None:
            return cached
        snapshot = CodeSnapshot.build(
            self.repository, self.git, repository_name=self.repository_name, baseline=canonical
        )
        self._snapshots[canonical] = snapshot
        return snapshot

    # ------------------------------------------------------------------ retrieval

    def retrieve(self, request: CodeRetrievalRequest) -> CodeRetrievalResponse:
        started = self.clock()
        baseline = self.repository.resolve_baseline(request.baseline)
        artifact = self.repository.get_artifact(request.artifact_id, baseline=baseline)
        if artifact.artifact_type is not ArtifactType.SCENARIO:
            raise InvalidRequest(
                "code discovery requires a scenario artifact; requirements have no direct code "
                "relation and a code hit is not scenario verification"
            )
        snapshot = self.snapshot(baseline)
        lexical = LexicalCodeIndex(snapshot)
        allowed = None if request.relation_types is None else set(request.relation_types)
        method = request.method or (
            RetrievalMethod.COCOINDEX if self.client is not None else RetrievalMethod.LEXICAL
        )
        limitations = [
            "CocoIndex Code indexes code/test chunks, not Gherkin scenarios.",
            "A candidate is a proposal; it is not an accepted link or verification evidence.",
        ]
        if snapshot.skipped:
            limitations.append(f"unreadable artifacts skipped: {', '.join(snapshot.skipped)}")

        if method is RetrievalMethod.LEXICAL:
            result = lexical.search(
                build_query(artifact), top_k=request.top_k, relation_types=allowed
            )
            return CodeRetrievalResponse(
                schema_version=self._schema_version(),
                artifact_id=artifact.artifact_id,
                baseline=baseline,
                revision=snapshot.commit,
                status=RetrievalStatus.OK,
                method=RetrievalMethod.LEXICAL,
                provider="lexical",
                model_version="deterministic-token-overlap-v1",
                index_binding=snapshot.index_binding,
                hits=result.hits,
                latency_ms=result.latency_ms,
                limitations=limitations,
            )

        if self.client is None:
            return CodeRetrievalResponse(
                schema_version=self._schema_version(),
                artifact_id=artifact.artifact_id,
                baseline=baseline,
                revision=snapshot.commit,
                status=RetrievalStatus.NOT_AVAILABLE,
                method=RetrievalMethod.COCOINDEX,
                provider="cocoindex",
                model_version=self.model_version,
                index_binding=snapshot.index_binding,
                latency_ms=(self.clock() - started) * 1_000.0,
                limitations=[
                    "CocoIndex is not configured; set CTA_CCC_PROJECT_ROOT and "
                    "CTA_CCC_LIVE_OPT_IN (with isolated COCOINDEX_CODE_DIR/RUNTIME_DIR) or request "
                    "the lexical method.",
                    *limitations,
                ],
            )
        if self.require_live_root:
            project_root = getattr(self.client.transport, "project_root", None)
            if project_root is None:
                raise SnapshotError("the live CocoIndex client exposes no project root")
            snapshot.validate_project_root(Path(project_root))
        search = self.client.search(
            build_query(artifact),
            limit=min(50, max(request.top_k * 3, request.top_k)),
            languages=("python",),
            paths=tuple(sorted(snapshot.artifacts_by_path)),
            refresh_index=False,
        )
        mapped, unresolved = map_hits(snapshot, search.hits, relation_types=allowed)
        hits = [
            RetrievalHit(
                rank=rank,
                score=min(1.0, max(0.0, item.hit.score)),
                raw_score=item.hit.score,
                artifact_id=item.artifact.artifact_id,
                relation_type=item.relation_type,
                path=item.hit.path,
                start_line=item.hit.start_line,
                end_line=item.hit.end_line,
                revision=item.artifact.revision,
                content_hash=item.artifact.content_hash,
                method=RetrievalMethod.COCOINDEX,
            )
            for rank, item in enumerate(mapped[: request.top_k], start=1)
        ]
        return CodeRetrievalResponse(
            schema_version=self._schema_version(),
            artifact_id=artifact.artifact_id,
            baseline=baseline,
            revision=snapshot.commit,
            status=RetrievalStatus.OK,
            method=RetrievalMethod.COCOINDEX,
            provider=COCOINDEX_PROVIDER,
            model_version=self.model_version,
            index_binding=snapshot.index_binding,
            hits=hits,
            unresolved=unresolved if request.include_unresolved else [],
            latency_ms=search.latency_ms,
            limitations=limitations,
        )

    @staticmethod
    def _schema_version() -> str:
        from app.version import SCHEMA_VERSION

        return SCHEMA_VERSION


class CocoIndexCandidateDiscovery:
    """`CandidateDiscovery` adapter over :class:`CodeDiscovery` (proposals only)."""

    provider_name = "cocoindex"

    def __init__(
        self,
        discovery: CodeDiscovery,
        *,
        baseline: str | None = None,
        model_version: str | None = None,
    ) -> None:
        self._discovery = discovery
        self._baseline = baseline
        self.model_version = model_version or discovery.model_version
        self.index_revision = discovery.snapshot(
            self._discovery.repository.resolve_baseline(baseline)
        ).index_binding

    def binding_for(self, baseline: str | None = None) -> str:
        """Per-request snapshot binding, including when no candidates remain."""
        selected = baseline if baseline is not None else self._baseline
        return self._discovery.snapshot(
            self._discovery.repository.resolve_baseline(selected)
        ).index_binding

    def discover(
        self,
        artifact_id: str,
        *,
        top_k: int = 5,
        relation_types: Sequence[RelationType] | None = None,
        baseline: str | None = None,
    ) -> list[TraceCandidate]:
        if top_k < 1:
            raise ValueError("top_k must be >= 1")
        selected = baseline if baseline is not None else self._baseline
        response = self._discovery.retrieve(
            CodeRetrievalRequest(
                artifact_id=artifact_id,
                baseline=selected,
                top_k=top_k,
                method=RetrievalMethod.COCOINDEX,
                relation_types=list(relation_types) if relation_types else None,
            )
        )
        if response.status is RetrievalStatus.NOT_AVAILABLE:
            raise CocoIndexUnavailableError(
                "CocoIndex discovery is not configured; the lexical method remains available "
                "through POST /api/retrieval/code"
            )
        return [
            TraceCandidate(
                source_id=artifact_id,
                target_id=hit.artifact_id,
                proposed_relation_type=hit.relation_type,
                rank=hit.rank,
                score=hit.score,
                discovery_provider=self.provider_name,
                model_version=self.model_version,
                index_revision=response.index_binding,
                rationale=(
                    f"{hit.method.value} {hit.path}:{hit.start_line}-{hit.end_line} "
                    f"raw_score={hit.raw_score:.6f}; snapshot={response.index_binding}; "
                    f"template={QUERY_TEMPLATE}"
                ),
            )
            for hit in response.hits
        ]


def configured_model_version(settings=None) -> str:
    """Report the adapter version and the configured embedding model, or ``unavailable``.

    The model is read from the isolated CocoIndex global settings or the project settings; CTA does
    not assume the PR 1 model when a different project is configured.
    """
    import os

    import yaml

    versions = ", ".join(sorted(SUPPORTED_SERVER_VERSIONS))
    candidates: list[Path] = []
    state = os.environ.get("COCOINDEX_CODE_DIR")
    if state:
        candidates.append(Path(state) / "global_settings.yml")
    project_root = getattr(settings, "ccc_project_root", None)
    if project_root is not None:
        candidates.append(Path(project_root) / ".cocoindex_code" / "settings.yml")
    model: str | None = None
    for candidate in candidates:
        if not candidate.is_file():
            continue
        try:
            document = yaml.safe_load(candidate.read_text(encoding="utf-8")) or {}
        except yaml.YAMLError:
            continue
        embedding = document.get("embedding")
        if not isinstance(embedding, dict):
            continue
        configured = embedding.get("model")
        if isinstance(configured, str) and configured.strip():
            model = configured.strip()
            break
    return f"cocoindex-code {versions}; embedding={model or 'unavailable'}"


def live_client(settings) -> CocoIndexSearchClient:
    """Build the approved live transport only for an explicitly configured/opted-in project."""
    from app.discovery.cocoindex_mcp import StdioMcpTransport

    if not settings.cocoindex_enabled:
        raise InvalidRequest(
            "CocoIndex live retrieval requires CTA_CCC_PROJECT_ROOT and CTA_CCC_LIVE_OPT_IN"
        )
    transport = StdioMcpTransport(
        executable=settings.ccc_executable,
        project_root=settings.ccc_project_root,
        environment={},
    )
    return CocoIndexSearchClient(transport)
