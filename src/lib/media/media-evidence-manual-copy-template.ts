import type { MediaBrowserEvidenceArchivePacket } from "@/lib/media/media-browser-evidence-archive-packet";
import type { MediaBrowserEvidenceExportDecision } from "@/lib/media/media-browser-evidence-export-decision";
import type { MediaDexiePrimaryPromotionDecision } from "@/lib/media/media-dexie-primary-promotion-decision";
import type { MediaIndexedDbManualEvidence } from "@/lib/media/media-indexeddb-manual-evidence";

export type MediaEvidenceManualCopyTemplateSectionId =
  | "scope"
  | "manual-evidence"
  | "promotion-decision"
  | "archive-packet"
  | "export-decision"
  | "blocked-work";

export type MediaEvidenceManualCopyTemplateSection = {
  id: MediaEvidenceManualCopyTemplateSectionId;
  heading: string;
  lines: string[];
};

export type MediaEvidenceManualCopyTemplateInput = {
  manualEvidence: MediaIndexedDbManualEvidence;
  promotionDecision: MediaDexiePrimaryPromotionDecision;
  archivePacket: MediaBrowserEvidenceArchivePacket;
  exportDecision: MediaBrowserEvidenceExportDecision;
};

export type MediaEvidenceManualCopyTemplate = {
  source: "media-evidence-manual-copy-template";
  mode: "manual-copy-only";
  storage: "not-persisted";
  sections: MediaEvidenceManualCopyTemplateSection[];
};

function formatList(values: readonly string[]): string {
  return values.length ? values.join(", ") : "none";
}

export function createMediaEvidenceManualCopyTemplate({
  manualEvidence,
  promotionDecision,
  archivePacket,
  exportDecision,
}: MediaEvidenceManualCopyTemplateInput): MediaEvidenceManualCopyTemplate {
  return {
    source: "media-evidence-manual-copy-template",
    mode: "manual-copy-only",
    storage: "not-persisted",
    sections: [
      {
        id: "scope",
        heading: "Scope",
        lines: [
          "Browser-local media evidence only.",
          "No media binaries, uploads, downloads, server export, or app file writes.",
        ],
      },
      {
        id: "manual-evidence",
        heading: "Manual Evidence",
        lines: [
          `Status: ${manualEvidence.status}`,
          `Blockers: ${formatList(manualEvidence.blockers)}`,
        ],
      },
      {
        id: "promotion-decision",
        heading: "Promotion Decision",
        lines: [
          `Status: ${promotionDecision.status}`,
          `Blockers: ${formatList(promotionDecision.blockers)}`,
        ],
      },
      {
        id: "archive-packet",
        heading: "Archive Packet",
        lines: [
          `Status: ${archivePacket.status}`,
          `Blockers: ${formatList(archivePacket.blockers)}`,
          `Media binaries: ${archivePacket.includes.mediaBinaries}`,
        ],
      },
      {
        id: "export-decision",
        heading: "Export Decision",
        lines: [
          `Status: ${exportDecision.status}`,
          `Blockers: ${formatList(exportDecision.blockers)}`,
        ],
      },
      {
        id: "blocked-work",
        heading: "Blocked Work",
        lines: [
          "Do not implement browser downloads, clipboard writes, persisted archives, API routes, server storage, media serving, or Dexie primary profile-state promotion from this template.",
        ],
      },
    ],
  };
}
