"""The committed generated fixtures must be exactly what the generator produces now.

This is the guard behind every other fixture-based test and behind CI: without it, a stale
``snapshot.json`` or ``baselines.json`` would let the suite pass against data the generator no
longer produces.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
API_DIR = REPO_ROOT / "fixtures" / "api-responses"


def run_verify(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "tools/fixturectl.py", "verify", *args],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )


def test_committed_generated_files_are_current() -> None:
    result = run_verify()
    assert result.returncode == 0, result.stdout + result.stderr
    assert "reproducible" in result.stdout


def test_drift_detection_fails_when_a_generated_file_is_edited(tmp_path: Path) -> None:
    tampered_api = tmp_path / "api-responses"
    shutil.copytree(API_DIR, tampered_api)
    target = tampered_api / "findings.baseline-b.json"
    payload = target.read_text(encoding="utf-8")
    target.write_text(
        payload.replace("reverification_required", "verification_failed"), encoding="utf-8"
    )

    result = run_verify("--api-dir", str(tampered_api))
    assert result.returncode == 1
    assert "findings.baseline-b.json" in result.stderr
    assert "fixturectl.py all" in result.stderr


def test_drift_detection_fails_when_a_generated_file_is_missing(tmp_path: Path) -> None:
    tampered_api = tmp_path / "api-responses"
    shutil.copytree(API_DIR, tampered_api)
    (tampered_api / "snapshot.json").unlink()

    result = run_verify("--api-dir", str(tampered_api))
    assert result.returncode == 1
    assert "missing from the repository" in result.stderr


def test_drift_detection_fails_when_the_baseline_manifest_is_tampered(tmp_path: Path) -> None:
    """Review R3: a directory walker cannot verify a single file, and reported false success."""
    manifest = tmp_path / "baselines.json"
    payload = json.loads(
        (REPO_ROOT / "fixtures/banking-demo/expected/baselines.json").read_text(encoding="utf-8")
    )
    payload["tags"]["baseline-a"] = "0" * 40
    manifest.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")

    result = run_verify("--baselines", str(manifest))
    assert result.returncode == 1
    assert "baselines.json" in result.stderr
    assert "out of date" in result.stderr


def test_drift_detection_fails_when_the_baseline_manifest_is_missing(tmp_path: Path) -> None:
    """Review R3: deleting the manifest must be reported, not silently accepted."""
    missing = tmp_path / "baselines.json"

    result = run_verify("--baselines", str(missing))
    assert result.returncode == 1
    assert "missing from the repository" in result.stderr
    assert "baselines.json" in result.stderr
