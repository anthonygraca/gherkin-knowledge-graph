# Independent implementation review — AS-04, submission 1 of 7

## 1. Story and authorization

**Task:** AS-04 — Summary of findings and coverage counts.
**Roadmap/feature:** F-06 UI, roadmap §6 AS-04; milestone **M1 — AI-free vertical slice**.
**GitHub story:** anthonygraca/gherkin-knowledge-graph issue **#26**, verified OPEN at
2026-11-13T04:13:19Z (`gh issue view`), milestone "M1 — AI-free vertical slice".
**Owner:** C; **Implementer/integrator:** OMP.
**Repository:** `<task_repo>` (read-only sandbox).
**Base:** `d238776bf0b53e6963f8e81721ce9a106f848adb` (`main`, AS-01 merge).
**Branch:** `feat/26-as-04-summary-ui`. **Submission:** 1 of 7.

### User outcome

A lead can choose a baseline, see findings counts and per-requirement coverage, and inspect a
requirement's thread with accepted links, proposals, and evidence — offline.

### Scope

React + TypeScript + Vite dashboard; baseline selector; summary counts and coverage; thread view;
Vitest component tests against committed fixture responses; frontend CI job; setup docs; a browser
demonstration. Also includes the nonblocking AS01-R1 test-strength repair (test only). Non-goals:
link review, computed assurance in the UI, authentication, deployment.

### Proposed commit references

1. `test(assurance): [issue #2] bind finding revisions to the manifest tag`, body `Refs #2`.
2. `feat(ui): [issue #26] show findings summary and requirement threads`, body `Refs #26`.

## 2. Acceptance criteria (canonical snapshot)

File `docs/stories/AS-04.feature`, sha256
`44f0ce7d64cdd2f80fa093a0adcdd5964821c5fa4102abbccf503dc7484d6f6e`.

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
No separate human refinement sign-off is recorded. Browser evidence demonstrates the built surface;
it is not stakeholder acceptance.

Repository constraints (AGENTS.md): offline test execution; counts derived from responses; proposals
never counted as coverage; no model calls; no hand-edited generated files.

## 3. Snapshot and manifest

Snapshot captured 2026-11-13T04:22Z. Manifest (sha256 of every task file, including screenshots):

```text
7d82d45f0d7bd214b9a014d89ed696ca0c32550bd4b81c3cbfaccc1866908315  frontend/package.json
5fd857b362d57ef48f0ff8862d474770ad5dc98d33c944bc64734dacd1591bac  frontend/package-lock.json
bde007f1fd26fa27cc068f64d8c02ee388ee08d22c7d4a15b211c0cd5870d7d1  frontend/vite.config.ts
770b4140bbb581e2dfd9ea9946ffc9c75a1d86ba7d2db5f77c83e37cbdf9d808  frontend/tsconfig.json
7f421e06013a7643878525b2591838ec5bc13016fe479f294ca91119de2f2b5e  frontend/tsconfig.app.json
3ced5d22ba9e246c839a695526296a8d067fbe9db838d728516d2eac9215b333  frontend/tsconfig.node.json
4e00b5c1e7c64dfbeb8aa8fca0d0acc71be382a17960305e256c1b76a3f765f2  frontend/index.html
0bfe47c42f21690c67b2d54320f32a138ab3b81835f2fab891607f20c8267fbb  frontend/src/App.test.tsx
1c66162f8af7f27f5cc2bd2485dc43c3eea709df36bd4c029df7ae5fd539d44a  frontend/src/App.tsx
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
371406b7d3371d978fad7bab88cbbdcc2a371028edea0a051daf9d7e2ebb5505  docs/reports/omp-as-04-summary/IMPLEMENTATION.md
3cdfb978541c7b70be7e301d54494985fc5bea41db9cc8cf239c308b1f77e61f  docs/reports/omp-as-04-summary/PROMPT_LOG.md
e72964f89706ee61da84c117178d79a941a86b438d74a05d3023ce010701b92a  docs/reports/omp-as-04-summary/METRICS.md
fb95acee7bdd2a981f3d632489bb81e795aef3761aaedd564e290647e7a52bed  docs/reports/omp-as-04-summary/evidence/summary-baseline-a.png
879b156cfa1b214ec2c03cd89536259a421b4e44ea2ef7e0d8320327e94b36aa  docs/reports/omp-as-04-summary/evidence/summary-mobile-390.png
d6983475aec8ad17c45a5c747b9566d8d79690d1744f5d4eb86ed9f70b5f4502  docs/reports/omp-as-04-summary/evidence/thread-req-001-baseline-b.png
6150fa2356813c46a0b940b7c110695000537314ac65c4c9ae5fa33765c1e6a9  docs/reports/omp-as-04-summary/evidence/thread-req-002-proposals.png
```

