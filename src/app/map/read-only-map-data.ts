import { Agent } from "undici";

const READ_TIMEOUT_MS = 5000;
const localHttpsReadOnlyDispatcher = new Agent({
  connect: { rejectUnauthorized: false },
});

export const readOnlyMapEndpointAllowlist = [
  {
    endpoint: "/v1/cartographer/live-state",
    label: "Live state",
    displayPurpose: "Current branch, HEAD, dirty files, blockers, and safe next action",
    expectedFields: ["current_branch", "current_head", "recommended_safety_state"],
    riskyReadOnly: false,
  },
  {
    endpoint: "/v1/cartographer/status",
    label: "Status",
    displayPurpose: "Current read-only status and safety limits",
    expectedFields: ["status", "write_actions_enabled", "safety"],
    riskyReadOnly: false,
  },
  {
    endpoint: "/v1/cartographer/repo-map",
    label: "Repo map",
    displayPurpose: "Repository map summary",
    expectedFields: ["status", "maps", "safety"],
    riskyReadOnly: false,
  },
  {
    endpoint: "/v1/cartographer/sub-cartographers",
    label: "Sub-cartographers",
    displayPurpose: "Display-only sub-cartographer lanes and output contracts",
    expectedFields: ["status", "roles", "routes", "safety"],
    riskyReadOnly: false,
  },
  {
    endpoint: "/v1/cartographer/trust-score",
    label: "Trust score",
    displayPurpose: "Trust score signal without granting authority",
    expectedFields: ["status", "score", "signals", "safety"],
    riskyReadOnly: false,
  },
  {
    endpoint: "/v1/cartographer/audit-trail",
    label: "Audit trail",
    displayPurpose: "Risky read-only audit hints with conservative normalization",
    expectedFields: ["status", "events", "event_count", "safety"],
    riskyReadOnly: true,
  },
] as const;

export const blockedEndpointClasses = [
  "Any endpoint that changes state instead of only reading it",
  "Any approve, review, apply, commit, push, branch, or autonomy expansion path",
  "Any endpoint that mutates files, queues, events, approvals, evidence, receipts, audit ledgers, branches, worktrees, runtime, tests, dashboard, /coding, package, config, env, generated, Scout, API, or Source Proxy state",
];

export const blockedActionClasses = [
  "File writes",
  "Evidence writes",
  "Receipt writes",
  "Durable queue writes",
  "Event storage writes",
  "Queue execution",
  "Command execution through Cartographer",
  "Local shell execution through Cartographer",
  "Automatic task selection",
  "Approval generation",
  "Approval recording",
  "Self-approval",
  "Approval-token runtime creation",
  "Branch or worktree creation",
  "Commit, push, merge, stash, checkout, clean, or delete",
  "Runtime, test, dashboard, /coding, package, config, env, generated, Scout, API, or Source Proxy mutation",
];

type EndpointState = {
  endpoint: string;
  label: string;
  displayPurpose: string;
  state: "live" | "fallback" | "blocked";
  detail: string;
  sourceSummary: string[];
  responseTimeMs: number | null;
  statusCode: number | null;
  failureKind:
    | "none"
    | "timeout"
    | "network-or-fetch-error"
    | "http-error"
    | "malformed-shape"
    | "blocked"
    | "missing-origin";
  shapeSummary: string;
  riskyReadOnly: boolean;
};

type RecommendationPacket = {
  packet_id: string;
  status_date: string;
  packet_kind: "display-only-read-only-map";
  fallback_state: "none" | "active" | "partial";
  fallback_reason: string;
  source_endpoints_observed: string[];
  source_endpoints_blocked: string[];
  protected_lane_findings: string[];
  blocked_action_classes: string[];
  recommendation_summary: string;
  manual_next_step: string;
  authority_denials: string[];
};

export type ReadOnlyMapData = {
  mode: "read-only-live" | "static-fallback";
  statusLabel: string;
  summary: string;
  timeoutMs: number;
  fallbackProof: string[];
  endpoints: EndpointState[];
  recommendationPacket: RecommendationPacket;
};

