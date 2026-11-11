"""Consolidated evidence run bound to the frozen snapshot.

Runs every gate and the R1-R7 probes, capturing stdout/stderr/exit per command.
"""

import subprocess
import time
from pathlib import Path

REPO = Path(
    "/home/anthonygraca/CSU Fullerton Dropbox/Anthony Graca/"
    "cpsc-583-knowledge-representation/project/gherkin-knowledge-graph"
)
SCRATCH = Path("/tmp/cta-rereview-1/evidence")
SCRATCH.mkdir(parents=True, exist_ok=True)

COMMANDS = [
    ("gate_pytest", ["uv", "run", "--project", "backend", "pytest", "backend/tests", "-q"]),
    ("gate_verify", ["uv", "run", "--project", "backend", "python", "tools/fixturectl.py", "verify"]),
    ("gate_ruff_check", ["uv", "run", "--project", "backend", "ruff", "check", "."]),
    ("gate_ruff_format", ["uv", "run", "--project", "backend", "ruff", "format", "--check", "."]),
    ("gate_git_diff_check", ["git", "diff", "--check"]),
    ("probe_r1", ["uv", "run", "--project", "backend", "python", "/tmp/cta-rereview-1/p_r1_port.py"]),
    ("probe_r2_r4", ["uv", "run", "--project", "backend", "python", "/tmp/cta-rereview-1/p_r2_r4_http.py"]),
    ("probe_r3", ["uv", "run", "--project", "backend", "python", "/tmp/cta-rereview-1/p_r3_verify.py"]),
    ("probe_r5", ["uv", "run", "--project", "backend", "python", "/tmp/cta-rereview-1/p_r5_hash.py"]),
    ("probe_r6", ["uv", "run", "--project", "backend", "python", "/tmp/cta-rereview-1/p_r6_mutation.py"]),
    (
        "probe_r7",
        [
            "uv", "run", "--project", "backend", "python",
            "tools/fixturectl.py", "build", "&&",
        ],
    ),
    ("net_denied", ["unshare", "-rn", "sh", "/tmp/cta-rereview-1/net_denied.sh"]),
]

for name, command in COMMANDS:
    if name == "probe_r7":
        # build first (separate run), then the worktree probe
        subprocess.run(
            ["uv", "run", "--project", "backend", "python", "tools/fixturectl.py", "build"],
            cwd=REPO, capture_output=True, text=True, check=False,
        )
        command = [
            "uv", "run", "--project", "backend", "python",
            "/tmp/cta-rereview-1/p_r7_worktree.py",
        ]
    start = time.time()
    result = subprocess.run(command, cwd=REPO, capture_output=True, text=True)
    elapsed = time.time() - start
    payload = (
        f"$ {' '.join(command)}\nexit={result.returncode} elapsed={elapsed:.1f}s\n"
        f"--- stdout ---\n{result.stdout}\n--- stderr ---\n{result.stderr}"
    )
    (SCRATCH / f"{name}.txt").write_text(payload, encoding="utf-8")
    print(f"{name}: exit={result.returncode} elapsed={elapsed:.1f}s")
