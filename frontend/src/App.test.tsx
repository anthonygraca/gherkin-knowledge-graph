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
    await screen.findAllByText("reverification_required");
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

describe("findings drill-down (AS-05)", () => {
  async function findingsRegion(): Promise<HTMLElement> {
    return screen.findByRole("region", { name: "Findings" });
  }

  function findingDetails(type: string, region: HTMLElement): HTMLDetailsElement {
    const badge = within(region).getAllByText(type)[0];
    const details = badge.closest("details");
    if (!details) throw new Error(`no drill-down for ${type}`);
    return details;
  }

  it("shows the rule, baseline, changed artifact and tested evidence for reverification (SCN-2041)", async () => {
    render(<App api={fakeApi()} />);
    await selectBaseline("baseline-b");
    const region = await findingsRegion();
    const reverification = findingDetails("reverification_required", region);
    const expected = readFixture<FindingsResponse>("findings.baseline-b.json").findings.find(
      (finding) => finding.finding_type === "reverification_required",
    )!;

    fireEvent.click(within(reverification).getByRole("button", { name: "Show thread for REQ-001" }));
    await screen.findByRole("region", { name: /Thread for REQ-001/ });

    expect(within(reverification).getAllByText("RULE-REVERIFICATION-REQUIRED")).toHaveLength(2);
    expect(within(reverification).getAllByText(expected.evaluated_baseline).length).toBeGreaterThan(0);
    expect(within(reverification).getAllByText(/CODE-001/).length).toBeGreaterThan(0);
    expect((await within(reverification).findAllByText(/EV-001/)).length).toBeGreaterThan(0);
    const thread = readFixture<ThreadResponse>("threads/REQ-001.baseline-b.json");
    const evidence = thread.evidence.find((item) => item.evidence_id === "EV-001")!;
    expect(within(reverification).getAllByText(evidence.tested_commit).length).toBeGreaterThan(0);
    expect(within(reverification).getAllByText(/not a verification failure/i).length).toBeGreaterThan(0);
  });

  it("presents a confirmed failure differently from reverification (SCN-2042)", async () => {
    render(<App api={fakeApi()} />);
    await selectBaseline("baseline-b");
    const region = await findingsRegion();
    const failure = findingDetails("verification_failed", region);
    const expected = readFixture<FindingsResponse>("findings.baseline-b.json").findings.find(
      (finding) => finding.finding_type === "verification_failed",
    )!;

    // Opening the finding loads its own evidence; the selected thread stays REQ-001.
    fireEvent.click(within(failure).getByText("verification_failed"));
    await within(failure).findAllByText(/EV-003/);

    expect(within(failure).getAllByText("RULE-VERIFICATION-FAILED")).toHaveLength(2);
    expect(within(failure).getAllByText(expected.evaluated_baseline).length).toBeGreaterThan(0);
    expect((await within(failure).findAllByText(/EV-003/)).length).toBeGreaterThan(0);
    expect(within(failure).getByText(/Verification failed/i)).toBeInTheDocument();
    expect(within(failure).queryByText(/not a verification failure/i)).not.toBeInTheDocument();
    const thread = readFixture<ThreadResponse>("threads/REQ-003.baseline-b.json");
    await within(failure).findByText(
      thread.evidence.find((item) => item.evidence_id === "EV-003")!.tested_commit,
    );
    // The selected thread is still REQ-001; the failure's evidence came from its own lookup.
    expect(screen.getByRole("region", { name: /Thread for REQ-001/ })).toBeInTheDocument();
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

    fireEvent.click(within(summaryRegion()).getByRole("button", { name: "REQ-001" }));
    const recovered = await screen.findByRole("region", { name: /Thread for REQ-001/ });
    expect(within(recovered).getByText("LNK-001")).toBeInTheDocument();
    expect(screen.queryByRole("alert")).toBeNull();
  });
});


  it("does not reuse one baseline's evidence for another baseline (AS-05)", async () => {
    render(<App api={fakeApi()} />);
    await selectBaseline("baseline-a");
    const regionA = await screen.findByRole("region", { name: "Findings" });
    const detailsFor = (type: string, region: HTMLElement): HTMLDetailsElement => {
      const badge = within(region).getAllByText(type)[0];
      const element = badge.closest("details");
      if (!element) throw new Error(`no drill-down for ${type}`);
      return element;
    };
    const lifecycle = detailsFor("lifecycle_review_required", regionA);
    fireEvent.click(within(lifecycle).getByText("lifecycle_review_required"));
    await within(lifecycle).findAllByText(/EV-/).catch(() => []);

    await selectBaseline("baseline-b");
    const regionB = await screen.findByRole("region", { name: "Findings" });
    const failure = detailsFor("verification_failed", regionB);
    fireEvent.click(within(failure).getByText("verification_failed"));
    const thread = readFixture<ThreadResponse>("threads/REQ-003.baseline-b.json");
    await within(failure).findByText(
      thread.evidence.find((item) => item.evidence_id === "EV-003")!.tested_commit,
    );
    expect(within(failure).getAllByText(/EV-003/).length).toBeGreaterThan(0);
  });
