/// <reference types="vitest/globals" />

import {
  fetchJsonWithTimeout,
  isPlanUnavailableEnvelope,
  ROUTE_RESPONSE_INVALID_PREFIX,
  parseRouteDecisionPayload,
} from "@/lib/coding/proxy-route-payload";

describe("parseRouteDecisionPayload", () => {
  it("accepts route 200 with classification only", () => {
    const r = parseRouteDecisionPayload({
      task_classification: "implementation",
      recommended_route: undefined,
    });
    expect(r.ok).toBe(true);
  });

  it("accepts route 200 with route only", () => {
    const r = parseRouteDecisionPayload({
      recommended_route: "local_route",
    });
    expect(r.ok).toBe(true);
  });

  it("preserves config-blocked route metadata for honest UI display", () => {
    const payload = {
      recommended_route: "codex_cli",
      task_classification: "implementation",
      status: "config_blocked",
      reason_code: "codex_binary_not_found",
    };

    const r = parseRouteDecisionPayload(payload);
    expect(r.ok).toBe(true);
    if (r.ok) {
      expect(r.decision).toBe(payload);
      const reasonCode: string | undefined = r.decision.reason_code;
      expect(r.decision.status).toBe("config_blocked");
      expect(reasonCode).toBe("codex_binary_not_found");
    }
  });

  it("rejects empty object", () => {
    const r = parseRouteDecisionPayload({});
    expect(r.ok).toBe(false);
    if (!r.ok) {
      expect(r.error).toMatch(/missing both/);
    }
  });

  it("rejects non-object", () => {
    expect(parseRouteDecisionPayload(null).ok).toBe(false);
  });
});

describe("isPlanUnavailableEnvelope", () => {
  it("is true for plan_available false (200 not-ready envelope)", () => {
    expect(
      isPlanUnavailableEnvelope({
        plan_available: false,
        reason_code: "plan_not_ready",
        task: { status: "running" },
      }),
    ).toBe(true);
  });

  it("is false when plan_available is true", () => {
    expect(isPlanUnavailableEnvelope({ plan_available: true, coder_packet: {} })).toBe(false);
  });
});

describe("ROUTE_RESPONSE_INVALID_PREFIX", () => {
  it("is stable for workflow gating", () => {
    expect(ROUTE_RESPONSE_INVALID_PREFIX).toBe("route_response_invalid:");
  });
});

describe("fetchJsonWithTimeout", () => {
  const originalFetch = globalThis.fetch;

  afterEach(() => {
    globalThis.fetch = originalFetch;
    vi.restoreAllMocks();
  });

  it("reports non-JSON route bodies instead of pretending the loader is still running", async () => {
    globalThis.fetch = vi.fn(async () => new Response("<html>proxy down</html>", { status: 502 }));

    await expect(
      fetchJsonWithTimeout("/v1/decisions/route", { method: "POST" }, { label: "Route" }),
    ).rejects.toThrow("Route returned non-JSON body (HTTP 502, <html>proxy down</html>).");
  });

  it("reports aborted route requests as timeouts with the route label", async () => {
    globalThis.fetch = vi.fn(async () => {
      throw new DOMException("The operation was aborted.", "AbortError");
    });

    await expect(
      fetchJsonWithTimeout(
        "/v1/decisions/route",
        { method: "POST" },
        { label: "Route", timeoutMs: 1_000 },
      ),
    ).rejects.toThrow("Route timed out after 1s.");
  });
});
