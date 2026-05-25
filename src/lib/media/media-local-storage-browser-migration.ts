import { mediaDb, type SpiritMediaDB } from "@/lib/media/media-db";
import { flattenedCatalogItems, mediaProfiles } from "@/lib/media/media-catalog-source";
import {
  createMediaLocalStorageMigrationPlan,
  type MediaLocalStorageMigrationPlan,
} from "@/lib/media/media-local-storage-migration";
import {
  writeMediaLocalStorageMigrationPlan,
  type MediaLocalStorageMigrationWritableTables,
  type MediaLocalStorageMigrationWriteSummary,
} from "@/lib/media/media-local-storage-migration-write";
import { readMediaLocalStorageSnapshot } from "@/lib/media/media-local-storage-snapshot";

type ReadableStorage = {
  getItem: (key: string) => string | null;
};

export type MediaLocalStorageBrowserMigrationResult =
  | {
      status: "unavailable";
      reason: "local-storage-unavailable" | "indexeddb-unavailable";
    }
  | {
      status: "migrated";
      plan: MediaLocalStorageMigrationPlan;
      summary: MediaLocalStorageMigrationWriteSummary;
    };

export type MediaLocalStorageBrowserMigrationOptions = {
  storage?: ReadableStorage | null;
  db?: SpiritMediaDB | null;
  migratedAt?: string;
};

function getBrowserLocalStorage(): Storage | null {
  if (typeof window === "undefined" || !window.localStorage) {
    return null;
  }

  return window.localStorage;
}

function toMigrationWritableTables(
  db: SpiritMediaDB,
): MediaLocalStorageMigrationWritableTables {
  return {
    watchlistEntries: db.watchlistEntries,
    playbackProgress: db.playbackProgress,
    curationChecks: db.curationChecks,
    playbackAcceptance: db.playbackAcceptance,
  };
}

export async function runMediaLocalStorageBrowserMigration(
  options: MediaLocalStorageBrowserMigrationOptions = {},
): Promise<MediaLocalStorageBrowserMigrationResult> {
  const storage =
    "storage" in options ? options.storage : getBrowserLocalStorage();
  if (!storage) {
    return {
      status: "unavailable",
      reason: "local-storage-unavailable",
    };
  }

  const db = "db" in options ? options.db : mediaDb;
  if (!db) {
    return {
      status: "unavailable",
      reason: "indexeddb-unavailable",
    };
  }

  const profileIds = mediaProfiles.map((profile) => profile.id);
  const catalogItemIds = flattenedCatalogItems.map((item) => item.id);
  const plan = createMediaLocalStorageMigrationPlan(
    readMediaLocalStorageSnapshot(storage, profileIds),
    {
      migratedAt: options.migratedAt ?? new Date().toISOString(),
      catalogItemIds,
    },
  );

  return {
    status: "migrated",
    plan,
    summary: await writeMediaLocalStorageMigrationPlan(
      toMigrationWritableTables(db),
      plan,
    ),
  };
}
