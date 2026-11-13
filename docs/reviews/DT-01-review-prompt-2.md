# Independent implementation review — DT-01, submission 2 of 7

## 1. Story and submission context

**Task:** DT-01 — Requirements and Gherkin scenarios parsed into stable artifacts.
**Roadmap/feature:** F-02 Ingestion, roadmap §6 DT-01; milestone **M1 — AI-free vertical slice**.
**GitHub story:** anthonygraca/gherkin-knowledge-graph issue **#20**, verified OPEN at
2026-11-13T00:52:26Z with `gh issue view 20 --json number,title,state,milestone,url`; milestone
"M1 — AI-free vertical slice".
**Owner:** B. Implementer/integrator: OMP. Milestone ceiling: M1.
**Repository:** `<task_repo>` (read-only sandbox).
**Base revision:** `e18cdcfafe058e2f1d99c3c0b4bc2e155e9b16c9` (`main`).
**Branch:** `feat/20-dt-01-ingestion`.
**Submission:** 2 of 7. Submission 1 (2026-11-13T00:58:20Z snapshot) returned **REQUEST_CHANGES**
with blocking findings DT01-R1…R4 and nonblocking DT01-N1. The verbatim verdict is
`docs/reviews/DT-01-review.md`; the submission-1 packet (which contains the previously reviewed
file contents) is `docs/reviews/DT-01-review-prompt.md`. All five findings are addressed in this
submission; none was dismissed.

Current behavior differs from submission 1 only where section 4 says so. Unchanged files that the
round-1 reviewer verified are referenced by hash instead of being copied again (packet economy);
changed files and all new tests are included in full.

### User outcome

A systems engineer can point ingestion at a repository revision and receive stable artifact
identities for requirements and Gherkin scenarios, each pinned to one immutable commit and content
hash, so later rules and change detection can rely on those identities.

### Scope / non-goals (unchanged)

Scope: requirement front matter, `@SCN-nnn` scenarios, revision-pinned Git reads, artifact hashing,
loud rejection of malformed declarations. Non-goals: DT-02 source/test artifacts, DT-03 links,
DT-04 threads/store cutover, AS-01 rules, AS-04 UI, a Gherkin runner, general repository layouts,
sub-file granularity, durable storage (ADR 0006).

### Proposed commit reference

`feat(ingestion): [issue #20] parse requirements and Gherkin into stable artifacts` with body
`Refs #20`. Closure is a PR/merge decision after this review.

## 2. Acceptance criteria (canonical snapshot)

File: `docs/stories/DT-01.feature`, sha256
`f9482054b95e080ad31db37738cd91224aea821731d16daefd6569d69e21e576`.

SCN-507…511 were added in this submission to make the repaired defect classes (revision pinning,
declaration context, YAML semantics, malformed identity tokens) observable acceptance criteria.
The intake criteria SCN-501…506 keep their wording and were not weakened.

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

  @SCN-507
  Scenario: A symbolic revision is resolved once for the whole scan
    Given the fixture repository has tag "baseline-a" at a full commit SHA
    When the revision is ingested by tag name
    Then every artifact revision is that full commit SHA
    And ingesting the same revision by its SHA returns identical artifacts

  @SCN-508
  Scenario: Scenario-like text inside a doc string is data
    Given a tagged scenario whose step contains a doc string with "@SCN-999" and "Scenario: not real"
    When the scenarios are ingested
    Then only the real tagged scenario becomes an artifact

  @SCN-509
  Scenario: A malformed scenario identity token is rejected
    Given a scenario tagged "@SCN-99"
    When the scenarios are ingested
    Then ingestion fails with an error naming "@SCN-99"

  @SCN-510
  Scenario: Quoted front matter values keep their meaning
    Given a requirement whose id and status are quoted YAML strings with a trailing comment
    When the requirement is ingested
    Then the id is "REQ-900" without quotation marks
    And the status is "superseded" without the comment
    And a quoted title is stored without quotation marks

  @SCN-511
  Scenario: Invalid YAML front matter is rejected
    Given a requirement whose front matter has an unterminated quoted title
    When the revision is ingested
    Then ingestion fails with an error naming the file and the YAML problem
```

Refinement disposition: criteria derive from the owner-authored issue intake and roadmap §6;
failure and boundary scenarios were added without weakening intake wording. No separate human
refinement sign-off is recorded, and the draft project definition is not treated as an approved
requirements baseline.

Repository constraints that apply (AGENTS.md): offline by default (no network/GPU/model/DB/Docker
in tests or default paths); proposals ≠ accepted links ≠ verification; anything claiming
verification is revision-aware with content hashes; hand-labeled oracle data is independent of the
code under test; contract-only endpoints stay 501; Pydantic models are the API/domain boundary.

## 3. Snapshot, manifest, and cumulative diff

Snapshot captured 2026-11-13T01:14Z. Manifest (sha256 of every task file):

```text
c87a149c478ddbcd7322ffbdda723362bda18729da264048be5c3eaa9e58cdbf  backend/app/ingestion/__init__.py
b33cd36ad1a42f9f18720cf11f5d42aea424646ba8ff5b286587995ab2799a1d  backend/app/ingestion/errors.py
7e2ea7cd8dae466caa3915f4c17ae85b22543350a883d1ef8234397a4bb67aed  backend/app/ingestion/parsers.py
eaaec286ca5dddff28914b6e3a431338a4082b17edd703548ec9fda811d6c005  backend/app/ingestion/repository.py
6300e39d2bcf1305bd5c69ef337f4ae48999bb5134556a4b457befea4500556f  backend/app/ingestion/scan.py
37e23872d1b930b27a18b9a31572c177e45026252f807504f08cf141d789fd45  backend/tests/test_ingestion_parsers.py
562a143489e58334b233cec66caa8eba073e2abe7c1e7768a48ea87226ad0ac6  backend/tests/test_ingestion_artifacts.py
0d3cf3827bddf31240411461d5c802876f99eab362ca8c6b1ecce3269e38b5e2  backend/pyproject.toml
3328532e7693da5df68c6d3d2d7f74a2d693270e660ac1d9708bcff15b45bfc5  backend/uv.lock
f9482054b95e080ad31db37738cd91224aea821731d16daefd6569d69e21e576  docs/stories/DT-01.feature
53781893f534a85c3649a9905b83f2aa2c28c82bedd58f4ec6ee9f629e7c3767  docs/stories/DT-01.md
5926759c78412da49573bdb745fb1369db2e3e0786f774eb0556280c9ddbcbd9  docs/architecture.md
72982280dcae3e56e825720fc099bd027be7c8dda4b09594dd3bec016d86868a  docs/STATUS.md
05310679a2bc002f0188caf7f97c04a5d824b4e9629bba43b844dacecaf97d9d  docs/reports/omp-dt-01-ingestion/IMPLEMENTATION.md
d3069151346ce892dab847d25e2bde13e1638d5a12e6ce71b457902f49dad94d  docs/reports/omp-dt-01-ingestion/METRICS.md
737df73803347c037293fb60826aef253f75a3e69efed7d035387152bf2dfca8  docs/reports/omp-dt-01-ingestion/PROMPT_LOG.md
c1d4860795b3104c71a3c8b511512e4e12303e853d7cc9ba7ba3f3f6a50282e2  docs/reviews/DT-01-review-prompt.md
047db754c1335ed2b3f4361645b5331d4f3531e778fd84027018bfadc6a0089f  docs/reviews/DT-01-review.md
```

Schema/package versions: `SCHEMA_VERSION = 0.1.0`, `PACKAGE_VERSION = 0.1.0`. This submission adds
the runtime dependency `pyyaml>=6,<7` and updates `backend/uv.lock`; no generated fixture, oracle,
contract model, API response, or workflow file is modified.

### Tracked-file diff (cumulative, against the base revision)

```diff
diff --git a/backend/pyproject.toml b/backend/pyproject.toml
index 2cbd66f..33ddf95 100644
--- a/backend/pyproject.toml
+++ b/backend/pyproject.toml
@@ -6,6 +6,7 @@ requires-python = ">=3.11"
 dependencies = [
     "fastapi>=0.115,<1",
     "pydantic>=2.9,<3",
+    "pyyaml>=6,<7",
     "uvicorn>=0.30,<1",
 ]
 
