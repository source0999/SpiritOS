import { describe, expect, it } from "vitest";

import {
  buildRouteUnavailableDiagnostic,
  classifyApiRouteAvailabilityFailure,
  extractReasonCodeFromSummary,
  isNextHtml404,
  isRouteInfraUnavailableSummary,
  isRouteUnavailableResponse,
  NEXT_HTML_404_MARKER,
  ROUTE_UNAVAILABLE_REASON_CODES,
} from "@/lib/coding/route-availability";

function html404Response(): Response {
  return new Response(
    `<!DOCTYPE html><html><body>${NEXT_HTML_404_MARKER}</body></html>`,
    { status: 404, headers: { "content-type": "text/html; charset=utf-8" } },
  );
}

function json422Response(): Response {
  return new Response(JSON.stringify({ detail: [{ msg: "Field required" }] }), {
    status: 422,
    headers: { "content-type": "application/json" },
  });
}

describe("route availability helpers", () => {
  it("detects Next HTML 404 specifically", () => {
    const response = html404Response();
    const body = NEXT_HTML_404_MARKER;
    expect(isNextHtml404(response, body)).toBe(true);
    expect(isRouteUnavailableResponse(response, body)).toBe(true);
  });

  it("does not treat JSON validation errors as route unavailability", async () => {
    const response = json422Response();
    const body = await response.text();
    expect(isNextHtml404(response, body)).toBe(false);
    expect(classifyApiRouteAvailabilityFailure("/v1/tasks/long-running", response, body)).toBeNull();
  });

  it("builds infra diagnostics with reason_code and rerun guidance", () => {
    const diagnostic = buildRouteUnavailableDiagnostic(
      {
        route: "/v1/tasks/long-running",
        status: 404,
        contentType: "text/html; charset=utf-8",
        reasonCode: ROUTE_UNAVAILABLE_REASON_CODES.html404,
        bodyExcerpt: NEXT_HTML_404_MARKER,
      },
      4,
    );
    expect(diagnostic.failure_reason).toContain("INFRA:");
    expect(diagnostic.error_summary).toContain(
      `reason_code=${ROUTE_UNAVAILABLE_REASON_CODES.html404}`,
    );
    expect(diagnostic.next_recommended_action).toContain("prompt 4");
  });

  it("classifies infra summaries for suite abort logic", () => {
    const summary = `reason_code=${ROUTE_UNAVAILABLE_REASON_CODES.html404}; route=/v1/tasks/long-running`;
    expect(extractReasonCodeFromSummary(summary)).toBe(ROUTE_UNAVAILABLE_REASON_CODES.html404);
    expect(isRouteInfraUnavailableSummary(summary, "INFRA: SpiritOS API routes disappeared mid-run.")).toBe(true);
    expect(isRouteInfraUnavailableSummary("reason_code=coder_sync_timeout", "timeout")).toBe(false);
  });
});
