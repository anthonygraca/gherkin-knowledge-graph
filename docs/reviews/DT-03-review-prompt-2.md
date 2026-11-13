# Independent implementation review — DT-03, submission 2 of 7

## 1. Submission context and prior dispositions

**Task:** DT-03 — Typed, provenance-aware traceability links with review state.
**Roadmap:** F-03 Links, roadmap §6 DT-03; milestone **M1 — AI-free vertical slice**.
**GitHub story:** issue **#22**, verified OPEN 2026-11-13T02:50:26Z. **Owner:** B.
**Implementer/integrator:** OMP. **Repository:** `<task_repo>` (read-only sandbox).
**Base:** `590e776b67d9e340f9e68df04472222ee4fd0720` (`main`, DT-02 merge).
**Branch:** `feat/22-dt-03-links`. **Submission:** 2 of 7.

Round 1 (`docs/reviews/DT-03-review.md`) returned REQUEST_CHANGES:

* **R1** — the file-level review-state error omitted the affected link ids (SCN-605).
* **R2** — the packet's `scan.py` dependency pointer was stale (evidence identity).
* **R3** — the duplicate-id mapping claimed cross-file coverage that the test did not exercise.

All three are addressed; no finding was dismissed. The corrected `scan.py` pointer for this base is
`2a602ee3668bd1560e42aa8870c6a1875b3977a082d449109892852c73e0a613` (the DT-02 file), not the
DT-01 value that appeared in submission 1.

### User outcome

An engineer can read the declared relationships for a revision with their provenance and review
state, knowing that a proposal never appears as an accepted relationship and that a link cannot
silently contradict the relation vocabulary.

### Scope / non-goals (unchanged)

Read and validate accepted/proposed link files; return artifacts + links through
`ingest_revision`. Non-goals: mutation/review decisions (AS-06), evidence/threads (DT-04), findings,
discovery.

### Proposed commit reference

`feat(links): [issue #22] ingest typed traceability links with review state`, body `Refs #22`.

## 2. Acceptance criteria (canonical snapshot)

File `docs/stories/DT-03.feature`, sha256
`d6e390d908616388cbc69ae2dbabd5371ef6a15115a83b447f7696dbf6c83200` (unchanged).

```gherkin
# Canonical acceptance specification for DT-03 (#22), M1.
# Source criteria: the GitHub story intake at
# https://github.com/anthonygraca/gherkin-knowledge-graph/issues/22 (verified 2026-11-13T02:50:26Z)
# and roadmap §6 F-03. Failure scenarios were added during refinement; the two intake scenarios
# keep their wording.
# Verified by the pytest selectors mapped in DT-03.md. These scenarios are not currently bound
# to or executed by a Gherkin runner.
@DT-03 @issue-22 @M1
Feature: DT-03: Typed, provenance-aware traceability links with review state
  Links are directional claims: requirement --verified_by--> scenario,
  scenario --implemented_by--> source, scenario --exercised_by--> test. Accepted links and
  proposals live in separate declared files and are never merged into one collection. Ingestion
  validates direction, endpoints, and declared review state; it does not mutate links.

  @SCN-601
  Scenario: Accepted relationship recorded with provenance
    Given an accepted link between "REQ-001" and "SCN-001" of type "verified_by"
    When the link is read back
    Then its review_state is "accepted"
    And its provenance records the reviewer and the decision time

  @SCN-602
  Scenario: Proposals never appear as accepted relationships
    Given "LNK-007" proposes "REQ-002" verified_by "SCN-002"
    When the links for "REQ-002" are listed
    Then "LNK-007" appears only in the proposed collection
    And the accepted collection is empty

  @SCN-603
  Scenario: A link that contradicts its relation direction is rejected
    Given a link from "CODE-001" to "SCN-001" of type "verified_by"
    When the revision is ingested
    Then ingestion fails with an error naming the link and the expected direction

  @SCN-604
  Scenario: A link to an unknown artifact is rejected
    Given a link whose target "SCN-999" does not exist at the revision
    When the revision is ingested
    Then ingestion fails with an error naming "SCN-999"

  @SCN-605
  Scenario: A link file declaring the wrong review state is rejected
    Given "evidence/accepted-links.json" contains a link with review_state "proposed"
    When the revision is ingested
    Then ingestion fails with an error naming the file and the link

  @SCN-606
  Scenario: Repeated ingestion returns identical link facts
    Given a revision with accepted and proposed links
    When the revision is ingested twice
    Then the link ids, review states, provenance, and timestamps are identical
    And no decision history is rewritten
```

Refinement disposition: owner-authored issue intake + roadmap §6; failure scenarios were added
without weakening the intake. No separate human refinement sign-off is recorded.

Repository constraints (AGENTS.md): proposals ≠ accepted links ≠ verification; revision-aware
content hashes; offline defaults; independent oracle expectations; contract-only endpoints stay 501.

## 3. Snapshot, manifest, and diff

Snapshot captured 2026-11-13T03:01Z. Manifest (sha256 of every task file):

