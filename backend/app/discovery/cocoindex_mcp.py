"""Bounded MCP stdio transport for CocoIndex Code (``ccc mcp``).

One process per call: the adapter starts the server in the configured project root, performs the
MCP initialize/tools handshake, issues one search, and reaps the process group it started.

Lifecycle policy: the ``ccc mcp`` entry point is not side-effect free. On startup it schedules its
own asynchronous index update, and its client may start or restart a daemon. CTA therefore refuses
to run against the default shared user state: both ``COCOINDEX_CODE_DIR`` and
``COCOINDEX_CODE_RUNTIME_DIR`` must point at an isolated state/runtime pair. Any daemon start,
restart, or background index is then confined to that isolated pair and the configured disposable
project snapshot. This adapter never signals the default shared daemon.

The subprocess receives an allow-listed environment. CTA credentials and unrelated tokens in the
parent process are not inherited.
"""

from __future__ import annotations

import json
import os
import selectors
import shutil
import signal
import subprocess
import threading
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from app.discovery.ai import sanitize_text
from app.discovery.cocoindex import (
    MAX_FILTERS,
    MAX_LIMIT,
    MAX_QUERY_CHARS,
    MAX_RESPONSE_BYTES,
    SUPPORTED_SERVER_NAME,
    SUPPORTED_SERVER_VERSIONS,
    CocoIndexCapabilities,
    CocoIndexCapabilityError,
    CocoIndexConfigurationError,
    CocoIndexProtocolError,
    CocoIndexRawSearch,
    CocoIndexSearchRequest,
    CocoIndexServerInfo,
    CocoIndexTimeoutError,
    CocoIndexTool,
    CocoIndexUnavailableError,
    normalize_search_payload,
)

DEFAULT_TIMEOUT_SECONDS = 90.0
MAX_TIMEOUT_SECONDS = 600.0
DEFAULT_CLEANUP_SECONDS = 5.0
MAX_STDERR_BYTES = 64 * 1_024
PROTOCOL_VERSION = "2024-11-05"
MCP_SERVER_ARGS: tuple[str, ...] = ("mcp",)

#: Environment keys the child may see. Everything else (API keys, tokens, CTA_* secrets) is
#: dropped. ``COCOINDEX_CODE_*`` selects an isolated daemon for tests and per-snapshot probes.
ALLOWED_ENVIRONMENT = frozenset(
    {
        "PATH",
        "HOME",
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "TMPDIR",
        "XDG_RUNTIME_DIR",
        "COCOINDEX_CODE_DIR",
        "COCOINDEX_CODE_RUNTIME_DIR",
        "OLLAMA_API_BASE",
        "SSL_CERT_FILE",
        "SSL_CERT_DIR",
        "REQUESTS_CA_BUNDLE",
    }
)

_REQUIRED_SEARCH_PROPERTIES = (
    "query",
    "limit",
    "offset",
    "refresh_index",
    "languages",
    "paths",
)

# Annotations do not constrain a request. Everything else must be a keyword the adapter has
# explicitly reviewed; unknown assertion keywords are rejected rather than ignored.
_ANNOTATION_KEYWORDS = frozenset(
    {
        "title",
        "description",
        "default",
        "examples",
        "deprecated",
        "readOnly",
        "writeOnly",
        "$comment",
    }
)
_TOP_SCHEMA_KEYWORDS = _ANNOTATION_KEYWORDS | frozenset(
    {"type", "properties", "required", "additionalProperties", "$schema"}
)
_QUERY_KEYWORDS = _ANNOTATION_KEYWORDS | frozenset({"type", "maxLength", "minLength"})
_LIMIT_KEYWORDS = _ANNOTATION_KEYWORDS | frozenset({"type", "minimum", "maximum"})
_OFFSET_KEYWORDS = _ANNOTATION_KEYWORDS | frozenset({"type", "minimum"})
_REFRESH_KEYWORDS = _ANNOTATION_KEYWORDS | frozenset({"type"})
_FILTER_PROPERTY_KEYWORDS = _ANNOTATION_KEYWORDS | frozenset({"anyOf", "maxItems"})
_FILTER_UNION_KEYWORDS = _ANNOTATION_KEYWORDS | frozenset({"type", "items", "maxItems"})
_ARRAY_SCHEMA_KEYWORDS = _ANNOTATION_KEYWORDS | frozenset({"type", "items", "maxItems"})
_NULL_SCHEMA_KEYWORDS = _ANNOTATION_KEYWORDS | frozenset({"type"})
_ITEMS_SCHEMA_KEYWORDS = _ANNOTATION_KEYWORDS | frozenset({"type"})


