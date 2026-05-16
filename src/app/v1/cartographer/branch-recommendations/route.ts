import { sourceProxyFetch } from "@/lib/source-proxy-origin";

export async function GET() {
  let response;
  try {
    response = await sourceProxyFetch("/v1/cartographer/branch-recommendations", {
      method: "GET",
    });
  } catch (error) {
    return Response.json(
      {
        status: "unavailable",
        write_actions_enabled: false,
        recommended: false,
        branch_name: null,
        reason: null,
        requires_approval: false,
        recommendations: [],
        recommendation_count: 0,
        branch_creation_enabled: false,
        actions_taken: false,
        error: "The dashboard could not reach the Source Proxy Cartographer endpoint.",
        detail: error instanceof Error ? error.message : "Unknown connection error.",
      },
      { status: 200 },
    );
  }

  const text = await response.text();
  const contentType = response.headers.get("content-type") ?? "application/json";
  if (!contentType.includes("application/json")) {
    return new Response(text, {
      headers: { "content-type": contentType },
      status: response.status,
      statusText: response.statusText,
    });
  }

  try {
    const payload = JSON.parse(text) as Record<string, unknown>;
    return Response.json(normalizeBranchRecommendationPayload(payload), {
      status: response.status,
      statusText: response.statusText,
    });
  } catch {
    return new Response(text, {
      headers: { "content-type": contentType },
      status: response.status,
      statusText: response.statusText,
    });
  }
}

function normalizeBranchRecommendationPayload(payload: Record<string, unknown>) {
  const recommendations = Array.isArray(payload.recommendations) ? payload.recommendations : [];
  const first = recommendations[0];
  const firstRecord = first && typeof first === "object" ? (first as Record<string, unknown>) : null;
  return {
    ...payload,
    recommended: payload.recommended ?? recommendations.length > 0,
    branch_name: payload.branch_name ?? firstRecord?.suggested_branch ?? null,
    reason: payload.reason ?? firstRecord?.reason ?? null,
    requires_approval: payload.requires_approval ?? firstRecord?.requires_approval ?? false,
    branch_creation_enabled: payload.branch_creation_enabled ?? false,
    actions_taken: payload.actions_taken ?? false,
  };
}
