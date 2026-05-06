// ── Oracle UI visual lane - maps live session/capability to orb + visualizer ───────
// > No new voice state machine: this is a thin paint adapter over
// > `OracleVoiceSessionStatus` + homelab capability rows.

import type { OracleBrowserCapabilityReport } from "@/lib/oracle/oracle-browser-capabilities";
import type { OracleVoiceSessionStatus } from "@/lib/oracle/oracle-voice-session";

/** Bars + orb intensity - six buckets for CSS. */
export type OracleVisualState =
  | "idle"
  | "permission"
  | "listening"
  | "processing"
  | "speaking"
  | "error";

export type HomelabOracleBadgeVariant = "pending" | "live" | "offline" | "ready";

export function getOracleVisualStateFromSessionStatus(
  status: OracleVoiceSessionStatus,
): OracleVisualState {
  switch (status) {
    case "error":
      return "error";
    case "permission-needed":
    case "requesting-mic":
    case "blocked":
    case "unsupported":
      return "permission";
    case "listening":
    case "hearing-speech":
      return "listening";
    case "silence-detected":
    case "transcribing":
    case "thinking":
    case "restarting":
      return "processing";
    case "speaking":
      return "speaking";
    case "idle":
    case "ready":
    case "stopped":
    default:
      return "idle";
  }
}

/**
 * Homelab card has no live mic stream - only capability + badge paint.
 * Insecure / hard API gaps read as error; soft “degraded” reads as permission lane.
 */
export function getOracleVisualStateForHomelab(input: {
  mounted: boolean;
  capability: OracleBrowserCapabilityReport;
  badgeVariant: HomelabOracleBadgeVariant;
}): OracleVisualState {
  const { mounted, capability, badgeVariant } = input;
  if (!mounted) return "idle";
  if (capability.isSecureContext === false) return "error";
  if (!capability.canUseMic) return "permission";
  if (badgeVariant === "offline") return "permission";
  return "idle";
}
