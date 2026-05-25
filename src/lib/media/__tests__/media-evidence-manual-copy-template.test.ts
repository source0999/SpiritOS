import { describe, expect, it } from "vitest";

import type { MediaBrowserEvidenceArchivePacket } from "@/lib/media/media-browser-evidence-archive-packet";
import type { MediaBrowserEvidenceExportDecision } from "@/lib/media/media-browser-evidence-export-decision";
import type { MediaDexiePrimaryPromotionDecision } from "@/lib/media/media-dexie-primary-promotion-decision";
import { createMediaEvidenceManualCopyTemplate } from "@/lib/media/media-evidence-manual-copy-template";
import type { MediaIndexedDbManualEvidence } from "@/lib/media/media-indexeddb-manual-evidence";

const manualEvidence: MediaIndexedDbManualEvidence = {
  source: "media-indexeddb-manual-evidence",
  status: "blocked",
  blockers: ["manual-acceptance-not-passed"],
  primaryReadiness: {
    status: "blocked",
    blockers: ["manual-acceptance-not-passed"],
  },
  captured: {
    manualAcceptanceStatus: "not-run",
    runtimeReadSourceStatus: "local-fallback",
    latestProfileWriteStatus: "not-run",
    indexedDbTablesInspected: false,
    localStorageFallbackPreserved: true,
    skippedEntriesReviewed: false,
  },
};

const promotionDecision: MediaDexiePrimaryPromotionDecision = {
  source: "media-dexie-primary-promotion-decision",
  status: "do-not-promote",
  blockers: ["manual-evidence-not-accepted"],
  inheritedEvidenceBlockers: ["manual-acceptance-not-passed"],
};

const archivePacket: MediaBrowserEvidenceArchivePacket = {
  source: "media-browser-evidence-archive-packet",
  status: "draft",
  blockers: ["browser-run-notes-not-captured"],
  includes: {
    manualEvidenceStatus: "blocked",
    promotionDecisionStatus: "do-not-promote",
    browserRunNotes: false,
    archiveLocation: false,
    localOnlyScope: true,
    mediaBinaries: "excluded",
  },
};

const exportDecision: MediaBrowserEvidenceExportDecision = {
  source: "media-browser-evidence-export-decision",
  status: "do-not-export",
  blockers: ["archive-packet-not-ready"],
  archivePacketStatus: "draft",
};

describe("createMediaEvidenceManualCopyTemplate", () => {
  it("creates a manual-copy-only template that is not persisted by the app", () => {
    expect(
      createMediaEvidenceManualCopyTemplate({
        manualEvidence,
        promotionDecision,
        archivePacket,
        exportDecision,
      }),
    ).toMatchObject({
      source: "media-evidence-manual-copy-template",
      mode: "manual-copy-only",
      storage: "not-persisted",
    });
  });

  it("includes the expected copy sections in stable order", () => {
    expect(
      createMediaEvidenceManualCopyTemplate({
        manualEvidence,
        promotionDecision,
        archivePacket,
        exportDecision,
      }).sections.map((section) => section.id),
    ).toEqual([
      "scope",
      "manual-evidence",
      "promotion-decision",
      "archive-packet",
      "export-decision",
      "blocked-work",
    ]);
  });

  it("summarizes current blocked and draft evidence states", () => {
    const template = createMediaEvidenceManualCopyTemplate({
      manualEvidence,
      promotionDecision,
      archivePacket,
      exportDecision,
    });

    expect(template.sections[1].lines).toContain("Status: blocked");
    expect(template.sections[2].lines).toContain("Status: do-not-promote");
    expect(template.sections[3].lines).toContain("Status: draft");
    expect(template.sections[3].lines).toContain("Media binaries: excluded");
    expect(template.sections[4].lines).toContain("Status: do-not-export");
  });

  it("keeps generated copy from implying file writes, downloads, server export, or primary promotion", () => {
    const blockedWork = createMediaEvidenceManualCopyTemplate({
      manualEvidence,
      promotionDecision,
      archivePacket,
      exportDecision,
    }).sections.find((section) => section.id === "blocked-work");

    expect(blockedWork?.lines.join(" ")).toContain("browser downloads");
    expect(blockedWork?.lines.join(" ")).toContain("persisted archives");
    expect(blockedWork?.lines.join(" ")).toContain("server storage");
    expect(blockedWork?.lines.join(" ")).toContain(
      "Dexie primary profile-state promotion",
    );
  });
});
