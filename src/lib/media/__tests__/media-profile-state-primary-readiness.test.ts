import { describe, expect, it } from "vitest";

import {
  evaluateMediaProfileStatePrimaryReadiness,
  formatMediaProfileStatePrimaryReadiness,
} from "@/lib/media/media-profile-state-primary-readiness";

describe("media-profile-state-primary-readiness", () => {
  it("blocks primary state when Dexie read, write, or manual acceptance is missing", () => {
    const readiness = evaluateMediaProfileStatePrimaryReadiness({
      runtimeReadSourceStatus: "local-fallback",
      latestProfileWriteResult: null,
      manualAcceptanceReport: null,
    });

    expect(readiness).toEqual({
      status: "blocked",
      blockers: [
        "runtime-read-source-not-dexie",
        "latest-profile-write-not-dexie",
        "manual-acceptance-not-passed",
      ],
    });
    expect(formatMediaProfileStatePrimaryReadiness(readiness)).toBe("Blocked");
  });

  it("reports ready when Dexie read, write, and manual acceptance have passed", () => {
    const readiness = evaluateMediaProfileStatePrimaryReadiness({
      runtimeReadSourceStatus: "dexie",
      latestProfileWriteResult: {
        localStorage: "written",
        dexie: {
          status: "written",
          summary: {
            tableName: "watchlistEntries",
            action: "put",
            profileId: "britton",
            catalogItemId: "movie-local-lights",
          },
        },
      },
      manualAcceptanceReport: {
        source: "media-indexeddb-manual-acceptance",
        checkedAt: "2026-05-23T21:00:00.000Z",
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
          plan: {
            source: "media-local-storage",
            selectedProfileId: "britton",
            migratedAt: "2026-05-23T21:00:00.000Z",
            profileCount: 1,
            records: {
              watchlistEntries: [],
              playbackProgress: [],
              curationChecks: [],
              playbackAcceptance: [],
            },
            skippedEntries: [],
          },
          summary: {
            source: "media-local-storage",
            selectedProfileId: "britton",
            migratedAt: "2026-05-23T21:00:00.000Z",
            skippedEntryCount: 0,
            entries: [],
          },
        },
        checklist: {
          metadataSeeded: true,
          profileStateMigrated: true,
          skippedEntriesReviewed: true,
          localStoragePreserved: true,
        },
      },
    });

    expect(readiness).toEqual({
      status: "ready",
      blockers: [],
    });
    expect(formatMediaProfileStatePrimaryReadiness(readiness)).toBe("Ready");
  });
});
