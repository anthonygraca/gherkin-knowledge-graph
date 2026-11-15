"""Same-machine EmbeddingGemma 2 discovery provider (AI-02).

The default CTA path never imports this module's optional runtime. When local inference is
explicitly enabled, the provider loads a permissively licensed ONNX text model from a local
directory, embeds the eligible corpus in memory, and returns ordinary
:class:`~app.domain.models.TraceCandidate` proposals. It has no writer: no accepted link,
review state, evidence, or finding is created.

No request leaves the machine. A configured endpoint must be loopback; any other endpoint is
refused before a connection is attempted. Missing weights and malformed model output are typed
retrieval failures, never empty successes.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import threading
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from app.domain.enums import RELATION_DIRECTION, ArtifactType, RelationType
from app.domain.errors import InvalidRequest, RetrievalUnavailable
from app.domain.models import Artifact, TraceCandidate
from app.domain.ports import ArtifactRepository
from app.ingestion.repository import GitRepository

PROVIDER_NAME = "local-embeddinggemma"
MODEL_ID = "embeddinggemma-2-text-270m-q8_0"
WEIGHTS_FILES = ("onnx/model_quantized.onnx", "onnx/model_quantized.onnx_data")
TOKENIZER_FILE = "tokenizer.json"
DIMENSION = 768
MAX_TOKENS = 512
QUERY_TEMPLATE_CODE = "task: code retrieval | query: "
QUERY_TEMPLATE_SEARCH = "task: search result | query: "
DOCUMENT_TEMPLATE = "title: {title} | text: {content}"
FORMATTING_VERSION = "ai02-code-query-v1/document-title-text-v1"

_LOOPBACK_HOSTS = {"127.0.0.1", "localhost", "::1"}
_ARTIFACT_TAG = re.compile(r"@(SCN-\d{3})")


class EmbeddingRuntime(Protocol):
    """Minimal local runtime boundary; deterministic fakes implement the same methods."""

    model_id: str
    weights_digest: str
    runtime_version: str
    dimension: int
    max_tokens: int

    def embed(self, texts: list[str]) -> list[list[float]]: ...


@dataclass
class OnnxEmbeddingRuntime:
    """CPU ONNX runtime for the EmbeddingGemma 2 text model.

    Lazy imports keep the default offline suite free of onnxruntime/tokenizers. The runtime
    validates every embedding (finite, expected dimension, non-zero norm) before returning it.
    """

    model_dir: Path
    expected_weights_digest: str | None = None
    max_tokens: int = MAX_TOKENS
    threads: int = 4
    model_id: str = MODEL_ID
    runtime_version: str = field(init=False)
    weights_digest: str = field(init=False)
    dimension: int = DIMENSION
    _session: object = field(init=False, repr=False)
    _tokenizer: object = field(init=False, repr=False)
    _numpy: object = field(init=False, repr=False)

    def __post_init__(self) -> None:
        missing = [
            name
            for name in (*WEIGHTS_FILES, TOKENIZER_FILE)
            if not (self.model_dir / name).is_file()
        ]
        if missing:
            raise RetrievalUnavailable(
                "Local EmbeddingGemma 2 weights are not installed under "
                f"{self.model_dir}: missing {', '.join(missing)}. No download or remote fallback "
                "is attempted."
            )
        digest = _weights_digest(self.model_dir)
        if self.expected_weights_digest is not None and digest != self.expected_weights_digest:
            raise RetrievalUnavailable(
                f"Local weights digest {digest} does not match the configured "
                f"{self.expected_weights_digest}; refusing to use different weights. "
                "No download or remote fallback is attempted."
            )
        try:
            import numpy as np
            import onnxruntime as ort
            from tokenizers import Tokenizer
        except ImportError as exc:
            raise RetrievalUnavailable(
                "The local-embedding runtime is not installed; run "
                "'uv sync --project backend --extra local-embedding' on this machine. "
                "No download or remote fallback is attempted."
            ) from exc
        self._numpy = np
        self.weights_digest = digest
        self.runtime_version = f"onnxruntime {ort.__version__}"
        options = ort.SessionOptions()
        options.intra_op_num_threads = max(1, self.threads)
        options.inter_op_num_threads = 1
        self._session = ort.InferenceSession(
            str(self.model_dir / WEIGHTS_FILES[0]),
            sess_options=options,
            providers=["CPUExecutionProvider"],
        )
        self._tokenizer = Tokenizer.from_file(str(self.model_dir / TOKENIZER_FILE))
        self._tokenizer.enable_truncation(max_length=self.max_tokens)

    @property
    def model_version(self) -> str:
        return f"{self.model_id}@{self.weights_digest[:12]}"

    def embed(self, texts: list[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            encoding = self._tokenizer.encode(text)
            ids = self._numpy.asarray([encoding.ids], dtype=self._numpy.int64)
            mask = self._numpy.ones_like(ids)
            empty = self._numpy.zeros((0, 512), dtype=self._numpy.float32)
            feed = {
                "input_ids": ids,
                "attention_mask": mask,
                "image_features": empty,
                "video_features": empty,
                "audio_features": empty,
            }
            embedding = self._session.run(["sentence_embedding"], feed)[0][0]
            vector = [float(value) for value in embedding]
            if len(vector) != self.dimension:
                raise RetrievalUnavailable(
                    f"Local embedding returned dimension {len(vector)}, expected {self.dimension}."
                )
            if not all(math.isfinite(value) for value in vector):
                raise RetrievalUnavailable("Local embedding returned a non-finite value.")
            norm = math.sqrt(sum(value * value for value in vector))
            if norm <= 0:
                raise RetrievalUnavailable("Local embedding returned a zero vector.")
            vectors.append([value / norm for value in vector])
        return vectors


@dataclass
class _Corpus:
    baseline: str
    commit: str
    binding: str
    documents: dict[str, str]
    embeddings: dict[str, list[float]]
    locators: dict[str, str]


class LocalEmbeddingCandidateDiscovery:
    """`CandidateDiscovery` over a local EmbeddingGemma 2 runtime and an in-memory corpus."""

    provider_name = PROVIDER_NAME

    def __init__(
        self,
        repository: ArtifactRepository,
        git: GitRepository,
        *,
        runtime: EmbeddingRuntime,
        model_version: str | None = None,
        formatting_version: str = FORMATTING_VERSION,
    ) -> None:
        self._repository = repository
        self._git = git
        self._runtime = runtime
        if model_version is None:
            model_id = getattr(runtime, "model_id", None)
            weights_digest = getattr(runtime, "weights_digest", None)
            if not model_id or not weights_digest:
                raise RetrievalUnavailable(
                    "The local runtime did not report a model identity and weights digest; "
                    "candidates will not be returned with invented provenance."
                )
            digest_hex = weights_digest.removeprefix("sha256:")
            model_version = f"{model_id}@sha256:{digest_hex[:12]}"
        self.model_version = model_version
        self.formatting_version = formatting_version
        self._lock = threading.RLock()
        self._corpora: dict[str, _Corpus] = {}

    @property
    def index_revision(self) -> str:
        return self.binding_for(None)

    @property
    def runtime(self) -> EmbeddingRuntime:
        return self._runtime

    def binding_for(self, baseline: str | None = None) -> str:
        canonical = self._repository.resolve_baseline(baseline)
        corpus = self._corpus(canonical)
        return corpus.binding

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
        canonical = self._repository.resolve_baseline(baseline)
        source = self._repository.get_artifact(artifact_id, baseline=canonical)
        allowed = self._allowed_relations(source, relation_types)
        if not allowed:
            return []
        corpus = self._corpus(canonical)
        query = self._query_text(source, corpus)
        query_vector = self._validate_vector(self._runtime.embed([query])[0])
        scored: list[tuple[float, Artifact]] = []
        for target in self._targets(corpus, source, allowed):
            if target.artifact_id == source.artifact_id:
                continue
            target_vector = corpus.embeddings[target.artifact_id]
            cosine = sum(a * b for a, b in zip(query_vector, target_vector, strict=True))
            scored.append((max(0.0, min(1.0, cosine)), target))
        scored.sort(key=lambda item: (-item[0], item[1].artifact_id))
        candidates: list[TraceCandidate] = []
        for rank, (score, target) in enumerate(scored[:top_k], start=1):
            candidates.append(
                TraceCandidate(
                    source_id=source.artifact_id,
                    target_id=target.artifact_id,
                    proposed_relation_type=_relation_between(
                        source.artifact_type, target.artifact_type, allowed
                    ),
                    rank=rank,
                    score=score,
                    discovery_provider=self.provider_name,
                    model_version=self.model_version,
                    index_revision=corpus.binding,
                    rationale=(
                        f"local cosine {score:.6f}; {MODEL_ID}; "
                        f"{self.formatting_version}; {corpus.binding}"
                    ),
                )
            )
        return candidates

    # ------------------------------------------------------------- internals

    def _allowed_relations(
        self, source: Artifact, requested: Sequence[RelationType] | None
    ) -> list[RelationType]:
        if requested is not None:
            return list(requested)
        if source.artifact_type is ArtifactType.REQUIREMENT:
            return [RelationType.VERIFIED_BY]
        if source.artifact_type is ArtifactType.SCENARIO:
            return [RelationType.IMPLEMENTED_BY, RelationType.EXERCISED_BY]
        return []

    def _targets(
        self, corpus: _Corpus, source: Artifact, allowed: list[RelationType]
    ) -> list[Artifact]:
        artifacts = {
            artifact.artifact_id: artifact
            for artifact in self._repository.list_artifacts(corpus.baseline)
        }
        targets: list[Artifact] = []
        for relation in allowed:
            expected_source, expected_target = RELATION_DIRECTION[relation]
            if source.artifact_type is not expected_source:
                continue
            for artifact in artifacts.values():
                if artifact.artifact_type is expected_target:
                    targets.append(artifact)
        unique = {artifact.artifact_id: artifact for artifact in targets}
        return sorted(unique.values(), key=lambda artifact: artifact.artifact_id)

    def _corpus(self, baseline: str) -> _Corpus:
        with self._lock:
            cached = self._corpora.get(baseline)
            if cached is not None:
                return cached
            commit = self._repository.commit_of(baseline)
            artifacts = self._repository.list_artifacts(baseline)
            documents: dict[str, str] = {}
            locators: dict[str, str] = {}
            for artifact in artifacts:
                documents[artifact.artifact_id] = self._document_text(artifact, commit)
                locators[artifact.artifact_id] = artifact.locator
            binding = _binding(
                baseline=baseline,
                commit=commit,
                artifacts=artifacts,
                model_version=self.model_version,
                weights_digest=getattr(self._runtime, "weights_digest", "unknown"),
                formatting=self.formatting_version,
            )
            embeddings: dict[str, list[float]] = {}
            if artifacts:
                vectors = self._runtime.embed([documents[a.artifact_id] for a in artifacts])
                if len(vectors) != len(artifacts):
                    raise RetrievalUnavailable(
                        "Local embedding runtime returned a different number of vectors "
                        "than inputs."
                    )
                for artifact, vector in zip(artifacts, vectors, strict=True):
                    embeddings[artifact.artifact_id] = self._validate_vector(vector)
            corpus = _Corpus(
                baseline=baseline,
                commit=commit,
                binding=binding,
                documents=documents,
                embeddings=embeddings,
                locators=locators,
            )
            self._corpora[baseline] = corpus
            return corpus

    def _validate_vector(self, vector: list[float]) -> list[float]:
        if len(vector) != self._runtime.dimension:
            raise RetrievalUnavailable(
                f"Local embedding returned dimension {len(vector)}, expected "
                f"{self._runtime.dimension}."
            )
        if not all(math.isfinite(value) for value in vector):
            raise RetrievalUnavailable("Local embedding returned a non-finite value.")
        norm = math.sqrt(sum(value * value for value in vector))
        if norm <= 0:
            raise RetrievalUnavailable("Local embedding returned a zero vector.")
        return [value / norm for value in vector]

    def _document_text(self, artifact: Artifact, commit: str) -> str:
        path = artifact.locator.split("#", 1)[0]
        try:
            raw = self._git.read_blob(commit, path)
        except Exception:  # noqa: BLE001 - an unreadable artifact is not a candidate
            raw = b""
        content = raw.decode("utf-8", "replace")
        if artifact.artifact_type is ArtifactType.SCENARIO:
            content = _scenario_block(content, artifact.locator) or artifact.title
        return DOCUMENT_TEMPLATE.format(title=artifact.locator, content=content)

    def _query_text(self, source: Artifact, corpus: _Corpus) -> str:
        path = source.locator.split("#", 1)[0]
        try:
            raw = self._git.read_blob(corpus.commit, path)
        except Exception:  # noqa: BLE001
            raw = b""
        content = raw.decode("utf-8", "replace")
        if source.artifact_type is ArtifactType.SCENARIO:
            content = _scenario_block(content, source.locator) or source.title
            template = QUERY_TEMPLATE_CODE
        else:
            template = QUERY_TEMPLATE_SEARCH
        return f"{template}{source.title}\n{content}".strip()


def _relation_between(
    source_type: ArtifactType,
    target_type: ArtifactType,
    allowed: Sequence[RelationType],
) -> RelationType:
    for relation in allowed:
        if RELATION_DIRECTION[relation] == (source_type, target_type):
            return relation
    raise InvalidRequest(
        f"No allowed relation connects {source_type.value} -> {target_type.value}."
    )


def _weights_digest(model_dir: Path) -> str:
    digest = hashlib.sha256()
    for name in WEIGHTS_FILES:
        path = model_dir / name
        digest.update(name.encode("utf-8"))
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def _binding(
    *,
    baseline: str,
    commit: str,
    artifacts: list[Artifact],
    model_version: str,
    weights_digest: str,
    formatting: str,
) -> str:
    payload = {
        "baseline": baseline,
        "commit": commit,
        "model_version": model_version,
        "weights_digest": weights_digest,
        "formatting": formatting,
        "dimension": DIMENSION,
        "artifacts": [
            {
                "artifact_id": artifact.artifact_id,
                "artifact_type": str(artifact.artifact_type),
                "locator": artifact.locator,
                "revision": artifact.revision,
                "content_hash": artifact.content_hash,
            }
            for artifact in sorted(artifacts, key=lambda item: item.artifact_id)
        ],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return f"sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"


def _scenario_block(text: str, locator: str) -> str | None:
    anchor = locator.split("#", 1)[1] if "#" in locator else None
    if anchor is None:
        return None
    lines = text.splitlines()
    start = next((index for index, line in enumerate(lines) if f"@{anchor}" in line), None)
    if start is None:
        return None
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if _ARTIFACT_TAG.search(lines[index]) and lines[index].lstrip().startswith("@"):
            end = index
            break
    return "\n".join(lines[start:end]).strip()


def validate_local_endpoint(endpoint: str | None) -> None:
    """Refuse a non-loopback endpoint before any connection is attempted."""
    if endpoint is None:
        return
    from urllib.parse import urlsplit

    parsed = urlsplit(endpoint)
    if parsed.hostname not in _LOOPBACK_HOSTS:
        raise InvalidRequest(
            f"Local inference mode refuses endpoint {endpoint!r}: only loopback endpoints "
            "are permitted; no connection was attempted."
        )


__all__ = [
    "EmbeddingRuntime",
    "LocalEmbeddingCandidateDiscovery",
    "OnnxEmbeddingRuntime",
    "validate_local_endpoint",
]
