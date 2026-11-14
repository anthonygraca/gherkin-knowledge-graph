#!/usr/bin/env python3
"""Write a hash manifest of the dirty working tree used for a review submission.

A review packet that names hashes must name the files the reviewer actually sees. This tool records
every changed or untracked (non-ignored) path and its SHA-256, plus the base commit, so a dirty-tree
submission is reproducible evidence rather than a claim.

    python tools/dirty_manifest.py --out docs/reports/omp-m2-milestone/dirty-tree-manifest.txt
"""

from __future__ import annotations

import argparse
import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    status = _git("status", "--porcelain", "--untracked-files=all", "--", ".")
    base = _git("rev-parse", "HEAD").strip()
    lines = [f"base_commit {base}", f"state {_git('status', '--porcelain').strip() or 'clean'}"]
    seen: set[str] = set()
    out_relative = str(args.out.resolve().relative_to(ROOT))
    excluded = (
        ".agents/",
        ".omp/",
        "skills-lock.json",
        ".build/",
        "review-1-stdout.log",
        "review-2-stdout.log",
        "review-3-stdout.log",
    )
    for row in status.splitlines():
        path = row[3:].strip()
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        path = path.strip('"')
        if (
            path in seen
            or path.startswith(excluded)
            or path == out_relative
            or __import__("re").fullmatch(r"review-\d+-stdout\.log", Path(path).name)
        ):
            continue
        seen.add(path)
        target = ROOT / path
        if target.is_file():
            digest = hashlib.sha256(target.read_bytes()).hexdigest()
            lines.append(f"file {path} sha256:{digest}")
        elif target.is_dir():
            for child in sorted(target.rglob("*")):
                if not child.is_file():
                    continue
                relative = str(child.relative_to(ROOT))
                if relative in seen:
                    continue
                seen.add(relative)
                digest = hashlib.sha256(child.read_bytes()).hexdigest()
                lines.append(f"file {relative} sha256:{digest}")
        else:
            lines.append(f"deleted {path}")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text("\n".join(sorted(lines)) + "\n", encoding="utf-8")
    print(f"wrote {args.out} ({len(lines) - 2} entries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
