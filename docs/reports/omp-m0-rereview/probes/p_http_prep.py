"""Prepare a tampered fixture copy for the live-HTTP negative probes."""

import json
import shutil
from pathlib import Path

root = Path.cwd()
dst = Path("/tmp/cta-rereview-1/tampered-fixtures")
if dst.exists():
    shutil.rmtree(dst)
dst.mkdir(parents=True)
shutil.copytree(root / "fixtures/api-responses", dst / "api-responses")
shutil.copytree(root / "fixtures/banking-demo/expected", dst / "banking-demo" / "expected")

thread = dst / "api-responses/threads/REQ-002.baseline-a.json"
payload = json.loads(thread.read_text(encoding="utf-8"))
payload["accepted_links"] = payload.pop("proposed_links")
payload["proposed_links"] = []
thread.write_text(json.dumps(payload), encoding="utf-8")

findings = dst / "api-responses/findings.baseline-a.json"
payload = json.loads(findings.read_text(encoding="utf-8"))
payload["schema_version"] = "999.0.0"
findings.write_text(json.dumps(payload), encoding="utf-8")

print("tampered fixtures ready:", dst)
