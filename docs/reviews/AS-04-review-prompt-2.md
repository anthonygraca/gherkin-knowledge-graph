# Independent implementation review — AS-04, submission 2 of 7

## 1. Submission context and prior dispositions

**Task:** AS-04 — Summary of findings and coverage counts.
**Roadmap:** F-06 UI, roadmap §6 AS-04; milestone **M1 — AI-free vertical slice**.
**GitHub story:** issue **#26**, verified OPEN 2026-11-13T04:13:19Z. **Owner:** C.
**Repository:** `<task_repo>` (read-only sandbox).
**Base:** `d238776bf0b53e6963f8e81721ce9a106f848adb` (`main`, AS-01 merge).
**Branch:** `feat/26-as-04-summary-ui`. **Submission:** 2 of 7.

Round 1 (`docs/reviews/AS-04-review.md`) returned REQUEST_CHANGES:

* **R1** — a baseline change could display the previous baseline's counts/coverage under the new
  baseline; failures were indistinguishable from empty success.
* **R2** — a selection change could display the previous requirement's chain under the new
  heading; baseline changes had the same exposure.
* **N1** — the count test checked category disappearance, not a changed numeric count.

All three are addressed; none was dismissed.

### User outcome

A lead can choose a baseline, see findings counts and per-requirement coverage, and inspect a
requirement's thread with accepted links, proposals, and evidence — offline.

### Scope / non-goals (unchanged)

React + TypeScript + Vite dashboard, baseline selector, summary/coverage, thread view, component
tests against committed fixtures, frontend CI job, setup docs, browser demonstration. Includes the
AS01-R1 test-strength repair. Non-goals: link review, computed assurance in the UI, auth,
deployment.

### Proposed commit references

1. `test(assurance): [issue #2] bind finding revisions to the manifest tag`, body `Refs #2`.
2. `feat(ui): [issue #26] show findings summary and requirement threads`, body `Refs #26`.

## 2. Acceptance criteria (canonical snapshot)

File `docs/stories/AS-04.feature`, sha256
`44f0ce7d64cdd2f80fa093a0adcdd5964821c5fa4102abbccf503dc7484d6f6e` (unchanged).

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

Refinement disposition: owner-authored issue intake + roadmap §6; boundary scenarios were added.
No separate human refinement sign-off is recorded.

Repository constraints (AGENTS.md): offline test execution; counts derived from responses; proposals
never counted as coverage; no model calls; no hand-edited generated files.

## 3. Snapshot and manifest

Snapshot captured 2026-11-13T04:44Z. Manifest (sha256 of every task file, including screenshots):

