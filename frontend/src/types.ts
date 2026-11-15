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
  failed_provider?: string;
  registered_providers?: string[];
  durability?: string;
}

export interface ProposalSnapshot {
  snapshot_digest: string;
  source_id: string;
  target_id: string;
  relation_type: RelationType;
  baseline: string;
  baseline_commit: string;
  source_content_hash: string;
  target_content_hash: string;
  provider: string | null;
  model_version: string | null;
  index_revision: string | null;
  score: number | null;
  rationale: string | null;
  captured_at: string;
}

export interface ProposalRecord {
  link: TraceLink;
  snapshot: ProposalSnapshot | null;
  binding: "captured" | "legacy";
}

export interface WorkspaceProposalsResponse {
  schema_version: string;
  baseline: string;
  review_revision: number;
  proposals: ProposalRecord[];
}

export interface ReviewEvent {
  review_revision: number;
  event: "proposal_captured" | "decision_recorded";
  recorded_at: string;
  operator: string;
  baseline: string;
  baseline_commit: string;
  link: TraceLink;
  snapshot: ProposalSnapshot;
  decision: "accept" | "reject" | null;
  reason: string | null;
}

export interface WorkspaceHistoryResponse {
  schema_version: string;
  baseline: string;
  review_revision: number;
  events: ReviewEvent[];
}

export interface WorkspaceThreadResponse extends ThreadResponse {
  review_revision: number;
}

export interface ReviewConfig {
  schema_version: string;
  enabled: boolean;
  operator: string | null;
  loopback_only: boolean;
}

export interface DiscoveryCandidate {
  source_id: string;
  target_id: string;
  proposed_relation_type: RelationType;
  rank: number;
  score: number;
  discovery_provider: string;
  model_version: string;
  index_revision: string;
  rationale: string | null;
}

export interface DiscoveryResponse {
  schema_version: string;
  artifact_id: string;
  provider: string;
  model_version: string;
  index_revision: string;
  candidates: DiscoveryCandidate[];
}

export interface ProviderDescriptor {
  name: string;
  kind: "fixture" | "model" | "unknown";
  default: boolean;
}

export interface ProviderCatalogResponse {
  schema_version: string;
  default: string;
  providers: ProviderDescriptor[];
}
