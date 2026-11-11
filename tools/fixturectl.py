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
from typing import Any, TypeVar

from pydantic import BaseModel

from app.discovery.fake import FakeCandidateDiscovery, compute_index_revision
from app.domain.api import DiscoveryResponse, ThreadResponse
from app.domain.enums import ArtifactType, ReviewState
from app.domain.models import (
    Artifact,
    AssuranceFinding,
    TraceLink,
    VerificationEvidence,
    make_finding,
)
from app.domain.oracle import (
    BaselineCommit,
    BaselinesManifest,
    BaselineSnapshot,
    CandidateIndexFile,
    ExpectedFindingsFile,
    FixtureEvidenceFile,
    FixtureHistory,
    FixtureLinkFile,
    FixtureSnapshot,
    MaterializedFindings,
)
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

EVIDENCE_PATH = "evidence/verification-runs.json"
ACCEPTED_LINKS_PATH = "evidence/accepted-links.json"
PROPOSED_LINKS_PATH = "evidence/proposed-links.json"

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
ANNOTATION_RE = re.compile(r"^#\s*cta:artifact\s+((?:CODE|TEST)-\d{3})\s*$", re.MULTILINE)
SCENARIO_TAG_RE = re.compile(r"^@(SCN-\d{3})$")
SCENARIO_LINE_RE = re.compile(r"^\s*Scenario:\s*(\S.*?)\s*$")

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


