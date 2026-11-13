# Independent implementation review — DT-02, submission 1 of 7

## 1. Story and authorization

**Task:** DT-02 — Source and test artifacts tied to path and Git revision.
**Roadmap/feature:** F-02 Ingestion, roadmap §6 DT-02; milestone **M1 — AI-free vertical slice**.
**GitHub story:** anthonygraca/gherkin-knowledge-graph issue **#21**, verified OPEN at
2026-11-13T02:01:06Z (`gh issue view`), milestone "M1 — AI-free vertical slice".
**Owner:** B. **Implementer/integrator:** OMP. **Repository:** `<task_repo>` (read-only sandbox).
**Base:** `26a25d0b739994631e098e6eae5307a47325a0ba` (`main`, DT-01 merge).
**Branch:** `feat/21-dt-02-source-test-artifacts`.
**Submission:** 1 of 7.

### User outcome

An engineer can trust that `CODE-*` and `TEST-*` artifacts describe the committed file at the
requested revision, so later change detection compares hashes that correspond to repository
content rather than to a developer's working tree.

### Scope

First-line `# cta:artifact CODE-nnn` / `TEST-nnn` parsing, source/test scan support, first-line and
single-identity enforcement, committed-blob hashing, and generator reuse. Non-goals: links,
evidence, threads, store/API cutover (DT-03/DT-04); non-Python sources; sub-file granularity;
annotations anywhere but the first line; a Gherkin runner.

### Proposed commit reference

`feat(ingestion): [issue #21] parse source and test annotations from committed revisions` with body
`Refs #21` (and `Refs #20` for the generator convergence).

## 2. Acceptance criteria (canonical snapshot)

File `docs/stories/DT-02.feature`, sha256
`08c0e96d371724a9d640cefdc1e07d060e7c72cbfe141877022d662489d90e8a`.

```gherkin
# Canonical acceptance specification for DT-02 (#21), M1.
# Source criteria: the GitHub story intake at
# https://github.com/anthonygraca/gherkin-knowledge-graph/issues/21 (verified 2026-11-13T02:01:06Z)
# and roadmap §6 F-02. Failure and boundary scenarios were added during refinement; the two intake
# scenarios keep their intent.
# Verified by the pytest selectors mapped in DT-02.md. These scenarios are not currently bound
# to or executed by a Gherkin runner.
@DT-02 @issue-21 @M1
Feature: DT-02: Source and test artifacts tied to path and Git revision
  A Python file declares itself as a source or test artifact with a first-line
  `# cta:artifact CODE-nnn` / `TEST-nnn` annotation. Ingestion reads the committed blob at the
  requested revision, so revisions and content hashes describe what Git holds, not what the
  working tree happens to contain.

  @SCN-521
  Scenario: Source artifact declared by in-file annotation
    Given "src/accounts.py" begins with the annotation "# cta:artifact CODE-001"
    When the repository is ingested at "baseline-b"
    Then artifact "CODE-001" has type "source" and locator "src/accounts.py"
    And its revision is the commit tagged "baseline-b"
    And its content_hash differs from the same artifact at "baseline-a"

  @SCN-522
  Scenario: Files without an annotation are not artifacts
    Given "src/__init__.py" has no cta:artifact annotation
    When the repository is ingested
    Then no artifact references "src/__init__.py"

  @SCN-523
  Scenario: Test artifact declared by in-file annotation
    Given "tests/test_accounts.py" begins with "# cta:artifact TEST-001"
    When the repository is ingested at "baseline-a"
    Then artifact "TEST-001" has type "test" and locator "tests/test_accounts.py"
    And its content_hash is the sha256 of the committed blob

  @SCN-524
  Scenario: An annotation that is not on the first line is rejected
    Given a Python file whose annotation appears after its first line
    When the repository is ingested
    Then ingestion fails with an error naming that file

  @SCN-525
  Scenario: A file cannot declare two artifact identities
    Given a Python file containing two different cta:artifact annotations
    When the repository is ingested
    Then ingestion fails with an error naming the conflicting identities

  @SCN-526
  Scenario: Content hashes come from the committed revision
    Given an ingested revision with a clean working tree
    When a file is modified in the working tree without committing
    Then re-ingesting the same revision returns the committed content_hash
    And the artifact revision is unchanged

  @SCN-527
  Scenario: Every declared artifact matches the committed snapshot at both baselines
    Given the fixture repository built from its declarative history
    When each tagged baseline is ingested
    Then the artifact ids, types, titles, locators, revisions, and content hashes equal
      "fixtures/api-responses/snapshot.json" for that baseline