diff --git a/backend/uv.lock b/backend/uv.lock
index 85c4049..2cefc6a 100644
--- a/backend/uv.lock
+++ b/backend/uv.lock
@@ -1,5 +1,5 @@
 version = 1
-revision = 3
+revision = 5
 requires-python = ">=3.11"
 
 [[package]]
@@ -67,6 +67,7 @@ source = { editable = "." }
 dependencies = [
     { name = "fastapi" },
     { name = "pydantic" },
+    { name = "pyyaml" },
     { name = "uvicorn" },
 ]
 
@@ -81,6 +82,7 @@ dev = [
 requires-dist = [
     { name = "fastapi", specifier = ">=0.115,<1" },
     { name = "pydantic", specifier = ">=2.9,<3" },
+    { name = "pyyaml", specifier = ">=6,<7" },
     { name = "uvicorn", specifier = ">=0.30,<1" },
 ]
 
@@ -370,6 +372,61 @@ wheels = [
     { url = "https://files.pythonhosted.org/packages/a8/a4/20da314d277121d6534b3a980b29035dcd51e6744bd79075a6ce8fa4eb8d/pytest-8.4.2-py3-none-any.whl", hash = "sha256:872f880de3fc3a5bdc88a11b39c9710c3497a547cfa9320bc3c5e62fbf272e79", size = 365750, upload-time = "2025-09-04T14:34:20.226Z" },
 ]
 
+[[package]]
+name = "pyyaml"
+version = "6.0.3"
+source = { registry = "https://pypi.org/simple" }
+sdist = { url = "https://files.pythonhosted.org/packages/05/8e/961c0007c59b8dd7729d542c61a4d537767a59645b82a0b521206e1e25c2/pyyaml-6.0.3.tar.gz", hash = "sha256:d76623373421df22fb4cf8817020cbb7ef15c725b9d5e45f17e189bfc384190f", size = 130960, upload-time = "2025-09-25T21:33:16.546Z" }
+wheels = [
+    { url = "https://files.pythonhosted.org/packages/6d/16/a95b6757765b7b031c9374925bb718d55e0a9ba8a1b6a12d25962ea44347/pyyaml-6.0.3-cp311-cp311-macosx_10_13_x86_64.whl", hash = "sha256:44edc647873928551a01e7a563d7452ccdebee747728c1080d881d68af7b997e", size = 185826, upload-time = "2025-09-25T21:31:58.655Z" },
+    { url = "https://files.pythonhosted.org/packages/16/19/13de8e4377ed53079ee996e1ab0a9c33ec2faf808a4647b7b4c0d46dd239/pyyaml-6.0.3-cp311-cp311-macosx_11_0_arm64.whl", hash = "sha256:652cb6edd41e718550aad172851962662ff2681490a8a711af6a4d288dd96824", size = 175577, upload-time = "2025-09-25T21:32:00.088Z" },
+    { url = "https://files.pythonhosted.org/packages/0c/62/d2eb46264d4b157dae1275b573017abec435397aa59cbcdab6fc978a8af4/pyyaml-6.0.3-cp311-cp311-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl", hash = "sha256:10892704fc220243f5305762e276552a0395f7beb4dbf9b14ec8fd43b57f126c", size = 775556, upload-time = "2025-09-25T21:32:01.31Z" },
+    { url = "https://files.pythonhosted.org/packages/10/cb/16c3f2cf3266edd25aaa00d6c4350381c8b012ed6f5276675b9eba8d9ff4/pyyaml-6.0.3-cp311-cp311-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl", hash = "sha256:850774a7879607d3a6f50d36d04f00ee69e7fc816450e5f7e58d7f17f1ae5c00", size = 882114, upload-time = "2025-09-25T21:32:03.376Z" },
+    { url = "https://files.pythonhosted.org/packages/71/60/917329f640924b18ff085ab889a11c763e0b573da888e8404ff486657602/pyyaml-6.0.3-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl", hash = "sha256:b8bb0864c5a28024fac8a632c443c87c5aa6f215c0b126c449ae1a150412f31d", size = 806638, upload-time = "2025-09-25T21:32:04.553Z" },
+    { url = "https://files.pythonhosted.org/packages/dd/6f/529b0f316a9fd167281a6c3826b5583e6192dba792dd55e3203d3f8e655a/pyyaml-6.0.3-cp311-cp311-musllinux_1_2_aarch64.whl", hash = "sha256:1d37d57ad971609cf3c53ba6a7e365e40660e3be0e5175fa9f2365a379d6095a", size = 767463, upload-time = "2025-09-25T21:32:06.152Z" },
+    { url = "https://files.pythonhosted.org/packages/f2/6a/b627b4e0c1dd03718543519ffb2f1deea4a1e6d42fbab8021936a4d22589/pyyaml-6.0.3-cp311-cp311-musllinux_1_2_x86_64.whl", hash = "sha256:37503bfbfc9d2c40b344d06b2199cf0e96e97957ab1c1b546fd4f87e53e5d3e4", size = 794986, upload-time = "2025-09-25T21:32:07.367Z" },
+    { url = "https://files.pythonhosted.org/packages/45/91/47a6e1c42d9ee337c4839208f30d9f09caa9f720ec7582917b264defc875/pyyaml-6.0.3-cp311-cp311-win32.whl", hash = "sha256:8098f252adfa6c80ab48096053f512f2321f0b998f98150cea9bd23d83e1467b", size = 142543, upload-time = "2025-09-25T21:32:08.95Z" },
+    { url = "https://files.pythonhosted.org/packages/da/e3/ea007450a105ae919a72393cb06f122f288ef60bba2dc64b26e2646fa315/pyyaml-6.0.3-cp311-cp311-win_amd64.whl", hash = "sha256:9f3bfb4965eb874431221a3ff3fdcddc7e74e3b07799e0e84ca4a0f867d449bf", size = 158763, upload-time = "2025-09-25T21:32:09.96Z" },
+    { url = "https://files.pythonhosted.org/packages/d1/33/422b98d2195232ca1826284a76852ad5a86fe23e31b009c9886b2d0fb8b2/pyyaml-6.0.3-cp312-cp312-macosx_10_13_x86_64.whl", hash = "sha256:7f047e29dcae44602496db43be01ad42fc6f1cc0d8cd6c83d342306c32270196", size = 182063, upload-time = "2025-09-25T21:32:11.445Z" },
+    { url = "https://files.pythonhosted.org/packages/89/a0/6cf41a19a1f2f3feab0e9c0b74134aa2ce6849093d5517a0c550fe37a648/pyyaml-6.0.3-cp312-cp312-macosx_11_0_arm64.whl", hash = "sha256:fc09d0aa354569bc501d4e787133afc08552722d3ab34836a80547331bb5d4a0", size = 173973, upload-time = "2025-09-25T21:32:12.492Z" },
+    { url = "https://files.pythonhosted.org/packages/ed/23/7a778b6bd0b9a8039df8b1b1d80e2e2ad78aa04171592c8a5c43a56a6af4/pyyaml-6.0.3-cp312-cp312-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl", hash = "sha256:9149cad251584d5fb4981be1ecde53a1ca46c891a79788c0df828d2f166bda28", size = 775116, upload-time = "2025-09-25T21:32:13.652Z" },
+    { url = "https://files.pythonhosted.org/packages/65/30/d7353c338e12baef4ecc1b09e877c1970bd3382789c159b4f89d6a70dc09/pyyaml-6.0.3-cp312-cp312-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl", hash = "sha256:5fdec68f91a0c6739b380c83b951e2c72ac0197ace422360e6d5a959d8d97b2c", size = 844011, upload-time = "2025-09-25T21:32:15.21Z" },
+    { url = "https://files.pythonhosted.org/packages/8b/9d/b3589d3877982d4f2329302ef98a8026e7f4443c765c46cfecc8858c6b4b/pyyaml-6.0.3-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl", hash = "sha256:ba1cc08a7ccde2d2ec775841541641e4548226580ab850948cbfda66a1befcdc", size = 807870, upload-time = "2025-09-25T21:32:16.431Z" },
+    { url = "https://files.pythonhosted.org/packages/05/c0/b3be26a015601b822b97d9149ff8cb5ead58c66f981e04fedf4e762f4bd4/pyyaml-6.0.3-cp312-cp312-musllinux_1_2_aarch64.whl", hash = "sha256:8dc52c23056b9ddd46818a57b78404882310fb473d63f17b07d5c40421e47f8e", size = 761089, upload-time = "2025-09-25T21:32:17.56Z" },
+    { url = "https://files.pythonhosted.org/packages/be/8e/98435a21d1d4b46590d5459a22d88128103f8da4c2d4cb8f14f2a96504e1/pyyaml-6.0.3-cp312-cp312-musllinux_1_2_x86_64.whl", hash = "sha256:41715c910c881bc081f1e8872880d3c650acf13dfa8214bad49ed4cede7c34ea", size = 790181, upload-time = "2025-09-25T21:32:18.834Z" },
+    { url = "https://files.pythonhosted.org/packages/74/93/7baea19427dcfbe1e5a372d81473250b379f04b1bd3c4c5ff825e2327202/pyyaml-6.0.3-cp312-cp312-win32.whl", hash = "sha256:96b533f0e99f6579b3d4d4995707cf36df9100d67e0c8303a0c55b27b5f99bc5", size = 137658, upload-time = "2025-09-25T21:32:20.209Z" },
+    { url = "https://files.pythonhosted.org/packages/86/bf/899e81e4cce32febab4fb42bb97dcdf66bc135272882d1987881a4b519e9/pyyaml-6.0.3-cp312-cp312-win_amd64.whl", hash = "sha256:5fcd34e47f6e0b794d17de1b4ff496c00986e1c83f7ab2fb8fcfe9616ff7477b", size = 154003, upload-time = "2025-09-25T21:32:21.167Z" },
+    { url = "https://files.pythonhosted.org/packages/1a/08/67bd04656199bbb51dbed1439b7f27601dfb576fb864099c7ef0c3e55531/pyyaml-6.0.3-cp312-cp312-win_arm64.whl", hash = "sha256:64386e5e707d03a7e172c0701abfb7e10f0fb753ee1d773128192742712a98fd", size = 140344, upload-time = "2025-09-25T21:32:22.617Z" },
+    { url = "https://files.pythonhosted.org/packages/d1/11/0fd08f8192109f7169db964b5707a2f1e8b745d4e239b784a5a1dd80d1db/pyyaml-6.0.3-cp313-cp313-macosx_10_13_x86_64.whl", hash = "sha256:8da9669d359f02c0b91ccc01cac4a67f16afec0dac22c2ad09f46bee0697eba8", size = 181669, upload-time = "2025-09-25T21:32:23.673Z" },
+    { url = "https://files.pythonhosted.org/packages/b1/16/95309993f1d3748cd644e02e38b75d50cbc0d9561d21f390a76242ce073f/pyyaml-6.0.3-cp313-cp313-macosx_11_0_arm64.whl", hash = "sha256:2283a07e2c21a2aa78d9c4442724ec1eb15f5e42a723b99cb3d822d48f5f7ad1", size = 173252, upload-time = "2025-09-25T21:32:25.149Z" },
+    { url = "https://files.pythonhosted.org/packages/50/31/b20f376d3f810b9b2371e72ef5adb33879b25edb7a6d072cb7ca0c486398/pyyaml-6.0.3-cp313-cp313-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl", hash = "sha256:ee2922902c45ae8ccada2c5b501ab86c36525b883eff4255313a253a3160861c", size = 767081, upload-time = "2025-09-25T21:32:26.575Z" },
+    { url = "https://files.pythonhosted.org/packages/49/1e/a55ca81e949270d5d4432fbbd19dfea5321eda7c41a849d443dc92fd1ff7/pyyaml-6.0.3-cp313-cp313-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl", hash = "sha256:a33284e20b78bd4a18c8c2282d549d10bc8408a2a7ff57653c0cf0b9be0afce5", size = 841159, upload-time = "2025-09-25T21:32:27.727Z" },
+    { url = "https://files.pythonhosted.org/packages/74/27/e5b8f34d02d9995b80abcef563ea1f8b56d20134d8f4e5e81733b1feceb2/pyyaml-6.0.3-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl", hash = "sha256:0f29edc409a6392443abf94b9cf89ce99889a1dd5376d94316ae5145dfedd5d6", size = 801626, upload-time = "2025-09-25T21:32:28.878Z" },
+    { url = "https://files.pythonhosted.org/packages/f9/11/ba845c23988798f40e52ba45f34849aa8a1f2d4af4b798588010792ebad6/pyyaml-6.0.3-cp313-cp313-musllinux_1_2_aarch64.whl", hash = "sha256:f7057c9a337546edc7973c0d3ba84ddcdf0daa14533c2065749c9075001090e6", size = 753613, upload-time = "2025-09-25T21:32:30.178Z" },
+    { url = "https://files.pythonhosted.org/packages/3d/e0/7966e1a7bfc0a45bf0a7fb6b98ea03fc9b8d84fa7f2229e9659680b69ee3/pyyaml-6.0.3-cp313-cp313-musllinux_1_2_x86_64.whl", hash = "sha256:eda16858a3cab07b80edaf74336ece1f986ba330fdb8ee0d6c0d68fe82bc96be", size = 794115, upload-time = "2025-09-25T21:32:31.353Z" },
+    { url = "https://files.pythonhosted.org/packages/de/94/980b50a6531b3019e45ddeada0626d45fa85cbe22300844a7983285bed3b/pyyaml-6.0.3-cp313-cp313-win32.whl", hash = "sha256:d0eae10f8159e8fdad514efdc92d74fd8d682c933a6dd088030f3834bc8e6b26", size = 137427, upload-time = "2025-09-25T21:32:32.58Z" },
+    { url = "https://files.pythonhosted.org/packages/97/c9/39d5b874e8b28845e4ec2202b5da735d0199dbe5b8fb85f91398814a9a46/pyyaml-6.0.3-cp313-cp313-win_amd64.whl", hash = "sha256:79005a0d97d5ddabfeeea4cf676af11e647e41d81c9a7722a193022accdb6b7c", size = 154090, upload-time = "2025-09-25T21:32:33.659Z" },
+    { url = "https://files.pythonhosted.org/packages/73/e8/2bdf3ca2090f68bb3d75b44da7bbc71843b19c9f2b9cb9b0f4ab7a5a4329/pyyaml-6.0.3-cp313-cp313-win_arm64.whl", hash = "sha256:5498cd1645aa724a7c71c8f378eb29ebe23da2fc0d7a08071d89469bf1d2defb", size = 140246, upload-time = "2025-09-25T21:32:34.663Z" },
+    { url = "https://files.pythonhosted.org/packages/9d/8c/f4bd7f6465179953d3ac9bc44ac1a8a3e6122cf8ada906b4f96c60172d43/pyyaml-6.0.3-cp314-cp314-macosx_10_13_x86_64.whl", hash = "sha256:8d1fab6bb153a416f9aeb4b8763bc0f22a5586065f86f7664fc23339fc1c1fac", size = 181814, upload-time = "2025-09-25T21:32:35.712Z" },
+    { url = "https://files.pythonhosted.org/packages/bd/9c/4d95bb87eb2063d20db7b60faa3840c1b18025517ae857371c4dd55a6b3a/pyyaml-6.0.3-cp314-cp314-macosx_11_0_arm64.whl", hash = "sha256:34d5fcd24b8445fadc33f9cf348c1047101756fd760b4dacb5c3e99755703310", size = 173809, upload-time = "2025-09-25T21:32:36.789Z" },
+    { url = "https://files.pythonhosted.org/packages/92/b5/47e807c2623074914e29dabd16cbbdd4bf5e9b2db9f8090fa64411fc5382/pyyaml-6.0.3-cp314-cp314-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl", hash = "sha256:501a031947e3a9025ed4405a168e6ef5ae3126c59f90ce0cd6f2bfc477be31b7", size = 766454, upload-time = "2025-09-25T21:32:37.966Z" },
+    { url = "https://files.pythonhosted.org/packages/02/9e/e5e9b168be58564121efb3de6859c452fccde0ab093d8438905899a3a483/pyyaml-6.0.3-cp314-cp314-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl", hash = "sha256:b3bc83488de33889877a0f2543ade9f70c67d66d9ebb4ac959502e12de895788", size = 836355, upload-time = "2025-09-25T21:32:39.178Z" },
+    { url = "https://files.pythonhosted.org/packages/88/f9/16491d7ed2a919954993e48aa941b200f38040928474c9e85ea9e64222c3/pyyaml-6.0.3-cp314-cp314-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl", hash = "sha256:c458b6d084f9b935061bc36216e8a69a7e293a2f1e68bf956dcd9e6cbcd143f5", size = 794175, upload-time = "2025-09-25T21:32:40.865Z" },
+    { url = "https://files.pythonhosted.org/packages/dd/3f/5989debef34dc6397317802b527dbbafb2b4760878a53d4166579111411e/pyyaml-6.0.3-cp314-cp314-musllinux_1_2_aarch64.whl", hash = "sha256:7c6610def4f163542a622a73fb39f534f8c101d690126992300bf3207eab9764", size = 755228, upload-time = "2025-09-25T21:32:42.084Z" },
+    { url = "https://files.pythonhosted.org/packages/d7/ce/af88a49043cd2e265be63d083fc75b27b6ed062f5f9fd6cdc223ad62f03e/pyyaml-6.0.3-cp314-cp314-musllinux_1_2_x86_64.whl", hash = "sha256:5190d403f121660ce8d1d2c1bb2ef1bd05b5f68533fc5c2ea899bd15f4399b35", size = 789194, upload-time = "2025-09-25T21:32:43.362Z" },
+    { url = "https://files.pythonhosted.org/packages/23/20/bb6982b26a40bb43951265ba29d4c246ef0ff59c9fdcdf0ed04e0687de4d/pyyaml-6.0.3-cp314-cp314-win_amd64.whl", hash = "sha256:4a2e8cebe2ff6ab7d1050ecd59c25d4c8bd7e6f400f5f82b96557ac0abafd0ac", size = 156429, upload-time = "2025-09-25T21:32:57.844Z" },
+    { url = "https://files.pythonhosted.org/packages/f4/f4/a4541072bb9422c8a883ab55255f918fa378ecf083f5b85e87fc2b4eda1b/pyyaml-6.0.3-cp314-cp314-win_arm64.whl", hash = "sha256:93dda82c9c22deb0a405ea4dc5f2d0cda384168e466364dec6255b293923b2f3", size = 143912, upload-time = "2025-09-25T21:32:59.247Z" },
+    { url = "https://files.pythonhosted.org/packages/7c/f9/07dd09ae774e4616edf6cda684ee78f97777bdd15847253637a6f052a62f/pyyaml-6.0.3-cp314-cp314t-macosx_10_13_x86_64.whl", hash = "sha256:02893d100e99e03eda1c8fd5c441d8c60103fd175728e23e431db1b589cf5ab3", size = 189108, upload-time = "2025-09-25T21:32:44.377Z" },
+    { url = "https://files.pythonhosted.org/packages/4e/78/8d08c9fb7ce09ad8c38ad533c1191cf27f7ae1effe5bb9400a46d9437fcf/pyyaml-6.0.3-cp314-cp314t-macosx_11_0_arm64.whl", hash = "sha256:c1ff362665ae507275af2853520967820d9124984e0f7466736aea23d8611fba", size = 183641, upload-time = "2025-09-25T21:32:45.407Z" },
+    { url = "https://files.pythonhosted.org/packages/7b/5b/3babb19104a46945cf816d047db2788bcaf8c94527a805610b0289a01c6b/pyyaml-6.0.3-cp314-cp314t-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl", hash = "sha256:6adc77889b628398debc7b65c073bcb99c4a0237b248cacaf3fe8a557563ef6c", size = 831901, upload-time = "2025-09-25T21:32:48.83Z" },
+    { url = "https://files.pythonhosted.org/packages/8b/cc/dff0684d8dc44da4d22a13f35f073d558c268780ce3c6ba1b87055bb0b87/pyyaml-6.0.3-cp314-cp314t-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl", hash = "sha256:a80cb027f6b349846a3bf6d73b5e95e782175e52f22108cfa17876aaeff93702", size = 861132, upload-time = "2025-09-25T21:32:50.149Z" },
+    { url = "https://files.pythonhosted.org/packages/b1/5e/f77dc6b9036943e285ba76b49e118d9ea929885becb0a29ba8a7c75e29fe/pyyaml-6.0.3-cp314-cp314t-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl", hash = "sha256:00c4bdeba853cc34e7dd471f16b4114f4162dc03e6b7afcc2128711f0eca823c", size = 839261, upload-time = "2025-09-25T21:32:51.808Z" },
+    { url = "https://files.pythonhosted.org/packages/ce/88/a9db1376aa2a228197c58b37302f284b5617f56a5d959fd1763fb1675ce6/pyyaml-6.0.3-cp314-cp314t-musllinux_1_2_aarch64.whl", hash = "sha256:66e1674c3ef6f541c35191caae2d429b967b99e02040f5ba928632d9a7f0f065", size = 805272, upload-time = "2025-09-25T21:32:52.941Z" },
+    { url = "https://files.pythonhosted.org/packages/da/92/1446574745d74df0c92e6aa4a7b0b3130706a4142b2d1a5869f2eaa423c6/pyyaml-6.0.3-cp314-cp314t-musllinux_1_2_x86_64.whl", hash = "sha256:16249ee61e95f858e83976573de0f5b2893b3677ba71c9dd36b9cf8be9ac6d65", size = 829923, upload-time = "2025-09-25T21:32:54.537Z" },
+    { url = "https://files.pythonhosted.org/packages/f0/7a/1c7270340330e575b92f397352af856a8c06f230aa3e76f86b39d01b416a/pyyaml-6.0.3-cp314-cp314t-win_amd64.whl", hash = "sha256:4ad1906908f2f5ae4e5a8ddfce73c320c2a1429ec52eafd27138b7f1cbe341c9", size = 174062, upload-time = "2025-09-25T21:32:55.767Z" },
+    { url = "https://files.pythonhosted.org/packages/f1/12/de94a39c2ef588c7e6455cfbe7343d3b2dc9d6b6b2f40c4c6565744c873d/pyyaml-6.0.3-cp314-cp314t-win_arm64.whl", hash = "sha256:ebc55a14a21cb14062aa4162f906cd962b28e2e9ea38f9b4391244cd8de4ae0b", size = 149341, upload-time = "2025-09-25T21:32:56.828Z" },
+]
+
 [[package]]
 name = "ruff"
 version = "0.17.4"
diff --git a/docs/STATUS.md b/docs/STATUS.md
index 58c56ae..3166e36 100644
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
@@ -15,15 +15,14 @@ Independent review:  docs/reviews/M0-review.md — first review: "M0 not verifie
                      docs/reviews/M0-rereview-2.md — re-review round 2 (GPT-6.1 Sol, xhigh):
                      APPROVE at snapshot bca69cf (tree e55ff9f); R8 repaired/closed; no open
                      major finding; M0 exit criteria verified within scope
-Active task:         none — SETUP-01 commit-reference enforcement landed via PR #42; commitlint
-                     green on the landed history (9 commits). Next work: M1 (B: DT-01/DT-02,
-                     C: AS-01/AS-04) with A's M3 items in parallel; outstanding owner actions:
-                     #18/#19 closure, FT-03 review, required-check ruleset, README work item
-Tests executed:      M0 approved snapshot (bca69cf): 107 passed offline (also under an OS-level
-                     network denial); fixturectl verify exit 0; ruff clean.
-                     Current tree (main f34ae07 + the uncommitted SETUP-01 slice): 135 passed
-                     (same 135 under an OS-level network denial); fixturectl verify exit 0;
-                     ruff check/format clean (35 files); commitlint checks pass on real history.
+Historical (SETUP-01, 2026-11-12): the commit-reference slice landed via PR #42; commitlint
+                     green on the landed history (9 commits); the M0 approved snapshot bca69cf
+                     had 107 passed; the SETUP-01 tree then had 135 passed (also under an
+                     OS-level network denial). Outstanding owner actions: #18/#19 closure, the
+                     FT-03/project-definition reviews, the required-check ruleset, README work item.
+Tests executed:      DT-01 (2026-11-13T01:13Z): 169 passed (also under an OS-level network
+                     denial); fixturectl verify exit 0; ruff check/format clean. Round-1 review
+                     findings repaired; details in docs/reports/omp-dt-01-ingestion/.
 Current API/schema version: 0.1.0
 Tracker:             docs/traceability-issue-map.md (features → user stories → tasks)
 Run records:         docs/reports/omp-m0-rereview/ and docs/reports/omp-setup-01-commitlint/
@@ -33,6 +32,28 @@ Environment:         Python ≥3.11, uv, git ≥2.28; no GPU, LLM, vector store,
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

### Changed implementation files (complete)

`backend/app/ingestion/parsers.py`:
```python
"""Pure text parsers for artifact declarations.

Declaration conventions are defined in ``docs/domain-contracts.md``:

* requirement: YAML front matter with ``id:`` and ``title:`` in ``requirements/*.md``;
* scenario: an ``@SCN-nnn`` tag immediately preceding the Gherkin ``Scenario:`` line.

Parsers are pure functions over text so malformed-input behaviour is testable without Git, and
they never guess: an unrecognizable declaration raises :class:`IngestionError` rather than
producing a partial result. Front matter is parsed as YAML (quoted values and comments keep their
declared meaning) and only string scalars are accepted, matching the requirement schema.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

import yaml

from app.ingestion.errors import IngestionError

SCENARIO_ID_RE = re.compile(r"SCN-\d{3}")
SCENARIO_LINE_RE = re.compile(r"^\s*Scenario:\s*(?P<title>\S.*?)\s*$")
DOC_STRING_DELIMITERS = ('"""', "```")

FRONT_MATTER_OPEN = "---\n"
FRONT_MATTER_DELIMITER = "\n---\n"


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

    Quoted scalars lose their quotation marks, comments are not part of a value, duplicate keys
    and invalid YAML raise, and non-string scalars are rejected: the requirement schema declares
    these fields as strings, so silently stringifying ``status: yes`` would invent meaning.
    """
    if not text.startswith(FRONT_MATTER_OPEN):
        raise IngestionError(
            f"{where}: expected a '---' front matter block at the start of the file"
        )
    end = text.find(FRONT_MATTER_DELIMITER, len(FRONT_MATTER_OPEN))
    if end == -1:
        raise IngestionError(f"{where}: front matter block is not terminated by '---'")

    try:
        parsed = yaml.load(text[len(FRONT_MATTER_OPEN) : end], Loader=_UniqueKeyLoader)
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

    for line in text.splitlines():
        stripped = line.strip()
        if in_doc_string:
            if stripped.startswith(doc_delimiter):
                in_doc_string = False
            continue
        if stripped.startswith(DOC_STRING_DELIMITERS):
            if pending is not None:
                raise IngestionError(
                    f"{where}: tag @{pending} is not followed by a 'Scenario:' line"
                )
            doc_delimiter = '"""' if stripped.startswith('"""') else "```"
            if doc_delimiter not in stripped[len(doc_delimiter) :]:
                in_doc_string = True
            continue
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("@"):
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


def _identity_tokens(line: str, *, where: str) -> list[str]:
    """Valid ``@SCN-nnn`` identities on a tag line; malformed reserved tokens raise."""
    identities: list[str] = []
    for token in line.split():
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

### Changed tests (complete)

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
```

### Changed documentation (complete)

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
| Canonical criteria | [DT-01.feature](DT-01.feature), sha256 `f9482054b95e080ad31db37738cd91224aea821731d16daefd6569d69e21e576` |
| Upstream obligation | Roadmap §4 artifact contract, §5 fixture discipline, §6 F-02; project-definition REQ-105 (draft, not approved) |
| Dependencies | M0 approved (FT-01 #18, FT-02 #19); PyYAML runtime dependency added for front-matter parsing. No later-milestone dependency |

## User outcome

A systems engineer can point the system at a repository revision and receive stable artifact
identities for requirements and Gherkin scenarios, with the revision and content hash that the
identity was read at. Later rules and change detection can rely on those identities without
re-parsing ad hoc files.

## Scope

* Parse requirement front matter (`id`, `title`, `status`) from `requirements/*.md` as YAML:
  quoted values and comments keep their declared meaning; duplicate keys, invalid YAML, and
  non-string scalars are rejected.
* Resolve the requested revision to one full commit SHA at the scan boundary; every Git read and
  every `Artifact.revision` uses that SHA, so tags and abbreviated SHAs cannot leak into
  provenance or let a moving reference mix revisions mid-scan.
* Parse `@SCN-nnn`-tagged scenarios from `features/*.feature`; the artifact locator anchors the
  scenario inside its file; the title is the scenario name.
* Read bytes from the pinned Git revision (not the working tree) and compute
  `content_hash = sha256:<hex>` over the blob.
* Fail loudly on malformed input: missing/torn front matter, invalid YAML, a dangling `@SCN` tag,
  a malformed `@SCN` token, two identity tags on one line, an artifact id whose prefix disagrees
  with its type, duplicate artifact identities, or unreadable/non-UTF-8 files.
* Treat Gherkin doc-string contents as data: tags and `Scenario:` text inside a doc string never
  declare an artifact, and an unterminated doc string is an error.
* Accept additional non-identity Gherkin tags on the same line or on intervening tag lines
  (`@smoke @SCN-907`); only the `@SCN-nnn` token declares identity.
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
| `parsers.py` | Pure text parsers: YAML front matter (safe loader, duplicate-key rejection) and tagged scenarios with doc-string awareness |
| `repository.py` | `GitRepository`: revision resolution, tree listing, blob reads via the Git CLI |
| `scan.py` | Revision scan resolved once to a full commit SHA → `Artifact` list, with duplicate-identity and type/prefix rejection |

Parsers are pure functions so malformed-input cases are unit-testable without Git. Front matter
uses `PyYAML` (added as a runtime dependency) instead of a hand-rolled subset; that is the boring
choice for a declared YAML format. Git access is read-only and uses the repository's existing Git
prerequisite (roadmap §3 allows the Git CLI). No database is introduced (ADR 0006 #1 stays open;
DT-04 documents the M1 in-process store).

Assumptions (load-bearing, stated here):

1. Requirements live at `requirements/*.md`; scenarios live at `features/*.feature`, matching the
   fixture and `docs/domain-contracts.md`.
2. A scenario tag is followed by its `Scenario:` line, optionally separated by blank lines,
   comment lines, or additional non-identity tag lines. Any other intervening declaration
   (`Rule:`, `Scenario Outline:`, a step, a doc string) is a dangling identity and an error.
3. Artifact granularity is file level; every scenario in one file shares that file's content hash.
4. Identity is path-stable; a renamed file is a new artifact (ADR 0006 #8).
5. Front-matter values are YAML string scalars; numeric- or boolean-looking values must be quoted
   if they are intended as strings. `PyYAML` is the parser (safe loader, duplicate-key detection).

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
| SCN-507 | Tag and SHA ingestion return identical artifacts with the full SHA; an abbreviated SHA is expanded; a recording repository proves every read uses the resolved commit | `::test_tag_and_sha_ingestion_return_identical_artifacts`, `::test_abbreviated_sha_is_pinned_to_the_full_commit`, `::test_every_read_uses_the_resolved_commit` |
| SCN-508 | Doc-string tags and `Scenario:` text are ignored; an unterminated doc string raises | `backend/tests/test_ingestion_parsers.py::test_doc_string_contents_are_data`, `::test_an_unterminated_doc_string_is_rejected` |
| SCN-509 | `@SCN-99` alone and beside a valid identity raise naming the token | `backend/tests/test_ingestion_parsers.py::test_a_malformed_identity_token_is_rejected`, `::test_a_malformed_identity_beside_a_valid_one_is_rejected` |
| SCN-510 | Quoted id/title/status parse without marks; a trailing comment is excluded (parser and scanner levels) | `backend/tests/test_ingestion_parsers.py::test_front_matter_parses_quoted_values_and_comments`, `backend/tests/test_ingestion_artifacts.py::test_quoted_front_matter_values_are_parsed` |
| SCN-511 | Unterminated quoted YAML raises at parser and scanner levels; non-string scalars are rejected | `backend/tests/test_ingestion_parsers.py::test_front_matter_rejects_invalid_yaml`, `::test_front_matter_rejects_non_string_scalars`, `backend/tests/test_ingestion_artifacts.py::test_invalid_yaml_is_rejected_by_the_scanner` |
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
| Canonical criteria | [DT-01.feature](../../stories/DT-01.feature), sha256 `f9482054b95e080ad31db37738cd91224aea821731d16daefd6569d69e21e576` |
| Brief / verification map | [DT-01.md](../../stories/DT-01.md) |
| Branch / base | `feat/20-dt-01-ingestion` from `e18cdcfafe058e2f1d99c3c0b4bc2e155e9b16c9` |
| Contract version | `SCHEMA_VERSION = 0.1.0`, `PACKAGE_VERSION = 0.1.0` (no API/domain contract change) |
| Submission | **2 of 7** (round 1 = REQUEST_CHANGES; R1–R4 repaired before this submission) |
| Snapshot captured | 2026-11-13T01:14Z |

## What changed

| Path | sha256 | Purpose |
| --- | --- | --- |
| `backend/app/ingestion/__init__.py` | `c87a149c478ddbcd7322ffbdda723362bda18729da264048be5c3eaa9e58cdbf` | Package exports |
| `backend/app/ingestion/errors.py` | `b33cd36ad1a42f9f18720cf11f5d42aea424646ba8ff5b286587995ab2799a1d` | `IngestionError` for malformed content / Git access |
| `backend/app/ingestion/parsers.py` | `7e2ea7cd8dae466caa3915f4c17ae85b22543350a883d1ef8234397a4bb67aed` | YAML front matter + declaration-aware scenario parsing |
| `backend/app/ingestion/repository.py` | `eaaec286ca5dddff28914b6e3a431338a4082b17edd703548ec9fda811d6c005` | Read-only Git access at explicit revisions |
| `backend/app/ingestion/scan.py` | `6300e39d2bcf1305bd5c69ef337f4ae48999bb5134556a4b457befea4500556f` | Scan resolved once to a full commit; duplicate/prefix guards |
| `backend/tests/test_ingestion_parsers.py` | `37e23872d1b930b27a18b9a31572c177e45026252f807504f08cf141d789fd45` | Parser tests, including YAML and declaration context |
| `backend/tests/test_ingestion_artifacts.py` | `562a143489e58334b233cec66caa8eba073e2abe7c1e7768a48ea87226ad0ac6` | Acceptance tests against the built fixture and temp repositories |
| `backend/pyproject.toml` | `0d3cf3827bddf31240411461d5c802876f99eab362ca8c6b1ecce3269e38b5e2` | Adds `pyyaml>=6,<7` for declared YAML front matter |
| `backend/uv.lock` | `3328532e7693da5df68c6d3d2d7f74a2d693270e660ac1d9708bcff15b45bfc5` | Locked dependency graph |
| `docs/stories/DT-01.feature` | `f9482054b95e080ad31db37738cd91224aea821731d16daefd6569d69e21e576` | Canonical criteria (SCN-501…511) |
| `docs/stories/DT-01.md` | `53781893f534a85c3649a9905b83f2aa2c28c82bedd58f4ec6ee9f629e7c3767` | Brief, assumptions, verification map |
| `docs/architecture.md` | `5926759c78412da49573bdb745fb1369db2e3e0786f774eb0556280c9ddbcbd9` | Ingestion status is no longer "absent" |
| `docs/STATUS.md` | `72982280dcae3e56e825720fc099bd027be7c8dda4b09594dd3bec016d86868a` | M1 ledger; SETUP-01 figures labelled historical |

Generated fixtures, oracle labels, contract models, API responses, and the API itself are
untouched. `tools/fixturectl.py` still produces the M0 fixtures and is reused by ingestion only in
DT-02, after the scanner also covers source/test artifacts.

## Review round 1 — REQUEST_CHANGES (submission 1 of 7)

Reviewer: Codex `gpt-6.1-sol`, effort `xhigh`, read-only; session `01a1d25d-1906-72e1-bc4a-d40fc65f12f7`;
2026-11-13T01:01:52Z → 01:06:39Z; exit 0; 14/14 supplied hashes matched before and after. Verdict and
full findings: `docs/reviews/DT-01-review.md`.

| Finding | Severity | Repair | Recheck |
| --- | --- | --- | --- |
| DT01-R1 revision expressions leaked into artifact provenance; reads could mix revisions | major, blocking | `scan_artifacts` resolves once to a full commit SHA and uses it for every read and every `Artifact.revision` | `test_tag_and_sha_ingestion_return_identical_artifacts`, `test_abbreviated_sha_is_pinned_to_the_full_commit`, `test_every_read_uses_the_resolved_commit` |
| DT01-R2 a pending tag could attach to a scenario across `Rule:`/`Scenario Outline:` or from doc-string text | major, blocking | Declaration-aware state machine: only a `Scenario:` line (with blank/comment/tag lines allowed) consumes the identity; any other declaration raises; doc strings are lexical data; unterminated doc strings raise | `test_tag_before_a_rule_does_not_capture_a_nested_scenario`, `test_tag_before_a_scenario_outline_is_rejected_as_unsupported`, `test_doc_string_contents_are_data`, `test_an_unterminated_doc_string_is_rejected` |
| DT01-R3 hand-rolled front matter changed YAML meaning and accepted invalid YAML | major, blocking | `PyYAML` safe loader with duplicate-key rejection; string-scalar validation; quoted values/comments preserved; invalid YAML raises | `test_front_matter_parses_quoted_values_and_comments`, `test_front_matter_rejects_invalid_yaml`, `test_front_matter_rejects_non_string_scalars`, `test_quoted_front_matter_values_are_parsed`, `test_invalid_yaml_is_rejected_by_the_scanner` |
| DT01-R4 malformed `@SCN` tokens were silently ignored | major, blocking | Reserved-prefix token validation: any `@SCN…` token that is not `@SCN-nnn` raises, alone or beside a valid identity | `test_a_malformed_identity_token_is_rejected`, `test_a_malformed_identity_beside_a_valid_one_is_rejected` |
| DT01-N1 `STATUS.md` still said "Active task: none" and mixed older SETUP-01 results into current status | minor, nonblocking | Header and results corrected; SETUP-01 figures labelled historical | inspection |

New scenarios SCN-507…511 were added to the canonical specification to make the repaired defect
classes observable; the intake criteria were not weakened.

## Acceptance results

| Criterion | Check | Result |
| --- | --- | --- |
| SCN-501 requirement parsed | `tests/test_ingestion_artifacts.py::test_requirement_document_is_parsed_into_an_artifact` | PASS |
| SCN-502 scenario identity | `::test_scenario_identity_comes_from_the_gherkin_tag` | PASS |
| SCN-503 missing front matter | `::test_requirement_without_front_matter_is_rejected` | PASS |
| SCN-504 untagged scenario | `::test_untagged_scenario_creates_no_artifact` | PASS |
| SCN-505 dangling tag | `::test_dangling_scenario_tag_is_rejected` | PASS |
| SCN-506 duplicate identity | `::test_duplicate_artifact_identities_are_rejected` | PASS |
| SCN-507 revision pinning | three tests listed under R1 | PASS |
| SCN-508 doc-string data | two parser tests listed under R2 | PASS |
| SCN-509 malformed identity | two parser tests listed under R4 | PASS |
| SCN-510 quoted YAML | parser + scanner tests listed under R3 | PASS |
| SCN-511 invalid YAML | parser (2) + scanner tests listed under R3 | PASS |
| DoD parse vs snapshot | `::test_parsed_artifacts_match_the_committed_snapshot_for_requirements_and_scenarios` | PASS |
| DoD malformed parsers | `tests/test_ingestion_parsers.py` (20 tests) | PASS |

Axis coverage: success (501/502), failure (503/505/506/509/511), boundary (504, 507, 508, 510),
plus multi-tag lines, id/type disagreement, duplicates, and doc strings.

## Commands and outcomes (as captured)

```text
captured_start=2026-11-13T01:13:09Z
uv sync --project backend --frozen               exit 0  Checked 25 packages
pytest backend/tests -q                          exit 0  169 passed, 1 warning in 4.22s
fixturectl.py verify                             exit 0  reproducible and committed files current
ruff check .                                     exit 0  All checks passed
ruff format --check .                            exit 0  all files formatted
git diff --check                                 exit 0
captured_end=2026-11-13T01:13:15Z

network denial at 2026-11-13T01:13:19Z: `unshare -rn backend/.venv/bin/python -m pytest
backend/tests -q` → exit 0, 169 passed; the earlier socket probe produced
`OSError: [Errno 101] Network is unreachable`.
```

Raw logs are in the external run directory `…/m1-roadmap-20261112/dt-01/`. The committed
`IMPLEMENTATION.md` is the summary; the review packet carries the file manifest at submission.

## Self-review after repair

* **Revision-aware:** one resolved commit per scan; tag/SHA equivalence and full-SHA provenance are
  asserted; hashes are taken over the exact blob.
* **Loud failures:** invalid YAML, non-string scalars, duplicate keys, dangling/malformed
  identities, declaration-context violations, doc-string imbalance, duplicate artifacts, and type
  prefix mismatches all raise `IngestionError` naming the input.
* **Untrusted input:** YAML uses a safe loader with no object construction; Git arguments use
  `--end-of-options` and NUL-delimited tree output; text is never executed.
* **Offline:** PyYAML is a local library; no network, model, database, or service is involved.
* **Separation:** ingestion still reads artifacts only and cannot create links or evidence.
* **Regression:** full suite, drift check, lint, and the network-denied suite pass.

## Independent review

**Submission 2 pending.** The verdict will be recorded in `docs/reviews/DT-01-review-2.md`.
Implementation acceptance is not claimed before that verdict.
```

### Unchanged since submission 1 (hash-pinned pointers)

The round-1 reviewer verified these files; their contents are unchanged and are not copied again.
They remain readable at the listed paths:

```text
c87a149c478ddbcd7322ffbdda723362bda18729da264048be5c3eaa9e58cdbf  backend/app/ingestion/__init__.py
b33cd36ad1a42f9f18720cf11f5d42aea424646ba8ff5b286587995ab2799a1d  backend/app/ingestion/errors.py
eaaec286ca5dddff28914b6e3a431338a4082b17edd703548ec9fda811d6c005  backend/app/ingestion/repository.py
5926759c78412da49573bdb745fb1369db2e3e0786f774eb0556280c9ddbcbd9  docs/architecture.md
```

## 4. Changes since submission 1 (finding dispositions)

| Finding | Severity | Repair | Recheck selectors |
| --- | --- | --- | --- |
| DT01-R1 revision expressions leaked into provenance; reads could mix revisions | major, blocking | `scan_artifacts` now resolves the expression once to a full commit SHA and uses that SHA for `list_paths`, every `read_blob`, and every `Artifact.revision`. | `test_tag_and_sha_ingestion_return_identical_artifacts`, `test_abbreviated_sha_is_pinned_to_the_full_commit`, `test_every_read_uses_the_resolved_commit` |
| DT01-R2 pending identity crossed `Rule:`/`Scenario Outline:` and doc-string text | major, blocking | New declaration-aware state machine: blank lines, comment lines, and additional non-identity tag lines may separate tag and `Scenario:`; any other declaration raises; doc strings are tracked lexically and their contents are data; an unterminated doc string raises. | `test_tag_before_a_rule_does_not_capture_a_nested_scenario`, `test_tag_before_a_scenario_outline_is_rejected_as_unsupported`, `test_doc_string_contents_are_data`, `test_an_unterminated_doc_string_is_rejected` |
| DT01-R3 hand-rolled front matter changed YAML meaning and accepted invalid YAML | major, blocking | Replaced with `PyYAML` `SafeLoader` plus a duplicate-key-rejecting mapping constructor; values must be string scalars; quoted values and comments keep their meaning; invalid YAML raises with the location. | `test_front_matter_parses_quoted_values_and_comments`, `test_front_matter_rejects_invalid_yaml`, `test_front_matter_rejects_non_string_scalars`, `test_quoted_front_matter_values_are_parsed`, `test_invalid_yaml_is_rejected_by_the_scanner` |
| DT01-R4 malformed `@SCN` tokens were silently ignored | major, blocking | `_identity_tokens` validates every reserved-prefix token; `@SCN-99`, `@SCN-001.1`, and a malformed token beside a valid one all raise naming the token and file. | `test_a_malformed_identity_token_is_rejected`, `test_a_malformed_identity_beside_a_valid_one_is_rejected` |
| DT01-N1 `STATUS.md` contradicted itself | minor, nonblocking | Header now names DT-01 as active; SETUP-01/M0 figures are labelled historical; DT-01 results are current. | inspection of `docs/STATUS.md` |

Reproduction before repair: each defect was reproduced from the verdict's exact probe (tag and
abbreviated-SHA scans; `Rule:`/`Scenario Outline:`/doc-string inputs; quoted, commented, and
unterminated YAML; `@SCN-99`). The repairs are the smallest changes that close the exposed defect
class, not special cases for the probe strings.

Regression risk considered: the fixture's own declarations are unchanged, so the parsed artifacts
must still equal the committed snapshot; `fixturectl verify` proves generated bytes are unchanged;
the full suite and the network-denied suite pass.

## 5. Implementation context

* Entry point: `app.ingestion.scan_artifacts(repository, revision, repository_name)`. The revision
  parameter is an expression; the function returns artifacts at one resolved commit.
* `app.ingestion.GitRepository` is read-only (rev-parse / ls-tree -z / cat-file). No write path.
* `tools/fixturectl.py` still owns generation in this story; DT-02 makes it reuse this scanner
  after source/test support lands.
* Targeted reads: `backend/app/domain/models.py` (Artifact), `docs/domain-contracts.md`
  (identity/hash rules), `backend/tests/conftest.py` (`built_fixture`), `tools/fixturectl.py`.
* The committed snapshot `fixtures/api-responses/snapshot.json` is the independent expectation for
  the scan; the hash check uses `fixturectl.git_blob`, not the scanner's hashing.

## 6. Evidence

| Criterion | Check (pytest selector) | Result |
| --- | --- | --- |
| SCN-501 | `tests/test_ingestion_artifacts.py::test_requirement_document_is_parsed_into_an_artifact` | PASS |
| SCN-502 | `::test_scenario_identity_comes_from_the_gherkin_tag` | PASS |
| SCN-503 | `::test_requirement_without_front_matter_is_rejected` | PASS |
| SCN-504 | `::test_untagged_scenario_creates_no_artifact` | PASS |
| SCN-505 | `::test_dangling_scenario_tag_is_rejected` | PASS |
| SCN-506 | `::test_duplicate_artifact_identities_are_rejected` | PASS |
| SCN-507 | `::test_tag_and_sha_ingestion_return_identical_artifacts`, `::test_abbreviated_sha_is_pinned_to_the_full_commit`, `::test_every_read_uses_the_resolved_commit` | PASS |
| SCN-508 | `tests/test_ingestion_parsers.py::test_doc_string_contents_are_data`, `::test_an_unterminated_doc_string_is_rejected` | PASS |
| SCN-509 | `tests/test_ingestion_parsers.py::test_a_malformed_identity_token_is_rejected`, `::test_a_malformed_identity_beside_a_valid_one_is_rejected` | PASS |
| SCN-510 | `tests/test_ingestion_parsers.py::test_front_matter_parses_quoted_values_and_comments`, `tests/test_ingestion_artifacts.py::test_quoted_front_matter_values_are_parsed` | PASS |
| SCN-511 | `tests/test_ingestion_parsers.py::test_front_matter_rejects_invalid_yaml`, `::test_front_matter_rejects_non_string_scalars`, `tests/test_ingestion_artifacts.py::test_invalid_yaml_is_rejected_by_the_scanner` | PASS |
| DoD snapshot equality | `::test_parsed_artifacts_match_the_committed_snapshot_for_requirements_and_scenarios` | PASS |
| DoD malformed parsers | `tests/test_ingestion_parsers.py` (20 tests) | PASS |

Actual invocations and exits, captured 2026-11-13T01:13:09Z–01:13:19Z:

```text
uv sync --project backend --frozen               exit 0  Checked 25 packages
uv run --project backend pytest backend/tests -q exit 0  169 passed, 1 warning in 4.22s
uv run --project backend python tools/fixturectl.py verify  exit 0  reproducible and current
uv run --project backend ruff check .            exit 0  All checks passed
uv run --project backend ruff format --check .   exit 0  all files formatted
git diff --check                                 exit 0
unshare -rn backend/.venv/bin/python -m pytest backend/tests -q  exit 0  169 passed
  (denial proven by a socket probe: OSError [Errno 101] Network is unreachable)
```

NOT RUN: API/HTTP checks (no route added), frontend checks, and general-repository ingestion beyond
the fixture layout. Raw logs are in the external run directory; `IMPLEMENTATION.md` records the
same exits and timestamps.

## 7. File-integrity requirement

The manifest in section 3 is the reviewed snapshot. If any manifest hash changed, the snapshot is
not the one reviewed. Do not edit files, install dependencies, regenerate fixtures, or commit.

## Reviewer instructions (mandatory)

You are the independent CTA implementation reviewer using GPT-6.1 Sol xhigh. Decide whether this exact snapshot satisfies the supplied story, every applicable Gherkin criterion, and repository invariants. Treat OMP's summaries and test results as claims to check against the supplied artifacts and targeted source inspection. Check proposal/accepted/evidence separation, real port compatibility, revision/content-hash semantics, honest errors/501s, independent oracle expectations, offline defaults, and generated-file discipline where relevant. Do not demand implementation of a later milestone. Do not edit files, implement repairs, regenerate fixtures, commit, or delegate. Ask OMP for missing runtime evidence; distinguish observed defects from hypotheses and unavailable checks. Return an AC-by-AC PASS, FAIL, or NOT VERIFIED assessment and actionable findings with stable IDs, severity, blocking status, AC/invariant, path/line, expected/actual behavior, and smallest correction/recheck. Keep optional suggestions and unrelated pre-existing defects separate. Return exactly one verdict: APPROVE, REQUEST_CHANGES, or NEEDS_INPUT. APPROVE requires every applicable criterion/check to be satisfied, no unresolved blocker, and the exact snapshot identified. In later rounds verify prior dispositions and regressions while retaining the complete acceptance assessment. A passing process, passing tests, or exhausted review limit is not approval. Agent review cannot attest human labeling or human link decisions.
