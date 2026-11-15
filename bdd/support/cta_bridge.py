#!/usr/bin/env python3
"""Cucumber → CTA bridge.

Cucumber-JS step definitions are JavaScript; CTA is Python. Rather than reimplementing the domain
in JavaScript (a second implementation that could drift), every step calls this bridge, which
invokes the real application code and returns one JSON document.

Protocol: one JSON request ``{"op": ..., "args": {...}}`` on stdin, one JSON response on stdout:

    {"ok": true, "result": {...}}          success
    {"ok": false, "error": {"type": ..., "code": ..., "detail": ...}}   domain/expected error

An expected application error (for a negative scenario) is still ``ok: false``: the step definition
asserts it and turns it into a passing scenario. The bridge never edits the repository under test
and never executes anything from an external repository.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
TOOLS = ROOT / "tools"
sys.path.insert(0, str(BACKEND))
sys.path.insert(0, str(TOOLS))

import fixturectl  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.assurance.rules import DeterministicAssuranceEvaluator  # noqa: E402
from app.discovery.registry import ProviderRegistry  # noqa: E402
from app.domain.errors import DomainError  # noqa: E402
from app.domain.portable import ExecutionImportRequest  # noqa: E402
from app.ingestion import GitRepository, ingest_revision  # noqa: E402
from app.main import create_app  # noqa: E402
from app.persistence.ingested import IngestedStore  # noqa: E402
from app.settings import Settings  # noqa: E402

FIXTURE_DIR = ROOT / "fixtures" / "banking-demo"
CACHE = ROOT / "bdd" / ".cache"


def _state_dir() -> Path:
    value = os.environ.get("CTA_BDD_STATE")
    if not value:
        raise RuntimeError("CTA_BDD_STATE is not set; the Cucumber World supplies it")
    path = Path(value)
    path.mkdir(parents=True, exist_ok=True)
    return path


def _state_path() -> Path:
    return _state_dir() / "world.json"


def _load_state() -> dict:
    path = _state_path()
    return json.loads(path.read_text("utf-8")) if path.exists() else {}


def _save_state(state: dict) -> None:
    _state_path().write_text(json.dumps(state, indent=2), encoding="utf-8")


def _fixture_repo() -> Path:
    from app.version import SCHEMA_VERSION

    destination = CACHE / "banking-repo"
    marker = destination / "expected" / "baselines.json"
    version_marker = CACHE / "schema-version.txt"
    current = version_marker.read_text(encoding="utf-8").strip() if version_marker.exists() else ""
    if not marker.exists() or current != SCHEMA_VERSION:
        destination.parent.mkdir(parents=True, exist_ok=True)
        fixturectl.build_repo(FIXTURE_DIR, destination)
        version_marker.write_text(SCHEMA_VERSION, encoding="utf-8")
    return destination


def _settings() -> Settings:
    return Settings(
        repo_root=ROOT, fixtures_dir=ROOT / "fixtures", fixture_repo_path=_fixture_repo()
    )


def _store() -> IngestedStore:
    return IngestedStore.from_settings(_settings())


def _client() -> TestClient:
    return TestClient(create_app(_settings()))


def _fixture_store() -> tuple[IngestedStore, object]:
    store = _store()
    return store, store


def _jsonable(value):
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value


def _repo_path(state: dict, name: str) -> Path:
    path = state.get("repos", {}).get(name)
    if not path:
        raise RuntimeError(f"no repository named {name!r} in this scenario")
    return Path(path)


def _git(repo: Path, *args: str, check: bool = True) -> str:
    result = subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=False)
    if check and result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.strip()}")
    return result.stdout


def _write_files(repo: Path, files: dict[str, str]) -> None:
    for name, content in files.items():
        target = repo / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if content.startswith("SYMLINK:"):
            target.symlink_to(content[len("SYMLINK:") :])
        else:
            target.write_text(content, encoding="utf-8")


def _commit(repo: Path, message: str) -> str:
    if repo.resolve() == ROOT:
        raise RuntimeError("refusing to commit the CTA repository root from the BDD harness")
    _git(repo, "add", "-A")
    _git(repo, "commit", "--quiet", "--allow-empty", "-m", message)
    return _git(repo, "rev-parse", "HEAD").strip()


def op_repo(args: dict) -> dict:
    state = _load_state()
    name = args.get("name", "repo")
    path = _state_dir() / "repos" / name
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)
    _git(path, "init", "--quiet", "-b", "main")
    _git(path, "config", "user.name", "BDD Fixture")
    _git(path, "config", "user.email", "bdd@example.invalid")
    _git(path, "config", "commit.gpgsign", "false")
    _write_files(path, args.get("files", {}))
    commit = _commit(path, args.get("message", "fixture commit"))
    state.setdefault("repos", {})[name] = str(path)
    _save_state(state)
    return {"path": str(path), "commit": commit}


def op_commit(args: dict) -> dict:
    state = _load_state()
    path = _repo_path(state, args.get("name", "repo"))
    _write_files(path, args.get("files", {}))
    commit = _commit(path, args.get("message", "fixture change"))
    state.setdefault("commits", {})[args.get("label", commit)] = commit
    _save_state(state)
    return {"commit": commit}


def op_write(args: dict) -> dict:
    state = _load_state()
    path = _repo_path(state, args.get("name", "repo"))
    _write_files(path, args.get("files", {}))
    return {"path": str(path)}


def op_repo_from_fixture(args: dict) -> dict:
    """Clone the built fixture at one tag into the scenario's state, keeping its history."""
    state = _load_state()
    name = args.get("name", "repo")
    path = _state_dir() / "repos" / name
    if path.exists():
        shutil.rmtree(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    _git(_fixture_repo().parent, "clone", "--quiet", str(_fixture_repo()), str(path))
    _git(path, "checkout", "--quiet", args["tag"])
    _git(path, "config", "user.name", "BDD Fixture")
    _git(path, "config", "user.email", "bdd@example.invalid")
    _git(path, "config", "commit.gpgsign", "false")
    state.setdefault("repos", {})[name] = str(path)
    _save_state(state)
    return {
        "path": str(path),
        "commit": _git(path, "rev-parse", "HEAD").strip(),
        "tags": _git(path, "tag", "--points-at", "HEAD").strip().split(),
    }


def op_blob_text(args: dict) -> dict:
    repository = GitRepository(_fixture_repo())
    return {"text": repository.read_blob(args["revision"], args["path"]).decode("utf-8")}


def op_blob_hash(args: dict) -> dict:
    state = _load_state()
    if "name" in args:
        path = _repo_path(state, args["name"])
    else:
        path = _fixture_repo()
    repository = GitRepository(path)
    blob = repository.read_blob(args["revision"], args["path"])
    import hashlib

    return {"content_hash": f"sha256:{hashlib.sha256(blob).hexdigest()}"}


def op_thread_without_examples(args: dict) -> dict:
    """Serve a thread from a fixtures copy that has no precomputed thread files."""
    state_dir = _state_dir()
    target = state_dir / "fixtures-copy"
    if target.exists():
        shutil.rmtree(target)
    ignore = shutil.ignore_patterns("threads", ".build", "__pycache__")
    shutil.copytree(ROOT / "fixtures", target, ignore=ignore)
    settings = Settings(repo_root=ROOT, fixtures_dir=target, fixture_repo_path=_fixture_repo())
    store = IngestedStore.from_settings(settings)
    thread = store.thread(args["id"], baseline=args.get("baseline"))
    from app.version import SCHEMA_VERSION

    return {"thread": _jsonable(thread), "schema_version": SCHEMA_VERSION}


def op_git(args: dict) -> dict:
    state = _load_state()
    path = _repo_path(state, args.get("name", "repo"))
    output = _git(path, *args.get("args", []), check=False)
    return {"output": output.strip()}


def op_ingest(args: dict) -> dict:
    if "name" in args:
        state = _load_state()
        path = _repo_path(state, args["name"])
        repository = GitRepository(path)
        revision = ingest_revision(
            repository, args.get("revision"), repository_name=args.get("repository", "probe")
        )
    else:
        store = _store()
        revision = store.ingest("banking-demo", args.get("revision"))
    result = {
        "commit": revision.commit,
        "artifact_ids": sorted(artifact.artifact_id for artifact in revision.artifacts),
        "artifacts": _jsonable(revision.artifacts),
        "accepted_links": _jsonable(revision.accepted_links),
        "proposed_links": _jsonable(revision.proposed_links),
        "evidence": _jsonable(revision.evidence),
    }
    state = _load_state()
    state.setdefault("revisions", {})[args.get("label", result["commit"])] = result["commit"]
    _save_state(state)
    return result


def op_artifact(args: dict) -> dict:
    store = _store()
    return {"artifact": _jsonable(store.get_artifact(args["id"], baseline=args.get("baseline")))}


def op_artifacts(args: dict) -> dict:
    store = _store()
    canonical = store.resolve_baseline(args.get("baseline"))
    artifacts = store.list_artifacts(canonical)
    if args.get("type"):
        artifacts = [item for item in artifacts if item.artifact_type.value == args["type"]]
    return {"baseline": canonical, "artifacts": _jsonable(artifacts)}


def op_thread(args: dict) -> dict:
    store = _store()
    return {"thread": _jsonable(store.thread(args["id"], baseline=args.get("baseline")))}


def op_links(args: dict) -> dict:
    store = _store()
    links = store.list_links(store.resolve_baseline(args.get("baseline")))
    return {"links": _jsonable(links)}


def op_link(args: dict) -> dict:
    store = _store()
    links = store.list_links(store.resolve_baseline(args.get("baseline")))
    link = next((item for item in links if item.link_id == args["id"]), None)
    return {"link": _jsonable(link) if link else None}


def op_findings(args: dict) -> dict:
    store = _store()
    evaluator = DeterministicAssuranceEvaluator(store)
    findings = evaluator.evaluate(args["baseline"], policy=args.get("policy"))
    return {"findings": _jsonable(findings), "commit": store.commit_of(args["baseline"])}


def op_api(args: dict) -> dict:
    client = _client()
    setup = args.get("setup_portable") or {}
    registry = client.app.state.portable
    for spec in setup.get("indexes", []):
        registry.index(
            spec["path"], repository_id=spec.get("repository_id"), revision=spec.get("revision")
        )
    for spec in setup.get("reports", []):
        registry.import_report(
            spec["repository_id"],
            ExecutionImportRequest(
                report_path=spec["report_path"],
                metadata_path=spec["metadata_path"],
                tested_commit=spec["tested_commit"],
                adapter=spec.get("adapter", "cucumber-messages"),
            ),
        )
    response = client.request(
        args.get("method", "GET"), args["path"], json=args.get("json"), params=args.get("params")
    )
    try:
        body = response.json()
    except ValueError:
        body = response.text
    return {"status": response.status_code, "body": body}


def op_schema_version(args: dict) -> dict:
    from app.version import SCHEMA_VERSION

    return {"version": SCHEMA_VERSION}


def op_settings(args: dict) -> dict:
    settings = _settings()
    return {
        "ai_mode": settings.ai_mode,
        "discovery_provider": settings.discovery_provider,
        "vector_backend": settings.vector_backend,
        "fixture": settings.fixture,
    }


def op_evidence(args: dict) -> dict:
    if "name" in args:
        state = _load_state()
        path = _repo_path(state, args["name"])
        revision = ingest_revision(GitRepository(path), args["revision"], repository_name="probe")
    else:
        store = _store()
        revision = (
            store._ingest(args["revision"])
            if args.get("revision") not in (None, *store.manifest.tags)
            else store._ingest(store.commit_of(args["revision"]))
        )
    return {"evidence": _jsonable(revision.evidence), "commit": revision.commit}


def op_artifact_diff(args: dict) -> dict:
    if "name" in args:
        state = _load_state()
        path = _repo_path(state, args["name"])
        repository = GitRepository(path)
        first = {
            a.artifact_id: a.content_hash
            for a in ingest_revision(repository, args["rev_a"], repository_name="probe").artifacts
        }
        second = {
            a.artifact_id: a.content_hash
            for a in ingest_revision(repository, args["rev_b"], repository_name="probe").artifacts
        }
    else:
        store = _store()
        first = {a.artifact_id: a.content_hash for a in store.artifacts_at(args["rev_a"])}
        second = {a.artifact_id: a.content_hash for a in store.artifacts_at(args["rev_b"])}
    changed = sorted(
        key for key in first.keys() | second.keys() if first.get(key) != second.get(key)
    )
    return {
        "changed": changed,
        "only_first": sorted(first.keys() - second.keys()),
        "only_second": sorted(second.keys() - first.keys()),
    }


def op_commit_manifest(args: dict) -> dict:
    payload = json.loads(
        (ROOT / "fixtures" / "banking-demo" / "expected" / "baselines.json").read_text("utf-8")
    )
    commit = next(item for item in payload["commits"] if item["id"] == args["id"])
    return {"commit": commit["commit"], "tags": commit["tags"]}


def op_changed(args: dict) -> dict:
    store = _store()
    return {
        "changed": store.changed_artifacts(args["baseline"], args["previous"]),
        "impacted_links": [
            link.link_id for link in store.impacted_links(args["baseline"], args["previous"])
        ],
    }


def op_manifest(args: dict) -> dict:
    payload = json.loads(
        (ROOT / "fixtures" / "banking-demo" / "expected" / "baselines.json").read_text("utf-8")
    )
    return {"tags": payload["tags"], "commits": payload["commits"]}


def op_snapshot(args: dict) -> dict:
    payload = json.loads((ROOT / "fixtures" / "api-responses" / "snapshot.json").read_text("utf-8"))
    if args.get("baseline"):
        payload = next(
            item for item in payload["baselines"] if item["baseline"] == args["baseline"]
        )
    return {"snapshot": payload}


def op_discover(args: dict) -> dict:
    store = _store()
    if args.get("assert_known"):
        store.get_artifact(args["artifact_id"])
    registry = ProviderRegistry(_settings())
    provider = registry.get(args.get("provider"))
    candidates = provider.discover(args["artifact_id"], top_k=args.get("top_k", 5))
    return {
        "provider": provider.provider_name,
        "model_version": provider.model_version,
        "index_revision": provider.index_revision,
        "providers": registry.registered,
        "candidates": _jsonable(candidates),
    }


def op_provider_error(args: dict) -> dict:
    registry = ProviderRegistry(_settings())
    registry.get(args["provider"])
    return {}


def op_build_fixture(args: dict) -> dict:
    import uuid

    destination = _state_dir() / "banking-builds" / uuid.uuid4().hex / "repo"
    manifest = fixturectl.build_repo(FIXTURE_DIR, destination)
    return {
        "path": str(destination),
        "tags": manifest.tags,
        "commits": [commit.model_dump(mode="json") for commit in manifest.commits],
    }


def op_fixture_tests(args: dict) -> dict:
    """Run the monitored application's own pytest suite at one tag in an isolated worktree."""
    destination = _state_dir() / "banking-tests-" / args["tag"]
    manifest = fixturectl.build_repo(FIXTURE_DIR, destination)
    worktree = destination.parent / f"worktree-{args['tag']}"
    _git(destination, "worktree", "add", "--detach", str(worktree), args["tag"])
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--tb=no"],
            cwd=worktree,
            capture_output=True,
            text=True,
            check=False,
        )
    finally:
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(worktree)],
            cwd=destination,
            capture_output=True,
            check=False,
        )
    failed = [
        line[len("FAILED ") :].split(" - ")[0].strip()
        for line in result.stdout.splitlines()
        if line.startswith("FAILED ")
    ]
    return {
        "exit_code": result.returncode,
        "failed": failed,
        "stdout": result.stdout,
        "tags": manifest.tags,
    }


