"""Throwaway recheck for review finding R1: same head, two bases -> applicability changes.

The CI trigger gap (missing `edited`) means a retargeted PR never re-checks the newly
applicable range. This probe demonstrates the range behavior the fix must schedule:
the unchanged head passes when the unlinked ancestor is excluded by the base and fails
when the adoption baseline is the base, making that ancestor applicable.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys
import tempfile

REPO = pathlib.Path(
    "/home/anthonygraca/CSU Fullerton Dropbox/Anthony Graca/"
    "cpsc-583-knowledge-representation/project/gherkin-knowledge-graph"
)
sys.path.insert(0, str(REPO / "tools"))
import commitlint  # noqa: E402  (tools/ path, same mechanism as the test suite)

ISSUE_MAP = """## Features
| F-01 | [#7](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/7) |
## User stories
| SETUP-01 | [#8](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/8) |
"""

with tempfile.TemporaryDirectory(prefix="cta-r1-repro-") as temporary:
    repo = pathlib.Path(temporary) / "repo"
    repo.mkdir()
    env = dict(os.environ, GIT_CONFIG_GLOBAL=os.devnull, GIT_CONFIG_SYSTEM=os.devnull)

    def g(*args: str) -> str:
        result = subprocess.run(
            ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True, env=env
        )
        return result.stdout.strip()

    g("init", "-b", "main")
    g("config", "user.name", "R1 repro")
    g("config", "user.email", "r1@example.invalid")
    (repo / "docs").mkdir()
    (repo / commitlint.ISSUE_MAP).write_text(ISSUE_MAP, encoding="utf-8")

    (repo / "f.txt").write_text("a", encoding="utf-8")
    g("add", ".")
    g("commit", "-m", "legacy baseline commit")
    baseline = g("rev-parse", "HEAD")

    (repo / "f.txt").write_text("b", encoding="utf-8")
    g("add", ".")
    g("commit", "-m", "unlinked change")  # must be reported when it becomes applicable
    unlinked = g("rev-parse", "HEAD")

    (repo / "f.txt").write_text("c", encoding="utf-8")
    g("add", ".")
    g("commit", "-m", "ci: [issue #8] head change")
    head = g("rev-parse", "HEAD")

    commitlint.LEGACY_BASELINE = baseline

    print(f"head={head[:12]} unlinked-ancestor={unlinked[:12]} baseline={baseline[:12]}")
    rc_unlinked_excluded = commitlint.main(["--repo", str(repo), "--base", unlinked, "--head", head])
    rc_baseline_base = commitlint.main(["--repo", str(repo), "--base", baseline, "--head", head])
    print(f"base=unlinked (ancestor excluded) -> exit {rc_unlinked_excluded} (expect 0)")
    print(f"base=baseline (ancestor applicable) -> exit {rc_baseline_base} (expect 1)")
    print(f"same head in both cases: {head}")
    assert rc_unlinked_excluded == 0 and rc_baseline_base == 1
    print("R1 recheck: PASS")
