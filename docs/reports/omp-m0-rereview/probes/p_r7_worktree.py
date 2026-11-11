"""R7 re-check: the review prompt's corrected fixture-test invocation works.

Runs the fixture suite from each worktree root with an absolute backend interpreter, then
shows the old outside-the-worktree invocation still fails collection (the prompt's rationale).
"""

import subprocess
import sys
import tempfile
from pathlib import Path

repo = Path("fixtures/banking-demo/.build/repo").resolve()
python = str(Path(sys.executable).absolute())
print("repo:", repo)
print("python:", python)

with tempfile.TemporaryDirectory(prefix="cta-acceptance-") as temporary:
    for tag in ("baseline-a", "baseline-b"):
        worktree = Path(temporary) / tag
        subprocess.run(
            ["git", "-C", str(repo), "worktree", "add", "--detach", str(worktree), tag],
            check=True,
        )
        try:
            result = subprocess.run(
                [python, "-m", "pytest", "-q", "--tb=short"],
                cwd=worktree,
                text=True,
                capture_output=True,
                check=False,
            )
            print(f"--- {tag}: exit={result.returncode}")
            print(result.stdout.strip()[-900:])
        finally:
            subprocess.run(
                ["git", "-C", str(repo), "worktree", "remove", "--force", str(worktree)],
                check=True,
            )

    # the pre-repair invocation style (absolute path from outside) remains a collection error
    worktree = Path(temporary) / "outside"
    subprocess.run(
        ["git", "-C", str(repo), "worktree", "add", "--detach", str(worktree), "baseline-a"],
        check=True,
    )
    try:
        result = subprocess.run(
            [python, "-m", "pytest", "-q", f"{worktree}/tests"],
            cwd=Path.cwd(),
            text=True,
            capture_output=True,
            check=False,
        )
        print(f"--- outside-invocation: exit={result.returncode}")
        print(result.stdout.strip()[-500:])
    finally:
        subprocess.run(
            ["git", "-C", str(repo), "worktree", "remove", "--force", str(worktree)],
            check=True,
        )