def _reject_unknown_keywords(
    schema: Mapping[str, Any], allowed: frozenset[str], *, field: str
) -> None:
    unknown = sorted(set(schema) - allowed)
    if unknown:
        raise CocoIndexCapabilityError(
            f"{field} uses unsupported validation keywords: {', '.join(unknown)}"
        )


def _is_string_array(schema: Any) -> bool:
    if not isinstance(schema, Mapping):
        return False
    declared = schema.get("type")
    array_like = declared == "array" or (
        isinstance(declared, list) and set(declared) == {"array", "null"}
    )
    return (
        array_like
        and isinstance(schema.get("items"), Mapping)
        and schema["items"].get("type") == "string"
    )


def _check_max_items(schema: Mapping[str, Any], *, field: str) -> None:
    max_items = schema.get("maxItems")
    if max_items is not None and (
        isinstance(max_items, bool) or not isinstance(max_items, int) or max_items < MAX_FILTERS
    ):
        raise CocoIndexCapabilityError(f"{field}.maxItems must allow {MAX_FILTERS} filters")


def _validate_filter_schema(schema: Any, *, field: str) -> None:
    if not isinstance(schema, Mapping):
        raise CocoIndexCapabilityError(f"{field} must be a schema object")
    if "anyOf" in schema:
        _reject_unknown_keywords(schema, _FILTER_PROPERTY_KEYWORDS, field=field)
    else:
        _reject_unknown_keywords(schema, _FILTER_UNION_KEYWORDS, field=field)
    _check_max_items(schema, field=field)
    declared = schema.get("type")
    array_schema: Mapping[str, Any] | None = None
    if isinstance(declared, list):
        if set(declared) != {"array", "null"} or not _is_string_array(schema):
            raise CocoIndexCapabilityError(f"{field} must accept an array of strings or null")
        array_schema = schema
    else:
        alternatives = schema.get("anyOf")
        if not isinstance(alternatives, list) or len(alternatives) != 2:
            raise CocoIndexCapabilityError(f"{field} must accept an array of strings or null")
        arrays = [item for item in alternatives if _is_string_array(item)]
        nulls = [
            item
            for item in alternatives
            if isinstance(item, Mapping) and item.get("type") == "null"
        ]
        if len(arrays) != 1 or len(nulls) != 1:
            raise CocoIndexCapabilityError(f"{field} must accept an array of strings or null")
        _reject_unknown_keywords(arrays[0], _ARRAY_SCHEMA_KEYWORDS, field=f"{field} array")
        _reject_unknown_keywords(nulls[0], _NULL_SCHEMA_KEYWORDS, field=f"{field} null")
        array_schema = arrays[0]
    assert array_schema is not None
    _check_max_items(array_schema, field=field)
    items = array_schema.get("items")
    if not isinstance(items, Mapping):
        raise CocoIndexCapabilityError(f"{field}.items must be a string schema")
    _reject_unknown_keywords(items, _ITEMS_SCHEMA_KEYWORDS, field=f"{field}.items")
    if items.get("type") != "string":
        raise CocoIndexCapabilityError(f"{field}.items must be a string schema")


def _bounded_seconds(value: float, *, name: str) -> float:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise CocoIndexConfigurationError(f"{name} must be a number of seconds")
    seconds = float(value)
    if not 0.0 < seconds <= MAX_TIMEOUT_SECONDS:
        raise CocoIndexConfigurationError(
            f"{name} must be greater than 0 and at most {MAX_TIMEOUT_SECONDS:.0f} seconds"
        )
    return seconds


def _resolve_executable(executable: str) -> str:
    candidate = executable.strip()
    if not candidate:
        raise CocoIndexConfigurationError("a CocoIndex executable must be configured")
    if "/" in candidate or "\\" in candidate:
        path = Path(candidate).expanduser().resolve()
        if not path.is_file() or not os.access(path, os.X_OK):
            raise CocoIndexConfigurationError(
                f"CocoIndex executable is not an executable file: {path}"
            )
        return str(path)
    located = shutil.which(candidate)
    if located is None:
        raise CocoIndexConfigurationError(
            f"CocoIndex executable '{candidate}' was not found on PATH"
        )
    return located


def _validate_project_root(project_root: Path) -> Path:
    root = project_root.expanduser().resolve()
    if not root.is_dir():
        raise CocoIndexConfigurationError(f"CocoIndex project root is not a directory: {root}")
    if root == Path.home().resolve():
        raise CocoIndexConfigurationError(
            "CocoIndex project root must not be the user home directory"
        )
    marker = root / ".cocoindex_code" / "settings.yml"
    if not marker.is_file():
        raise CocoIndexConfigurationError(
            f"CocoIndex project root has no {marker.relative_to(root)}; "
            "run 'ccc init' in the snapshot or choose the project root explicitly"
        )
    return root