```text
a2464c7f2edba85f8af1dac6af24efc4a05693fef6188ab6948fb2be4cb554c2  backend/app/domain/enums.py
679eea69414764999a4770725c01000521bbd508135840359ae5949e297e7889  backend/app/domain/oracle.py
3282cea94ca923a47571127b7b0a69c7ee89313ef7014458f48f8dd55ed57397  backend/app/ingestion/__init__.py
3c284b7e421182507ff0b7443b3b1ff036553ec8dc8b0ad1fdfaa497704f4aed  backend/app/ingestion/links.py
0e954a7de6b29700eeb53da38e4ade983428193386a7ccb99fc149b75f0e8e06  backend/app/ingestion/revision.py
f4ef0b02e4d51b1f1712b527fb69aed92e00cf75a44279a27e878e8c3289acc9  backend/tests/test_ingestion_links.py
d6e390d908616388cbc69ae2dbabd5371ef6a15115a83b447f7696dbf6c83200  docs/stories/DT-03.feature
aa2560a7838af3ae1134ba934d61d8758ce9936c90ddab89a60bf56ea4d4290c  docs/stories/DT-03.md
824a17b8ba243530036b61dbe12dda59caad65d5fd8102056b8c0669b66ab666  docs/domain-contracts.md
f2157cad7d2b7b3518f950cc46787bad7c098d977fbc3bf66753b59d39a4d303  docs/architecture.md
45a2af82317439f53a169ac595547acc55640c2220158eb151d3ba2bfde9b8c8  docs/STATUS.md
85d01d3640f5b228934c112d1dd454ce60e6e6111eb63c8052fa64f7221b20ce  docs/reports/omp-dt-03-links/IMPLEMENTATION.md
f5740bbb381dc6fcc9ff33d64bbed48a4557f3f43c504e581b37628aa025f156  docs/reports/omp-dt-03-links/METRICS.md
7e1cf0a760d70eba7abfed7cbe43a32770ef4843f15e53bc2c3020edf6cfdca4  docs/reports/omp-dt-03-links/PROMPT_LOG.md
38eb7a7899c6ae625ae0c52362f3b991800b7b7557e8fa7eb8cf2c4500cf0da0  docs/reviews/DT-03-review-prompt.md
fd2fb073f57653d268e45cdf9964193dbacea4ae0b5414b86440dc4395ce2932  docs/reviews/DT-03-review.md
```

Versions: `SCHEMA_VERSION = 0.1.0`, `PACKAGE_VERSION = 0.1.0`; no dependency change. No generated
fixture, oracle label, generated response, contract shape, or workflow file changed.

### Tracked-file diff (against base)

```diff
diff --git a/backend/app/domain/enums.py b/backend/app/domain/enums.py
index b0ba404..abe23d5 100644
--- a/backend/app/domain/enums.py
+++ b/backend/app/domain/enums.py
@@ -91,3 +91,13 @@ class RuleId(StrEnum):
     VERIFICATION_FAILED = "RULE-VERIFICATION-FAILED"
     CANDIDATE_PENDING_REVIEW = "RULE-CANDIDATE-PENDING-REVIEW"
     LIFECYCLE_SUPERSEDED = "RULE-LIFECYCLE-SUPERSEDED"
+
+
+#: Allowed ``(source type, target type)`` for each relation. Ingestion rejects a link whose
+#: artifact types disagree with this table; the vocabulary and direction are the contract
+#: (docs/domain-contracts.md), not a convention each consumer re-implements.
+RELATION_DIRECTION: dict[RelationType, tuple[ArtifactType, ArtifactType]] = {
+    RelationType.VERIFIED_BY: (ArtifactType.REQUIREMENT, ArtifactType.SCENARIO),
+    RelationType.IMPLEMENTED_BY: (ArtifactType.SCENARIO, ArtifactType.SOURCE),
+    RelationType.EXERCISED_BY: (ArtifactType.SCENARIO, ArtifactType.TEST),
+}
diff --git a/backend/app/domain/oracle.py b/backend/app/domain/oracle.py
index 5612951..cb4075d 100644
--- a/backend/app/domain/oracle.py
+++ b/backend/app/domain/oracle.py
@@ -288,6 +288,13 @@ class FixtureLinkFile(_FrozenModel):
             )
         return self
 
+    @model_validator(mode="after")
+    def _unique_ids(self) -> FixtureLinkFile:
+        identifiers = [link.link_id for link in self.links]
+        if len(identifiers) != len(set(identifiers)):
+            raise ValueError("link ids must be unique within a link file")
+        return self
+
 
 class MaterializedFindings(_FrozenModel):
     """``fixtures/api-responses/findings.<baseline>.json`` — sample findings response."""
diff --git a/docs/STATUS.md b/docs/STATUS.md
index 403ecd8..ec87118 100644
--- a/docs/STATUS.md
+++ b/docs/STATUS.md
@@ -2,10 +2,10 @@
 
 ```text
 Date:                2026-11-13
-Current branch:      feat/21-dt-02-source-test-artifacts (from main 26a25d0)
+Current branch:      feat/22-dt-03-links (from main 590e776)
 Milestone:           M0 — exit gate SATISFIED by re-review round 2 (historical record below)
                      M1 — IN PROGRESS; gate NOT yet satisfied