```text
7d82d45f0d7bd214b9a014d89ed696ca0c32550bd4b81c3cbfaccc1866908315  frontend/package.json
5fd857b362d57ef48f0ff8862d474770ad5dc98d33c944bc64734dacd1591bac  frontend/package-lock.json
bde007f1fd26fa27cc068f64d8c02ee388ee08d22c7d4a15b211c0cd5870d7d1  frontend/vite.config.ts
770b4140bbb581e2dfd9ea9946ffc9c75a1d86ba7d2db5f77c83e37cbdf9d808  frontend/tsconfig.json
3bee9baf0672e6e0de5fe433bc6ec75ef31eb87f3b319b1111afaac0864d0e28  frontend/tsconfig.app.json
3ced5d22ba9e246c839a695526296a8d067fbe9db838d728516d2eac9215b333  frontend/tsconfig.node.json
4e00b5c1e7c64dfbeb8aa8fca0d0acc71be382a17960305e256c1b76a3f765f2  frontend/index.html
8d45c6682d85e8e9e12422aabf59d7c8ff8ea3057409cbce1fadf47579d221f2  frontend/src/App.test.tsx
067fc9811101f6e0fea84e04568b2da5f87b8b579e8a28117c8562b466b96504  frontend/src/App.tsx
704cd9cb2b4b80f3c9d53ffb1a11273c6a4ea59bcd2c64df0920b3659561adfd  frontend/src/main.tsx
edfa55c6421cacbb2f1e1408e84a7b85b946ed3588670d494e0cd9a9326c86b5  frontend/src/api.ts
9b328c4843431fa76d8de00008fc159e95f99a840211085ff3b8f25e53d14409  frontend/src/test-setup.ts
6169bbac5bb00fde197aefd3fbedede17dc33403042059d7de1d3cc3b26f08df  frontend/src/types.ts
22d7c55129eee011cdff3123a98e69adf86b3b534ec97371d8e2cb16c3b1a772  frontend/src/styles.css
3a1b1a4fb55653d5162719932b8fc084e11476f8145b0fe59a3ed7727a15b4c1  .github/workflows/ci.yml
66547bba1717b2338557e503d9700aa3606d995c98f13b2bd1bc89adae2fdca0  docs/setup.md
d81c78a672a65843ff9d7133b1cf55037d6a2bbb3b12859c33feb10a5a6153e9  docs/architecture.md
5b3c32843c8ddb72ee016635e22075c0ed2a7ef3e5e38e24ed2c3c039fc00f2a  docs/STATUS.md
784361e690a18ebcbeebb3b47f403825a5fefd371068e1067b6fda907f613067  backend/tests/test_assurance_rules.py
44f0ce7d64cdd2f80fa093a0adcdd5964821c5fa4102abbccf503dc7484d6f6e  docs/stories/AS-04.feature
a90650fc994157f39bece4d6e5a57864b46806264084f15445e44b30dcad3ea1  docs/stories/AS-04.md
d2ba3c5b88fd3166b887fe4ce6acec052c272edff0082f92a922bb6aed307eb0  docs/reports/omp-as-04-summary/IMPLEMENTATION.md
5626a0b9201887321ee37ddebad7033725f59a71f61454731490a259eeb71f3a  docs/reports/omp-as-04-summary/PROMPT_LOG.md
4aad64b495c6c0c951836077c0cfa35a581b2be5cd9ef8a192ebf5d4b9091081  docs/reports/omp-as-04-summary/METRICS.md
a8428945cdd9762ed7c7d59529491e4c0969c8cea11e1565f136735ede92ff30  docs/reports/omp-as-04-summary/evidence/summary-baseline-a.png
150295d610a97195bbf285e5f324c5a72fdab567a8b78215a2f14711883a829a  docs/reports/omp-as-04-summary/evidence/summary-mobile-390.png
de3d3b2929d41f6991064807e39d14a4bdf662e0e084836db48039ae0004ad03  docs/reports/omp-as-04-summary/evidence/thread-req-001-baseline-b.png
6150fa2356813c46a0b940b7c110695000537314ac65c4c9ae5fa33765c1e6a9  docs/reports/omp-as-04-summary/evidence/thread-req-002-proposals.png
ebbbd1675777be9c361e5e842b113777e96da659c8b0310fc18a092160312be1  docs/reviews/AS-04-review.md
42253195ead218481771136b405be228d88a613e356d2f0d4a5aae7a28f68b30  docs/reviews/AS-04-review-prompt.md
```

`SCHEMA_VERSION = 0.2.0`, `PACKAGE_VERSION = 0.1.0`. No backend product change; the AS01-R1 test
assertion is included.

## 4. Changes since submission 1

### Keyed data and explicit failure states (`App.tsx`)

```diff
```

### Tests (`App.test.tsx`)

```diff
```

Summary data is stored with the baseline it was fetched for; the summary renders only when both
findings and artifacts carry the selected baseline. Thread data carries both baseline and root; the
body renders only when both match. Failed requests set explicit unavailable messages; old data is
hidden by the key regardless of timing.

| Finding | Severity | Repair | Recheck |
| --- | --- | --- | --- |
| AS04-R1 stale summary / empty-vs-failure | blocking | Keyed summary/artifacts; loading, unavailable, and empty states are distinct | "never shows the previous baseline's summary under the new baseline (AS04-R1)", "shows an explicit error instead of a stale or empty summary (AS04-R1)" |
| AS04-R2 stale thread / misattributed heading | blocking | Keyed thread by baseline+root; pending/unavailable states; no old chain under a new heading | "never pairs a thread heading with another requirement's chain (AS04-R2)", "shows an explicit error instead of another thread's contents (AS04-R2)" |
| AS04-N1 numeric count coverage | low, nonblocking | Added a two-findings-of-one-type response and asserted `2` | "renders a numeric count of two for two findings of one type (AS04-N1)" |