function fallbackData(detail: string): ReadOnlyMapData {
  return {
    mode: "static-fallback",
    statusLabel: "Static fallback",
    summary:
      "Live read-only data is unavailable. /map is showing safe fallback text with every action still blocked.",
    timeoutMs: READ_TIMEOUT_MS,
    fallbackProof: [
      "No request origin was available for read-only data.",
      "Every read-only source is marked fallback.",
      "Recommendation packet remains display-only.",
      "Safety denials remain visible.",
    ],
    endpoints: readOnlyMapEndpointAllowlist.map((source) => ({
      ...source,
      state: "fallback",
      detail,
      sourceSummary: ["Source was not read; safe fallback is active."],
      responseTimeMs: null,
      statusCode: null,
      failureKind: "missing-origin",
      shapeSummary: "not-read",
    })),
    recommendationPacket: {
      packet_id: "plan-1-read-only-map-fallback",
      status_date: "2026-05-22",
      packet_kind: "display-only-read-only-map",
      fallback_state: "active",
      fallback_reason: detail,
      source_endpoints_observed: [],
      source_endpoints_blocked: blockedEndpointClasses,
      protected_lane_findings: [
        "/coding remains protected",
        "dashboard files remain protected",
        "src/app/v1/** remains protected",
        "source_proxy/** remains protected",
        "tests remain protected",
      ],
      blocked_action_classes: blockedActionClasses,
      recommendation_summary:
        "Stay in read-only fallback. Do not approve, apply, execute, write, queue, commit, push, branch, or expand authority.",
      manual_next_step:
        "Review read-only source availability manually before any future expansion beyond Plan 1 display.",
      authority_denials: [
        "full auto is not granted",
        "limited unattended operation is not granted",
        "write authority is not granted",
        "command execution authority is not granted",
        "queue execution authority is not granted",
      ],
    },
  };
}

function isAllowedEndpoint(endpoint: string): boolean {
  return readOnlyMapEndpointAllowlist.some((source) => source.endpoint === endpoint);
}

async function readEndpoint(
  origin: string,
  source: (typeof readOnlyMapEndpointAllowlist)[number],
): Promise<EndpointState> {
  const startedAt = Date.now();

  if (!isAllowedEndpoint(source.endpoint)) {
    return {
      ...source,
      state: "blocked",
      detail: "Blocked source: this address is not approved for read-only display.",
      sourceSummary: ["Source was blocked before read; safe fallback is active."],
      responseTimeMs: Date.now() - startedAt,
      statusCode: null,
      failureKind: "blocked",
      shapeSummary: "blocked-before-read",
    };
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), READ_TIMEOUT_MS);

  try {
    const response = await fetch(`${origin}${source.endpoint}`, {
      ...readOnlyFetchInit(origin),
      signal: controller.signal,
    });

    if (!response.ok) {
      return {
        ...source,
        state: "fallback",
        detail: `Unavailable display data: GET returned ${response.status}.`,
        sourceSummary: ["Source did not return usable display data."],
        responseTimeMs: Date.now() - startedAt,
        statusCode: response.status,
        failureKind: "http-error",
        shapeSummary: "not-read",
      };
    }

    const payload: unknown = await response.json();
    const shape = normalizeEndpointShape(source.endpoint, payload);

    if (!shape.valid) {
      return {
        ...source,
        state: "fallback",
        detail: shape.detail,
        sourceSummary: ["Source payload was malformed; safe fallback is active."],
        responseTimeMs: Date.now() - startedAt,
        statusCode: response.status,
        failureKind: "malformed-shape",
        shapeSummary: shape.summary,
      };
    }

    return {
      ...source,
      state: "live",
      detail: source.riskyReadOnly
        ? "Risky read-only request succeeded. Payload is reduced to display-only availability."
        : "Read-only request succeeded. Payload is treated as display-only.",
      sourceSummary: summarizeEndpointPayload(source.endpoint, payload),
      responseTimeMs: Date.now() - startedAt,
      statusCode: response.status,
      failureKind: "none",
      shapeSummary: shape.summary,
    };
  } catch (error) {
    const responseTimeMs = Date.now() - startedAt;
    const timedOut = error instanceof DOMException && error.name === "AbortError";

    return {
      ...source,
      state: "fallback",
      detail: timedOut
        ? "Unavailable display data: request reached the read-only timeout."
        : "Unavailable display data: request failed before a response was received.",
      sourceSummary: ["Source could not be read; safe fallback is active."],
      responseTimeMs,
      statusCode: null,
      failureKind: timedOut ? "timeout" : "network-or-fetch-error",
      shapeSummary: "not-read",
    };
  } finally {
    clearTimeout(timeout);
  }
}

