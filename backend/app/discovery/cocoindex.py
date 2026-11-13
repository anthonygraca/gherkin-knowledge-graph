"""Optional CocoIndex Code search adapter (workstream A).

CocoIndex Code is an external, rebuildable *code-search cache*. This module is deliberately not a
:class:`app.domain.ports.CandidateDiscovery`: it has no artifact repository, no link vocabulary, no
review state, and no evidence writer. It turns one structured MCP ``search`` response into
non-authoritative hits that a later slice (AI-06 PR 2) may map to ``TraceCandidate`` values.

The default application never imports the live transport and never starts ``ccc``. Only
:class:`app.discovery.cocoindex_mcp.StdioMcpTransport` spawns a process, and only when a caller has
configured an explicit project root and live opt-in.
"""

from __future__ import annotations

import json
import math
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field, ValidationError, field_validator

COCOINDEX_PROVIDER = "cocoindex-code"
DEFAULT_LIMIT = 5
MAX_LIMIT = 100
MAX_QUERY_CHARS = 2_000
MAX_FILTERS = 10
MAX_FILTER_CHARS = 200
MAX_PATH_CHARS = 1_024
MAX_LANGUAGE_CHARS = 64
MAX_RESPONSE_BYTES = 512 * 1_024
MAX_HIT_CONTENT_CHARS = 256 * 1_024
MAX_REPORTED_MESSAGE_CHARS = 500

#: The only server identity this adapter is tested against. A different version is a capability
#: error until it is reviewed and added here; see ADR 0008.
SUPPORTED_SERVER_NAME = "cocoindex-code"
SUPPORTED_SERVER_VERSIONS = frozenset({"0.2.43"})


class CocoIndexError(Exception):
    """Typed adapter failure. Details contain no credentials or process environment values."""

    code = "cocoindex-error"

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)

    def __str__(self) -> str:
        return f"{self.code}: {self.detail}"


class CocoIndexConfigurationError(CocoIndexError):
    """The executable, project root, or project marker is missing or unsafe."""

    code = "cocoindex-configuration-error"


class CocoIndexRequestError(CocoIndexError):
    """A bounded request field was rejected before any process started."""

    code = "cocoindex-request-error"


class CocoIndexUnavailableError(CocoIndexError):
    """The server could not be started, exited early, or closed its pipes."""

    code = "cocoindex-unavailable"


class CocoIndexTimeoutError(CocoIndexError):
    """The total deadline expired; the process the adapter started was reaped."""

    code = "cocoindex-timeout"


class CocoIndexProtocolError(CocoIndexError):
    """A malformed or incompatible MCP response or search payload was rejected whole."""

    code = "cocoindex-protocol-error"


class CocoIndexQueryError(CocoIndexError):
    """The server reported ``success=false`` or an MCP tool error; no hits are returned."""

    code = "cocoindex-query-error"


class CocoIndexCapabilityError(CocoIndexError):
    """The server name, version, or tool schema is not the reviewed contract."""

    code = "cocoindex-capability-error"


def _clean_text(value: str, *, field: str) -> str:
    if not value or not value.strip():
        raise CocoIndexRequestError(f"{field} must be non-empty")
    if len(value) > MAX_QUERY_CHARS:
        raise CocoIndexRequestError(f"{field} must be at most {MAX_QUERY_CHARS} characters")
    if "\x00" in value:
        raise CocoIndexRequestError(f"{field} must not contain NUL")
    return value


def validate_relative_path(value: str, *, field: str) -> str:
    """Require a normalized, relative POSIX path.

    A returned hit path and a request path filter share this rule. Literal paths are valid globs
    (a pattern with no wildcard matches itself); the point is to keep the selector inside the
    configured project rather than to demand wildcards.
    """
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be a non-empty string")
    if len(value) > MAX_PATH_CHARS:
        raise ValueError(f"{field} must be at most {MAX_PATH_CHARS} characters")
    if "\x00" in value:
        raise ValueError(f"{field} must not contain NUL")
    if "\\" in value:
        raise ValueError(f"{field} must use POSIX '/' separators")
    if value.startswith("/") or value.startswith("//"):
        raise ValueError(f"{field} must be relative, not absolute")
    if len(value) >= 2 and value[1] == ":" and value[0].isalpha():
        raise ValueError(f"{field} must not carry a drive prefix")
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError(f"{field} must not contain empty, '.' or '..' components")
    if str(PurePosixPath(value)) != value:
        raise ValueError(f"{field} must be a normalized path")
    return value


