const LIVE_STATE_ENDPOINT = "/v1/cartographer/live-state";

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
      method: "GET",
      cache: "no-store",
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

function stringValue(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value : null;
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

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}