export async function getReadOnlyMapData(origin: string | null): Promise<ReadOnlyMapData> {
  if (!origin) {
    return fallbackData("Unavailable display data: request origin was not available.");
  }

  const endpoints = await Promise.all(
    readOnlyMapEndpointAllowlist.map((source) => readEndpoint(origin, source)),
  );
  const liveEndpoints = endpoints
    .filter((endpoint) => endpoint.state === "live")
    .map((endpoint) => endpoint.endpoint);
  const fallbackEndpoints = endpoints
    .filter((endpoint) => endpoint.state !== "live")
    .map((endpoint) => endpoint.endpoint);
  const hasFallback = fallbackEndpoints.length > 0;
  const allEndpointsFailed = liveEndpoints.length === 0;
  const fallbackReason = hasFallback
    ? allEndpointsFailed
      ? "All approved read-only data sources failed, timed out, returned an error, or returned malformed shape."
      : "One or more read-only data sources failed, timed out, returned an error, or returned malformed shape."
    : "All approved read-only data sources responded.";

  return {
    mode: allEndpointsFailed ? "static-fallback" : "read-only-live",
    statusLabel: allEndpointsFailed
      ? "Static fallback"
      : hasFallback
        ? "Partial live read-only display"
        : "Live read-only display",
    summary: allEndpointsFailed
      ? "Live read-only data is unavailable. /map is showing safe fallback text with every action still blocked."
      : hasFallback
      ? "At least one read-only source is unavailable. /map is preserving safe fallback text."
      : "All approved read-only sources responded. Data remains display-only and cannot grant authority.",
    timeoutMs: READ_TIMEOUT_MS,
    fallbackProof: hasFallback
      ? [
          fallbackReason,
          "Unavailable sources are listed in the debug details.",
          "Safe fallback text remains visible.",
          "No repair, approval, apply, execute, queue, command, commit, push, or branch control is rendered.",
        ]
      : [
          fallbackReason,
          "All payloads are treated as display-only.",
          "Blocked source and action classes remain visible.",
          "No authority is promoted by successful reads.",
        ],
    endpoints,
    recommendationPacket: {
      packet_id: hasFallback
        ? "plan-1-read-only-map-partial-fallback"
        : "plan-1-read-only-map-display-only",
      status_date: "2026-05-22",
      packet_kind: "display-only-read-only-map",
      fallback_state: allEndpointsFailed ? "active" : hasFallback ? "partial" : "none",
      fallback_reason: fallbackReason,
      source_endpoints_observed: liveEndpoints,
      source_endpoints_blocked: blockedEndpointClasses.concat(fallbackEndpoints),
      protected_lane_findings: [
        "/coding remains protected",
        "dashboard files remain protected",
        "src/app/v1/** remains protected",
        "source_proxy/** remains protected",
        "tests remain protected",
      ],
      blocked_action_classes: blockedActionClasses,
      recommendation_summary:
        "Keep Plan 1 display-only. Recommendations require human review and cannot approve or execute actions.",
      manual_next_step:
        "Review the read-only data manually and stop before any authority increase.",
      authority_denials: [
        "full auto is not granted",
        "limited unattended operation is not granted",
        "write authority is not granted",
        "command execution authority is not granted",
        "queue execution authority is not granted",
      ],
    },
  };
}

type ShapeResult = {
  valid: boolean;
  summary: string;
  detail: string;
};

function normalizeEndpointShape(endpoint: string, payload: unknown): ShapeResult {
  if (!isRecord(payload)) {
    return malformed("top-level payload is not an object");
  }

  switch (endpoint) {
    case "/v1/cartographer/live-state":
      return hasAnyField(payload, ["current_branch", "current_head", "recommended_safety_state"])
        ? valid("live-state object")
        : malformed("live-state payload did not include expected repository state fields");
    case "/v1/cartographer/status":
      return hasAnyField(payload, ["status", "write_actions_enabled", "safety"])
        ? valid("status object")
        : malformed("status payload did not include expected safety fields");
    case "/v1/cartographer/repo-map":
      return Array.isArray(payload.maps) || hasAnyField(payload, ["project_count", "safety"])
        ? valid("repo-map object")
        : malformed("repo-map payload did not include map or safety fields");
    case "/v1/cartographer/sub-cartographers":
      return Array.isArray(payload.roles) || Array.isArray(payload.routes)
        ? valid("sub-cartographers object")
        : malformed("sub-cartographers payload did not include role or route arrays");
    case "/v1/cartographer/trust-score":
      return typeof payload.score === "number" || Array.isArray(payload.signals)
        ? valid("trust-score object")
        : malformed("trust-score payload did not include score or signal fields");
    case "/v1/cartographer/audit-trail":
      return Array.isArray(payload.events) || typeof payload.event_count === "number"
        ? valid("audit-trail object reduced to event availability")
        : malformed("audit-trail payload did not include event list or event count fields");
    default:
      return malformed("endpoint is not part of the Phase 1 read-only shape contract");
  }
}