class CocoIndexSearchRequest(BaseModel):
    """A bounded search request. ``refresh_index`` defaults to false: no implicit index mutation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    query: str = Field(min_length=1, max_length=MAX_QUERY_CHARS)
    limit: int = Field(default=DEFAULT_LIMIT, ge=1, le=MAX_LIMIT)
    offset: int = Field(default=0, ge=0)
    refresh_index: bool = False
    languages: tuple[str, ...] = ()
    paths: tuple[str, ...] = ()

    @field_validator("query")
    @classmethod
    def _query(cls, value: str) -> str:
        return _clean_text(value, field="query")

    @field_validator("languages")
    @classmethod
    def _languages(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(value) > MAX_FILTERS:
            raise ValueError(f"at most {MAX_FILTERS} language filters are allowed")
        for language in value:
            if not language or len(language) > MAX_LANGUAGE_CHARS:
                raise ValueError(
                    f"language filters must be 1..{MAX_LANGUAGE_CHARS} characters each"
                )
            if not all(character.isalnum() or character in "+#._-" for character in language):
                raise ValueError(f"language filter {language!r} contains unsupported characters")
        return value

    @field_validator("paths")
    @classmethod
    def _paths(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(value) > MAX_FILTERS:
            raise ValueError(f"at most {MAX_FILTERS} path filters are allowed")
        for path in value:
            try:
                validate_relative_path(path, field="path filter")
            except ValueError as exc:
                raise ValueError(str(exc)) from exc
            if len(path) > MAX_FILTER_CHARS:
                raise ValueError(f"path filters must be at most {MAX_FILTER_CHARS} characters each")
        return value


class CocoIndexServerInfo(BaseModel):
    """Identity the MCP server reported about itself. Never inferred from the executable name."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1)
    version: str | None = None
    protocol_version: str | None = None


class CocoIndexTool(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1)
    description: str | None = None
    input_schema: dict[str, Any] = Field(default_factory=dict)


class CocoIndexCapabilities(BaseModel):
    """Observed MCP capabilities, recorded so a contract change is visible."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    server: CocoIndexServerInfo
    tools: tuple[CocoIndexTool, ...]

    def search_tool(self) -> CocoIndexTool:
        for tool in self.tools:
            if tool.name == "search":
                return tool
        raise CocoIndexCapabilityError("the MCP server does not expose a 'search' tool")


class CocoIndexHit(BaseModel):
    """One non-authoritative code chunk, exactly as the server reported it.

    ``score`` is the server's similarity score, not a calibrated probability. The model does not
    clamp, rescale, deduplicate, or rerank hits.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    path: str = Field(min_length=1)
    language: str = Field(min_length=1)
    start_line: int = Field(ge=1)
    end_line: int = Field(ge=1)
    content: str
    score: float

    @field_validator("path")
    @classmethod
    def _path(cls, value: str) -> str:
        try:
            return validate_relative_path(value, field="hit path")
        except ValueError as exc:
            raise ValueError(str(exc)) from exc

    @field_validator("language")
    @classmethod
    def _language(cls, value: str) -> str:
        if len(value) > MAX_LANGUAGE_CHARS:
            raise ValueError(f"hit language must be at most {MAX_LANGUAGE_CHARS} characters")
        return value

    @field_validator("content")
    @classmethod
    def _content(cls, value: str) -> str:
        if len(value) > MAX_HIT_CONTENT_CHARS:
            raise ValueError(f"hit content exceeds {MAX_HIT_CONTENT_CHARS} characters")
        return value

    @field_validator("score")
    @classmethod
    def _score(cls, value: float) -> float:
        if not math.isfinite(value):
            raise ValueError("hit score must be finite")
        return value


