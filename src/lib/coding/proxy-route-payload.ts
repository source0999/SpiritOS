// ── proxy-route-payload ─────────────────────────────────────────────
// Shared guards for /v1/decisions/* fetches so the coding UI never hangs
// silently on malformed JSON or hung post-route requests.

export const ROUTE_RESPONSE_INVALID_PREFIX = "route_response_invalid:";

/** GET …/plan returned 200 but no saved architect plan JSON yet (client treats as null plan). */
export function isPlanUnavailableEnvelope(payload: unknown): boolean {
  return (
    typeof payload === "object" &&
    payload !== null &&
    "plan_available" in payload &&
    (payload as { plan_available?: boolean }).plan_available === false
  );
}

export type RoutePayloadParse =
  | { ok: true; decision: Record<string, unknown> }
  | { ok: false; error: string };

/** Minimal shape check after JSON.parse so downstream UI never assumes fields exist. */
export function parseRouteDecisionPayload(payload: unknown): RoutePayloadParse {
  if (!payload || typeof payload !== "object") {
    return { ok: false, error: "Route payload is not a JSON object." };
  }
  const p = payload as Record<string, unknown>;
  const route = p.recommended_route;
  const classification = p.task_classification;
  if (typeof route !== "string" && typeof classification !== "string") {
    return {
      ok: false,
      error:
        "Route payload missing both recommended_route and task_classification (malformed proxy or BFF merge).",
    };
  }
  return { ok: true, decision: p };
}

export async function fetchJsonWithTimeout(
  url: string,
  init: RequestInit,
  options: { label: string; timeoutMs?: number },
): Promise<{ response: Response; payload: unknown }> {
  const timeoutMs = options.timeoutMs ?? 150_000;
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, { ...init, signal: controller.signal });
    const text = await response.text();
    let payload: unknown;
    try {
      payload = JSON.parse(text) as unknown;
    } catch {
      throw new Error(
        `${options.label} returned non-JSON body (HTTP ${response.status}, ${text.slice(0, 120)}).`,
      );
    }
    return { response, payload };
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new Error(`${options.label} timed out after ${Math.round(timeoutMs / 1000)}s.`);
    }
    if (error instanceof Error && error.name === "AbortError") {
      throw new Error(`${options.label} timed out after ${Math.round(timeoutMs / 1000)}s.`);
    }
    throw error;
  } finally {
    clearTimeout(timer);
  }
}
