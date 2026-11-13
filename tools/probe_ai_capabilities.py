#!/usr/bin/env python3
"""Report optional AI provider configuration and, only with ``--live``, probe the endpoint.

Without ``--live`` this command reads the process environment, prints a redacted summary, and
makes no network request. With ``--live`` it sends synthetic canary text only. Reports written by
``--live`` may contain local endpoint details; write them outside the repository (the default
refuses a path inside the repository unless ``--allow-repo-report`` is explicit).
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from app.discovery.ai import sanitize_capability_report
from app.settings import Settings, SettingsError, load_settings


def _utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def _offline_summary(settings: Settings, reason: str) -> dict[str, Any]:
    summary = {
        "schema_version": "1",
        "generated_at": _utc_now(),
        "probed": False,
        "reason": reason,
        "mode": settings.ai_mode,
        "llm": {
            "configured": settings.llm_base_url is not None and settings.llm_model is not None,
            "model": settings.llm_model,
            "api_key_present": settings.llm_api_key_present,
        },
        "embeddings": {
            "configured": settings.embeddings_configured,
            "model": settings.embed_model,
            "api_key_present": settings.embed_api_key_present,
        },
        "vector_backend": settings.vector_backend,
        "live_tests_enabled": settings.ai_live_tests,
        "limits": {
            "configured_timeout_seconds": 10.0,
            "configured_max_retries": 1,
            "retry_after_cap_seconds": 5.0,
            "concurrency_limit": "unknown",
        },
    }
    return sanitize_capability_report(
        summary, secrets=(settings.llm_api_key, settings.embed_api_key)
    )


def _write_report(path: Path, report: dict[str, Any]) -> None:
    resolved = path.expanduser().resolve()
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"report written to {resolved}", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--live",
        action="store_true",
        help="contact the configured endpoint with synthetic canary text (default: no network)",
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="write the JSON report; live reports should live outside the repository",
    )
    parser.add_argument(
        "--allow-repo-report",
        action="store_true",
        help="allow writing a report inside the repository (only sanitized content is produced)",
    )
    parser.add_argument(
        "--compact", action="store_true", help="print compact JSON instead of indented JSON"
    )
    args = parser.parse_args(argv)

    try:
        settings = load_settings()
    except SettingsError as exc:
        print(f"configuration error: {exc}", file=sys.stderr)
        return 2

    if not args.live:
        report = _offline_summary(
            settings, "no probe requested; pass --live to contact the configured endpoint"
        )
    else:
        if settings.ai_mode != "live":
            print(
                "configuration error: --live requires CTA_AI_MODE=live; fake mode never contacts "
                "an endpoint",
                file=sys.stderr,
            )
            return 2
        # Imported only on the live path so the offline command never imports the transport.
        from app.discovery.capabilities import probe_capabilities

        report = probe_capabilities(settings)
        print(
            "live probe used synthetic canary text only; the report may contain local endpoint "
            "details and must not be committed without owner review",
            file=sys.stderr,
        )

    # Apply the same sanitizer to every output path, including the offline summary. The offline
    # path must not rely on the live probe module for redaction.
    report = sanitize_capability_report(
        report, secrets=(settings.llm_api_key, settings.embed_api_key)
    )

    if args.report is not None:
        resolved_report = args.report.expanduser().resolve()
        if (
            resolved_report.is_relative_to(settings.repo_root.resolve())
            and not args.allow_repo_report
        ):
            print(
                "configuration error: refusing to write a capability report inside the "
                "repository; choose a path outside it or pass --allow-repo-report after "
                "reviewing the sanitized content",
                file=sys.stderr,
            )
            return 2
        _write_report(resolved_report, report)

    indent = None if args.compact else 2
    print(json.dumps(report, indent=indent, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
