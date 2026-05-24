const READ_TIMEOUT_MS = 1500;

export const readOnlyMapEndpointAllowlist = [
  {
    endpoint: "/v1/cartographer/status",
    label: "Status",
    displayPurpose: "Current read-only status and safety limits",
  },
  {
    endpoint: "/v1/cartographer/repo-map",
    label: "Repo map",
    displayPurpose: "Repository map summary",
  },
  {
    endpoint: "/v1/cartographer/blueprints",
    label: "Blueprints",
    displayPurpose: "Blueprint map summary",
  },
  {
    endpoint: "/v1/cartographer/proposals",
    label: "Proposals",
    displayPurpose: "Proposal summary for human review",
  },
  {
    endpoint: "/v1/cartographer/v1-evidence",
    label: "Evidence",
    displayPurpose: "Existing evidence summary",
  },
  {
    endpoint: "/v1/cartographer/audit-trail",
    label: "Audit trail",
    displayPurpose: "Existing audit hints",
  },
  {
    endpoint: "/v1/cartographer/v1-readiness",
    label: "Readiness",
    displayPurpose: "Readiness signal without granting authority",
  },
  {
    endpoint: "/v1/cartographer/trust-score",
    label: "Trust score",
    displayPurpose: "Trust score signal without granting authority",
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
  responseTimeMs: number | null;
  statusCode: number | null;
  failureKind:
    | "none"
    | "timeout"
    | "network-or-fetch-error"
    | "http-error"
    | "blocked"
    | "missing-origin";
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
      responseTimeMs: null,
      statusCode: null,
      failureKind: "missing-origin",
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
      responseTimeMs: Date.now() - startedAt,
      statusCode: null,
      failureKind: "blocked",
    };
  }

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), READ_TIMEOUT_MS);

  try {
    const response = await fetch(`${origin}${source.endpoint}`, {
      method: "GET",
      cache: "no-store",
      signal: controller.signal,
    });

    if (!response.ok) {
      return {
        ...source,
        state: "fallback",
        detail: `Unavailable display data: GET returned ${response.status}.`,
        responseTimeMs: Date.now() - startedAt,
        statusCode: response.status,
        failureKind: "http-error",
      };
    }

    await response.json();

    return {
      ...source,
      state: "live",
      detail: "Read-only request succeeded. Payload is treated as display-only.",
      responseTimeMs: Date.now() - startedAt,
      statusCode: response.status,
      failureKind: "none",
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
      responseTimeMs,
      statusCode: null,
      failureKind: timedOut ? "timeout" : "network-or-fetch-error",
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
  const fallbackReason = hasFallback
    ? "One or more read-only data sources failed, timed out, or returned an error."
    : "All approved read-only data sources responded.";

  return {
    mode: hasFallback ? "static-fallback" : "read-only-live",
    statusLabel: hasFallback ? "Partial fallback" : "Live read-only display",
    summary: hasFallback
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
      fallback_state: hasFallback ? "partial" : "none",
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
