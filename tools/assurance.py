#!/usr/bin/env python3
"""M4 assurance CLI: evaluate a pinned revision and compare finding sets.

Examples::

    uv run --project backend python tools/assurance.py evaluate \
        --baseline baseline-b --report "$RUNNER_TEMP/report.json" \
        --manifest "$RUNNER_TEMP/manifest.json" --summary "$GITHUB_STEP_SUMMARY"
    uv run --project backend python tools/assurance.py self-assure \
        --tested-commit <sha> --cucumber-report <ndjson> --metadata <json> ...
    uv run --project backend python tools/assurance.py diff \
        --previous a.json --current b.json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from app.assurance.reporting import (
    PORTABLE_RULES,
    REQUIREMENT_RULES,
    canonical_json,
    compare_reports,
    digest_bytes,
    evaluator_revision,
    incomplete_report,
    load_report,
    refusal_diagnostic,
    requirement_inputs,
    requirement_report,
    resolve_event_revision,
    self_report,
    write_atomic,
    write_report,
)
from app.assurance.rules import DeterministicAssuranceEvaluator
from app.domain.assurance_report import (
    AssuranceReport,
    AssuranceScope,
    Coverage,
    ExecutionReportProvenance,
    FailureStage,
    ReportInput,
    SourceDigest,
)
from app.domain.enums import ReviewState
from app.domain.errors import ReportsNotComparable
from app.domain.portable import ExecutionImportRequest
from app.persistence.ingested import IngestedStore
from app.persistence.portable import PortableRegistry
from app.settings import Settings

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_FIXTURES = REPO_ROOT / "fixtures"


def _deny_external_network() -> None:
    """Reject non-loopback Python socket connections for this invocation."""
    import socket

    original = socket.socket.connect

    def guarded(sock, address):  # type: ignore[no-untyped-def]
        host = address[0] if isinstance(address, tuple) else str(address)
        if host not in {"127.0.0.1", "::1", "localhost"}:
            raise OSError("external network access denied by --deny-network")
        return original(sock, address)

    socket.socket.connect = guarded  # type: ignore[method-assign]


class _CliFailure(RuntimeError):
    def __init__(self, detail: str, *, stage: FailureStage, code: str) -> None:
        super().__init__(detail)
        self.stage = stage
        self.code = code


def _generated_at(value: str | None) -> datetime:
    if value is None:
        return datetime.now(UTC)
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError("--generated-at must be timezone-aware")
    return parsed


def _settings(args: argparse.Namespace) -> Settings:
    return Settings(
        repo_root=REPO_ROOT,
        fixtures_dir=args.fixture_root.resolve(),
        fixture=args.repository,
        fixture_repo_path=args.fixture_repo.resolve() if args.fixture_repo else None,
    )


def _outside(path: Path, roots: tuple[Path, ...]) -> None:
    resolved = path.expanduser().resolve()
    for root in roots:
        root = root.resolve()
        if resolved == root or resolved.is_relative_to(root):
            raise _CliFailure(
                f"report destination must be outside the evaluated repository/fixture: {resolved}",
                stage=FailureStage.WRITE,
                code="report-path-inside-evaluated",
            )


def _summary(path: Path, lines: list[str]) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text("utf-8") if path.is_file() else ""
    path.write_text(existing + "\n".join(lines) + "\n", encoding="utf-8")


def _normalize_uris(path: Path, *, cucumber_root: Path, repo_root: Path, state_dir: Path) -> Path:
    """Normalize report-relative source URIs onto the evaluated checkout."""
    target = state_dir / f"normalized-{path.name}"
    state_dir.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    for line in path.read_text("utf-8").splitlines():
        if not line.strip():
            continue
        envelope = json.loads(line)
        for key in ("source", "gherkinDocument", "pickle"):
            payload = envelope.get(key)
            if isinstance(payload, dict) and isinstance(payload.get("uri"), str):
                candidate = (cucumber_root / payload["uri"]).resolve()
                try:
                    payload["uri"] = candidate.relative_to(repo_root.resolve()).as_posix()
                except ValueError:
                    pass
        definition = envelope.get("stepDefinition")
        if isinstance(definition, dict):
            reference = definition.get("sourceReference")
            if isinstance(reference, dict) and isinstance(reference.get("uri"), str):
                candidate = (cucumber_root / reference["uri"]).resolve()
                try:
                    reference["uri"] = candidate.relative_to(repo_root.resolve()).as_posix()
                except ValueError:
                    pass
        lines.append(json.dumps(envelope))
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


def _diagnostic(
    report: AssuranceReport, report_path: Path | None, manifest_path: Path | None
) -> int:
    payload = canonical_json(report) + "\n"
    if report_path is not None and manifest_path is not None:
        try:
            write_report(report, report_path, manifest_path)
            return 2
        except OSError:
            pass
    print(payload, file=sys.stderr)
    return 2


def _evaluate(args: argparse.Namespace) -> int:
    if args.deny_network:
        _deny_external_network()
    settings: Settings | None = None
    commit: str | None = None
    try:
        settings = _settings(args)
        _outside(args.report, (settings.fixture_repo, settings.fixtures_dir))
        _outside(args.manifest, (settings.fixture_repo, settings.fixtures_dir))
        store = IngestedStore.from_settings(settings)
        canonical = store.resolve_baseline(args.baseline)
        commit = store.commit_of(canonical)
        findings = DeterministicAssuranceEvaluator(store).evaluate(canonical)
        artifacts = store.list_artifacts(canonical)
        accepted = store.list_links(canonical, review_state=ReviewState.ACCEPTED)
        proposed = store.list_links(canonical, review_state=ReviewState.PROPOSED)
        evidence = store.list_evidence(canonical)
        historical: dict[str, ReportInput] = {}
        for row in evidence:
            if row.tested_commit in historical:
                continue
            try:
                tested = store.artifacts_at(row.tested_commit)
            except Exception:  # noqa: BLE001 - an unreadable historical commit is recorded absent
                continue
            historical[row.tested_commit] = ReportInput(
                kind="historical_artifact",
                id=row.tested_commit,
                revision=row.tested_commit,
                digest=digest_bytes(
                    canonical_json(
                        [artifact.model_dump(mode="json") for artifact in tested]
                    ).encode()
                ),
            )
        inputs = requirement_inputs(
            commit=commit,
            artifacts=artifacts,
            accepted_links=accepted,
            proposed_links=proposed,
            evidence=evidence,
            historical_inputs=historical.values(),
            fixture_manifest_digest=digest_bytes(settings.baselines_manifest_path.read_bytes()),
        )
        report = requirement_report(
            repository=settings.fixture,
            baseline=canonical,
            evaluated_revision=commit,
            evaluator_revision_value=args.evaluator_revision or evaluator_revision(REPO_ROOT),
            findings=findings,
            inputs=inputs,
            run_id=args.run_id,
            generated_at=_generated_at(args.generated_at),
        )
        try:
            write_report(report, args.report, args.manifest)
        except OSError as exc:
            raise _CliFailure(
                f"report destination is unwritable: {exc}",
                stage=FailureStage.WRITE,
                code="report-unwritable",
            ) from exc
        _summary(
            args.summary,
            [
                "# Assurance report",
                f"- scope: {report.scope.value}",
                f"- repository: {report.repository}",
                f"- baseline: {report.baseline}",
                f"- evaluated revision: {report.evaluated_revision}",
                f"- evaluator revision: {report.evaluator_revision}",
                f"- findings: {len(report.findings)}",
                f"- report digest: {report.report_digest}",
            ],
        )
        return 0
    except _CliFailure as exc:
        report = incomplete_report(
            scope=AssuranceScope.REQUIREMENT_ASSURANCE,
            repository=getattr(args, "repository", "banking-demo"),
            identity_strategy="fixture",
            baseline=getattr(args, "baseline", None),
            evaluated_revision=commit,
            evaluator_revision_value=args.evaluator_revision or evaluator_revision(REPO_ROOT),
            rule_scope=REQUIREMENT_RULES,
            inputs=[],
            reason=str(exc),
            stage=exc.stage,
            code=exc.code,
            run_id=args.run_id,
            generated_at=_generated_at(args.generated_at),
        )
        return _diagnostic(report, args.report, args.manifest)
    except Exception as exc:  # noqa: BLE001 - tool failures become incomplete diagnostics
        report = incomplete_report(
            scope=AssuranceScope.REQUIREMENT_ASSURANCE,
            repository=getattr(args, "repository", "banking-demo"),
            identity_strategy="fixture",
            baseline=getattr(args, "baseline", None),
            evaluated_revision=commit,
            evaluator_revision_value=args.evaluator_revision or evaluator_revision(REPO_ROOT),
            rule_scope=REQUIREMENT_RULES,
            inputs=[],
            reason=f"{type(exc).__name__}: {exc}",
            stage=FailureStage.RESOLUTION if commit is None else FailureStage.INPUT,
            code="revision-unknown" if commit is None else "input-unreadable",
            run_id=args.run_id,
            generated_at=_generated_at(args.generated_at),
        )
        return _diagnostic(report, args.report, args.manifest)


def _self_assure(args: argparse.Namespace) -> int:
    if args.deny_network:
        _deny_external_network()
    registry = PortableRegistry()
    tested_commit: str | None = None
    try:
        report_path = args.cucumber_report.expanduser().resolve()
        if not report_path.is_file():
            raise _CliFailure(
                f"execution report is missing: {report_path}",
                stage=FailureStage.INPUT,
                code="execution-report-missing",
            )
        _outside(args.report, (args.repo_root,))
        _outside(args.manifest, (args.repo_root,))
        report_path = _normalize_uris(
            report_path,
            cucumber_root=args.cucumber_root.resolve(),
            repo_root=args.repo_root.resolve(),
            state_dir=args.state_dir.resolve(),
        )
        metadata = args.metadata
        if metadata is None:
            metadata = args.state_dir / "report.meta.json"
            metadata.parent.mkdir(parents=True, exist_ok=True)
            metadata.write_text(
                json.dumps(
                    {"repository_id": args.repository_id, "tested_commit": args.tested_commit}
                ),
                encoding="utf-8",
            )
        metadata = metadata.expanduser().resolve()
        if not metadata.is_file():
            raise _CliFailure(
                f"execution-report provenance sidecar is missing: {metadata}",
                stage=FailureStage.INPUT,
                code="provenance-missing",
            )
        summary = registry.index(
            args.repo_root,
            repository_id=args.repository_id,
            revision=args.tested_commit,
        )
        tested_commit = summary.revision
        snapshot = registry.snapshot(args.repository_id, tested_commit)
        report_data, _ = registry.import_report(
            args.repository_id,
            ExecutionImportRequest(
                report_path=str(report_path),
                metadata_path=str(metadata),
                tested_commit=tested_commit,
            ),
        )
        indexed = {feature.path: feature.content_hash for feature in snapshot.features}
        for uri, digest in report_data.sources:
            if indexed.get(uri) != digest:
                raise _CliFailure(
                    f"execution report source {uri!r} does not match the indexed feature bytes",
                    stage=FailureStage.REPORT_PARSE,
                    code="report-provenance-mismatch",
                )
        findings, _ = registry.findings(args.repository_id, tested_commit)
        coverage_data = registry.coverage(args.repository_id, tested_commit)
        coverage = Coverage(
            available=True,
            features_indexed=len(snapshot.features),
            features_covered_by_report=len({uri for uri, _ in report_data.sources}),
            scenarios_total=coverage_data.scenarios_total,
            scenarios_executed=coverage_data.scenarios_executed,
            scenarios_skipped=0,
            scenarios_unknown=coverage_data.scenarios_without_execution,
            diagnostics=[diagnostic.code for diagnostic in snapshot.diagnostics],
        )
        execution = ExecutionReportProvenance(
            report_digest=report_data.report_digest,
            tested_commit=tested_commit,
            adapter=report_data.adapter,
            sources=[SourceDigest(path=uri, digest=digest) for uri, digest in report_data.sources],
            metadata_digest=digest_bytes(metadata.read_bytes()),
        )
        inputs = [
            ReportInput(
                kind="execution_report",
                path=str(report_path),
                revision=tested_commit,
                digest=digest_bytes(report_path.read_bytes()),
            ),
            ReportInput(
                kind="provenance_sidecar",
                path=str(metadata),
                revision=tested_commit,
                digest=digest_bytes(metadata.read_bytes()),
            ),
            *[
                ReportInput(
                    kind="feature",
                    path=path,
                    revision=tested_commit,
                    digest=digest,
                )
                for path, digest in sorted(indexed.items())
            ],
            ReportInput(
                kind="policy",
                id="default",
                digest=digest_bytes(b'{"policy":"default","policy_version":"1"}'),
            ),
        ]
        report = self_report(
            repository=args.repository_id,
            tested_commit=tested_commit,
            evaluator_revision_value=args.evaluator_revision or evaluator_revision(REPO_ROOT),
            findings=findings,
            inputs=inputs,
            coverage=coverage,
            execution_report=execution,
            run_id=args.run_id,
            generated_at=_generated_at(args.generated_at),
        )
        try:
            write_report(report, args.report, args.manifest)
        except OSError as exc:
            raise _CliFailure(
                f"report destination is unwritable: {exc}",
                stage=FailureStage.WRITE,
                code="report-unwritable",
            ) from exc
        _summary(
            args.summary,
            [
                "# Self-assurance report",
                f"- scope: {report.scope.value}",
                f"- repository: {report.repository}",
                f"- evaluated revision: {report.evaluated_revision}",
                f"- evaluator revision: {report.evaluator_revision}",
                f"- findings: {len(report.findings)}",
                f"- execution report digest: {report.execution_report.report_digest}",
            ],
        )
        return 0
    except _CliFailure as exc:
        report = incomplete_report(
            scope=AssuranceScope.GHERKIN_EXECUTABILITY,
            repository=args.repository_id,
            identity_strategy="explicit",
            baseline=None,
            evaluated_revision=tested_commit,
            evaluator_revision_value=args.evaluator_revision or evaluator_revision(REPO_ROOT),
            rule_scope=PORTABLE_RULES,
            inputs=[],
            reason=str(exc),
            stage=exc.stage,
            code=exc.code,
            run_id=args.run_id,
            generated_at=_generated_at(args.generated_at),
        )
        return _diagnostic(report, args.report, args.manifest)
    except Exception as exc:  # noqa: BLE001 - tool failures become incomplete diagnostics
        report = incomplete_report(
            scope=AssuranceScope.GHERKIN_EXECUTABILITY,
            repository=args.repository_id,
            identity_strategy="explicit",
            baseline=None,
            evaluated_revision=tested_commit,
            evaluator_revision_value=args.evaluator_revision or evaluator_revision(REPO_ROOT),
            rule_scope=PORTABLE_RULES,
            inputs=[],
            reason=f"{type(exc).__name__}: {exc}",
            stage=FailureStage.REPORT_PARSE,
            code="report-malformed",
            run_id=args.run_id,
            generated_at=_generated_at(args.generated_at),
        )
        return _diagnostic(report, args.report, args.manifest)


def _diff(args: argparse.Namespace) -> int:
    try:
        previous = load_report(args.previous, side="previous")
        current = load_report(args.current, side="current")
        diff = compare_reports(previous, current)
    except ReportsNotComparable as exc:
        print(canonical_json(refusal_diagnostic(exc)), file=sys.stdout)
        return 2
    if args.output:
        write_atomic(args.output, canonical_json(diff) + "\n")
    print(canonical_json(diff))
    _summary(
        args.summary,
        [
            "# Findings diff",
            f"- previous revision: {diff.previous_revision}",
            f"- current revision: {diff.current_revision}",
            f"- new: {diff.counts.new}",
            f"- unchanged: {diff.counts.unchanged}",
            f"- resolved: {diff.counts.resolved}",
        ],
    )
    return 0


def _resolve(args: argparse.Namespace) -> int:
    try:
        event = json.loads(args.event.read_text("utf-8"))
        print(resolve_event_revision(event))
        return 0
    except Exception as exc:  # noqa: BLE001 - a resolution failure is a tool failure
        print(json.dumps({"code": "revision-unknown", "reason": str(exc)}), file=sys.stderr)
        return 2


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="assurance")
    sub = parser.add_subparsers(dest="command", required=True)
    evaluate = sub.add_parser("evaluate")
    evaluate.add_argument("--repository", default="banking-demo")
    evaluate.add_argument("--baseline", required=True)
    evaluate.add_argument("--fixture-root", type=Path, default=DEFAULT_FIXTURES)
    evaluate.add_argument("--fixture-repo", type=Path)
    evaluate.add_argument("--report", type=Path, required=True)
    evaluate.add_argument("--manifest", type=Path, required=True)
    evaluate.add_argument("--summary", type=Path)
    evaluate.add_argument("--evaluator-revision")
    evaluate.add_argument("--run-id")
    evaluate.add_argument("--generated-at")
    evaluate.add_argument("--deny-network", action="store_true")
    evaluate.set_defaults(func=_evaluate)

    self_assure = sub.add_parser("self-assure")
    self_assure.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    self_assure.add_argument("--repository-id", required=True)
    self_assure.add_argument("--tested-commit", required=True)
    self_assure.add_argument("--cucumber-report", type=Path, required=True)
    self_assure.add_argument("--cucumber-root", type=Path, default=REPO_ROOT)
    self_assure.add_argument("--metadata", type=Path)
    self_assure.add_argument("--state-dir", type=Path, default=Path(".cta"))
    self_assure.add_argument("--report", type=Path, required=True)
    self_assure.add_argument("--manifest", type=Path, required=True)
    self_assure.add_argument("--summary", type=Path)
    self_assure.add_argument("--evaluator-revision")
    self_assure.add_argument("--run-id")
    self_assure.add_argument("--generated-at")
    self_assure.add_argument("--deny-network", action="store_true")
    self_assure.set_defaults(func=_self_assure)

    diff = sub.add_parser("diff")
    diff.add_argument("--previous", type=Path, required=True)
    diff.add_argument("--current", type=Path, required=True)
    diff.add_argument("--output", type=Path)
    diff.add_argument("--summary", type=Path)
    diff.set_defaults(func=_diff)

    resolve = sub.add_parser("resolve-revision")
    resolve.add_argument("--event", type=Path, required=True)
    resolve.set_defaults(func=_resolve)
    return parser


def main() -> int:
    args = _parser().parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
