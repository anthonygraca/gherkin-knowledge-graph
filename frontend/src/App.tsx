import { useEffect, useMemo, useState } from "react";

import { ApiError, createApi, type Api } from "./api";
import type {
  Artifact,
  DiscoveryCandidate,
  DiscoveryResponse,
  Evidence,
  Finding,
  Health,
  ProposalRecord,
  ProviderCatalogResponse,
  ReviewConfig,
  ReviewEvent,
  ThreadResponse,
  TraceLink,
} from "./types";
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

type ProviderKind = "fixture" | "model" | "unknown";
type ProviderKinds = Record<string, ProviderKind>;

const HISTORICAL_PROVIDER_KINDS: ProviderKinds = {
  fake: "fixture",
  cocoindex: "model",
  "local-embeddinggemma": "model",
};

function providerLabel(kind: ProviderKind | undefined): string {
  return kind === "fixture"
    ? "fixture-generated"
    : kind === "model"
      ? "model-backed"
      : "provider kind not recorded";
}

function providerIndexLabel(kind: ProviderKind | undefined): string {
  return kind === "model"
    ? "CTA snapshot binding"
    : kind === "fixture"
      ? "Fixture index revision"
      : "Index identity";
}

function provenanceValues(
  provider: string | null,
  model: string | null,
  index: string | null,
  kinds: ProviderKinds,
) {
  const kind = provider ? kinds[provider] : undefined;
  return {
    provider: provider ?? "not recorded",
    model: model ?? "not recorded",
    index: index ?? "not recorded",
    label: providerLabel(kind),
    indexLabel: providerIndexLabel(kind),
  };
}

function provenanceOf(record: ProposalRecord, kinds: ProviderKinds) {
  const snapshot = record.snapshot;
  return provenanceValues(
    snapshot?.provider ??
      (record.link.provenance.discovery_provider as string | undefined) ??
      null,
    snapshot?.model_version ??
      (record.link.provenance.model_version as string | undefined) ??
      null,
    snapshot?.index_revision ??
      (record.link.provenance.index_revision as string | undefined) ??
      null,
    kinds,
  );
}

function provenanceOfLink(link: TraceLink, kinds: ProviderKinds) {
  return provenanceValues(
    (link.provenance.discovery_provider as string | undefined) ?? null,
    (link.provenance.model_version as string | undefined) ?? null,
    (link.provenance.index_revision as string | undefined) ?? null,
    kinds,
  );
}

function candidateProvenance(candidate: DiscoveryCandidate, kinds: ProviderKinds) {
  return provenanceValues(
    candidate.discovery_provider,
    candidate.model_version,
    candidate.index_revision,
    kinds,
  );
}

function provenanceOfEvent(event: ReviewEvent, kinds: ProviderKinds) {
  const snapshot = event.snapshot;
  return provenanceValues(
    snapshot.provider ??
      (event.link.provenance.discovery_provider as string | undefined) ??
      null,
    snapshot.model_version ??
      (event.link.provenance.model_version as string | undefined) ??
      null,
    snapshot.index_revision ??
      (event.link.provenance.index_revision as string | undefined) ??
      null,
    kinds,
  );
}

