#!/usr/bin/env python3
"""Fixture tooling for Continuous Traceability Assurance.

Commands (run from the repository root with the backend environment):

    uv run --project backend python tools/fixturectl.py build
    uv run --project backend python tools/fixturectl.py materialize
    uv run --project backend python tools/fixturectl.py all
    uv run --project backend python tools/fixturectl.py verify

``build`` creates the nested fixture Git repository from the declarative history in
``fixtures/banking-demo/history.json`` and writes ``expected/baselines.json``.
``materialize`` writes ``fixtures/api-responses/`` (snapshot, sample findings responses,
thread responses, discovery responses) from the built repository plus the hand-labeled oracle.
``verify`` does both into a temporary directory, compares against the committed files, and
exits non-zero on drift (used by CI and the drift test).

Reproducibility contract: fixed author/committer identity, dates, messages, and branch
contents, so the commit SHAs are identical on every machine and git version. If a fixture
content edit changes them, ``verify`` fails on purpose and a human decides to regenerate.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel

from app.discovery.fake import FakeCandidateDiscovery, compute_index_revision
from app.domain.api import DiscoveryResponse
from app.domain.enums import ArtifactType
from app.domain.models import AssuranceFinding, make_finding
from app.domain.oracle import (
    BaselineCommit,
    BaselinesManifest,
    BaselineSnapshot,
    CandidateIndexFile,
    ExpectedFindingsFile,
    FixtureHistory,
    FixtureSnapshot,
    MaterializedFindings,
)
from app.ingestion import GitRepository, IngestionError, assemble_thread
from app.ingestion.evidence import load_evidence as ingest_evidence
from app.ingestion.links import load_links as ingest_links
from app.ingestion.scan import scan_artifacts as scan_revision_artifacts
from app.persistence.fixtures import load_model
from app.version import SCHEMA_VERSION

REPO_ROOT = Path(__file__).resolve().parents[1]
FIXTURE_NAME = "banking-demo"
FIXTURE_DIR = REPO_ROOT / "fixtures" / FIXTURE_NAME
BUILD_DIR = FIXTURE_DIR / ".build"
REPO_DIR = BUILD_DIR / "repo"
EXPECTED_DIR = FIXTURE_DIR / "expected"
API_DIR = REPO_ROOT / "fixtures" / "api-responses"

GENERATED_BY = "tools/fixturectl.py"

GIT_IDENTITY = {
    "GIT_AUTHOR_NAME": "CTA Fixture Bot",
    "GIT_AUTHOR_EMAIL": "fixture@example.invalid",
    "GIT_COMMITTER_NAME": "CTA Fixture Bot",
    "GIT_COMMITTER_EMAIL": "fixture@example.invalid",
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_SYSTEM": os.devnull,
    # Pin the object format: without this the generator inherits GIT_DEFAULT_HASH from the caller's
    # environment and every baseline SHA changes (review finding R5).
    "GIT_DEFAULT_HASH": "sha1",
    "LC_ALL": "C",
    "TZ": "UTC",
}
GIT_FLAGS = (
    "-c",
    "core.autocrlf=false",
    "-c",
    "commit.gpgsign=false",
    "-c",
    "core.fileMode=true",
)

TOKEN_RE = re.compile(r"\{\{([A-Za-z0-9_:\-.]+)\}\}")

ModelT = TypeVar("ModelT", bound=BaseModel)


class FixtureToolError(RuntimeError):
    """Tooling failure with a human-readable explanation."""


# ----------------------------------------------------------------------------------------
# Git plumbing
# ----------------------------------------------------------------------------------------


def git(args: Iterable[str], *, cwd: Path, env_extra: dict[str, str] | None = None) -> str:
    result = subprocess.run(
        ["git", *GIT_FLAGS, *args],
        cwd=cwd,
        env={**os.environ, **GIT_IDENTITY, **(env_extra or {})},
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise FixtureToolError(
            f"git {' '.join(args)} failed in {cwd} (exit {result.returncode}):\n"
            f"{result.stderr.decode('utf-8', 'replace').strip()}"
        )
    return result.stdout.decode("utf-8", "replace").strip()


def git_blob(repo: Path, commit: str, path: str) -> bytes:
    result = subprocess.run(
        ["git", *GIT_FLAGS, "cat-file", "blob", f"{commit}:{path}"],
        cwd=repo,
        env={**os.environ, **GIT_IDENTITY},
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise FixtureToolError(f"cannot read {commit}:{path}:\n{result.stderr.decode().strip()}")
    return result.stdout


# ----------------------------------------------------------------------------------------
# Overlays and tokens
# ----------------------------------------------------------------------------------------


def discovery_tokens(expected_dir: Path) -> dict[str, str]:
    index = load_model(expected_dir / "candidate-links.json", CandidateIndexFile)
    return {
        "DISCOVERY_PROVIDER": index.provider,
        "DISCOVERY_MODEL_VERSION": index.model_version,
        "DISCOVERY_INDEX_REVISION": compute_index_revision(index),
    }


def render_tokens(text: str, tokens: dict[str, str], *, where: Path) -> str:
    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in tokens:
            available = ", ".join(sorted(tokens)) or "none"
            raise FixtureToolError(
                f"{where}: unknown token {{{{{key}}}}}. Available tokens: {available}"
            )
        return tokens[key]

    return TOKEN_RE.sub(replace, text)


def copy_overlay(src_dir: Path, dest_dir: Path, tokens: dict[str, str]) -> list[str]:
    """Copy an overlay tree over the work tree, rendering tokens in every text file."""
    if not src_dir.is_dir():
        raise FixtureToolError(f"overlay directory '{src_dir}' does not exist")
    written: list[str] = []
    for source in sorted(path for path in src_dir.rglob("*") if path.is_file()):
        relative = source.relative_to(src_dir)
        target = dest_dir / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            text = source.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:  # pragma: no cover - fixture overlays are text
            raise FixtureToolError(f"{source} is not UTF-8 text: {exc}") from exc
        target.write_text(render_tokens(text, tokens, where=source), encoding="utf-8")
        written.append(str(relative))
    return written


# ----------------------------------------------------------------------------------------
# Building the nested repository
# ----------------------------------------------------------------------------------------


def build_repo(fixture_dir: Path, dest: Path) -> BaselinesManifest:
    history = load_model(fixture_dir / "history.json", FixtureHistory)
    tokens = discovery_tokens(fixture_dir / "expected")
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    git(["init", "-q"], cwd=dest)
    git(["symbolic-ref", "HEAD", "refs/heads/main"], cwd=dest)

    commits: list[BaselineCommit] = []
    for spec in history.commits:
        tokens.update({f"COMMIT:{commit.id}": commit.commit for commit in commits})
        copy_overlay(fixture_dir / spec.overlay, dest, tokens)
        git(["add", "-A"], cwd=dest)
        git(
            ["commit", "-q", "--no-gpg-sign", "-m", spec.message],
            cwd=dest,
            env_extra={
                "GIT_AUTHOR_DATE": spec.date.isoformat(),
                "GIT_COMMITTER_DATE": spec.date.isoformat(),
            },
        )
        sha = git(["rev-parse", "HEAD"], cwd=dest)
        for tag in spec.tags:
            git(["tag", tag], cwd=dest)
        commits.append(
            BaselineCommit(
                id=spec.id,
                commit=sha,
                date=spec.date,
                message=spec.message,
                tags=list(spec.tags),
            )
        )

    return BaselinesManifest(
        schema_version=SCHEMA_VERSION,
        fixture=history.fixture,
        generated_by=GENERATED_BY,
        commits=commits,
        tags={tag: commit.commit for commit in commits for tag in commit.tags},
    )


# ----------------------------------------------------------------------------------------
# Scanning artifacts out of a revision
# ----------------------------------------------------------------------------------------


# ----------------------------------------------------------------------------------------
# Snapshot, findings, threads
# ----------------------------------------------------------------------------------------


def build_snapshot(manifest: BaselinesManifest, repo: Path) -> FixtureSnapshot:
    baselines: list[BaselineSnapshot] = []
    repository = GitRepository(repo)
    for tag, commit in manifest.tags.items():
        artifacts = scan_revision_artifacts(repository, commit, repository_name=manifest.fixture)
        by_id = {artifact.artifact_id: artifact for artifact in artifacts}
        accepted, proposed = ingest_links(repository, commit, artifacts=by_id)
        baselines.append(
            BaselineSnapshot(
                baseline=tag,
                commit=commit,
                artifacts=artifacts,
                accepted_links=accepted,
                proposed_links=proposed,
                evidence=ingest_evidence(repository, commit, artifacts=by_id),
            )
        )
    return FixtureSnapshot(
        schema_version=SCHEMA_VERSION,
        fixture=manifest.fixture,
        generated_by=GENERATED_BY,
        baselines=baselines,
    )


def stamp_findings(
    expected: ExpectedFindingsFile, baseline: BaselineSnapshot
) -> list[AssuranceFinding]:
    evidence_ids = {item.evidence_id for item in baseline.evidence}
    findings: list[AssuranceFinding] = []
    for item in expected.findings:
        revisions: dict[str, str] = {}
        for artifact_id in item.artifact_ids:
            artifact = baseline.artifact(artifact_id)
            if artifact is None:
                raise FixtureToolError(
                    f"{expected.baseline}: oracle finding {item.finding_type} references unknown "
                    f"artifact {artifact_id}"
                )
            revisions[artifact_id] = artifact.revision
        unknown_evidence = sorted(set(item.evidence_ids) - evidence_ids)
        if unknown_evidence:
            raise FixtureToolError(
                f"{expected.baseline}: oracle finding {item.finding_type} references unknown "
                f"evidence {unknown_evidence}"
            )
        findings.append(
            make_finding(
                rule_id=item.rule_id,
                finding_type=item.finding_type,
                severity=item.severity,
                artifact_ids=item.artifact_ids,
                evaluated_baseline=baseline.commit,
                explanation=item.explanation,
                evidence_ids=item.evidence_ids,
                artifact_revisions=revisions,
                status=item.status,
            )
        )
    return findings


# ----------------------------------------------------------------------------------------
# Writing and comparing generated files
# ----------------------------------------------------------------------------------------


def dump_model(model: BaseModel) -> str:
    return json.dumps(model.model_dump(mode="json"), indent=2, ensure_ascii=False) + "\n"


def write_json(path: Path, model: BaseModel) -> bool:
    payload = dump_model(model)
    if path.exists() and path.read_text(encoding="utf-8") == payload:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(payload, encoding="utf-8")
    return True


def materialize(
    *,
    repo: Path,
    manifest: BaselinesManifest,
    expected_dir: Path,
    api_dir: Path,
) -> list[Path]:
    """Write the fixture-backed API responses; returns the paths written, in order."""
    written: list[Path] = []
    snapshot = build_snapshot(manifest, repo)
    snapshot_path = api_dir / "snapshot.json"
    if write_json(snapshot_path, snapshot):
        written.append(snapshot_path)

    for baseline in snapshot.baselines:
        expected = load_model(expected_dir / f"{baseline.baseline}.json", ExpectedFindingsFile)
        if expected.baseline != baseline.baseline:
            raise FixtureToolError(
                f"{expected_dir / f'{baseline.baseline}.json'} declares baseline "
                f"{expected.baseline!r}, expected {baseline.baseline!r}"
            )
        findings_path = api_dir / f"findings.{baseline.baseline}.json"
        if write_json(
            findings_path,
            MaterializedFindings(
                schema_version=SCHEMA_VERSION,
                baseline=baseline.baseline,
                findings=stamp_findings(expected, baseline),
            ),
        ):
            written.append(findings_path)

        for artifact in baseline.artifacts:
            if artifact.artifact_type is not ArtifactType.REQUIREMENT:
                continue
            thread_path = api_dir / "threads" / f"{artifact.artifact_id}.{baseline.baseline}.json"
            thread = assemble_thread(
                root_id=artifact.artifact_id,
                baseline=baseline.baseline,
                artifacts=baseline.artifacts,
                accepted_links=baseline.accepted_links,
                proposed_links=baseline.proposed_links,
                evidence=baseline.evidence,
            )
            if write_json(thread_path, thread):
                written.append(thread_path)

    provider = FakeCandidateDiscovery.from_fixture(expected_dir / "candidate-links.json")
    index = load_model(expected_dir / "candidate-links.json", CandidateIndexFile)
    for artifact_id in sorted({candidate.source_id for candidate in index.candidates}):
        discovery_path = api_dir / f"discovery.{artifact_id}.json"
        if write_json(
            discovery_path,
            DiscoveryResponse(
                schema_version=SCHEMA_VERSION,
                artifact_id=artifact_id,
                provider=provider.provider_name,
                model_version=provider.model_version,
                index_revision=provider.index_revision,
                candidates=provider.discover(artifact_id, top_k=50),
            ),
        ):
            written.append(discovery_path)

    return written


def iter_json(root: Path) -> Iterator[Path]:
    return iter(sorted(path for path in root.rglob("*.json") if path.is_file()))


def compare_tree(committed: Path, generated: Path) -> list[str]:
    """Report drift between a committed directory and a freshly generated one."""
    problems: list[str] = []
    committed_files = {path.relative_to(committed) for path in iter_json(committed)}
    generated_files = {path.relative_to(generated) for path in iter_json(generated)}
    for missing in sorted(generated_files - committed_files):
        problems.append(f"missing from the repository: {committed / missing}")
    for extra in sorted(committed_files - generated_files):
        problems.append(f"no longer generated (stale file): {committed / extra}")
    for relative in sorted(committed_files & generated_files):
        expected_text = (committed / relative).read_text(encoding="utf-8")
        actual_text = (generated / relative).read_text(encoding="utf-8")
        if expected_text != actual_text:
            problems.append(f"out of date: {committed / relative}")
    return problems


def compare_file(committed: Path, generated: Path) -> list[str]:
    """Compare a single generated file, handling absence explicitly.

    A directory walker cannot verify a file: passed two file paths it enumerates nothing and
    reports success. The baseline manifest is a single file, so it needs this comparison
    (review finding R3).
    """
    if not committed.is_file():
        return [f"missing from the repository: {committed}"]
    if committed.read_text(encoding="utf-8") != generated.read_text(encoding="utf-8"):
        return [f"out of date: {committed}"]
    return []


# ----------------------------------------------------------------------------------------
# Commands
# ----------------------------------------------------------------------------------------


def command_build(*, quiet: bool = False) -> BaselinesManifest:
    manifest = build_repo(FIXTURE_DIR, REPO_DIR)
    changed = write_json(EXPECTED_DIR / "baselines.json", manifest)
    if not quiet:
        for commit in manifest.commits:
            tags = f"  tags: {', '.join(commit.tags)}" if commit.tags else ""
            print(f"{commit.commit[:12]}  {commit.id}{tags}")
        print(
            f"wrote {EXPECTED_DIR / 'baselines.json'}"
            + (" (updated)" if changed else " (unchanged)")
        )
    return manifest


def command_materialize(*, quiet: bool = False) -> list[Path]:
    if not REPO_DIR.exists():
        raise FixtureToolError("fixture repository is missing; run 'fixturectl.py build' first")
    manifest = build_repo(FIXTURE_DIR, REPO_DIR)
    write_json(EXPECTED_DIR / "baselines.json", manifest)
    written = materialize(
        repo=REPO_DIR, manifest=manifest, expected_dir=EXPECTED_DIR, api_dir=API_DIR
    )
    if not quiet:
        for path in written:
            print(f"wrote {path.relative_to(REPO_ROOT)}")
        print(f"{len(written)} generated file(s) changed")
    return written


def command_verify(*, api_dir: Path | None = None, baselines_path: Path | None = None) -> int:
    committed_api = api_dir or API_DIR
    committed_baselines = baselines_path or (EXPECTED_DIR / "baselines.json")
    with tempfile.TemporaryDirectory(prefix="cta-fixture-verify-") as temporary:
        scratch = Path(temporary)
        manifest = build_repo(FIXTURE_DIR, scratch / "repo")
        generated_baselines = scratch / "baselines.json"
        write_json(generated_baselines, manifest)
        generated_api = scratch / "api"
        materialize(
            repo=scratch / "repo",
            manifest=manifest,
            expected_dir=EXPECTED_DIR,
            api_dir=generated_api,
        )
        problems = compare_file(committed_baselines, generated_baselines)
        problems += compare_tree(committed_api, generated_api)

    if problems:
        print("Generated fixture files are out of date:", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        print(
            "\nRegenerate and commit with:\n"
            "  uv run --project backend python tools/fixturectl.py all\n",
            file=sys.stderr,
        )
        return 1

    print(f"fixture generation is reproducible and committed files are current ({FIXTURE_NAME})")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="fixturectl",
        description="Build, materialize, and verify the CTA fixture repository.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("build", help="build the nested fixture repository + baselines.json")
    subparsers.add_parser("materialize", help="write fixtures/api-responses/*")
    subparsers.add_parser("all", help="build then materialize")
    verify_parser = subparsers.add_parser("verify", help="fail if generated files are stale")
    verify_parser.add_argument(
        "--api-dir",
        type=Path,
        default=None,
        help="compare against this directory instead of fixtures/api-responses",
    )
    verify_parser.add_argument(
        "--baselines",
        type=Path,
        default=None,
        help="compare against this manifest instead of expected/baselines.json",
    )
    args = parser.parse_args(argv)

    try:
        if args.command == "build":
            command_build()
            return 0
        if args.command == "materialize":
            command_materialize()
            return 0
        if args.command == "all":
            command_build()
            command_materialize()
            return 0
        return command_verify(api_dir=args.api_dir, baselines_path=args.baselines)
    except (FixtureToolError, IngestionError) as exc:
        print(f"fixturectl: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
