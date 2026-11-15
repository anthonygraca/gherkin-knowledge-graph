import type {
  ArtifactListResponse,
  DiscoveryResponse,
  FindingsResponse,
  Health,
  ProblemDetails,
  ProviderCatalogResponse,
  ReviewConfig,
  ThreadResponse,
  TraceLink,
  WorkspaceHistoryResponse,
  WorkspaceProposalsResponse,
  WorkspaceThreadResponse,
} from "./types";

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    detail: string,
    readonly problem?: ProblemDetails,
  ) {
    super(detail);
    this.name = "ApiError";
  }
}

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, {
    ...init,
    headers: { Accept: "application/json", "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    let code = `http-${response.status}`;
    let problem: ProblemDetails | undefined;
    try {
      problem = (await response.json()) as ProblemDetails;
      detail = problem.detail || detail;
      code = problem.code || code;
    } catch {
      // a non-JSON error body keeps the HTTP status as the explanation
    }
    throw new ApiError(response.status, code, detail, problem);
  }
  return (await response.json()) as T;
}

async function getJson<T>(path: string): Promise<T> {
  return requestJson<T>(path, { headers: { Accept: "application/json" } });
}

export interface ReviewDecisionRequest {
  decision: "accept" | "reject";
  reviewer_id: string;
  baseline: string;
  reason?: string;
}

export interface Api {
  health(): Promise<Health>;
  findings(baseline: string): Promise<FindingsResponse>;
  artifacts(baseline: string): Promise<ArtifactListResponse>;
  thread(artifactIds: string, baseline: string): Promise<ThreadResponse>;
  reviewConfig(): Promise<ReviewConfig>;
  workspaceThread(artifactIds: string, baseline: string): Promise<WorkspaceThreadResponse>;
  workspaceProposals(baseline: string): Promise<WorkspaceProposalsResponse>;
  workspaceHistory(baseline: string): Promise<WorkspaceHistoryResponse>;
  review(linkId: string, request: ReviewDecisionRequest): Promise<TraceLink>;
  providers(): Promise<ProviderCatalogResponse>;
  discover(
    artifactId: string,
    provider: string,
    baseline: string,
    topK?: number,
  ): Promise<DiscoveryResponse>;
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
    reviewConfig: () => getJson<ReviewConfig>(`${baseUrl}/api/review/config`),
    workspaceThread: (artifactIds, baseline) =>
      getJson<WorkspaceThreadResponse>(
        `${baseUrl}/api/workspace/threads/${encodeURIComponent(artifactIds)}${query(baseline)}`,
      ),
    workspaceProposals: (baseline) =>
      getJson<WorkspaceProposalsResponse>(`${baseUrl}/api/workspace/proposals${query(baseline)}`),
    workspaceHistory: (baseline) =>
      getJson<WorkspaceHistoryResponse>(`${baseUrl}/api/workspace/history${query(baseline)}`),
    review: (linkId, body) =>
      requestJson<TraceLink>(
        `${baseUrl}/api/links/${encodeURIComponent(linkId)}/review`,
        { method: "POST", body: JSON.stringify(body) },
      ),
    providers: () => getJson<ProviderCatalogResponse>(`${baseUrl}/api/discovery/providers`),
    discover: (artifactId, provider, baseline, topK = 5) =>
      requestJson<DiscoveryResponse>(`${baseUrl}/api/discovery`, {
        method: "POST",
        body: JSON.stringify({
          artifact_id: artifactId,
          provider,
          baseline,
          top_k: topK,
        }),
      }),
  };
}
