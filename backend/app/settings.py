"""Runtime settings.

Offline by default: the application configures no remote endpoint unless ``CTA_AI_MODE=live``.
The AI provider variables are read here and validated without contacting any endpoint; provider
adapters are constructed only when the application or a tool asks for them.

Secret handling: API keys live in the process environment only. They are excluded from the
dataclass ``repr`` and must never be logged, serialized into a report, or sent to the frontend.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

DEFAULT_FIXTURE = "banking-demo"
DEFAULT_AI_MODE = "fake"
DEFAULT_VECTOR_BACKEND = "memory"

ENV_REPO_ROOT = "CTA_REPO_ROOT"
ENV_FIXTURES_DIR = "CTA_FIXTURES_DIR"
ENV_FIXTURE = "CTA_FIXTURE"
ENV_FIXTURE_REPO = "CTA_FIXTURE_REPO"
ENV_DISCOVERY_PROVIDER = "CTA_DISCOVERY_PROVIDER"

# Starting names from the RAG mission; kept verbatim so deployment configuration is explicit.
ENV_AI_MODE = "CTA_AI_MODE"
ENV_LLM_BASE_URL = "CTA_LLM_BASE_URL"
ENV_LLM_MODEL = "CTA_LLM_MODEL"
ENV_LLM_API_KEY = "CTA_LLM_API_KEY"
ENV_EMBED_BASE_URL = "CTA_EMBED_BASE_URL"
ENV_EMBED_MODEL = "CTA_EMBED_MODEL"
ENV_EMBED_API_KEY = "CTA_EMBED_API_KEY"
ENV_VECTOR_BACKEND = "CTA_VECTOR_BACKEND"
ENV_AI_LIVE_TESTS = "CTA_AI_LIVE_TESTS"

# CocoIndex Code (AI-06): an optional external code-search cache. Offline unless explicitly
# configured and opted in; it is never a default discovery provider in PR 1.
ENV_CCC_EXECUTABLE = "CTA_CCC_EXECUTABLE"
ENV_CCC_PROJECT_ROOT = "CTA_CCC_PROJECT_ROOT"
ENV_CCC_LIVE_OPT_IN = "CTA_CCC_LIVE_OPT_IN"
ENV_CCC_LIVE_TESTS = "CTA_CCC_LIVE_TESTS"

# AS-06 trusted-local-operator review mode. The journal is application-owned and must live
# outside the fixture/evaluated repository.
ENV_REVIEW_OPERATOR = "CTA_REVIEW_OPERATOR"
ENV_REVIEW_JOURNAL = "CTA_REVIEW_JOURNAL"

# AI-02 same-machine local inference. Disabled by default; the fake provider remains the default.
ENV_LOCAL_EMBEDDING = "CTA_LOCAL_EMBEDDING"
ENV_LOCAL_EMBEDDING_MODEL_DIR = "CTA_LOCAL_EMBEDDING_MODEL_DIR"
ENV_LOCAL_EMBEDDING_ENDPOINT = "CTA_LOCAL_EMBEDDING_ENDPOINT"
ENV_LOCAL_EMBEDDING_WEIGHTS_DIGEST = "CTA_LOCAL_EMBEDDING_WEIGHTS_DIGEST"
ENV_LOCAL_EMBEDDING_LIVE_TESTS = "CTA_LOCAL_EMBEDDING_LIVE_TESTS"

# AI-03 CTA-owned retrieval manifests. Application-owned, outside the fixture/evaluated repo.
ENV_RETRIEVAL_SNAPSHOT_DIR = "CTA_RETRIEVAL_SNAPSHOT_DIR"
DEFAULT_RETRIEVAL_SNAPSHOT_DIR = ".cta/retrieval-snapshots"

DEFAULT_CCC_EXECUTABLE = "ccc"
DEFAULT_REVIEW_JOURNAL = ".cta/review-journal.ndjson"

ALLOWED_AI_MODES: tuple[str, ...] = ("fake", "live")
#: PR 1 validates the selector but ships no vector index; PR 2 owns the in-memory index.
ALLOWED_VECTOR_BACKENDS: tuple[str, ...] = ("memory",)


class SettingsError(ValueError):
    """Invalid runtime configuration, raised before any network call."""


def _clean(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _env_flag(name: str, *, default: bool = False) -> bool:
    raw = _clean(os.environ.get(name))
    if raw is None:
        return default
    lowered = raw.lower()
    if lowered in {"1", "true", "yes", "on"}:
        return True
    if lowered in {"0", "false", "no", "off"}:
        return False
    raise SettingsError(f"{name} must be a boolean (1/0, true/false, yes/no, on/off)")


def validate_base_url(name: str, value: str | None) -> str | None:
    """Validate and normalize an HTTP(S) API base URL without contacting it.

    The configured value is the OpenAI-compatible API root, including its path prefix (for
    example ``http://host:8000/v1``). Credentials belong in the API-key variable, never in the
    URL; a query or fragment is rejected so a secret cannot be hidden there.
    """
    if value is None:
        return None
    normalized = value.strip().rstrip("/")
    parsed = urlsplit(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise SettingsError(f"{name} must be an absolute http(s) URL")
    if parsed.username or parsed.password:
        raise SettingsError(f"{name} must not contain credentials; use the API-key variable")
    if parsed.query or parsed.fragment:
        raise SettingsError(f"{name} must not contain a query or fragment")
    return normalized


@dataclass(frozen=True)
class Settings:
    repo_root: Path
    fixtures_dir: Path
    fixture: str = DEFAULT_FIXTURE
    discovery_provider: str = "fake"
    fixture_repo_path: Path | None = None

    # AI providers. `fake` is the default and keeps every normal path offline.
    ai_mode: str = DEFAULT_AI_MODE
    llm_base_url: str | None = None
    llm_model: str | None = None
    llm_api_key: str | None = field(default=None, repr=False)
    embed_base_url: str | None = None
    embed_model: str | None = None
    embed_api_key: str | None = field(default=None, repr=False)
    vector_backend: str = DEFAULT_VECTOR_BACKEND
    ai_live_tests: bool = False

    # CocoIndex Code capability (AI-06). The project root must be an initialized CocoIndex
    # project; live opt-in is separate so merely configuring a path contacts nothing.
    ccc_executable: str = DEFAULT_CCC_EXECUTABLE
    ccc_project_root: Path | None = None
    cocoindex_live_opt_in: bool = False
    ccc_live_tests: bool = False

    # Trusted-local-operator review (AS-06). Unset operator disables every review mutation.
    review_operator: str | None = None
    review_journal_path: Path | None = None
    review_loopback_only: bool = True

    # AI-02 same-machine local inference. An endpoint is accepted only on loopback; a remote
    # endpoint is refused by the provider rather than silently contacted.
    local_embedding_enabled: bool = False
    local_embedding_model_dir: Path | None = None
    local_embedding_endpoint: str | None = None
    local_embedding_weights_digest: str | None = None
    local_embedding_live_tests: bool = False

    # AI-03 application-owned retrieval manifest store.
    retrieval_snapshot_dir: Path | None = None

    def __post_init__(self) -> None:
        mode = self.ai_mode.strip().lower()
        vector_backend = self.vector_backend.strip().lower()
        object.__setattr__(self, "ai_mode", mode)
        object.__setattr__(self, "vector_backend", vector_backend)
        object.__setattr__(
            self, "llm_base_url", validate_base_url(ENV_LLM_BASE_URL, self.llm_base_url)
        )
        object.__setattr__(
            self, "embed_base_url", validate_base_url(ENV_EMBED_BASE_URL, self.embed_base_url)
        )
        object.__setattr__(self, "llm_model", _clean(self.llm_model))
        object.__setattr__(self, "embed_model", _clean(self.embed_model))
        object.__setattr__(self, "llm_api_key", _clean(self.llm_api_key))
        object.__setattr__(self, "embed_api_key", _clean(self.embed_api_key))

        if mode not in ALLOWED_AI_MODES:
            raise SettingsError(
                f"{ENV_AI_MODE} must be one of {', '.join(ALLOWED_AI_MODES)}; got '{mode}'"
            )
        if vector_backend not in ALLOWED_VECTOR_BACKENDS:
            raise SettingsError(
                f"{ENV_VECTOR_BACKEND} must be one of {', '.join(ALLOWED_VECTOR_BACKENDS)} "
                f"in PR 1; got '{vector_backend}'"
            )
        if mode == "live" and (self.llm_base_url is None or self.llm_model is None):
            raise SettingsError(
                f"{ENV_AI_MODE}=live requires {ENV_LLM_BASE_URL} and {ENV_LLM_MODEL}; "
                "the application will not silently fall back to fake"
            )
        if (self.embed_base_url is None) != (self.embed_model is None):
            raise SettingsError(
                f"{ENV_EMBED_BASE_URL} and {ENV_EMBED_MODEL} must be set together; "
                "embeddings are unavailable otherwise"
            )

        executable = _clean(self.ccc_executable) or DEFAULT_CCC_EXECUTABLE
        object.__setattr__(self, "ccc_executable", executable)
        if self.ccc_project_root is not None:
            root = self.ccc_project_root.expanduser().resolve()
            object.__setattr__(self, "ccc_project_root", root)
            if not root.is_dir():
                raise SettingsError(f"{ENV_CCC_PROJECT_ROOT} is not a directory: {root}")
            if root == Path.home().resolve():
                raise SettingsError(f"{ENV_CCC_PROJECT_ROOT} must not be the user home directory")
            if not (root / ".cocoindex_code" / "settings.yml").is_file():
                raise SettingsError(
                    f"{ENV_CCC_PROJECT_ROOT} is not an initialized CocoIndex project "
                    "(missing .cocoindex_code/settings.yml); run 'ccc init' in the snapshot"
                )
        if self.cocoindex_live_opt_in and self.ccc_project_root is None:
            raise SettingsError(
                f"{ENV_CCC_LIVE_OPT_IN}=true requires {ENV_CCC_PROJECT_ROOT}; "
                "the application will not guess a project to index"
            )

        operator = _clean(self.review_operator)
        object.__setattr__(self, "review_operator", operator)
        journal = self.review_journal_path or (self.repo_root / DEFAULT_REVIEW_JOURNAL)
        journal = journal.expanduser().resolve()
        forbidden = [self.fixtures_dir.resolve(), self.fixture_repo.resolve()]
        for root in forbidden:
            if journal == root or journal.is_relative_to(root):
                raise SettingsError(
                    f"{ENV_REVIEW_JOURNAL} must be outside the fixture and evaluated repository; "
                    f"got {journal} inside {root}"
                )
        if journal.is_dir():
            raise SettingsError(
                f"{ENV_REVIEW_JOURNAL} is a directory, not a journal file: {journal}"
            )
        object.__setattr__(self, "review_journal_path", journal)
        object.__setattr__(self, "review_loopback_only", True)

        model_dir = self.local_embedding_model_dir
        if model_dir is not None:
            object.__setattr__(self, "local_embedding_model_dir", model_dir.expanduser().resolve())
        endpoint = validate_base_url(ENV_LOCAL_EMBEDDING_ENDPOINT, self.local_embedding_endpoint)
        object.__setattr__(self, "local_embedding_endpoint", endpoint)
        digest = _clean(self.local_embedding_weights_digest)
        if digest is not None and not digest.startswith("sha256:"):
            raise SettingsError(
                f"{ENV_LOCAL_EMBEDDING_WEIGHTS_DIGEST} must be 'sha256:<hex>'; got {digest!r}"
            )
        object.__setattr__(self, "local_embedding_weights_digest", digest)

        snapshot_dir = self.retrieval_snapshot_dir or (
            self.repo_root / DEFAULT_RETRIEVAL_SNAPSHOT_DIR
        )
        snapshot_dir = snapshot_dir.expanduser().resolve()
        for root in (self.fixtures_dir.resolve(), self.fixture_repo.resolve()):
            if snapshot_dir == root or snapshot_dir.is_relative_to(root):
                raise SettingsError(
                    f"{ENV_RETRIEVAL_SNAPSHOT_DIR} must be outside the fixture and evaluated "
                    f"repository; got {snapshot_dir} inside {root}"
                )
        object.__setattr__(self, "retrieval_snapshot_dir", snapshot_dir)

    @property
    def llm_api_key_present(self) -> bool:
        """Whether a key is configured. The value itself is never reported."""
        return self.llm_api_key is not None

    @property
    def embed_api_key_present(self) -> bool:
        return self.embed_api_key is not None

    @property
    def embeddings_configured(self) -> bool:
        return self.embed_base_url is not None and self.embed_model is not None

    @property
    def cocoindex_enabled(self) -> bool:
        """Whether a live CocoIndex probe is both configured and explicitly opted in."""
        return self.cocoindex_live_opt_in and self.ccc_project_root is not None

    @property
    def review_enabled(self) -> bool:
        """Review mutations are available only with an explicit operator identity."""
        return self.review_operator is not None

    @property
    def review_journal(self) -> Path:
        assert self.review_journal_path is not None  # set in __post_init__
        return self.review_journal_path

    @property
    def local_embedding_configured(self) -> bool:
        """Local mode is registered only when explicitly enabled."""
        return self.local_embedding_enabled

    @property
    def retrieval_snapshots(self) -> Path:
        assert self.retrieval_snapshot_dir is not None  # set in __post_init__
        return self.retrieval_snapshot_dir

    @property
    def fixture_dir(self) -> Path:
        return self.fixtures_dir / self.fixture

    @property
    def fixture_repo(self) -> Path:
        """Nested Git repository ingested for reads; built by ``fixturectl build``."""
        return self.fixture_repo_path or (self.fixture_dir / ".build" / "repo")

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
    fixture_repo = os.environ.get(ENV_FIXTURE_REPO)
    ccc_root = _clean(os.environ.get(ENV_CCC_PROJECT_ROOT))
    return Settings(
        repo_root=repo_root,
        fixtures_dir=fixtures_dir,
        fixture=os.environ.get(ENV_FIXTURE, DEFAULT_FIXTURE),
        discovery_provider=os.environ.get(ENV_DISCOVERY_PROVIDER, "fake"),
        fixture_repo_path=Path(fixture_repo).resolve() if fixture_repo else None,
        ai_mode=os.environ.get(ENV_AI_MODE, DEFAULT_AI_MODE),
        llm_base_url=_clean(os.environ.get(ENV_LLM_BASE_URL)),
        llm_model=_clean(os.environ.get(ENV_LLM_MODEL)),
        llm_api_key=_clean(os.environ.get(ENV_LLM_API_KEY)),
        embed_base_url=_clean(os.environ.get(ENV_EMBED_BASE_URL)),
        embed_model=_clean(os.environ.get(ENV_EMBED_MODEL)),
        embed_api_key=_clean(os.environ.get(ENV_EMBED_API_KEY)),
        vector_backend=os.environ.get(ENV_VECTOR_BACKEND, DEFAULT_VECTOR_BACKEND),
        ai_live_tests=_env_flag(ENV_AI_LIVE_TESTS),
        ccc_executable=_clean(os.environ.get(ENV_CCC_EXECUTABLE)) or DEFAULT_CCC_EXECUTABLE,
        ccc_project_root=Path(ccc_root).expanduser() if ccc_root else None,
        cocoindex_live_opt_in=_env_flag(ENV_CCC_LIVE_OPT_IN),
        ccc_live_tests=_env_flag(ENV_CCC_LIVE_TESTS),
        review_operator=_clean(os.environ.get(ENV_REVIEW_OPERATOR)),
        review_journal_path=(
            Path(os.environ[ENV_REVIEW_JOURNAL]).expanduser()
            if os.environ.get(ENV_REVIEW_JOURNAL)
            else None
        ),
        local_embedding_enabled=_env_flag(ENV_LOCAL_EMBEDDING),
        local_embedding_model_dir=(
            Path(os.environ[ENV_LOCAL_EMBEDDING_MODEL_DIR]).expanduser()
            if os.environ.get(ENV_LOCAL_EMBEDDING_MODEL_DIR)
            else None
        ),
        local_embedding_endpoint=_clean(os.environ.get(ENV_LOCAL_EMBEDDING_ENDPOINT)),
        local_embedding_weights_digest=_clean(os.environ.get(ENV_LOCAL_EMBEDDING_WEIGHTS_DIGEST)),
        local_embedding_live_tests=_env_flag(ENV_LOCAL_EMBEDDING_LIVE_TESTS),
        retrieval_snapshot_dir=(
            Path(os.environ[ENV_RETRIEVAL_SNAPSHOT_DIR]).expanduser()
            if os.environ.get(ENV_RETRIEVAL_SNAPSHOT_DIR)
            else None
        ),
    )


def default_repo_root() -> Path:
    """Repository root assuming the documented monorepo layout (backend/app/settings.py)."""
    return Path(__file__).resolve().parents[2]
