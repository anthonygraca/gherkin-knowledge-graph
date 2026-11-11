"""R6 re-check: a sha256->sha1 fingerprint mutation must now fail the suite.

Reproduces the reviewer's disposable-clone mutation, offline, in a temp directory.
"""

import subprocess
import tempfile
from pathlib import Path

with tempfile.TemporaryDirectory(prefix="cta-m0-fingerprint-mutation-") as d:
    clone = Path(d) / "clone"
    subprocess.run(["git", "clone", "--quiet", "--no-hardlinks", ".", str(clone)], check=True)
    path = clone / "backend/app/domain/models.py"
    text = path.read_text(encoding="utf-8")
    assert "hashlib.sha256(payload.encode" in text
    mutated = text.replace("hashlib.sha256(payload.encode", "hashlib.sha1(payload.encode")
    path.write_text(mutated, encoding="utf-8")

    commands = [
        ["uv", "sync", "--offline", "--frozen", "--project", "backend"],
        ["uv", "run", "--offline", "--project", "backend", "python", "tools/fixturectl.py", "all"],
        ["uv", "run", "--offline", "--project", "backend", "pytest", "backend/tests", "-q"],
    ]
    for command in commands:
        result = subprocess.run(command, cwd=clone, text=True, capture_output=True)
        lines = [line for line in (result.stdout + result.stderr).splitlines() if line.strip()]
        print(f"$ {' '.join(command)}\nexit={result.returncode}")
        print("\n".join(lines[-12:]))
        print("---")