### Full changed files

`frontend/src/App.tsx`:
```tsx
import { useEffect, useMemo, useState } from "react";

import { ApiError, createApi, type Api } from "./api";
import type { Artifact, Evidence, Finding, Health, ThreadResponse, TraceLink } from "./types";
import "./styles.css";

function errorMessage(error: unknown): string {
  if (error instanceof ApiError) return `${error.code}: ${error.message}`;
  if (error instanceof Error) return error.message;
  return String(error);
}

function requirementState(id: string, findings: Finding[]): { label: string; tone: string } {
  const named = findings.filter((finding) => finding.artifact_ids.includes(id));
  if (named.some((finding) => finding.finding_type === "missing_verification_link")) {
    return { label: "Missing verification", tone: "bad" };
  }
  if (named.length > 0) {
    const types = [...new Set(named.map((finding) => finding.finding_type))].sort().join(", ");
    return { label: `Needs review: ${types}`, tone: "warn" };
  }
  return { label: "Covered", tone: "good" };
}

function provenanceText(link: TraceLink): string {
  const reviewer = link.provenance.reviewer_id;
  const decided = link.provenance.decided_at;
  return [reviewer, decided].filter(Boolean).join(" · ");
}

function LinksTable({ links }: { links: TraceLink[] }) {
  if (links.length === 0) return <p className="empty">None.</p>;
  return (
    <table>
      <thead>
        <tr>
          <th>Link</th>
          <th>Relation</th>
          <th>Source → target</th>
          <th>Provenance</th>
        </tr>
      </thead>
      <tbody>
        {links.map((link) => (
          <tr key={link.link_id}>
            <td>{link.link_id}</td>
            <td>
              <code>{link.relation_type}</code>
            </td>
            <td>
              {link.source_id} → {link.target_id}
            </td>
            <td>{provenanceText(link)}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

function EvidenceTable({ evidence }: { evidence: Evidence[] }) {
  if (evidence.length === 0) return <p className="empty">None.</p>;
  return (
    <table>
      <thead>
        <tr>
          <th>Evidence</th>
          <th>Test / scenario</th>
          <th>Result</th>
          <th>Executed</th>
        </tr>
      </thead>
      <tbody>
        {evidence.map((item) => (
          <tr key={item.evidence_id}>
            <td>{item.evidence_id}</td>
            <td>
              {item.test_id}
              {item.scenario_id ? ` / ${item.scenario_id}` : ""}
            </td>
            <td>
              <span className={`badge ${item.result === "passed" ? "good" : "bad"}`}>
                {item.result}
              </span>
            </td>
            <td>{item.executed_at}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}

export interface AppProps {
  api?: Api;
}

export function App({ api }: AppProps) {
  const client = useMemo(() => api ?? createApi(), [api]);
  const [health, setHealth] = useState<Health | null>(null);
  const [baseline, setBaseline] = useState("");
  const [findingsData, setFindingsData] = useState<{
    baseline: string;
    findings: Finding[];
  } | null>(null);
  const [artifactsData, setArtifactsData] = useState<{
    baseline: string;
    artifacts: Artifact[];
  } | null>(null);
  const [selected, setSelected] = useState("");
  const [threadData, setThreadData] = useState<{
    baseline: string;
    rootId: string;
    thread: ThreadResponse;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [summaryFailed, setSummaryFailed] = useState(false);
  const [threadFailed, setThreadFailed] = useState(false);

  // Data is rendered only under the baseline/root it was requested for, so a slow response can
  // never leave one baseline's counts or one requirement's chain under another heading.
  const summaryReady =
    findingsData?.baseline === baseline && artifactsData?.baseline === baseline;
  const findings = summaryReady && findingsData ? findingsData.findings : [];
  const artifacts = summaryReady && artifactsData ? artifactsData.artifacts : [];
  const thread =
    threadData && threadData.baseline === baseline && threadData.rootId === selected
      ? threadData.thread
      : null;

  useEffect(() => {
    let cancelled = false;
    client
      .health()
      .then((value) => {
        if (cancelled) return;
        setHealth(value);
        setBaseline((current) => current || value.baselines.at(-1) || "");
      })
      .catch((reason) => {
        if (!cancelled) setError(errorMessage(reason));
      });
    return () => {
      cancelled = true;
    };
  }, [client]);

  useEffect(() => {
    if (!baseline) return;
    let cancelled = false;
    setError(null);
    setSummaryFailed(false);
    Promise.all([client.findings(baseline), client.artifacts(baseline)])
      .then(([findingResponse, artifactResponse]) => {
        if (cancelled) return;
        setFindingsData({ baseline, findings: findingResponse.findings });
        setArtifactsData({ baseline, artifacts: artifactResponse.artifacts });
        const requirements = artifactResponse.artifacts.filter(
          (artifact) => artifact.artifact_type === "requirement",
        );
        setSelected((current) =>
          requirements.some((artifact) => artifact.artifact_id === current)
            ? current
            : (requirements[0]?.artifact_id ?? ""),
        );
      })
      .catch((reason) => {
        if (!cancelled) {
          setSummaryFailed(true);
          setError(errorMessage(reason));
        }
      });
    return () => {
      cancelled = true;
    };
  }, [client, baseline]);

  useEffect(() => {
    if (!summaryReady || !baseline || !selected) return;
    let cancelled = false;
    setThreadFailed(false);
    client
      .thread(selected, baseline)
      .then((value) => {
        if (!cancelled) setThreadData({ baseline, rootId: selected, thread: value });
      })
      .catch((reason) => {
        if (!cancelled) {
          setThreadFailed(true);
          setError(errorMessage(reason));
        }
      });
    return () => {
      cancelled = true;
    };
  }, [client, baseline, selected, summaryReady]);

  const counts = useMemo(() => {
    const byType = new Map<string, number>();
    for (const finding of findings) {
      byType.set(finding.finding_type, (byType.get(finding.finding_type) ?? 0) + 1);
    }
    return [...byType.entries()].sort(([left], [right]) => left.localeCompare(right));
  }, [findings]);

  const requirements = useMemo(
    () =>
      artifacts
        .filter((artifact) => artifact.artifact_type === "requirement")
        .sort((left, right) => left.artifact_id.localeCompare(right.artifact_id)),
    [artifacts],
  );

  const baselineCommit =
    health?.baseline_commits[baseline] ?? thread?.artifacts[0]?.revision ?? "";

  return (
    <main className="app">
      <header>
        <h1>Continuous Traceability Assurance</h1>
        <p className="subtitle">
          Requirement threads, accepted relationships, and assurance findings at one baseline.
        </p>
        {health && (
          <div className="baseline-bar">
            <label htmlFor="baseline">Baseline</label>
            <select
              id="baseline"
              value={baseline}
              onChange={(event) => setBaseline(event.target.value)}
            >
              {health.baselines.map((name) => (
                <option key={name} value={name}>
                  {name}
                </option>
              ))}
            </select>
            <span className="commit" title="Resolved commit">
              {baselineCommit ? baselineCommit.slice(0, 12) : ""}
            </span>
            <span className="source-note">Findings: reviewed fixture sample</span>
          </div>
        )}
      </header>

      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      {baseline && !summaryReady && <p className="loading">Loading…</p>}

      <section aria-labelledby="summary-heading">
        <h2 id="summary-heading">Findings summary</h2>
        <p className="baseline-line">
          Baseline <strong>{baseline}</strong>
          {baselineCommit ? <span className="commit"> · {baselineCommit}</span> : null}
        </p>
        {!summaryReady ? (
          <p className="empty">
            {summaryFailed
              ? "Findings are unavailable for this baseline."
              : "Loading findings for this baseline…"}
          </p>
        ) : (
          <>
            {counts.length === 0 ? (
              <p className="empty">No findings at this baseline.</p>
            ) : (
              <ul className="counts" aria-label="Finding counts by type">
                {counts.map(([type, count]) => (
                  <li key={type}>
                    <span>{type}</span>
                    <strong>{count}</strong>
                  </li>
                ))}
              </ul>
            )}

            <h3>Requirements</h3>
            <table>
              <thead>
                <tr>
                  <th>Requirement</th>
                  <th>Title</th>
                  <th>Coverage</th>
                </tr>
              </thead>
              <tbody>
                {requirements.map((artifact) => {
                  const state = requirementState(artifact.artifact_id, findings);
                  return (
                    <tr
                      key={artifact.artifact_id}
                      className={artifact.artifact_id === selected ? "selected" : ""}
                    >
                      <td>
                        <button
                          type="button"
                          className="link-button"
                          onClick={() => setSelected(artifact.artifact_id)}
                        >
                          {artifact.artifact_id}
                        </button>
                      </td>
                      <td>{artifact.title}</td>
                      <td>
                        <span className={`badge ${state.tone}`}>{state.label}</span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </>
        )}
      </section>

      <section aria-labelledby="thread-heading">
        <h2 id="thread-heading">
          Thread {summaryReady && selected ? `for ${selected}` : ""}{" "}
          <span className="baseline-chip">{baseline}</span>
        </h2>
        {!thread ? (
          <p className="empty">
            {threadFailed
              ? "Thread unavailable for this requirement."
              : selected && summaryReady
                ? "Loading thread…"
                : "Select a requirement to inspect its thread."}
          </p>
        ) : (
          <>
            <h3>Accepted relationships</h3>
            <LinksTable links={thread.accepted_links} />

            <h3>
              Proposals <span className="badge warn">not accepted</span>
            </h3>
            <LinksTable links={thread.proposed_links} />

            <h3>Evidence</h3>
            <EvidenceTable evidence={thread.evidence} />
          </>
        )}
      </section>
    </main>
  );
}
```

