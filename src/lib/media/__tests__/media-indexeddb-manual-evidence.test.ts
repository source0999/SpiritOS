import { describe, expect, it } from "vitest";

import type { MediaIndexedDbManualAcceptanceReport } from "@/lib/media/media-indexeddb-manual-acceptance";
import { evaluateMediaIndexedDbManualEvidence } from "@/lib/media/media-indexeddb-manual-evidence";
import type { MediaProfileStateDualWriteResult } from "@/lib/media/media-profile-state-dual-write";

const passedManualReport: MediaIndexedDbManualAcceptanceReport = {
  source: "media-indexeddb-manual-acceptance",
  checkedAt: "2026-05-23T20:00:00.000Z",
  status: "passed",
  seedResult: {
    status: "seeded",
    summary: {
      source: "durable-demo-media-records",
      entries: [],
    },
  },
  migrationResult: {
    status: "migrated",
    summary: {
      source: "media-local-storage",
      selectedProfileId: "britton",
      migratedAt: "2026-05-23T20:00:00.000Z",
      skippedEntryCount: 0,
      entries: [],
    },
    plan: {
      source: "media-local-storage",
      selectedProfileId: "britton",
      migratedAt: "2026-05-23T20:00:00.000Z",
      profileCount: 1,
      records: {
        watchlistEntries: [],
        playbackProgress: [],
        curationChecks: [],
        playbackAcceptance: [],
      },
      skippedEntries: [],
    },
  },
  checklist: {
    metadataSeeded: true,
    profileStateMigrated: true,
    skippedEntriesReviewed: true,
    localStoragePreserved: true,
  },
};

const dexieWrittenResult: MediaProfileStateDualWriteResult = {
  localStorage: "written",
  dexie: {
    status: "written",
    summary: {
      tableName: "watchlistEntries",
      action: "put",
      profileId: "britton",
      catalogItemId: "local-lights",
    },
  },
};

describe("evaluateMediaIndexedDbManualEvidence", () => {
  it("accepts evidence only when manual browser proof, Dexie read, Dexie write, table inspection, and fallback pass", () => {
    expect(
      evaluateMediaIndexedDbManualEvidence({
        manualAcceptanceReport: passedManualReport,
        runtimeReadSourceStatus: "dexie",
        latestProfileWriteResult: dexieWrittenResult,
        indexedDbTablesInspected: true,
        localStorageFallbackPreserved: true,
        skippedEntriesReviewed: true,
        requiresAutomationOrServerWork: false,
      }),
    ).toMatchObject({
      source: "media-indexeddb-manual-evidence",
      status: "accepted",
      blockers: [],
      primaryReadiness: {
        status: "ready",
        blockers: [],
      },
      captured: {
        manualAcceptanceStatus: "passed",
        runtimeReadSourceStatus: "dexie",
        latestProfileWriteStatus: "written",
        indexedDbTablesInspected: true,
        localStorageFallbackPreserved: true,
        skippedEntriesReviewed: true,
      },
    });
  });

  it("stays incomplete when manual proof is good but table inspection is missing", () => {
    expect(
      evaluateMediaIndexedDbManualEvidence({
        manualAcceptanceReport: passedManualReport,
        runtimeReadSourceStatus: "dexie",
        latestProfileWriteResult: dexieWrittenResult,
        indexedDbTablesInspected: false,
        localStorageFallbackPreserved: true,
        skippedEntriesReviewed: true,
        requiresAutomationOrServerWork: false,
      }),
    ).toMatchObject({
      status: "incomplete",
      blockers: ["indexeddb-tables-not-inspected"],
    });
  });

  it("blocks when the manual report is missing or not passed", () => {
    const evidence = evaluateMediaIndexedDbManualEvidence({
      manualAcceptanceReport: null,
      runtimeReadSourceStatus: "dexie",
      latestProfileWriteResult: dexieWrittenResult,
      indexedDbTablesInspected: true,
      localStorageFallbackPreserved: true,
      skippedEntriesReviewed: true,
      requiresAutomationOrServerWork: false,
    });

    expect(evidence.status).toBe("blocked");
    expect(evidence.blockers).toContain("manual-acceptance-not-passed");
    expect(evidence.captured.manualAcceptanceStatus).toBe("not-run");
  });

  it("blocks when localStorage fallback is not preserved", () => {
    expect(
      evaluateMediaIndexedDbManualEvidence({
        manualAcceptanceReport: passedManualReport,
        runtimeReadSourceStatus: "dexie",
        latestProfileWriteResult: dexieWrittenResult,
        indexedDbTablesInspected: true,
        localStorageFallbackPreserved: false,
        skippedEntriesReviewed: true,
        requiresAutomationOrServerWork: false,
      }),
    ).toMatchObject({
      status: "blocked",
      blockers: ["local-storage-fallback-not-preserved"],
    });
  });

  it("blocks if accepting evidence would require automation or server work", () => {
    expect(
      evaluateMediaIndexedDbManualEvidence({
        manualAcceptanceReport: passedManualReport,
        runtimeReadSourceStatus: "dexie",
        latestProfileWriteResult: dexieWrittenResult,
        indexedDbTablesInspected: true,
        localStorageFallbackPreserved: true,
        skippedEntriesReviewed: true,
        requiresAutomationOrServerWork: true,
      }),
    ).toMatchObject({
      status: "blocked",
      blockers: ["automation-or-server-work-required"],
    });
  });
});
