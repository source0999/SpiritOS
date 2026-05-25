import type { MediaDexiePrimaryPromotionDecision } from "@/lib/media/media-dexie-primary-promotion-decision";
import type { MediaIndexedDbManualEvidence } from "@/lib/media/media-indexeddb-manual-evidence";

export type MediaBrowserEvidenceArchivePacketStatus = "ready" | "draft" | "blocked";

export type MediaBrowserEvidenceArchivePacketBlocker =
  | "browser-run-notes-not-captured"
  | "archive-location-not-recorded"
  | "local-only-scope-not-declared"
  | "media-binaries-attached"
  | "server-or-automation-evidence-required";

export type MediaBrowserEvidenceArchivePacketInput = {
  manualEvidence: MediaIndexedDbManualEvidence;
  promotionDecision: MediaDexiePrimaryPromotionDecision;
  browserRunNotesCaptured: boolean;
  archiveLocationRecorded: boolean;
  localOnlyScopeDeclared: boolean;
  mediaBinariesAttached: boolean;
  requiresServerOrAutomationEvidence: boolean;
};

export type MediaBrowserEvidenceArchivePacket = {
  source: "media-browser-evidence-archive-packet";
  status: MediaBrowserEvidenceArchivePacketStatus;
  blockers: MediaBrowserEvidenceArchivePacketBlocker[];
  includes: {
    manualEvidenceStatus: MediaIndexedDbManualEvidence["status"];
    promotionDecisionStatus: MediaDexiePrimaryPromotionDecision["status"];
    browserRunNotes: boolean;
    archiveLocation: boolean;
    localOnlyScope: boolean;
    mediaBinaries: "excluded" | "attached";
  };
};

function getArchivePacketStatus(
  blockers: MediaBrowserEvidenceArchivePacketBlocker[],
): MediaBrowserEvidenceArchivePacketStatus {
  if (
    blockers.includes("media-binaries-attached") ||
    blockers.includes("server-or-automation-evidence-required")
  ) {
    return "blocked";
  }

  return blockers.length ? "draft" : "ready";
}

export function evaluateMediaBrowserEvidenceArchivePacket(
  input: MediaBrowserEvidenceArchivePacketInput,
): MediaBrowserEvidenceArchivePacket {
  const blockers: MediaBrowserEvidenceArchivePacketBlocker[] = [];

  if (!input.browserRunNotesCaptured) {
    blockers.push("browser-run-notes-not-captured");
  }

  if (!input.archiveLocationRecorded) {
    blockers.push("archive-location-not-recorded");
  }

  if (!input.localOnlyScopeDeclared) {
    blockers.push("local-only-scope-not-declared");
  }

  if (input.mediaBinariesAttached) {
    blockers.push("media-binaries-attached");
  }

  if (input.requiresServerOrAutomationEvidence) {
    blockers.push("server-or-automation-evidence-required");
  }

  return {
    source: "media-browser-evidence-archive-packet",
    status: getArchivePacketStatus(blockers),
    blockers,
    includes: {
      manualEvidenceStatus: input.manualEvidence.status,
      promotionDecisionStatus: input.promotionDecision.status,
      browserRunNotes: input.browserRunNotesCaptured,
      archiveLocation: input.archiveLocationRecorded,
      localOnlyScope: input.localOnlyScopeDeclared,
      mediaBinaries: input.mediaBinariesAttached ? "attached" : "excluded",
    },
  };
}

export function formatMediaBrowserEvidenceArchivePacketStatus(
  status: MediaBrowserEvidenceArchivePacketStatus,
): string {
  return status === "ready" ? "Ready" : status === "blocked" ? "Blocked" : "Draft";
}