`frontend/src/App.test.tsx`:
```tsx
import { fireEvent, render, screen, within } from "@testing-library/react";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, expect, it } from "vitest";

import { App } from "./App";
import type { Api } from "./api";
import type {
  Artifact,
  ArtifactListResponse,
  FindingsResponse,
  Health,
  ThreadResponse,
} from "./types";

const here = dirname(fileURLToPath(import.meta.url));
const fixtureDir = resolve(here, "../../fixtures/api-responses");

function readFixture<T>(name: string): T {
  return JSON.parse(readFileSync(resolve(fixtureDir, name), "utf8")) as T;
}

interface SnapshotBaseline {
  baseline: string;
  commit: string;
  artifacts: Artifact[];
}

interface Snapshot {
  schema_version: string;
  baselines: SnapshotBaseline[];
}

const snapshot = readFixture<Snapshot>("snapshot.json");

function fakeApi(overrides: { findings?: Record<string, FindingsResponse> } = {}): Api {
  const findings = overrides.findings ?? {
    "baseline-a": readFixture<FindingsResponse>("findings.baseline-a.json"),
    "baseline-b": readFixture<FindingsResponse>("findings.baseline-b.json"),
  };
  const health: Health = {
    status: "ok",
    package_version: "0.1.0",
    schema_version: snapshot.schema_version,
    fixture: "banking-demo",
    baselines: snapshot.baselines.map((entry) => entry.baseline),
    baseline_commits: Object.fromEntries(
      snapshot.baselines.map((entry) => [entry.baseline, entry.commit]),
    ),
    discovery_providers: ["fake"],
  };
  return {
    health: async () => health,
    findings: async (baseline) => findings[baseline],
    artifacts: async (baseline): Promise<ArtifactListResponse> => ({
      schema_version: snapshot.schema_version,
      baseline,
      artifacts: snapshot.baselines.find((entry) => entry.baseline === baseline)?.artifacts ?? [],
    }),
    thread: async (artifactId, baseline) =>
      readFixture<ThreadResponse>(`threads/${artifactId}.${baseline}.json`),
  };
}

async function selectBaseline(name: string): Promise<void> {
  const selector = await screen.findByLabelText("Baseline");
  fireEvent.change(selector, { target: { value: name } });
}

function deferred<T>() {
  return Promise.withResolvers<T>();
}

function summaryRegion(): HTMLElement {
  return screen.getByRole("region", { name: "Findings summary" });
}

function requirementRow(artifactId: string): HTMLElement {
  const cell = within(summaryRegion()).getByText(artifactId);
  const row = cell.closest("tr");
  if (!row) throw new Error(`no row for ${artifactId}`);
  return row;
}

describe("findings summary", () => {
  it("shows counts by type and coverage for baseline-a (SCN-801)", async () => {
    render(<App api={fakeApi()} />);
    await selectBaseline("baseline-a");
    await screen.findByRole("region", { name: /Thread for REQ-001/ });

    const counts = await screen.findByLabelText("Finding counts by type");
    const missing = within(counts).getByText("missing_verification_link").closest("li");
    expect(missing).not.toBeNull();
    expect(within(missing as HTMLElement).getByText("1")).toBeInTheDocument();

    expect(within(requirementRow("REQ-001")).getByText("Covered")).toBeInTheDocument();
    expect(
      within(requirementRow("REQ-002")).getByText("Missing verification"),
    ).toBeInTheDocument();
    expect(within(summaryRegion()).getByText("baseline-a")).toBeInTheDocument();
  });

  it("reloads when the baseline selector changes (SCN-802)", async () => {
    render(<App api={fakeApi()} />);
    await selectBaseline("baseline-a");
    await screen.findByLabelText("Finding counts by type");

    await selectBaseline("baseline-b");
    const counts = await screen.findByLabelText("Finding counts by type");
    await screen.findByRole("region", { name: /Thread for REQ-001/ });
    expect(within(counts).getByText("reverification_required")).toBeInTheDocument();
    expect(within(summaryRegion()).getByText("baseline-b")).toBeInTheDocument();
    expect(
      within(requirementRow("REQ-001")).getByText("Needs review: reverification_required"),
    ).toBeInTheDocument();
  });

  it("derives counts from the response instead of hard-coding them (SCN-803)", async () => {
    const altered = structuredClone(readFixture<FindingsResponse>("findings.baseline-a.json"));
    altered.findings = altered.findings.filter(
      (finding) => !finding.artifact_ids.includes("REQ-002"),
    );
    render(
      <App
        api={fakeApi({
          findings: {
            "baseline-a": altered,
            "baseline-b": readFixture<FindingsResponse>("findings.baseline-b.json"),
          },
        })}
      />,
    );
    await selectBaseline("baseline-a");
    await screen.findByRole("region", { name: /Thread for REQ-001/ });

    const counts = await screen.findByLabelText("Finding counts by type");
    expect(within(counts).queryByText("missing_verification_link")).toBeNull();
    expect(within(requirementRow("REQ-002")).getByText("Covered")).toBeInTheDocument();
  });

  it("never shows the previous baseline's summary under the new baseline (AS04-R1)", async () => {
    const base = fakeApi();
    const pending = deferred<FindingsResponse>();
    const api: Api = {
      ...base,
      findings: (baseline) =>
        baseline === "baseline-b" ? pending.promise : base.findings(baseline),
    };
    render(<App api={api} />);
    await selectBaseline("baseline-a");
    await screen.findByText("Covered");

    await selectBaseline("baseline-b");
    expect(screen.queryByText("missing_verification_link")).toBeNull();
    expect(screen.getByText("Loading findings for this baseline…")).toBeInTheDocument();

    pending.resolve(readFixture<FindingsResponse>("findings.baseline-b.json"));
    await screen.findByText("reverification_required");
    expect(within(summaryRegion()).getByText("baseline-b")).toBeInTheDocument();
  });

  it("renders a numeric count of two for two findings of one type (AS04-N1)", async () => {
    const altered = structuredClone(readFixture<FindingsResponse>("findings.baseline-a.json"));
    const template = altered.findings.find(
      (finding) => finding.finding_type === "lifecycle_review_required",
    );
    if (!template) throw new Error("fixture lacks a lifecycle finding");
    altered.findings = [
      { ...template, finding_id: "FND-0000000000000001", artifact_ids: ["REQ-001"] },
      { ...template, finding_id: "FND-0000000000000002", artifact_ids: ["REQ-003"] },
    ];
    render(
      <App
        api={fakeApi({
          findings: {
            "baseline-a": altered,
            "baseline-b": readFixture<FindingsResponse>("findings.baseline-b.json"),
          },
        })}
      />,
    );
    await selectBaseline("baseline-a");

    const counts = await screen.findByLabelText("Finding counts by type");
    const row = within(counts).getByText("lifecycle_review_required").closest("li");
    if (!row) throw new Error("no count row for lifecycle_review_required");
    expect(within(row).getByText("2")).toBeInTheDocument();
  });

  it("shows an explicit error instead of a stale or empty summary (AS04-R1)", async () => {
    const base = fakeApi();
    const api: Api = {
      ...base,
      findings: (baseline) =>
        baseline === "baseline-b"
          ? Promise.reject(new Error("summary request failed"))
          : base.findings(baseline),
    };
    render(<App api={api} />);
    await selectBaseline("baseline-a");
    await screen.findByText("Covered");

    await selectBaseline("baseline-b");
    expect(
      await screen.findByText("Findings are unavailable for this baseline."),
    ).toBeInTheDocument();
    expect(screen.queryByText("missing_verification_link")).toBeNull();
    expect(screen.queryByText("No findings at this baseline.")).toBeNull();
  });
});

describe("thread view", () => {
  it("labels proposals and keeps them out of coverage (SCN-804)", async () => {
    render(<App api={fakeApi()} />);
    await selectBaseline("baseline-a");

    await screen.findByRole("button", { name: "REQ-002" });
    fireEvent.click(within(summaryRegion()).getByRole("button", { name: "REQ-002" }));
    const thread = await screen.findByRole("region", { name: /Thread for REQ-002/ });
    expect(within(thread).getByText("LNK-007")).toBeInTheDocument();
    expect(within(thread).getByText("not accepted")).toBeInTheDocument();
    expect(
      within(requirementRow("REQ-002")).getByText("Missing verification"),
    ).toBeInTheDocument();
  });

  it("shows the accepted chain and its evidence (SCN-805)", async () => {
    render(<App api={fakeApi()} />);
    await selectBaseline("baseline-b");

    await screen.findByRole("button", { name: "REQ-001" });
    fireEvent.click(within(summaryRegion()).getByRole("button", { name: "REQ-001" }));
    const thread = await screen.findByRole("region", { name: /Thread for REQ-001/ });
    for (const linkId of ["LNK-001", "LNK-002", "LNK-003"]) {
      expect(within(thread).getByText(linkId)).toBeInTheDocument();
    }
    expect(within(thread).getByText("verified_by")).toBeInTheDocument();
    expect(within(thread).getByText("EV-001")).toBeInTheDocument();
    expect(within(thread).getByText("passed")).toBeInTheDocument();
    expect(within(thread).getByText("baseline-b")).toBeInTheDocument();
  });

  it("never pairs a thread heading with another requirement's chain (AS04-R2)", async () => {
    const base = fakeApi();
    const pending = deferred<ThreadResponse>();
    const api: Api = {
      ...base,
      thread: (artifactId, baseline) =>
        artifactId === "REQ-002" ? pending.promise : base.thread(artifactId, baseline),
    };
    render(<App api={api} />);
    await selectBaseline("baseline-a");
    await screen.findByRole("region", { name: /Thread for REQ-001/ });

    fireEvent.click(within(summaryRegion()).getByRole("button", { name: "REQ-002" }));
    await screen.findByText("Loading thread…");
    const pendingThread = screen.getByRole("region", { name: /Thread for REQ-002/ });
    expect(within(pendingThread).queryByText("LNK-001")).toBeNull();

    pending.resolve(readFixture<ThreadResponse>("threads/REQ-002.baseline-a.json"));
    const loaded = await screen.findByRole("region", { name: /Thread for REQ-002/ });
    expect(within(loaded).getByText("LNK-007")).toBeInTheDocument();
  });

  it("shows an explicit error instead of another thread's contents (AS04-R2)", async () => {
    const base = fakeApi();
    const api: Api = {
      ...base,
      thread: (artifactId, baseline) =>
        artifactId === "REQ-002"
          ? Promise.reject(new Error("thread request failed"))
          : base.thread(artifactId, baseline),
    };
    render(<App api={api} />);
    await selectBaseline("baseline-a");
    await screen.findByRole("region", { name: /Thread for REQ-001/ });
    await screen.findByRole("button", { name: "REQ-002" });

    fireEvent.click(within(summaryRegion()).getByRole("button", { name: "REQ-002" }));
    expect(
      await screen.findByText("Thread unavailable for this requirement."),
    ).toBeInTheDocument();
    const thread = screen.getByRole("region", { name: /Thread for REQ-002/ });
    expect(within(thread).queryByText("LNK-001")).toBeNull();
  });
});
```

