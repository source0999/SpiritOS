import type { MediaBrowserEvidenceArchivePacket } from "@/lib/media/media-browser-evidence-archive-packet";

export type MediaBrowserEvidenceExportDecisionStatus =
  | "export-ready"
  | "do-not-export";

export type MediaBrowserEvidenceExportDecisionBlocker =
  | "archive-packet-not-ready"
  | "manual-export-approval-missing"
  | "export-location-not-selected"
  | "media-binaries-not-excluded"
  | "app-file-write-requested"
  | "server-export-requested";

export type MediaBrowserEvidenceExportDecisionInput = {
  archivePacket: MediaBrowserEvidenceArchivePacket;
  manualExportApproval: boolean;
  exportLocationSelected: boolean;
  mediaBinariesExcluded: boolean;
  appFileWriteRequested: boolean;
  serverExportRequested: boolean;
};

export type MediaBrowserEvidenceExportDecision = {
  source: "media-browser-evidence-export-decision";
  status: MediaBrowserEvidenceExportDecisionStatus;
  blockers: MediaBrowserEvidenceExportDecisionBlocker[];
  archivePacketStatus: MediaBrowserEvidenceArchivePacket["status"];
};

export function evaluateMediaBrowserEvidenceExportDecision(
  input: MediaBrowserEvidenceExportDecisionInput,
): MediaBrowserEvidenceExportDecision {
  const blockers: MediaBrowserEvidenceExportDecisionBlocker[] = [];

  if (input.archivePacket.status !== "ready") {
    blockers.push("archive-packet-not-ready");
  }

  if (!input.manualExportApproval) {
    blockers.push("manual-export-approval-missing");
  }

  if (!input.exportLocationSelected) {
    blockers.push("export-location-not-selected");
  }

  if (!input.mediaBinariesExcluded) {
    blockers.push("media-binaries-not-excluded");
  }

  if (input.appFileWriteRequested) {
    blockers.push("app-file-write-requested");
  }

  if (input.serverExportRequested) {
    blockers.push("server-export-requested");
  }

  return {
    source: "media-browser-evidence-export-decision",
    status: blockers.length ? "do-not-export" : "export-ready",
    blockers,
    archivePacketStatus: input.archivePacket.status,
  };
}

export function formatMediaBrowserEvidenceExportDecision(
  decision: MediaBrowserEvidenceExportDecision,
): string {
  return decision.status === "export-ready" ? "Export ready" : "Do not export";
}
