"""R5 re-check: build is reproducible and pinned against caller Git configuration."""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "tools"))
import fixturectl as f  # noqa: E402
from app.domain.oracle import BaselinesManifest  # noqa: E402
from app.persistence.fixtures import load_model  # noqa: E402

committed = load_model(
    Path("fixtures/banking-demo/expected/baselines.json"), BaselinesManifest
)
with tempfile.TemporaryDirectory(prefix="cta-m0-repro-") as d:
    root = Path(d)
    first = f.build_repo(f.FIXTURE_DIR, root / "one")
    second = f.build_repo(f.FIXTURE_DIR, root / "two")
    print(
        "different directories, tags equal:",
        first.tags == second.tags,
        "| equals committed:",
        first.tags == committed.tags,
    )

    cfg = root / "global.gitconfig"
    subprocess.run(
        ["git", "config", "--file", str(cfg), "commit.gpgsign", "true"], check=True
    )
    os.environ.update({"GIT_CONFIG_GLOBAL": str(cfg), "TZ": "Pacific/Honolulu"})
    third = f.build_repo(f.FIXTURE_DIR, root / "signed-tz")
    print(
        "global commit.gpgsign=true + TZ=Pacific/Honolulu, tags equal committed:",
        third.tags == committed.tags,
    )

    os.environ["GIT_DEFAULT_HASH"] = "sha256"
    fourth = f.build_repo(f.FIXTURE_DIR, root / "sha256")
    print("GIT_DEFAULT_HASH=sha256, tags equal committed:", fourth.tags == committed.tags)
    print("committed tags:", committed.tags)
    print("sha256-env tags:", fourth.tags)
