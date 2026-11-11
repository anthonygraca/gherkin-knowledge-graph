"""R2+R4 re-check: mispartitioned thread file and unsupported schema versions are rejected."""

import json
import shutil
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.domain.api import ThreadResponse
from app.main import create_app
from app.settings import Settings

root = Path.cwd()
client = TestClient(create_app())

thread = client.get("/api/threads/REQ-002?baseline=baseline-a").json()
thread["accepted_links"] = thread.pop("proposed_links")
thread["proposed_links"] = []
try:
    ThreadResponse.model_validate(thread)
    print("R2 model: ACCEPTED (BAD)")
except ValidationError as exc:
    print("R2 model: rejected, mentions accepted_links:", "accepted_links" in str(exc))

with tempfile.TemporaryDirectory(prefix="cta-m0-contract-") as d:
    fixtures = Path(d) / "fixtures"
    shutil.copytree(root / "fixtures/api-responses", fixtures / "api-responses")
    shutil.copytree(root / "fixtures/banking-demo/expected", fixtures / "banking-demo" / "expected")
    app = create_app(Settings(repo_root=root, fixtures_dir=fixtures))
    c = TestClient(app)

    path = fixtures / "api-responses/threads/REQ-002.baseline-a.json"
    path.write_text(json.dumps(thread))
    r = c.get("/api/threads/REQ-002?baseline=baseline-a")
    print("R2 http mispartitioned thread:", r.status_code, r.json().get("code"))

    for relative, url in (
        ("threads/REQ-001.baseline-a.json", "/api/threads/REQ-001?baseline=baseline-a"),
        ("findings.baseline-a.json", "/api/findings?baseline=baseline-a"),
    ):
        path = fixtures / "api-responses" / relative
        data = json.loads(path.read_text())
        data["schema_version"] = "999.0.0"
        path.write_text(json.dumps(data))
        r = c.get(url)
        body = r.json()
        print(
            f"R4 http {relative}:",
            r.status_code,
            body.get("code"),
            "| mentions 999.0.0:",
            "999.0.0" in body.get("detail", ""),
        )

    snapshot_path = fixtures / "api-responses/snapshot.json"
    snapshot = json.loads(snapshot_path.read_text())
    snapshot["schema_version"] = "999.0.0"
    snapshot_path.write_text(json.dumps(snapshot))
    try:
        create_app(Settings(repo_root=root, fixtures_dir=fixtures))
        print("R4 snapshot: ACCEPTED (BAD)")
    except Exception as exc:  # noqa: BLE001 - probe wants the concrete type name
        print("R4 snapshot: rejected ->", type(exc).__name__)
