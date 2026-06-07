export const NEXT_HTML_404_MARKER = "404: This page could not be found";

export const ROUTE_UNAVAILABLE_REASON_CODES = {
  html404: "next_v1_routes_unavailable_html_404",
  manifestLost: "next_api_route_manifest_lost_mid_suite",
  hmr: "frontend_api_route_unavailable_after_hmr",
} as const;

export type RouteUnavailableReasonCode =
  (typeof ROUTE_UNAVAILABLE_REASON_CODES)[keyof typeof ROUTE_UNAVAILABLE_REASON_CODES];

export type RouteAvailabilityFailure = {
  route: string;
  status: number;
  contentType: string;
  reasonCode: RouteUnavailableReasonCode;
  bodyExcerpt: string;
};

export function isNextHtml404(response: Response, bodyText: string): boolean {
  if (response.status !== 404) return false;
  const contentType = (response.headers.get("content-type") ?? "").toLowerCase();
  if (!contentType.includes("text/html")) return false;
  return bodyText.includes(NEXT_HTML_404_MARKER);
}

export function isRouteUnavailableResponse(response: Response, bodyText: string): boolean {
  return isNextHtml404(response, bodyText);
}

export function classifyApiRouteAvailabilityFailure(
  route: string,
  response: Response,
  bodyText: string,
  reasonCode: RouteUnavailableReasonCode = ROUTE_UNAVAILABLE_REASON_CODES.html404,
): RouteAvailabilityFailure | null {
  if (!isRouteUnavailableResponse(response, bodyText)) return null;
  return {
    route,
    status: response.status,
    contentType: response.headers.get("content-type") ?? "",
    reasonCode,
    bodyExcerpt: bodyText.slice(0, 240),
  };
}

export function buildRouteUnavailableDiagnostic(
  failure: RouteAvailabilityFailure,
  promptNumber?: number,
): {
  error_summary: string;
  failure_reason: string;
  next_recommended_action: string;
  visible_result_label: "NEEDS FIX";
} {
  const resumeFrom =
    typeof promptNumber === "number" && promptNumber > 0 ? ` prompt ${promptNumber}` : " the failed prompt";
  return {
    error_summary: [
      `reason_code=${failure.reasonCode}`,
      `route=${failure.route}`,
      `status=${failure.status}`,
      `content_type=${failure.contentType || "text/html"}`,
    ].join("; "),
    failure_reason:
      "INFRA: SpiritOS API routes disappeared mid-run. /coding is up, but /v1 routes returned Next HTML 404.",
    next_recommended_action: `Restart spiritos-lan (npm run dev:https:lan) and rerun from${resumeFrom}.`,
    visible_result_label: "NEEDS FIX",
  };
}

export function extractReasonCodeFromSummary(summary: string): string {
  const match = summary.match(/reason_code=([^\s;]+)/);
  return match?.[1]?.trim() ?? "";
}

export function isRouteInfraUnavailableSummary(
  errorSummary: string,
  failureReason: string,
): boolean {
  const reasonCode = extractReasonCodeFromSummary(errorSummary);
  if (
    reasonCode === ROUTE_UNAVAILABLE_REASON_CODES.html404 ||
    reasonCode === ROUTE_UNAVAILABLE_REASON_CODES.manifestLost ||
    reasonCode === ROUTE_UNAVAILABLE_REASON_CODES.hmr
  ) {
    return true;
  }
  return failureReason.startsWith("INFRA:");
}

export async function readResponseBody(response: Response): Promise<string> {
  try {
    return await response.text();
  } catch {
    return "";
  }
}

export async function readApiResponseWithTimeout(
  response: Response,
  route: string,
  timeoutMs = 30_000,
  externalSignal?: AbortSignal | null,
): Promise<string> {
  const schedule = typeof window !== "undefined" ? window.setTimeout.bind(window) : setTimeout;
  const cancel = typeof window !== "undefined" ? window.clearTimeout.bind(window) : clearTimeout;
  return new Promise((resolve, reject) => {
    const timer = schedule(() => {
      reject(new Error(`read_body_timeout:${route}`));
    }, timeoutMs);
    const onExternalAbort = () => {
      cancel(timer);
      reject(new DOMException("Aborted", "AbortError"));
    };
    externalSignal?.addEventListener("abort", onExternalAbort);
    void readResponseBody(response)
      .then((bodyText) => {
        cancel(timer);
        externalSignal?.removeEventListener("abort", onExternalAbort);
        resolve(bodyText);
      })
      .catch((error) => {
        cancel(timer);
        externalSignal?.removeEventListener("abort", onExternalAbort);
        reject(error);
      });
  });
}

export async function readApiResponse(
  response: Response,
  route: string,
  reasonCode: RouteUnavailableReasonCode = ROUTE_UNAVAILABLE_REASON_CODES.html404,
  options: { bodyTimeoutMs?: number; signal?: AbortSignal | null } = {},
): Promise<{
  bodyText: string;
  payload: unknown;
  routeFailure: RouteAvailabilityFailure | null;
}> {
  const bodyText =
    options.bodyTimeoutMs != null
      ? await readApiResponseWithTimeout(response, route, options.bodyTimeoutMs, options.signal)
      : await readResponseBody(response);
  const routeFailure = classifyApiRouteAvailabilityFailure(route, response, bodyText, reasonCode);
  if (routeFailure) {
    return { bodyText, payload: {}, routeFailure };
  }
  let payload: unknown = {};
  if (bodyText.trim()) {
    try {
      payload = JSON.parse(bodyText);
    } catch {
      payload = {};
    }
  }
  return { bodyText, payload, routeFailure: null };
}