def validate_isolated_state(environment: Mapping[str, str]) -> tuple[Path, Path]:
    """Require a state/runtime pair that is not the shared default user state.

    ``ccc mcp`` may start/restart a daemon and always schedules a background index update. CTA
    confines those effects by refusing the default ``~/.cocoindex_code`` state and requiring an
    explicit, initialized global-settings directory plus a separate runtime directory.
    """
    state_raw = environment.get("COCOINDEX_CODE_DIR")
    runtime_raw = environment.get("COCOINDEX_CODE_RUNTIME_DIR")
    if not state_raw or not runtime_raw:
        raise CocoIndexConfigurationError(
            "CocoIndex live use requires COCOINDEX_CODE_DIR and COCOINDEX_CODE_RUNTIME_DIR "
            "for an isolated state/daemon; CTA will not use the shared default user state"
        )
    if (
        not Path(state_raw).expanduser().is_absolute()
        or not Path(runtime_raw).expanduser().is_absolute()
    ):
        raise CocoIndexConfigurationError(
            "COCOINDEX_CODE_DIR and COCOINDEX_CODE_RUNTIME_DIR must be absolute paths; "
            "the child runs in the snapshot directory, so relative paths would resolve differently"
        )
    state = Path(state_raw).expanduser().resolve()
    runtime = Path(runtime_raw).expanduser().resolve()
    default_state = (Path.home() / ".cocoindex_code").resolve()
    if state == default_state or runtime == default_state:
        raise CocoIndexConfigurationError(
            "CocoIndex state/runtime must not be the shared ~/.cocoindex_code directory"
        )
    if not state.is_dir():
        raise CocoIndexConfigurationError(f"CocoIndex state directory does not exist: {state}")
    if not (state / "global_settings.yml").is_file():
        raise CocoIndexConfigurationError(
            f"CocoIndex state directory has no global_settings.yml: {state}; "
            "create an isolated settings file before live use"
        )
    return state, runtime


def child_environment(extra: Mapping[str, str] | None = None) -> dict[str, str]:
    env = {key: os.environ[key] for key in sorted(ALLOWED_ENVIRONMENT) if key in os.environ}
    if extra:
        for key, value in extra.items():
            if key not in ALLOWED_ENVIRONMENT:
                raise CocoIndexConfigurationError(
                    f"environment key '{key}' is not allowed for the CocoIndex subprocess"
                )
            env[key] = value
    return env


def _same_json(left: Any, right: Any) -> bool:
    """Strict JSON equality: ``True`` is not ``1`` and ``False`` is not ``0``."""
    if isinstance(left, bool) or isinstance(right, bool):
        return isinstance(left, bool) and isinstance(right, bool) and left is right
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return left == right
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(
            _same_json(left[key], right[key]) for key in left
        )
    if isinstance(left, list):
        return len(left) == len(right) and all(
            _same_json(left_item, right_item)
            for left_item, right_item in zip(left, right, strict=True)
        )
    return left == right


class _StderrCapture:
    """Drain stderr concurrently, retaining only a bounded tail.

    The read loop uses ``select`` with a short timeout and a stop flag, so cleanup never waits on
    a descendant that holds the stderr pipe open.
    """

    def __init__(self, stream: Any, limit: int) -> None:
        self._stream = stream
        self._limit = limit
        self._buffer = bytearray()
        self._total = 0
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, name="cocoindex-stderr", daemon=True)

    def start(self) -> None:
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()

    def join(self, timeout: float) -> None:
        self._thread.join(timeout)

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                import select

                ready, _, _ = select.select([self._stream], [], [], 0.05)
            except (OSError, ValueError):
                return
            if not ready:
                continue
            try:
                chunk = self._stream.read(8_192)
            except (OSError, ValueError):
                return
            if not chunk:
                return
            with self._lock:
                self._total += len(chunk)
                self._buffer.extend(chunk)
                if len(self._buffer) > self._limit:
                    del self._buffer[: len(self._buffer) - self._limit]

    def text(self) -> str:
        with self._lock:
            raw = bytes(self._buffer)
            truncated = self._total > len(raw)
        value = raw.decode("utf-8", "replace").replace("\x00", "").replace("\r", " ").strip()
        value = sanitize_text(value)
        if truncated:
            value = f"[truncated] {value}"
        return value[-1_500:]


