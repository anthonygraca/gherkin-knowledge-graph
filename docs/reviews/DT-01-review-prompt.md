# Independent implementation review — DT-01, submission 1 of 7

## 1. Story and authorization

**Task:** DT-01 — Requirements and Gherkin scenarios parsed into stable artifacts.
**Roadmap/feature:** F-02 Ingestion, roadmap §6 DT-01; milestone **M1 — AI-free vertical slice**.
**GitHub story:** anthonygraca/gherkin-knowledge-graph issue **#20**, verified OPEN at
2026-11-13T00:52:26Z with `gh issue view 20 --json number,title,state,milestone,url`; milestone
"M1 — AI-free vertical slice"; URL https://github.com/anthonygraca/gherkin-knowledge-graph/issues/20.
**Owner:** B. Implementer/integrator: OMP. Milestone ceiling: M1.
**Repository:** `<task_repo>` (read-only sandbox; the coordinator runs from the repository root).
**Base revision:** `e18cdcfafe058e2f1d99c3c0b4bc2e155e9b16c9` (`main`).
**Branch:** `feat/20-dt-01-ingestion`.
**User-authorized scope:** roadmap-mode run through the M1 gate; GitHub authority through merge
after required CI and independent/owner reviews. You are the independent implementation reviewer,
not the owner of product intent.

### User outcome

A systems engineer can point ingestion at a repository revision and receive stable artifact
identities for requirements and Gherkin scenarios, each pinned to the revision and content hash it
was read at, so later rules and change detection can rely on those identities.

### Scope of this submission

Requirement front matter parsing, `@SCN-nnn` scenario parsing, revision-pinned Git reads, artifact
content hashing, and loud rejection of malformed declarations. Source/test annotations, links,
evidence, threads, assurance rules, and API routes are **not** in this story.

### Non-goals (do not demand them here)

* DT-02 source/test artifacts; DT-03 link ingestion; DT-04 thread assembly and store cutover;
  AS-01 rules; AS-04 UI.
* A Gherkin runner or step bindings.
* General repository layouts, non-Markdown requirements, sub-file granularity.
* A database or durable store (ADR 0006 keeps the storage decision open).

### Proposed commit reference

`feat(ingestion): [issue #20] parse requirements and Gherkin into stable artifacts` with body
`Refs #20`. No `Closes` in the commit; closure is a PR/merge decision after this review.

## 2. Acceptance criteria (canonical snapshot)

File: `docs/stories/DT-01.feature`, sha256
`92440cffffee2ebcb344cba4842b242293891e72cbad8e1d42ebf01a21c000da`.

```gherkin
# Canonical acceptance specification for DT-01 (#20), M1.
# Source criteria: the GitHub story intake at
# https://github.com/anthonygraca/gherkin-knowledge-graph/issues/20 (verified 2026-11-13T00:52:26Z)
# and roadmap §6 F-02. Failure and boundary scenarios were added during refinement; the two
# intake scenarios keep their original wording.
# Verified by the pytest selectors mapped in DT-01.md. These scenarios are not currently bound
# to or executed by a Gherkin runner.
@DT-01 @issue-20 @M1
Feature: DT-01: Requirements and Gherkin scenarios parsed into stable artifacts
  A requirement document declares its identity in YAML front matter. A Gherkin scenario
  declares its identity with an @SCN-nnn tag. Ingestion reads the repository at a pinned
  revision, never the working tree, and rejects malformed declarations instead of skipping
  them silently.

  @SCN-501
  Scenario: Requirement document parsed into an artifact
    Given the fixture repository checked out at "baseline-a"
    When the requirements are ingested
    Then an artifact "REQ-001" of type "requirement" exists with title "Instant withdrawal availability"
    And its locator is "requirements/REQ-001.md"
    And its content_hash is the sha256 of the file bytes at that revision
    And its metadata records status "active"

  @SCN-502
  Scenario: Scenario identity comes from the Gherkin tag
    Given "features/withdrawals.feature" contains the tag "@SCN-001"
    When the scenarios are ingested
    Then an artifact "SCN-001" of type "scenario" exists with locator "features/withdrawals.feature#SCN-001"
    And its title is the scenario name from the feature file
    And unannotated files produce no artifacts

  @SCN-503
  Scenario: A requirement without front matter is rejected
    Given a repository revision where "requirements/BROKEN.md" has no front matter block
    When the revision is ingested
    Then ingestion fails with an error naming "requirements/BROKEN.md"
    And no partial artifact set is returned

  @SCN-504
  Scenario: An untagged scenario creates no artifact
    Given a feature file containing a scenario without an "@SCN-nnn" tag
    When the scenarios are ingested
    Then no artifact is created for that scenario

  @SCN-505
  Scenario: A dangling scenario tag is rejected
    Given a feature file where "@SCN-999" is not followed by a "Scenario:" line
    When the scenarios are ingested
    Then ingestion fails with an error naming "@SCN-999"

  @SCN-506
  Scenario: Duplicate artifact identities are rejected
    Given two requirement documents declare the same id "REQ-900"
    When the revision is ingested
    Then ingestion fails with an error naming "REQ-900"
```

Refinement disposition: criteria derive from the owner-authored issue intake and roadmap §6;
failure and boundary scenarios were added without weakening intake wording. No separate human
refinement sign-off is recorded, and the draft project definition is not treated as an approved
requirements baseline. Do not treat this freeze as product-owner approval.

Repository constraints that apply (AGENTS.md): offline by default (no network/GPU/model/DB/Docker
in tests or default paths); proposals ≠ accepted links ≠ verification; anything claiming
verification is revision-aware with content hashes; hand-labeled oracle data is independent of the
code under test; contract-only endpoints stay 501; Pydantic models are the API/domain boundary.

## 3. Snapshot and complete diff

Snapshot captured 2026-11-13T00:58:20Z. Manifest (sha256 of every task file):

