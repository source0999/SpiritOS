// ── Oracle browser capability probe - SSR-safe mic/secure-context diagnostics ─────
// > Plain http:// to a LAN/Tailscale IP hides navigator.mediaDevices by design.
// > This module gives the UI one stable shape so we never hydrate one string and
// > then rip it out for a totally different one on the client tick. Source, if you
// > "fix" this by reading window during render, you will eat the hydration mismatch
// > yourself.

export type OracleBrowserCapabilityBlockedReason =
  | "not-mounted"
  | "insecure-context"
  | "missing-media-devices"
  | "missing-get-user-media"
  | "missing-media-recorder"
  | "unsupported-browser"
  | null;

export type OracleBrowserCapabilityReport = {
  /** Mirrors the `mounted` arg - false on SSR + first paint. */
  mounted: boolean;
  /** `window.isSecureContext` after mount. `null` until mounted (hydration-safe). */
  isSecureContext: boolean | null;
  hasNavigator: boolean;
  hasMediaDevices: boolean;
  hasGetUserMedia: boolean;
  hasMediaRecorder: boolean;
  hasAudioContext: boolean;
  /** True only when every capability needed for `MediaRecorder + getUserMedia` is present. */
  canUseMic: boolean;
  blockedReason: OracleBrowserCapabilityBlockedReason;
  /** Short human copy meant for UI hints. Stable until mounted to avoid hydration churn. */
  userMessage: string;
};

/** Stable pre-mount value - must match SSR every time. */
const SSR_REPORT: OracleBrowserCapabilityReport = {
  mounted: false,
  isSecureContext: null,
  hasNavigator: false,
  hasMediaDevices: false,
  hasGetUserMedia: false,
  hasMediaRecorder: false,
  hasAudioContext: false,
  canUseMic: false,
  blockedReason: "not-mounted",
  userMessage: "Checking voice input…",
};

/**
 * Build the capability report. `mounted` is the page-level mounted flag  - 
 * we refuse to inspect `window`/`navigator` until React tells us we're
 * past hydration. That keeps SSR and first paint identical.
 *
 * Browser checks live here (and only here). If you find yourself calling
 * `navigator.mediaDevices` from a component, route it through this report
 * instead. Less surface area = fewer Spirit roastings in the Toxic Grader.
 */
export function getOracleBrowserCapabilityReport(
  mounted: boolean,
): OracleBrowserCapabilityReport {
  if (!mounted) return SSR_REPORT;

  const hasWindow = typeof window !== "undefined";
  const hasNavigator = typeof navigator !== "undefined";
  const isSecureContext = hasWindow ? Boolean(window.isSecureContext) : false;
  const mediaDevices = hasNavigator ? navigator.mediaDevices : undefined;
  const hasMediaDevices = Boolean(mediaDevices);
  const hasGetUserMedia = Boolean(mediaDevices && typeof mediaDevices.getUserMedia === "function");
  const hasMediaRecorder = typeof MediaRecorder !== "undefined";
  const audioCtxCtor = hasWindow
    ? window.AudioContext ||
      (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext
    : undefined;
  const hasAudioContext = typeof audioCtxCtor === "function";

  const canUseMic =
    hasNavigator &&
    hasMediaDevices &&
    hasGetUserMedia &&
    hasMediaRecorder &&
    isSecureContext;

  let blockedReason: OracleBrowserCapabilityBlockedReason = null;
  let userMessage = "Mic ready.";

  if (!hasNavigator || !hasWindow) {
    blockedReason = "unsupported-browser";
    userMessage = "Voice input not available in this environment.";
  } else if (!isSecureContext) {
    blockedReason = "insecure-context";
    userMessage =
      "Mic access is blocked on this HTTP address. Use localhost, 127.0.0.1, or HTTPS.";
  } else if (!hasMediaDevices) {
    // Secure context but no mediaDevices - almost always an old browser.
    blockedReason = "missing-media-devices";
    userMessage = "Microphone API unavailable in this browser.";
  } else if (!hasGetUserMedia) {
    blockedReason = "missing-get-user-media";
    userMessage = "Microphone capture (getUserMedia) is not available in this browser.";
  } else if (!hasMediaRecorder) {
    blockedReason = "missing-media-recorder";
    userMessage = "Audio recording (MediaRecorder) is not supported in this browser.";
  }

  return {
    mounted: true,
    isSecureContext,
    hasNavigator,
    hasMediaDevices,
    hasGetUserMedia,
    hasMediaRecorder,
    hasAudioContext,
    canUseMic,
    blockedReason,
    userMessage,
  };
}

/** Same-host HTTPS variant of the current URL (or null when not relevant). */
export function getOracleHttpsUpgradeUrl(): string | null {
  if (typeof window === "undefined") return null;
  if (window.isSecureContext) return null;
  if (window.location.protocol !== "http:") return null;
  const { host, pathname, search, hash } = window.location;
  return `https://${host}${pathname}${search}${hash}`;
}