```

Refinement disposition: owner-authored issue intake + roadmap §6; failure/boundary scenarios were
added without weakening the intake. No separate human refinement sign-off is recorded; the draft
project definition is not an approved baseline.

Repository constraints (AGENTS.md): offline by default; proposals ≠ accepted links ≠ verification;
revision/content-hash semantics; independent oracle expectations; contract-only endpoints stay 501;
no generated-file hand edits.

## 3. Snapshot, manifest, and diff

Snapshot captured 2026-11-13T02:08Z. Manifest (sha256 of every task file):

```text
c87a149c478ddbcd7322ffbdda723362bda18729da264048be5c3eaa9e58cdbf  backend/app/ingestion/__init__.py
b33cd36ad1a42f9f18720cf11f5d42aea424646ba8ff5b286587995ab2799a1d  backend/app/ingestion/errors.py
4cff0a3a49c139d4b96f5e5e272714988a181fb8340f117d98a693a5002e26b6  backend/app/ingestion/parsers.py
eaaec286ca5dddff28914b6e3a431338a4082b17edd703548ec9fda811d6c005  backend/app/ingestion/repository.py
2a602ee3668bd1560e42aa8870c6a1875b3977a082d449109892852c73e0a613  backend/app/ingestion/scan.py
43483704398312b94ab55ff45f0e98ec496fde12ef4fc6ed9a730dd20b99b7c2  tools/fixturectl.py
d3f6ac078f68b1c7944d16b389df87bcd97afcdfb39d7943f1af22a3ca134b24  backend/tests/test_ingestion_parsers.py
5ca164098ccedbabf1691211220249323213e8d1f5257a90d3dfcfb6fed5d188  backend/tests/test_ingestion_artifacts.py
08c0e96d371724a9d640cefdc1e07d060e7c72cbfe141877022d662489d90e8a  docs/stories/DT-02.feature
8d071a4f6a559cc68ca2e362df66a527412934f5a688522e3c3f3a23710030c9  docs/stories/DT-02.md
a00a510fc5fd37c3b913656434d70891e17d4ad5d3f123ec010b79eccf1c7485  docs/architecture.md
0574dfde81c148af3ac02fd5e732337332fd013159e198eed0d55149e1e05cc3  docs/STATUS.md
e68436388edb6257b07f4d9a72c989e6245a55982c51751ddcac9a3ad045f898  docs/reports/omp-dt-02-artifacts/IMPLEMENTATION.md
21a63e84a06a2702fdeb2c13d55514b753a35351bb51ad1f3e683349a2d17eb0  docs/reports/omp-dt-02-artifacts/METRICS.md
0e26ce718d3a722469466b104fc36852609b984d67bef99c8d8bde1380a47baf  docs/reports/omp-dt-02-artifacts/PROMPT_LOG.md
```

Versions: `SCHEMA_VERSION = 0.1.0`, `PACKAGE_VERSION = 0.1.0`; no dependency change. No generated
fixture, oracle, contract, API response, or workflow file changed.

### Tracked-file diff (against base)

```diff
diff --git a/docs/STATUS.md b/docs/STATUS.md
index 3166e36..403ecd8 100644
--- a/docs/STATUS.md
+++ b/docs/STATUS.md
@@ -2,10 +2,10 @@
 
 ```text
 Date:                2026-11-13
-Current branch:      main at e18cdcf (PR #43 merged); M1 work starts from that revision
+Current branch:      feat/21-dt-02-source-test-artifacts (from main 26a25d0)
 Milestone:           M0 — exit gate SATISFIED by re-review round 2 (historical record below)
                      M1 — IN PROGRESS; gate NOT yet satisfied
-Active task:         DT-01 (#20) requirements and Gherkin parsed into stable artifacts
+Active task:         DT-02 (#21) source and test artifacts tied to path and Git revision
 Independent review:  docs/reviews/M0-review.md — first review: "M0 not verified"
                      docs/reviews/M0-rereview-1.md — re-review round 1 (GPT-6.1 Sol, xhigh):
                      NEEDS_INPUT; R1–R7 all repaired; AC-1.1…AC-1.8 and AC-2.1…AC-2.5 all PASS;
@@ -20,9 +20,11 @@ Historical (SETUP-01, 2026-11-12): the commit-reference slice landed via PR #42;
                      had 107 passed; the SETUP-01 tree then had 135 passed (also under an
                      OS-level network denial). Outstanding owner actions: #18/#19 closure, the
                      FT-03/project-definition reviews, the required-check ruleset, README work item.
-Tests executed:      DT-01 (2026-11-13T01:13Z): 169 passed (also under an OS-level network
-                     denial); fixturectl verify exit 0; ruff check/format clean. Round-1 review
-                     findings repaired; details in docs/reports/omp-dt-01-ingestion/.
+Tests executed:      DT-02 (2026-11-13T02:07Z): 197 passed (also under an OS-level network
+                     denial); fixturectl verify exit 0 with the generator reusing the shared
+                     scanner; ruff check/format clean.
+                     DT-01 approved snapshot: 183 passed; PR #44 merged as 26a25d0 with both
+                     hosted checks passing; issue #20 closed.
 Current API/schema version: 0.1.0
 Tracker:             docs/traceability-issue-map.md (features → user stories → tasks)
 Run records:         docs/reports/omp-m0-rereview/ and docs/reports/omp-setup-01-commitlint/
@@ -43,8 +45,8 @@ not claim that draft as an approved baseline.
 
 | Story | GitHub | Owner | Canonical feature | State |
 | --- | --- | --- | --- | --- |
-| DT-01 requirements + scenarios parsed | [#20](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/20) | B | [DT-01.feature](stories/DT-01.feature) | refined; implementation in review |
-| DT-02 source/test artifacts | [#21](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/21) | B | not yet written | eligible after DT-01 |
+| DT-01 requirements + scenarios parsed | [#20](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/20) | B | [DT-01.feature](stories/DT-01.feature) | **merged** PR [#44](https://github.com/anthonygraca/gherkin-knowledge-graph/pull/44) → `26a25d0`; APPROVE at submission 5; issue closed |
+| DT-02 source/test artifacts | [#21](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/21) | B | [DT-02.feature](stories/DT-02.feature) | refined; implementation in review |
 | DT-03 typed links + review state | [#22](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/22) | B | not yet written | eligible after DT-02 |
 | DT-04 requirement thread | [#23](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/23) | B | not yet written | eligible after DT-03 |
 | AS-01 missing-link finding | [#2](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/2) | C | not yet written | eligible after DT-04 |
diff --git a/docs/architecture.md b/docs/architecture.md
index b5522e8..246fb5a 100644
--- a/docs/architecture.md
+++ b/docs/architecture.md
@@ -41,7 +41,7 @@ Two rules explain most of the layout:
 | `app/discovery/fake.py` | Fixture-backed candidate provider | Working implementation (deliberately fake) |
 | `app/assurance/sample_findings.py` | Replay of reviewed sample findings | Mock service (rule engine arrives in C-PR1) |
 | `app/api/` | Routes, dependencies, RFC 9457 problem documents | Working |
-| `app/ingestion/` | Revision-pinned parsing: requirement/Gherkin artifacts (DT-01); source/test (DT-02), links (DT-03), store cutover (DT-04) | Requirements and scenarios implemented; the rest absent by design |
+| `app/ingestion/` | Revision-pinned parsing: requirement/Gherkin artifacts (DT-01), source/test annotations (DT-02), links (DT-03), store cutover (DT-04) | Requirements, scenarios, source, and test implemented; links/store absent by design |
 | `frontend/` | React/TypeScript dashboard | Absent by design; created in C-PR1 |
 
 ## Request flows
diff --git a/tools/fixturectl.py b/tools/fixturectl.py
index 20d46df..2294fb5 100755
--- a/tools/fixturectl.py
+++ b/tools/fixturectl.py
@@ -32,7 +32,7 @@ import sys
 import tempfile
 from collections.abc import Iterable, Iterator
 from pathlib import Path
-from typing import Any, TypeVar
+from typing import TypeVar
 
 from pydantic import BaseModel
 
@@ -40,7 +40,6 @@ from app.discovery.fake import FakeCandidateDiscovery, compute_index_revision
 from app.domain.api import DiscoveryResponse, ThreadResponse
 from app.domain.enums import ArtifactType, ReviewState
 from app.domain.models import (
-    Artifact,
     AssuranceFinding,
     TraceLink,
     VerificationEvidence,
@@ -58,6 +57,8 @@ from app.domain.oracle import (
     FixtureSnapshot,
     MaterializedFindings,
 )
+from app.ingestion import GitRepository, IngestionError
+from app.ingestion.scan import scan_artifacts as scan_revision_artifacts
 from app.persistence.fixtures import load_model
 from app.version import SCHEMA_VERSION
 
@@ -98,9 +99,6 @@ GIT_FLAGS = (
 )
 
 TOKEN_RE = re.compile(r"\{\{([A-Za-z0-9_:\-.]+)\}\}")
-ANNOTATION_RE = re.compile(r"^#\s*cta:artifact\s+((?:CODE|TEST)-\d{3})\s*$", re.MULTILINE)
-SCENARIO_TAG_RE = re.compile(r"^@(SCN-\d{3})$")
-SCENARIO_LINE_RE = re.compile(r"^\s*Scenario:\s*(\S.*?)\s*$")
 
 ModelT = TypeVar("ModelT", bound=BaseModel)
 
@@ -242,107 +240,6 @@ def build_repo(fixture_dir: Path, dest: Path) -> BaselinesManifest:
 # ----------------------------------------------------------------------------------------
 
 
-def parse_front_matter(text: str, *, where: str) -> dict[str, str]:
-    if not text.startswith("---\n"):
-        raise FixtureToolError(
-            f"{where}: expected a '---' front matter block at the start of the file"
-        )
-    end = text.find("\n---\n", 3)
-    if end == -1:
-        raise FixtureToolError(f"{where}: front matter block is not terminated by '---'")
-    fields: dict[str, str] = {}
-    for line in text[4:end].splitlines():
-        if not line.strip():
-            continue
-        key, separator, value = line.partition(":")
-        if not separator:
-            raise FixtureToolError(f"{where}: unusable front matter line {line!r}")
-        fields[key.strip()] = value.strip()
-    return fields
-
-
-def parse_scenarios(text: str, *, where: str) -> list[tuple[str, str]]:
-    """Return (scenario_id, title) pairs for ``@SCN-nnn`` tagged scenarios."""
-    found: list[tuple[str, str]] = []
-    pending: str | None = None
-    for line in text.splitlines():
-        tag = SCENARIO_TAG_RE.match(line.strip())
-        if tag:
-            pending = tag.group(1)
-            continue
-        if pending is None:
-            continue
-        match = SCENARIO_LINE_RE.match(line)
-        if match:
-            found.append((pending, match.group(1)))
-            pending = None
-    if pending is not None:
-        raise FixtureToolError(f"{where}: tag @{pending} is not followed by a 'Scenario:' line")
-    return found
-
-
-def scan_artifacts(repo: Path, commit: str, repository: str) -> list[Artifact]:
-    listed = git(["ls-tree", "-r", "--name-only", commit], cwd=repo).splitlines()
-    artifacts: list[Artifact] = []
-    for path in sorted(listed):
-        blob = git_blob(repo, commit, path)
-        content_hash = f"sha256:{__import__('hashlib').sha256(blob).hexdigest()}"
-        common: dict[str, Any] = {
-            "source_uri": f"fixture://{repository}/{path}",
-            "repository": repository,
-            "revision": commit,
-            "content_hash": content_hash,
-        }
-        if path.startswith("requirements/") and path.endswith(".md"):
-            fields = parse_front_matter(blob.decode("utf-8"), where=f"{commit}:{path}")
-            missing = {"id", "title"} - fields.keys()
-            if missing:
-                raise FixtureToolError(
-                    f"{commit}:{path}: missing front matter keys {sorted(missing)}"
-                )
-            artifacts.append(
-                Artifact(
-                    artifact_id=fields["id"],
-                    artifact_type=ArtifactType.REQUIREMENT,
-                    title=fields["title"],
-                    locator=path,
-                    metadata={"status": fields.get("status", "active")},
-                    **common,
-                )
-            )
-        elif path.startswith("features/") and path.endswith(".feature"):
-            for scenario_id, title in parse_scenarios(
-                blob.decode("utf-8"), where=f"{commit}:{path}"
-            ):
-                artifacts.append(
-                    Artifact(
-                        artifact_id=scenario_id,
-                        artifact_type=ArtifactType.SCENARIO,
-                        title=title,
-                        locator=f"{path}#{scenario_id}",
-                        **common,
-                    )
-                )
-        elif path.endswith(".py"):
-            annotation = ANNOTATION_RE.search(blob.decode("utf-8"))
-            if annotation:
-                artifact_id = annotation.group(1)
-                artifacts.append(
-                    Artifact(
-                        artifact_id=artifact_id,
-                        artifact_type=(
-                            ArtifactType.SOURCE
-                            if artifact_id.startswith("CODE")
-                            else ArtifactType.TEST
-                        ),
-                        title=path,
-                        locator=path,
-                        **common,
-                    )
-                )
-    return artifacts
-
-
 def load_evidence(repo: Path, commit: str) -> list[VerificationEvidence]:
     listed = git(["ls-tree", "-r", "--name-only", commit], cwd=repo).splitlines()
     if EVIDENCE_PATH not in listed:
@@ -395,7 +292,9 @@ def build_snapshot(manifest: BaselinesManifest, repo: Path) -> FixtureSnapshot:
             BaselineSnapshot(
                 baseline=tag,
                 commit=commit,
-                artifacts=scan_artifacts(repo, commit, manifest.fixture),
+                artifacts=scan_revision_artifacts(
+                    GitRepository(repo), commit, repository_name=manifest.fixture
+                ),
                 accepted_links=accepted,
                 proposed_links=proposed,
                 evidence=load_evidence(repo, commit),
@@ -711,7 +610,7 @@ def main(argv: list[str] | None = None) -> int:
             command_materialize()
             return 0
         return command_verify(api_dir=args.api_dir, baselines_path=args.baselines)
-    except FixtureToolError as exc:
+    except (FixtureToolError, IngestionError) as exc:
         print(f"fixturectl: {exc}", file=sys.stderr)
         return 2
 
```

