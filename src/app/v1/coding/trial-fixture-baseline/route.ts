import { sourceProxyFetch } from "@/lib/source-proxy-origin";
import {
  BACKEND_ROUTE_TRIAL_FIXTURE_PATH,
  COMPONENT_TRIAL_FIXTURE_PATH,
  backendRouteTrialHasOkParam,
  componentTrialHasWarningTone,
} from "@/lib/coding/agent-trials-ui";

type JsonRecord = Record<string, unknown>;

function asRecord(value: unknown): JsonRecord {
  return value && typeof value === "object" ? (value as JsonRecord) : {};
}

async function readWorkspaceFile(path: string): Promise<string | null> {
  try {
    const response = await sourceProxyFetch("/v1/workspace/read", {
      body: JSON.stringify({ path, max_bytes: 64000 }),
      headers: { "content-type": "application/json" },
      method: "POST",
    });
    if (!response.ok) return null;
    const payload = await response.json() as unknown;
    const record = asRecord(payload);
    return typeof record.excerpt === "string"
      ? record.excerpt
      : typeof record.content === "string"
        ? record.content
        : null;
  } catch {
    return null;
  }
}

export async function GET() {
  if (process.env.SPIRIT_CODING_USE_PROXY !== "true") {
    return Response.json(
      { error: "SPIRIT_CODING_USE_PROXY is not true" },
      { status: 409 },
    );
  }

  const [componentExcerpt, backendRouteExcerpt] = await Promise.all([
    readWorkspaceFile(COMPONENT_TRIAL_FIXTURE_PATH),
    readWorkspaceFile(BACKEND_ROUTE_TRIAL_FIXTURE_PATH),
  ]);

  return Response.json({
    backend_route_trial: {
      excerpt: backendRouteExcerpt,
      has_ok_param: backendRouteExcerpt ? backendRouteTrialHasOkParam(backendRouteExcerpt) : null,
      path: BACKEND_ROUTE_TRIAL_FIXTURE_PATH,
    },
    component_trial: {
      excerpt: componentExcerpt,
      has_warning_tone: componentExcerpt ? componentTrialHasWarningTone(componentExcerpt) : null,
      path: COMPONENT_TRIAL_FIXTURE_PATH,
    },
    excerpt: componentExcerpt,
    has_warning_tone: componentExcerpt ? componentTrialHasWarningTone(componentExcerpt) : null,
    path: COMPONENT_TRIAL_FIXTURE_PATH,
  });
}
