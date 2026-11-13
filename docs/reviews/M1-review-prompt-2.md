# M1 milestone exit review — submission 2 of 7

## 1. Scope

**Milestone:** M1 — AI-free vertical slice (roadmap §7).
**Exit criterion (verbatim):** "Demo `REQ-001` digital thread and one intentionally missing link
end-to-end; all tests run without GPU/embedding dependency."
**Integrated code snapshot:** `29df1050aea4ad8b0b42041fd519636a6b0b7794` (`main`, after the AS-04 merge).
**Review tree:** `e1497cfd91626709195035154e50a6003681f681` (`main`, after the round-1 repairs).
**Prior verdict:** `docs/reviews/M1-review.md` — **NEEDS_INPUT** (submission 1): all 40 story
criteria and the M1 engineering exit PASS at `29df105`; **M1-E1** (blocking evidence: retained
hosted-CI results), **M1-N1** (nonblocking: findings OpenAPI description), **M1-N2** (nonblocking:
packet digest duplication). This submission supplies the dispositions below; product behavior is
unchanged from `29df105` except the findings-description string.

A milestone approval requires every M1 story criterion and the exit criterion to be satisfied at this
snapshot, with no open major finding.

### Stories in scope

| Story | Issue | Canonical criteria | Task verdict |
| --- | --- | --- | --- |
| DT-01 requirements/scenarios | [#20](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/20) | `docs/stories/DT-01.feature` | APPROVE, `docs/reviews/DT-01-review-5.md` |
| DT-02 source/test artifacts | [#21](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/21) | `docs/stories/DT-02.feature` | APPROVE, `docs/reviews/DT-02-review-4.md` |
| DT-03 typed links | [#22](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/22) | `docs/stories/DT-03.feature` | APPROVE, `docs/reviews/DT-03-review-2.md` |
| DT-04 requirement thread | [#23](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/23) | `docs/stories/DT-04.feature` | APPROVE, `docs/reviews/DT-04-review-2.md` |
| AS-01 missing-link findings | [#2](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/2) | `docs/stories/AS-01.feature` | APPROVE (+ nonblocking AS01-R1, repaired), `docs/reviews/AS-01-review.md` |
| AS-04 findings/coverage UI | [#26](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/26) | `docs/stories/AS-04.feature` | APPROVE, `docs/reviews/AS-04-review-3.md` |

Merged commits: `26a25d0` (DT-01), `590e776` (DT-02), `0970f7a` (DT-03), `c43541b` (DT-04),
`d238776` (AS-01), `29df105` (AS-04). All six issues are closed. Hosted CI on the integrated commit
(run `43370472013`): Commit references, Offline tests, and Frontend tests all success — raw evidence
below.

## 2. Round-1 dispositions

| Finding | Severity | Disposition |
| --- | --- | --- |
| M1-E1 hosted required checks not retained | medium, blocking evidence | Raw `gh run view 43370472013` and the commit check-runs API are committed at `29df105`; the full SHA, completed/success status, and all three job conclusions are reproduced below. Files: `evidence/hosted-ci-43370472013.json`, `evidence/check-runs-29df105.json`, `evidence/hosted-checks.txt`. |
| M1-N1 findings OpenAPI description stale | low, nonblocking | `backend/app/api/routes.py` now describes the implemented M1 rule subset (missing verification links) and the AS-02/AS-03 deferral. Backend suite and ruff re-run: `evidence/repair-checks.txt`, 233 passed. |
| M1-N2 stale duplicate report digest in the packet | low, nonblocking | This packet uses exactly one manifest block with current digests; every line was checked against the tree. |

### Hosted CI evidence (verbatim capture)

```text
captured_utc=2026-11-13T05:59:41Z
cmd=gh run view 43370472013 --repo anthonygraca/gherkin-knowledge-graph --json headSha,status,conclusion,jobs,url,createdAt,updatedAt,event,displayTitle
exit=0
{"headSha":"29df1050aea4ad8b0b42041fd519636a6b0b7794","status":"completed","conclusion":"success","event":"push","url":"https://github.com/anthonygraca/gherkin-knowledge-graph/actions/runs/43370472013","jobs":[{"name":"Offline contract, fixture, and API tests","conclusion":"success"},{"name":"Commit references","conclusion":"success"},{"name":"Frontend build and component tests","conclusion":"success"}]}
cmd=gh api repos/anthonygraca/gherkin-knowledge-graph/commits/29df105.../check-runs
exit=0
{"total_count":3,"checks":[{"name":"Frontend build and component tests","status":"completed","conclusion":"success","head_sha":"29df1050aea4ad8b0b42041fd519636a6b0b7794"},{"name":"Commit references","status":"completed","conclusion":"success","head_sha":"29df1050aea4ad8b0b42041fd519636a6b0b7794"},{"name":"Offline contract, fixture, and API tests","status":"completed","conclusion":"success","head_sha":"29df1050aea4ad8b0b42041fd519636a6b0b7794"}]}
```

## 3. Snapshot, manifest, and captured checks

Manifest (sha256 of the six features, contracts, code, frontend, docs, task verdicts/reports,
fixture identity, demo evidence, and round-1 repair evidence):

```text
3a1b1a4fb55653d5162719932b8fc084e11476f8145b0fe59a3ed7727a15b4c1  .github/workflows/ci.yml
c0a6da4403d7ef2131842c47d458585add2b3f6b484a611c7cae70fcb0524eea  backend/app/api/__init__.py
fb9b493481e405cb86d964744378bb04c4a2436ae4ddfcf91b0bbaa7dc9f45a9  backend/app/api/deps.py
5a5412e1ace2649e51aa1118b0f85fc291f7efa3c2d49ddb0982b4ebdeb77896  backend/app/api/errors.py
be2a54eeb1425e1260ba0d3ee44a1473e0423f54622241a7f893b8b1d688b2bf  backend/app/api/routes.py
4228de874bf9cb7f2992da45b70bd75565f4a60c94b55eb6037f45379c5f40dd  backend/app/assurance/__init__.py
adf0fd7707f95343f4cd75ce9f476598cf368fb53e0dc88988a953df18f4d008  backend/app/assurance/rules.py
95ffcff97f0c3d806ac2257ade5cee8014d3ef600e84b163314d1831f2870e85  backend/app/assurance/sample_findings.py
e3b54915a0656cb3a9d55bf61c5e31d891ca903e852c7410e366d307bcdc8e63  backend/app/domain/__init__.py
b486374b06ad0f1f6492a95b8a2af2a0c52b27039011e8566f13d75762a0f65d  backend/app/domain/api.py
a2464c7f2edba85f8af1dac6af24efc4a05693fef6188ab6948fb2be4cb554c2  backend/app/domain/enums.py
3daa531c3c3c74fd2d50ef82e65bf69b96cb018970479399eb70b5c21c4073be  backend/app/domain/errors.py
85b138bf96155db66c9a2226703a5772c3c577d727b93253cb05993cade67f0f  backend/app/domain/models.py
679eea69414764999a4770725c01000521bbd508135840359ae5949e297e7889  backend/app/domain/oracle.py
193a0639ae4cd693ca4c7dcb1ed06d46b1e2bd20f4346dbb2f96f3a055359145  backend/app/domain/policy.py
17e65def989f2c24c5f4a7dc8514fe9c9e6c72b1a1eb52602f174de45292382d  backend/app/domain/ports.py
4200999207d79bffbd59cd30b72959b2039c4b1067e827087ee75b037918ea0e  backend/app/ingestion/__init__.py
b33cd36ad1a42f9f18720cf11f5d42aea424646ba8ff5b286587995ab2799a1d  backend/app/ingestion/errors.py
88db8934b47d78f2256a40b6f5bfca0e72cc062a4c297b282a66c0242ae385cf  backend/app/ingestion/evidence.py
3c284b7e421182507ff0b7443b3b1ff036553ec8dc8b0ad1fdfaa497704f4aed  backend/app/ingestion/links.py
80554d82097e88b0e83bf4b535aafd843359bec5e0cc956ea8cd0eb2ab232e1c  backend/app/ingestion/parsers.py
eaaec286ca5dddff28914b6e3a431338a4082b17edd703548ec9fda811d6c005  backend/app/ingestion/repository.py
761fee3b1944516158773161b49747b6430853f7456d3c6be7028a148c783f07  backend/app/ingestion/revision.py
2a602ee3668bd1560e42aa8870c6a1875b3977a082d449109892852c73e0a613  backend/app/ingestion/scan.py
e930e3043bb952c63ac3d9afb05bf7227ea3437284946188083187a04a4d47a4  backend/app/ingestion/thread.py
7ebd1e5f9a943fd027167ec8e23c0e236efd12f09e34ab9c598a29643ce0bd7e  backend/app/main.py
b97341218d37c7f2ae78f03f2259478ab4b321f658cee0737a14397e9488c064  backend/app/persistence/__init__.py
7cf4a242acd13e0e1d5a687a6def15570505df59d5dcedec2468580bfad22888  backend/app/persistence/fixtures.py
5aa0cac1fa9bc5ccc997c9d6a335de42e6e0f0ef984e0ad82b64fb7e85535e44  backend/app/persistence/ingested.py
397de92385a945305a221da84f98841dd031281c64acc3c1f96c87055d749341  backend/app/settings.py
cd722cd24a15b23666731258391f8b6c1d1b943838248f3d81df6e5f3cf8275b  backend/app/version.py
bd18be5bbf7df3fba479a2b35daef1dc09f38e2c0d358f2ca4ebe4d686476711  docs/STATUS.md
8134ad961dbbd6ee2031977b2893efad82ba7c21e35febe6563b27eda9be27a0  docs/api-contracts.md
d81c78a672a65843ff9d7133b1cf55037d6a2bbb3b12859c33feb10a5a6153e9  docs/architecture.md
9a33f65da79f96148b36ee03ebc4f8dbe05cfa8e039297e36d922a073e94c165  docs/domain-contracts.md
f102ad9130fdb985bd9451f05ffd28ba0dc658bb21070de8a0b664db28991469  docs/reports/omp-as-01-missing-link/IMPLEMENTATION.md
740f12ebb908c52f44e8e35071d410759d659a6cb63a045e1d843b6fecf87f1a  docs/reports/omp-as-04-summary/IMPLEMENTATION.md
777e5f2e2d9850b2eaae7b768d4411b9ed78ae4e9672fee729eb20e0930d8812  docs/reports/omp-dt-01-ingestion/IMPLEMENTATION.md
60667be0f7bfdd0f64033ed70ec196c4d99e4075162cca2f4b51bdb719459387  docs/reports/omp-dt-02-artifacts/IMPLEMENTATION.md
76047e33f62a5d00704712a0cf100529fc6a30c18417c5679df0342744cb8d59  docs/reports/omp-dt-03-links/IMPLEMENTATION.md
4cded01b774e0f7d66f9b827ed81a6062a8111a2e67e33fc552773bef48b658e  docs/reports/omp-dt-04-thread/IMPLEMENTATION.md
a2464e1efe3f568ed11232e73a513fdb9aa0764b33aa6492b83738abbc0084ae  docs/reports/omp-m1-milestone/IMPLEMENTATION.md
b71a773a40b4173911e99b04bb8f7ddfd58df09f77046fd65711ee31cc7c3542  docs/reports/omp-m1-milestone/evidence/check-runs-29df105.json
f9bda8eef11065adc15a87419323597a45a85fff50db280dd0d8c1e5b1a28069  docs/reports/omp-m1-milestone/evidence/checks-frontend.txt
2547d2c809b6a554757d59350e207afdda0fbf429707d8694089f203fc4ff4a4  docs/reports/omp-m1-milestone/evidence/checks.txt
25eeac63a3fca1b1f238041fb71fd7f48824192833082e324e921dbd384c97fb  docs/reports/omp-m1-milestone/evidence/commitlint.log
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  docs/reports/omp-m1-milestone/evidence/diffcheck.log
c0a4c5e9c37772b73119d3aca0e9ed372104f77b552ec18a532973cd849da584  docs/reports/omp-m1-milestone/evidence/fixturectl.log
7df18b42c43329c0833da621f67724dca7a56dfff20a450ae0336efb05e24f06  docs/reports/omp-m1-milestone/evidence/format.log
d7cf729269079a37e98e0ab252cd2ee8b39e533f1f404d41216ccb9ebf97f02c  docs/reports/omp-m1-milestone/evidence/hosted-checks.txt
92cc76b0476f41ea7b2184e25d18ecdab64aeb373c3d78435f97d3623b5d9943  docs/reports/omp-m1-milestone/evidence/hosted-ci-43370472013.json
2bb42d03c7ba6dc990616737f67bde90264927577c4b95dd90a87da7b9cc7556  docs/reports/omp-m1-milestone/evidence/http-artifacts-a.json
b2327f6ce41e2692d6925c47b30bea0480b5f65d1655584c2047f39640a9879c  docs/reports/omp-m1-milestone/evidence/http-evaluate-a.json
e862331f31ade26df577363232e18cc542952be87f4737b71bf220c71e3479a6  docs/reports/omp-m1-milestone/evidence/http-evaluate-b.json
efed98a5f02ccdb926cc6966469a85ad9e9ed3b266739d9b248d04f3fc3811b0  docs/reports/omp-m1-milestone/evidence/http-findings-a.json
4369db82a996fcd97b31e55f802c893b1d305c826d6b5c5dd16b8cab34dd7772  docs/reports/omp-m1-milestone/evidence/http-health.json
3ff8a3d1a56f2c460f263055826d3370f0ca7e2dd5ac5e36dae642e3aa9b06a1  docs/reports/omp-m1-milestone/evidence/http-ingestion-a.json
b683afcc89c91f91ad7cd12a205b126d4db0ab6ff91c768d9e5f47dc963edfcb  docs/reports/omp-m1-milestone/evidence/http-thread-req001-b-sha.json
b683afcc89c91f91ad7cd12a205b126d4db0ab6ff91c768d9e5f47dc963edfcb  docs/reports/omp-m1-milestone/evidence/http-thread-req001-b.json
6150fa2356813c46a0b940b7c110695000537314ac65c4c9ae5fa33765c1e6a9  docs/reports/omp-m1-milestone/evidence/m1-proposals-req-002.png
fb95acee7bdd2a981f3d632489bb81e795aef3761aaedd564e290647e7a52bed  docs/reports/omp-m1-milestone/evidence/m1-summary-baseline-a.png
150295d610a97195bbf285e5f324c5a72fdab567a8b78215a2f14711883a829a  docs/reports/omp-m1-milestone/evidence/m1-summary-mobile.png
de3d3b2929d41f6991064807e39d14a4bdf662e0e084836db48039ae0004ad03  docs/reports/omp-m1-milestone/evidence/m1-thread-req-001-baseline-b.png
cd345a739335f126a136d84dfaf2f7258e8988e8e0a098822156cb16250baee5  docs/reports/omp-m1-milestone/evidence/network-probe.log
51397156ceaf348be1570b9fff6f95ab84d8bd3ca27c6931ac24ea0ad6d16ad3  docs/reports/omp-m1-milestone/evidence/npm-build.log
38462875ef3d359de1da96b435743ac6d4540bcfdd7bc5d526311e5f23a4dccb  docs/reports/omp-m1-milestone/evidence/npm-test.log
3560ce549af18dcd2fce04bd4100c814f870cca624e444c6501dc29f35948832  docs/reports/omp-m1-milestone/evidence/pytest-full.log
854722cbf74c04095f38564d5cbe9f10d3a9245eba26d9738c84db53a630af44  docs/reports/omp-m1-milestone/evidence/pytest-network-denied.log
649301e74785a5e78074b81d42931afa1c7d649ccbd27da6f982145ba008f8b6  docs/reports/omp-m1-milestone/evidence/repair-checks.txt
e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  docs/reports/omp-m1-milestone/evidence/repair-diff.log
7df18b42c43329c0833da621f67724dca7a56dfff20a450ae0336efb05e24f06  docs/reports/omp-m1-milestone/evidence/repair-format.log
f6383f2741cc95861d4f7459319fbf0a9c9bada5edcd83a19e1c2f196478cd75  docs/reports/omp-m1-milestone/evidence/repair-pytest.log
82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18  docs/reports/omp-m1-milestone/evidence/repair-ruff.log
82b3e6a6c090a57601d22943bd23fca9218d1031dbe5a7b754092f9a156b4f18  docs/reports/omp-m1-milestone/evidence/ruff.log
8aa350fb904269914661329bfd2c445d0e7406a75e1826ca6279b353587f9bfc  docs/reviews/AS-01-review.md
de6237169468110e7ca15d09e83c9bfa4b00aded94193c385560b5beeb95fb27  docs/reviews/AS-04-review-3.md
1017e5cc7462d4c4e92d4a14ceea90bf75c32ddb9a414f32aea588c304c992c2  docs/reviews/DT-01-review-5.md
cf58c19b1296d330760bd8c34e15e00ec41fa977e83753802a316e48e748b201  docs/reviews/DT-02-review-4.md
96dbb2effd6a471a08da2bb2fc03075ec57f8c5f90190f2dcd79976567140bfb  docs/reviews/DT-03-review-2.md
308e7abd7a524220d69d4f0716a6cff48de992c90bb74f3832d7333c4c3f135d  docs/reviews/DT-04-review-2.md
064ebfa3ab0d41c241790a21d51602ab95255df6b852a9dae7499b7cc95f06b8  docs/reviews/M1-review.md
66547bba1717b2338557e503d9700aa3606d995c98f13b2bd1bc89adae2fdca0  docs/setup.md
835b6d313960624402eccdcf4b51ca5c87ee790ec0249df7a7e72a0ec95a8c85  docs/stories/AS-01.feature
44f0ce7d64cdd2f80fa093a0adcdd5964821c5fa4102abbccf503dc7484d6f6e  docs/stories/AS-04.feature
5517104a2cfffe255304ff5fc4e67a5186150f6c54c1456e21d8bb7b10bf4b4d  docs/stories/DT-01.feature
08c0e96d371724a9d640cefdc1e07d060e7c72cbfe141877022d662489d90e8a  docs/stories/DT-02.feature
d6e390d908616388cbc69ae2dbabd5371ef6a15115a83b447f7696dbf6c83200  docs/stories/DT-03.feature
02301bee448f33efc07d9e0e1d37ccafa1d1a2b9a9bd303bfa622a0fd5eb94e9  docs/stories/DT-04.feature
3aa2987be0c85299f40ec609f6ee8684e4eaceebb52f7723b8d85cd2b99a6a82  fixtures/api-responses/snapshot.json
7b0eccbdfb2575b07eea414d966a22638394c2ea65d33e9b7b5a976f557116ac  fixtures/banking-demo/expected/baselines.json
5fd857b362d57ef48f0ff8862d474770ad5dc98d33c944bc64734dacd1591bac  frontend/package-lock.json
7d82d45f0d7bd214b9a014d89ed696ca0c32550bd4b81c3cbfaccc1866908315  frontend/package.json
7317566625f28486211673a0e0b42f7bcc5600b9103c775fa541710a46148fc2  frontend/src/App.test.tsx
0ed430a622b6dc3acce7e5f5666ee0a7258034fe8c338a4a01d91d9b4c1de446  frontend/src/App.tsx
edfa55c6421cacbb2f1e1408e84a7b85b946ed3588670d494e0cd9a9326c86b5  frontend/src/api.ts
22d7c55129eee011cdff3123a98e69adf86b3b534ec97371d8e2cb16c3b1a772  frontend/src/styles.css
6169bbac5bb00fde197aefd3fbedede17dc33403042059d7de1d3cc3b26f08df  frontend/src/types.ts
bde007f1fd26fa27cc068f64d8c02ee388ee08d22c7d4a15b211c0cd5870d7d1  frontend/vite.config.ts
0072e017e27ff488b575300f1be324efe0a11ef7f84e92a5b960df210ac7bcae  tools/fixturectl.py
```

Captured checks at the integrated code snapshot `29df105`:

```text
commit=29df1050aea4ad8b0b42041fd519636a6b0b7794
captured_start=2026-11-13T05:13:37Z
cmd=uv run --project backend pytest backend/tests -q
exit=0
cmd=uv run --project backend python tools/fixturectl.py verify
exit=0
cmd=uv run --project backend ruff check .
exit=0
cmd=uv run --project backend ruff format --check .
exit=0
cmd=git diff --check
exit=0
cmd=python tools/commitlint.py
exit=0
probe_captured=2026-11-13T05:13:45Z
cmd=unshare -rn backend/.venv/bin/python (socket probe)
exit=0
cmd=unshare -rn backend/.venv/bin/python -m pytest backend/tests -q
exit=0
captured_end=2026-11-13T05:13:53Z
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
233 passed, 1 warning in 6.78s
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
233 passed, 1 warning in 6.68s
DENIED: OSError: [Errno 101] Network is unreachable
cmd=npm run build
exit=0
cmd=npm test
exit=0
dist/assets/index-DA71Skzm.js   230.90 kB │ gzip: 71.95 kB
✓ built in 1.27s
      Tests  10 passed (10)
   Start at  21:13:58
   Duration  2.24s (transform 143ms, setup 90ms, collect 244ms, tests 818ms, environment 554ms, prepare 112ms)

```

Round-1 repair recheck (OpenAPI description; no behavior change):

```text
captured_start=2026-11-13T06:01:16Z
cmd=uv run --project backend pytest backend/tests -q
exit=0
cmd=uv run --project backend ruff check .
exit=0
cmd=uv run --project backend ruff format --check .
exit=0
cmd=git diff --check
exit=0
captured_end=2026-11-13T06:01:25Z
-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
233 passed, 1 warning in 7.93s
```

## 4. Canonical acceptance criteria (full snapshots)

### DT-01
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
    And an opening delimiter line never also closes the same doc string
    And an unterminated doc string is an error

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

### DT-02
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

### DT-03
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

### DT-04
```gherkin
# Canonical acceptance specification for DT-04 (#23), M1.
# Source criteria: the GitHub story intake at
# https://github.com/anthonygraca/gherkin-knowledge-graph/issues/23 (verified 2026-11-13T03:12:49Z)
# and roadmap §6 F-03. Failure, boundary, and cutover scenarios were added during refinement; the
# two intake scenarios keep their wording.
# Verified by the pytest selectors mapped in DT-04.md. These scenarios are not currently bound
# to or executed by a Gherkin runner.
@DT-04 @issue-23 @M1
Feature: DT-04: Retrieve the thread associated with a requirement
  A thread is assembled from the ingested revision: the requirement, the accepted links reachable
  from it, the artifacts those links reach, and the evidence for the scenarios and tests in the
  thread. Proposals remain a separate array. The response is independent of tag-vs-SHA wording and
  of any precomputed example file.

  @SCN-611
  Scenario: Thread for a fully linked requirement
    Given the fixture repository is ingested at "baseline-b"
    When the thread for "REQ-001" is requested
    Then the response contains "REQ-001", "SCN-001", "CODE-001", and "TEST-001"
    And the accepted links "LNK-001", "LNK-002", and "LNK-003"
    And the evidence recorded for "SCN-001"
    And the response is identical whether the baseline is given as the tag or the commit SHA

  @SCN-612
  Scenario: Thread for a requirement with only a proposal
    Given "REQ-002" has no accepted links
    When the thread for "REQ-002" is requested
    Then "accepted_links" is empty
    And "LNK-007" appears only in "proposed_links"

  @SCN-613
  Scenario: The thread is assembled from the ingested revision
    Given the committed thread example files are unavailable
    When the thread for "REQ-001" is requested
    Then the same thread is served from parsed repository data
    And its schema_version matches the running contract

  @SCN-614
  Scenario: Unknown and non-requirement roots are documented 404s
    Given "REQ-999" does not exist
    When its thread is requested
    Then the response is 404 "artifact-not-found"
    And a thread for an existing source artifact "CODE-001" is 404 "thread-not-found"

  @SCN-615
  Scenario: Re-ingesting a revision reports what it found
    Given the fixture repository at "baseline-a"
    When an ingestion run is requested
    Then it reports the artifact, accepted-link, proposed-link, and evidence counts
    And its run id is deterministically derived from the resolved commit

  @SCN-616
  Scenario: Artifact inventory for a baseline
    Given the fixture repository is ingested at "baseline-a"
    When artifacts are listed for that baseline
    Then every requirement, scenario, source, and test artifact is returned
    And filtering by artifact type returns only that type
```

### AS-01
```gherkin
# Canonical acceptance specification for AS-01 (#2), M1.
# Source criteria: the GitHub story intake at
# https://github.com/anthonygraca/gherkin-knowledge-graph/issues/2 (verified 2026-11-13T03:56:41Z)
# and roadmap §6 F-05. Boundary and failure scenarios were added during refinement; the intake
# scenario keeps its wording.
# Verified by the pytest selectors mapped in AS-01.md. These scenarios are not currently bound
# to or executed by a Gherkin runner.
@AS-01 @issue-2 @M1
Feature: AS-01: Missing coverage/link findings
  A requirement is missing verification when it has no accepted `verified_by` link to an existing
  scenario at the evaluated baseline. A proposal is not acceptance. The rule is deterministic,
  offline, and explains its inputs and simplifying assumptions.

  @SCN-701
  Scenario: Requirement has no accepted verification scenario
    Given requirement "REQ-002" exists
    And no accepted verification scenario is linked to "REQ-002"
    When assurance evaluates baseline "baseline-a"
    Then a "missing_verification_link" finding is produced for "REQ-002"

  @SCN-702
  Scenario: A pending proposal does not satisfy the rule
    Given "LNK-007" proposes "REQ-002" verified_by "SCN-002" and is not accepted
    When assurance evaluates baseline "baseline-a"
    Then "REQ-002" still produces a "missing_verification_link" finding
    And the proposal is not counted as an accepted link

  @SCN-703
  Scenario: A requirement with accepted verification has no such finding
    Given "REQ-001" has accepted link "LNK-001" verified_by "SCN-001"
    When assurance evaluates baseline "baseline-a"
    Then no "missing_verification_link" finding names "REQ-001"

  @SCN-704
  Scenario: Findings identify their rule, inputs, and evaluated baseline
    Given assurance evaluated baseline "baseline-b"
    Then each finding names the rule id, severity, artifact revisions, and resolved commit
    And the finding fingerprint follows the canonical rule-and-artifact inputs

  @SCN-705
  Scenario: Unusable evaluation requests are rejected honestly
    When assurance is asked for baseline "baseline-z"
    Then the response is 404 "baseline-not-found"
    When assurance is asked for an unknown policy
    Then the response is 400 "invalid-request"
```

### AS-04
```gherkin
# Canonical acceptance specification for AS-04 (#26), M1.
# Source criteria: the GitHub story intake at
# https://github.com/anthonygraca/gherkin-knowledge-graph/issues/26 (verified 2026-11-13T04:13:19Z)
# and roadmap §6 F-06. Boundary scenarios were added during refinement; the two intake scenarios
# keep their wording. Verified by frontend component tests plus a recorded browser demonstration;
# the scenarios are not executed by a Gherkin runner.
@AS-04 @issue-26 @M1
Feature: AS-04: Summary of findings and coverage counts
  The dashboard shows, for the selected baseline, how many findings of each type exist and which
  requirements are covered. Counts come from the findings response. Proposals are displayed as
  proposals and never counted as coverage.

  @SCN-801
  Scenario: Coverage summary for a baseline
    Given the fixture data at "baseline-a"
    When the dashboard loads the summary
    Then it shows the finding counts by type for that baseline
    And it shows "REQ-001" as fully covered
    And it shows "REQ-002" as missing a verification scenario

  @SCN-802
  Scenario: The baseline is always visible
    Given findings for "baseline-a" and "baseline-b" differ
    When the baseline selector changes
    Then the summary reloads for the selected baseline
    And the selected baseline is displayed with the numbers

  @SCN-803
  Scenario: Counts are derived from the response, not hard-coded
    Given a findings response containing a different set of findings
    When the dashboard renders it
    Then the displayed counts change accordingly

  @SCN-804
  Scenario: Proposals are labelled and excluded from coverage
    Given "REQ-002" has proposed link "LNK-007" and no accepted verification link
    When its thread is displayed
    Then "LNK-007" is labelled as a proposal
    And "REQ-002" is not shown as covered

  @SCN-805
  Scenario: The thread view shows the accepted chain and its evidence
    Given the fixture data at "baseline-b"
    When the thread for "REQ-001" is displayed
    Then the accepted links and their relation types are shown
    And the evidence for "SCN-001" is shown
    And the baseline is shown with the thread
```

The per-story implementation records and independent verdicts (hash-listed above) carry the
AC-to-check tables. The M1 run record is
`docs/reports/omp-m1-milestone/IMPLEMENTATION.md`.

## 5. Scope limits and separate gates

* **Stakeholder validation** of the demo has not been attested by the owner; this review cannot
  supply it. It is a lifecycle release/validation gate, separate from the M1 engineering exit.
* The draft `docs/project-definition.md` and the M0 feature-extraction/mapping reviews remain owner
  dispositions; M1 stories derive from the roadmap.
* Tracker closure of #18/#19, the required-status-check ruleset, and the README work item are owner
  actions outside this review.
* Hosted CI on the integrated commit is green; browser automation is not part of CI.
* No M2+ behavior (staleness/failure rules, full findings switch, link review, real embeddings) is
  claimed or required here.
* `GET /api/findings` intentionally replays the reviewed sample until the rule set is complete;
  `POST /api/assurance/evaluate` implements the M1 rule only. Do not treat this as hidden M2 work.

## Reviewer instructions (mandatory)

You are the independent CTA milestone reviewer using GPT-6.1 Sol xhigh. Decide whether the exact
integrated snapshot satisfies every M1 story acceptance criterion and the roadmap M1 exit criterion,
and whether the repository invariants hold. Treat OMP's summaries and test results as claims to check
against the artifacts and targeted source inspection. Do not demand later-milestone implementation.
Do not edit files, implement repairs, regenerate fixtures, commit, or delegate. Ask OMP for missing
runtime evidence; distinguish observed defects from hypotheses and unavailable checks. Return a
criterion-by-criterion PASS, FAIL, or NOT VERIFIED assessment, actionable findings with stable IDs,
severity, blocking status, path/line, expected/actual behavior and smallest correction/recheck, and
exactly one verdict: APPROVE, REQUEST_CHANGES, or NEEDS_INPUT. APPROVE requires every M1 criterion and
the exit demo to be satisfied at this snapshot, no open major finding, and green required checks.
This approval does not attest human stakeholder validation, human labels, or release authorization.
