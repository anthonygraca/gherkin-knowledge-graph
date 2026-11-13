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
