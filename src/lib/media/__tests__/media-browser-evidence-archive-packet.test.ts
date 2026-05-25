import { describe, expect, it } from "vitest";

import type { MediaDexiePrimaryPromotionDecision } from "@/lib/media/media-dexie-primary-promotion-decision";
import {
  evaluateMediaBrowserEvidenceArchivePacket,
  formatMediaBrowserEvidenceArchivePacketStatus,
} from "@/lib/media/media-browser-evidence-archive-packet";
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
  blockers: [
    "manual-evidence-not-accepted",
    "explicit-promotion-approval-missing",
  ],
  inheritedEvidenceBlockers: ["manual-acceptance-not-passed"],
};

describe("evaluateMediaBrowserEvidenceArchivePacket", () => {
  it("creates a ready archive packet when manual notes, location, and local-only scope are captured", () => {
    expect(
      evaluateMediaBrowserEvidenceArchivePacket({
        manualEvidence,
        promotionDecision,
        browserRunNotesCaptured: true,
        archiveLocationRecorded: true,
        localOnlyScopeDeclared: true,
        mediaBinariesAttached: false,
        requiresServerOrAutomationEvidence: false,
      }),
    ).toEqual({
      source: "media-browser-evidence-archive-packet",
      status: "ready",
      blockers: [],
      includes: {
        manualEvidenceStatus: "blocked",
        promotionDecisionStatus: "do-not-promote",
        browserRunNotes: true,
        archiveLocation: true,
        localOnlyScope: true,
        mediaBinaries: "excluded",
      },
    });
  });

  it("stays draft when notes or archive location are not captured", () => {
    expect(
      evaluateMediaBrowserEvidenceArchivePacket({
        manualEvidence,
        promotionDecision,
        browserRunNotesCaptured: false,
        archiveLocationRecorded: false,
        localOnlyScopeDeclared: true,
        mediaBinariesAttached: false,
        requiresServerOrAutomationEvidence: false,
      }),
    ).toMatchObject({
      status: "draft",
      blockers: [
        "browser-run-notes-not-captured",
        "archive-location-not-recorded",
      ],
    });
  });

  it("blocks if evidence archive would include media binaries or require server automation proof", () => {
    expect(
      evaluateMediaBrowserEvidenceArchivePacket({
        manualEvidence,
        promotionDecision,
        browserRunNotesCaptured: true,
        archiveLocationRecorded: true,
        localOnlyScopeDeclared: true,
        mediaBinariesAttached: true,
        requiresServerOrAutomationEvidence: true,
      }),
    ).toMatchObject({
      status: "blocked",
      blockers: [
        "media-binaries-attached",
        "server-or-automation-evidence-required",
      ],
      includes: {
        mediaBinaries: "attached",
      },
    });
  });

  it("formats archive packet status for read-only UI display", () => {
    expect(formatMediaBrowserEvidenceArchivePacketStatus("ready")).toBe("Ready");
    expect(formatMediaBrowserEvidenceArchivePacketStatus("draft")).toBe("Draft");
    expect(formatMediaBrowserEvidenceArchivePacketStatus("blocked")).toBe(
      "Blocked",
    );
  });
});
