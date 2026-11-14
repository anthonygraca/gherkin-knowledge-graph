#!/usr/bin/env python3
"""Build the deterministic Git histories for the external-style fixtures.

Why a builder: the portable path must index a *pinned commit in a Git repository*, not a directory
of files. The two fixtures under ``fixtures/external-*/tree`` are ordinary projects that never
adopted CTA conventions; this script materializes them as real repositories with fixed identities,
dates, messages, and tags so every machine produces the same SHAs.

This script writes only under the destination directory. It never touches the fixture sources and
never runs anything from the built repository.

    uv run --project backend python tools/external_fixture.py build --dest /tmp/cta-external
    uv run --project backend python tools/external_fixture.py show-refs --dest /tmp/cta-external
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = {
    "external-recipes": ROOT / "fixtures" / "external-recipes",
    "external-twin": ROOT / "fixtures" / "external-twin",
}

GIT_IDENTITY = {
    "GIT_AUTHOR_NAME": "External Fixture Bot",
    "GIT_AUTHOR_EMAIL": "external@example.invalid",
    "GIT_COMMITTER_NAME": "External Fixture Bot",
    "GIT_COMMITTER_EMAIL": "external@example.invalid",
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_SYSTEM": os.devnull,
    "GIT_DEFAULT_HASH": "sha1",
    "LC_ALL": "C",
    "TZ": "UTC",
}


def git(args: list[str], *, cwd: Path, env: dict[str, str] | None = None) -> str:
    merged = {**os.environ, **GIT_IDENTITY, **(env or {})}
    result = subprocess.run(
        ["git", *args], cwd=cwd, env=merged, capture_output=True, text=True, check=False
    )
    if result.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} failed in {cwd}: {result.stderr.strip()}")
    return result.stdout


def copy_tree(source: Path, dest: Path) -> None:
    for path in sorted(source.rglob("*")):
        if path.is_dir():
            continue
        target = dest / path.relative_to(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)


def build_repo(fixture_dir: Path, dest: Path) -> dict[str, str]:
    """Materialize one fixture's declarative history and return ``tag -> commit``."""
    history = json.loads((fixture_dir / "history.json").read_text(encoding="utf-8"))
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    git(["init", "--quiet", "-b", "main"], cwd=dest)
    git(["config", "user.name", GIT_IDENTITY["GIT_AUTHOR_NAME"]], cwd=dest)
    git(["config", "user.email", GIT_IDENTITY["GIT_AUTHOR_EMAIL"]], cwd=dest)
    tags: dict[str, str] = {}
    for commit in history["commits"]:
        copy_tree(fixture_dir / commit["overlay"], dest)
        git(["add", "-A"], cwd=dest)
        date = commit["date"]
        git(
            ["commit", "--quiet", "--allow-empty", "-m", commit["message"]],
            cwd=dest,
            env={"GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date},
        )
        sha = git(["rev-parse", "HEAD"], cwd=dest).strip()
        for tag in commit.get("tags", []):
            git(["tag", tag, sha], cwd=dest)
            tags[tag] = sha
    return tags


def build_all(dest_root: Path) -> dict[str, dict[str, str]]:
    dest_root.mkdir(parents=True, exist_ok=True)
    return {
        name: build_repo(fixture_dir, dest_root / name)
        for name, fixture_dir in sorted(FIXTURES.items())
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    build = subparsers.add_parser("build", help="build both fixture repositories")
    build.add_argument("--dest", type=Path, default=None)
    show = subparsers.add_parser("show-refs", help="print tag -> commit for a built tree")
    show.add_argument("--dest", type=Path, default=None)
    args = parser.parse_args(argv)
    dest = args.dest or Path(tempfile.mkdtemp(prefix="cta-external-"))
    if args.command == "build":
        refs = build_all(dest)
        print(json.dumps(refs, indent=2, sort_keys=True))
        return 0
    refs = {
        name: {
            tag: git(["rev-parse", tag], cwd=dest / name).strip()
            for tag in git(["tag"], cwd=dest / name).split()
        }
        for name in FIXTURES
        if (dest / name).is_dir()
    }
    print(json.dumps(refs, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