def op_fixture_repo(args: dict) -> dict:
    return {"path": str(_fixture_repo())}


def op_external_build(args: dict) -> dict:
    import external_fixture

    destination = CACHE / "external"
    refs = external_fixture.build_all(destination)
    return {
        "repositories": {
            name: {"path": str(destination / name), "tags": tags} for name, tags in refs.items()
        }
    }


def op_tracked(args: dict) -> dict:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", args.get("pattern", "")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    return {"files": [line for line in result.stdout.splitlines() if line]}


def op_assurance_fixture(args: dict) -> dict:
    from assurance_fixture import build_probe_report

    state = Path(os.environ["CTA_BDD_STATE"]) / "assurance-fixture"
    return build_probe_report(
        state,
        feature=args.get("feature", "docs/stories/CI-01.feature"),
        failed=bool(args.get("failed", False)),
    )


def op_assurance(args: dict) -> dict:
    """Run the real M4 assurance CLI and return its artifacts."""
    state = Path(os.environ["CTA_BDD_STATE"]) / "assurance"
    state.mkdir(parents=True, exist_ok=True)
    command = args["command"]
    cli_command = "self-assure" if command == "self" else command
    argv = [sys.executable, str(ROOT / "tools" / "assurance.py"), cli_command]
    report_path = Path(args["report"]) if args.get("report") else state / "report.json"
    manifest_path = Path(args["manifest"]) if args.get("manifest") else state / "manifest.json"
    summary_path = state / "summary.md"
    diff_path = state / "diff.json"
    diff_path.unlink(missing_ok=True)
    if command == "evaluate":
        argv.extend(
            [
                "--repository",
                args.get("repository", "banking-demo"),
                "--baseline",
                args["baseline"],
                "--report",
                str(report_path),
                "--manifest",
                str(manifest_path),
                "--summary",
                str(summary_path),
                "--evaluator-revision",
                args.get("evaluator_revision", "cta@0.1.0+test+assurance"),
            ]
        )
        if args.get("fixture_repo"):
            argv.extend(["--fixture-repo", args["fixture_repo"]])
    elif command == "self":
        if args.get("metadata"):
            metadata = Path(args["metadata"])
        else:
            metadata = state / "report.meta.json"
            metadata.write_text(
                json.dumps(
                    {
                        "repository_id": args["repository_id"],
                        "tested_commit": args["tested_commit"],
                    }
                ),
                encoding="utf-8",
            )
        argv.extend(
            [
                "--repo-root",
                args.get("repo_root", str(ROOT)),
                "--repository-id",
                args["repository_id"],
                "--tested-commit",
                args["tested_commit"],
                "--cucumber-report",
                args["cucumber_report"],
                "--cucumber-root",
                args.get("cucumber_root", str(ROOT / "bdd")),
                "--metadata",
                str(metadata),
                "--state-dir",
                str(state),
                "--report",
                str(report_path),
                "--manifest",
                str(manifest_path),
                "--summary",
                str(summary_path),
                "--evaluator-revision",
                args.get("evaluator_revision", "cta@0.1.0+test+assurance"),
            ]
        )
    elif command == "diff":
        argv.extend(
            [
                "--previous",
                args["previous"],
                "--current",
                args["current"],
                "--output",
                str(diff_path),
                "--summary",
                str(summary_path),
            ]
        )
    elif command == "resolve-revision":
        event_path = state / "event.json"
        event_path.write_text(json.dumps(args["event"]), encoding="utf-8")
        argv.extend(["--event", str(event_path)])
    else:
        raise ValueError(f"unknown assurance command {command!r}")
    if args.get("deny_network") and command in {"evaluate", "self"}:
        argv.append("--deny-network")
    result = subprocess.run(
        argv,
        cwd=ROOT,
        env={**os.environ, "PYTHONPATH": str(ROOT / "backend")},
        capture_output=True,
        text=True,
        check=False,
    )
    response = {
        "command": command,
        "status": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }
    for key, path in (
        ("report", report_path),
        ("manifest", manifest_path),
        ("diff", diff_path),
    ):
        if path.is_file():
            try:
                response[key] = json.loads(path.read_text("utf-8"))
            except json.JSONDecodeError:
                response[key] = path.read_text("utf-8")
    if summary_path.is_file():
        response["summary"] = summary_path.read_text("utf-8")
    return response


