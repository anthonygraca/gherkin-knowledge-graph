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

const FINDING_MEANING: Record<string, string> = {
  reverification_required:
    "Reverification requested: relevant content changed after this recorded run. This is not a verification failure.",
  verification_failed:
    "Verification failed: a recorded execution at this baseline failed. Its failing step and run are named below.",
  missing_verification_link:
    "No accepted verification scenario is linked, so the requirement has no verification claim.",
  missing_implementation_link:
    "No accepted implementation link is recorded, so the scenario has no verified implementation claim.",
  candidate_pending_review:
    "A proposal exists and has not been reviewed. A proposal is not an accepted relationship.",
  lifecycle_review_required:
    "The requirement is superseded but still carries accepted relationships; a lifecycle decision is required.",
  undefined_step: "The framework reported a Gherkin step with no matching definition.",
  ambiguous_step: "The framework reported a Gherkin step matching more than one definition.",
  execution_failed: "A recorded scenario execution failed.",
};

const FINDING_TONE: Record<string, string> = {
  verification_failed: "bad",
  execution_failed: "bad",
  undefined_step: "bad",
  ambiguous_step: "bad",
  reverification_required: "warn",
  missing_verification_link: "bad",
  missing_implementation_link: "warn",
  candidate_pending_review: "warn",
  lifecycle_review_required: "warn",
};

export function FindingDrilldown({
  finding,
  evidence,
  onSelect,
  onOpen,
}: {
  finding: Finding;
  evidence: Evidence[];
  onSelect: (artifactId: string) => void;
  onOpen: (finding: Finding) => void;
}) {
  const requirement = finding.artifact_ids.find((id) => id.startsWith("REQ-"));
  const related = evidence.filter((item) => finding.evidence_ids.includes(item.evidence_id));
  return (
    <details
      className="finding"
      data-finding-id={finding.finding_id}
      onToggle={(event) => {
        if (event.currentTarget.open) onOpen(finding);
      }}
    >
      <summary>
        <span className={`badge ${FINDING_TONE[finding.finding_type] ?? "warn"}`}>
          {finding.finding_type}
        </span>{" "}
        <code>{finding.rule_id}</code> · severity {finding.severity}
        {requirement ? (
          <>
            <span> · {requirement} </span>
            <button
              type="button"
              className="link-button"
              onClick={(event) => {
                event.preventDefault();
                onSelect(requirement);
              }}
            >
              Show thread for {requirement}
            </button>
          </>
        ) : (
          <span> · {finding.artifact_ids.join(", ")}</span>
        )}
      </summary>
      <dl className="finding-detail">
        <dt>Meaning</dt>
        <dd>{FINDING_MEANING[finding.finding_type] ?? "Deterministic finding."}</dd>
        <dt>Rule</dt>
        <dd>
          <code>{finding.rule_id}</code>
        </dd>
        <dt>Evaluated baseline</dt>
        <dd>
          <code>{finding.evaluated_baseline}</code>
        </dd>
        <dt>Artifacts and revisions</dt>
        <dd>
          <ul>
            {finding.artifact_ids.map((artifactId) => (
              <li key={artifactId}>
                <code>{artifactId}</code>{" "}
                <span className="commit">{finding.artifact_revisions[artifactId] ?? "unknown"}</span>
              </li>
            ))}
          </ul>
        </dd>
        <dt>Evidence</dt>
        <dd>
          {finding.evidence_ids.length === 0 ? (
            <span className="empty">No execution evidence applies.</span>
          ) : related.length === 0 ? (
            <span className="empty">
              {finding.evidence_ids.join(", ")} — open the requirement thread to load the recorded
              run.
            </span>
          ) : (
            <ul>
              {related.map((item) => (
                <li key={item.evidence_id}>
                  <code>{item.evidence_id}</code> {item.result} · tested commit{" "}
                  <span className="commit">{item.tested_commit}</span> · executed {item.executed_at}
                </li>
              ))}
            </ul>
          )}
        </dd>
        <dt>Explanation</dt>
        <dd>{finding.explanation}</dd>
      </dl>
    </details>
  );
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
  const [healthError, setHealthError] = useState<string | null>(null);
  const [summaryError, setSummaryError] = useState<string | null>(null);
  const [threadError, setThreadError] = useState<string | null>(null);
  const [summaryFailed, setSummaryFailed] = useState(false);
  const [threadFailed, setThreadFailed] = useState(false);
  // Evidence is loaded per requirement when a finding is opened, so a finding never borrows
  // another requirement's thread (AS-05).
  const [evidenceCache, setEvidenceCache] = useState<Record<string, Evidence[]>>({});

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
        if (!cancelled) setHealthError(errorMessage(reason));
      });
    return () => {
      cancelled = true;
    };
  }, [client]);

  useEffect(() => {
    if (!baseline) return;
    let cancelled = false;
    setSummaryError(null);
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
          setSummaryError(errorMessage(reason));
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
    setThreadError(null);
    client
      .thread(selected, baseline)
      .then((value) => {
        if (!cancelled) setThreadData({ baseline, rootId: selected, thread: value });
      })
      .catch((reason) => {
        if (!cancelled) {
          setThreadFailed(true);
          setThreadError(errorMessage(reason));
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

  const loadFindingEvidence = (finding: Finding) => {
    const requirements = finding.artifact_ids.filter((id) => id.startsWith("REQ-"));
    for (const requirement of requirements) {
      // Cache and in-flight keys are scoped by baseline: a response fetched for baseline-a must
      // never satisfy a baseline-b finding, and a stale response must not overwrite the current
      // selection.
      const key = `${baseline}:${requirement}`;
      if (evidenceCache[key] !== undefined) continue;
      setEvidenceCache((current) => (current[key] !== undefined ? current : { ...current, [key]: [] }));
      client
        .thread(requirement, baseline)
        .then((value) => {
          setEvidenceCache((current) => ({ ...current, [key]: value.evidence }));
        })
        .catch(() => {
          // Leave the empty marker removed so a later open retries; the finding still shows its
          // evidence ids rather than claiming there is none.
          setEvidenceCache((current) => {
            const next = { ...current };
            delete next[key];
            return next;
          });
        });
    }
  };

  const evidenceFor = (finding: Finding): Evidence[] => {
    const collected = new Map<string, Evidence>();
    for (const artifactId of finding.artifact_ids) {
      for (const item of evidenceCache[`${baseline}:${artifactId}`] ?? []) {
        collected.set(item.evidence_id, item);
      }
    }
    if (collected.size > 0) return [...collected.values()];
    return thread?.evidence ?? [];
  };

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
            <span className="source-note">Findings: evaluated rule set</span>
          </div>
        )}
      </header>

      {(healthError || summaryError || threadError) && (
        <p role="alert" className="error">
          {healthError ?? summaryError ?? threadError}
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

      <section aria-labelledby="findings-heading">
        <h2 id="findings-heading">Findings</h2>
        {!summaryReady ? (
          <p className="empty">Loading the findings drill-down…</p>
        ) : findings.length === 0 ? (
          <p className="empty">No findings at this baseline.</p>
        ) : (
          findings.map((finding) => (
            <FindingDrilldown
              key={finding.finding_id}
              finding={finding}
              evidence={evidenceFor(finding)}
              onSelect={setSelected}
              onOpen={loadFindingEvidence}
            />
          ))
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
