import type { MediaIndexedDbManualAcceptanceReport } from "@/lib/media/media-indexeddb-manual-acceptance";
import type { MediaProfileStateDualWriteResult } from "@/lib/media/media-profile-state-dual-write";
import type {
  MediaProfileStatePrimaryReadiness,
  MediaProfileStatePrimaryReadinessInput,
} from "@/lib/media/media-profile-state-primary-readiness";
import { evaluateMediaProfileStatePrimaryReadiness } from "@/lib/media/media-profile-state-primary-readiness";
import type { MediaRuntimeReadSource } from "@/lib/media/media-runtime-read-source";

export type MediaIndexedDbManualEvidenceStatus =
  | "accepted"
  | "blocked"
  | "incomplete";

export type MediaIndexedDbManualEvidenceBlocker =
  | "manual-acceptance-not-passed"
  | "runtime-read-source-not-dexie"
  | "latest-profile-write-not-dexie"
  | "primary-readiness-not-ready"
  | "local-storage-fallback-not-preserved"
  | "skipped-entries-unreviewed"
  | "indexeddb-tables-not-inspected"
  | "automation-or-server-work-required";

export type MediaIndexedDbManualEvidenceInput = {
  manualAcceptanceReport: MediaIndexedDbManualAcceptanceReport | null;
  runtimeReadSourceStatus: MediaRuntimeReadSource["status"];
  latestProfileWriteResult: MediaProfileStateDualWriteResult | null;
  indexedDbTablesInspected: boolean;
  localStorageFallbackPreserved: boolean;
  skippedEntriesReviewed: boolean;
  requiresAutomationOrServerWork: boolean;
};

export type MediaIndexedDbManualEvidence = {
  source: "media-indexeddb-manual-evidence";
  status: MediaIndexedDbManualEvidenceStatus;
  blockers: MediaIndexedDbManualEvidenceBlocker[];
  primaryReadiness: MediaProfileStatePrimaryReadiness;
  captured: {
    manualAcceptanceStatus: MediaIndexedDbManualAcceptanceReport["status"] | "not-run";
    runtimeReadSourceStatus: MediaRuntimeReadSource["status"];
    latestProfileWriteStatus:
      | MediaProfileStateDualWriteResult["dexie"]["status"]
      | "not-run";
    indexedDbTablesInspected: boolean;
    localStorageFallbackPreserved: boolean;
    skippedEntriesReviewed: boolean;
  };
};

function getPrimaryReadinessInput({
  manualAcceptanceReport,
  runtimeReadSourceStatus,
  latestProfileWriteResult,
}: MediaIndexedDbManualEvidenceInput): MediaProfileStatePrimaryReadinessInput {
  return {
    manualAcceptanceReport,
    runtimeReadSourceStatus,
    latestProfileWriteResult,
  };
}

function getEvidenceStatus(
  blockers: MediaIndexedDbManualEvidenceBlocker[],
): MediaIndexedDbManualEvidenceStatus {
  if (blockers.includes("automation-or-server-work-required")) {
    return "blocked";
  }

  if (
    blockers.includes("manual-acceptance-not-passed") ||
    blockers.includes("skipped-entries-unreviewed") ||
    blockers.includes("local-storage-fallback-not-preserved")
  ) {
    return "blocked";
  }

  return blockers.length === 0 ? "accepted" : "incomplete";
}

export function evaluateMediaIndexedDbManualEvidence(
  input: MediaIndexedDbManualEvidenceInput,
): MediaIndexedDbManualEvidence {
  const primaryReadiness = evaluateMediaProfileStatePrimaryReadiness(
    getPrimaryReadinessInput(input),
  );
  const blockers: MediaIndexedDbManualEvidenceBlocker[] = [];

  if (input.requiresAutomationOrServerWork) {
    blockers.push("automation-or-server-work-required");
  }

  if (input.manualAcceptanceReport?.status !== "passed") {
    blockers.push("manual-acceptance-not-passed");
  }

  if (input.runtimeReadSourceStatus !== "dexie") {
    blockers.push("runtime-read-source-not-dexie");
  }

  if (input.latestProfileWriteResult?.dexie.status !== "written") {
    blockers.push("latest-profile-write-not-dexie");
  }

  if (primaryReadiness.status !== "ready") {
    blockers.push("primary-readiness-not-ready");
  }

  if (!input.localStorageFallbackPreserved) {
    blockers.push("local-storage-fallback-not-preserved");
  }

  if (!input.skippedEntriesReviewed) {
    blockers.push("skipped-entries-unreviewed");
  }

  if (!input.indexedDbTablesInspected) {
    blockers.push("indexeddb-tables-not-inspected");
  }

  return {
    source: "media-indexeddb-manual-evidence",
    status: getEvidenceStatus(blockers),
    blockers,
    primaryReadiness,
    captured: {
      manualAcceptanceStatus: input.manualAcceptanceReport?.status ?? "not-run",
      runtimeReadSourceStatus: input.runtimeReadSourceStatus,
      latestProfileWriteStatus:
        input.latestProfileWriteResult?.dexie.status ?? "not-run",
      indexedDbTablesInspected: input.indexedDbTablesInspected,
      localStorageFallbackPreserved: input.localStorageFallbackPreserved,
      skippedEntriesReviewed: input.skippedEntriesReviewed,
    },
  };
}
