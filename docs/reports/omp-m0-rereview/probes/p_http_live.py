"""Live-HTTP probes: pristine server (8031) and tampered server (8032)."""

import httpx

pristine = httpx.Client(base_url="http://127.0.0.1:8031", timeout=15)
tampered = httpx.Client(base_url="http://127.0.0.1:8032", timeout=15)

health = pristine.get("/health")
print("health:", health.status_code, health.json()["schema_version"], health.json()["baselines"])

thread = pristine.get("/api/threads/REQ-001", params={"baseline": "baseline-b"}).json()
print(
    "thread REQ-001 @baseline-b:",
    [link["link_id"] for link in thread["accepted_links"]],
    "evidence:",
    [item["evidence_id"] for item in thread["evidence"]],
    "baseline field:",
    thread["baseline"],
)

findings = pristine.get("/api/findings", params={"baseline": "baseline-b"}).json()
print(
    "findings @baseline-b:",
    sorted({item["finding_type"] for item in findings["findings"]}),
)

discovery = pristine.post("/api/discovery", json={"artifact_id": "SCN-001"}).json()
top = discovery["candidates"][0]
print(
    "discovery SCN-001 rank1:",
    top["target_id"],
    top["rank"],
    "| link_id key present:",
    "link_id" in top,
    "| review_state key present:",
    "review_state" in top,
)

evaluate = pristine.post("/api/assurance/evaluate", json={"baseline": "baseline-a"})
print(
    "POST /api/assurance/evaluate:",
    evaluate.status_code,
    evaluate.json()["code"],
    "|",
    evaluate.json()["story"],
    "|",
    evaluate.json()["milestone"],
)

sha = health.json()["baseline_commits"]["baseline-a"]
by_tag = pristine.get("/api/artifacts/REQ-001", params={"baseline": "baseline-a"}).content
by_sha = pristine.get("/api/artifacts/REQ-001", params={"baseline": sha}).content
print("artifact tag/SHA bodies identical:", by_tag == by_sha)

unknown = pristine.get("/api/artifacts/REQ-999")
malformed = pristine.get("/api/artifacts/not-an-id")
unknown_baseline = pristine.get("/api/findings", params={"baseline": "baseline-z"})
print("unknown artifact:", unknown.status_code, unknown.json()["code"])
print("malformed id:", malformed.status_code, malformed.json()["code"])
print("unknown baseline:", unknown_baseline.status_code, unknown_baseline.json()["code"])

mispartitioned = tampered.get("/api/threads/REQ-002", params={"baseline": "baseline-a"})
unsupported = tampered.get("/api/findings", params={"baseline": "baseline-a"})
still_ok = tampered.get("/api/threads/REQ-001", params={"baseline": "baseline-b"})
print(
    "tampered server mispartitioned thread:",
    mispartitioned.status_code,
    mispartitioned.json().get("code"),
)
print(
    "tampered server unsupported findings version:",
    unsupported.status_code,
    unsupported.json().get("code"),
    "| mentions 999.0.0:",
    "999.0.0" in unsupported.json().get("detail", ""),
)
print("tampered server unaffected thread:", still_ok.status_code)