function CandidatePanel({
  catalog,
  artifacts,
  source,
  onSource,
  provider,
  onProvider,
  custom,
  onCustom,
  providerKinds,
  loading,
  data,
  error,
  onDiscover,
}: {
  catalog: ProviderCatalogResponse;
  artifacts: Artifact[];
  source: string;
  onSource: (value: string) => void;
  provider: string;
  onProvider: (value: string) => void;
  custom: string;
  onCustom: (value: string) => void;
  providerKinds: ProviderKinds;
  loading: boolean;
  data: { baseline: string; source: string; response: DiscoveryResponse } | null;
  error: ApiError | null;
  onDiscover: () => void;
}) {
  const problem = error instanceof ApiError ? error.problem : undefined;
  const failed = problem?.failed_provider;
  const registered = problem?.registered_providers;
  return (
    <section aria-labelledby="candidates-heading">
      <h2 id="candidates-heading">Discovery candidates</h2>
      <p className="source-note">
        Default provider: <strong>{catalog.default}</strong>. Candidates are proposals, never
        accepted links.
      </p>
      <div className="candidate-controls">
        <label>
          Source artifact
          <select
            aria-label="Source artifact"
            value={source}
            onChange={(event) => onSource(event.target.value)}
          >
            {artifacts.map((artifact) => (
              <option key={artifact.artifact_id} value={artifact.artifact_id}>
                {artifact.artifact_id} · {artifact.artifact_type}
              </option>
            ))}
          </select>
        </label>
        <label>
          Provider
          <select
            aria-label="Provider"
            value={provider}
            onChange={(event) => onProvider(event.target.value)}
          >
            {catalog.providers.map((item) => (
              <option key={item.name} value={item.name}>
                {item.name} ({item.kind})
              </option>
            ))}
          </select>
        </label>
        <label>
          Custom provider name
          <input
            type="text"
            aria-label="Custom provider name"
            value={custom}
            placeholder="optional"
            onChange={(event) => onCustom(event.target.value)}
          />
        </label>
        <button type="button" onClick={onDiscover} disabled={loading || !source}>
          {loading ? "Finding candidates…" : "Find candidates"}
        </button>
      </div>
      {error && problem?.code === "provider-not-registered" && (
        <div role="alert" className="error">
          <p>
            Provider unavailable: <code>{failed ?? "unknown"}</code>
          </p>
          <p>
            Registered providers: <code>{(registered ?? catalog.providers.map((p) => p.name)).join(", ")}</code>
          </p>
          <p>“fake” remains selectable; no candidate was substituted.</p>
        </div>
      )}
      {error && problem?.code === "provider-unavailable" && (
        <p role="alert" className="error">
          Provider failed: <code>{failed ?? "unknown"}</code>. No candidates were returned for
          this request; the accepted thread and evidence remain available.
        </p>
      )}
      {error && problem?.code !== "provider-not-registered" && problem?.code !== "provider-unavailable" && (
        <p role="alert" className="error">
          {errorMessage(error)}
        </p>
      )}
      {loading && <p className="loading">Loading candidates…</p>}
      {!loading && !error && data && data.response.candidates.length === 0 && (
        <div className="candidate-empty">
          <p>0 candidates.</p>
          <p>
            Provider <code>{data.response.provider}</code> · model{" "}
            <code>{data.response.model_version}</code> · index{" "}
            <code>{data.response.index_revision}</code>
          </p>
        </div>
      )}
      {!loading && !error && data && data.response.candidates.length > 0 && (
        <ol className="candidate-list" aria-label="Discovery candidates">
          {data.response.candidates.map((candidate) => {
            const provenance = candidateProvenance(candidate, providerKinds);
            return (
              <li
                key={`${candidate.rank}-${candidate.target_id}`}
                data-target-id={candidate.target_id}
              >
                <strong>
                  #{candidate.rank} {candidate.target_id}
                </strong>{" "}
                · <code>{candidate.proposed_relation_type}</code> · score{" "}
                {candidate.score.toFixed(3)}
                <dl>
                  <dt>Provider</dt>
                  <dd>{provenance.provider}</dd>
                  <dt>Model version</dt>
                  <dd>{provenance.model}</dd>
                  <dt>{provenance.indexLabel}</dt>
                  <dd className="commit">{provenance.index}</dd>
                  <dt>Origin</dt>
                  <dd>{provenance.label}</dd>
                </dl>
                {candidate.rationale && <p className="source-note">{candidate.rationale}</p>}
              </li>
            );
          })}
        </ol>
      )}
    </section>
  );
}