### New and changed implementation files (complete)

`backend/app/ingestion/parsers.py`:
```python
"""Pure text parsers for artifact declarations.

Declaration conventions are defined in ``docs/domain-contracts.md``:

* requirement: YAML front matter with ``id:`` and ``title:`` in ``requirements/*.md``;
* scenario: an ``@SCN-nnn`` tag immediately preceding the Gherkin ``Scenario:`` line.

Parsers are pure functions over text so malformed-input behaviour is testable without Git, and
they never guess: an unrecognizable declaration raises :class:`IngestionError` rather than
producing a partial result.

Lexing rules that matter (each exists because a review probe broke a looser rule):

* Front-matter boundaries are ``---`` lines at column 0. The YAML document is the **exact original
  substring** between them — it is never split and rejoined, so control characters, Unicode line
  separators, and CRLF reach PyYAML unchanged. PyYAML is the authority on YAML validity.
* Gherkin lines are split on LF only; a trailing CR is removed. No other character is treated as
  a line boundary.
* Only string scalars are accepted for front matter, matching the requirement schema.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import yaml

from app.ingestion.errors import IngestionError

SCENARIO_ID_RE = re.compile(r"SCN-\d{3}")
SCENARIO_LINE_RE = re.compile(r"^[ \t]*Scenario:[ \t]*(?P<title>\S.*?)[ \t]*$")
ANNOTATION_RE = re.compile(r"^#\s*cta:artifact\s+(?P<id>(?:CODE|TEST)-\d{3})\s*$")
ANNOTATION_ATTEMPT_RE = re.compile(r"^\s*#\s*cta:artifact\b")
DOC_STRING_DELIMITERS = ('"""', "```")

INDENT = " \t"
LINE_END = " \t\r"


@dataclass(frozen=True)
class ScenarioDeclaration:
    """One tagged scenario found in a feature file."""

    scenario_id: str
    title: str


class _UniqueKeyLoader(yaml.SafeLoader):
    """Safe YAML loader that rejects duplicate mapping keys instead of overwriting them."""


def _construct_mapping(
    loader: _UniqueKeyLoader, node: yaml.MappingNode, deep: bool = False
) -> dict[str, Any]:
    mapping: dict[str, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, str):
            raise IngestionError(f"front matter keys must be strings, got {key!r}")
        if key in mapping:
            raise IngestionError(f"duplicate front matter key {key!r}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


_UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, _construct_mapping)


