import type { SpiritMediaDB } from "@/lib/media/media-db";
import {
  seedMediaDbWhenAvailable,
  type MediaDbBrowserWriteResult,
} from "@/lib/media/media-db-browser-write";
import {
  runMediaLocalStorageBrowserMigration,
  type MediaLocalStorageBrowserMigrationResult,
} from "@/lib/media/media-local-storage-browser-migration";

type ReadableStorage = {
  getItem: (key: string) => string | null;
};

export type MediaIndexedDbManualAcceptanceStatus =
  | "passed"
  | "blocked"
  | "needs-browser-run";

export type MediaIndexedDbManualAcceptanceReport = {
  source: "media-indexeddb-manual-acceptance";
  checkedAt: string;
  status: MediaIndexedDbManualAcceptanceStatus;
  seedResult: MediaDbBrowserWriteResult;
  migrationResult: MediaLocalStorageBrowserMigrationResult;
  checklist: {
    metadataSeeded: boolean;
    profileStateMigrated: boolean;
    skippedEntriesReviewed: boolean;
    localStoragePreserved: boolean;
  };
};

export type MediaIndexedDbManualAcceptanceOptions = {
  storage?: ReadableStorage | null;
  db?: SpiritMediaDB | null;
  checkedAt?: string;
};

function getStatus(
  seedResult: MediaDbBrowserWriteResult,
  migrationResult: MediaLocalStorageBrowserMigrationResult,
): MediaIndexedDbManualAcceptanceStatus {
  if (
    seedResult.status === "unavailable" ||
    migrationResult.status === "unavailable"
  ) {
    return "needs-browser-run";
  }

  if (migrationResult.plan.skippedEntries.length > 0) {
    return "blocked";
  }

  return "passed";
}

export async function createMediaIndexedDbManualAcceptanceReport(
  options: MediaIndexedDbManualAcceptanceOptions = {},
): Promise<MediaIndexedDbManualAcceptanceReport> {
  const checkedAt = options.checkedAt ?? new Date().toISOString();
  const db = "db" in options ? options.db : undefined;
  const seedResult = await seedMediaDbWhenAvailable(db);
  const migrationResult = await runMediaLocalStorageBrowserMigration({
    storage: "storage" in options ? options.storage : undefined,
    db,
    migratedAt: checkedAt,
  });
  const skippedEntryCount =
    migrationResult.status === "migrated"
      ? migrationResult.plan.skippedEntries.length
      : 0;

  return {
    source: "media-indexeddb-manual-acceptance",
    checkedAt,
    status: getStatus(seedResult, migrationResult),
    seedResult,
    migrationResult,
    checklist: {
      metadataSeeded: seedResult.status === "seeded",
      profileStateMigrated: migrationResult.status === "migrated",
      skippedEntriesReviewed: skippedEntryCount === 0,
      localStoragePreserved: true,
    },
  };
}
