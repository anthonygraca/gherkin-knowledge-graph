#!/usr/bin/env python3
"""Capability probe for the optional CocoIndex Code adapter (AI-06, synthetic text only).

Without ``--live`` this command reads the process environment and prints a summary. It starts no
process, accesses no CocoIndex index, and makes no request. With ``--live`` it runs the configured
``ccc`` diagnostics, the MCP capability handshake, one bounded search, and an Ollama availability
check. A live report can contain local paths and endpoint details: write it outside the repository,
or use ``--sanitized-report`` for the reduced record that is safe to commit.

A missing configuration or endpoint is ``NOT RUN``/unavailable, never a pass. A configured but
failing step makes the probe exit non-zero.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from app.discovery.cocoindex import (
    CocoIndexError,
    CocoIndexSearchClient,
    verify_hits_against_snapshot,
)
from app.discovery.cocoindex_mcp import (
    DEFAULT_CLEANUP_SECONDS,
    StdioMcpTransport,
    child_environment,
    validate_isolated_state,
)
from app.settings import Settings, SettingsError, load_settings

SCHEMA_VERSION = "1"
DEFAULT_OLLAMA_TIMEOUT = 90.0
ADAPTER_FILES = (
    "backend/app/discovery/cocoindex.py",
    "backend/app/discovery/cocoindex_mcp.py",
    "tools/probe_cocoindex.py",
)


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _sha256_file(path: Path, *, limit: int = 512 * 1_024 * 1_024) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        while chunk := handle.read(1_048_576):
            size += len(chunk)
            if size > limit:
                return {"method": "unavailable", "reason": "index file exceeds hash limit"}
            digest.update(chunk)
    return {
        "method": "sha256 of the project-local index file, computed outside the MCP contract",
        "sha256": f"sha256:{digest.hexdigest()}",
        "bytes": size,
        "modified_at": datetime.fromtimestamp(path.stat().st_mtime, UTC)
        .isoformat()
        .replace("+00:00", "Z"),
    }


def _run_command(
    command: list[str],
    *,
    cwd: Path | None,
    timeout: float,
    env: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    started = time.monotonic()
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=dict(env) if env is not None else child_environment(),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        return {
            "status": "failed",
            "detail": f"executable not found: {command[0]}",
            "latency_ms": round((time.monotonic() - started) * 1_000, 1),
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "timeout",
            "detail": f"no result within {timeout:.0f}s",
            "latency_ms": round((time.monotonic() - started) * 1_000, 1),
        }
    except OSError as exc:
        return {
            "status": "failed",
            "detail": f"could not run {command[0]}: {exc.strerror or exc}",
            "latency_ms": round((time.monotonic() - started) * 1_000, 1),
        }
    stdout = completed.stdout.strip()
    stderr = completed.stderr.strip()
    return {
        "status": "ok" if completed.returncode == 0 else "failed",
        "exit_code": completed.returncode,
        "latency_ms": round((time.monotonic() - started) * 1_000, 1),
        "stdout_tail": stdout[-1_500:],
        "stderr_tail": stderr[-1_500:],
    }


def _ccc_state_dir() -> Path:
    override = os.environ.get("COCOINDEX_CODE_DIR")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".cocoindex_code"


def _read_ccc_settings() -> dict[str, Any]:
    path = _ccc_state_dir() / "global_settings.yml"
    if not path.is_file():
        return {"present": False, "path": str(path)}
    try:
        parsed = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:
        return {"present": True, "path": str(path), "error": str(exc)}
    embedding = parsed.get("embedding") if isinstance(parsed, dict) else None
    envs = parsed.get("envs") if isinstance(parsed, dict) else None
    model = embedding.get("model") if isinstance(embedding, dict) else None
    provider = embedding.get("provider") if isinstance(embedding, dict) else None
    ollama_base = envs.get("OLLAMA_API_BASE") if isinstance(envs, dict) else None
    return {
        "present": True,
        "path": str(path),
        "sha256": _sha256_file(path)["sha256"] if path.is_file() else None,
        "embedding_provider": provider,
        "embedding_model": model,
        "ollama_base_url": ollama_base,
    }


def _endpoint_class(url: str | None) -> str:
    if not url:
        return "unconfigured"
    try:
        host = urllib.parse.urlsplit(url).hostname or ""
    except ValueError:
        return "invalid"
    if host in {"localhost", "127.0.0.1", "::1"}:
        return "localhost"
    if host.endswith(".svc.cluster.local"):
        return "cluster"
    return "other"


def _http_json(
    url: str, *, payload: dict[str, Any] | None, timeout: float
) -> tuple[dict[str, Any] | None, str | None]:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = urllib.request.Request(
        url, data=data, headers=headers, method="POST" if data else "GET"
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8")), None
    except urllib.error.HTTPError as exc:
        return None, f"HTTP {exc.code}"
    except urllib.error.URLError as exc:
        return None, f"transport error: {exc.reason}"
    except TimeoutError:
        return None, f"timeout after {timeout:.0f}s"
    except json.JSONDecodeError:
        return None, "response was not JSON"
    except OSError as exc:
        return None, f"transport error: {exc.strerror or exc}"


def _probe_ollama(base_url: str, model: str | None, *, timeout: float) -> dict[str, Any]:
    started = time.monotonic()
    if not model:
        return {"status": "not_run", "detail": "no embedding model in the CocoIndex settings"}
    # CocoIndex stores a LiteLLM model string (for example ``ollama/<tag>``); Ollama's native
    # API takes the bare tag. Record both so the translation is visible, not assumed.
    native_model = model.split("/", 1)[1] if model.startswith("ollama/") else model
    tags, error = _http_json(f"{base_url.rstrip('/')}/api/tags", payload=None, timeout=timeout)
    if tags is None:
        return {"status": "failed", "detail": error, "endpoint_class": _endpoint_class(base_url)}
    names = [
        item.get("name")
        for item in tags.get("models", [])
        if isinstance(item, dict) and isinstance(item.get("name"), str)
    ]
    observed = next(
        (item for item in tags.get("models", []) if item.get("name") == native_model), None
    )
    if observed is None:
        return {
            "status": "unavailable",
            "detail": f"model {native_model!r} is not installed",
            "configured_model": model,
            "endpoint_class": _endpoint_class(base_url),
            "installed_models": sorted(names),
            "latency_ms": round((time.monotonic() - started) * 1_000, 1),
        }
    embed, error = _http_json(
        f"{base_url.rstrip('/')}/api/embed",
        payload={"model": native_model, "input": "CTA synthetic CocoIndex capability canary"},
        timeout=timeout,
    )
    if embed is None:
        return {
            "status": "failed",
            "detail": error,
            "configured_model": model,
            "endpoint_class": _endpoint_class(base_url),
            "latency_ms": round((time.monotonic() - started) * 1_000, 1),
        }
    vectors = embed.get("embeddings")
    dimension = len(vectors[0]) if isinstance(vectors, list) and vectors else 0
    return {
        "status": "ok",
        "configured_model": model,
        "endpoint_class": _endpoint_class(base_url),
        "model": embed.get("model", native_model),
        "dimension": dimension,
        "vector_count": len(vectors) if isinstance(vectors, list) else 0,
        "latency_ms": round((time.monotonic() - started) * 1_000, 1),
        "digest": observed.get("digest"),
        "size_bytes": observed.get("size"),
    }


def _snapshot_provenance(settings: Settings, root: Path) -> dict[str, Any]:
    revision = _run_command(["git", "-C", str(root), "rev-parse", "HEAD"], cwd=None, timeout=15)
    status = _run_command(["git", "-C", str(root), "status", "--porcelain"], cwd=None, timeout=15)
    dirty = False
    if status.get("status") == "ok":
        dirty = any(
            line and not line.startswith("?? .cocoindex_code/")
            for line in status.get("stdout_tail", "").splitlines()
        )
    adapter_revision = _run_command(
        ["git", "-C", str(settings.repo_root), "rev-parse", "HEAD"], cwd=None, timeout=15
    )
    index_file = root / ".cocoindex_code" / "target_sqlite.db"
    settings_file = root / ".cocoindex_code" / "settings.yml"
    adapter_hashes = {
        path: (_sha256_file(settings.repo_root / path) or {}).get("sha256")
        for path in ADAPTER_FILES
    }
    return {
        "snapshot_revision": revision.get("stdout_tail")
        if revision.get("status") == "ok"
        else None,
        "snapshot_dirty": dirty,
        "index_snapshot": _sha256_file(index_file),
        "project_settings_sha256": (_sha256_file(settings_file) or {}).get("sha256"),
        "adapter_revision": (
            adapter_revision.get("stdout_tail") if adapter_revision.get("status") == "ok" else None
        ),
        "adapter_file_hashes": adapter_hashes,
    }


def _configuration_summary(settings: Settings) -> dict[str, Any]:
    executable_found = None
    if settings.ccc_executable:
        executable_found = shutil.which(settings.ccc_executable) or (
            settings.ccc_executable
            if Path(settings.ccc_executable).expanduser().is_file()
            else None
        )
    return {
        "live_opt_in": settings.cocoindex_live_opt_in,
        "live_tests_enabled": settings.ccc_live_tests,
        "executable": settings.ccc_executable,
        "executable_found": executable_found is not None,
        "project_root_configured": settings.ccc_project_root is not None,
        "project_root": str(settings.ccc_project_root) if settings.ccc_project_root else None,
        "project_marker_present": bool(
            settings.ccc_project_root
            and (settings.ccc_project_root / ".cocoindex_code" / "settings.yml").is_file()
        ),
    }


def _lifecycle_state(root: Path, runtime: Path) -> dict[str, Any]:
    pid_path = runtime / "daemon.pid"
    daemon_pid: int | None = None
    try:
        daemon_pid = int(pid_path.read_text(encoding="utf-8").strip())
    except (FileNotFoundError, OSError, ValueError):
        daemon_pid = None
    index_file = root / ".cocoindex_code" / "target_sqlite.db"
    snapshot = _sha256_file(index_file)
    return {
        "daemon_pid": daemon_pid,
        "index_sha256": (snapshot or {}).get("sha256"),
        "index_bytes": (snapshot or {}).get("bytes"),
    }


def _overall_status(steps: Mapping[str, Mapping[str, Any]], *, search_required: bool) -> str:
    required = [
        "ccc_version",
        "ccc_status",
        "ccc_doctor",
        "mcp_capabilities",
        "ollama",
    ]
    if search_required:
        required.append("search")
    for name in required:
        if steps.get(name, {}).get("status") != "ok":
            return "failed"
    for step in steps.values():
        if step.get("status") in {"failed", "timeout", "unavailable"}:
            return "failed"
    return "ok"


def _probe_live(settings: Settings, args: argparse.Namespace) -> dict[str, Any]:
    assert settings.ccc_project_root is not None
    root = settings.ccc_project_root
    report: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _utc_now(),
        "probed": True,
        "overall": "ok",
        "configuration": _configuration_summary(settings),
        "provenance": {},
        "steps": {},
        "observed": {},
        "missing_capabilities": [],
        "limitations": [],
    }
    try:
        provided_environment = child_environment()
        state_dir, runtime_dir = validate_isolated_state(provided_environment)
    except CocoIndexError as exc:
        report["overall"] = "failed"
        report["steps"]["isolation"] = {
            "status": "failed",
            "detail": f"{exc.code}: {exc.detail}",
        }
        report["missing_capabilities"] = [f"isolation: {exc.code}: {exc.detail}"]
        report["limitations"] = [
            "ccc mcp may start a daemon and always schedules its own background index; "
            "CTA refuses the shared default state, so no live step was run."
        ]
        return report
    isolated_environment = {
        **provided_environment,
        "COCOINDEX_CODE_DIR": str(state_dir),
        "COCOINDEX_CODE_RUNTIME_DIR": str(runtime_dir),
    }
    report["provenance"] = _snapshot_provenance(settings, root)
    report["configuration"]["isolated_state"] = str(state_dir)
    report["configuration"]["isolated_runtime"] = str(runtime_dir)
    lifecycle_before = _lifecycle_state(root, runtime_dir)
    report["lifecycle"] = {"before": lifecycle_before}
    steps = report["steps"]
    ccc = settings.ccc_executable
    steps["ccc_version"] = _run_command(
        [ccc, "version"], cwd=root, timeout=20, env=isolated_environment
    )
    steps["ccc_status"] = _run_command(
        [ccc, "status"], cwd=root, timeout=45, env=isolated_environment
    )
    steps["ccc_doctor"] = _run_command(
        [ccc, "doctor"], cwd=root, timeout=30, env=isolated_environment
    )

    raw_payload: dict[str, Any] | None = None
    try:
        transport = StdioMcpTransport(
            executable=ccc,
            project_root=root,
            timeout=args.timeout,
            cleanup_timeout=DEFAULT_CLEANUP_SECONDS,
            environment=isolated_environment,
        )
        capabilities = transport.capabilities(timeout=args.timeout)
        tool = capabilities.search_tool()
        report["observed"]["server"] = capabilities.server.model_dump()
        report["observed"]["tool"] = {
            "name": tool.name,
            "properties": sorted((tool.input_schema.get("properties") or {}).keys()),
            "required": tool.input_schema.get("required"),
        }
        steps["mcp_capabilities"] = {
            "status": "ok",
            "detail": f"{capabilities.server.name} {capabilities.server.version}",
        }
        if not args.query:
            steps["search"] = {"status": "not_run", "detail": "--query not supplied"}
        else:
            client = CocoIndexSearchClient(transport)
            started = time.monotonic()

            def capture(payload: dict[str, Any]) -> None:
                nonlocal raw_payload
                raw_payload = payload

            result = client.search(
                args.query,
                limit=args.limit,
                refresh_index=args.refresh_index,
                languages=tuple(args.language or ()),
                paths=tuple(args.path or ()),
                timeout=args.timeout,
                capture=capture,
            )
            verify_hits_against_snapshot(root, result.hits)
            report["observed"]["search"] = {
                "query": args.query,
                "limit": args.limit,
                "refresh_index": args.refresh_index,
                "languages": sorted(args.language or []),
                "paths": sorted(args.path or []),
                "hit_count": len(result.hits),
                "total_returned": result.total_returned,
                "latency_ms": round((time.monotonic() - started) * 1_000, 1),
                "hits": [
                    {
                        "path": hit.path,
                        "language": hit.language,
                        "start_line": hit.start_line,
                        "end_line": hit.end_line,
                        "score": hit.score,
                        "content_bytes": len(hit.content.encode("utf-8")),
                        "content_sha256": (
                            f"sha256:{hashlib.sha256(hit.content.encode('utf-8')).hexdigest()}"
                        ),
                        "snapshot_content_sha256": (_sha256_file(root / hit.path) or {}).get(
                            "sha256"
                        ),
                    }
                    for hit in result.hits
                ],
                "index_identity": result.index_identity,
            }
            if result.hits:
                steps["search"] = {
                    "status": "ok",
                    "detail": f"{len(result.hits)} hit(s) verified against the snapshot",
                }
            else:
                steps["search"] = {
                    "status": "failed",
                    "detail": "the smoke search returned no hits; an empty result is a valid "
                    "adapter result but not a live smoke acceptance",
                }
            if raw_payload is not None and args.capture_response:
                _write_json(
                    args.capture_response,
                    {"captured_at": _utc_now(), "payload": raw_payload},
                    settings=settings,
                    allow_repo=False,
                )
    except CocoIndexError as exc:
        if "mcp_capabilities" not in steps:
            steps["mcp_capabilities"] = {
                "status": "failed",
                "detail": f"{exc.code}: {exc.detail}",
            }
        if args.query:
            steps["search"] = {"status": "failed", "detail": f"{exc.code}: {exc.detail}"}
    except OSError as exc:
        steps["mcp_capabilities"] = {"status": "failed", "detail": str(exc)}

    ccc_settings = _read_ccc_settings()
    report["cocoindex_settings"] = {
        key: value for key, value in ccc_settings.items() if key != "path"
    }
    base_url = (
        args.ollama_base_url
        or ccc_settings.get("ollama_base_url")
        or os.environ.get("OLLAMA_API_BASE")
        or "http://localhost:11434"
    )
    report["steps"]["ollama"] = _probe_ollama(
        str(base_url), ccc_settings.get("embedding_model"), timeout=args.ollama_timeout
    )

    lifecycle_after = _lifecycle_state(root, runtime_dir)
    before = lifecycle_before
    report["lifecycle"] = {
        "before": before,
        "after": lifecycle_after,
        "daemon_started_by_session": before["daemon_pid"] is None
        and lifecycle_after["daemon_pid"] is not None,
        "daemon_restarted_by_session": before["daemon_pid"] is not None
        and lifecycle_after["daemon_pid"] != before["daemon_pid"],
        "index_changed_by_session": before["index_sha256"] != lifecycle_after["index_sha256"],
        "background_index_note": (
            "ccc mcp starts its own asynchronous index update on session startup; "
            "refresh_index=false only suppresses the tool's explicit refresh. The effect is "
            "confined to the isolated state and the configured disposable snapshot."
        ),
    }
    report["overall"] = _overall_status(steps, search_required=bool(args.query))
    for name, step in steps.items():
        if step.get("status") in {"failed", "timeout", "unavailable", "not_run"}:
            if name == "search" and not args.query:
                continue
            report["missing_capabilities"].append(f"{name}: {step.get('detail') or step['status']}")
    report["limitations"] = [
        "CocoIndex Code 0.2.43 does not report an index revision over MCP; index identity is "
        "reported as unavailable and an external index-file hash is recorded separately.",
        "The MCP include patterns cover code and text files, not .feature scenario parsing.",
        "A synthetic single-snapshot smoke is a capability observation, not retrieval quality.",
        "ccc mcp schedules its own background index on startup and may start/restart a daemon; "
        "CTA confines this to an isolated COCOINDEX_CODE_DIR/RUNTIME_DIR pair.",
    ]
    return report


def _write_json(
    path: Path, payload: dict[str, Any], *, settings: Settings, allow_repo: bool
) -> Path:
    resolved = path.expanduser().resolve()
    if resolved.is_relative_to(settings.repo_root.resolve()) and not allow_repo:
        raise SystemExit(
            f"refusing to write a raw probe report inside the repository: {resolved}; "
            "use --allow-repo-report only for sanitized content"
        )
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return resolved


def _scrub(value: Any, replacements: dict[str, str]) -> Any:
    if isinstance(value, str):
        scrubbed = value
        for old, new in replacements.items():
            scrubbed = scrubbed.replace(old, new)
        return re.sub(r"https?://\S+", "<endpoint>", scrubbed)
    if isinstance(value, list):
        return [_scrub(item, replacements) for item in value]
    if isinstance(value, dict):
        return {key: _scrub(item, replacements) for key, item in value.items()}
    return value


def _sanitized(report: dict[str, Any], settings: Settings) -> dict[str, Any]:
    provenance = report.get("provenance", {})
    observed = report.get("observed", {})
    steps = {
        name: {
            key: value
            for key, value in step.items()
            if key in {"status", "exit_code", "latency_ms", "detail"}
        }
        for name, step in report.get("steps", {}).items()
    }
    search = observed.get("search")
    if isinstance(search, dict):
        search = {key: value for key, value in search.items() if key != "query"}
    sanitized = {
        "schema_version": report.get("schema_version"),
        "generated_at": report.get("generated_at"),
        "probed": report.get("probed"),
        "overall": report.get("overall"),
        "configuration": {
            "live_opt_in": report.get("configuration", {}).get("live_opt_in"),
            "live_tests_enabled": report.get("configuration", {}).get("live_tests_enabled"),
            "executable_found": report.get("configuration", {}).get("executable_found"),
            "project_marker_present": report.get("configuration", {}).get("project_marker_present"),
            "project_root": "<snapshot>"
            if report.get("configuration", {}).get("project_root_configured")
            else None,
        },
        "provenance": {
            "snapshot_revision": provenance.get("snapshot_revision"),
            "snapshot_dirty": provenance.get("snapshot_dirty"),
            "index_snapshot": provenance.get("index_snapshot"),
            "project_settings_sha256": provenance.get("project_settings_sha256"),
            "adapter_revision": provenance.get("adapter_revision"),
            "adapter_file_hashes": provenance.get("adapter_file_hashes"),
        },
        "steps": steps,
        "lifecycle": report.get("lifecycle"),
        "observed": {
            "server": observed.get("server"),
            "tool": observed.get("tool"),
            "search": search,
            "embedding_model": report.get("cocoindex_settings", {}).get("embedding_model"),
            "embedding_provider": report.get("cocoindex_settings", {}).get("embedding_provider"),
        },
        "missing_capabilities": report.get("missing_capabilities", []),
        "limitations": report.get("limitations", []),
    }
    replacements = {
        str(settings.repo_root): "<repository>",
        str(Path.home()): "<home>",
    }
    if settings.ccc_project_root is not None:
        replacements[str(settings.ccc_project_root)] = "<snapshot>"
    return _scrub(sanitized, replacements)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--live", action="store_true", help="contact the configured CocoIndex project"
    )
    parser.add_argument("--query", help="synthetic search query; omit to probe capabilities only")
    parser.add_argument("--limit", type=int, default=5)
    parser.add_argument("--language", action="append", help="language filter (repeatable)")
    parser.add_argument("--path", action="append", help="relative path glob filter (repeatable)")
    parser.add_argument(
        "--refresh-index", action="store_true", help="let CocoIndex update the index"
    )
    parser.add_argument("--timeout", type=float, default=180.0, help="per MCP operation deadline")
    parser.add_argument("--ollama-timeout", type=float, default=DEFAULT_OLLAMA_TIMEOUT)
    parser.add_argument("--ollama-base-url", help="override the embedding endpoint for the probe")
    parser.add_argument(
        "--report", type=Path, help="raw JSON report; write it outside the repository"
    )
    parser.add_argument("--sanitized-report", type=Path, help="reduced JSON report safe to commit")
    parser.add_argument(
        "--allow-repo-report",
        action="store_true",
        help="allow a raw report inside the repository",
    )
    parser.add_argument("--capture-response", type=Path, help="raw structured search payload")
    args = parser.parse_args(argv)

    try:
        settings = load_settings()
    except SettingsError as exc:
        print(f"probe_cocoindex: configuration error: {exc}", file=sys.stderr)
        return 2

    if not args.live:
        report = {
            "schema_version": SCHEMA_VERSION,
            "generated_at": _utc_now(),
            "probed": False,
            "overall": "NOT RUN",
            "reason": "--live not supplied",
            "configuration": _configuration_summary(settings),
            "steps": {
                "ccc_version": {"status": "not_run"},
                "ccc_status": {"status": "not_run"},
                "ccc_doctor": {"status": "not_run"},
                "mcp_capabilities": {"status": "not_run"},
                "search": {"status": "not_run"},
                "ollama": {"status": "not_run"},
            },
        }
    elif not settings.cocoindex_live_opt_in:
        report = {
            "schema_version": SCHEMA_VERSION,
            "generated_at": _utc_now(),
            "probed": False,
            "overall": "NOT RUN",
            "reason": "CTA_CCC_LIVE_OPT_IN is not enabled",
            "configuration": _configuration_summary(settings),
            "steps": {"search": {"status": "not_run"}},
        }
    else:
        report = _probe_live(settings, args)

    if args.report:
        resolved = _write_json(
            args.report, report, settings=settings, allow_repo=args.allow_repo_report
        )
        print(f"raw report: {resolved}", file=sys.stderr)
    if args.sanitized_report:
        resolved = _write_json(
            args.sanitized_report, _sanitized(report, settings), settings=settings, allow_repo=True
        )
        print(f"sanitized report: {resolved}", file=sys.stderr)

    summary = {
        "overall": report.get("overall"),
        "probed": report.get("probed"),
        "steps": {name: step.get("status") for name, step in report.get("steps", {}).items()},
    }
    print(json.dumps(summary, sort_keys=True))
    return 1 if report.get("overall") == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