## 5. Implementation context

* The app takes an injected `Api`; tests inject committed JSON. Vite proxies `/health` and `/api`
  in development.
* Requirements come from `/api/artifacts`; counts from `/api/findings`; the thread is fetched per
  selection. Proposals render only from `proposed_links` with a `not accepted` badge.
* Targeted reads: `frontend/src/App.test.tsx`, `fixtures/api-responses/findings.*.json`,
  `fixtures/api-responses/threads/*`, `frontend/package.json`, `.github/workflows/ci.yml`.

## 6. Evidence

| Criterion | Check | Result |
| --- | --- | --- |
| SCN-801 | "shows counts by type and coverage for baseline-a" | PASS |
| SCN-802 | "reloads when the baseline selector changes"; AS04-R1 transition/failure tests | PASS |
| SCN-803 | "derives counts from the response"; AS04-N1 numeric test | PASS |
| SCN-804 | "labels proposals and keeps them out of coverage" | PASS |
| SCN-805 | "shows the accepted chain and its evidence"; AS04-R2 transition/failure tests | PASS |
| Browser | real backend + Vite: two baselines, proposal thread, mobile viewport, 0 console errors | PASS |

Captured invocations and exits, 2026-11-13T04:37:37Z–04:43:44Z:

```text
backend: pytest backend/tests -q     exit 0  233 passed (also under OS-level network denial)
backend: fixturectl.py verify        exit 0  reproducible and current
backend: ruff check/format           exit 0
backend: git diff --check            exit 0
frontend: npm run build              exit 0  built in 1.66s
frontend: npm test                   exit 0  10 passed
```

