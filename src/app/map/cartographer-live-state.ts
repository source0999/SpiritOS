import { Agent } from "undici";

const LIVE_STATE_ENDPOINT = "/v1/cartographer/live-state";
const localHttpsLiveStateDispatcher = new Agent({
  connect: { rejectUnauthorized: false },
});

export type CartographerLiveState = {
  available: boolean;
  currentBranch: string | null;
  currentHead: string | null;
  recommendedSafetyState: "clear" | "caution" | "blocked";
  trackedDirtyFiles: string[];
  untrackedFiles: string[];
  protectedLaneMatches: { path: string; lane: string }[];
  blockerReasons: string[];
  collectedAt: string | null;
  safeNextAction: string;
  detail: string;
  truthPacket: CartographerTruthPacket;
};

export type CartographerTruthPacket = {
  schemaVersion: string;
  status: "no_go" | "blocked" | "caution" | "clear" | "unknown" | "stale";
  decisionDefault: "no_go";
  advisoryOnly: boolean;
  facts: {
    totalDirtyCount: number;
    protectedLaneCount: number;
    gitAvailable: boolean;
  };
  recommendations: {
    confidence: string;
    noGoReason: string;
    safeNextAction: string;
  };
  stateFlags: {
    verified: boolean;
    blocked: boolean;
    stale: boolean;
    unknown: boolean;
    caution: boolean;
    clear: boolean;
    noGo: boolean;
    advisoryOnly: boolean;
  };
  authority: {
    authorityGranted: boolean;
    writeActionsEnabled: boolean;
    queueAuthorityGranted: boolean;
    canMutate: boolean;
  };
  evidenceLinks: CartographerTruthEvidenceLink[];
  verifiedFields: string[];
  unknownFields: string[];
  staleFields: string[];
};

export type CartographerTruthEvidenceLink = {
  label: string;
  kind: string;
  href: string;
  summary: string;
  authorityGranted: boolean;
  reviewOnly: boolean;
};

const unavailableState: CartographerLiveState = {
  available: false,
  currentBranch: null,
  currentHead: null,
  recommendedSafetyState: "blocked",
  trackedDirtyFiles: [],
  untrackedFiles: [],
  protectedLaneMatches: [],
  blockerReasons: ["live state endpoint is unavailable"],
  collectedAt: null,
  safeNextAction:
    "Stop and manually inspect repository state before using Cartographer for decisions.",
  detail: "Live Cartographer state could not be read.",
  truthPacket: unavailableTruthPacket("live_state_unavailable"),
};

export async function getCartographerLiveState(
  origin: string | null,
): Promise<CartographerLiveState> {
  if (!origin) {
    return {
      ...unavailableState,
      detail: "Request origin was unavailable, so live state was not fetched.",
    };
  }

  try {
    const response = await fetch(`${origin}${LIVE_STATE_ENDPOINT}`, {
      ...readOnlyFetchInit(origin),
    });

    if (!response.ok) {
      return {
        ...unavailableState,
        detail: `Live state endpoint returned HTTP ${response.status}.`,
      };
    }

    const payload: unknown = await response.json();
    return normalizeLiveState(payload);
  } catch (error) {
    return {
      ...unavailableState,
      detail:
        error instanceof Error
          ? `Live state request failed: ${error.message}`
          : "Live state request failed.",
    };
  }
}

function normalizeLiveState(payload: unknown): CartographerLiveState {
  if (!isRecord(payload)) {
    return {
      ...unavailableState,
      detail: "Live state endpoint returned an unexpected payload shape.",
    };
  }

  const recommendedSafetyState = safetyStateFor(
    stringValue(payload.recommended_safety_state),
  );
  const blockerReasons = stringArray(payload.blocker_reasons);
  const trackedDirtyFiles = stringArray(payload.tracked_dirty_files);
  const untrackedFiles = stringArray(payload.untracked_files);
  const protectedLaneMatches = laneMatches(payload.protected_lane_matches);
  const truthPacket = normalizeTruthPacket(payload.truth_packet, {
    gitAvailable: booleanValue(payload.git_available) ?? true,
    protectedLaneCount: protectedLaneMatches.length,
    totalDirtyCount: trackedDirtyFiles.length + untrackedFiles.length,
  });

  return {
    available: true,
    currentBranch: stringValue(payload.current_branch),
    currentHead: stringValue(payload.current_head),
    recommendedSafetyState,
    trackedDirtyFiles,
    untrackedFiles,
    protectedLaneMatches,
    blockerReasons,
    collectedAt: stringValue(payload.collected_at),
    safeNextAction: safeNextActionFor(
      recommendedSafetyState,
      blockerReasons,
      trackedDirtyFiles.length + untrackedFiles.length,
    ),
    detail: "Live state endpoint responded with display-only repository state.",
    truthPacket,
  };
}