class CocoIndexSearchResult(BaseModel):
    """Normalized observation. It has no link, review, evidence, or assurance field by design."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    provider: str = COCOINDEX_PROVIDER
    query: str
    limit: int
    offset: int
    refresh_index: bool
    hits: tuple[CocoIndexHit, ...]
    total_returned: int = Field(ge=0)
    message: str | None = None
    server: CocoIndexServerInfo | None = None
    #: Caller-supplied context, not an observation of what produced the index.
    project_root: str | None = None
    #: CocoIndex 0.2.43 does not report an index revision over MCP, so this stays ``None``.
    index_identity: str | None = None
    latency_ms: float = Field(ge=0)


@dataclass(frozen=True)
class CocoIndexRawSearch:
    """Transport-level result: the unmodified structured payload plus observed server identity."""

    payload: Mapping[str, Any]
    server: CocoIndexServerInfo | None = None


@runtime_checkable
class CocoIndexTransport(Protocol):
    """A bounded structured search transport. The live implementation spawns ``ccc mcp``."""

    project_root: Path | None

    def capabilities(self, *, timeout: float | None = None) -> CocoIndexCapabilities: ...

    def search(
        self, request: CocoIndexSearchRequest, *, timeout: float | None = None
    ) -> CocoIndexRawSearch: ...


class FakeCocoIndexTransport:
    """Deterministic transport over a captured payload. Never starts a process."""

    def __init__(
        self,
        payload: Mapping[str, Any],
        *,
        server: CocoIndexServerInfo | None = None,
        capabilities: CocoIndexCapabilities | None = None,
        project_root: Path | None = None,
    ) -> None:
        self._payload = payload
        self._server = server
        self._capabilities = capabilities
        self.project_root = project_root
        self.requests: list[CocoIndexSearchRequest] = []

    @classmethod
    def from_fixture(
        cls, path: Path, *, project_root: Path | None = None
    ) -> FakeCocoIndexTransport:
        """Load a captured response fixture (harness metadata plus ``payload``)."""
        document = json.loads(path.read_text(encoding="utf-8"))
        server = (
            CocoIndexServerInfo.model_validate(document["server_info"])
            if document.get("server_info")
            else None
        )
        return cls(document["payload"], server=server, project_root=project_root)

    def capabilities(self, *, timeout: float | None = None) -> CocoIndexCapabilities:
        if self._capabilities is None:
            raise CocoIndexUnavailableError("the fake transport has no capabilities")
        return self._capabilities

    def search(
        self, request: CocoIndexSearchRequest, *, timeout: float | None = None
    ) -> CocoIndexRawSearch:
        self.requests.append(request)
        return CocoIndexRawSearch(payload=self._payload, server=self._server)


def _require_mapping(value: Any, *, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise CocoIndexProtocolError(f"{field} must be an object")
    return value


def _require_exact_int(value: Any, *, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise CocoIndexProtocolError(f"{field} must be an integer")
    return value


def _require_bool(value: Any, *, field: str) -> bool:
    if not isinstance(value, bool):
        raise CocoIndexProtocolError(f"{field} must be a boolean")
    return value


def _require_number(value: Any, *, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CocoIndexProtocolError(f"{field} must be a number")
    number = float(value)
    if not math.isfinite(number):
        raise CocoIndexProtocolError(f"{field} must be finite")
    return number


def _reported_message(payload: Mapping[str, Any]) -> str | None:
    message = payload.get("message")
    if message is None:
        return None
    if not isinstance(message, str):
        raise CocoIndexProtocolError("message must be a string or null")
    cleaned = message.replace("\r", " ").replace("\n", " ").strip()
    return cleaned[:MAX_REPORTED_MESSAGE_CHARS] or None


def normalize_search_payload(
    payload: Mapping[str, Any],
    request: CocoIndexSearchRequest,
    *,
    server: CocoIndexServerInfo | None = None,
    project_root: Path | None = None,
    latency_ms: float = 0.0,
    max_hit_content_chars: int = MAX_HIT_CONTENT_CHARS,
) -> CocoIndexSearchResult:
    """Normalize one structured MCP search payload, rejecting malformed data whole.

    The server's ``success=false`` is reported before any hit is inspected: partial results from
    a failed query are never presented as a successful list.
    """
    document = _require_mapping(payload, field="search result")
    success = _require_bool(document.get("success"), field="search result success")
    message = _reported_message(document)
    if not success:
        raise CocoIndexQueryError(message or "the server reported success=false")

    results = document.get("results")
    if not isinstance(results, list):
        raise CocoIndexProtocolError("search result results must be a list")
    if len(results) > MAX_LIMIT:
        raise CocoIndexProtocolError(f"search result returned more than {MAX_LIMIT} hits")
    if len(results) > request.limit:
        raise CocoIndexProtocolError(
            f"search result returned {len(results)} hits for a limit of {request.limit}"
        )
    total = _require_exact_int(document.get("total_returned"), field="total_returned")
    offset = _require_exact_int(document.get("offset"), field="offset")
    if offset != request.offset:
        raise CocoIndexProtocolError(
            f"search result offset {offset} does not match request offset {request.offset}"
        )
    if total != len(results):
        raise CocoIndexProtocolError(
            f"search result total_returned {total} does not match {len(results)} hits"
        )

    hits: list[CocoIndexHit] = []
    for index, item in enumerate(results):
        raw = _require_mapping(item, field=f"hit {index}")
        path = raw.get("file_path")
        language = raw.get("language")
        content = raw.get("content")
        if (
            not isinstance(path, str)
            or not isinstance(language, str)
            or not isinstance(content, str)
        ):
            raise CocoIndexProtocolError(f"hit {index} has a non-string path, language, or content")
        if len(content) > max_hit_content_chars:
            raise CocoIndexProtocolError(
                f"hit {index} content exceeds {max_hit_content_chars} characters"
            )
        start = _require_exact_int(raw.get("start_line"), field=f"hit {index} start_line")
        end = _require_exact_int(raw.get("end_line"), field=f"hit {index} end_line")
        if start < 1 or end < start:
            raise CocoIndexProtocolError(f"hit {index} has an invalid line range {start}..{end}")
        score = _require_number(raw.get("score"), field=f"hit {index} score")
        try:
            hits.append(
                CocoIndexHit(
                    path=path,
                    language=language,
                    start_line=start,
                    end_line=end,
                    content=content,
                    score=score,
                )
            )
        except ValidationError as exc:
            raise CocoIndexProtocolError(f"hit {index} violates the hit contract: {exc}") from exc

    return CocoIndexSearchResult(
        query=request.query,
        limit=request.limit,
        offset=request.offset,
        refresh_index=request.refresh_index,
        hits=tuple(hits),
        total_returned=total,
        message=message,
        server=server,
        project_root=str(project_root) if project_root is not None else None,
        index_identity=None,
        latency_ms=max(0.0, latency_ms),
    )


def verify_hits_against_snapshot(project_root: Path, hits: Sequence[CocoIndexHit]) -> None:
    """Check hits against the snapshot on disk, rejecting any mismatch.

    Declared comparison rule: the hit content equals the file's lines
    ``start_line..end_line`` after removing one trailing newline from each. A path that resolves
    outside the configured root (including through a symlink), a missing file, a range beyond end
    of file, or different content is a protocol error, not a hit to repair.
    """
    root = project_root.resolve()
    for index, hit in enumerate(hits):
        candidate = (root / hit.path).resolve()
        if not candidate.is_relative_to(root):
            raise CocoIndexProtocolError(
                f"hit {index} resolves outside the configured project root"
            )
        if not candidate.is_file():
            raise CocoIndexProtocolError(f"hit {index} refers to a missing file: {hit.path}")
        lines = candidate.read_text(encoding="utf-8").splitlines(keepends=True)
        if hit.end_line > len(lines):
            raise CocoIndexProtocolError(
                f"hit {index} ends at line {hit.end_line} beyond end of file ({len(lines)} lines)"
            )
        expected = "".join(lines[hit.start_line - 1 : hit.end_line]).removesuffix("\n")
        reported = hit.content.removesuffix("\n")
        if reported != expected:
            raise CocoIndexProtocolError(
                f"hit {index} content does not match {hit.path} lines "
                f"{hit.start_line}..{hit.end_line} at the recorded snapshot"
            )


class CocoIndexSearchClient:
    """Normalizes a transport's structured search result. Holds no repository or writer."""

    provider_name = COCOINDEX_PROVIDER

    def __init__(
        self,
        transport: CocoIndexTransport,
        *,
        clock: Callable[[], float] = time.monotonic,
        max_hit_content_chars: int = MAX_HIT_CONTENT_CHARS,
    ) -> None:
        if not 1 <= max_hit_content_chars <= MAX_HIT_CONTENT_CHARS:
            raise CocoIndexConfigurationError(
                f"max_hit_content_chars must be 1..{MAX_HIT_CONTENT_CHARS}"
            )
        self._transport = transport
        self._clock = clock
        self._max_hit_content_chars = max_hit_content_chars

    @property
    def transport(self) -> CocoIndexTransport:
        return self._transport

    def capabilities(self, *, timeout: float | None = None) -> CocoIndexCapabilities:
        return self._transport.capabilities(timeout=timeout)

    def search(
        self,
        query: str,
        *,
        limit: int = DEFAULT_LIMIT,
        offset: int = 0,
        refresh_index: bool = False,
        languages: Sequence[str] = (),
        paths: Sequence[str] = (),
        timeout: float | None = None,
        capture: Callable[[Mapping[str, Any]], None] | None = None,
    ) -> CocoIndexSearchResult:
        try:
            request = CocoIndexSearchRequest(
                query=query,
                limit=limit,
                offset=offset,
                refresh_index=refresh_index,
                languages=tuple(languages),
                paths=tuple(paths),
            )
        except ValidationError as exc:
            raise CocoIndexRequestError(f"invalid search request: {exc}") from exc
        return self.search_request(request, timeout=timeout, capture=capture)

    def search_request(
        self,
        request: CocoIndexSearchRequest,
        *,
        timeout: float | None = None,
        capture: Callable[[Mapping[str, Any]], None] | None = None,
    ) -> CocoIndexSearchResult:
        started = self._clock()
        raw = self._transport.search(request, timeout=timeout)
        latency_ms = (self._clock() - started) * 1_000.0
        if capture is not None:
            capture(raw.payload)
        return normalize_search_payload(
            raw.payload,
            request,
            server=raw.server,
            project_root=self._transport.project_root,
            latency_ms=latency_ms,
            max_hit_content_chars=self._max_hit_content_chars,
        )