-Active task:         DT-02 (#21) source and test artifacts tied to path and Git revision
+Active task:         DT-03 (#22) typed, provenance-aware links with review state
 Independent review:  docs/reviews/M0-review.md — first review: "M0 not verified"
                      docs/reviews/M0-rereview-1.md — re-review round 1 (GPT-6.1 Sol, xhigh):
                      NEEDS_INPUT; R1–R7 all repaired; AC-1.1…AC-1.8 and AC-2.1…AC-2.5 all PASS;
@@ -20,9 +20,10 @@ Historical (SETUP-01, 2026-11-12): the commit-reference slice landed via PR #42;
                      had 107 passed; the SETUP-01 tree then had 135 passed (also under an
                      OS-level network denial). Outstanding owner actions: #18/#19 closure, the
                      FT-03/project-definition reviews, the required-check ruleset, README work item.
-Tests executed:      DT-02 (2026-11-13T02:07Z): 197 passed (also under an OS-level network
-                     denial); fixturectl verify exit 0 with the generator reusing the shared
-                     scanner; ruff check/format clean.
+Tests executed:      DT-03 (2026-11-13T02:53Z): 9 focused link tests passed; full suite recorded
+                     in docs/reports/omp-dt-03-links/.
+                     DT-02 approved snapshot: 208 passed; PR #45 merged as 590e776 with both
+                     hosted checks passing; issue #21 closed.
                      DT-01 approved snapshot: 183 passed; PR #44 merged as 26a25d0 with both
                      hosted checks passing; issue #20 closed.
 Current API/schema version: 0.1.0
@@ -46,8 +47,8 @@ not claim that draft as an approved baseline.
 | Story | GitHub | Owner | Canonical feature | State |
 | --- | --- | --- | --- | --- |
 | DT-01 requirements + scenarios parsed | [#20](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/20) | B | [DT-01.feature](stories/DT-01.feature) | **merged** PR [#44](https://github.com/anthonygraca/gherkin-knowledge-graph/pull/44) → `26a25d0`; APPROVE at submission 5; issue closed |
-| DT-02 source/test artifacts | [#21](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/21) | B | [DT-02.feature](stories/DT-02.feature) | refined; implementation in review |
-| DT-03 typed links + review state | [#22](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/22) | B | not yet written | eligible after DT-02 |
+| DT-02 source/test artifacts | [#21](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/21) | B | [DT-02.feature](stories/DT-02.feature) | **merged** PR [#45](https://github.com/anthonygraca/gherkin-knowledge-graph/pull/45) → `590e776`; APPROVE at submission 4; issue closed |
+| DT-03 typed links + review state | [#22](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/22) | B | [DT-03.feature](stories/DT-03.feature) | refined; implementation in review |
 | DT-04 requirement thread | [#23](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/23) | B | not yet written | eligible after DT-03 |
 | AS-01 missing-link finding | [#2](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/2) | C | not yet written | eligible after DT-04 |
 | AS-04 findings/coverage summary | [#26](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/26) | C | not yet written | eligible after AS-01 |
diff --git a/docs/architecture.md b/docs/architecture.md
index 246fb5a..553c1d7 100644
--- a/docs/architecture.md
+++ b/docs/architecture.md
@@ -41,7 +41,7 @@ Two rules explain most of the layout:
 | `app/discovery/fake.py` | Fixture-backed candidate provider | Working implementation (deliberately fake) |
 | `app/assurance/sample_findings.py` | Replay of reviewed sample findings | Mock service (rule engine arrives in C-PR1) |
 | `app/api/` | Routes, dependencies, RFC 9457 problem documents | Working |
-| `app/ingestion/` | Revision-pinned parsing: requirement/Gherkin artifacts (DT-01), source/test annotations (DT-02), links (DT-03), store cutover (DT-04) | Requirements, scenarios, source, and test implemented; links/store absent by design |
+| `app/ingestion/` | Revision-pinned parsing: requirement/Gherkin artifacts (DT-01), source/test annotations (DT-02), links (DT-03), store cutover (DT-04) | Requirements, scenarios, source, test, and links implemented; store cutover remains |
 | `frontend/` | React/TypeScript dashboard | Absent by design; created in C-PR1 |
 
 ## Request flows
diff --git a/docs/domain-contracts.md b/docs/domain-contracts.md
index 2ffd594..95af502 100644
--- a/docs/domain-contracts.md
+++ b/docs/domain-contracts.md
@@ -52,6 +52,12 @@ Direction is `source --relation_type--> target`:
 Adding a relation type is an additive contract change: enum, docs, oracle, and tests in one
 change. Direction ambiguity is a bug — discovery is anchored on `source_id`.
 
+Ingestion validates every declared link: the file's `schema_version` must match, its
+`review_state` must match the file name, ids must be unique within and across the accepted and
+proposed files, both endpoints must exist at the revision, and the source/target artifact types
+must equal `RELATION_DIRECTION[relation_type]`. A violation fails ingestion; links are never
+silently dropped. The table in `app/domain/enums.py` is the executable form of this section.
+
 ## Review states
 
 `proposed` → `accepted` | `rejected`. Only humans (or the fixture) set these. Consequences:
```

### Changed since submission 1 (complete)

`backend/app/ingestion/links.py`:
```python
"""Ingest declared traceability links from a repository revision.

Links are read, never written here: accepted and proposed relationships live in separate files,
ingestion validates them, and no code path can promote a proposal. Review decisions are AS-06.
"""

from __future__ import annotations

import json

from pydantic import ValidationError

from app.domain.enums import RELATION_DIRECTION, ReviewState
from app.domain.models import Artifact, TraceLink
from app.domain.oracle import FixtureLinkFile
from app.ingestion.errors import IngestionError
from app.ingestion.repository import GitRepository
from app.version import SCHEMA_VERSION

ACCEPTED_LINKS_PATH = "evidence/accepted-links.json"
PROPOSED_LINKS_PATH = "evidence/proposed-links.json"


def load_links(
    repository: GitRepository, commit: str, *, artifacts: dict[str, Artifact]
) -> tuple[list[TraceLink], list[TraceLink]]:
    """Accepted and proposed links at ``commit``, sorted by id.

    A missing file means the repository declares no links of that state. Present files are
    validated for contract version, declared state, duplicate ids, endpoints, and direction.
    """
    paths = set(repository.list_paths(commit))
    accepted = _read(repository, commit, paths, ACCEPTED_LINKS_PATH, ReviewState.ACCEPTED)
    proposed = _read(repository, commit, paths, PROPOSED_LINKS_PATH, ReviewState.PROPOSED)

    declared_at: dict[str, str] = {}
    for where, links in ((ACCEPTED_LINKS_PATH, accepted), (PROPOSED_LINKS_PATH, proposed)):
        for link in links:
            previous = declared_at.get(link.link_id)
            if previous is not None:
                raise IngestionError(
                    f"{commit}:{where}: duplicate link id {link.link_id!r}; "
                    f"already declared in {previous}"
                )
            declared_at[link.link_id] = where
            _validate_link(link, artifacts, where=f"{commit}:{where}")

    return (
        sorted(accepted, key=lambda link: link.link_id),
        sorted(proposed, key=lambda link: link.link_id),
    )


def _read(
    repository: GitRepository,
    commit: str,
    paths: set[str],
    path: str,
    expected_state: ReviewState,
) -> list[TraceLink]:
    if path not in paths:
        return []
    where = f"{commit}:{path}"
    raw = repository.read_blob(commit, path)
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise IngestionError(f"{where}: link file is not valid UTF-8 JSON: {exc}") from exc
    try:
        parsed = FixtureLinkFile.model_validate(payload)
    except ValidationError as exc:
        raise IngestionError(
            f"{where}: link file does not satisfy FixtureLinkFile:\n{exc}"
        ) from exc

    if parsed.schema_version != SCHEMA_VERSION:
        raise IngestionError(
            f"{where}: declares schema_version {parsed.schema_version!r}; this build implements "
            f"{SCHEMA_VERSION!r}"
        )
    if parsed.review_state != expected_state:
        affected = ", ".join(sorted(link.link_id for link in parsed.links)) or "none"
        raise IngestionError(
            f"{where}: declares review_state {parsed.review_state.value!r} but should be "
            f"{expected_state.value!r}; affected links: {affected}"
        )
    return list(parsed.links)


def _validate_link(link: TraceLink, artifacts: dict[str, Artifact], *, where: str) -> None:
    source = artifacts.get(link.source_id)
    target = artifacts.get(link.target_id)
    if source is None:
        raise IngestionError(
            f"{where}: link {link.link_id} references unknown source artifact {link.source_id!r}"
        )
    if target is None:
        raise IngestionError(
            f"{where}: link {link.link_id} references unknown target artifact {link.target_id!r}"
        )
    expected_source, expected_target = RELATION_DIRECTION[link.relation_type]
    if (source.artifact_type, target.artifact_type) != (expected_source, expected_target):
        raise IngestionError(
            f"{where}: link {link.link_id} relation {link.relation_type.value!r} must connect "
            f"{expected_source.value} -> {expected_target.value}, got "
            f"{source.artifact_type.value} -> {target.artifact_type.value}"
        )
```

`backend/tests/test_ingestion_links.py`:
```python
"""DT-03 acceptance: declared links are typed, validated, and never merged by state."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

from app.domain.oracle import FixtureSnapshot
from app.ingestion import GitRepository, IngestionError, ingest_revision
from app.version import SCHEMA_VERSION


def requirement(requirement_id: str) -> str:
    return f"---\nid: {requirement_id}\ntitle: A requirement\nstatus: active\n---\n\n# Body\n"


def feature(scenario_id: str) -> str:
    return f"Feature: Demo\n\n  @{scenario_id}\n  Scenario: A behaviour\n    Given a thing\n"


def source(artifact_id: str) -> str:
    return f"# cta:artifact {artifact_id}\nVALUE = 1\n"


def link(
    link_id: str,
    source_id: str,
    target_id: str,
    relation_type: str,
    *,
    review_state: str = "accepted",
) -> dict[str, object]:
    return {
        "link_id": link_id,
        "source_id": source_id,
        "target_id": target_id,
        "relation_type": relation_type,
        "review_state": review_state,
        "provenance": {
            "method": "manual-review",
            "reviewer_id": "rv-test",
            "decided_at": "2026-09-28T10:00:00+00:00",
        },
        "created_at": "2026-09-27T15:30:00+00:00",
        "updated_at": "2026-09-28T10:00:00+00:00",
    }


def link_file(review_state: str, links: list[dict[str, object]]) -> str:
    return json.dumps(
        {
            "schema_version": SCHEMA_VERSION,
            "repository": "demo",
            "review_state": review_state,
            "links": links,
        }
    )


def make_repo(tmp_path: Path, files: dict[str, str]) -> GitRepository:
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q")
    for relative, text in files.items():
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    _git(root, "add", "-A")
    _git(
        root,
        "-c",
        "user.name=Link Test",
        "-c",
        "user.email=test@example.invalid",
        "-c",
        "commit.gpgsign=false",
        "commit",
        "-q",
        "-m",
        "fixture",
    )
    return GitRepository(root=root)


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)


def base_files() -> dict[str, str]:
    return {
        "requirements/REQ-900.md": requirement("REQ-900"),
        "features/demo.feature": feature("SCN-900"),
        "src/accounts.py": source("CODE-900"),
        "tests/test_demo.py": source("TEST-900"),
    }


def test_ingested_links_match_the_committed_snapshot(
    built_fixture, snapshot: FixtureSnapshot
) -> None:
    repository = GitRepository(root=built_fixture.repo)
    for entry in snapshot.baselines:
        revision = ingest_revision(repository, entry.commit, repository_name="banking-demo")
        assert revision.accepted_links == entry.accepted_links, entry.baseline
        assert revision.proposed_links == entry.proposed_links, entry.baseline


def test_proposals_are_ingested_separately(built_fixture) -> None:
    revision = ingest_revision(
        GitRepository(root=built_fixture.repo),
        "baseline-a",
        repository_name="banking-demo",
    )
    assert [link.link_id for link in revision.accepted_links if link.source_id == "REQ-002"] == []
    proposed = [link.link_id for link in revision.proposed_links]
    assert proposed == ["LNK-007"]
    assert revision.proposed_links[0].review_state.value == "proposed"


def test_wrong_relation_direction_is_rejected(tmp_path: Path) -> None:
    files = base_files()
    files["evidence/accepted-links.json"] = link_file(
        "accepted", [link("LNK-900", "CODE-900", "SCN-900", "verified_by")]
    )
    repository = make_repo(tmp_path, files)
    with pytest.raises(IngestionError, match="must connect requirement -> scenario"):
        ingest_revision(repository, repository.resolve(), repository_name="demo")


def test_link_to_unknown_artifact_is_rejected(tmp_path: Path) -> None:
    files = base_files()
    files["evidence/accepted-links.json"] = link_file(
        "accepted", [link("LNK-901", "REQ-900", "SCN-999", "verified_by")]
    )
    repository = make_repo(tmp_path, files)
    with pytest.raises(IngestionError, match="SCN-999"):
        ingest_revision(repository, repository.resolve(), repository_name="demo")


def test_file_with_the_wrong_review_state_is_rejected(tmp_path: Path) -> None:
    files = base_files()
    files["evidence/accepted-links.json"] = link_file(
        "proposed", [link("LNK-902", "REQ-900", "SCN-900", "verified_by", review_state="proposed")]
    )
    repository = make_repo(tmp_path, files)
    with pytest.raises(IngestionError) as failure:
        ingest_revision(repository, repository.resolve(), repository_name="demo")
    message = str(failure.value)
    assert "accepted-links.json" in message
    assert "LNK-902" in message


def test_a_proposed_member_in_an_accepted_file_is_rejected_naming_the_link(
    tmp_path: Path,
) -> None:
    files = base_files()
    files["evidence/accepted-links.json"] = link_file(
        "accepted", [link("LNK-908", "REQ-900", "SCN-900", "verified_by", review_state="proposed")]
    )
    repository = make_repo(tmp_path, files)
    with pytest.raises(IngestionError) as failure:
        ingest_revision(repository, repository.resolve(), repository_name="demo")
    assert "LNK-908" in str(failure.value)


def test_repeated_ingestion_returns_identical_links(tmp_path: Path) -> None:
    files = base_files()
    files["evidence/accepted-links.json"] = link_file(
        "accepted", [link("LNK-903", "REQ-900", "SCN-900", "verified_by")]
    )
    files["evidence/proposed-links.json"] = link_file(
        "proposed",
        [link("LNK-904", "SCN-900", "CODE-900", "implemented_by", review_state="proposed")],
    )
    repository = make_repo(tmp_path, files)
    first = ingest_revision(repository, repository.resolve(), repository_name="demo")
    second = ingest_revision(repository, repository.resolve(), repository_name="demo")
    assert first.accepted_links == second.accepted_links
    assert first.proposed_links == second.proposed_links
    assert first.accepted_links[0].provenance["decided_at"] == "2026-09-28T10:00:00+00:00"


def test_duplicate_link_ids_are_rejected(tmp_path: Path) -> None:
    files = base_files()
    files["evidence/accepted-links.json"] = link_file(
        "accepted",
        [
            link("LNK-905", "REQ-900", "SCN-900", "verified_by"),
            link("LNK-905", "SCN-900", "CODE-900", "implemented_by"),
        ],
    )
    repository = make_repo(tmp_path, files)
    with pytest.raises(IngestionError, match="link ids must be unique"):
        ingest_revision(repository, repository.resolve(), repository_name="demo")


def test_duplicate_link_ids_across_files_are_rejected(tmp_path: Path) -> None:
    files = base_files()
    files["evidence/accepted-links.json"] = link_file(
        "accepted", [link("LNK-907", "REQ-900", "SCN-900", "verified_by")]
    )
    files["evidence/proposed-links.json"] = link_file(
        "proposed",
        [link("LNK-907", "SCN-900", "CODE-900", "implemented_by", review_state="proposed")],
    )
    repository = make_repo(tmp_path, files)
    with pytest.raises(IngestionError, match="duplicate link id 'LNK-907'"):
        ingest_revision(repository, repository.resolve(), repository_name="demo")


def test_unsupported_link_schema_version_is_rejected(tmp_path: Path) -> None:
    files = base_files()
    payload = json.loads(
        link_file("accepted", [link("LNK-906", "REQ-900", "SCN-900", "verified_by")])
    )
    payload["schema_version"] = "999.0.0"
    files["evidence/accepted-links.json"] = json.dumps(payload)
    repository = make_repo(tmp_path, files)
    with pytest.raises(IngestionError, match="999.0.0"):
        ingest_revision(repository, repository.resolve(), repository_name="demo")


def test_absent_link_files_are_empty(tmp_path: Path) -> None:
    repository = make_repo(tmp_path, base_files())
    revision = ingest_revision(repository, repository.resolve(), repository_name="demo")
    assert revision.accepted_links == []
    assert revision.proposed_links == []
```

`docs/stories/DT-03.md`:
```markdown
# DT-03 — Typed, provenance-aware traceability links with review state

**Milestone:** M1 — AI-free vertical slice · **Owner:** B · **Implementer:** OMP · **Status:**
refined; implementation in progress.

| Record | Value |
| --- | --- |
| Roadmap / feature | F-03 Links · roadmap §6 DT-03 |
| GitHub story | [#22](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/22) — verified OPEN 2026-11-13T02:50:26Z (`gh issue view`), milestone "M1 — AI-free vertical slice" |
| Parent feature issue | [#10](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/10) |
| Canonical criteria | [DT-03.feature](DT-03.feature), sha256 `d6e390d908616388cbc69ae2dbabd5371ef6a15115a83b447f7696dbf6c83200` |
| Dependencies | DT-02 (#21) merged at `590e776b67d9e340f9e68df04472222ee4fd0720`; DT-01 scanner |
| Upstream obligation | Roadmap §4 `TraceLink`; ADR 0004; project-definition REQ-102/105 (draft) |

## User outcome

An engineer can read the declared relationships for a revision with their provenance and review
state, knowing that a proposal never appears as an accepted relationship and that a link cannot
silently contradict the relation vocabulary.

## Scope

* Read `evidence/accepted-links.json` and `evidence/proposed-links.json` from the pinned revision.
* Validate the file's `schema_version`, declared review state, link schema, unique ids (within and
  across the two files), endpoint existence, and relation direction.
* Return accepted and proposed links as separate collections; repeated ingestion returns identical
  facts.
* Add `ingest_revision` returning artifacts + links (evidence arrives with DT-04).

## Non-goals

Writing or mutating links; review decisions (AS-06, M3); evidence/findings; discovery; thread/API
assembly (DT-04). A missing link file means "no declared links" (empty collections), not a malformed
declaration.

## Preservation boundaries

Fixture link files, artifacts, generated responses, and contracts are unchanged. DT-01/DT-02
behavior is preserved. No schema change: the domain models/enums already exist; this story adds
validation and ingestion. A duplicate-id validator on `FixtureLinkFile` strengthens an existing
invariant without changing the wire shape.

## Design impact

* `app/domain/enums.py`: `RELATION_DIRECTION` table (relation → allowed source/target artifact
  types), making the documented direction executable.
* `app/domain/oracle.py`: `FixtureLinkFile` rejects duplicate link ids.
* `app/ingestion/links.py`: parse/validate link files, reject wrong file state, unknown endpoints,
  duplicate ids across files, direction mismatches, and unsupported schema versions.
* `app/ingestion/revision.py`: `IngestedRevision` + `ingest_revision`.
* `app/ingestion/__init__.py`: exports.
* Docs: `docs/domain-contracts.md` (direction validation, duplicate ids), `docs/architecture.md`.

Assumptions:

1. Each file declares exactly one review state, matching its name; the model enforces membership.
2. Endpoints must exist as artifacts at the same revision; a dangling link is an error.
3. Decision history is the declared file content at the revision; ingestion is read-only, so
   repeated reads are identical. Append-only review decisions are AS-06's scope.
4. Link ids are unique across both files at a revision.

## Refinement disposition

Derived from the owner-authored issue intake and roadmap §6; failure scenarios were added without
weakening the intake. No separate human refinement sign-off is recorded, and the draft project
definition is not treated as an approved requirements baseline.

## Verification mapping

| Scenario | Observable check | Pytest selector |
| --- | --- | --- |
| SCN-601 accepted provenance | All accepted links at both baselines equal the committed snapshot, including reviewer/decided_at | `backend/tests/test_ingestion_links.py::test_ingested_links_match_the_committed_snapshot` |
| SCN-602 proposal separation | REQ-002 has no accepted links; LNK-007 is proposed only | `backend/tests/test_ingestion_links.py::test_proposals_are_ingested_separately` |
| SCN-603 wrong direction | Temp repo with CODE-900→SCN-900 `verified_by` raises naming the expected direction | `backend/tests/test_ingestion_links.py::test_wrong_relation_direction_is_rejected` |
| SCN-604 unknown endpoint | Link to `SCN-999` raises naming it | `backend/tests/test_ingestion_links.py::test_link_to_unknown_artifact_is_rejected` |
| SCN-605 wrong file state | `accepted-links.json` declaring `proposed` raises naming the file and `LNK-902`; a proposed member inside a file declaring `accepted` raises naming that link | `backend/tests/test_ingestion_links.py::test_file_with_the_wrong_review_state_is_rejected`, `::test_a_proposed_member_in_an_accepted_file_is_rejected_naming_the_link` |
| SCN-606 repeated ingestion | Two ingests return identical link facts | `backend/tests/test_ingestion_links.py::test_repeated_ingestion_returns_identical_links` |
| DoD duplicate ids | Duplicate ids within one file and across the accepted/proposed files raise | `backend/tests/test_ingestion_links.py::test_duplicate_link_ids_are_rejected`, `::test_duplicate_link_ids_across_files_are_rejected` |
| DoD schema version | A link file with an unsupported schema version raises | `backend/tests/test_ingestion_links.py::test_unsupported_link_schema_version_is_rejected` |
| DoD missing files | A revision with no link files yields empty collections | `backend/tests/test_ingestion_links.py::test_absent_link_files_are_empty` |

A mapping row is not an execution result; the run record carries the actual invocation and result.

## Verification plan

Focused link tests, full offline suite, fixture drift, ruff, and the network-denied suite.
```

`docs/reports/omp-dt-03-links/IMPLEMENTATION.md`:
```markdown
# DT-03 implementation record — typed, provenance-aware links with review state

| Field | Value |
| --- | --- |
| Story | DT-03 — [#22](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/22), verified OPEN 2026-11-13T02:50:26Z (`gh issue view`, milestone "M1 — AI-free vertical slice") |
| Canonical criteria | [DT-03.feature](../../stories/DT-03.feature), sha256 `d6e390d908616388cbc69ae2dbabd5371ef6a15115a83b447f7696dbf6c83200` |
| Brief / verification map | [DT-03.md](../../stories/DT-03.md) |
| Branch / base | `feat/22-dt-03-links` from `590e776b67d9e340f9e68df04472222ee4fd0720` (DT-02 merge) |
| Contract version | `SCHEMA_VERSION = 0.1.0`, `PACKAGE_VERSION = 0.1.0` (validation only; no shape change) |
| Submission | **2 of 7** (round 1 = REQUEST_CHANGES; DT03-R1/R2/R3 repaired) |
| Snapshot captured | 2026-11-13T03:01Z |

## What changed

| Path | sha256 | Purpose |
| --- | --- | --- |
| `backend/app/domain/enums.py` | `a2464c7f2edba85f8af1dac6af24efc4a05693fef6188ab6948fb2be4cb554c2` | Adds `RELATION_DIRECTION`, the executable direction contract |
| `backend/app/domain/oracle.py` | `679eea69414764999a4770725c01000521bbd508135840359ae5949e297e7889` | `FixtureLinkFile` rejects duplicate ids within a file |
| `backend/app/ingestion/__init__.py` | `3282cea94ca923a47571127b7b0a69c7ee89313ef7014458f48f8dd55ed57397` | Exports `IngestedRevision` / `ingest_revision` |
| `backend/app/ingestion/links.py` | `3c284b7e421182507ff0b7443b3b1ff036553ec8dc8b0ad1fdfaa497704f4aed` | Reads and validates accepted/proposed link files; state errors name affected links |
| `backend/app/ingestion/revision.py` | `0e954a7de6b29700eeb53da38e4ade983428193386a7ccb99fc149b75f0e8e06` | Assembles one revision's artifacts + links |
| `backend/tests/test_ingestion_links.py` | `f4ef0b02e4d51b1f1712b527fb69aed92e00cf75a44279a27e878e8c3289acc9` | Eleven link-ingestion tests (within/across-file duplicates, state diagnostics) |
| `docs/stories/DT-03.feature` | `d6e390d908616388cbc69ae2dbabd5371ef6a15115a83b447f7696dbf6c83200` | Canonical criteria (SCN-601…606) |
| `docs/stories/DT-03.md` | `aa2560a7838af3ae1134ba934d61d8758ce9936c90ddab89a60bf56ea4d4290c` | Brief, assumptions, verification map |
| `docs/domain-contracts.md` | `824a17b8ba243530036b61dbe12dda59caad65d5fd8102056b8c0669b66ab666` | Documents link validation and duplicate ids |
| `docs/architecture.md` | `f2157cad7d2b7b3518f950cc46787bad7c098d977fbc3bf66753b59d39a4d303` | Ingestion status includes links |
| `docs/STATUS.md` | `45a2af82317439f53a169ac595547acc55640c2220158eb151d3ba2bfde9b8c8` | DT-02 landed; DT-03 active |

Generated fixtures, oracle labels, generated responses, and the API are untouched.

## Review round 1 — REQUEST_CHANGES (submission 1 of 7)

Reviewer: Codex `gpt-6.1-sol`, `xhigh`, read-only; session `01a1d2d4-9cc6-7dd2-b772-761f67718f7f`;
2026-11-13T02:55:11Z → 02:58:57Z (226.49 s), exit 0; 14/14 task hashes matched.
Verdict: `docs/reviews/DT-03-review.md`.

| Finding | Severity | Repair | Recheck |
| --- | --- | --- | --- |
| DT03-R1 the file-level review-state error omitted the affected link ids (SCN-605) | medium, blocking | The error names the file, the expected/declared state, and the sorted affected link ids; the test asserts the filename and `LNK-902`, and a proposed member inside an accepted file is separately rejected naming that link | `test_file_with_the_wrong_review_state_is_rejected`, `test_a_proposed_member_in_an_accepted_file_is_rejected_naming_the_link` |
| DT03-R2 the packet's `scan.py` dependency pointer was stale (DT-01 hash instead of the DT-02 file) | medium, blocking evidence | Corrected to `2a602ee3668bd1560e42aa8870c6a1875b3977a082d449109892852c73e0a613` in submission 2; no implementation change | manifest check in the resubmission |
| DT03-R3 the duplicate-id mapping claimed cross-file coverage the test did not exercise | low, nonblocking | Added a cross-file duplicate test and corrected the brief/record | `test_duplicate_link_ids_across_files_are_rejected` |

The packet inconsistency was an evidence-identity defect, not a source edit; the resubmission's
manifest is the corrected snapshot.

## Acceptance results

| Criterion | Check | Result |
| --- | --- | --- |
| SCN-601 accepted provenance | `tests/test_ingestion_links.py::test_ingested_links_match_the_committed_snapshot` (all accepted links, both baselines) | PASS |
| SCN-602 proposal separation | `::test_proposals_are_ingested_separately` | PASS |
| SCN-603 wrong direction | `::test_wrong_relation_direction_is_rejected` (names `requirement -> scenario`) | PASS |
| SCN-604 unknown endpoint | `::test_link_to_unknown_artifact_is_rejected` (names `SCN-999`) | PASS |
| SCN-605 wrong file state | `::test_file_with_the_wrong_review_state_is_rejected` (file + LNK-902), `::test_a_proposed_member_in_an_accepted_file_is_rejected_naming_the_link` | PASS |
| SCN-606 repeated ingestion | `::test_repeated_ingestion_returns_identical_links` | PASS |
| DoD duplicate ids | `::test_duplicate_link_ids_are_rejected` (within a file), `::test_duplicate_link_ids_across_files_are_rejected` (across accepted/proposed) | PASS |
| DoD schema version | `::test_unsupported_link_schema_version_is_rejected` | PASS |
| DoD absent files | `::test_absent_link_files_are_empty` | PASS |

Axis coverage: success (601), separation (602), failure (603/604/605/schema/duplicates), boundary
(absent files), stability (606).

## Commands and outcomes (as captured)

```text
captured_start=2026-11-13T03:00:50Z
pytest backend/tests -q                          exit 0  219 passed, 1 warning in 5.88s
fixturectl.py verify                             exit 0  reproducible and committed files current
ruff check .                                     exit 0  All checks passed
ruff format --check .                            exit 0  all files formatted
git diff --check                                 exit 0
captured_end=2026-11-13T03:00:58Z

network denial at 2026-11-13T03:00:58Z: `unshare -rn backend/.venv/bin/python -m pytest
backend/tests -q` → exit 0, 219 passed.
```

Raw logs are in the external run directory `…/m1-roadmap-20261112/dt-03/`.

## Self-review

* **Proposal/acceptance separation:** two files, two collections; a wrong file state or a duplicate
  id is rejected; no code path merges or promotes proposals.
* **Direction and endpoints:** `RELATION_DIRECTION` is the single executable table; unknown
  endpoints and type mismatches fail ingestion instead of producing a plausibly typed edge.
* **Revision-aware:** links are read from the resolved commit; repeated ingestion is identical.
* **No mutation:** ingestion is read-only; append-only review decisions remain AS-06.
* **No contract change:** models/enums already existed; this adds validation. `fixturectl verify`
  confirms no generated bytes changed.
* **Offline:** local Git and JSON only; network-denied suite passes.

Known limits: review writes/history are AS-06 (M3); evidence ingestion and thread assembly are
DT-04; candidate proposals from discovery are not links until recorded (ADR 0004).

## Independent review

**Submission 2 pending.** The verdict will be recorded in `docs/reviews/DT-03-review-2.md`.
Implementation acceptance is not claimed before that verdict.
```

### Unchanged since submission 1 (hash-pinned pointers, corrected)

```text
eaaec286ca5dddff28914b6e3a431338a4082b17edd703548ec9fda811d6c005  backend/app/ingestion/repository.py
2a602ee3668bd1560e42aa8870c6a1875b3977a082d449109892852c73e0a613  backend/app/ingestion/scan.py
b33cd36ad1a42f9f18720cf11f5d42aea424646ba8ff5b286587995ab2799a1d  backend/app/ingestion/errors.py
3282cea94ca923a47571127b7b0a69c7ee89313ef7014458f48f8dd55ed57397  backend/app/ingestion/__init__.py
a2464c7f2edba85f8af1dac6af24efc4a05693fef6188ab6948fb2be4cb554c2  backend/app/domain/enums.py
679eea69414764999a4770725c01000521bbd508135840359ae5949e297e7889  backend/app/domain/oracle.py
d6e390d908616388cbc69ae2dbabd5371ef6a15115a83b447f7696dbf6c83200  docs/stories/DT-03.feature
824a17b8ba243530036b61dbe12dda59caad65d5fd8102056b8c0669b66ab666  docs/domain-contracts.md
f2157cad7d2b7b3518f950cc46787bad7c098d977fbc3bf66753b59d39a4d303  docs/architecture.md
45a2af82317439f53a169ac595547acc55640c2220158eb151d3ba2bfde9b8c8  docs/STATUS.md
```

## 4. Changes since submission 1

| Finding | Severity | Repair | Recheck |
| --- | --- | --- | --- |
| DT03-R1 file-level state error omitted affected link ids | medium, blocking | The diagnostic names the file, declared/expected state, and sorted affected ids. A proposed member inside an accepted file is rejected separately, naming that link. | `test_file_with_the_wrong_review_state_is_rejected` (asserts file + LNK-902), `test_a_proposed_member_in_an_accepted_file_is_rejected_naming_the_link` |
| DT03-R2 packet `scan.py` pointer was stale | medium, blocking evidence | Corrected to the DT-02 hash above; no source change. | manifest check in this submission |
| DT03-R3 duplicate-id mapping claimed untested cross-file coverage | low, nonblocking | Added a cross-file duplicate test and corrected the brief/record. | `test_duplicate_link_ids_across_files_are_rejected` |

## 5. Implementation context

* `load_links` lists the tree once, reads each present link file, validates contract version and
  declared state, then checks ids (within and across files), endpoints, and direction.
* `ingest_revision` resolves once, scans artifacts, and loads links with the artifact index.
* `RELATION_DIRECTION` in `app/domain/enums.py` is the executable direction contract.
* Targeted reads: `backend/app/domain/models.py`, `docs/domain-contracts.md`, ADR 0004,
  `backend/tests/conftest.py`.

## 6. Evidence

| Criterion | Check | Result |
| --- | --- | --- |
| SCN-601 | `tests/test_ingestion_links.py::test_ingested_links_match_the_committed_snapshot` | PASS |
| SCN-602 | `::test_proposals_are_ingested_separately` | PASS |
| SCN-603 | `::test_wrong_relation_direction_is_rejected` | PASS |
| SCN-604 | `::test_link_to_unknown_artifact_is_rejected` | PASS |
| SCN-605 | `::test_file_with_the_wrong_review_state_is_rejected`, `::test_a_proposed_member_in_an_accepted_file_is_rejected_naming_the_link` | PASS |
| SCN-606 | `::test_repeated_ingestion_returns_identical_links` | PASS |
| Duplicate ids | `::test_duplicate_link_ids_are_rejected`, `::test_duplicate_link_ids_across_files_are_rejected` | PASS |
| Schema version | `::test_unsupported_link_schema_version_is_rejected` | PASS |
| Absent files | `::test_absent_link_files_are_empty` | PASS |

Actual invocations and exits, captured 2026-11-13T03:00:50Z–03:00:58Z:

```text
uv run --project backend pytest backend/tests -q exit 0  219 passed, 1 warning in 5.88s
uv run --project backend python tools/fixturectl.py verify  exit 0  reproducible and current
uv run --project backend ruff check .            exit 0  All checks passed
uv run --project backend ruff format --check .   exit 0  all files formatted
git diff --check                                 exit 0
unshare -rn backend/.venv/bin/python -m pytest backend/tests -q  exit 0  219 passed
```

NOT RUN: API/HTTP, frontend, write/review mutations (AS-06). Full logs are in the external run
directory; `IMPLEMENTATION.md` records the same exits.

## 7. File-integrity requirement

The manifest in section 3 is the reviewed snapshot. If any manifest hash changed, the snapshot is
not the one reviewed. Do not edit files, install dependencies, regenerate fixtures, or commit.

## Reviewer instructions (mandatory)

You are the independent CTA implementation reviewer using GPT-6.1 Sol xhigh. Decide whether this exact snapshot satisfies the supplied story, every applicable Gherkin criterion, and repository invariants. Treat OMP's summaries and test results as claims to check against the supplied artifacts and targeted source inspection. Check proposal/accepted/evidence separation, real port compatibility, revision/content-hash semantics, honest errors/501s, independent oracle expectations, offline defaults, and generated-file discipline where relevant. Do not demand implementation of a later milestone. Do not edit files, implement repairs, regenerate fixtures, commit, or delegate. Ask OMP for missing runtime evidence; distinguish observed defects from hypotheses and unavailable checks. Return an AC-by-AC PASS, FAIL, or NOT VERIFIED assessment and actionable findings with stable IDs, severity, blocking status, AC/invariant, path/line, expected/actual behavior, and smallest correction/recheck. Keep optional suggestions and unrelated pre-existing defects separate. Return exactly one verdict: APPROVE, REQUEST_CHANGES, or NEEDS_INPUT. APPROVE requires every applicable criterion/check to be satisfied, no unresolved blocker, and the exact snapshot identified. In later rounds verify prior dispositions and regressions while retaining the complete acceptance assessment. A passing process, passing tests, or exhausted review limit is not approval. Agent review cannot attest human labeling or human link decisions.