function ReviewWorkspace({
  config,
  proposals,
  history,
  availableProviders,
  providerKinds,
  busy,
  error,
  onDecide,
}: {
  config: ReviewConfig;
  proposals: ProposalRecord[];
  history: ReviewEvent[];
  availableProviders: string[];
  providerKinds: ProviderKinds;
  busy: boolean;
  error: string | null;
  onDecide: (linkId: string, decision: "accept" | "reject", reason?: string) => Promise<void>;
}) {
  const [reasons, setReasons] = useState<Record<string, string>>({});
  if (!config.enabled) {
    return (
      <section aria-labelledby="review-heading">
        <h2 id="review-heading">Review proposals</h2>
        <p className="empty">
          Review writes are disabled: no operator identity is configured.
        </p>
      </section>
    );
  }
  return (
    <section aria-labelledby="review-heading">
      <h2 id="review-heading">Review proposals</h2>
      <p className="source-note">Operator {config.operator} · loopback review writes</p>
      {error && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
      {proposals.length === 0 ? (
        <p className="empty">No pending proposals for this requirement.</p>
      ) : (
        proposals.map((record) => {
          const provenance = provenanceOf(record, providerKinds);
          const link = record.link;
          const reason = reasons[link.link_id] ?? "";
          return (
            <article
              className="proposal"
              key={link.link_id}
              data-link-id={link.link_id}
              data-state={link.review_state}
            >
              <h3>
                <code>{link.link_id}</code>{" "}
                <span className="badge warn">{link.review_state}</span>
              </h3>
              <p>
                {link.source_id} → {link.target_id} · <code>{link.relation_type}</code>
              </p>
              <dl>
                <dt>Provider</dt>
                <dd>{provenance.provider}</dd>
                <dt>Model version</dt>
                <dd>{provenance.model}</dd>
                <dt>{provenance.indexLabel}</dt>
                <dd className="commit">{provenance.index}</dd>
                <dt>Origin</dt>
                <dd>{provenance.label}</dd>
              </dl>
              {provenance.provider !== "not recorded" &&
                !availableProviders.includes(provenance.provider) && (
                  <p className="empty">
                    Provider {provenance.provider} is not in the current registry; the recorded
                    provenance is retained.
                  </p>
                )}
              <label>
                Reason for rejecting {link.link_id}
                <input
                  type="text"
                  value={reason}
                  disabled={busy}
                  onChange={(event) =>
                    setReasons((current) => ({ ...current, [link.link_id]: event.target.value }))
                  }
                />
              </label>
              <div className="proposal-actions">
                <button
                  type="button"
                  disabled={busy}
                  onClick={() => onDecide(link.link_id, "accept")}
                >
                  Accept {link.link_id}
                </button>
                <button
                  type="button"
                  disabled={busy || reason.trim().length === 0}
                  onClick={() => onDecide(link.link_id, "reject", reason)}
                >
                  Reject {link.link_id}
                </button>
              </div>
            </article>
          );
        })
      )}
      <h3 id="history-heading">Review history</h3>
      {history.length === 0 ? (
        <p className="empty">No review decisions recorded for this baseline.</p>
      ) : (
        <ul aria-label="Review history" className="review-history">
          {history.map((event) => {
            const provenance = provenanceOfEvent(event, providerKinds);
            return (
              <li key={event.review_revision} data-event={event.event}>
                <code>{event.link.link_id}</code>{" "}
                {event.event === "decision_recorded" ? event.decision : "captured"} by{" "}
                {event.operator} at {event.recorded_at}
                {event.reason ? ` · reason: ${event.reason}` : ""}
                <span className="provenance-line">
                  provider {provenance.provider} · model {provenance.model} ·{" "}
                  {provenance.indexLabel} {provenance.index} · {provenance.label}
                  {provenance.provider !== "not recorded" &&
                  !availableProviders.includes(provenance.provider)
                    ? ` · provider ${provenance.provider} is not in the current registry`
                    : ""}
                </span>
              </li>
            );
          })}
        </ul>
      )}
    </section>
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

function ProposalLinksTable({
  links,
  providerKinds,
  availableProviders,
}: {
  links: TraceLink[];
  providerKinds: ProviderKinds;
  availableProviders: string[];
}) {
  if (links.length === 0) return <p className="empty">None.</p>;
  return (
    <table>
      <thead>
        <tr>
          <th>Link</th>
          <th>Relation</th>
          <th>Source → target</th>
          <th>Provider</th>
          <th>Model version</th>
          <th>Index identity</th>
          <th>Origin</th>
        </tr>
      </thead>
      <tbody>
        {links.map((link) => {
          const provenance = provenanceOfLink(link, providerKinds);
          return (
            <tr key={link.link_id} data-link-id={link.link_id}>
              <td>{link.link_id}</td>
              <td>
                <code>{link.relation_type}</code>
              </td>
              <td>
                {link.source_id} → {link.target_id}
              </td>
              <td>{provenance.provider}</td>
              <td>{provenance.model}</td>
              <td>
                {provenance.indexLabel}: <span className="commit">{provenance.index}</span>
                {provenance.provider !== "not recorded" &&
                !availableProviders.includes(provenance.provider)
                  ? " · provider not in the current registry"
                  : ""}
              </td>
              <td>{provenance.label}</td>
            </tr>
          );
        })}
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
  const [reviewConfig, setReviewConfig] = useState<ReviewConfig | null>(null);
  const [proposalsData, setProposalsData] = useState<{
    baseline: string;
    proposals: ProposalRecord[];
  } | null>(null);
  const [historyData, setHistoryData] = useState<{
    baseline: string;
    events: ReviewEvent[];
  } | null>(null);
  const [reviewError, setReviewError] = useState<string | null>(null);
  const [reviewBusy, setReviewBusy] = useState(false);
  const [reviewRefresh, setReviewRefresh] = useState(0);
  const [providerCatalog, setProviderCatalog] = useState<ProviderCatalogResponse | null>(null);
  const [candidateSource, setCandidateSource] = useState("");
  const [candidateProvider, setCandidateProvider] = useState("");
  const [candidateCustom, setCandidateCustom] = useState("");
  const [candidateData, setCandidateData] = useState<{
    baseline: string;
    source: string;
    response: DiscoveryResponse;
  } | null>(null);
  const [candidateError, setCandidateError] = useState<ApiError | null>(null);
  const [candidateLoading, setCandidateLoading] = useState(false);
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
    let cancelled = false;
    if (typeof client.reviewConfig !== "function") {
      setReviewConfig(null);
      return () => {
        cancelled = true;
      };
    }
    client
      .reviewConfig()
      .then((value) => {
        if (!cancelled) setReviewConfig(value);
      })
      .catch(() => {
        if (!cancelled) setReviewConfig(null);
      });
    return () => {
      cancelled = true;
    };
  }, [client]);

  useEffect(() => {
    let cancelled = false;
    if (typeof client.providers !== "function") return undefined;
    client
      .providers()
      .then((catalog) => {
        if (cancelled) return;
        setProviderCatalog(catalog);
        setCandidateProvider((current) => current || catalog.default);
      })
      .catch(() => {
        if (!cancelled) setProviderCatalog(null);
      });
    return () => {
      cancelled = true;
    };
  }, [client]);

  useEffect(() => {
    setCandidateData(null);
    setCandidateError(null);
  }, [baseline, candidateSource]);

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
        setCandidateSource((current) =>
          current && artifactResponse.artifacts.some((artifact) => artifact.artifact_id === current)
            ? current
            : (artifactResponse.artifacts.find(
                (artifact) => artifact.artifact_type === "scenario",
              )?.artifact_id ??
              requirements[0]?.artifact_id ??
              ""),
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
    const loadThread = reviewConfig?.enabled
      ? client.workspaceThread(selected, baseline)
      : client.thread(selected, baseline);
    loadThread
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
  }, [client, baseline, selected, summaryReady, reviewConfig?.enabled, reviewRefresh]);

  useEffect(() => {
    if (!reviewConfig?.enabled || !baseline) {
      setProposalsData(null);
      setHistoryData(null);
      return;
    }
    let cancelled = false;
    Promise.all([client.workspaceProposals(baseline), client.workspaceHistory(baseline)])
      .then(([proposalResponse, historyResponse]) => {
        if (cancelled) return;
        setProposalsData({ baseline, proposals: proposalResponse.proposals });
        setHistoryData({ baseline, events: historyResponse.events });
      })
      .catch((reason) => {
        if (!cancelled) setReviewError(errorMessage(reason));
      });
    return () => {
      cancelled = true;
    };
  }, [client, baseline, reviewConfig?.enabled, reviewRefresh]);

  const decideProposal = async (
    linkId: string,
    decision: "accept" | "reject",
    reason?: string,
  ): Promise<void> => {
    if (!reviewConfig?.operator) {
      setReviewError("review-identity-unavailable: no operator identity is configured");
      return;
    }
    setReviewBusy(true);
    setReviewError(null);
    try {
      await client.review(linkId, {
        decision,
        reviewer_id: reviewConfig.operator,
        baseline,
        ...(reason !== undefined ? { reason } : {}),
      });
      // A successful write re-reads the server projection; the UI never mutates optimistically.
      setReviewRefresh((current) => current + 1);
    } catch (reason) {
      // A refused write is reported verbatim and does not refresh into a success-looking state.
      setReviewError(errorMessage(reason));
    } finally {
      setReviewBusy(false);
    }
  };

  const findCandidates = async (): Promise<void> => {
    const provider = candidateCustom.trim() || candidateProvider || providerCatalog?.default || "fake";
    setCandidateLoading(true);
    setCandidateError(null);
    setCandidateData(null);
    try {
      const response = await client.discover(candidateSource, provider, baseline);
      setCandidateData({ baseline, source: candidateSource, response });
    } catch (reason) {
      setCandidateError(
        reason instanceof ApiError
          ? reason
          : new ApiError(0, "request-failed", errorMessage(reason)),
      );
    } finally {
      setCandidateLoading(false);
    }
  };

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

  const visibleProposals = useMemo(() => {
    const proposals = proposalsData?.baseline === baseline ? proposalsData.proposals : [];
    if (!thread) return proposals;
    return proposals.filter((record) =>
      thread.artifacts.some(
        (artifact) =>
          artifact.artifact_id === record.link.source_id ||
          artifact.artifact_id === record.link.target_id,
      ),
    );
  }, [proposalsData, baseline, thread]);
  const reviewHistory = historyData?.baseline === baseline ? historyData.events : [];
  const providerKinds = useMemo<ProviderKinds>(
    () => ({
      ...HISTORICAL_PROVIDER_KINDS,
      ...Object.fromEntries(
        (providerCatalog?.providers ?? []).map((item) => [item.name, item.kind]),
      ),
    }),
    [providerCatalog],
  );
  const candidateView =
    candidateData?.baseline === baseline && candidateData?.source === candidateSource
      ? candidateData
      : null;

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
            <ProposalLinksTable
              links={thread.proposed_links}
              providerKinds={providerKinds}
              availableProviders={providerCatalog?.providers.map((item) => item.name) ?? []}
            />

            <h3>Evidence</h3>
            <EvidenceTable evidence={thread.evidence} />
          </>
        )}
      </section>

      {reviewConfig && (
        <ReviewWorkspace
          config={reviewConfig}
          proposals={visibleProposals}
          history={reviewHistory}
          availableProviders={providerCatalog?.providers.map((item) => item.name) ?? []}
          providerKinds={providerKinds}
          busy={reviewBusy}
          error={reviewError}
          onDecide={decideProposal}
        />
      )}

      {providerCatalog && (
        <CandidatePanel
          catalog={providerCatalog}
          artifacts={artifacts}
          source={candidateSource}
          onSource={setCandidateSource}
          provider={candidateProvider}
          onProvider={setCandidateProvider}
          custom={candidateCustom}
          onCustom={setCandidateCustom}
          providerKinds={providerKinds}
          loading={candidateLoading}
          data={candidateView}
          error={candidateError}
          onDiscover={findCandidates}
        />
      )}
    </main>
  );
}