def op_inventory(args: dict) -> dict:
    path = ROOT / "fixtures" / args["fixture"] / "expected" / "inventory.json"
    return {"inventory": json.loads(path.read_text("utf-8"))}


def op_commitlint(args: dict) -> dict:
    """Exercise the real commitlint functions against scenario-built Git histories."""
    import commitlint

    mode = args.get("mode", "message")
    if mode == "known":
        map_path = Path(args.get("map") or (ROOT / commitlint.ISSUE_MAP))
        issues = commitlint.known_issues(map_path.read_text(encoding="utf-8"))
        return {"exit_code": 0, "known_issues": sorted(issues), "errors": []}
    if mode == "message":
        if args.get("map"):
            issues = commitlint.known_issues(Path(args["map"]).read_text(encoding="utf-8"))
        else:
            issues = commitlint.known_issues(
                (ROOT / commitlint.ISSUE_MAP).read_text(encoding="utf-8")
            )
        errors = commitlint.check_message(args["message"], issues)
        return {
            "exit_code": 1 if errors else 0,
            "errors": errors,
            "known_issues": sorted(issues),
        }
    if mode == "range":
        state = _load_state()
        repo = Path(args.get("repo") or _repo_path(state, args.get("name", "repo")))
        try:
            commits = commitlint.commits_to_check(
                repo,
                args.get("head", "HEAD"),
                args.get("base"),
                args["legacy_baseline"],
            )
            failures: list[str] = []
            details: list[dict] = []
            for commit in commits:
                issues = commitlint.known_issues(
                    commitlint.git(repo, "show", f"{commit}:{commitlint.ISSUE_MAP}")
                )
                message = commitlint.git(repo, "show", "-s", "--format=%B", commit)
                errors = commitlint.check_message(message, issues)
                details.append(
                    {"commit": commit, "subject": message.splitlines()[0], "errors": errors}
                )
                failures.extend(f"{commit[:12]}: {error}" for error in errors)
            return {
                "exit_code": 1 if failures else 0,
                "errors": failures,
                "commits": commits,
                "details": details,
            }
        except commitlint.LintError as exc:
            return {"exit_code": 2, "errors": [str(exc)], "commits": []}
    raise RuntimeError(f"unknown commitlint mode {mode!r}")


