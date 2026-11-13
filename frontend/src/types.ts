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
