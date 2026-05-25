import type { MediaIndexedDbManualAcceptanceReport } from "@/lib/media/media-indexeddb-manual-acceptance";
import type { MediaProfileStateDualWriteResult } from "@/lib/media/media-profile-state-dual-write";
import type { MediaRuntimeReadSource } from "@/lib/media/media-runtime-read-source";

export type MediaProfileStatePrimaryReadinessBlocker =
  | "runtime-read-source-not-dexie"
  | "latest-profile-write-not-dexie"
  | "manual-acceptance-not-passed";

export type MediaProfileStatePrimaryReadiness = {
  status: "ready" | "blocked";
  blockers: MediaProfileStatePrimaryReadinessBlocker[];
};

export type MediaProfileStatePrimaryReadinessInput = {
  runtimeReadSourceStatus: MediaRuntimeReadSource["status"];
  latestProfileWriteResult: MediaProfileStateDualWriteResult | null;
  manualAcceptanceReport: MediaIndexedDbManualAcceptanceReport | null;
};

export function evaluateMediaProfileStatePrimaryReadiness({
  runtimeReadSourceStatus,
  latestProfileWriteResult,
  manualAcceptanceReport,
}: MediaProfileStatePrimaryReadinessInput): MediaProfileStatePrimaryReadiness {
  const blockers: MediaProfileStatePrimaryReadinessBlocker[] = [];

  if (runtimeReadSourceStatus !== "dexie") {
    blockers.push("runtime-read-source-not-dexie");
  }

  if (latestProfileWriteResult?.dexie.status !== "written") {
    blockers.push("latest-profile-write-not-dexie");
  }

  if (manualAcceptanceReport?.status !== "passed") {
    blockers.push("manual-acceptance-not-passed");
  }

  return {
    status: blockers.length ? "blocked" : "ready",
    blockers,
  };
}

export function formatMediaProfileStatePrimaryReadiness(
  readiness: MediaProfileStatePrimaryReadiness,
): string {
  return readiness.status === "ready" ? "Ready" : "Blocked";
}