def op_shallow_clone(args: dict) -> dict:
    """Create a shallow clone of a scenario repository and return its path."""
    state = _load_state()
    source = _repo_path(state, args.get("name", "repo"))
    destination = _state_dir() / "repos" / f"{args.get('name', 'repo')}-shallow"
    if destination.exists():
        shutil.rmtree(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    _git(
        _state_dir(),
        "clone",
        "--quiet",
        "--depth",
        "1",
        f"file://{source}",
        str(destination),
    )
    return {"path": str(destination)}


def op_code_retrieval(args: dict) -> dict:
    from app.discovery.cocoindex import (
        CocoIndexSearchClient,
        FakeCocoIndexTransport,
    )
    from app.discovery.code_index import CodeDiscovery, configured_model_version
    from app.domain.retrieval import CodeRetrievalRequest
    from app.ingestion.repository import GitRepository

    store = _store()
    built = _fixture_repo()
    git = GitRepository(built)
    client = None
    project_root = built if args.get("require_live_root") else Path("/snapshot")
    if args.get("captured"):
        client = CocoIndexSearchClient(
            FakeCocoIndexTransport.from_fixture(Path(args["captured"]), project_root=project_root)
        )
    elif args.get("payload"):
        client = CocoIndexSearchClient(
            FakeCocoIndexTransport(args["payload"], project_root=project_root)
        )
    discovery = CodeDiscovery(
        repository=store,
        git=git,
        repository_name="banking-demo",
        client=client,
        model_version=args.get("model_version", configured_model_version()),
        require_live_root=bool(args.get("require_live_root", False)),
    )
    from app.assurance.rules import DeterministicAssuranceEvaluator

    canonical = store.resolve_baseline(args["request"].get("baseline"))
    evaluator = DeterministicAssuranceEvaluator(store)

    def capture() -> dict:
        return {
            "links": _jsonable(store.list_links(canonical)),
            "evidence": _jsonable(store.list_evidence(canonical)),
            "artifacts": _jsonable(store.list_artifacts(canonical)),
            "findings": _jsonable(evaluator.evaluate(canonical)),
        }

    before = capture()
    try:
        response = discovery.retrieve(CodeRetrievalRequest.model_validate(args["request"]))
    except Exception as exc:  # noqa: BLE001 - rejection path is part of the audit
        if not args.get("capture_rejection"):
            raise
        after = capture()
        audit = {key: before[key] == after[key] for key in before}
        audit["all_unchanged"] = all(audit.values())
        return {
            "rejected": {"type": type(exc).__name__, "detail": str(exc)},
            "audit": audit,
        }
    after = capture()
    audit = {key: before[key] == after[key] for key in before}
    audit["all_unchanged"] = all(audit.values())
    return {"response": _jsonable(response), "audit": audit}


def op_dataset_variant(args: dict) -> dict:
    state = _state_dir()
    source = ROOT / "fixtures/banking-demo/expected/candidate-links.json"
    payload = json.loads(source.read_text(encoding="utf-8"))
    payload["model_version"] = "fake-fixture-v1-variant"
    target = state / "candidate-links-variant.json"
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    return {"path": str(target), "sha256": f"sha256:{digest}"}


def op_candidate_benchmark(args: dict) -> dict:
    import contextlib
    import io

    import evaluate_candidates

    state = _state_dir()
    output = state / "candidate-benchmark.json"
    command = ["--out", str(output)]
    if args.get("dataset_path"):
        command += ["--dataset", args["dataset_path"]]
    with contextlib.redirect_stdout(io.StringIO()):
        exit_code = evaluate_candidates.main(command)
    if exit_code != 0:
        raise RuntimeError(f"candidate benchmark exited {exit_code}")
    return {"report": json.loads(output.read_text(encoding="utf-8"))}


def op_rag_benchmark(args: dict) -> dict:
    import contextlib
    import io

    import evaluate_rag

    state = _state_dir()
    output = state / "rag-benchmark.json"
    code_eval = ROOT / "docs/reports/omp-cocoindex-pr2/evidence/live-eval-baseline-a.json"
    with contextlib.redirect_stdout(io.StringIO()):
        exit_code = evaluate_rag.main(["--code-eval", str(code_eval), "--out", str(output)])
    if exit_code != 0:
        raise RuntimeError(f"benchmark exited {exit_code}")
    return {"report": json.loads(output.read_text(encoding="utf-8"))}


def op_answer(args: dict) -> dict:
    from app.discovery.code_index import CodeDiscovery
    from app.domain.answers import AnswerRequest
    from app.graphrag.context import AnswerService
    from app.ingestion.repository import GitRepository

    store = _store()
    request = AnswerRequest.model_validate(args["request"])
    code = None
    if request.include_semantic_candidates:
        code = CodeDiscovery(
            repository=store,
            git=GitRepository(_fixture_repo()),
            repository_name="banking-demo",
            model_version="deterministic-token-overlap-v1",
        )
    return {"response": _jsonable(AnswerService(store, code_discovery=code).answer(request))}


def op_hashes(args: dict) -> dict:
    state = _load_state()
    path = Path(args["path"]) if args.get("path") else _repo_path(state, args.get("name", "repo"))
    import hashlib

    hashes = {}
    for item in sorted(path.rglob("*")):
        if item.is_file() and ".git" not in item.parts:
            hashes[str(item.relative_to(path))] = hashlib.sha256(item.read_bytes()).hexdigest()
    return {
        "hashes": hashes,
        "status": _git(path, "status", "--porcelain", "--untracked-files=all").strip(),
    }


def _tree_digest(path: Path) -> str:
    import hashlib

    digest = hashlib.sha256()
    for item in sorted(path.rglob("*")):
        if item.is_file() and ".git" not in item.parts:
            digest.update(str(item.relative_to(path)).encode("utf-8"))
            digest.update(item.read_bytes())
    return f"sha256:{digest.hexdigest()}"


def _review_state() -> dict:
    state = _load_state()
    return state.setdefault("review", {})


def _review_init(args: dict) -> dict:
    import uuid

    state = _load_state()
    review = state.setdefault("review", {})
    journal = Path(
        args.get("journal") or (_state_dir() / "review" / f"journal-{uuid.uuid4().hex}.ndjson")
    )
    journal.parent.mkdir(parents=True, exist_ok=True)
    if args.get("fresh", True) and journal.exists():
        journal.unlink()
    repo = Path(args.get("repo") or _fixture_repo())
    review.update(
        {
            "journal": str(journal),
            "operator": args.get("operator", "rv-ana"),
            "repo": str(repo),
        }
    )
    _save_state(state)
    settings = _review_settings()
    client = _review_client()
    baseline = client.get("/api/findings", params={"baseline": "baseline-a"}).json()
    thread = client.get("/api/threads/REQ-002", params={"baseline": "baseline-a"}).json()
    review["baseline"] = {
        "findings": baseline,
        "thread": thread,
        "evidence": thread["evidence"],
        "fixture_digest": _tree_digest(_fixture_repo()),
        "journal_hashes": _journal_hashes(journal) if journal.exists() else None,
    }
    state = _load_state()
    state["review"] = review
    _save_state(state)
    return {
        "journal": str(journal),
        "operator": settings.review_operator,
        "outside_fixture": not journal.resolve().is_relative_to(ROOT / "fixtures"),
        "config": client.get("/api/review/config").json(),
        "events": _review_journal_events(journal),
    }


def _review_settings() -> Settings:
    from dataclasses import replace

    review = _review_state()
    return replace(
        _settings(),
        fixture_repo_path=Path(review.get("repo") or _fixture_repo()),
        review_operator=review.get("operator", "rv-ana"),
        review_journal_path=Path(review["journal"]),
    )


def _review_client():
    from fastapi.testclient import TestClient

    return TestClient(create_app(_review_settings()))


def _review_workspace():
    from app.persistence.review import ReviewWorkspace

    settings = _review_settings()
    return ReviewWorkspace(create_app(settings).state.store, settings)


def _review_journal_events(path: Path) -> list[dict]:
    from app.persistence.review import ReviewJournal

    journal = ReviewJournal(path)
    return [event.model_dump(mode="json") for event in journal.events]


def _review_capture_payload(
    client,
    *,
    source_id="SCN-002",
    target_id="CODE-001",
    relation_type="implemented_by",
    baseline="baseline-a",
    **overrides,
):
    artifacts = {
        artifact["artifact_id"]: artifact
        for artifact in client.get("/api/artifacts", params={"baseline": baseline}).json()[
            "artifacts"
        ]
    }
    payload = {
        "source_id": source_id,
        "target_id": target_id,
        "relation_type": relation_type,
        "baseline": baseline,
        "source_content_hash": artifacts[source_id]["content_hash"],
        "target_content_hash": artifacts[target_id]["content_hash"],
        "provider": "fake",
        "model_version": "fake-fixture-v1",
        "index_revision": "sha256:" + "a" * 64,
        "score": 0.71,
    }
    payload.update(overrides)
    return payload


def _review_last_capture() -> dict:
    return _review_state().get("last_capture", {})


def op_review(args: dict) -> dict:
    action = args.get("action")
    if action == "init":
        return _review_init(args)
    if action == "config":
        return _review_client().get("/api/review/config").json()

    client = _review_client()
    review = _review_state()

    if action == "capture":
        payload = None
        if args.get("candidate"):
            from app.discovery.registry import ProviderRegistry
            from app.domain.enums import RelationType

            settings = _review_settings()
            provider = ProviderRegistry(settings).get("fake")
            candidates = provider.discover(
                "SCN-002", top_k=50, relation_types=[RelationType.IMPLEMENTED_BY]
            )
            candidate = next(
                (
                    item
                    for item in candidates
                    if item.source_id == "SCN-002" and item.target_id == "CODE-001"
                ),
                None,
            )
            if candidate is None:
                raise RuntimeError(
                    "the fake index has no SCN-002 implemented_by CODE-001 candidate"
                )
            payload = _review_capture_payload(
                client,
                provider=candidate.discovery_provider,
                model_version=candidate.model_version,
                index_revision=candidate.index_revision,
                score=candidate.score,
                rationale=candidate.rationale,
            )
        elif args.get("stored"):
            payload = _review_last_capture()["payload"]
        elif args.get("submission"):
            base = _review_last_capture()["payload"]
            payload = dict(base)
            if args["submission"] == "the same endpoints with a different provider identity":
                payload["provider"] = "cocoindex"
            elif args["submission"] == "the identical snapshot again":
                pass
            elif args["submission"] == "the same endpoints after a terminal decision":
                link_id = _review_last_capture()["body"]["link"]["link_id"]
                decision = client.post(
                    f"/api/links/{link_id}/review",
                    json={
                        "decision": "accept",
                        "reviewer_id": "rv-ana",
                        "baseline": base["baseline"],
                    },
                )
                if decision.status_code != 200:
                    raise RuntimeError(f"terminal decision setup failed: {decision.text}")
            else:
                raise RuntimeError(f"unknown capture submission {args['submission']!r}")
        else:
            overrides = {
                key: args[key]
                for key in ("source_id", "target_id", "relation_type", "baseline")
                if key in args
            }
            payload = _review_capture_payload(client, **overrides)
            defect = args.get("defect")
            if defect == "an unknown target artifact SCN-999":
                payload["target_id"] = "SCN-999"
            elif defect == "a relation direction that contradicts the endpoint artifact types":
                payload["source_id"], payload["target_id"] = "CODE-001", "SCN-002"
                payload["source_content_hash"], payload["target_content_hash"] = (
                    payload["target_content_hash"],
                    payload["source_content_hash"],
                )
            elif defect == "a source content hash that disagrees":
                payload["source_content_hash"] = "sha256:" + "b" * 64
            elif defect == "a target content hash that disagrees":
                payload["target_content_hash"] = "sha256:" + "b" * 64
            elif defect:
                raise RuntimeError(f"unknown capture defect {defect!r}")

        if args.get("dry_run"):
            review["last_capture"] = {"payload": payload, "status": None, "body": {}}
            state = _load_state()
            state["review"] = review
            _save_state(state)
            return review["last_capture"]

        before = _tree_digest(_fixture_repo())
        response = client.post("/api/link-proposals", json=payload)
        after = _tree_digest(_fixture_repo())
        body = response.json()
        review["last_capture"] = {
            "status": response.status_code,
            "body": body,
            "payload": payload,
            "fixture_unchanged": before == after,
            "digest_valid": (
                "snapshot" in body
                and body["snapshot"]["snapshot_digest"]
                == _independent_snapshot_digest(body["snapshot"])
            ),
        }
        state = _load_state()
        state["review"] = review
        _save_state(state)
        return review["last_capture"]

    if action == "decide":
        link_id = args.get("link_id") or _review_last_capture()["body"]["link"]["link_id"]
        payload: dict = {
            "decision": args.get("decision", "accept"),
            "reviewer_id": args.get("reviewer", "rv-ana"),
            "baseline": args.get("baseline", "baseline-a"),
        }
        reason = args.get("reason")
        if reason is None and "reason" in args:
            payload["reason"] = None
        elif reason == "no reason field":
            pass
        elif reason == "a null reason":
            payload["reason"] = None
        elif reason == "an empty reason":
            payload["reason"] = ""
        elif reason == "a reason of three space characters":
            payload["reason"] = "   "
        elif reason is not None:
            payload["reason"] = reason
        headers = {}
        if args.get("origin"):
            headers["Origin"] = args["origin"]
        if args.get("client_host"):
            from fastapi.testclient import TestClient

            request_client = TestClient(
                create_app(_review_settings()), client=(args["client_host"], 50000)
            )
        else:
            request_client = client
        before = client.get("/api/workspace/history", params={"baseline": payload["baseline"]})
        before_count = len(before.json()["events"]) if before.status_code == 200 else 0
        journal_path = Path(_review_state()["journal"])
        before_hashes = _journal_hashes(journal_path)
        response = request_client.post(
            f"/api/links/{link_id}/review", json=payload, headers=headers
        )
        after_events = _review_journal_events(journal_path) if journal_path.exists() else []
        review["last_decision"] = {
            "status": response.status_code,
            "body": response.json(),
            "payload": payload,
            "link_id": link_id,
            "history_revision_before": before_count,
            "journal_hashes_before": before_hashes,
            "journal_events": after_events,
            "journal_hashes": _journal_hashes(journal_path),
        }
        state = _load_state()
        state["review"] = review
        _save_state(state)
        return review["last_decision"]

    if action == "workspace":
        kind = args.get("kind", "history")
        params = {"baseline": args.get("baseline", "baseline-a")}
        if kind == "thread":
            path = f"/api/workspace/threads/{args.get('artifact_id', 'REQ-002')}"
        elif kind == "proposals":
            path = "/api/workspace/proposals"
        elif kind == "history":
            path = "/api/workspace/history"
        else:
            raise RuntimeError(f"unknown workspace kind {kind!r}")
        response = client.get(path, params=params)
        return {"status": response.status_code, "body": response.json()}

    if action == "restart":
        path = Path(_review_state()["journal"])
        before = _journal_hashes(path)
        restarted = _review_client()
        return {
            "config": restarted.get("/api/review/config").json(),
            "journal_hashes_before": before,
            "journal_hashes_after": _journal_hashes(path),
            "history": restarted.get(
                "/api/workspace/history", params={"baseline": args.get("baseline", "baseline-a")}
            ).json(),
        }

    if action == "journal":
        path = Path(_review_state()["journal"])
        hashes = _journal_hashes(path)
        result = {
            "path": str(path),
            "exists": path.exists(),
            "bytes_sha256": hashes["bytes_sha256"],
            "bytes": hashes["bytes"],
            "line_count": hashes["line_count"],
            "events": _review_journal_events(path) if path.exists() else [],
        }
        if "prefix_bytes" in args:
            import hashlib

            raw = path.read_bytes() if path.exists() else b""
            length = min(max(0, int(args["prefix_bytes"])), len(raw))
            result["prefix_sha256"] = f"sha256:{hashlib.sha256(raw[:length]).hexdigest()}"
        return result

    if action == "baseline":
        baseline = args.get("baseline", "baseline-a")
        findings = client.get("/api/findings", params={"baseline": baseline}).json()
        thread = client.get("/api/threads/REQ-002", params={"baseline": baseline}).json()
        path = Path(_review_state()["journal"])
        review["baseline"] = {
            "findings": findings,
            "thread": thread,
            "evidence": thread["evidence"],
            "fixture_digest": _tree_digest(_fixture_repo()),
            "journal_hashes": _journal_hashes(path) if path.exists() else None,
        }
        state = _load_state()
        state["review"] = review
        _save_state(state)
        return review["baseline"]

    if action == "compare_baseline":
        baseline = args.get("baseline", "baseline-a")
        recorded = _review_state().get("baseline")
        if recorded is None:
            raise RuntimeError("no recorded baseline comparison")
        findings = client.get("/api/findings", params={"baseline": baseline}).json()
        thread = client.get("/api/threads/REQ-002", params={"baseline": baseline}).json()
        path = Path(_review_state()["journal"])
        return {
            "findings_equal": findings == recorded["findings"],
            "evidence_equal": thread["evidence"] == recorded["evidence"],
            "thread_equal": thread == recorded["thread"],
            "fixture_equal": _tree_digest(_fixture_repo()) == recorded["fixture_digest"],
            "journal": _journal_hashes(path) if path.exists() else None,
        }

    if action == "concurrent":
        import threading

        from app.domain.enums import ReviewDecision

        settings = _review_settings()
        workspace = _review_workspace()
        outcomes: list[dict] = []

        def decide(decision: str, reason: str | None) -> None:
            from app.domain.errors import ReviewConflict

            try:
                link = workspace.review(
                    args.get("link_id", "LNK-007"),
                    decision=ReviewDecision(decision),
                    reviewer_id="rv-ana",
                    baseline=args.get("baseline", "baseline-a"),
                    reason=reason,
                )
                outcomes.append({"status": 200, "body": link.model_dump(mode="json")})
            except ReviewConflict as exc:
                outcomes.append({"status": 409, "body": {"code": exc.code, "detail": exc.detail}})

        threads = [
            threading.Thread(target=decide, args=("accept", None)),
            threading.Thread(target=decide, args=("reject", "concurrent rejection")),
        ]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        path = Path(_review_state()["journal"])
        return {"outcomes": outcomes, "events": _review_journal_events(path)}

    if action == "evidence_only":
        import uuid

        destination = _state_dir() / "review" / f"evidence-only-{uuid.uuid4().hex}"
        _git(_fixture_repo().parent, "clone", "--quiet", str(_fixture_repo()), str(destination))
        _git(destination, "checkout", "--quiet", "baseline-a")
        _git(destination, "config", "user.name", "BDD Fixture")
        _git(destination, "config", "user.email", "bdd@example.invalid")
        _git(destination, "config", "commit.gpgsign", "false")
        commit = _commit(destination, "Evidence-only observation")
        review["repo"] = str(destination)
        review["evidence_only_commit"] = commit
        state = _load_state()
        state["review"] = review
        _save_state(state)
        return {"commit": commit, "repo": str(destination)}

    if action == "findings":
        baseline = args.get("baseline", "baseline-a")
        response = client.get("/api/findings", params={"baseline": baseline})
        return {"status": response.status_code, "body": response.json()}

    if action == "failing_capture":
        from fastapi.testclient import TestClient

        from app.persistence.review import ReviewJournal, ReviewWorkspace

        mode = args.get("mode", "rollback")

        class FailingJournal(ReviewJournal):
            def __init__(self, path: Path) -> None:
                self.calls = 0
                super().__init__(path)

            def _fsync(self, fd: int) -> None:
                self.calls += 1
                if self.calls == 2:
                    raise OSError("injected fsync failure")
                super()._fsync(fd)

        class IndeterminateJournal(FailingJournal):
            def _truncate(self, fd: int, size: int) -> None:
                raise OSError("injected truncate failure")

        settings = _review_settings()
        journal = (IndeterminateJournal if mode == "indeterminate" else FailingJournal)(
            Path(settings.review_journal)
        )
        app = create_app(settings)
        app.state.review = ReviewWorkspace(app.state.store, settings, journal=journal)
        scenario_client = TestClient(app)
        payload = args.get("payload") or _review_last_capture()["payload"]
        response = scenario_client.post("/api/link-proposals", json=payload)
        path = Path(settings.review_journal)
        return {
            "status": response.status_code,
            "body": response.json(),
            "live_pending": app.state.review.pending("baseline-a").model_dump(mode="json"),
            "journal_hashes": _journal_hashes(path),
        }

    if action == "failing_decide":
        from fastapi.testclient import TestClient

        from app.persistence.review import ReviewJournal, ReviewWorkspace

        mode = args.get("mode", "rollback")

        class FailingJournal(ReviewJournal):
            def __init__(self, path: Path) -> None:
                self.calls = 0
                super().__init__(path)

            def _fsync(self, fd: int) -> None:
                self.calls += 1
                if self.calls == 2:
                    raise OSError("injected fsync failure")
                super()._fsync(fd)

        class IndeterminateJournal(FailingJournal):
            def _truncate(self, fd: int, size: int) -> None:
                raise OSError("injected truncate failure")

        settings = _review_settings()
        journal = (IndeterminateJournal if mode == "indeterminate" else FailingJournal)(
            Path(settings.review_journal)
        )
        app = create_app(settings)
        app.state.review = ReviewWorkspace(app.state.store, settings, journal=journal)
        scenario_client = TestClient(app)
        link_id = args.get("link_id", "LNK-007")
        response = scenario_client.post(
            f"/api/links/{link_id}/review",
            json={
                "decision": args.get("decision", "accept"),
                "reviewer_id": "rv-ana",
                "baseline": args.get("baseline", "baseline-a"),
            },
        )
        path = Path(settings.review_journal)
        return {
            "status": response.status_code,
            "body": response.json(),
            "live_pending": app.state.review.pending("baseline-a").model_dump(mode="json"),
            "live_history": app.state.review.history("baseline-a").model_dump(mode="json"),
            "journal_hashes": _journal_hashes(path),
        }

    if action == "tail":
        path = Path(_review_state()["journal"])
        payload_line = json.dumps(
            {"event": {}, "record_digest": "sha256:" + "a" * 64}, separators=(",", ":")
        )
        with path.open("a", encoding="utf-8") as handle:
            handle.write(payload_line + "\n")
        return {"path": str(path)}

    raise RuntimeError(f"unknown review action {action!r}")


def _journal_hashes(path: Path) -> dict:
    import hashlib

    if not path.exists():
        return {"bytes_sha256": None, "line_count": 0, "bytes": 0}
    raw = path.read_bytes()
    return {
        "bytes_sha256": f"sha256:{hashlib.sha256(raw).hexdigest()}",
        "line_count": len(raw.splitlines()),
        "bytes": len(raw),
    }


def _independent_snapshot_digest(snapshot: dict) -> str:
    import hashlib
    import json

    payload = {
        "source_id": snapshot["source_id"],
        "target_id": snapshot["target_id"],
        "relation_type": snapshot["relation_type"],
        "baseline": snapshot["baseline"],
        "baseline_commit": snapshot["baseline_commit"],
        "source_content_hash": snapshot["source_content_hash"],
        "target_content_hash": snapshot["target_content_hash"],
        "provider": snapshot["provider"],
        "model_version": snapshot["model_version"],
        "index_revision": snapshot["index_revision"],
    }
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return f"sha256:{hashlib.sha256(canonical.encode('utf-8')).hexdigest()}"


class _KeywordRuntime:
    """Deterministic local runtime used by the offline AI-02 contract scenario."""

    model_id = "embeddinggemma-2-text-270m-q8_0"
    weights_digest = "sha256:" + "a" * 64
    runtime_version = "deterministic-keyword-runtime"
    dimension = 3
    max_tokens = 512

    def embed(self, texts):
        import math

        vectors = []
        for text in texts:
            lowered = text.lower()
            vector = [0.0, 0.0, 0.0]
            if "withdraw" in lowered:
                vector[0] += 1.0
            if "transfer" in lowered:
                vector[1] += 1.0
            if "account" in lowered:
                vector[2] += 1.0
            if not any(vector):
                vector[2] = 1.0
            norm = math.sqrt(sum(value * value for value in vector))
            vectors.append([value / norm for value in vector])
        return vectors


class _NaNRuntime(_KeywordRuntime):
    def embed(self, texts):
        return [[float("nan"), 0.0, 0.0] for _ in texts]


def _local_provider(runtime):
    from app.discovery.local_embedding import LocalEmbeddingCandidateDiscovery
    from app.ingestion.repository import GitRepository

    store = _store()
    return LocalEmbeddingCandidateDiscovery(store, GitRepository(_fixture_repo()), runtime=runtime)


def _deny_network(attempts: list[str] | None = None) -> object:
    import socket

    original = socket.socket.connect

    def deny(sock, address):
        if attempts is not None:
            attempts.append(str(address))
        raise OSError(f"network connection attempted to {address!r}")

    socket.socket.connect = deny
    return original


def _restore_network(original) -> None:
    import socket

    socket.socket.connect = original


class _FailingRefreshAdapter:
    def refresh(self, *, baseline, commit, plan, config):
        raise TimeoutError("deterministic retrieval index adapter timed out")


def _retrieval_state() -> dict:
    state = _load_state()
    return state.setdefault("retrieval", {})


def _retrieval_init(args: dict) -> dict:
    import uuid

    state = _load_state()
    retrieval = state.setdefault("retrieval", {})
    snapshots = _state_dir() / "retrieval" / f"snapshots-{uuid.uuid4().hex}"
    snapshots.mkdir(parents=True, exist_ok=True)
    retrieval.update({"snapshots": str(snapshots), "repo": str(_fixture_repo())})
    state["retrieval"] = retrieval
    _save_state(state)
    return {
        "snapshots": str(snapshots),
        "repo": str(_fixture_repo()),
        "manifest": None,
    }


def _retrieval_settings():
    from dataclasses import replace

    retrieval = _retrieval_state()
    return replace(
        _settings(),
        fixture_repo_path=Path(retrieval.get("repo") or _fixture_repo()),
        retrieval_snapshot_dir=Path(retrieval["snapshots"]),
        review_journal_path=_state_dir() / "review" / "journal.ndjson",
    )


def _retrieval_client():
    from fastapi.testclient import TestClient

    return TestClient(create_app(_retrieval_settings()))


def _retrieval_config(args: dict):
    from app.domain.retrieval_lifecycle import RetrievalConfig

    weights = args.get("weights_digest")
    if weights is None:
        return None
    return RetrievalConfig(
        provider="cocoindex",
        model_id="embeddinggemma-2-text-270m-q8_0",
        model_version="embeddinggemma-2-text-270m-q8_0@sha256:" + "b" * 12,
        weights_digest=weights,
        runtime="cocoindex 0.2.43",
        formatting_version="ai03-test-v1",
    )


def _retrieval_service():
    from app.ingestion.repository import GitRepository
    from app.retrieval.lifecycle import RetrievalLifecycle

    settings = _retrieval_settings()
    return RetrievalLifecycle(
        IngestedStore.from_settings(settings),
        GitRepository(settings.fixture_repo),
        settings.retrieval_snapshots,
        repository_name=settings.fixture,
    )


def op_retrieval_lifecycle(args: dict) -> dict:
    action = args.get("action", "init")
    if action == "init":
        return _retrieval_init(args)

    if action == "evidence_only":
        import uuid

        destination = _state_dir() / "retrieval" / f"evidence-only-{uuid.uuid4().hex}"
        _git(_fixture_repo().parent, "clone", "--quiet", str(_fixture_repo()), str(destination))
        _git(destination, "checkout", "--quiet", "baseline-a")
        _git(destination, "config", "user.name", "BDD Fixture")
        _git(destination, "config", "user.email", "bdd@example.invalid")
        _git(destination, "config", "commit.gpgsign", "false")
        commit = _commit(destination, "Evidence-only retrieval observation")
        retrieval = _retrieval_state()
        retrieval["repo"] = str(destination)
        state = _load_state()
        state["retrieval"] = retrieval
        _save_state(state)
        from app.assurance.rules import DeterministicAssuranceEvaluator
        from app.persistence.ingested import IngestedStore

        store = IngestedStore.from_settings(_retrieval_settings())
        evaluator = DeterministicAssuranceEvaluator(store)
        before = evaluator.evaluate("baseline-a")
        after = evaluator.evaluate(commit)
        findings_unchanged = [
            (finding.finding_id, finding.finding_type, finding.artifact_ids) for finding in before
        ] == [(finding.finding_id, finding.finding_type, finding.artifact_ids) for finding in after]
        return {
            "commit": commit,
            "repo": str(destination),
            "findings_unchanged": findings_unchanged,
            "verification_failed": [
                finding.finding_id
                for finding in after
                if finding.finding_type.value == "verification_failed"
            ],
        }

    client = _retrieval_client()
    if action == "plan":
        service = _retrieval_service()
        plan = service.plan(args["baseline"], args.get("previous_baseline"))
        return plan.model_dump(mode="json")

    if action == "refresh":
        if args.get("adapter") == "failing":
            service = _retrieval_service()
            try:
                manifest = service.refresh(
                    args["baseline"],
                    previous_baseline=args.get("previous_baseline"),
                    config=_retrieval_config(args),
                    adapter=_FailingRefreshAdapter(),
                )
            except Exception as exc:
                return {"status": 503, "error": type(exc).__name__, "detail": str(exc)}
            return {"status": 200, "body": manifest.model_dump(mode="json")}
        response = client.post(
            "/api/retrieval/refresh",
            json={
                "baseline": args["baseline"],
                "previous_baseline": args.get("previous_baseline"),
                "config": (
                    _retrieval_config(args).model_dump(mode="json")
                    if _retrieval_config(args) is not None
                    else None
                ),
            },
        )
        return {"status": response.status_code, "body": response.json()}

    if action == "manifest":
        response = client.get(f"/api/retrieval/manifests/{args['baseline']}")
        return {"status": response.status_code, "body": response.json()}

    if action == "manifests":
        response = client.get("/api/retrieval/manifests")
        return {"status": response.status_code, "body": response.json()}

    if action == "combine":
        response = client.post(
            "/api/retrieval/combine",
            json={"snapshot_binding": args["snapshot_binding"], "batches": args["batches"]},
        )
        return {"status": response.status_code, "body": response.json()}

    raise RuntimeError(f"unknown retrieval lifecycle action {action!r}")


def op_local_embedding(args: dict) -> dict:
    from dataclasses import replace

    from app.discovery.registry import ProviderRegistry
    from app.main import create_app

    action = args.get("action", "contract")
    base = _settings()
    store = _store()

    if action == "default_fake":
        registry = ProviderRegistry(base, store)
        attempts: list[str] = []
        original = _deny_network(attempts)
        try:
            candidates = registry.get(None).discover("SCN-001")
        finally:
            _restore_network(original)
        import sys

        return {
            "registered": registry.registered,
            "candidates": _jsonable(candidates),
            "provider": candidates[0].discovery_provider if candidates else "fake",
            "onnxruntime_imported": "onnxruntime" in sys.modules,
            "model_dir_configured": base.local_embedding_model_dir is not None,
            "network_attempts": attempts,
        }

    if action == "remote_endpoint":
        settings = replace(
            base,
            local_embedding_enabled=True,
            local_embedding_endpoint="http://192.0.2.10:11434",
            review_journal_path=_state_dir() / "review-local" / "journal.ndjson",
        )
        app = create_app(settings)
        attempts: list[str] = []
        original = _deny_network(attempts)
        try:
            from fastapi.testclient import TestClient

            response = TestClient(app).post(
                "/api/discovery",
                json={"artifact_id": "SCN-001", "provider": "local-embeddinggemma"},
            )
        finally:
            _restore_network(original)
        return {
            "status": response.status_code,
            "body": response.json(),
            "network_attempts": attempts,
        }

    if action == "missing_weights":
        condition = args.get("condition", "absent")
        model_dir = _state_dir() / "review-local" / f"model-{condition}"
        expected = "sha256:" + "a" * 64
        if condition in {"mismatch", "runtime_missing"}:
            model_dir.mkdir(parents=True, exist_ok=True)
            (model_dir / "onnx").mkdir(exist_ok=True)
            (model_dir / "onnx" / "model_quantized.onnx").write_bytes(b"graph")
            (model_dir / "onnx" / "model_quantized.onnx_data").write_bytes(b"data")
            (model_dir / "tokenizer.json").write_text("{}", "utf-8")
        settings = replace(
            base,
            local_embedding_enabled=True,
            local_embedding_model_dir=model_dir,
            local_embedding_weights_digest=(expected if condition != "runtime_missing" else None),
            review_journal_path=_state_dir() / "review-local" / "journal.ndjson",
        )
        import sys

        from fastapi.testclient import TestClient

        patched: dict[str, object] = {}
        if condition == "runtime_missing":
            for name in ("onnxruntime", "tokenizers"):
                patched[name] = sys.modules.get(name)
                sys.modules[name] = None
        try:
            client = TestClient(create_app(settings))
            before = {
                "findings": client.get("/api/findings", params={"baseline": "baseline-a"}).json(),
                "thread": client.get(
                    "/api/threads/REQ-001", params={"baseline": "baseline-a"}
                ).json(),
            }
            response = client.post(
                "/api/discovery",
                json={"artifact_id": "SCN-001", "provider": "local-embeddinggemma"},
            )
            after = {
                "findings": client.get("/api/findings", params={"baseline": "baseline-a"}).json(),
                "thread": client.get(
                    "/api/threads/REQ-001", params={"baseline": "baseline-a"}
                ).json(),
            }
        finally:
            for name, value in patched.items():
                if value is None:
                    sys.modules.pop(name, None)
                else:
                    sys.modules[name] = value
        return {
            "status": response.status_code,
            "body": response.json(),
            "unchanged": before == after,
            "condition": condition,
        }

    if action == "contract":
        provider = _local_provider(_KeywordRuntime())
        from app.assurance.rules import DeterministicAssuranceEvaluator

        evaluator = DeterministicAssuranceEvaluator(store)
        before = (
            store.list_links("baseline-a"),
            store.list_evidence("baseline-a"),
            evaluator.evaluate("baseline-a"),
        )
        candidates = provider.discover("SCN-001", top_k=10)
        trimmed = provider.discover("SCN-001", top_k=1)
        sources = provider.discover("SCN-001", relation_types=["implemented_by"])
        tests = provider.discover("SCN-001", relation_types=["exercised_by"])
        requirements = provider.discover("REQ-001")

        settings = replace(
            base,
            local_embedding_enabled=True,
            local_embedding_model_dir=None,
            review_journal_path=_state_dir() / "review-local" / "journal.ndjson",
        )
        from fastapi.testclient import TestClient

        app = create_app(settings)
        from app.discovery.registry import ProviderRegistry

        registry = ProviderRegistry(settings, app.state.store)
        registry._cache["local-embeddinggemma"] = provider
        app.state.providers = registry
        empty = TestClient(app).post(
            "/api/discovery",
            json={
                "artifact_id": "CODE-001",
                "provider": "local-embeddinggemma",
                "baseline": "baseline-a",
            },
        )

        from app.discovery.local_embedding import (
            LocalEmbeddingCandidateDiscovery,
            RetrievalUnavailable,
        )
        from app.ingestion.repository import GitRepository

        class NoProvenanceRuntime:
            dimension = 3
            max_tokens = 512
            runtime_version = "no-provenance"

            def embed(self, texts):
                return [[1.0, 0.0, 0.0] for _ in texts]

        try:
            LocalEmbeddingCandidateDiscovery(
                store,
                GitRepository(_fixture_repo()),
                runtime=NoProvenanceRuntime(),
            )
            unavailable_provenance = False
        except RetrievalUnavailable:
            unavailable_provenance = True

        after = (
            store.list_links("baseline-a"),
            store.list_evidence("baseline-a"),
            evaluator.evaluate("baseline-a"),
        )
        return {
            "provider": provider.provider_name,
            "model_version": provider.model_version,
            "index_revision": provider.index_revision,
            "candidates": _jsonable(candidates),
            "trimmed": _jsonable(trimmed),
            "sources": _jsonable(sources),
            "tests": _jsonable(tests),
            "requirements": _jsonable(requirements),
            "empty_status": empty.status_code,
            "empty_response": empty.json(),
            "unavailable_provenance": unavailable_provenance,
            "unchanged": before == after,
        }

    if action == "malformed":
        provider = _local_provider(_NaNRuntime())
        settings = replace(
            base,
            local_embedding_enabled=True,
            local_embedding_model_dir=None,
            review_journal_path=_state_dir() / "review-local" / "journal.ndjson",
        )
        app = create_app(settings)
        registry = ProviderRegistry(settings, app.state.store)
        registry._cache["local-embeddinggemma"] = provider
        app.state.providers = registry
        from fastapi.testclient import TestClient

        client = TestClient(app)
        before = client.get("/api/findings", params={"baseline": "baseline-a"}).json()
        response = client.post(
            "/api/discovery",
            json={"artifact_id": "SCN-001", "provider": "local-embeddinggemma"},
        )
        after = client.get("/api/findings", params={"baseline": "baseline-a"}).json()
        return {
            "status": response.status_code,
            "body": response.json(),
            "unchanged": before == after,
        }

    if action == "live":
        from app.discovery.local_embedding import (
            LocalEmbeddingCandidateDiscovery,
            OnnxEmbeddingRuntime,
        )
        from app.ingestion.repository import GitRepository

        model_dir = Path(
            args.get("model_dir")
            or (Path.home() / ".local/share/cta/models/embeddinggemma-2-text-270m-onnx")
        ).expanduser()
        if not model_dir.is_dir():
            raise RuntimeError(f"local model directory is absent: {model_dir}")
        started = __import__("time").perf_counter()
        runtime = OnnxEmbeddingRuntime(
            model_dir,
            expected_weights_digest=args.get("weights_digest"),
        )
        provider = LocalEmbeddingCandidateDiscovery(
            store, GitRepository(_fixture_repo()), runtime=runtime
        )
        load_seconds = __import__("time").perf_counter() - started
        from app.assurance.rules import DeterministicAssuranceEvaluator

        evaluator = DeterministicAssuranceEvaluator(store)
        before = (
            store.list_links("baseline-a"),
            store.list_evidence("baseline-a"),
            evaluator.evaluate("baseline-a"),
        )
        import time

        index_started = time.perf_counter()
        binding = provider.binding_for("baseline-a")
        index_seconds = time.perf_counter() - index_started
        expected_binding = "sha256:814eb9914310d4d18f68859fbb5e89230773f026a50e931cb16889b1e3eaac52"
        assert binding == expected_binding
        latencies = []
        result_sets = {}
        for artifact_id in ("SCN-001", "REQ-001", "SCN-002"):
            query_started = time.perf_counter()
            candidates = provider.discover(artifact_id, top_k=10, baseline="baseline-a")
            latencies.append((time.perf_counter() - query_started) * 1000.0)
            result_sets[artifact_id] = [item.target_id for item in candidates]
        candidates = provider.discover("SCN-001", top_k=10, baseline="baseline-a")
        trimmed = provider.discover("SCN-001", top_k=1, baseline="baseline-a")
        top_k_rejected = False
        try:
            provider.discover("SCN-001", top_k=0, baseline="baseline-a")
        except ValueError:
            top_k_rejected = True
        assert top_k_rejected
        sources = provider.discover(
            "SCN-001", relation_types=["implemented_by"], baseline="baseline-a"
        )
        tests = provider.discover("SCN-001", relation_types=["exercised_by"], baseline="baseline-a")
        incompatible = provider.discover(
            "SCN-001", relation_types=["verified_by"], baseline="baseline-a"
        )
        requirements = provider.discover("REQ-001", baseline="baseline-a")
        empty_source = provider.discover("CODE-001", baseline="baseline-a")
        from dataclasses import replace

        from fastapi.testclient import TestClient

        from app.discovery.registry import ProviderRegistry
        from app.main import create_app

        api_settings = replace(
            _settings(),
            local_embedding_enabled=True,
            local_embedding_model_dir=model_dir,
            review_journal_path=_state_dir() / "review-local" / "journal.ndjson",
        )
        api_app = create_app(api_settings)
        api_registry = ProviderRegistry(api_settings, api_app.state.store)
        api_registry._cache["local-embeddinggemma"] = provider
        api_app.state.providers = api_registry
        api = TestClient(api_app)
        thread_before = api.get("/api/threads/REQ-001", params={"baseline": "baseline-a"})
        assert thread_before.status_code == 200, thread_before.text
        empty = api.post(
            "/api/discovery",
            json={
                "artifact_id": "CODE-001",
                "provider": "local-embeddinggemma",
                "baseline": "baseline-a",
            },
        )
        thread_after = api.get("/api/threads/REQ-001", params={"baseline": "baseline-a"})
        assert thread_after.status_code == 200, thread_after.text
        assert thread_after.json() == thread_before.json()
        thread_body = thread_after.json()
        assert isinstance(thread_body["accepted_links"], list)
        assert isinstance(thread_body["proposed_links"], list)
        after = (
            store.list_links("baseline-a"),
            store.list_evidence("baseline-a"),
            evaluator.evaluate("baseline-a"),
        )
        import os
        import socket

        try:
            socket.create_connection(("192.0.2.1", 9), timeout=1)
            external_egress = True
        except OSError:
            external_egress = False
        record = {
            "model_dir": str(model_dir),
            "model_version": provider.model_version,
            "index_revision": binding,
            "weights_digest": runtime.weights_digest,
            "manifest_weights_digest": args.get("weights_digest"),
            "runtime": runtime.runtime_version,
            "formatting": provider.formatting_version,
            "baseline": "baseline-a",
            "git": store.commit_of("baseline-a"),
            "load_seconds": round(load_seconds, 3),
            "index_seconds": round(index_seconds, 3),
            "query_latency_ms": [round(value, 1) for value in latencies],
            "results": result_sets,
            "candidates": _jsonable(candidates),
            "trimmed": _jsonable(trimmed),
            "sources": _jsonable(sources),
            "tests": _jsonable(tests),
            "incompatible": _jsonable(incompatible),
            "requirements": _jsonable(requirements),
            "empty_source": _jsonable(empty_source),
            "empty_response": {"status": empty.status_code, "body": empty.json()},
            "expected_binding": expected_binding,
            "binding_matches_fixture": binding == expected_binding,
            "top_k_rejected": top_k_rejected,
            "thread_accepted_links": thread_body["accepted_links"],
            "thread_proposed_links": thread_body["proposed_links"],
            "thread_equal": thread_after.json() == thread_before.json(),
            "no_link_fields": all(
                not hasattr(item, "link_id") and not hasattr(item, "review_state")
                for item in candidates
            ),
            "unchanged": before == after,
            "external_egress": external_egress,
            "egress_denied_env": os.environ.get("CTA_EGRESS_DENIED") == "1",
            "network_namespace": os.readlink("/proc/self/ns/net"),
        }
        if args.get("output"):
            Path(args["output"]).parent.mkdir(parents=True, exist_ok=True)
            Path(args["output"]).write_text(
                json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8"
            )
        return record

    raise RuntimeError(f"unknown local embedding action {action!r}")


OPS = {
    "repo": op_repo,
    "repo_from_fixture": op_repo_from_fixture,
    "blob_text": op_blob_text,
    "blob_hash": op_blob_hash,
    "thread_without_examples": op_thread_without_examples,
    "commit": op_commit,
    "write": op_write,
    "git": op_git,
    "ingest": op_ingest,
    "artifact": op_artifact,
    "artifacts": op_artifacts,
    "thread": op_thread,
    "link": op_link,
    "links": op_links,
    "findings": op_findings,
    "api": op_api,
    "snapshot": op_snapshot,
    "changed": op_changed,
    "evidence": op_evidence,
    "artifact_diff": op_artifact_diff,
    "commit_manifest": op_commit_manifest,
    "manifest": op_manifest,
    "settings": op_settings,
    "schema_version": op_schema_version,
    "discover": op_discover,
    "provider_error": op_provider_error,
    "build_fixture": op_build_fixture,
    "fixture_tests": op_fixture_tests,
    "commitlint": op_commitlint,
    "code_retrieval": op_code_retrieval,
    "answer": op_answer,
    "rag_benchmark": op_rag_benchmark,
    "candidate_benchmark": op_candidate_benchmark,
    "dataset_variant": op_dataset_variant,
    "hashes": op_hashes,
    "review": op_review,
    "local_embedding": op_local_embedding,
    "retrieval_lifecycle": op_retrieval_lifecycle,
    "shallow_clone": op_shallow_clone,
    "external_build": op_external_build,
    "fixture_repo": op_fixture_repo,
    "inventory": op_inventory,
    "assurance": op_assurance,
    "assurance_fixture": op_assurance_fixture,
    "tracked": op_tracked,
}


def main() -> int:
    request = json.loads(sys.stdin.read())
    op = request.get("op")
    handler = OPS.get(op)
    if handler is None:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": {
                        "type": "BridgeError",
                        "code": "unknown-op",
                        "detail": f"unknown operation {op!r}",
                    },
                }
            )
        )
        return 3
    try:
        result = handler(request.get("args", {}))
    except DomainError as exc:
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": {"type": type(exc).__name__, "code": exc.code, "detail": exc.detail},
                }
            )
        )
        return 0
    except Exception as exc:  # noqa: BLE001 - expected application rejections surface here
        print(
            json.dumps(
                {
                    "ok": False,
                    "error": {"type": type(exc).__name__, "code": None, "detail": str(exc)},
                }
            )
        )
        return 0
    print(json.dumps({"ok": True, "result": result}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