function normalizeTruthPacket(
  value: unknown,
  fallbackFacts: {
    gitAvailable: boolean;
    protectedLaneCount: number;
    totalDirtyCount: number;
  },
): CartographerTruthPacket {
  if (!isRecord(value)) {
    return unavailableTruthPacket("truth_packet_missing_or_malformed", fallbackFacts);
  }

  const facts = isRecord(value.facts) ? value.facts : {};
  const recommendations = isRecord(value.recommendations) ? value.recommendations : {};
  const stateFlags = isRecord(value.state_flags) ? value.state_flags : {};
  const authority = isRecord(value.authority) ? value.authority : {};

  return {
    schemaVersion:
      stringValue(value.schema_version) ?? "cartographer.truth-packet.unknown",
    status: truthStatusFor(stringValue(value.status)),
    decisionDefault: "no_go",
    advisoryOnly: booleanValue(value.advisory_only) ?? true,
    facts: {
      totalDirtyCount:
        numberValue(facts.total_dirty_count) ?? fallbackFacts.totalDirtyCount,
      protectedLaneCount:
        numberValue(facts.protected_lane_count) ?? fallbackFacts.protectedLaneCount,
      gitAvailable: booleanValue(facts.git_available) ?? fallbackFacts.gitAvailable,
    },
    recommendations: {
      confidence: stringValue(recommendations.confidence) ?? "unknown",
      noGoReason: stringValue(recommendations.no_go_reason) ?? "no_go_default",
      safeNextAction:
        stringValue(recommendations.safe_next_action) ??
        "Treat the truth packet as NO-GO until it is available and verified.",
    },
    stateFlags: {
      verified: booleanValue(stateFlags.verified) ?? false,
      blocked: booleanValue(stateFlags.blocked) ?? true,
      stale: booleanValue(stateFlags.stale) ?? false,
      unknown: booleanValue(stateFlags.unknown) ?? true,
      caution: booleanValue(stateFlags.caution) ?? false,
      clear: booleanValue(stateFlags.clear) ?? false,
      noGo: booleanValue(stateFlags.no_go) ?? true,
      advisoryOnly: booleanValue(stateFlags.advisory_only) ?? true,
    },
    authority: {
      authorityGranted: booleanValue(authority.authority_granted) ?? false,
      writeActionsEnabled: booleanValue(authority.write_actions_enabled) ?? false,
      queueAuthorityGranted: booleanValue(authority.queue_authority_granted) ?? false,
      canMutate: booleanValue(authority.can_mutate) ?? false,
    },
    evidenceLinks: evidenceLinks(value.evidence_links),
    verifiedFields: stringArray(value.verified_fields),
    unknownFields: stringArray(value.unknown_fields),
    staleFields: stringArray(value.stale_fields),
  };
}

function unavailableTruthPacket(
  reason: string,
  facts: {
    gitAvailable: boolean;
    protectedLaneCount: number;
    totalDirtyCount: number;
  } = { gitAvailable: false, protectedLaneCount: 0, totalDirtyCount: 0 },
): CartographerTruthPacket {
  return {
    schemaVersion: "cartographer.truth-packet.unavailable",
    status: "no_go",
    decisionDefault: "no_go",
    advisoryOnly: true,
    facts,
    recommendations: {
      confidence: "low",
      noGoReason: reason,
      safeNextAction:
        "Treat the truth packet as NO-GO until it is available and verified.",
    },
    stateFlags: {
      verified: false,
      blocked: true,
      stale: false,
      unknown: true,
      caution: false,
      clear: false,
      noGo: true,
      advisoryOnly: true,
    },
    authority: {
      authorityGranted: false,
      writeActionsEnabled: false,
      queueAuthorityGranted: false,
      canMutate: false,
    },
    evidenceLinks: [],
    verifiedFields: [],
    unknownFields: ["truth_packet"],
    staleFields: [],
  };
}

function safeNextActionFor(
  state: CartographerLiveState["recommendedSafetyState"],
  blockerReasons: string[],
  dirtyFileCount: number,
): string {
  if (state === "blocked") {
    return blockerReasons.length > 0
      ? "Stop and resolve the listed blockers before granting any later Cartographer authority."
      : "Stop because live state is blocked; inspect the endpoint before proceeding.";
  }

  if (state === "caution") {
    return dirtyFileCount > 0
      ? "Review dirty files manually and keep Cartographer read-only."
      : "Proceed carefully in read-only mode and verify live state again before any new phase.";
  }

  return "Repository state is clear for read-only review only; no write or execution authority is granted.";
}

function safetyStateFor(value: string | null): CartographerLiveState["recommendedSafetyState"] {
  if (value === "clear" || value === "caution" || value === "blocked") {
    return value;
  }

  return "blocked";
}

function truthStatusFor(value: string | null): CartographerTruthPacket["status"] {
  if (
    value === "no_go" ||
    value === "blocked" ||
    value === "caution" ||
    value === "clear" ||
    value === "unknown" ||
    value === "stale"
  ) {
    return value;
  }

  return "no_go";
}

function stringValue(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value : null;
}

function numberValue(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function booleanValue(value: unknown): boolean | null {
  return typeof value === "boolean" ? value : null;
}

function stringArray(value: unknown): string[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.filter((item): item is string => typeof item === "string");
}

function laneMatches(value: unknown): { path: string; lane: string }[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.flatMap((item) => {
    if (!isRecord(item)) {
      return [];
    }
    const path = stringValue(item.path);
    const lane = stringValue(item.lane);
    if (!path || !lane) {
      return [];
    }
    return [{ path, lane }];
  });
}

function evidenceLinks(value: unknown): CartographerTruthEvidenceLink[] {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.flatMap((item) => {
    if (!isRecord(item)) {
      return [];
    }
    const label = stringValue(item.label);
    const kind = stringValue(item.kind);
    const href = stringValue(item.href);
    const summary = stringValue(item.summary);
    if (!label || !kind || !href || !summary) {
      return [];
    }
    return [
      {
        label,
        kind,
        href,
        summary,
        authorityGranted: booleanValue(item.authority_granted) ?? false,
        reviewOnly: booleanValue(item.review_only) ?? true,
      },
    ];
  });
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function readOnlyFetchInit(origin: string): RequestInit {
  const init = {
    method: "GET",
    cache: "no-store",
    ...(isLocalHttpsOrigin(origin)
      ? { dispatcher: localHttpsLiveStateDispatcher }
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
