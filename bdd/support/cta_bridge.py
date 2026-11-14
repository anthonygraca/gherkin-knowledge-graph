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
    "hashes": op_hashes,
    "shallow_clone": op_shallow_clone,
    "external_build": op_external_build,
    "fixture_repo": op_fixture_repo,
    "inventory": op_inventory,
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