Browser demonstration (managed headless browser, servers started/stopped by OMP): baseline-a
counts and coverage; REQ-002 proposals labelled `not accepted`; baseline-b thread with LNK-001..003
and EV-001; 390×844 summary; zero console errors. Screenshots are hash-listed above at
`docs/reports/omp-as-04-summary/evidence/`.

NOT RUN: visual review by a human stakeholder; link review (AS-06); browser automation in CI.

## 7. File-integrity requirement

The manifest in section 3 is the reviewed snapshot. If any manifest hash changed, the snapshot is
not the one reviewed. Do not edit files, install dependencies, regenerate fixtures, or commit.

## Reviewer instructions (mandatory)

You are the independent CTA implementation reviewer using GPT-6.1 Sol xhigh. Decide whether this exact snapshot satisfies the supplied story, every applicable Gherkin criterion, and repository invariants. Treat OMP's summaries and test results as claims to check against the supplied artifacts and targeted source inspection. Check proposal/accepted/evidence separation, real port compatibility, revision/content-hash semantics, honest errors/501s, independent oracle expectations, offline defaults, and generated-file discipline where relevant. Do not demand implementation of a later milestone. Do not edit files, implement repairs, regenerate fixtures, commit, or delegate. Ask OMP for missing runtime evidence; distinguish observed defects from hypotheses and unavailable checks. Return an AC-by-AC PASS, FAIL, or NOT VERIFIED assessment and actionable findings with stable IDs, severity, blocking status, AC/invariant, path/line, expected/actual behavior, and smallest correction/recheck. Keep optional suggestions and unrelated pre-existing defects separate. Return exactly one verdict: APPROVE, REQUEST_CHANGES, or NEEDS_INPUT. APPROVE requires every applicable criterion/check to be satisfied, no unresolved blocker, and the exact snapshot identified. In later rounds verify prior dispositions and regressions while retaining the complete acceptance assessment. A passing process, passing tests, or exhausted review limit is not approval. Agent review cannot attest human labeling or human link decisions.