function summarizeEndpointPayload(endpoint: string, payload: unknown): string[] {
  if (!isRecord(payload)) {
    return ["Source responded, but no display summary was available."];
  }

  switch (endpoint) {
    case "/v1/cartographer/live-state":
      return [
        `Branch: ${stringValue(payload.current_branch) ?? "unknown"}`,
        `HEAD: ${stringValue(payload.current_head) ?? "unknown"}`,
        `Safety state: ${stringValue(payload.recommended_safety_state) ?? "unknown"}`,
        `Dirty files: ${stringArray(payload.tracked_dirty_files).length} tracked, ${stringArray(payload.untracked_files).length} untracked`,
      ];
    case "/v1/cartographer/status":
      return [
        `Status: ${stringValue(payload.status) ?? "unknown"}`,
        `Write actions enabled: ${booleanLabel(payload.write_actions_enabled)}`,
        `Configured roots: ${recordArray(payload.configured_roots).length}`,
        `Pending proposals: ${numberValue(payload.pending_proposals) ?? 0}`,
      ];
    case "/v1/cartographer/repo-map":
      return [
        `Status: ${stringValue(payload.status) ?? "unknown"}`,
        `Repo maps: ${recordArray(payload.maps).length}`,
        `Project count: ${numberValue(payload.project_count) ?? 0}`,
        `Write policy: ${safetyString(payload.safety, "write_policy") ?? "read-only fallback"}`,
      ];
    case "/v1/cartographer/sub-cartographers":
      return [
        `Roles observed: ${recordArray(payload.roles).length}`,
        `Routes observed: ${recordArray(payload.routes).length}`,
        `Outputs observed: ${recordArray(payload.outputs).length}`,
        ...recordArray(payload.roles)
          .map((role) => {
            const label = stringValue(role.label) ?? stringValue(role.role_id);
            const authority = stringValue(role.max_authority) ?? "read_only";
            return label ? `${label}: ${authority}` : null;
          })
          .filter((item): item is string => item !== null),
      ];
    case "/v1/cartographer/trust-score": {
      const signals = recordArray(payload.signals);
      const failedSignals = signals.filter((signal) => signal.passed === false);
      return [
        `Score: ${numberValue(payload.score) ?? "unknown"}`,
        `Grade: ${stringValue(payload.grade) ?? "unknown"}`,
        `Authority granted: ${booleanLabel(payload.authority_granted)}`,
        `Signals: ${signals.length} total, ${failedSignals.length} need review`,
        stringValue(payload.explanation) ?? "Trust score is advisory only.",
      ];
    }
    case "/v1/cartographer/audit-trail": {
      const events = recordArray(payload.events);
      const firstEvent = events[0];
      return [
        `Events visible: ${numberValue(payload.event_count) ?? events.length}`,
        `First event: ${firstEvent ? stringValue(firstEvent.event) ?? "unknown" : "none"}`,
        `First result: ${firstEvent ? stringValue(firstEvent.result) ?? "unknown" : "none"}`,
        "Audit trail is reduced to review-only availability and summary text.",
      ];
    }
    default:
      return ["Source responded, but no display summary was available."];
  }
}

function hasAnyField(payload: Record<string, unknown>, fields: string[]): boolean {
  return fields.some((field) => field in payload);
}

function stringValue(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value : null;
}

function numberValue(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function stringArray(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.filter((item): item is string => typeof item === "string");
}

function recordArray(value: unknown): Record<string, unknown>[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.filter(isRecord);
}

function booleanLabel(value: unknown): string {
  if (typeof value === "boolean") {
    return value ? "yes" : "no";
  }

  return "unknown";
}

function safetyString(value: unknown, field: string): string | null {
  if (!isRecord(value)) {
    return null;
  }

  return stringValue(value[field]);
}

function valid(summary: string): ShapeResult {
  return {
    valid: true,
    summary,
    detail: "Read-only endpoint shape matched the Phase 1 display contract.",
  };
}

function malformed(reason: string): ShapeResult {
  return {
    valid: false,
    summary: "malformed-shape",
    detail: `Unavailable display data: ${reason}.`,
  };
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function readOnlyFetchInit(origin: string): RequestInit {
  const init = {
    method: "GET",
    cache: "no-store",
    ...(isLocalHttpsOrigin(origin)
      ? { dispatcher: localHttpsReadOnlyDispatcher }
      : {}),
  };

  return init as RequestInit;
}

function isLocalHttpsOrigin(origin: string): boolean {
  try {
    const url = new URL(origin);
    return url.protocol === "https:" && isLocalDevHost(url.hostname);
  } catch {
    return false;
  }
}

function isLocalDevHost(hostname: string): boolean {
  return (
    hostname === "localhost" ||
    hostname === "127.0.0.1" ||
    hostname === "::1" ||
    hostname === "0.0.0.0" ||
    hostname.startsWith("10.") ||
    hostname.startsWith("192.168.") ||
    /^172\.(1[6-9]|2\d|3[0-1])\./.test(hostname)
  );
}
