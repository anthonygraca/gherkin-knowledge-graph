"""Command-line access to the portable repository surface.

Every command prints one JSON document on stdout and exits non-zero on failure. The CLI is a thin
adapter over the same in-process registry the API uses; it deliberately performs no writes to the
indexed repository and no project-code execution.

    python -m app.cli index ../some-repo --repo-id some-repo --ref v1
    python -m app.cli scenarios ../some-repo --repo-id some-repo --ref v1
    python -m app.cli steps ../some-repo --repo-id some-repo --ref v1 --scenario <key>
    python -m app.cli definitions ../some-repo --repo-id some-repo --ref v1 \\
        --report report.ndjson --tested-commit <sha>
    python -m app.cli unresolved ../some-repo --repo-id some-repo --ref v1 \\
        --report report.ndjson --tested-commit <sha>
    python -m app.cli executions ../some-repo --repo-id some-repo --ref v1
    python -m app.cli findings ../some-repo --repo-id some-repo --ref v1

The ref must be a tag or commit in the repository; queries never fall back to another revision.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.domain.portable import (
    BindingResponse,
    ExecutionImportRequest,
    ExecutionListResponse,
    PortableIndexSummary,
    ScenarioListResponse,
    StepListResponse,
)
from app.persistence.portable import PortableRegistry
from app.version import SCHEMA_VERSION


def _registry(args: argparse.Namespace, *, import_report: bool = False) -> PortableRegistry:
    registry = PortableRegistry()
    registry.index(Path(args.path), repository_id=args.repo_id, revision=args.ref)
    if import_report and args.report:
        registry.import_report(
            registry.summaries()[0].repository_id,
            ExecutionImportRequest(
                report_path=args.report,
                metadata_path=args.metadata,
                tested_commit=args.tested_commit or args.ref,
            ),
        )
    return registry


def _repository_id(registry: PortableRegistry) -> str:
    return registry.summaries()[0].repository_id


def _scenarios(args: argparse.Namespace, registry: PortableRegistry) -> ScenarioListResponse:
    snapshot = registry.snapshot(_repository_id(registry), args.ref)
    scenarios = [scenario for feature in snapshot.features for scenario in feature.scenarios]
    if args.tag:
        wanted = f"@{args.tag.lstrip('@')}"
        scenarios = [scenario for scenario in scenarios if wanted in scenario.tags]
    if args.feature_path:
        scenarios = [scenario for scenario in scenarios if scenario.path == args.feature_path]
    return ScenarioListResponse(
        schema_version=SCHEMA_VERSION,
        repository_id=snapshot.repository_id,
        revision=snapshot.revision,
        source_digest=snapshot.source_digest,
        parser=snapshot.parser,
        scenarios=scenarios,
    )


def _steps(args: argparse.Namespace, registry: PortableRegistry) -> StepListResponse:
    snapshot = registry.snapshot(_repository_id(registry), args.ref)
    scenarios = [scenario for feature in snapshot.features for scenario in feature.scenarios]
    if args.scenario:
        scenarios = [scenario for scenario in scenarios if scenario.scenario_key == args.scenario]
    seen: set[str] = set()
    steps = []
    for scenario in scenarios:
        for step in scenario.steps:
            if step.step_key in seen:
                continue
            seen.add(step.step_key)
            steps.append(step)
    return StepListResponse(
        schema_version=SCHEMA_VERSION,
        repository_id=snapshot.repository_id,
        revision=snapshot.revision,
        source_digest=snapshot.source_digest,
        parser=snapshot.parser,
        steps=steps,
    )


def _bindings(args: argparse.Namespace, registry: PortableRegistry) -> BindingResponse:
    snapshot = registry.snapshot(_repository_id(registry), args.ref)
    availability, reason, definitions, resolutions, reports = registry.bindings(
        snapshot.repository_id, snapshot.revision
    )
    return BindingResponse(
        schema_version=SCHEMA_VERSION,
        repository_id=snapshot.repository_id,
        revision=snapshot.revision,
        source_digest=snapshot.source_digest,
        parser=snapshot.parser,
        availability=availability,
        reason=reason,
        adapter=reports[0].adapter if reports else None,
        tested_commit=reports[0].executions[0].tested_commit if reports else None,
        report_uri=reports[0].report_uri if reports else None,
        step_definitions=list(definitions),
        resolutions=list(resolutions),
    )


def _unresolved(args: argparse.Namespace, registry: PortableRegistry) -> BindingResponse:
    response = _bindings(args, registry)
    return response.model_copy(
        update={
            "resolutions": [
                resolution
                for resolution in response.resolutions
                if resolution.status.value in {"undefined", "ambiguous"}
            ]
        }
    )


def _executions(args: argparse.Namespace, registry: PortableRegistry) -> ExecutionListResponse:
    snapshot = registry.snapshot(_repository_id(registry), args.ref)
    executions, _ = registry.executions(snapshot.repository_id, snapshot.revision)
    return ExecutionListResponse(
        schema_version=SCHEMA_VERSION,
        repository_id=snapshot.repository_id,
        revision=snapshot.revision,
        source_digest=snapshot.source_digest,
        parser=snapshot.parser,
        executions=executions,
        coverage=registry.coverage(snapshot.repository_id, snapshot.revision),
        reports=registry.provenance(snapshot.repository_id, snapshot.revision),
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cta", description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(name: str, help_text: str, *, report: bool = False) -> argparse.ArgumentParser:
        command = sub.add_parser(name, help=help_text)
        command.add_argument("path", help="Local repository path (read-only)")
        command.add_argument("--repo-id", default=None, help="Explicit stable repository id")
        command.add_argument("--ref", required=True, help="Pinned tag or commit to index")
        if report:
            command.add_argument("--report", default=None, help="Cucumber Messages NDJSON file")
            command.add_argument(
                "--metadata",
                default=None,
                help="Provenance sidecar naming the tested commit (required with --report)",
            )
            command.add_argument(
                "--tested-commit",
                default=None,
                help="Commit the report tested (defaults to --ref)",
            )
        return command

    add_common("index", "Index one commit and print the summary")
    scenarios = add_common("scenarios", "List scenarios")
    scenarios.add_argument("--tag", default=None)
    scenarios.add_argument("--feature-path", default=None)
    steps = add_common("steps", "List steps")
    steps.add_argument("--scenario", default=None)
    add_common("definitions", "Step definitions and resolutions", report=True)
    add_common("unresolved", "Undefined or ambiguous steps", report=True)
    add_common("executions", "Observed scenario executions", report=True)
    add_common("findings", "Executability findings", report=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    wants_report = getattr(args, "report", None) is not None
    try:
        registry = _registry(args, import_report=wants_report)
        if args.command == "index":
            summary: PortableIndexSummary = registry.summaries()[0]
            payload = summary.model_dump(mode="json")
        elif args.command == "scenarios":
            payload = _scenarios(args, registry).model_dump(mode="json")
        elif args.command == "steps":
            payload = _steps(args, registry).model_dump(mode="json")
        elif args.command == "definitions":
            payload = _bindings(args, registry).model_dump(mode="json")
        elif args.command == "unresolved":
            payload = _unresolved(args, registry).model_dump(mode="json")
        elif args.command == "executions":
            payload = _executions(args, registry).model_dump(mode="json")
        elif args.command == "findings":
            findings, tested_commit = registry.findings(_repository_id(registry), args.ref)
            payload = {
                "schema_version": SCHEMA_VERSION,
                "repository_id": _repository_id(registry),
                "revision": registry.snapshot(_repository_id(registry), args.ref).revision,
                "tested_commit": tested_commit,
                "findings": [finding.model_dump(mode="json") for finding in findings],
            }
        else:  # pragma: no cover - argparse enforces the command set
            raise RuntimeError(f"unhandled command {args.command}")
    except Exception as exc:  # noqa: BLE001 - CLI boundary: report, do not traceback
        print(
            json.dumps(
                {
                    "error": type(exc).__name__,
                    "detail": str(exc),
                    "code": getattr(exc, "code", None),
                },
                indent=2,
            ),
            file=sys.stderr,
        )
        return 2
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