```text
c87a149c478ddbcd7322ffbdda723362bda18729da264048be5c3eaa9e58cdbf  backend/app/ingestion/__init__.py
b33cd36ad1a42f9f18720cf11f5d42aea424646ba8ff5b286587995ab2799a1d  backend/app/ingestion/errors.py
6d8455aa8a9b0a963c162e332e6938dc1d1a094b2276686cf4ce598ae214041b  backend/app/ingestion/parsers.py
eaaec286ca5dddff28914b6e3a431338a4082b17edd703548ec9fda811d6c005  backend/app/ingestion/repository.py
34977ced7b3044ef8f6826f0ed0a07b3883251ed164220249f456d9b8ea8a45e  backend/app/ingestion/scan.py
95b3762b1d20b3e6d58b18ef107f8626e2ee35e9132a8caf7e3a9848ce931b93  backend/tests/test_ingestion_parsers.py
eabf4dc27132b4489fbcfcf249e2d20a61159743ee934e19b08805870f2c8425  backend/tests/test_ingestion_artifacts.py
92440cffffee2ebcb344cba4842b242293891e72cbad8e1d42ebf01a21c000da  docs/stories/DT-01.feature
75fc1d5fcc2cb4df1c33dcb05297a6d506322a13df4fa76d8ce847870fab5507  docs/stories/DT-01.md
5926759c78412da49573bdb745fb1369db2e3e0786f774eb0556280c9ddbcbd9  docs/architecture.md
5d949036dfa341290b54ec4f0dac1c4e075a07d8ae567de0b3ff50684c2e9619  docs/STATUS.md
9fc43b0a1be4ddee54f4de093d03334d8136eb93512da756f4d94fa40a9e7e9f  docs/reports/omp-dt-01-ingestion/IMPLEMENTATION.md
b7f7206b8d706fe432def2fb1394cb03408817c88a608773c175bbf1d5b8479a  docs/reports/omp-dt-01-ingestion/PROMPT_LOG.md
80b157fbb539b377890bacb247fd31fd97ce2ad739aaf84d9415ff1f51ac25de  docs/reports/omp-dt-01-ingestion/METRICS.md
```

Schema/package versions at this snapshot: `SCHEMA_VERSION = 0.1.0`, `PACKAGE_VERSION = 0.1.0`.
No generated fixture, oracle, contract model, API response, or workflow file is modified.

### Tracked-file diff

```diff
diff --git a/docs/STATUS.md b/docs/STATUS.md
index 58c56ae..344b962 100644
--- a/docs/STATUS.md
+++ b/docs/STATUS.md
@@ -1,11 +1,11 @@
 # Status
 
 ```text