def parse_front_matter(text: str, *, where: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        raise FixtureToolError(
            f"{where}: expected a '---' front matter block at the start of the file"
        )
    end = text.find("\n---\n", 3)
    if end == -1:
        raise FixtureToolError(f"{where}: front matter block is not terminated by '---'")
    fields: dict[str, str] = {}
    for line in text[4:end].splitlines():
        if not line.strip():
            continue
        key, separator, value = line.partition(":")
        if not separator:
            raise FixtureToolError(f"{where}: unusable front matter line {line!r}")
        fields[key.strip()] = value.strip()
    return fields


def parse_scenarios(text: str, *, where: str) -> list[tuple[str, str]]:
    """Return (scenario_id, title) pairs for ``@SCN-nnn`` tagged scenarios."""
    found: list[tuple[str, str]] = []
    pending: str | None = None
    for line in text.splitlines():
        tag = SCENARIO_TAG_RE.match(line.strip())
        if tag:
            pending = tag.group(1)
            continue
        if pending is None:
            continue
        match = SCENARIO_LINE_RE.match(line)
        if match:
            found.append((pending, match.group(1)))
            pending = None
    if pending is not None:
        raise FixtureToolError(f"{where}: tag @{pending} is not followed by a 'Scenario:' line")
    return found


def scan_artifacts(repo: Path, commit: str, repository: str) -> list[Artifact]:
    listed = git(["ls-tree", "-r", "--name-only", commit], cwd=repo).splitlines()
    artifacts: list[Artifact] = []
    for path in sorted(listed):
        blob = git_blob(repo, commit, path)
        content_hash = f"sha256:{__import__('hashlib').sha256(blob).hexdigest()}"
        common: dict[str, Any] = {
            "source_uri": f"fixture://{repository}/{path}",
            "repository": repository,
            "revision": commit,
            "content_hash": content_hash,
        }
        if path.startswith("requirements/") and path.endswith(".md"):
            fields = parse_front_matter(blob.decode("utf-8"), where=f"{commit}:{path}")
            missing = {"id", "title"} - fields.keys()
            if missing:
                raise FixtureToolError(
                    f"{commit}:{path}: missing front matter keys {sorted(missing)}"
                )
            artifacts.append(
                Artifact(
                    artifact_id=fields["id"],
                    artifact_type=ArtifactType.REQUIREMENT,
                    title=fields["title"],
                    locator=path,
                    metadata={"status": fields.get("status", "active")},
                    **common,
                )
            )
        elif path.startswith("features/") and path.endswith(".feature"):
            for scenario_id, title in parse_scenarios(
                blob.decode("utf-8"), where=f"{commit}:{path}"
            ):
                artifacts.append(
                    Artifact(
                        artifact_id=scenario_id,
                        artifact_type=ArtifactType.SCENARIO,
                        title=title,
                        locator=f"{path}#{scenario_id}",
                        **common,
                    )
                )
        elif path.endswith(".py"):
            annotation = ANNOTATION_RE.search(blob.decode("utf-8"))
            if annotation:
                artifact_id = annotation.group(1)
                artifacts.append(
                    Artifact(
                        artifact_id=artifact_id,
                        artifact_type=(
                            ArtifactType.SOURCE
                            if artifact_id.startswith("CODE")
                            else ArtifactType.TEST
                        ),
                        title=path,
                        locator=path,
                        **common,
                    )
                )
    return artifacts


def load_evidence(repo: Path, commit: str) -> list[VerificationEvidence]:
    listed = git(["ls-tree", "-r", "--name-only", commit], cwd=repo).splitlines()
    if EVIDENCE_PATH not in listed:
        return []
    payload = json.loads(git_blob(repo, commit, EVIDENCE_PATH).decode("utf-8"))
    try:
        parsed = FixtureEvidenceFile.model_validate(payload)
    except Exception as exc:
        raise FixtureToolError(
            f"{commit}:{EVIDENCE_PATH} does not satisfy FixtureEvidenceFile:\n{exc}"
        ) from exc
    return list(parsed.runs)


def load_links(repo: Path, commit: str) -> tuple[list[TraceLink], list[TraceLink]]:
    listed = git(["ls-tree", "-r", "--name-only", commit], cwd=repo).splitlines()

    def read(path: str, expected_state: ReviewState) -> list[TraceLink]:
        if path not in listed:
            return []
        payload = json.loads(git_blob(repo, commit, path).decode("utf-8"))
        try:
            parsed = FixtureLinkFile.model_validate(payload)
        except Exception as exc:
            raise FixtureToolError(
                f"{commit}:{path} does not satisfy FixtureLinkFile:\n{exc}"
            ) from exc
        if parsed.review_state != expected_state:
            raise FixtureToolError(
                f"{commit}:{path} declares review_state={parsed.review_state} "
                f"but should be {expected_state}"
            )
        return list(parsed.links)

    accepted = read(ACCEPTED_LINKS_PATH, ReviewState.ACCEPTED)
    proposed = read(PROPOSED_LINKS_PATH, ReviewState.PROPOSED)
    return accepted, proposed


# ----------------------------------------------------------------------------------------
# Snapshot, findings, threads
# ----------------------------------------------------------------------------------------


def build_snapshot(manifest: BaselinesManifest, repo: Path) -> FixtureSnapshot:
    baselines: list[BaselineSnapshot] = []
    for tag, commit in manifest.tags.items():
        accepted, proposed = load_links(repo, commit)
        baselines.append(
            BaselineSnapshot(
                baseline=tag,
                commit=commit,
                artifacts=scan_artifacts(repo, commit, manifest.fixture),
                accepted_links=accepted,
                proposed_links=proposed,
                evidence=load_evidence(repo, commit),
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


def build_thread(baseline: BaselineSnapshot, root_id: str) -> ThreadResponse:
    accepted_by_source: dict[str, list[TraceLink]] = {}
    for link in baseline.accepted_links:
        accepted_by_source.setdefault(link.source_id, []).append(link)

    visited = {root_id}
    frontier = [root_id]
    while frontier:
        following: list[str] = []
        for artifact_id in frontier:
            for link in accepted_by_source.get(artifact_id, []):
                if link.target_id not in visited:
                    visited.add(link.target_id)
                    following.append(link.target_id)
        frontier = following

    return ThreadResponse(
        schema_version=SCHEMA_VERSION,
        root_id=root_id,
        baseline=baseline.baseline,
        artifacts=sorted(
            (a for a in baseline.artifacts if a.artifact_id in visited), key=lambda a: a.artifact_id
        ),
        accepted_links=sorted(
            (
                link
                for link in baseline.accepted_links
                if link.source_id in visited and link.target_id in visited
            ),
            key=lambda link: link.link_id,
        ),
        proposed_links=sorted(
            (
                link
                for link in baseline.proposed_links
                if link.source_id in visited or link.target_id in visited
            ),
            key=lambda link: link.link_id,
        ),
        evidence=sorted(
            (
                item
                for item in baseline.evidence
                if item.scenario_id in visited or item.test_id in visited
            ),
            key=lambda item: item.evidence_id,
        ),
    )


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
            if write_json(thread_path, build_thread(baseline, artifact.artifact_id)):
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
    except FixtureToolError as exc:
        print(f"fixturectl: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