class _LineReader:
    """Read newline-delimited JSON from a child's stdout with a shared deadline."""

    def __init__(self, stdout: Any, *, max_message_bytes: int) -> None:
        self._stdout = stdout
        self._max_message_bytes = max_message_bytes
        self._buffer = bytearray()
        self._selector = None
        try:
            import selectors

            self._selector = selectors.DefaultSelector()
            self._selector.register(stdout, selectors.EVENT_READ)
        except (ImportError, ValueError, OSError):
            self._selector = None

    def close(self) -> None:
        if self._selector is not None:
            try:
                self._selector.close()
            except OSError:
                pass

    def read(self, deadline: float) -> dict[str, Any]:
        while True:
            newline = self._buffer.find(b"\n")
            if newline >= 0:
                line = bytes(self._buffer[:newline])
                del self._buffer[: newline + 1]
                return self._decode(line)
            if len(self._buffer) > self._max_message_bytes:
                raise CocoIndexProtocolError(
                    f"MCP message exceeds {self._max_message_bytes} bytes without a newline"
                )
            remaining = deadline - time.monotonic()
            if remaining <= 0.0:
                raise CocoIndexTimeoutError("timed out waiting for the MCP server")
            if self._selector is not None:
                if not self._selector.select(remaining):
                    raise CocoIndexTimeoutError("timed out waiting for the MCP server")
            elif not self._wait_readable(remaining):
                raise CocoIndexTimeoutError("timed out waiting for the MCP server")
            try:
                chunk = os.read(self._stdout.fileno(), 65_536)
            except OSError as exc:
                raise CocoIndexUnavailableError(
                    f"could not read the MCP server output: {exc.strerror or exc}"
                ) from exc
            if not chunk:
                raise CocoIndexUnavailableError("the MCP server closed its output pipe")
            self._buffer.extend(chunk)

    def _wait_readable(self, remaining: float) -> bool:
        import select

        ready, _, _ = select.select([self._stdout], [], [], remaining)
        return bool(ready)

    def _decode(self, line: bytes) -> dict[str, Any]:
        if len(line) > self._max_message_bytes:
            raise CocoIndexProtocolError(f"MCP message exceeds {self._max_message_bytes} bytes")
        try:
            message = json.loads(line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            preview = line[:200].decode("utf-8", "replace")
            raise CocoIndexProtocolError(
                f"MCP server returned a non-JSON line: {preview!r}"
            ) from exc
        if not isinstance(message, dict):
            raise CocoIndexProtocolError("MCP message must be a JSON object")
        if message.get("jsonrpc") != "2.0":
            raise CocoIndexProtocolError("MCP message must declare jsonrpc 2.0")
        return message


class StdioMcpTransport:
    """Spawn ``ccc mcp`` once per call and normalize its structured search result."""

    def __init__(
        self,
        *,
        executable: str = "ccc",
        project_root: Path,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        cleanup_timeout: float = DEFAULT_CLEANUP_SECONDS,
        expected_versions: frozenset[str] = SUPPORTED_SERVER_VERSIONS,
        max_response_bytes: int = MAX_RESPONSE_BYTES,
        max_stderr_bytes: int = MAX_STDERR_BYTES,
        stdin_pipe_bytes: int | None = None,
        environment: Mapping[str, str] | None = None,
    ) -> None:
        self._executable = _resolve_executable(executable)
        self.project_root = _validate_project_root(project_root)
        self._timeout = _bounded_seconds(timeout, name="timeout")
        self._cleanup_timeout = _bounded_seconds(cleanup_timeout, name="cleanup_timeout")
        self._expected_versions = expected_versions
        if max_response_bytes < 1_024:
            raise CocoIndexConfigurationError("max_response_bytes must be at least 1024")
        self._max_response_bytes = max_response_bytes
        if max_stderr_bytes < 1_024:
            raise CocoIndexConfigurationError("max_stderr_bytes must be at least 1024")
        self._max_stderr_bytes = max_stderr_bytes
        if stdin_pipe_bytes is not None and not 1_024 <= stdin_pipe_bytes <= 1_048_576:
            raise CocoIndexConfigurationError("stdin_pipe_bytes must be 1024..1048576")
        self._stdin_pipe_bytes = stdin_pipe_bytes
        self._environment = child_environment(environment)
        self.isolated_state, self.isolated_runtime = validate_isolated_state(self._environment)
        self._environment["COCOINDEX_CODE_DIR"] = str(self.isolated_state)
        self._environment["COCOINDEX_CODE_RUNTIME_DIR"] = str(self.isolated_runtime)
        if self.isolated_state == (self.project_root / ".cocoindex_code").resolve():
            raise CocoIndexConfigurationError(
                "CocoIndex state directory must be separate from the project-local "
                ".cocoindex_code index directory"
            )

    # -- public API -----------------------------------------------------------------

    def capabilities(self, *, timeout: float | None = None) -> CocoIndexCapabilities:
        deadline_seconds = self._deadline_seconds(timeout)
        with self._session(deadline_seconds) as session:
            return session.capabilities

    def search(
        self, request: CocoIndexSearchRequest, *, timeout: float | None = None
    ) -> CocoIndexRawSearch:
        deadline_seconds = self._deadline_seconds(timeout)
        with self._session(deadline_seconds) as session:
            return session.search(request)

    # -- session --------------------------------------------------------------------

    def _deadline_seconds(self, timeout: float | None) -> float:
        if timeout is None:
            return self._timeout
        return _bounded_seconds(timeout, name="timeout")

    def _session(self, timeout: float) -> _Session:
        return _Session(
            executable=self._executable,
            project_root=self.project_root,
            timeout=timeout,
            cleanup_timeout=self._cleanup_timeout,
            expected_versions=self._expected_versions,
            max_response_bytes=self._max_response_bytes,
            max_stderr_bytes=self._max_stderr_bytes,
            stdin_pipe_bytes=self._stdin_pipe_bytes,
            environment=self._environment,
        )


class _Session:
    """One short-lived MCP process and its handshake."""

    def __init__(
        self,
        *,
        executable: str,
        project_root: Path,
        timeout: float,
        cleanup_timeout: float,
        expected_versions: frozenset[str],
        max_response_bytes: int,
        max_stderr_bytes: int,
        stdin_pipe_bytes: int | None,
        environment: Mapping[str, str],
    ) -> None:
        self._executable = executable
        self._project_root = project_root
        self._timeout = timeout
        self._cleanup_timeout = cleanup_timeout
        self._expected_versions = expected_versions
        self._max_response_bytes = max_response_bytes
        self._max_stderr_bytes = max_stderr_bytes
        self._stdin_pipe_bytes = stdin_pipe_bytes
        self._environment = dict(environment)
        self._process: subprocess.Popen[bytes] | None = None
        self._reader: _LineReader | None = None
        self._stderr: _StderrCapture | None = None
        self._pgid: int | None = None
        self._stdin_fd: int | None = None
        self._next_id = 1
        self._deadline = 0.0
        self.capabilities: CocoIndexCapabilities | None = None
        self.server: CocoIndexServerInfo | None = None

    def __enter__(self) -> _Session:
        self._deadline = time.monotonic() + self._timeout
        self._start()
        try:
            self._handshake()
        except BaseException:
            self._stop(self._process)
            self._process = None
            raise
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> bool:
        process = self._process
        self._process = None
        self._stop(process)
        return False

    # -- lifecycle ------------------------------------------------------------------

    def _start(self) -> None:
        try:
            self._process = subprocess.Popen(
                [self._executable, *MCP_SERVER_ARGS],
                cwd=self._project_root,
                env=self._environment,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=os.name == "posix",
                bufsize=0,
            )
        except OSError as exc:
            raise CocoIndexUnavailableError(
                f"could not start the MCP server: {exc.strerror or exc}"
            ) from exc
        assert self._process.stderr is not None
        assert self._process.stdout is not None
        if os.name == "posix":
            self._pgid = os.getpgid(self._process.pid)
            if self._process.stdin is not None:
                self._stdin_fd = self._process.stdin.fileno()
                os.set_blocking(self._stdin_fd, False)
                if self._stdin_pipe_bytes is not None:
                    import fcntl

                    try:
                        fcntl.fcntl(self._stdin_fd, fcntl.F_SETPIPE_SZ, self._stdin_pipe_bytes)
                    except OSError:
                        pass
        self._stderr = _StderrCapture(self._process.stderr, self._max_stderr_bytes)
        self._stderr.start()
        self._reader = _LineReader(self._process.stdout, max_message_bytes=self._max_response_bytes)

    def _stop(self, process: subprocess.Popen[bytes] | None) -> None:
        if self._reader is not None:
            self._reader.close()
            self._reader = None
        if process is not None:
            # Signal the saved process group even when the leader already exited: a descendant
            # can still hold the stderr pipe open. The daemon is started in its own session, so
            # this never targets the shared daemon.
            if os.name == "posix" and self._pgid is not None:
                self._signal_group(signal.SIGTERM)
            elif process.poll() is None:
                process.terminate()
            term_wait = min(1.0, self._cleanup_timeout / 2.0)
            if process.poll() is None:
                try:
                    process.wait(timeout=term_wait)
                except subprocess.TimeoutExpired:
                    pass
            if os.name == "posix" and self._pgid is not None:
                self._signal_group(signal.SIGKILL)
            elif process.poll() is None:
                process.kill()
            try:
                process.wait(timeout=self._cleanup_timeout)
            except subprocess.TimeoutExpired:
                pass
        self._stop_stderr()
        if process is not None:
            for stream in (process.stdin, process.stdout, process.stderr):
                if stream is not None:
                    try:
                        stream.close()
                    except OSError:
                        pass
        self._stdin_fd = None
        self._pgid = None

    def _stop_stderr(self) -> None:
        if self._stderr is None:
            return
        self._stderr.stop()
        self._stderr.join(min(0.5, self._cleanup_timeout))
        self._stderr = None

    def _signal_group(self, signum: int) -> None:
        if self._pgid is None:
            return
        try:
            os.killpg(self._pgid, signum)
        except (ProcessLookupError, PermissionError, OSError):
            pass

    def _failure(self, message: str) -> CocoIndexUnavailableError:
        stderr = self._stderr.text() if self._stderr is not None else ""
        detail = f"{message}: {stderr}" if stderr else message
        return CocoIndexUnavailableError(detail)

    # -- protocol -------------------------------------------------------------------

    def _handshake(self) -> None:
        result = self._request(
            "initialize",
            {
                "protocolVersion": PROTOCOL_VERSION,
                "capabilities": {},
                "clientInfo": {"name": "cta-cocoindex-client", "version": "0.1.0"},
            },
        )
        server = self._server_info(result)
        self.server = server
        self._send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        tools_result = self._request("tools/list", {})
        tools = self._tools(tools_result)
        self.capabilities = CocoIndexCapabilities(server=server, tools=tools)
        self._validate_search_tool(self.capabilities)

    def _server_info(self, result: Mapping[str, Any]) -> CocoIndexServerInfo:
        raw = result.get("serverInfo")
        if not isinstance(raw, Mapping):
            raise CocoIndexCapabilityError("the MCP server did not report serverInfo")
        name = raw.get("name")
        version = raw.get("version")
        if not isinstance(name, str) or not name:
            raise CocoIndexCapabilityError("the MCP serverInfo name is missing")
        if name != SUPPORTED_SERVER_NAME:
            raise CocoIndexCapabilityError(
                f"unexpected MCP server name {name!r}; expected {SUPPORTED_SERVER_NAME!r}"
            )
        if not isinstance(version, str) or version not in self._expected_versions:
            expected = ", ".join(sorted(self._expected_versions))
            raise CocoIndexCapabilityError(
                f"untested CocoIndex server version {version!r}; tested versions: {expected}"
            )
        protocol = result.get("protocolVersion")
        return CocoIndexServerInfo(
            name=name,
            version=version,
            protocol_version=protocol if isinstance(protocol, str) else None,
        )

    def _tools(self, result: Mapping[str, Any]) -> tuple[CocoIndexTool, ...]:
        raw_tools = result.get("tools")
        if not isinstance(raw_tools, list):
            raise CocoIndexProtocolError("tools/list did not return a tools list")
        tools: list[CocoIndexTool] = []
        for item in raw_tools:
            if not isinstance(item, Mapping):
                raise CocoIndexProtocolError("tools/list contains a non-object tool")
            name = item.get("name")
            if not isinstance(name, str) or not name:
                raise CocoIndexProtocolError("tools/list contains a tool without a name")
            description = item.get("description")
            schema = item.get("inputSchema")
            try:
                tools.append(
                    CocoIndexTool(
                        name=name,
                        description=description if isinstance(description, str) else None,
                        input_schema=dict(schema) if isinstance(schema, Mapping) else {},
                    )
                )
            except ValueError as exc:
                raise CocoIndexProtocolError(f"invalid tool entry: {exc}") from exc
        return tuple(tools)

    @staticmethod
    def _validate_search_tool(capabilities: CocoIndexCapabilities) -> None:
        tool = capabilities.search_tool()
        schema = tool.input_schema
        _reject_unknown_keywords(schema, _TOP_SCHEMA_KEYWORDS, field="search input")
        if schema.get("type") != "object":
            raise CocoIndexCapabilityError("the search tool input must be an object schema")
        properties = schema.get("properties")
        if not isinstance(properties, Mapping):
            raise CocoIndexCapabilityError("the search tool exposes no input properties")
        missing = [name for name in _REQUIRED_SEARCH_PROPERTIES if name not in properties]
        if missing:
            raise CocoIndexCapabilityError(
                f"the search tool is missing properties: {', '.join(missing)}"
            )
        property_keywords = {
            "query": _QUERY_KEYWORDS,
            "limit": _LIMIT_KEYWORDS,
            "offset": _OFFSET_KEYWORDS,
            "refresh_index": _REFRESH_KEYWORDS,
        }
        for name, allowed in property_keywords.items():
            property_schema = properties[name]
            if not isinstance(property_schema, Mapping):
                raise CocoIndexCapabilityError(f"search.{name} must be a schema object")
            _reject_unknown_keywords(property_schema, allowed, field=f"search.{name}")
        for name in ("languages", "paths"):
            _validate_filter_schema(properties[name], field=f"search.{name}")
        required = schema.get("required")
        if (
            not isinstance(required, list)
            or not all(isinstance(name, str) for name in required)
            or set(required) != {"query"}
        ):
            raise CocoIndexCapabilityError(
                "the search tool must require exactly 'query' (no unknown required arguments)"
            )

        query = properties["query"]
        if not isinstance(query, Mapping) or query.get("type") != "string":
            raise CocoIndexCapabilityError("search.query must be a string schema")
        query_max = query.get("maxLength")
        if query_max is not None and (
            isinstance(query_max, bool)
            or not isinstance(query_max, int)
            or query_max < MAX_QUERY_CHARS
        ):
            raise CocoIndexCapabilityError(
                f"search.query.maxLength must allow {MAX_QUERY_CHARS} characters"
            )
        query_min = query.get("minLength")
        if query_min is not None and (
            isinstance(query_min, bool) or not isinstance(query_min, int) or query_min > 1
        ):
            raise CocoIndexCapabilityError("search.query.minLength must allow one character")
        limit = properties["limit"]
        if not isinstance(limit, Mapping) or limit.get("type") != "integer":
            raise CocoIndexCapabilityError("search.limit must be an integer schema")
        minimum = limit.get("minimum")
        maximum = limit.get("maximum")
        if (
            isinstance(minimum, bool)
            or not isinstance(minimum, int)
            or minimum > 1
            or isinstance(maximum, bool)
            or not isinstance(maximum, int)
            or maximum < MAX_LIMIT
        ):
            raise CocoIndexCapabilityError(
                f"search.limit must accept 1..{MAX_LIMIT}; schema minimum={minimum!r} "
                f"maximum={maximum!r}"
            )
        offset = properties["offset"]
        if not isinstance(offset, Mapping) or offset.get("type") != "integer":
            raise CocoIndexCapabilityError("search.offset must be an integer schema")
        offset_minimum = offset.get("minimum")
        if (
            isinstance(offset_minimum, bool)
            or not isinstance(offset_minimum, int)
            or offset_minimum > 0
        ):
            raise CocoIndexCapabilityError("search.offset must accept a non-negative offset")
        if "maximum" in offset:
            raise CocoIndexCapabilityError(
                "search.offset must not cap the adapter's non-negative offset range"
            )
        refresh = properties["refresh_index"]
        if not isinstance(refresh, Mapping) or refresh.get("type") != "boolean":
            raise CocoIndexCapabilityError("search.refresh_index must be a boolean schema")

    def _request(self, method: str, params: Mapping[str, Any]) -> Mapping[str, Any]:
        request_id = self._next_id
        self._next_id += 1
        self._send({"jsonrpc": "2.0", "id": request_id, "method": method, "params": dict(params)})
        assert self._reader is not None
        while True:
            try:
                message = self._reader.read(self._deadline)
            except CocoIndexTimeoutError:
                raise
            except CocoIndexUnavailableError as exc:
                process = self._process
                if process is not None:
                    try:
                        process.wait(timeout=1.0)
                    except subprocess.TimeoutExpired:
                        pass
                    raise self._failure(f"{exc.detail} (exit code {process.returncode})") from exc
                raise
            if "id" not in message:
                continue
            if message.get("id") != request_id:
                raise CocoIndexProtocolError(
                    f"MCP response id {message.get('id')!r} does not match request {request_id}"
                )
            if "error" in message:
                error = message.get("error")
                if not isinstance(error, Mapping):
                    raise CocoIndexProtocolError("MCP error must be an object")
                code = error.get("code")
                text = error.get("message")
                raise CocoIndexProtocolError(
                    f"MCP error {code!r}: {sanitize_text(str(text))[:300]}"
                )
            result = message.get("result")
            if not isinstance(result, Mapping):
                raise CocoIndexProtocolError(f"MCP {method} returned no result object")
            return result

    def _send(self, message: Mapping[str, Any]) -> None:
        process = self._process
        if process is None or process.stdin is None:
            raise CocoIndexUnavailableError("the MCP server is not running")
        self._write_all((json.dumps(message) + "\n").encode("utf-8"))

    def _write_all(self, data: bytes) -> None:
        """Write one message without blocking past the session deadline."""
        process = self._process
        if process is None or process.stdin is None:
            raise CocoIndexUnavailableError("the MCP server is not running")
        if os.name != "posix":
            # Windows pipes are not selectable through DefaultSelector. Keep the write on a
            # daemon thread and bound the wait; cleanup kills the process if it stalls.
            error: list[BaseException] = []

            def _write() -> None:
                try:
                    process.stdin.write(data)  # type: ignore[union-attr]
                    process.stdin.flush()  # type: ignore[union-attr]
                except BaseException as exc:  # noqa: BLE001 - re-raised on the caller thread
                    error.append(exc)

            thread = threading.Thread(target=_write, daemon=True)
            thread.start()
            thread.join(max(0.0, self._deadline - time.monotonic()))
            if thread.is_alive():
                raise CocoIndexTimeoutError("timed out writing to the MCP server")
            if error:
                raise self._failure("could not write to the MCP server") from error[0]
            return
        if self._stdin_fd is None:
            raise CocoIndexUnavailableError("the MCP server input pipe is unavailable")
        selector = selectors.DefaultSelector()
        view = memoryview(data)
        try:
            selector.register(self._stdin_fd, selectors.EVENT_WRITE)
            while view:
                remaining = self._deadline - time.monotonic()
                if remaining <= 0.0:
                    raise CocoIndexTimeoutError("timed out writing to the MCP server")
                if not selector.select(remaining):
                    raise CocoIndexTimeoutError("timed out writing to the MCP server")
                try:
                    written = os.write(self._stdin_fd, view[:4_096])
                except BlockingIOError:
                    continue
                except (BrokenPipeError, OSError) as exc:
                    raise self._failure("could not write to the MCP server") from exc
                if written <= 0:
                    raise self._failure("the MCP server input pipe closed")
                view = view[written:]
        finally:
            selector.close()

    def search(self, request: CocoIndexSearchRequest) -> CocoIndexRawSearch:
        result = self._request(
            "tools/call",
            {
                "name": "search",
                "arguments": {
                    "query": request.query,
                    "limit": request.limit,
                    "offset": request.offset,
                    "refresh_index": request.refresh_index,
                    "languages": list(request.languages) or None,
                    "paths": list(request.paths) or None,
                },
            },
        )
        if result.get("isError") is True:
            raise CocoIndexProtocolError(self._error_text(result))
        payload = self._payload(result, request)
        return CocoIndexRawSearch(payload=payload, server=self.server)

    @staticmethod
    def _error_text(result: Mapping[str, Any]) -> str:
        content = result.get("content")
        if isinstance(content, list):
            for item in content:
                if isinstance(item, Mapping) and item.get("type") == "text":
                    text = item.get("text")
                    if isinstance(text, str):
                        return f"the search tool reported an error: {sanitize_text(text)[:300]}"
        return "the search tool reported an error"

    def _payload(
        self, result: Mapping[str, Any], request: CocoIndexSearchRequest
    ) -> Mapping[str, Any]:
        structured_present = "structuredContent" in result
        structured: Mapping[str, Any] | None = None
        if structured_present:
            raw_structured = result["structuredContent"]
            if not isinstance(raw_structured, Mapping):
                raise CocoIndexProtocolError("structuredContent must be an object when present")
            structured = raw_structured

        content_present = "content" in result
        text_payload: Mapping[str, Any] | None = None
        if content_present:
            content = result["content"]
            if not isinstance(content, list) or not content:
                raise CocoIndexProtocolError(
                    "the search result content must be a non-empty list when present"
                )
            texts: list[str] = []
            for item in content:
                if not isinstance(item, Mapping):
                    raise CocoIndexProtocolError("the search content contains a non-object item")
                if item.get("type") != "text":
                    raise CocoIndexProtocolError("the search content contains a non-text block")
                text = item.get("text")
                if not isinstance(text, str):
                    raise CocoIndexProtocolError("the search text content is not a string")
                texts.append(text)
            if len(texts) != 1:
                raise CocoIndexProtocolError(
                    "the search result must carry exactly one text content block"
                )
            raw = texts[0].encode("utf-8")
            if len(raw) > self._max_response_bytes:
                raise CocoIndexProtocolError(
                    f"the search payload exceeds {self._max_response_bytes} bytes"
                )
            try:
                parsed = json.loads(texts[0])
            except json.JSONDecodeError as exc:
                raise CocoIndexProtocolError("the search text content is not valid JSON") from exc
            if not isinstance(parsed, Mapping):
                raise CocoIndexProtocolError("the search payload must be a JSON object")
            text_payload = parsed

        structured_payload = (
            structured if isinstance(structured, Mapping) and "success" in structured else None
        )
        if structured_present and structured_payload is None:
            raise CocoIndexProtocolError(
                "structuredContent must carry a search payload when present"
            )
        if text_payload is not None and structured_payload is not None:
            # Every supplied representation must be valid and agree. Strict JSON comparison keeps
            # Python's True == 1 from masking an invalid text payload behind valid structured data.
            if not _same_json(text_payload, structured_payload):
                raise CocoIndexProtocolError("the text content and structuredContent disagree")
        # Validate every supplied representation independently; numeric equality must not let a
        # float line/count in one representation hide behind an exact integer in the other.
        for supplied in (text_payload, structured_payload):
            if supplied is not None:
                normalize_search_payload(supplied, request, server=self.server)
        if structured_payload is not None:
            return structured_payload
        if text_payload is not None:
            return text_payload
        raise CocoIndexProtocolError("the search result carries no structured search payload")