-Date:                2026-11-12
-Current branch:      main — at d4af73a (PR #42 merged 2026-11-12; #38 → efa824b, #41 → f34ae07
-                     after the owner's conforming merge-message rewrite, #42 → d4af73a with a
-                     conforming merge subject; hosted push run 43161043845 success)
-Milestone:           M0 — implementation complete; exit gate SATISFIED by re-review round 2
+Date:                2026-11-13
+Current branch:      main at e18cdcf (PR #43 merged); M1 work starts from that revision
+Milestone:           M0 — exit gate SATISFIED by re-review round 2 (historical record below)
+                     M1 — IN PROGRESS; gate NOT yet satisfied
+Active task:         DT-01 (#20) requirements and Gherkin parsed into stable artifacts
 Independent review:  docs/reviews/M0-review.md — first review: "M0 not verified"
                      docs/reviews/M0-rereview-1.md — re-review round 1 (GPT-6.1 Sol, xhigh):
                      NEEDS_INPUT; R1–R7 all repaired; AC-1.1…AC-1.8 and AC-2.1…AC-2.5 all PASS;
@@ -33,6 +33,28 @@ Environment:         Python ≥3.11, uv, git ≥2.28; no GPU, LLM, vector store,
                      during tests
 ```
 
+## Roadmap execution — M1 (active)
+
+Run started 2026-11-13T00:44Z from `e18cdcf` in roadmap mode with the milestone ceiling at M1.
+GitHub authority for this run: scoped issue updates, branch pushes, PR creation, and merges after
+required CI and independent/owner reviews. M0's gate is satisfied; **M1's gate is not yet
+satisfied**. Lifecycle note: the draft `project-definition.md` intent/obligations and the M0
+feature-extraction reviews remain owner dispositions; M1 stories derive from the roadmap and do
+not claim that draft as an approved baseline.
+
+| Story | GitHub | Owner | Canonical feature | State |
+| --- | --- | --- | --- | --- |
+| DT-01 requirements + scenarios parsed | [#20](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/20) | B | [DT-01.feature](stories/DT-01.feature) | refined; implementation in review |
+| DT-02 source/test artifacts | [#21](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/21) | B | not yet written | eligible after DT-01 |
+| DT-03 typed links + review state | [#22](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/22) | B | not yet written | eligible after DT-02 |
+| DT-04 requirement thread | [#23](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/23) | B | not yet written | eligible after DT-03 |
+| AS-01 missing-link finding | [#2](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/2) | C | not yet written | eligible after DT-04 |
+| AS-04 findings/coverage summary | [#26](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/26) | C | not yet written | eligible after AS-01 |
+
+Per-task reports live under `docs/reports/omp-<task-slug>/`; each carries the AC-to-check table,
+actual commands/exits, the snapshot identity, and the independent verdict. Issue closure is
+recorded separately from implementation, approval, and merge.
+
 ## SETUP-01 commit-reference enforcement — landed (2026-11-12)
 
 The previously uncommitted SETUP-01 follow-up slice (#8) was resumed, re-verified on base `f34ae07`
diff --git a/docs/architecture.md b/docs/architecture.md
index 79b2a00..b5522e8 100644
--- a/docs/architecture.md
+++ b/docs/architecture.md
@@ -29,7 +29,7 @@ Two rules explain most of the layout:
 
 ## Modules
 
-| Module | What it is | Status in M0 |
+| Module | What it is | Status |
 | --- | --- | --- |
 | `app/domain/enums.py` | Closed vocabularies: artifact types, relations, review states, finding types, rule ids, severities | Contract |
 | `app/domain/models.py` | `Artifact`, `TraceLink`, `VerificationEvidence`, `TraceCandidate`, `AssuranceFinding`, fingerprint function | Contract |
@@ -41,7 +41,7 @@ Two rules explain most of the layout:
 | `app/discovery/fake.py` | Fixture-backed candidate provider | Working implementation (deliberately fake) |
 | `app/assurance/sample_findings.py` | Replay of reviewed sample findings | Mock service (rule engine arrives in C-PR1) |
 | `app/api/` | Routes, dependencies, RFC 9457 problem documents | Working |
-| `app/ingestion/` | Parsers + persistence | Absent by design; created in B-PR1 |
+| `app/ingestion/` | Revision-pinned parsing: requirement/Gherkin artifacts (DT-01); source/test (DT-02), links (DT-03), store cutover (DT-04) | Requirements and scenarios implemented; the rest absent by design |
 | `frontend/` | React/TypeScript dashboard | Absent by design; created in C-PR1 |
 
 ## Request flows
@@ -65,14 +65,14 @@ writes the responses. `verify` does all of that into a temporary directory and d
 
 ## What is real and what is not
 
-| Claim | Reality in M0 |
+| Claim | Reality at this snapshot |
 | --- | --- |
 | Git history, tags, and revisions | Real. Four commits, fixed SHAs, verified reproducible. |
 | Artifact identity, content hashes, revisions | Real, computed from git blobs. |
 | Fixture tests passing/failing as labeled | Real: the suite runs the fixture's own tests at both tags. |
 | Findings | **Not computed.** Reviewed sample responses generated from the hand-labeled oracle. |
 | Retrieval quality | **Not measured.** Candidate scores are fixture labels, never model output. |
-| Ingestion from a real repository | Not implemented; `POST /api/ingestion/run` returns 501 naming B-PR1. |
+| Ingestion from a real repository | Requirements and Gherkin scenarios are parsed from the nested fixture repository at a pinned revision (DT-01). Source/test artifacts, links, and the API cutover land in DT-02…DT-04; `POST /api/ingestion/run` still returns 501 until DT-04. |
 | Link review and audit history | Not implemented; `POST /api/links/{id}/review` returns 501 naming AS-06. |
 
 This is why the `contract-only` endpoints return 501 instead of plausible-looking data: the
```

### New implementation files (complete)

`backend/app/ingestion/__init__.py`:
```python
"""Repository ingestion (roadmap §3): revision-pinned parsing into domain artifacts.

The package is intentionally small. DT-01 adds requirement and Gherkin parsing; DT-02 adds
source/test annotations; DT-03 adds link ingestion; DT-04 assembles threads from the result.
Nothing here writes accepted links, review states, or verification evidence on its own: links
and evidence are *read* from declared repository files.
"""

from app.ingestion.errors import IngestionError
from app.ingestion.repository import GitRepository
from app.ingestion.scan import scan_artifacts

__all__ = ["GitRepository", "IngestionError", "scan_artifacts"]
```

`backend/app/ingestion/errors.py`:
```python
"""Ingestion failures.

Malformed repository content is not a client-request error and must not be skipped silently.
Parsers raise :class:`IngestionError`; the caller decides how to present it (the fixture-backed
API maps it to a documented server-side problem document).
"""

from __future__ import annotations


class IngestionError(ValueError):
    """Repository content or Git access made ingestion impossible."""
```

`backend/app/ingestion/parsers.py`:
```python
"""Pure text parsers for artifact declarations.

Declaration conventions are defined in ``docs/domain-contracts.md``:

* requirement: YAML front matter with ``id:`` and ``title:`` in ``requirements/*.md``;
* scenario: an ``@SCN-nnn`` tag immediately preceding the Gherkin ``Scenario:`` line.

Parsers are pure functions over text so malformed-input behaviour is testable without Git, and
they never guess: an unrecognizable declaration raises :class:`IngestionError` rather than
producing a partial result.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from app.ingestion.errors import IngestionError

SCENARIO_TAG_RE = re.compile(r"(?<!\S)@(?P<id>SCN-\d{3})(?!\S)")
SCENARIO_LINE_RE = re.compile(r"^\s*Scenario:\s*(?P<title>\S.*?)\s*$")

FRONT_MATTER_OPEN = "---\n"
FRONT_MATTER_DELIMITER = "\n---\n"


@dataclass(frozen=True)
class ScenarioDeclaration:
    """One tagged scenario found in a feature file."""

    scenario_id: str
    title: str


def parse_front_matter(text: str, *, where: str) -> dict[str, str]:
    """Return the top-level ``key: value`` pairs of a leading front matter block.

    Values stay strings: the requirement schema is the only consumer and it declares the types
    it accepts. Duplicate keys and unusable lines are errors, not last-one-wins surprises.
    """
    if not text.startswith(FRONT_MATTER_OPEN):
        raise IngestionError(
            f"{where}: expected a '---' front matter block at the start of the file"
        )
    end = text.find(FRONT_MATTER_DELIMITER, len(FRONT_MATTER_OPEN))
    if end == -1:
        raise IngestionError(f"{where}: front matter block is not terminated by '---'")

    fields: dict[str, str] = {}
    for line in text[len(FRONT_MATTER_OPEN) : end].splitlines():
        if not line.strip():
            continue
        key, separator, value = line.partition(":")
        if not separator:
            raise IngestionError(f"{where}: unusable front matter line {line!r}")
        key = key.strip()
        if not key:
            raise IngestionError(f"{where}: empty front matter key in line {line!r}")
        if key in fields:
            raise IngestionError(f"{where}: duplicate front matter key {key!r}")
        fields[key] = value.strip()
    return fields


def parse_scenarios(text: str, *, where: str) -> list[ScenarioDeclaration]:
    """Return the scenarios declared with an ``@SCN-nnn`` tag, in file order.

    A scenario without the tag is not an artifact and is ignored by design. A tag that is not
    followed by a ``Scenario:`` line is a broken declaration and raises.
    """
    found: list[ScenarioDeclaration] = []
    pending: str | None = None
    for line in text.splitlines():
        if line.lstrip().startswith("@"):
            identities = SCENARIO_TAG_RE.findall(line)
            if len(identities) > 1:
                raise IngestionError(
                    f"{where}: a scenario line carries more than one identity tag: "
                    f"{', '.join(identities)}"
                )
            if identities:
                if pending is not None:
                    raise IngestionError(
                        f"{where}: tag @{pending} is not followed by a 'Scenario:' line"
                    )
                pending = identities[0]
                continue
        if pending is None:
            continue
        match = SCENARIO_LINE_RE.match(line)
        if match:
            found.append(ScenarioDeclaration(scenario_id=pending, title=match.group("title")))
            pending = None
    if pending is not None:
        raise IngestionError(f"{where}: tag @{pending} is not followed by a 'Scenario:' line")
    return found
```

`backend/app/ingestion/repository.py`:
```python
"""Read-only Git access for ingestion.

Uses the Git CLI — the project's documented prerequisite (roadmap §3, docs/setup.md) — and
reads committed objects, never the working tree. Only the operations ingestion needs are
exposed; there is no write path.

Paths and blob contents are treated as untrusted input: paths come from ``git ls-tree -z`` and
object expressions are terminated with ``--end-of-options`` so a repository cannot smuggle a
command-line option into a revision expression.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from app.ingestion.errors import IngestionError

GIT_READ_FLAGS = ("-c", "core.autocrlf=false")


@dataclass(frozen=True)
class GitRepository:
    """A repository read at explicit revisions."""

    root: Path

    def resolve(self, revision: str | None = None) -> str:
        """Resolve a revision expression (tag, SHA, branch) to a commit SHA.

        ``None`` selects the repository's current ``HEAD``. An unknown expression raises.
        """
        expression = revision or "HEAD"
        output = self._run("rev-parse", "--verify", "--end-of-options", f"{expression}^{{commit}}")
        return output.decode("utf-8", "replace").strip()

    def list_paths(self, revision: str) -> list[str]:
        """Every file path in the revision's tree, sorted, NUL-delimited for exact names."""
        output = self._run("ls-tree", "-r", "-z", "--name-only", revision)
        paths = [entry.decode("utf-8") for entry in output.split(b"\0") if entry]
        return sorted(paths)

    def read_blob(self, revision: str, path: str) -> bytes:
        """Exact bytes of ``path`` at ``revision`` (the content hash is taken over these)."""
        object_id = (
            self._run("rev-parse", "--verify", "--end-of-options", f"{revision}:{path}")
            .decode("utf-8", "replace")
            .strip()
        )
        return self._run("cat-file", "blob", object_id)

    def _run(self, *args: str) -> bytes:
        try:
            result = subprocess.run(
                ["git", *GIT_READ_FLAGS, *args],
                cwd=self.root,
                capture_output=True,
                check=False,
            )
        except FileNotFoundError as exc:
            raise IngestionError(
                "git is not installed; ingestion reads committed revisions through the Git CLI"
            ) from exc
        if result.returncode != 0:
            detail = result.stderr.decode("utf-8", "replace").strip() or "no diagnostic output"
            raise IngestionError(f"git {' '.join(args)} failed in {self.root}: {detail}")
        return result.stdout
```

`backend/app/ingestion/scan.py`:
```python
"""Scan one repository revision into domain artifacts.

DT-01 covers requirements and Gherkin scenarios. Source and test annotations are added by
DT-02; the scan is deliberately not extensible ahead of a story that needs it.
"""

from __future__ import annotations

import hashlib

from pydantic import ValidationError

from app.domain.enums import ArtifactType
from app.domain.models import Artifact
from app.ingestion.errors import IngestionError
from app.ingestion.parsers import parse_front_matter, parse_scenarios
from app.ingestion.repository import GitRepository

REQUIREMENTS_PREFIX = "requirements/"
FEATURES_PREFIX = "features/"

#: ``artifact_id`` prefixes are part of the identity contract (docs/domain-contracts.md).
ARTIFACT_ID_PREFIX = {
    ArtifactType.REQUIREMENT: "REQ-",
    ArtifactType.SCENARIO: "SCN-",
    ArtifactType.SOURCE: "CODE-",
    ArtifactType.TEST: "TEST-",
}


def scan_artifacts(
    repository: GitRepository, revision: str, *, repository_name: str
) -> list[Artifact]:
    """Every declared artifact at ``revision``, in tree order.

    Raises :class:`IngestionError` for unreadable content, malformed declarations, or duplicate
    artifact identities. A caller never receives a silently partial inventory.
    """
    artifacts: list[Artifact] = []
    declared_at: dict[str, str] = {}

    for path in repository.list_paths(revision):
        blob = repository.read_blob(revision, path)
        if path.startswith(REQUIREMENTS_PREFIX) and path.endswith(".md"):
            found = [
                _requirement(blob, path=path, revision=revision, repository_name=repository_name)
            ]
        elif path.startswith(FEATURES_PREFIX) and path.endswith(".feature"):
            found = _scenarios(blob, path=path, revision=revision, repository_name=repository_name)
        else:
            continue

        for artifact in found:
            previous = declared_at.get(artifact.artifact_id)
            if previous is not None:
                raise IngestionError(
                    f"{revision}: duplicate artifact id {artifact.artifact_id!r}: declared by "
                    f"{previous} and {artifact.locator}"
                )
            declared_at[artifact.artifact_id] = artifact.locator
            artifacts.append(artifact)

    return artifacts


def _requirement(blob: bytes, *, path: str, revision: str, repository_name: str) -> Artifact:
    where = f"{revision}:{path}"
    fields = parse_front_matter(_decode(blob, where=where), where=where)
    missing = {"id", "title"} - fields.keys()
    if missing:
        raise IngestionError(f"{where}: missing front matter keys {sorted(missing)}")
    return _artifact(
        artifact_id=fields["id"],
        artifact_type=ArtifactType.REQUIREMENT,
        title=fields["title"],
        locator=path,
        blob=blob,
        revision=revision,
        repository_name=repository_name,
        metadata={"status": fields.get("status", "active")},
    )


def _scenarios(blob: bytes, *, path: str, revision: str, repository_name: str) -> list[Artifact]:
    where = f"{revision}:{path}"
    declarations = parse_scenarios(_decode(blob, where=where), where=where)
    return [
        _artifact(
            artifact_id=declaration.scenario_id,
            artifact_type=ArtifactType.SCENARIO,
            title=declaration.title,
            locator=f"{path}#{declaration.scenario_id}",
            blob=blob,
            revision=revision,
            repository_name=repository_name,
        )
        for declaration in declarations
    ]


def _artifact(
    *,
    artifact_id: str,
    artifact_type: ArtifactType,
    title: str,
    locator: str,
    blob: bytes,
    revision: str,
    repository_name: str,
    metadata: dict[str, str] | None = None,
) -> Artifact:
    path = locator.split("#", 1)[0]
    prefix = ARTIFACT_ID_PREFIX[artifact_type]
    if not artifact_id.startswith(prefix):
        raise IngestionError(
            f"{revision}:{locator}: a {artifact_type.value} artifact id must start with "
            f"{prefix!r}, got {artifact_id!r}"
        )
    try:
        return Artifact(
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            title=title,
            source_uri=f"fixture://{repository_name}/{path}",
            repository=repository_name,
            revision=revision,
            content_hash=f"sha256:{hashlib.sha256(blob).hexdigest()}",
            locator=locator,
            metadata=metadata or {},
        )
    except ValidationError as exc:
        raise IngestionError(f"{revision}:{locator}: invalid artifact declaration:\n{exc}") from exc


def _decode(blob: bytes, *, where: str) -> str:
    try:
        return blob.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise IngestionError(f"{where}: artifact file is not UTF-8 text: {exc}") from exc
```

### New tests (complete)

`backend/tests/test_ingestion_parsers.py`:
```python
"""Unit tests for the pure artifact-declaration parsers (DT-01)."""

from __future__ import annotations

import pytest

from app.ingestion.errors import IngestionError
from app.ingestion.parsers import parse_front_matter, parse_scenarios

WHERE = "test:requirements/REQ-900.md"


# ---------------------------------------------------------------------------- front matter


def test_front_matter_returns_the_declared_fields() -> None:
    text = "---\nid: REQ-900\ntitle: A stated title\nstatus: active\n---\n\n# Body\n"
    assert parse_front_matter(text, where=WHERE) == {
        "id": "REQ-900",
        "title": "A stated title",
        "status": "active",
    }


def test_front_matter_rejects_a_file_without_a_block() -> None:
    with pytest.raises(IngestionError, match="front matter block at the start"):
        parse_front_matter("# No front matter\n", where=WHERE)


def test_front_matter_rejects_an_unterminated_block() -> None:
    with pytest.raises(IngestionError, match="not terminated"):
        parse_front_matter("---\nid: REQ-900\n", where=WHERE)


def test_front_matter_rejects_an_unusable_line() -> None:
    with pytest.raises(IngestionError, match="unusable front matter line"):
        parse_front_matter("---\nid: REQ-900\nnot a pair\n---\n", where=WHERE)


def test_front_matter_rejects_a_duplicate_key() -> None:
    with pytest.raises(IngestionError, match="duplicate front matter key"):
        parse_front_matter("---\nid: REQ-900\nid: REQ-901\n---\n", where=WHERE)


# ------------------------------------------------------------------------------- scenarios


def test_scenarios_use_the_tag_as_identity_and_the_line_as_title() -> None:
    text = (
        "Feature: Demo\n\n"
        "  @SCN-901\n"
        "  Scenario: First behaviour\n"
        "    Given a thing\n\n"
        "  @SCN-902\n"
        "  Scenario: Second behaviour\n"
        "    Then another thing\n"
    )
    assert [(item.scenario_id, item.title) for item in parse_scenarios(text, where=WHERE)] == [
        ("SCN-901", "First behaviour"),
        ("SCN-902", "Second behaviour"),
    ]


def test_untagged_scenarios_are_ignored() -> None:
    text = (
        "Feature: Demo\n\n"
        "  Scenario: No identity\n"
        "    Given a thing\n\n"
        "  @SCN-903\n"
        "  Scenario: Tagged\n"
        "    Then another thing\n"
    )
    assert [item.scenario_id for item in parse_scenarios(text, where=WHERE)] == ["SCN-903"]


def test_a_tag_must_be_followed_by_a_scenario_line() -> None:
    text = "Feature: Demo\n\n  @SCN-904\n  Rule: not a scenario\n"
    with pytest.raises(IngestionError, match="tag @SCN-904 is not followed by a 'Scenario:' line"):
        parse_scenarios(text, where=WHERE)


def test_a_new_tag_before_a_scenario_line_is_a_broken_declaration() -> None:
    text = "Feature: Demo\n\n  @SCN-905\n  @SCN-906\n  Scenario: Only one identity\n"
    with pytest.raises(IngestionError, match="tag @SCN-905 is not followed"):
        parse_scenarios(text, where=WHERE)


def test_identity_tag_may_share_a_line_with_non_identity_tags() -> None:
    text = "Feature: Demo\n\n  @smoke @SCN-907 @AC-9.9\n  Scenario: Tagged with friends\n"
    assert [item.scenario_id for item in parse_scenarios(text, where=WHERE)] == ["SCN-907"]


def test_one_scenario_line_cannot_carry_two_identity_tags() -> None:
    text = "Feature: Demo\n\n  @SCN-908 @SCN-909\n  Scenario: Ambiguous identity\n"
    with pytest.raises(IngestionError, match="more than one identity tag"):
        parse_scenarios(text, where=WHERE)
```

`backend/tests/test_ingestion_artifacts.py`:
```python
"""DT-01 acceptance: requirements and Gherkin scenarios become stable artifacts.

Expectations come from the committed snapshot (shared fixture input) and from independently
computed Git blob hashes, never from the scanner's own output.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

from app.domain.enums import ArtifactType
from app.domain.oracle import FixtureSnapshot
from app.ingestion import GitRepository, IngestionError, scan_artifacts

KEPT_TYPES = {ArtifactType.REQUIREMENT, ArtifactType.SCENARIO}


def make_repo(tmp_path: Path, files: dict[str, str]) -> GitRepository:
    """A throwaway repository whose committed content is exactly ``files``."""
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
        "user.name=Ingestion Test",
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


def requirement(requirement_id: str, title: str = "A title", status: str = "active") -> str:
    return f"---\nid: {requirement_id}\ntitle: {title}\nstatus: {status}\n---\n\n# Body\n"


def feature(*, tag: str, title: str, untagged: bool = False) -> str:
    body = f"Feature: Demo\n\n  @{tag}\n  Scenario: {title}\n    Given a thing\n"
    if untagged:
        body += "\n  Scenario: Anonymous\n    Given another thing\n"
    return body


# ------------------------------------------------------------------------ SCN-501, SCN-502


def test_requirement_document_is_parsed_into_an_artifact(
    built_fixture, snapshot: FixtureSnapshot
) -> None:
    repository = GitRepository(root=built_fixture.repo)
    revision = built_fixture.tag("baseline-a")
    artifacts = {
        item.artifact_id: item
        for item in scan_artifacts(repository, revision, repository_name="banking-demo")
    }

    artifact = artifacts["REQ-001"]
    expected = next(
        item
        for entry in snapshot.baselines
        if entry.baseline == "baseline-a"
        for item in entry.artifacts
        if item.artifact_id == "REQ-001"
    )
    assert artifact == expected
    assert artifact.artifact_type is ArtifactType.REQUIREMENT
    assert artifact.title == "Instant withdrawal availability"
    assert artifact.locator == "requirements/REQ-001.md"
    assert artifact.metadata == {"status": "active"}
    assert artifact.revision == revision
    assert artifact.content_hash == built_fixture.blob_sha256(revision, "requirements/REQ-001.md")


def test_scenario_identity_comes_from_the_gherkin_tag(
    built_fixture, snapshot: FixtureSnapshot
) -> None:
    repository = GitRepository(root=built_fixture.repo)
    revision = built_fixture.tag("baseline-a")
    artifacts = scan_artifacts(repository, revision, repository_name="banking-demo")
    by_id = {item.artifact_id: item for item in artifacts}

    scenario = by_id["SCN-001"]
    expected = next(
        item
        for entry in snapshot.baselines
        if entry.baseline == "baseline-a"
        for item in entry.artifacts
        if item.artifact_id == "SCN-001"
    )
    assert scenario == expected
    assert scenario.artifact_type is ArtifactType.SCENARIO
    assert scenario.locator == "features/withdrawals.feature#SCN-001"
    assert scenario.title == "Successful instant withdrawal"
    assert scenario.content_hash == built_fixture.blob_sha256(
        revision, "features/withdrawals.feature"
    )

    # Unannotated files are not artifacts: this revision declares none of them.
    assert not [item for item in artifacts if item.locator.startswith(("src/", "tests/"))]


def test_parsed_artifacts_match_the_committed_snapshot_for_requirements_and_scenarios(
    built_fixture, snapshot: FixtureSnapshot
) -> None:
    repository = GitRepository(root=built_fixture.repo)
    for entry in snapshot.baselines:
        expected = {
            item.artifact_id: item for item in entry.artifacts if item.artifact_type in KEPT_TYPES
        }
        actual = {
            item.artifact_id: item
            for item in scan_artifacts(repository, entry.commit, repository_name="banking-demo")
        }
        assert actual == expected, entry.baseline


# ---------------------------------------------------------------- SCN-503 … SCN-506 failures


def test_requirement_without_front_matter_is_rejected(tmp_path: Path) -> None:
    repository = make_repo(
        tmp_path,
        {
            "requirements/GOOD.md": requirement("REQ-901"),
            "requirements/BROKEN.md": "# Missing front matter\n",
        },
    )
    with pytest.raises(IngestionError, match="requirements/BROKEN.md"):
        scan_artifacts(repository, repository.resolve(), repository_name="demo")


def test_untagged_scenario_creates_no_artifact(tmp_path: Path) -> None:
    repository = make_repo(
        tmp_path,
        {
            "features/demo.feature": feature(
                tag="SCN-903", title="Only the tagged one", untagged=True
            )
        },
    )
    artifacts = scan_artifacts(repository, repository.resolve(), repository_name="demo")
    assert [item.artifact_id for item in artifacts] == ["SCN-903"]
    assert not [item for item in artifacts if item.title == "Anonymous"]


def test_dangling_scenario_tag_is_rejected(tmp_path: Path) -> None:
    repository = make_repo(
        tmp_path,
        {"features/demo.feature": "Feature: Demo\n\n  @SCN-999\n  Rule: broken\n"},
    )
    with pytest.raises(IngestionError, match="@SCN-999"):
        scan_artifacts(repository, repository.resolve(), repository_name="demo")


def test_duplicate_artifact_identities_are_rejected(tmp_path: Path) -> None:
    repository = make_repo(
        tmp_path,
        {
            "requirements/one.md": requirement("REQ-900", title="First"),
            "requirements/two.md": requirement("REQ-900", title="Second"),
        },
    )
    with pytest.raises(IngestionError, match="REQ-900"):
        scan_artifacts(repository, repository.resolve(), repository_name="demo")


def test_requirement_id_with_the_wrong_type_prefix_is_rejected(tmp_path: Path) -> None:
    repository = make_repo(
        tmp_path, {"requirements/one.md": requirement("CODE-001", title="Wrong kind")}
    )
    with pytest.raises(IngestionError, match="must start with 'REQ-'"):
        scan_artifacts(repository, repository.resolve(), repository_name="demo")
```

### New documentation (complete)

`docs/stories/DT-01.md`:
```markdown
# DT-01 — Requirements and Gherkin scenarios parsed into stable artifacts

**Milestone:** M1 — AI-free vertical slice · **Owner:** B · **Implementer:** OMP (shared
integration owner for the API boundary) · **Status:** refined, implementation in progress.

| Record | Value |
| --- | --- |
| Roadmap / feature | F-02 Ingestion · roadmap §6 DT-01 |
| GitHub story | [#20](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/20) — verified 2026-11-13T00:52:26Z (`gh issue view`), state OPEN, milestone "M1 — AI-free vertical slice" |
| Parent feature issue | [#9](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/9) |
| Canonical criteria | [DT-01.feature](DT-01.feature), sha256 `92440cffffee2ebcb344cba4842b242293891e72cbad8e1d42ebf01a21c000da` |
| Upstream obligation | Roadmap §4 artifact contract, §5 fixture discipline, §6 F-02; project-definition REQ-105 (draft, not approved) |
| Dependencies | M0 approved (FT-01 #18, FT-02 #19). No later-milestone dependency |

## User outcome

A systems engineer can point the system at a repository revision and receive stable artifact
identities for requirements and Gherkin scenarios, with the revision and content hash that the
identity was read at. Later rules and change detection can rely on those identities without
re-parsing ad hoc files.

## Scope

* Parse requirement front matter (`id`, `title`, `status`) from `requirements/*.md`.
* Parse `@SCN-nnn`-tagged scenarios from `features/*.feature`; the artifact locator anchors the
  scenario inside its file; the title is the scenario name.
* Read bytes from the pinned Git revision (not the working tree) and compute
  `content_hash = sha256:<hex>` over the blob.
* Fail loudly on malformed input: missing/torn front matter, a dangling `@SCN` tag, two identity
  tags on one line, an artifact id whose prefix disagrees with its type, duplicate artifact
  identities, or unreadable/non-UTF-8 files.
* Accept additional non-identity Gherkin tags on the same line (`@smoke @SCN-907`); only the
  `@SCN-nnn` token declares identity.
* Compare the parsed result with the committed `fixtures/api-responses/snapshot.json` for the
  requirement and scenario subset.

## Non-goals

* Source and test artifacts, Git change comparison, links, evidence, threads, rules, and API
  routes. DT-02/DT-03/DT-04/AS-01 own those; this story creates no empty scaffolding for them.
* General repository discovery (nested paths, configurable conventions) and non-Markdown
  requirement formats. The M1 convention is the fixture layout; widening it needs a later story.
* A Gherkin runner or step bindings.
* Accepting untrusted repository content as trusted: parsed titles are data, never executed or
  interpreted as instructions.

## Preservation boundaries

* The M0 fixture repository, generated snapshot/responses, oracle labels, and contracts are
  inputs. This story adds read-only parsing code and changes no generated file.
* `tools/fixturectl.py` keeps producing the M0 fixtures during this story. The shared parser is
  reused by the generator in DT-02, after the scanner also covers source/test artifacts, so the
  snapshot remains the generator's authoritative output at every step.
* No schema-version change: no request/response shape is added.

## Design impact

Creates `backend/app/ingestion/`:

| Module | Responsibility |
| --- | --- |
| `errors.py` | `IngestionError` for malformed repository content; mapped to a documented problem by the caller |
| `parsers.py` | Pure text parsers: front matter and tagged scenarios |
| `repository.py` | `GitRepository`: revision resolution, tree listing, blob reads via the Git CLI |
| `scan.py` | Revision scan → `Artifact` list, with duplicate-identity rejection |

Parsers are pure functions so malformed-input cases are unit-testable without Git. Git access is
read-only and uses the repository's existing Git prerequisite (roadmap §3 allows the Git CLI).
No database is introduced (ADR 0006 #1 stays open; DT-04 documents the M1 in-process store).

Assumptions (load-bearing, stated here):

1. Requirements live at `requirements/*.md`; scenarios live at `features/*.feature`, matching the
   fixture and `docs/domain-contracts.md`.
2. A scenario tag immediately precedes its `Scenario:` line, optionally separated by blank lines.
3. Artifact granularity is file level; every scenario in one file shares that file's content hash.
4. Identity is path-stable; a renamed file is a new artifact (ADR 0006 #8).

## Refinement disposition

The criteria are derived from the owner-authored GitHub intake and roadmap §6; failure and
boundary scenarios were added without weakening the intake criteria. This is a refinement freeze
by the implementer, not a product-owner approval: no separate human refinement sign-off is
recorded, and the draft project definition is not treated as an approved requirements baseline.
Implementation acceptance is decided by the independent review recorded in
`docs/reviews/`.

## Verification mapping

| Scenario | Observable check | Pytest selector |
| --- | --- | --- |
| SCN-501 | Ingests the built fixture at `baseline-a`; compares `REQ-001` to the committed snapshot and to an independently computed blob hash | `backend/tests/test_ingestion_artifacts.py::test_requirement_document_is_parsed_into_an_artifact` |
| SCN-502 | Compares `SCN-001` (locator, title) to the snapshot; asserts unannotated files yield nothing | `backend/tests/test_ingestion_artifacts.py::test_scenario_identity_comes_from_the_gherkin_tag` |
| SCN-503 | Temp repository with a front-matter-less requirement raises `IngestionError` naming the path | `backend/tests/test_ingestion_artifacts.py::test_requirement_without_front_matter_is_rejected` |
| SCN-504 | Feature file with an untagged scenario yields no artifact for it | `backend/tests/test_ingestion_artifacts.py::test_untagged_scenario_creates_no_artifact` |
| SCN-505 | Dangling tag raises `IngestionError` naming the tag | `backend/tests/test_ingestion_artifacts.py::test_dangling_scenario_tag_is_rejected` |
| SCN-506 | Two files declaring `REQ-900` raise `IngestionError` naming the id | `backend/tests/test_ingestion_artifacts.py::test_duplicate_artifact_identities_are_rejected` |
| DoD: parse vs snapshot | Every requirement/scenario in the snapshot is reproduced with identical id, type, locator, title, revision, hash | `::test_parsed_artifacts_match_the_committed_snapshot_for_requirements_and_scenarios` |
| DoD: malformed parsers | Direct parser tests for front matter and tags | `backend/tests/test_ingestion_parsers.py` |

A mapping row is not an execution result; the run record in
`docs/reports/omp-dt-01-ingestion/IMPLEMENTATION.md` carries the actual invocation and outcome.

## Verification plan

```bash
uv run --project backend pytest backend/tests/test_ingestion_artifacts.py \
  backend/tests/test_ingestion_parsers.py -q
uv run --project backend pytest backend/tests -q
uv run --project backend ruff check .
uv run --project backend ruff format --check .
```

Limitations: the M1 scanner does not yet parse source/test artifacts, links, or evidence; the
API still serves the M0 fixture read model until DT-04. No Gherkin runner executes the scenarios.
```

`docs/reports/omp-dt-01-ingestion/IMPLEMENTATION.md`:
```markdown
# DT-01 implementation record — requirements and Gherkin parsed into stable artifacts

| Field | Value |
| --- | --- |
| Story | DT-01 — [#20](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/20), verified OPEN on 2026-11-13T00:52:26Z (`gh issue view`, milestone "M1 — AI-free vertical slice") |
| Canonical criteria | [DT-01.feature](../../stories/DT-01.feature), sha256 `92440cffffee2ebcb344cba4842b242293891e72cbad8e1d42ebf01a21c000da` |
| Brief / verification map | [DT-01.md](../../stories/DT-01.md) |
| Branch / base | `feat/20-dt-01-ingestion` from `e18cdcfafe058e2f1d99c3c0b4bc2e155e9b16c9` |
| Contract version | `SCHEMA_VERSION = 0.1.0`, `PACKAGE_VERSION = 0.1.0` (no contract change) |
| Snapshot captured | 2026-11-13T00:58:20Z |

## What changed

| Path | sha256 | Purpose |
| --- | --- | --- |
| `backend/app/ingestion/__init__.py` | `c87a149c478ddbcd7322ffbdda723362bda18729da264048be5c3eaa9e58cdbf` | Package exports |
| `backend/app/ingestion/errors.py` | `b33cd36ad1a42f9f18720cf11f5d42aea424646ba8ff5b286587995ab2799a1d` | `IngestionError` for malformed content / Git access |
| `backend/app/ingestion/parsers.py` | `6d8455aa8a9b0a963c162e332e6938dc1d1a094b2276686cf4ce598ae214041b` | Pure front-matter and `@SCN` scenario parsers |
| `backend/app/ingestion/repository.py` | `eaaec286ca5dddff28914b6e3a431338a4082b17edd703548ec9fda811d6c005` | Read-only Git access at explicit revisions |
| `backend/app/ingestion/scan.py` | `34977ced7b3044ef8f6826f0ed0a07b3883251ed164220249f456d9b8ea8a45e` | Revision scan → `Artifact` inventory, duplicate/prefix guards |
| `backend/tests/test_ingestion_parsers.py` | `95b3762b1d20b3e6d58b18ef107f8626e2ee35e9132a8caf7e3a9848ce931b93` | 11 parser unit tests |
| `backend/tests/test_ingestion_artifacts.py` | `eabf4dc27132b4489fbcfcf249e2d20a61159743ee934e19b08805870f2c8425` | 8 acceptance tests against the built fixture and temp repositories |
| `docs/stories/DT-01.feature` | `92440cffffee2ebcb344cba4842b242293891e72cbad8e1d42ebf01a21c000da` | Canonical criteria |
| `docs/stories/DT-01.md` | `75fc1d5fcc2cb4df1c33dcb05297a6d506322a13df4fa76d8ce847870fab5507` | Brief, assumptions, verification map |
| `docs/architecture.md` | `5926759c78412da49573bdb745fb1369db2e3e0786f774eb0556280c9ddbcbd9` | Ingestion status is no longer "absent" |
| `docs/STATUS.md` | `5d949036dfa341290b54ec4f0dac1c4e075a07d8ae567de0b3ff50684c2e9619` | M1 roadmap ledger and active task |

Generated fixtures, oracle labels, contract models, and the API are untouched. `tools/fixturectl.py`
still produces the M0 fixtures and is reused by ingestion only in DT-02, after the scanner also
covers source/test artifacts.

## Acceptance results

| Criterion | Check | Result |
| --- | --- | --- |
| SCN-501 requirement parsed | `tests/test_ingestion_artifacts.py::test_requirement_document_is_parsed_into_an_artifact` — compares the whole `Artifact` to the committed snapshot and the hash to an independently read blob | PASS |
| SCN-502 scenario identity | `::test_scenario_identity_comes_from_the_gherkin_tag` | PASS |
| SCN-503 missing front matter | `::test_requirement_without_front_matter_is_rejected` | PASS |
| SCN-504 untagged scenario | `::test_untagged_scenario_creates_no_artifact` | PASS |
| SCN-505 dangling tag | `::test_dangling_scenario_tag_is_rejected` | PASS |
| SCN-506 duplicate identity | `::test_duplicate_artifact_identities_are_rejected` | PASS |
| DoD parse vs snapshot | `::test_parsed_artifacts_match_the_committed_snapshot_for_requirements_and_scenarios` (both baselines, every requirement/scenario field) | PASS |
| DoD malformed parsers | `tests/test_ingestion_parsers.py` (front matter, tags, multi-tag, duplicate key, two identity tags) | PASS |
| Additional guard (self-review) | `::test_requirement_id_with_the_wrong_type_prefix_is_rejected` | PASS |

Axis coverage: success (SCN-501/502), failure (SCN-503/505/506), boundary (SCN-504, multi-tag
line, wrong id prefix). No scenario was weakened from the issue intake.

## Commands and outcomes (as captured)

Raw logs are in the external run directory `…/m1-roadmap-20261112/dt-01/`; the outcomes below are
copied from the captured files at the timestamps shown.

```text
captured_start=2026-11-13T00:57:57Z
pytest backend/tests -q                         exit 0   154 passed, 1 warning in 3.89s
fixturectl.py verify                            exit 0   reproducible and committed files current
ruff check .                                    exit 0   All checks passed
ruff format --check .                           exit 0   42 files already formatted
git diff --check                                exit 0
captured_end=2026-11-13T00:58:02Z
```

Network denial (2026-11-13T00:58:10Z): `unshare -rn backend/.venv/bin/python` probe produced
`OSError: [Errno 101] Network is unreachable`; the full suite then reported `154 passed` with exit
0 under the same wrapper. This proves the suite needs no network; it does not prove the absence of
network use by git, which is local.

## Self-review

* **Proposals / accepted / evidence separation:** ingestion only *reads* artifact declarations.
  It does not read links or evidence yet and cannot create a link, review state, or evidence
  record. `TraceCandidate` is not involved.
* **Revision-aware:** `Artifact.revision` is the resolved commit SHA; `content_hash` is sha256 of
  the blob at that revision. The working tree is never read. A temp-repository test commits, then
  scans, so the hash comes from the Git object store.
* **Offline:** pure parsers plus the local Git CLI; no model, network, database, or Docker.
* **Independent expectations:** the snapshot comparison uses committed fixture data; the hash
  check uses `fixturectl.git_blob` (the fixture tool), not the scanner's hashing.
* **Failure honesty:** malformed declarations raise instead of being skipped; duplicate identity,
  type/prefix mismatch, and ambiguous identity tags are rejected.
* **Untrusted input:** repository text is decoded and validated; it is never executed or
  interpreted. Git arguments use `--end-of-options` and NUL-delimited tree output.
* **No earlier-milestone regression:** the full suite and fixture drift check pass.

Known limits (stated, not hidden): source/test annotations, links, evidence, thread assembly, and
the API cutover are later M1 stories; general repository layouts are out of scope; artifact
granularity is file level (ADR 0006).

## Independent review

**Pending.** Submission 1 will be recorded in `docs/reviews/DT-01-review.md` with the exact model
and effort; this record will be updated with the verdict and finding dispositions. Implementation
acceptance is not claimed before that verdict.
```

## 4. Implementation context

* Existing M0 architecture (unchanged by this slice): `docs/architecture.md`,
  `docs/domain-contracts.md`. The fixture generator `tools/fixturectl.py` already contains
  equivalent scanning logic for generated snapshots; DT-01 deliberately does **not** rewire it yet.
  DT-02 extends the scanner to source/test artifacts and then makes the generator reuse the shared
  parser, so generator and ingestion converge without a mid-story behavior change.
* New package entry point: `app.ingestion.scan_artifacts(repository, revision, repository_name)`.
  `app.ingestion.GitRepository` reads committed objects only (rev-parse / ls-tree -z / cat-file).
* Parser conventions come from `docs/domain-contracts.md` (Artifact identity) and the fixture
  layout `requirements/*.md`, `features/*.feature`.
* Tests use `built_fixture` (a fresh nested repository built from `fixtures/banking-demo`) and the
  committed `fixtures/api-responses/snapshot.json` as independent expectations.
* Targeted follow-up reads: `backend/app/domain/models.py` (Artifact), `docs/domain-contracts.md`
  (identity/hash rules), `backend/tests/conftest.py` (built_fixture helper),
  `tools/fixturectl.py` (generator scanning behavior this slice does not yet replace).

## 5. Evidence

| Criterion | Check (pytest selector) | Observed result |
| --- | --- | --- |
| SCN-501 | `tests/test_ingestion_artifacts.py::test_requirement_document_is_parsed_into_an_artifact` | PASS |
| SCN-502 | `::test_scenario_identity_comes_from_the_gherkin_tag` | PASS |
| SCN-503 | `::test_requirement_without_front_matter_is_rejected` | PASS |
| SCN-504 | `::test_untagged_scenario_creates_no_artifact` | PASS |
| SCN-505 | `::test_dangling_scenario_tag_is_rejected` | PASS |
| SCN-506 | `::test_duplicate_artifact_identities_are_rejected` | PASS |
| DoD snapshot equality | `::test_parsed_artifacts_match_the_committed_snapshot_for_requirements_and_scenarios` | PASS |
| DoD malformed parsers | `tests/test_ingestion_parsers.py` (11 tests) | PASS |
| Self-review guard | `::test_requirement_id_with_the_wrong_type_prefix_is_rejected` | PASS |

Actual invocations and exits, captured 2026-11-13T00:57:57Z–00:58:20Z:

```text
uv run --project backend pytest backend/tests -q              exit 0  154 passed, 1 warning in 3.89s
uv run --project backend python tools/fixturectl.py verify    exit 0  reproducible and committed files current
uv run --project backend ruff check .                         exit 0  All checks passed
uv run --project backend ruff format --check .                exit 0  42 files already formatted
git diff --check                                              exit 0
unshare -rn backend/.venv/bin/python -m pytest backend/tests  exit 0  154 passed
  (denial proven by a socket probe: OSError [Errno 101] Network is unreachable)
```

Evidence provenance: the full-suite and gate logs are raw files in the external run directory;
the committed `IMPLEMENTATION.md` records the same exits and timestamps. The snapshot comparison
uses committed fixture data, not the scanner's output. NOT RUN: any API/HTTP check (no route is
added in this story), any frontend check, and any general-repository ingestion beyond the fixture
layout.

## 6. File-integrity requirement

The manifest above is the reviewed snapshot. If any manifest hash changed, the snapshot is not
the one reviewed. Do not edit files, install dependencies, regenerate fixtures, or commit.

## Reviewer instructions (mandatory)

You are the independent CTA implementation reviewer using GPT-6.1 Sol xhigh. Decide whether this exact snapshot satisfies the supplied story, every applicable Gherkin criterion, and repository invariants. Treat OMP's summaries and test results as claims to check against the supplied artifacts and targeted source inspection. Check proposal/accepted/evidence separation, real port compatibility, revision/content-hash semantics, honest errors/501s, independent oracle expectations, offline defaults, and generated-file discipline where relevant. Do not demand implementation of a later milestone. Do not edit files, implement repairs, regenerate fixtures, commit, or delegate. Ask OMP for missing runtime evidence; distinguish observed defects from hypotheses and unavailable checks. Return an AC-by-AC PASS, FAIL, or NOT VERIFIED assessment and actionable findings with stable IDs, severity, blocking status, AC/invariant, path/line, expected/actual behavior, and smallest correction/recheck. Keep optional suggestions and unrelated pre-existing defects separate. Return exactly one verdict: APPROVE, REQUEST_CHANGES, or NEEDS_INPUT. APPROVE requires every applicable criterion/check to be satisfied, no unresolved blocker, and the exact snapshot identified. In later rounds verify prior dispositions and regressions while retaining the complete acceptance assessment. A passing process, passing tests, or exhausted review limit is not approval. Agent review cannot attest human labeling or human link decisions.