export const ROUTE_PROBE_TIMEOUT_MS = 10_000;

async function fetchWithRouteProbeTimeout(
  input: RequestInfo | URL,
  init: RequestInit = {},
  timeoutMs = ROUTE_PROBE_TIMEOUT_MS,
  externalSignal?: AbortSignal | null,
): Promise<Response> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  const onExternalAbort = () => controller.abort();
  externalSignal?.addEventListener("abort", onExternalAbort);
  try {
    return await fetch(input, {
      ...init,
      signal: controller.signal,
    });
  } finally {
    clearTimeout(timeout);
    externalSignal?.removeEventListener("abort", onExternalAbort);
  }
}

function isProbeAbortError(error: unknown, externalSignal?: AbortSignal | null): boolean {
  if (externalSignal?.aborted) return true;
  return error instanceof DOMException && error.name === "AbortError";
}

const PROBE_ROUTES = [
  {
    route: "/v1/coding/runs/recent?limit=1",
    init: { method: "GET" } as RequestInit,
  },
  {
    route: "/v1/tasks/long-running",
    init: {
      body: JSON.stringify({ diagnostic: true }),
      headers: { "content-type": "application/json" },
      method: "POST",
    } as RequestInit,
  },
  {
    route: "/v1/decisions/prompt-packet",
    init: {
      body: JSON.stringify({ diagnostic: true }),
      headers: { "content-type": "application/json" },
      method: "POST",
    } as RequestInit,
  },
] as const;

export type RouteProbeOptions = {
  fetchFn?: typeof fetch;
  reasonCode?: RouteUnavailableReasonCode;
  signal?: AbortSignal | null;
  timeoutMs?: number;
};

export async function probeCriticalV1Routes(
  options: RouteProbeOptions = {},
): Promise<
  | { ok: true }
  | { ok: false; failure: RouteAvailabilityFailure }
  | { ok: false; cancelled: true }
> {
  const fetchFn = options.fetchFn ?? fetch;
  const reasonCode = options.reasonCode ?? ROUTE_UNAVAILABLE_REASON_CODES.html404;
  const timeoutMs = options.timeoutMs ?? ROUTE_PROBE_TIMEOUT_MS;
  for (const probe of PROBE_ROUTES) {
    try {
      const response = await fetchWithRouteProbeTimeout(
        probe.route,
        probe.init,
        timeoutMs,
        options.signal,
      );
      const bodyText = await readResponseBody(response);
      const routeFailure = classifyApiRouteAvailabilityFailure(probe.route, response, bodyText, reasonCode);
      if (routeFailure) {
        return { ok: false, failure: routeFailure };
      }
      if (probe.init.method === "GET" && !response.ok) {
        return {
          ok: false,
          failure: {
            route: probe.route,
            status: response.status,
            contentType: response.headers.get("content-type") ?? "",
            reasonCode,
            bodyExcerpt: bodyText.slice(0, 240),
          },
        };
      }
    } catch (error) {
      if (isProbeAbortError(error, options.signal)) {
        return { ok: false, cancelled: true };
      }
      const message = error instanceof Error ? error.message : String(error);
      return {
        ok: false,
        failure: {
          route: probe.route,
          status: 0,
          contentType: "",
          reasonCode,
          bodyExcerpt: message.slice(0, 240),
        },
      };
    }
  }
  return { ok: true };
}

export async function waitForV1RoutesAfterHmr(
  options: RouteProbeOptions & { maxAttempts?: number; delayMs?: number } = {},
): Promise<
  | { ok: true }
  | { ok: false; failure: RouteAvailabilityFailure }
  | { ok: false; cancelled: true }
> {
  const maxAttempts = options.maxAttempts ?? 5;
  const delayMs = options.delayMs ?? 400;
  let lastFailure: RouteAvailabilityFailure | null = null;
  for (let attempt = 1; attempt <= maxAttempts; attempt += 1) {
    if (options.signal?.aborted) {
      return { ok: false, cancelled: true };
    }
    const probe = await probeCriticalV1Routes({
      ...options,
      reasonCode: ROUTE_UNAVAILABLE_REASON_CODES.hmr,
    });
    if (probe.ok) return { ok: true };
    if ("cancelled" in probe && probe.cancelled) {
      return { ok: false, cancelled: true };
    }
    if ("failure" in probe) {
      lastFailure = probe.failure;
    }
    if (attempt < maxAttempts) {
      await new Promise((resolve) => window.setTimeout(resolve, delayMs));
      if (options.signal?.aborted) {
        return { ok: false, cancelled: true };
      }
    }
  }
  return {
    ok: false,
    failure:
      lastFailure ?? {
        route: "/v1/coding/runs/recent?limit=1",
        status: 0,
        contentType: "",
        reasonCode: ROUTE_UNAVAILABLE_REASON_CODES.hmr,
        bodyExcerpt: "route probe exhausted retries",
      },
  };
}
