"""R3 re-check: `fixturectl.py verify` fails for a tampered or deleted baseline manifest."""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path.cwd()
source = root / "fixtures/banking-demo/expected/baselines.json"

with tempfile.TemporaryDirectory(prefix="cta-m0-manifest-") as d:
    scratch = Path(d)
    tampered = scratch / "baselines.json"
    data = json.loads(source.read_text(encoding="utf-8"))
    data["tags"]["baseline-a"] = "0" * 40
    tampered.write_text(json.dumps(data), encoding="utf-8")
    missing = scratch / "sub" / "baselines.json"

    for label, path in (("tampered", tampered), ("deleted", missing)):
        result = subprocess.run(
            [sys.executable, "tools/fixturectl.py", "verify", "--baselines", str(path)],
            cwd=root,
            text=True,
            capture_output=True,
            check=False,
        )
        output = (result.stdout + result.stderr).strip()
        print(f"R3 manifest {label}: exit={result.returncode}")
        print(output)
        print("---")
