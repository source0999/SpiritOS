import { sourceProxyFetch } from "@/lib/source-proxy-origin";

function degradedTelemetryStatus(detail: string) {
  return Response.json(
    {
      access_scope:
        "telemetry_unavailable: this fallback only reports that the Source proxy status endpoint could not be reached.",
      approval_boundaries: {},
      available_routes: [],
      context_bundle_status: {
        bundles: [],
        content_included: false,
      },
      disabled_tools: [],
      enabled_tools: [],
      error:
        "The coding page could not reach the Source proxy telemetry endpoint. Coding approvals still depend on their own preview gates.",
      detail,
      manifest_version: "telemetry-degraded",
      service: "source-proxy",
      status: "telemetry_unavailable",
      windows_bridge_status: {
        status: "not_probed",
      },
    },
    { status: 200 },
  );
}

export async function GET() {
  if (process.env.SPIRIT_CODING_USE_PROXY !== "true") {
    return Response.json(
      { error: "SPIRIT_CODING_USE_PROXY is not true" },
      { status: 409 },
    );
  }

  let response;
  try {
    response = await sourceProxyFetch("/v1/self/status", {
      method: "GET",
    });
  } catch (error) {
    return degradedTelemetryStatus(
      error instanceof Error ? error.message : "Unknown connection error.",
    );
  }

  return new Response(await response.text(), {
    headers: {
      "content-type": response.headers.get("content-type") ?? "application/json",
    },
    status: response.status,
    statusText: response.statusText,
  });
}