def parse_front_matter(text: str, *, where: str) -> dict[str, str]:
    """Return the top-level string fields of a leading YAML front matter block.

    Delimiters are recognized only as column-0 ``---`` lines; an indented ``---`` belongs to the
    YAML content. The payload is sliced from the original text, preserving every character, so the
    document PyYAML validates is the document the repository contains.
    """
    first_newline = text.find("\n")
    if first_newline == -1:
        raise IngestionError(
            f"{where}: expected a '---' front matter block at the start of the file"
        )
    if text[:first_newline].rstrip("\r") != "---":
        raise IngestionError(
            f"{where}: expected a '---' front matter block at the start of the file"
        )

    payload_start = first_newline + 1
    position = payload_start
    payload: str | None = None
    while position <= len(text):
        newline = text.find("\n", position)
        line_end = len(text) if newline == -1 else newline
        if text[position:line_end].rstrip("\r") == "---":
            payload = text[payload_start:position]
            break
        if newline == -1:
            break
        position = newline + 1
    if payload is None:
        raise IngestionError(f"{where}: front matter block is not terminated by '---'")

    try:
        parsed = yaml.load(payload, Loader=_UniqueKeyLoader)
    except IngestionError as exc:
        raise IngestionError(f"{where}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise IngestionError(f"{where}: front matter is not valid YAML: {exc}") from exc

    if parsed is None:
        return {}
    if not isinstance(parsed, dict):
        raise IngestionError(f"{where}: front matter must be a YAML mapping")
    fields: dict[str, str] = {}
    for key, value in parsed.items():
        if not isinstance(value, str):
            raise IngestionError(
                f"{where}: front matter key {key!r} must be a string scalar "
                f"(quote values that YAML would read as numbers or booleans)"
            )
        fields[key] = value
    return fields


def parse_scenarios(text: str, *, where: str) -> list[ScenarioDeclaration]:
    """Return the scenarios declared with an ``@SCN-nnn`` tag, in file order.

    Only a ``Scenario:`` line directly after the tag (blank lines, comment lines, and additional
    non-identity tags are allowed) consumes the identity. Any other declaration — ``Rule:``,
    ``Scenario Outline:``, a step, a doc string — leaves the tag dangling and is an error, so an
    identity can never attach to an unrelated scenario. Doc-string contents are data: tags and
    ``Scenario:`` text inside them are ignored.
    """
    found: list[ScenarioDeclaration] = []
    pending: str | None = None
    in_doc_string = False
    doc_delimiter = ""

    for raw_line in text.split("\n"):
        line = raw_line.rstrip("\r")
        stripped = line.strip(INDENT)
        if in_doc_string:
            if stripped == doc_delimiter:
                in_doc_string = False
            continue
        if stripped.startswith(DOC_STRING_DELIMITERS):
            if pending is not None:
                raise IngestionError(
                    f"{where}: tag @{pending} is not followed by a 'Scenario:' line"
                )
            doc_delimiter = '"""' if stripped.startswith('"""') else "```"
            in_doc_string = True
            continue
        if not stripped or stripped.startswith("#"):
            continue
        if line.lstrip(INDENT).startswith("@"):
            identities = _identity_tokens(stripped, where=where)
            if len(identities) > 1:
                raise IngestionError(
                    f"{where}: a scenario tag line carries more than one identity tag: "
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
            continue
        raise IngestionError(f"{where}: tag @{pending} is not followed by a 'Scenario:' line")

    if in_doc_string:
        raise IngestionError(f"{where}: doc string opened with {doc_delimiter!r} is not terminated")
    if pending is not None:
        raise IngestionError(f"{where}: tag @{pending} is not followed by a 'Scenario:' line")
    return found


def parse_annotation(text: str, *, where: str) -> str | None:
    """Return the first-line ``# cta:artifact CODE-nnn|TEST-nnn`` identity, if any.

    The annotation must be the first line. A declaration anywhere else, a malformed declaration
    using the reserved marker, or a second declaration raises: a source file never silently
    changes identity because a comment moved.
    """
    lines = text.split("\n")
    first = lines[0].rstrip("\r") if lines else ""
    match = ANNOTATION_RE.match(first)
    if match:
        artifact_id = match.group("id")
        for line in lines[1:]:
            if ANNOTATION_ATTEMPT_RE.match(line):
                raise IngestionError(
                    f"{where}: a file may declare only one artifact annotation; "
                    f"another appears at {line.strip()!r}"
                )
        return artifact_id
    for line in lines:
        if ANNOTATION_ATTEMPT_RE.match(line):
            raise IngestionError(
                f"{where}: an artifact annotation must be the first line and use "
                f"'# cta:artifact CODE-nnn|TEST-nnn': {line.strip()!r}"
            )
    return None


def _identity_tokens(line: str, *, where: str) -> list[str]:
    """Valid ``@SCN-nnn`` identities on a tag line; malformed reserved tokens raise."""
    identities: list[str] = []
    for token in re.split(r"[ \t]+", line.strip(INDENT)):
        if not token.startswith("@"):
            continue
        name = token[1:]
        if name.startswith("SCN"):
            if not SCENARIO_ID_RE.fullmatch(name):
                raise IngestionError(
                    f"{where}: malformed scenario identity {token!r}; expected @SCN-nnn"
                )
            identities.append(name)
    return identities
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
from app.ingestion.parsers import parse_annotation, parse_front_matter, parse_scenarios
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
    repository: GitRepository, revision: str | None, *, repository_name: str
) -> list[Artifact]:
    """Every declared artifact at one immutable commit, in tree order.

    The revision expression is resolved to a full commit SHA once; every read and every
    ``Artifact.revision`` uses that SHA, so a symbolic reference moving during the scan cannot
    mix revisions and abbreviated inputs cannot leak into provenance.

    Raises :class:`IngestionError` for unreadable content, malformed declarations, or duplicate
    artifact identities. A caller never receives a silently partial inventory.
    """
    commit = repository.resolve(revision)
    artifacts: list[Artifact] = []
    declared_at: dict[str, str] = {}

    for path in repository.list_paths(commit):
        blob = repository.read_blob(commit, path)
        if path.startswith(REQUIREMENTS_PREFIX) and path.endswith(".md"):
            found = [
                _requirement(blob, path=path, revision=commit, repository_name=repository_name)
            ]
        elif path.startswith(FEATURES_PREFIX) and path.endswith(".feature"):
            found = _scenarios(blob, path=path, revision=commit, repository_name=repository_name)
        elif path.endswith(".py"):
            artifact = _python_artifact(
                blob, path=path, revision=commit, repository_name=repository_name
            )
            found = [] if artifact is None else [artifact]
        else:
            continue

        for artifact in found:
            previous = declared_at.get(artifact.artifact_id)
            if previous is not None:
                raise IngestionError(
                    f"{commit}: duplicate artifact id {artifact.artifact_id!r}: declared by "
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


def _python_artifact(
    blob: bytes, *, path: str, revision: str, repository_name: str
) -> Artifact | None:
    where = f"{revision}:{path}"
    artifact_id = parse_annotation(_decode(blob, where=where), where=where)
    if artifact_id is None:
        return None
    return _artifact(
        artifact_id=artifact_id,
        artifact_type=(
            ArtifactType.SOURCE if artifact_id.startswith("CODE-") else ArtifactType.TEST
        ),
        title=path,
        locator=path,
        blob=blob,
        revision=revision,
        repository_name=repository_name,
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

`backend/tests/test_ingestion_parsers.py`:
```python
"""Unit tests for the pure artifact-declaration parsers (DT-01)."""

from __future__ import annotations

import pytest

from app.ingestion.errors import IngestionError
from app.ingestion.parsers import parse_annotation, parse_front_matter, parse_scenarios

WHERE = "test:requirements/REQ-900.md"
SOURCE_WHERE = "test:src/accounts.py"


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
    with pytest.raises(IngestionError, match="not valid YAML"):
        parse_front_matter("---\nid: REQ-900\nnot a pair\n---\n", where=WHERE)


def test_front_matter_rejects_a_duplicate_key() -> None:
    with pytest.raises(IngestionError, match="duplicate front matter key"):
        parse_front_matter("---\nid: REQ-900\nid: REQ-901\n---\n", where=WHERE)


def test_front_matter_parses_quoted_values_and_comments() -> None:
    text = '---\nid: "REQ-900"\ntitle: "A quoted title"\nstatus: superseded # historical\n---\n'
    assert parse_front_matter(text, where=WHERE) == {
        "id": "REQ-900",
        "title": "A quoted title",
        "status": "superseded",
    }


def test_front_matter_rejects_invalid_yaml() -> None:
    with pytest.raises(IngestionError, match="not valid YAML"):
        parse_front_matter('---\nid: REQ-900\ntitle: "unterminated\n---\n', where=WHERE)


def test_front_matter_rejects_non_string_scalars() -> None:
    with pytest.raises(IngestionError, match="must be a string scalar"):
        parse_front_matter("---\nid: REQ-900\nstatus: yes\n---\n", where=WHERE)


def test_front_matter_accepts_crlf_and_a_closing_delimiter_at_eof() -> None:
    crlf = "---\r\nid: REQ-900\r\ntitle: A title\r\n---\r\n"
    assert parse_front_matter(crlf, where=WHERE) == {"id": "REQ-900", "title": "A title"}
    at_eof = "---\nid: REQ-900\ntitle: A title\n---"
    assert parse_front_matter(at_eof, where=WHERE) == {"id": "REQ-900", "title": "A title"}


def test_indented_separator_inside_a_block_scalar_is_content() -> None:
    """R5: a closing delimiter belongs to column 0; indented `---` is scalar content."""
    text = (
        "---\n"
        "id: REQ-900\n"
        "title: |-\n"
        "  Before delimiter\n"
        "  ---\n"
        "  After delimiter\n"
        "status: superseded\n"
        "---\n"
    )
    assert parse_front_matter(text, where=WHERE) == {
        "id": "REQ-900",
        "title": "Before delimiter\n---\nAfter delimiter",
        "status": "superseded",
    }


def test_indented_separator_inside_a_quoted_scalar_is_content() -> None:
    text = '---\nid: REQ-900\ntitle: "Before\n  ---\n  After"\n---\n'
    # Flow scalars fold line breaks to spaces; the indented separator is content, not a boundary.
    assert parse_front_matter(text, where=WHERE)["title"] == "Before --- After"


def test_malformed_yaml_after_an_indented_separator_is_rejected() -> None:
    text = '---\nid: REQ-900\ntitle: |-\n  Before\n  ---\n  After\nbroken: "unterminated\n---\n'
    with pytest.raises(IngestionError, match="not valid YAML"):
        parse_front_matter(text, where=WHERE)


def test_an_indented_opening_delimiter_is_rejected() -> None:
    with pytest.raises(IngestionError, match="front matter block at the start"):
        parse_front_matter("  ---\nid: REQ-900\n---\n", where=WHERE)


def test_control_characters_inside_yaml_are_rejected() -> None:
    """R6: the loader receives the original substring; PyYAML rejects control characters."""
    text = "---\nid: REQ-900\ntitle: |-\n  Before\x0b  After\nstatus: superseded\n---\n"
    with pytest.raises(IngestionError, match="not valid YAML"):
        parse_front_matter(text, where=WHERE)
    with pytest.raises(IngestionError, match="not valid YAML"):
        parse_front_matter(text.replace("\x0b", "\x0c"), where=WHERE)


def test_unicode_line_separator_in_a_quoted_scalar_is_preserved() -> None:
    """R6: U+2028 is YAML content; it must not be split and rejoined as an ASCII newline."""
    text = '---\nid: REQ-900\ntitle: "Before\u2028  After"\n---\n'
    assert parse_front_matter(text, where=WHERE)["title"] == "Before\u2028After"


# ------------------------------------------------------------------------ source/test annotations


def test_annotation_declares_a_source_or_test_identity() -> None:
    assert (
        parse_annotation("# cta:artifact CODE-001\nprint('x')\n", where=SOURCE_WHERE) == "CODE-001"
    )
    assert parse_annotation("# cta:artifact TEST-002\n", where=SOURCE_WHERE) == "TEST-002"


def test_no_annotation_returns_none() -> None:
    text = '"""Documents the cta:artifact convention without declaring one."""\nVALUE = 1\n'
    assert parse_annotation(text, where=SOURCE_WHERE) is None


def test_annotation_after_the_first_line_is_rejected() -> None:
    with pytest.raises(IngestionError, match="must be the first line"):
        parse_annotation('"""doc"""\n# cta:artifact CODE-001\n', where=SOURCE_WHERE)


def test_a_malformed_first_line_annotation_is_rejected() -> None:
    with pytest.raises(IngestionError, match="must be the first line"):
        parse_annotation("# cta:artifact CODE-1\n", where=SOURCE_WHERE)


def test_a_second_annotation_is_rejected() -> None:
    with pytest.raises(IngestionError, match="only one artifact annotation"):
        parse_annotation("# cta:artifact CODE-001\n# cta:artifact TEST-002\n", where=SOURCE_WHERE)


def test_a_requirement_prefix_is_not_a_source_or_test_annotation() -> None:
    with pytest.raises(IngestionError, match="must be the first line"):
        parse_annotation("# cta:artifact REQ-001\n", where=SOURCE_WHERE)


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


def test_tags_may_be_split_across_lines() -> None:
    text = "Feature: Demo\n\n  @SCN-910\n  @smoke\n  Scenario: Still identified\n"
    assert [item.scenario_id for item in parse_scenarios(text, where=WHERE)] == ["SCN-910"]


def test_tag_before_a_rule_does_not_capture_a_nested_scenario() -> None:
    text = "Feature: Demo\n\n  @SCN-911\n  Rule: Grouping\n    Scenario: Not the tagged scenario\n"
    with pytest.raises(IngestionError, match="tag @SCN-911 is not followed"):
        parse_scenarios(text, where=WHERE)


def test_tag_before_a_scenario_outline_is_rejected_as_unsupported() -> None:
    text = "Feature: Demo\n\n  @SCN-912\n  Scenario Outline: Unsupported form\n"
    with pytest.raises(IngestionError, match="tag @SCN-912 is not followed"):
        parse_scenarios(text, where=WHERE)


def test_doc_string_contents_are_data() -> None:
    text = (
        "Feature: Demo\n\n"
        "  @SCN-913\n"
        "  Scenario: Real behaviour\n"
        "    Given a payload\n"
        '      """\n'
        "      @SCN-999\n"
        "      Scenario: not real\n"
        '      """\n'
    )
    assert [item.scenario_id for item in parse_scenarios(text, where=WHERE)] == ["SCN-913"]


def test_an_unterminated_doc_string_is_rejected() -> None:
    text = (
        "Feature: Demo\n\n"
        "  @SCN-914\n"
        "  Scenario: Real behaviour\n"
        "    Given a payload\n"
        '      """\n'
        "      Scenario: still data\n"
    )
    with pytest.raises(IngestionError, match="doc string .* is not terminated"):
        parse_scenarios(text, where=WHERE)


@pytest.mark.parametrize("opening", ['""""""', "``````"])
def test_a_repeated_delimiter_line_opens_an_unterminated_doc_string(opening: str) -> None:
    """R2 round-2: an opening line is never also its own terminator (Gherkin tokenizer)."""
    text = (
        "Feature: Demo\n\n"
        "  @SCN-920\n"
        "  Scenario: Real behaviour\n"
        "    Given a payload\n"
        f"      {opening}\n"
        "      @SCN-999\n"
        "      Scenario: not real\n"
    )
    with pytest.raises(IngestionError, match="doc string .* is not terminated"):
        parse_scenarios(text, where=WHERE)


def test_a_doc_string_with_a_media_type_opens_and_closes() -> None:
    text = (
        "Feature: Demo\n\n"
        "  @SCN-921\n"
        "  Scenario: Real behaviour\n"
        "    Given a payload\n"
        '      """json\n'
        '      {"ignored": true}\n'
        '      """\n'
    )
    assert [item.scenario_id for item in parse_scenarios(text, where=WHERE)] == ["SCN-921"]


def test_fenced_doc_string_contents_are_data() -> None:
    text = (
        "Feature: Demo\n\n"
        "  @SCN-922\n"
        "  Scenario: Real behaviour\n"
        "    Given a payload\n"
        "      ```text\n"
        "      @SCN-999\n"
        "      Scenario: not real\n"
        "      ```\n"
    )
    assert [item.scenario_id for item in parse_scenarios(text, where=WHERE)] == ["SCN-922"]


def test_a_malformed_identity_token_is_rejected() -> None:
    text = "Feature: Demo\n\n  @SCN-99\n  Scenario: Broken identity\n"
    with pytest.raises(IngestionError, match="@SCN-99"):
        parse_scenarios(text, where=WHERE)


def test_a_malformed_identity_beside_a_valid_one_is_rejected() -> None:
    text = "Feature: Demo\n\n  @SCN-99 @SCN-915\n  Scenario: Broken identity\n"
    with pytest.raises(IngestionError, match="@SCN-99"):
        parse_scenarios(text, where=WHERE)
```

`backend/tests/test_ingestion_artifacts.py`:
```python
"""DT-01 acceptance: requirements and Gherkin scenarios become stable artifacts.

Expectations come from the committed snapshot (shared fixture input) and from independently
computed Git blob hashes, never from the scanner's own output.
"""

from __future__ import annotations

import hashlib
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

    # Unannotated files are not artifacts. (Annotated src/tests files are added by DT-02.)
    locators = {item.locator for item in artifacts}
    assert "src/__init__.py" not in locators
    assert "conftest.py" not in locators


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
            if item.artifact_type in KEPT_TYPES
        }
        assert actual == expected, entry.baseline


# ------------------------------------------------------------------- SCN-507 revision pinning


def test_tag_and_sha_ingestion_return_identical_artifacts(built_fixture) -> None:
    repository = GitRepository(root=built_fixture.repo)
    sha = built_fixture.tag("baseline-a")
    by_tag = scan_artifacts(repository, "baseline-a", repository_name="banking-demo")
    by_sha = scan_artifacts(repository, sha, repository_name="banking-demo")
    assert by_tag == by_sha
    assert {artifact.revision for artifact in by_tag} == {sha}


def test_abbreviated_sha_is_pinned_to_the_full_commit(built_fixture) -> None:
    sha = built_fixture.tag("baseline-a")
    artifacts = scan_artifacts(
        GitRepository(root=built_fixture.repo), sha[:9], repository_name="banking-demo"
    )
    assert artifacts
    assert {artifact.revision for artifact in artifacts} == {sha}


def test_every_read_uses_the_resolved_commit(built_fixture) -> None:
    sha = built_fixture.tag("baseline-a")
    inner = GitRepository(root=built_fixture.repo)
    listed: list[str] = []

    class RecordingRepository:
        def resolve(self, revision: str | None) -> str:
            return inner.resolve(revision)

        def list_paths(self, commit: str) -> list[str]:
            listed.append(commit)
            assert commit == sha
            return inner.list_paths(commit)

        def read_blob(self, commit: str, path: str) -> bytes:
            assert commit == sha
            return inner.read_blob(commit, path)

    scan_artifacts(RecordingRepository(), "baseline-a", repository_name="banking-demo")
    assert listed == [sha]


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


def test_quoted_front_matter_values_are_parsed(tmp_path: Path) -> None:
    repository = make_repo(
        tmp_path,
        {
            "requirements/one.md": (
                "---\n"
                'id: "REQ-900"\n'
                'title: "A quoted title"\n'
                "status: superseded # historical\n"
                "---\n"
            )
        },
    )
    [artifact] = scan_artifacts(repository, repository.resolve(), repository_name="demo")
    assert artifact.artifact_id == "REQ-900"
    assert artifact.title == "A quoted title"
    assert artifact.metadata == {"status": "superseded"}


def test_invalid_yaml_is_rejected_by_the_scanner(tmp_path: Path) -> None:
    repository = make_repo(
        tmp_path,
        {"requirements/broken.md": '---\nid: REQ-900\ntitle: "unterminated\n---\n'},
    )
    with pytest.raises(IngestionError, match="not valid YAML"):
        scan_artifacts(repository, repository.resolve(), repository_name="demo")


def test_block_scalar_with_indented_separator_preserves_title_and_status(tmp_path: Path) -> None:
    repository = make_repo(
        tmp_path,
        {
            "requirements/one.md": (
                "---\n"
                "id: REQ-900\n"
                "title: |-\n"
                "  Before delimiter\n"
                "  ---\n"
                "  After delimiter\n"
                "status: superseded\n"
                "---\n"
            )
        },
    )
    [artifact] = scan_artifacts(repository, repository.resolve(), repository_name="demo")
    assert artifact.title == "Before delimiter\n---\nAfter delimiter"
    assert artifact.metadata == {"status": "superseded"}


def test_control_character_in_front_matter_is_rejected_by_the_scanner(tmp_path: Path) -> None:
    repository = make_repo(
        tmp_path,
        {"requirements/bad.md": ("---\nid: REQ-900\ntitle: |-\n  Before\x0b  After\n---\n")},
    )
    with pytest.raises(IngestionError, match="not valid YAML"):
        scan_artifacts(repository, repository.resolve(), repository_name="demo")


def test_unicode_line_separator_title_is_preserved_by_the_scanner(tmp_path: Path) -> None:
    repository = make_repo(
        tmp_path,
        {"requirements/one.md": '---\nid: REQ-900\ntitle: "Before\u2028  After"\n---\n'},
    )
    [artifact] = scan_artifacts(repository, repository.resolve(), repository_name="demo")
    assert artifact.title == "Before\u2028After"


# ------------------------------------------------------- SCN-521 … SCN-527 source/test artifacts


def test_source_annotation_is_parsed_at_the_requested_revision(
    built_fixture, snapshot: FixtureSnapshot
) -> None:
    repository = GitRepository(root=built_fixture.repo)
    baseline_b = built_fixture.tag("baseline-b")
    baseline_a = built_fixture.tag("baseline-a")
    at_b = {
        item.artifact_id: item
        for item in scan_artifacts(repository, baseline_b, repository_name="banking-demo")
    }
    at_a = {
        item.artifact_id: item
        for item in scan_artifacts(repository, baseline_a, repository_name="banking-demo")
    }

    artifact = at_b["CODE-001"]
    expected = next(
        item
        for entry in snapshot.baselines
        if entry.baseline == "baseline-b"
        for item in entry.artifacts
        if item.artifact_id == "CODE-001"
    )
    assert artifact == expected
    assert artifact.artifact_type is ArtifactType.SOURCE
    assert artifact.locator == "src/accounts.py"
    assert artifact.revision == baseline_b
    assert artifact.content_hash != at_a["CODE-001"].content_hash
    assert artifact.content_hash == built_fixture.blob_sha256(baseline_b, "src/accounts.py")


def test_test_annotation_is_parsed(built_fixture, snapshot: FixtureSnapshot) -> None:
    revision = built_fixture.tag("baseline-a")
    artifacts = {
        item.artifact_id: item
        for item in scan_artifacts(
            GitRepository(root=built_fixture.repo), revision, repository_name="banking-demo"
        )
    }
    artifact = artifacts["TEST-001"]
    expected = next(
        item
        for entry in snapshot.baselines
        if entry.baseline == "baseline-a"
        for item in entry.artifacts
        if item.artifact_id == "TEST-001"
    )
    assert artifact == expected
    assert artifact.artifact_type is ArtifactType.TEST
    assert artifact.locator == "tests/test_accounts.py"
    assert artifact.content_hash == built_fixture.blob_sha256(revision, "tests/test_accounts.py")


def test_files_without_annotations_are_not_artifacts(built_fixture) -> None:
    locators = {
        item.locator
        for item in scan_artifacts(
            GitRepository(root=built_fixture.repo),
            built_fixture.tag("baseline-b"),
            repository_name="banking-demo",
        )
    }
    assert "src/__init__.py" not in locators
    assert "conftest.py" not in locators
    assert locators >= {"src/accounts.py", "src/transfers.py", "tests/test_accounts.py"}


def test_annotation_after_the_first_line_is_rejected(tmp_path: Path) -> None:
    repository = make_repo(
        tmp_path,
        {"src/accounts.py": ('"""Module docstring."""\n# cta:artifact CODE-001\n\nVALUE = 1\n')},
    )
    with pytest.raises(IngestionError, match="src/accounts.py"):
        scan_artifacts(repository, repository.resolve(), repository_name="demo")


def test_two_annotations_in_one_file_are_rejected(tmp_path: Path) -> None:
    repository = make_repo(
        tmp_path,
        {
            "src/accounts.py": (
                '# cta:artifact CODE-001\n"""Module docstring."""\n# cta:artifact TEST-001\n'
            )
        },
    )
    with pytest.raises(IngestionError, match="only one artifact annotation"):
        scan_artifacts(repository, repository.resolve(), repository_name="demo")


def test_malformed_annotation_is_rejected(tmp_path: Path) -> None:
    repository = make_repo(tmp_path, {"src/accounts.py": "# cta:artifact CODE-1\nVALUE = 1\n"})
    with pytest.raises(IngestionError, match="must be the first line"):
        scan_artifacts(repository, repository.resolve(), repository_name="demo")


def test_content_hash_comes_from_the_committed_blob(tmp_path: Path) -> None:
    repository = make_repo(tmp_path, {"src/accounts.py": "# cta:artifact CODE-900\nVALUE = 1\n"})
    commit = repository.resolve()
    before = scan_artifacts(repository, commit, repository_name="demo")
    (repository.root / "src/accounts.py").write_text(
        "# cta:artifact CODE-900\nVALUE = 2\n", encoding="utf-8"
    )
    after = scan_artifacts(repository, commit, repository_name="demo")
    committed = b"# cta:artifact CODE-900\nVALUE = 1\n"
    assert before == after
    assert after[0].content_hash == f"sha256:{hashlib.sha256(committed).hexdigest()}"


def test_every_artifact_matches_the_committed_snapshot(
    built_fixture, snapshot: FixtureSnapshot
) -> None:
    repository = GitRepository(root=built_fixture.repo)
    for entry in snapshot.baselines:
        expected = {item.artifact_id: item for item in entry.artifacts}
        actual = {
            item.artifact_id: item
            for item in scan_artifacts(repository, entry.commit, repository_name="banking-demo")
        }
        assert actual == expected, entry.baseline
```

`docs/stories/DT-02.md`:
```markdown
# DT-02 — Source and test artifacts tied to path and Git revision

**Milestone:** M1 — AI-free vertical slice · **Owner:** B · **Implementer:** OMP · **Status:**
refined; implementation in progress.

| Record | Value |
| --- | --- |
| Roadmap / feature | F-02 Ingestion · roadmap §6 DT-02 |
| GitHub story | [#21](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/21) — verified OPEN 2026-11-13T02:01:06Z (`gh issue view`), milestone "M1 — AI-free vertical slice" |
| Parent feature issue | [#9](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/9) |
| Canonical criteria | [DT-02.feature](DT-02.feature), sha256 `08c0e96d371724a9d640cefdc1e07d060e7c72cbfe141877022d662489d90e8a` |
| Dependencies | DT-01 (#20) merged at `26a25d0b739994631e098e6eae5307a47325a0ba`; M0 approved |
| Upstream obligation | Roadmap §4 artifact contract, §5 fixture discipline; project-definition REQ-103 (draft, not approved) |

## User outcome

An engineer can trust that `CODE-*` and `TEST-*` artifacts describe the committed file at the
requested revision, so later change detection compares hashes that correspond to repository
content rather than to a developer's working tree.

## Scope

* Parse a first-line `# cta:artifact CODE-nnn` / `TEST-nnn` annotation into a source or test
  artifact.
* Extend the revision scan to Python files; unannotated files remain non-artifacts.
* Reject an annotation that is not on the first line, a malformed annotation using the reserved
  marker, and a file declaring more than one identity.
* Prove content hashes come from the committed blob even when the working tree changes.
* Make `tools/fixturectl.py` reuse the shared scanner, deleting the duplicate parser. Generated
  fixture bytes must remain identical; `fixturectl verify` is the guard.

## Non-goals

Links, evidence, thread assembly, store cutover, API changes (DT-03/DT-04); non-Python source
languages; sub-file granularity; accepting annotations anywhere but the first line; a Gherkin
runner.

## Preservation boundaries

Fixture inputs, hand-labeled oracle files, generated responses, and contracts are unchanged. DT-01
behavior (requirements/scenarios, YAML, revision pinning) is preserved. The generator's output must
stay byte-identical, so no fixture SHA changes and no regeneration is required.

## Design impact

`parsers.py` gains `parse_annotation` (first-line rule, reserved-marker malformed detection, at most
one identity). `scan.py` gains the `.py` branch and artifact-type inference. `tools/fixturectl.py`
imports `app.ingestion.scan_artifacts` and `app.ingestion.GitRepository`, drops its duplicate
front-matter/scenario/scanner functions, and maps `IngestionError` into its CLI error path. No
schema or dependency change.

Assumptions:

1. Source and test artifacts are Python files carrying the annotation as their first line.
2. Identity prefixes (`CODE-`/`TEST-`) determine the artifact type; a mismatch is an error.
3. Artifact granularity is file level; the content hash is the whole blob.
4. Identity is path-stable (ADR 0006 #8).

## Refinement disposition

Derived from the owner-authored issue intake and roadmap §6; failure and boundary scenarios were
added without weakening the intake. No separate human refinement sign-off is recorded, and the
draft project definition is not treated as an approved requirements baseline.

## Verification mapping

| Scenario | Observable check | Pytest selector |
| --- | --- | --- |
| SCN-521 | Ingests `baseline-b`; compares `CODE-001` to the snapshot and shows the hash changed from `baseline-a` | `backend/tests/test_ingestion_artifacts.py::test_source_annotation_is_parsed_at_the_requested_revision` |
| SCN-522 | Asserts no artifact locator is `src/__init__.py`, `conftest.py`, or another unannotated file | `backend/tests/test_ingestion_artifacts.py::test_files_without_annotations_are_not_artifacts` |
| SCN-523 | Compares `TEST-001` to the snapshot and to an independently read blob hash | `backend/tests/test_ingestion_artifacts.py::test_test_annotation_is_parsed` |
| SCN-524 | Temp repository with the annotation on line 2 raises naming the file | `backend/tests/test_ingestion_artifacts.py::test_annotation_after_the_first_line_is_rejected` |
| SCN-525 | Temp repository declaring `CODE-001` and `TEST-001` in one file raises | `backend/tests/test_ingestion_artifacts.py::test_two_annotations_in_one_file_are_rejected` |
| SCN-526 | Commit, modify the working tree, re-ingest the same commit; hash and revision are unchanged | `backend/tests/test_ingestion_artifacts.py::test_content_hash_comes_from_the_committed_blob` |
| SCN-527 | Every artifact at both baselines equals the committed snapshot exactly | `backend/tests/test_ingestion_artifacts.py::test_every_artifact_matches_the_committed_snapshot` |
| DoD generator reuse | `fixturectl verify` produces zero drift after the generator switches to the shared scanner; generated bytes are unchanged | `backend/tests/test_fixture_drift.py` (plus inspection of the generated diff) |

A mapping row is not an execution result; the run record in
`docs/reports/omp-dt-02-artifacts/IMPLEMENTATION.md` carries the actual invocation and result.

## Verification plan

```bash
uv run --project backend pytest backend/tests/test_ingestion_artifacts.py -q
uv run --project backend pytest backend/tests -q
uv run --project backend python tools/fixturectl.py verify
uv run --project backend ruff check .
uv run --project backend ruff format --check .
```

Limitations: Python-only annotations; links and evidence still unparsed; the API still serves the
M0 fixture read model until DT-04.
```

`docs/reports/omp-dt-02-artifacts/IMPLEMENTATION.md`:
```markdown
# DT-02 implementation record — source and test artifacts tied to path and Git revision

| Field | Value |
| --- | --- |
| Story | DT-02 — [#21](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/21), verified OPEN 2026-11-13T02:01:06Z (`gh issue view`, milestone "M1 — AI-free vertical slice") |
| Canonical criteria | [DT-02.feature](../../stories/DT-02.feature), sha256 `08c0e96d371724a9d640cefdc1e07d060e7c72cbfe141877022d662489d90e8a` |
| Brief / verification map | [DT-02.md](../../stories/DT-02.md) |
| Branch / base | `feat/21-dt-02-source-test-artifacts` from `26a25d0b739994631e098e6eae5307a47325a0ba` (DT-01 merge) |
| Contract version | `SCHEMA_VERSION = 0.1.0`, `PACKAGE_VERSION = 0.1.0` (no contract change) |
| Submission | **1 of 7** |
| Snapshot captured | 2026-11-13T02:08Z |

## What changed

| Path | sha256 | Purpose |
| --- | --- | --- |
| `backend/app/ingestion/parsers.py` | `4cff0a3a49c139d4b96f5e5e272714988a181fb8340f117d98a693a5002e26b6` | Adds first-line annotation parsing (one identity, reserved-marker rejection) |
| `backend/app/ingestion/scan.py` | `2a602ee3668bd1560e42aa8870c6a1875b3977a082d449109892852c73e0a613` | Adds the `.py` branch and source/test type inference |
| `tools/fixturectl.py` | `43483704398312b94ab55ff45f0e98ec496fde12ef4fc6ed9a730dd20b99b7c2` | Deletes the duplicate scanner and delegates to `app.ingestion` |
| `backend/tests/test_ingestion_parsers.py` | `d3f6ac078f68b1c7944d16b389df87bcd97afcdfb39d7943f1af22a3ca134b24` | Annotation parser tests (6 new) |
| `backend/tests/test_ingestion_artifacts.py` | `5ca164098ccedbabf1691211220249323213e8d1f5257a90d3dfcfb6fed5d188` | DT-02 acceptance tests (7 new) and the DT-01 subset comparison updated for the wider inventory |
| `docs/stories/DT-02.feature` | `08c0e96d371724a9d640cefdc1e07d060e7c72cbfe141877022d662489d90e8a` | Canonical criteria (SCN-521…527) |
| `docs/stories/DT-02.md` | `8d071a4f6a559cc68ca2e362df66a527412934f5a688522e3c3f3a23710030c9` | Brief, assumptions, verification map |
| `docs/architecture.md` | `a00a510fc5fd37c3b913656434d70891e17d4ad5d3f123ec010b79eccf1c7485` | Ingestion status includes source/test |
| `docs/STATUS.md` | `0574dfde81c148af3ac02fd5e732337332fd013159e198eed0d55149e1e05cc3` | DT-01 landed; DT-02 active |

Generated fixtures, oracle labels, and contracts are unchanged. The generator now uses the shared
scanner; `fixturectl verify` confirms the committed generated files are still byte-identical.

## Acceptance results

| Criterion | Check | Result |
| --- | --- | --- |
| SCN-521 source artifact at the requested revision | `tests/test_ingestion_artifacts.py::test_source_annotation_is_parsed_at_the_requested_revision` | PASS |
| SCN-522 files without annotations | `::test_files_without_annotations_are_not_artifacts` | PASS |
| SCN-523 test artifact + blob hash | `::test_test_annotation_is_parsed` | PASS |
| SCN-524 annotation not on the first line | `::test_annotation_after_the_first_line_is_rejected` | PASS |
| SCN-525 two identities in one file | `::test_two_annotations_in_one_file_are_rejected` | PASS |
| SCN-526 committed blob, not working tree | `::test_content_hash_comes_from_the_committed_blob` | PASS |
| SCN-527 full snapshot equality | `::test_every_artifact_matches_the_committed_snapshot` (all 10 artifacts, both baselines) | PASS |
| DoD generator reuse | `fixturectl.py verify` passes with the generator delegating to `app.ingestion`; no generated bytes changed | PASS |
| Parser malformed inputs | `tests/test_ingestion_parsers.py` annotation cases (first-line rule, malformed, duplicate, prose ignored) | PASS |

Axis coverage: success (521/523), failure (524/525/malformed), boundary (522, 526, 527).

## Commands and outcomes (as captured)

```text
captured_start=2026-11-13T02:07:14Z
pytest backend/tests -q                          exit 0  197 passed, 1 warning in 5.03s
fixturectl.py verify                             exit 0  reproducible and committed files current
ruff check .                                     exit 0  All checks passed
ruff format --check .                            exit 0  all files formatted
git diff --check                                 exit 0
captured_end=2026-11-13T02:07:20Z

network denial at 2026-11-13T02:07:26Z: `unshare -rn backend/.venv/bin/python -m pytest
backend/tests -q` → exit 0, 197 passed.
```

`tests/test_ingestion_parsers.py` collects 38 tests. Raw logs are in the external run directory
`…/m1-roadmap-20261112/dt-02/`.

## Self-review

* **Revision-aware:** source/test artifacts use the same resolved commit and blob hashes as DT-01;
  the working-tree probe shows a modified file is not reflected when re-ingesting the commit.
* **Loud failures:** an annotation anywhere but the first line, a malformed declaration, and a
  second identity all raise `IngestionError` naming the file.
* **Generator equivalence:** the duplicate scanner is deleted; `verify` proves the committed
  snapshot/responses are still exactly what the generator produces. This is the strongest available
  check that the shared parser did not change fixture identity.
* **No contract change:** no schema bump, no API change, no generated-file edit.
* **Offline:** parsing plus the local Git CLI; the network-denied suite passes.

Known limits: Python files only; the annotation is a first-line comment; links/evidence/threads and
the API cutover remain DT-03/DT-04.

## Independent review

**Submission 1 pending.** The verdict will be recorded in `docs/reviews/DT-02-review.md`.
Implementation acceptance is not claimed before that verdict.
```

### Unchanged DT-01 files used by this slice (hash-pinned pointers)

```text
c87a149c478ddbcd7322ffbdda723362bda18729da264048be5c3eaa9e58cdbf  backend/app/ingestion/__init__.py
b33cd36ad1a42f9f18720cf11f5d42aea424646ba8ff5b286587995ab2799a1d  backend/app/ingestion/errors.py
eaaec286ca5dddff28914b6e3a431338a4082b17edd703548ec9fda811d6c005  backend/app/ingestion/repository.py
```

## 4. Implementation context

* `scan_artifacts` resolves the revision once and now handles `.py` files in addition to
  requirements/features. Artifact type is inferred from the identity prefix (`CODE-` → source,
  `TEST-` → test); the artifact title is the path, matching the generator.
* `parse_annotation` requires the declaration to be the first line, rejects a malformed reserved
  marker and a second declaration, and ignores prose that merely mentions `cta:artifact`.
* `tools/fixturectl.py` now constructs `GitRepository` and calls the shared scanner for snapshots.
  Its duplicate parser/scanner code is deleted. `IngestionError` is mapped to the CLI error path.
  `fixturectl verify` proves the generated snapshot/responses are unchanged byte-for-byte.
* Targeted reads: `backend/app/domain/models.py` (Artifact), `docs/domain-contracts.md`
  (identity conventions), `backend/tests/conftest.py` (`built_fixture`), `tools/fixturectl.py`
  (remaining generator responsibilities: overlays, links, evidence, threads).

## 5. Evidence

| Criterion | Check (pytest selector) | Result |
| --- | --- | --- |
| SCN-521 | `tests/test_ingestion_artifacts.py::test_source_annotation_is_parsed_at_the_requested_revision` | PASS |
| SCN-522 | `::test_files_without_annotations_are_not_artifacts` | PASS |
| SCN-523 | `::test_test_annotation_is_parsed` | PASS |
| SCN-524 | `::test_annotation_after_the_first_line_is_rejected` | PASS |
| SCN-525 | `::test_two_annotations_in_one_file_are_rejected` | PASS |
| SCN-526 | `::test_content_hash_comes_from_the_committed_blob` | PASS |
| SCN-527 | `::test_every_artifact_matches_the_committed_snapshot` | PASS |
| Generator reuse | `tools/fixturectl.py verify` exit 0; committed generated files byte-identical | PASS |
| Parser cases | `tests/test_ingestion_parsers.py` annotation tests | PASS |

Actual invocations and exits, captured 2026-11-13T02:07:14Z–02:07:26Z:

```text
uv run --project backend pytest backend/tests -q exit 0  197 passed, 1 warning in 5.03s
uv run --project backend python tools/fixturectl.py verify  exit 0  reproducible and current
uv run --project backend ruff check .            exit 0  All checks passed
uv run --project backend ruff format --check .   exit 0  all files formatted
git diff --check                                 exit 0
unshare -rn backend/.venv/bin/python -m pytest backend/tests -q  exit 0  197 passed
```

NOT RUN: API/HTTP (no route changed), frontend, non-Python source languages. Full logs are in the
external run directory; `IMPLEMENTATION.md` records the same exits and timestamps.

## 6. File-integrity requirement

The manifest in section 3 is the reviewed snapshot. If any manifest hash changed, the snapshot is
not the one reviewed. Do not edit files, install dependencies, regenerate fixtures, or commit.

## Reviewer instructions (mandatory)

You are the independent CTA implementation reviewer using GPT-6.1 Sol xhigh. Decide whether this exact snapshot satisfies the supplied story, every applicable Gherkin criterion, and repository invariants. Treat OMP's summaries and test results as claims to check against the supplied artifacts and targeted source inspection. Check proposal/accepted/evidence separation, real port compatibility, revision/content-hash semantics, honest errors/501s, independent oracle expectations, offline defaults, and generated-file discipline where relevant. Do not demand implementation of a later milestone. Do not edit files, implement repairs, regenerate fixtures, commit, or delegate. Ask OMP for missing runtime evidence; distinguish observed defects from hypotheses and unavailable checks. Return an AC-by-AC PASS, FAIL, or NOT VERIFIED assessment and actionable findings with stable IDs, severity, blocking status, AC/invariant, path/line, expected/actual behavior, and smallest correction/recheck. Keep optional suggestions and unrelated pre-existing defects separate. Return exactly one verdict: APPROVE, REQUEST_CHANGES, or NEEDS_INPUT. APPROVE requires every applicable criterion/check to be satisfied, no unresolved blocker, and the exact snapshot identified. In later rounds verify prior dispositions and regressions while retaining the complete acceptance assessment. A passing process, passing tests, or exhausted review limit is not approval. Agent review cannot attest human labeling or human link decisions.