`SCHEMA_VERSION = 0.2.0` (unchanged), `PACKAGE_VERSION = 0.1.0`. The only backend change is the
AS01-R1 test assertion; product code and fixtures are unchanged.

## 4. Frontend implementation (complete)

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
  const [findings, setFindings] = useState<Finding[]>([]);
  const [artifacts, setArtifacts] = useState<Artifact[]>([]);
  const [selected, setSelected] = useState("");
  const [thread, setThread] = useState<ThreadResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

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
    setLoading(true);
    setError(null);
    Promise.all([client.findings(baseline), client.artifacts(baseline)])
      .then(([findingResponse, artifactResponse]) => {
        if (cancelled) return;
        setFindings(findingResponse.findings);
        setArtifacts(artifactResponse.artifacts);
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
        if (!cancelled) setError(errorMessage(reason));
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [client, baseline]);

  useEffect(() => {
    if (!baseline || !selected) {
      setThread(null);
      return;
    }
    let cancelled = false;
    client
      .thread(selected, baseline)
      .then((value) => {
        if (!cancelled) setThread(value);
      })
      .catch((reason) => {
        if (!cancelled) {
          setThread(null);
          setError(errorMessage(reason));
        }
      });
    return () => {
      cancelled = true;
    };
  }, [client, baseline, selected]);

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
      {loading && <p className="loading">Loading…</p>}

      <section aria-labelledby="summary-heading">
        <h2 id="summary-heading">Findings summary</h2>
        <p className="baseline-line">
          Baseline <strong>{baseline}</strong>
          {baselineCommit ? <span className="commit"> · {baselineCommit}</span> : null}
        </p>
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
      </section>

      <section aria-labelledby="thread-heading">
        <h2 id="thread-heading">
          Thread {selected ? `for ${selected}` : ""}{" "}
          <span className="baseline-chip">{baseline}</span>
        </h2>
        {!thread ? (
          <p className="empty">Select a requirement to inspect its thread.</p>
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

`frontend/src/api.ts`:
```ts
import type {
  ArtifactListResponse,
  FindingsResponse,
  Health,
  ProblemDetails,
  ThreadResponse,
} from "./types";

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    detail: string,
  ) {
    super(detail);
    this.name = "ApiError";
  }
}

async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(path, { headers: { Accept: "application/json" } });
  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    let code = `http-${response.status}`;
    try {
      const problem = (await response.json()) as ProblemDetails;
      detail = problem.detail || detail;
      code = problem.code || code;
    } catch {
      // a non-JSON error body keeps the HTTP status as the explanation
    }
    throw new ApiError(response.status, code, detail);
  }
  return (await response.json()) as T;
}

export interface Api {
  health(): Promise<Health>;
  findings(baseline: string): Promise<FindingsResponse>;
  artifacts(baseline: string): Promise<ArtifactListResponse>;
  thread(artifactIds: string, baseline: string): Promise<ThreadResponse>;
}

export function createApi(baseUrl = ""): Api {
  const query = (baseline: string) => `?baseline=${encodeURIComponent(baseline)}`;
  return {
    health: () => getJson<Health>(`${baseUrl}/health`),
    findings: (baseline) => getJson<FindingsResponse>(`${baseUrl}/api/findings${query(baseline)}`),
    artifacts: (baseline) =>
      getJson<ArtifactListResponse>(`${baseUrl}/api/artifacts${query(baseline)}`),
    thread: (artifactIds, baseline) =>
      getJson<ThreadResponse>(
        `${baseUrl}/api/threads/${encodeURIComponent(artifactIds)}${query(baseline)}`,
      ),
  };
}
```

`frontend/src/types.ts`:
```ts
export type ArtifactType = "requirement" | "scenario" | "source" | "test";
export type RelationType = "verified_by" | "implemented_by" | "exercised_by";
export type ReviewState = "proposed" | "accepted" | "rejected";
export type EvidenceResult = "passed" | "failed" | "skipped";

export interface Artifact {
  artifact_id: string;
  artifact_type: ArtifactType;
  title: string;
  source_uri: string;
  repository: string;
  revision: string;
  content_hash: string;
  locator: string;
  metadata: Record<string, string | number | boolean>;
}

export interface TraceLink {
  link_id: string;
  source_id: string;
  target_id: string;
  relation_type: RelationType;
  review_state: ReviewState;
  provenance: Record<string, string | number | boolean>;
  created_at: string;
  updated_at: string;
}

export interface Evidence {
  evidence_id: string;
  test_id: string;
  scenario_id: string | null;
  result: EvidenceResult;
  tested_commit: string;
  executed_at: string;
  run_uri: string;
}

export interface Finding {
  finding_id: string;
  finding_type: string;
  status: string;
  severity: string;
  artifact_ids: string[];
  evaluated_baseline: string;
  evidence_ids: string[];
  explanation: string;
  rule_id: string;
  artifact_revisions: Record<string, string>;
}

export interface Health {
  status: string;
  package_version: string;
  schema_version: string;
  fixture: string;
  baselines: string[];
  baseline_commits: Record<string, string>;
  discovery_providers: string[];
}

export interface FindingsResponse {
  schema_version: string;
  baseline: string;
  findings: Finding[];
}

export interface ArtifactListResponse {
  schema_version: string;
  baseline: string;
  artifacts: Artifact[];
}

export interface ThreadResponse {
  schema_version: string;
  root_id: string;
  baseline: string;
  artifacts: Artifact[];
  accepted_links: TraceLink[];
  proposed_links: TraceLink[];
  evidence: Evidence[];
}

export interface ProblemDetails {
  type: string;
  title: string;
  status: number;
  detail: string;
  instance: string;
  code?: string;
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
});

describe("thread view", () => {
  it("labels proposals and keeps them out of coverage (SCN-804)", async () => {
    render(<App api={fakeApi()} />);
    await selectBaseline("baseline-a");

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
});
```

`frontend/src/main.tsx`:
```tsx
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { App } from "./App";

const container = document.getElementById("root");
if (!container) {
  throw new Error("root element is missing from index.html");
}

createRoot(container).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
```

`frontend/vite.config.ts`:
```ts
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/health": "http://127.0.0.1:8000",
      "/api": "http://127.0.0.1:8000",
    },
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./src/test-setup.ts"],
    globals: true,
  },
});
```

`frontend/package.json`:
```json
{
  "name": "cta-dashboard",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "test": "vitest run"
  },
  "dependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0"
  },
  "devDependencies": {
    "@testing-library/jest-dom": "^6.6.3",
    "@testing-library/react": "^16.1.0",
    "@types/node": "^22.10.0",
    "@types/react": "^19.0.0",
    "@types/react-dom": "^19.0.0",
    "@vitejs/plugin-react": "^4.3.4",
    "jsdom": "^25.0.1",
    "typescript": "^5.7.2",
    "vite": "^6.0.5",
    "vitest": "^3.0.0"
  }
}

### Configuration, CI, docs, and the AS01-R1 test diff

```diff
diff --git a/.github/workflows/ci.yml b/.github/workflows/ci.yml
index 92ed4f0..1bdfe8d 100644
--- a/.github/workflows/ci.yml
+++ b/.github/workflows/ci.yml
@@ -64,3 +64,27 @@ jobs:
 
       - name: Format check
         run: uv run --project backend ruff format --check .
+
+  frontend:
+    name: Frontend build and component tests
+    runs-on: ubuntu-latest
+    defaults:
+      run:
+        working-directory: frontend
+    steps:
+      - uses: actions/checkout@v4
+
+      - uses: actions/setup-node@v4
+        with:
+          node-version: "22"
+          cache: npm
+          cache-dependency-path: frontend/package-lock.json
+
+      - name: Install frontend dependencies
+        run: npm ci
+
+      - name: Build
+        run: npm run build
+
+      - name: Component tests
+        run: npm test
diff --git a/backend/tests/test_assurance_rules.py b/backend/tests/test_assurance_rules.py
index 4c88b8f..86d847b 100644
--- a/backend/tests/test_assurance_rules.py
+++ b/backend/tests/test_assurance_rules.py
@@ -27,7 +27,7 @@ def evaluate(client: TestClient, baseline: str) -> FindingsResponse:
 
 @pytest.mark.parametrize("baseline", BASELINES)
 def test_evaluate_matches_the_oracle_missing_verification_finding(
-    client: TestClient, fixture_settings: Settings, baseline: str
+    client: TestClient, fixture_settings: Settings, committed_manifest, baseline: str
 ) -> None:
     body = evaluate(client, baseline)
     expected = [
@@ -51,7 +51,9 @@ def test_evaluate_matches_the_oracle_missing_verification_finding(
     assert finding.finding_id == finding_fingerprint(
         item.rule_id, item.finding_type, item.artifact_ids
     )
-    assert finding.evaluated_baseline == finding.artifact_revisions["REQ-002"]
+    expected_commit = committed_manifest.tags[baseline]
+    assert finding.evaluated_baseline == expected_commit
+    assert finding.artifact_revisions["REQ-002"] == expected_commit
 
 
 def test_evaluate_does_not_count_proposals(client: TestClient) -> None:
diff --git a/docs/STATUS.md b/docs/STATUS.md
index accc9cb..b4efee6 100644
--- a/docs/STATUS.md
+++ b/docs/STATUS.md
@@ -2,10 +2,10 @@
 
 ```text
 Date:                2026-11-13
-Current branch:      feat/2-as-01-missing-verification (from main c43541b)
+Current branch:      feat/26-as-04-summary-ui (from main d238776)
 Milestone:           M0 — exit gate SATISFIED by re-review round 2 (historical record below)
                      M1 — IN PROGRESS; gate NOT yet satisfied
-Active task:         AS-01 (#2) missing coverage/link findings
+Active task:         AS-04 (#26) findings and coverage summary UI
 Independent review:  docs/reviews/M0-review.md — first review: "M0 not verified"
                      docs/reviews/M0-rereview-1.md — re-review round 1 (GPT-6.1 Sol, xhigh):
                      NEEDS_INPUT; R1–R7 all repaired; AC-1.1…AC-1.8 and AC-2.1…AC-2.5 all PASS;
@@ -20,7 +20,11 @@ Historical (SETUP-01, 2026-11-12): the commit-reference slice landed via PR #42;
                      had 107 passed; the SETUP-01 tree then had 135 passed (also under an
                      OS-level network denial). Outstanding owner actions: #18/#19 closure, the
                      FT-03/project-definition reviews, the required-check ruleset, README work item.
-Tests executed:      AS-01 (in progress): focused assurance suite in docs/reports/omp-as-01-missing-link/.
+Tests executed:      AS-04 (in progress): frontend build/Vitest and browser demo in
+                     docs/reports/omp-as-04-summary/.
+                     AS-01 approved snapshot: 233 passed; PR #48 merged as d238776 with both
+                     hosted checks passing; issue #2 closed; AS01-R1 test strengthening applied
+                     on this branch.
                      DT-04 approved snapshot: 227 passed; PR #47 merged as c43541b with both
                      hosted checks passing; issue #23 closed.
                      DT-03 approved snapshot: 219 passed; PR #46 merged as 0970f7a with both
@@ -53,8 +57,8 @@ not claim that draft as an approved baseline.
 | DT-02 source/test artifacts | [#21](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/21) | B | [DT-02.feature](stories/DT-02.feature) | **merged** PR [#45](https://github.com/anthonygraca/gherkin-knowledge-graph/pull/45) → `590e776`; APPROVE at submission 4; issue closed |
 | DT-03 typed links + review state | [#22](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/22) | B | [DT-03.feature](stories/DT-03.feature) | **merged** PR [#46](https://github.com/anthonygraca/gherkin-knowledge-graph/pull/46) → `0970f7a`; APPROVE at submission 2; issue closed |
 | DT-04 requirement thread | [#23](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/23) | B | [DT-04.feature](stories/DT-04.feature) | **merged** PR [#47](https://github.com/anthonygraca/gherkin-knowledge-graph/pull/47) → `c43541b`; APPROVE at submission 2; issue closed |
-| AS-01 missing-link finding | [#2](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/2) | C | [AS-01.feature](stories/AS-01.feature) | refined; implementation in review |
-| AS-04 findings/coverage summary | [#26](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/26) | C | not yet written | eligible after AS-01 |
+| AS-01 missing-link finding | [#2](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/2) | C | [AS-01.feature](stories/AS-01.feature) | **merged** PR [#48](https://github.com/anthonygraca/gherkin-knowledge-graph/pull/48) → `d238776`; APPROVE at submission 1; issue closed |
+| AS-04 findings/coverage summary | [#26](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/26) | C | [AS-04.feature](stories/AS-04.feature) | refined; implementation in review |
 
 Per-task reports live under `docs/reports/omp-<task-slug>/`; each carries the AC-to-check table,
 actual commands/exits, the snapshot identity, and the independent verdict. Issue closure is
diff --git a/docs/architecture.md b/docs/architecture.md
index 51ec830..fe078ac 100644
--- a/docs/architecture.md
+++ b/docs/architecture.md
@@ -43,7 +43,7 @@ Two rules explain most of the layout:
 | `app/assurance/sample_findings.py` | Replay of reviewed sample findings for `GET /api/findings` | Mock service (full rule set in M2) |
 | `app/api/` | Routes, dependencies, RFC 9457 problem documents | Working |
 | `app/ingestion/` | Revision-pinned parsing: requirements/Gherkin (DT-01), source/test (DT-02), links (DT-03), evidence + thread assembly (DT-04) | Implemented |
-| `frontend/` | React/TypeScript dashboard | Absent by design; created in C-PR1 |
+| `frontend/` | React + TypeScript + Vite dashboard: baseline selector, findings summary, coverage, thread view; Vitest component tests | Implemented (AS-04) |
 
 ## Request flows
 
diff --git a/docs/setup.md b/docs/setup.md
index 62eba0d..346cebd 100644
--- a/docs/setup.md
+++ b/docs/setup.md
@@ -5,6 +5,7 @@
 * Python 3.11 or newer (3.12 is what CI uses)
 * [uv](https://docs.astral.sh/uv/) for dependency and environment management
 * `git` 2.29 or newer (fixture generation creates real repositories, tags, and pins the object format)
+* Node.js 22 and npm (frontend build and component tests only)
 
 Not required: Docker, a GPU, a model server, a database server, network access during tests.
 The first `uv sync` downloads dependencies from a package index; everything after that runs
@@ -34,6 +35,23 @@ uv run --project backend python tools/fixturectl.py verify         # build+mater
 generator produces now. CI runs it. If it fails, regenerate with `all` and commit the result
 with your fixture edit.
 
+## Frontend
+
+Dependencies install from the registry once; build and tests run offline.
+
+```bash
+cd frontend
+npm ci            # install the locked dependency tree
+npm run build     # TypeScript build + Vite bundle
+npm test          # Vitest component tests against committed fixture responses
+npm run dev       # dashboard at http://127.0.0.1:5173
+```
+
+Start the backend first (`uv run --project backend uvicorn app.main:app --port 8000`) with built
+fixtures. Vite proxies `/health` and `/api` to the backend. The dashboard shows the reviewed
+fixture findings and the assembled thread for the selected baseline; it needs no model or external
+service.
+
 ## Quality gates
 
 ```bash
```

`docs/stories/AS-04.md`:
```markdown
# AS-04 — Summary of findings and coverage counts

**Milestone:** M1 — AI-free vertical slice · **Owner:** C · **Implementer:** OMP · **Status:**
refined; implementation in progress.

| Record | Value |
| --- | --- |
| Roadmap / feature | F-06 UI · roadmap §6 AS-04 |
| GitHub story | [#26](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/26) — verified OPEN 2026-11-13T04:13:19Z (`gh issue view`), milestone "M1 — AI-free vertical slice" |
| Parent feature issue | [#12](https://github.com/anthonygraca/gherkin-knowledge-graph/issues/12) |
| Canonical criteria | [AS-04.feature](AS-04.feature), sha256 `44f0ce7d64cdd2f80fa093a0adcdd5964821c5fa4102abbccf503dc7484d6f6e` |
| Dependencies | AS-01 (#2) merged at `d238776bf0b53e6963f8e81721ce9a106f848adb`; DT-04 inventory/thread API |
| Upstream obligation | Roadmap §6 F-06 and the M1 deliverable ("UI shows a thread and finding"); ADR 0006 #5 |

## User outcome

A lead can open the dashboard, choose a baseline, and see how many findings of each type exist and
which requirements are covered or missing verification, then inspect a requirement's thread with
its accepted chain, proposals, and evidence — all offline against fixture data.

## Scope

* React + TypeScript + Vite dashboard in `frontend/` (the roadmap's stack; no divergence to record).
* Baseline selector from `/health`; selected baseline and resolved commit always visible.
* Summary counts by finding type from `/api/findings?baseline=`, plus per-requirement coverage
  derived from `/api/artifacts?baseline=` and the findings response.
* Requirement thread view from `/api/threads/{id}?baseline=`: accepted links with relation types,
  proposals clearly labelled and separated, evidence rows.
* Vitest component tests with an injected API returning the committed fixture responses; no network.
* A CI job for the frontend and setup documentation.
* A recorded browser demonstration with screenshots.

## Non-goals

Accepting/rejecting links (AS-06); computed assurance in the UI (it consumes the reviewed sample
findings in M1); authentication; deployment; a design system; SSR.

## Preservation boundaries

No backend response shape changes. The dashboard reads proposals only from `proposed_links` and
labels them. Counts are never hard-coded; tests change the response and assert the rendered numbers
change. Frontend test execution uses no network.

## Design impact

```text
frontend/
  package.json / package-lock.json
  vite.config.ts (dev proxy for /health and /api)
  tsconfig*.json
  index.html
  src/main.tsx, App.tsx, api.ts, types.ts, styles.css
  src/App.test.tsx, src/test-setup.ts
```

The app takes an injected `Api` object; tests supply committed JSON instead of starting a server. A
visible data-source note distinguishes the reviewed fixture findings from computed evaluation.
Tests read `fixtures/api-responses/*.json` directly (no copies), so drift in the committed examples
is visible to the UI tests.

Assumptions:

1. The backend runs at `127.0.0.1:8000` in development; Vite proxies `/health` and `/api`.
2. `GET /api/findings` is the reviewed sample response in M1; the UI says so.
3. Coverage means "no finding names this requirement"; a missing-verification finding is shown as
   such. Other finding types are shown as their own labels.
4. Requirement selection defaults to the first requirement id for the baseline.

## Refinement disposition

Derived from the owner-authored issue intake and roadmap §6; boundary scenarios were added. No
separate human refinement sign-off is recorded. Browser evidence demonstrates the built surface; it
is not stakeholder acceptance.

## Verification mapping

| Scenario | Observable check | Selector |
| --- | --- | --- |
| SCN-801 coverage summary | baseline-a counts, REQ-001 covered, REQ-002 missing verification | `frontend/src/App.test.tsx` "shows counts by type and coverage for baseline-a" |
| SCN-802 baseline visible/selector | selector change triggers baseline-b data and displays it | `frontend/src/App.test.tsx` "reloads when the baseline selector changes" |
| SCN-803 counts from response | altered findings response changes the rendered counts/coverage | `frontend/src/App.test.tsx` "derives counts from the response" |
| SCN-804 proposals labelled | REQ-002 thread shows LNK-007 under proposals and not covered | `frontend/src/App.test.tsx` "labels proposals and keeps them out of coverage" |
| SCN-805 thread chain/evidence | REQ-001 baseline-b shows LNK-001..003, relation types, EV-001 | `frontend/src/App.test.tsx` "shows the accepted chain and its evidence" |
| Browser demonstration | Load the real backend + Vite app; select baselines; capture summary/thread screenshots | `docs/reports/omp-as-04-summary/evidence/` |

A mapping row is not an execution result; the run record carries the actual invocation and result.

## Verification plan

```bash
cd frontend
npm ci
npm run build
npm test
```

Backend suite, fixture drift, ruff, network-denied suite, and a browser demonstration with the real
backend remain required. `npm ci` needs a package registry once; test execution does not.

## 5. Implementation context

* `App` takes an injected `Api`; the real client uses relative URLs and Vite proxies `/health` and
  `/api` to the backend. Tests inject committed JSON (no server, no network).
* Findings counts come from `/api/findings?baseline=`; requirements come from
  `/api/artifacts?baseline=`; coverage is derived by matching finding `artifact_ids`. The thread is
  fetched per selected requirement; proposals render only from `proposed_links` with a
  `not accepted` badge.
* A visible note says the findings are the reviewed fixture sample; the UI does not claim computed
  evaluation.
* Targeted reads: `frontend/src/App.test.tsx`, `fixtures/api-responses/findings.*.json`,
  `fixtures/api-responses/threads/*`, `frontend/package.json`, `.github/workflows/ci.yml`.

## 6. Evidence

| Criterion | Check | Result |
| --- | --- | --- |
| SCN-801 | `src/App.test.tsx` "shows counts by type and coverage for baseline-a" | PASS |
| SCN-802 | "reloads when the baseline selector changes" | PASS |
| SCN-803 | "derives counts from the response" | PASS |
| SCN-804 | "labels proposals and keeps them out of coverage" | PASS |
| SCN-805 | "shows the accepted chain and its evidence" | PASS |
| Browser | real backend + Vite: baseline-a/b, proposal thread, mobile viewport, 0 console errors | PASS |

Captured invocations and exits, 2026-11-13T04:20:14Z–04:20:37Z:

```text
backend: pytest backend/tests -q     exit 0  233 passed (also under OS-level network denial)
backend: fixturectl.py verify        exit 0  reproducible and current
backend: ruff check/format           exit 0
backend: git diff --check            exit 0
frontend: npm run build              exit 0  built in 1.42s
frontend: npm test                   exit 0  5 passed
```

Browser demonstration (managed headless browser, servers started/stopped by OMP):
baseline-a counts `candidate_pending_review/lifecycle_review_required/missing_implementation_link/missing_verification_link`
each 1; REQ-001 Covered; REQ-002 Missing verification; REQ-002 thread shows LNK-007 as `not accepted`;
baseline-b adds `reverification_required` and `verification_failed`; REQ-001 thread shows
LNK-001..003 and EV-001; 390×844 renders the summary. Screenshots are hash-listed above at
`docs/reports/omp-as-04-summary/evidence/`.

NOT RUN: visual review by a human stakeholder; link review (AS-06); browser automation in CI.

## 7. File-integrity requirement

The manifest in section 3 is the reviewed snapshot. If any manifest hash changed, the snapshot is
not the one reviewed. Do not edit files, install dependencies, regenerate fixtures, or commit.

## Reviewer instructions (mandatory)

You are the independent CTA implementation reviewer using GPT-6.1 Sol xhigh. Decide whether this exact snapshot satisfies the supplied story, every applicable Gherkin criterion, and repository invariants. Treat OMP's summaries and test results as claims to check against the supplied artifacts and targeted source inspection. Check proposal/accepted/evidence separation, real port compatibility, revision/content-hash semantics, honest errors/501s, independent oracle expectations, offline defaults, and generated-file discipline where relevant. Do not demand implementation of a later milestone. Do not edit files, implement repairs, regenerate fixtures, commit, or delegate. Ask OMP for missing runtime evidence; distinguish observed defects from hypotheses and unavailable checks. Return an AC-by-AC PASS, FAIL, or NOT VERIFIED assessment and actionable findings with stable IDs, severity, blocking status, AC/invariant, path/line, expected/actual behavior, and smallest correction/recheck. Keep optional suggestions and unrelated pre-existing defects separate. Return exactly one verdict: APPROVE, REQUEST_CHANGES, or NEEDS_INPUT. APPROVE requires every applicable criterion/check to be satisfied, no unresolved blocker, and the exact snapshot identified. In later rounds verify prior dispositions and regressions while retaining the complete acceptance assessment. A passing process, passing tests, or exhausted review limit is not approval. Agent review cannot attest human labeling or human link decisions.
