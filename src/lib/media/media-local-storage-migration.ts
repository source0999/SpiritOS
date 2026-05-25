import type {
  MediaProfileId,
  MediaProfileState,
} from "@/components/media/media-types";
import type {
  DurableMediaCurationCheckRecord,
  DurableMediaPlaybackAcceptanceEvidenceRecord,
  DurableMediaPlaybackProgressRecord,
  DurableMediaWatchlistEntryRecord,
} from "@/lib/media/media-durable-types";

export type MediaLocalStorageMigrationSnapshot = {
  selectedProfileId: MediaProfileId;
  profileStates: MediaProfileState[];
};

export type MediaLocalStorageMigratedRecords = {
  watchlistEntries: DurableMediaWatchlistEntryRecord[];
  playbackProgress: DurableMediaPlaybackProgressRecord[];
  curationChecks: DurableMediaCurationCheckRecord[];
  playbackAcceptance: DurableMediaPlaybackAcceptanceEvidenceRecord[];
};

export type MediaLocalStorageMigrationSkippedEntry = {
  profileId: MediaProfileId;
  catalogItemId: string;
  tableName: keyof MediaLocalStorageMigratedRecords;
  reason: "duplicate-entry" | "unknown-catalog-item";
};

export type MediaLocalStorageMigrationPlan = {
  source: "media-local-storage";
  selectedProfileId: MediaProfileId;
  migratedAt: string;
  profileCount: number;
  records: MediaLocalStorageMigratedRecords;
  skippedEntries: MediaLocalStorageMigrationSkippedEntry[];
};

export type MediaLocalStorageMigrationOptions = {
  migratedAt: string;
  catalogItemIds?: readonly string[];
};

function createEmptyRecords(): MediaLocalStorageMigratedRecords {
  return {
    watchlistEntries: [],
    playbackProgress: [],
    curationChecks: [],
    playbackAcceptance: [],
  };
}

function createDuplicateKey(profileId: MediaProfileId, catalogItemId: string) {
  return `${profileId}:${catalogItemId}`;
}

function canMigrateCatalogItem(
  profileId: MediaProfileId,
  catalogItemId: string,
  tableName: keyof MediaLocalStorageMigratedRecords,
  knownCatalogItemIds: ReadonlySet<string> | undefined,
  skippedEntries: MediaLocalStorageMigrationSkippedEntry[],
): boolean {
  if (!knownCatalogItemIds || knownCatalogItemIds.has(catalogItemId)) {
    return true;
  }

  skippedEntries.push({
    profileId,
    catalogItemId,
    tableName,
    reason: "unknown-catalog-item",
  });
  return false;
}

function canAddUniqueEntry(
  profileId: MediaProfileId,
  catalogItemId: string,
  tableName: keyof MediaLocalStorageMigratedRecords,
  seenKeys: Set<string>,
  skippedEntries: MediaLocalStorageMigrationSkippedEntry[],
): boolean {
  const key = createDuplicateKey(profileId, catalogItemId);
  if (!seenKeys.has(key)) {
    seenKeys.add(key);
    return true;
  }

  skippedEntries.push({
    profileId,
    catalogItemId,
    tableName,
    reason: "duplicate-entry",
  });
  return false;
}

export function createMediaLocalStorageMigrationPlan(
  snapshot: MediaLocalStorageMigrationSnapshot,
  options: MediaLocalStorageMigrationOptions,
): MediaLocalStorageMigrationPlan {
  const records = createEmptyRecords();
  const skippedEntries: MediaLocalStorageMigrationSkippedEntry[] = [];
  const knownCatalogItemIds = options.catalogItemIds
    ? new Set(options.catalogItemIds)
    : undefined;
  const seenWatchlist = new Set<string>();
  const seenProgress = new Set<string>();
  const seenCurationChecks = new Set<string>();
  const seenPlaybackAcceptance = new Set<string>();

  for (const profileState of snapshot.profileStates) {
    for (const catalogItemId of profileState.watchlistIds) {
      if (
        !canMigrateCatalogItem(
          profileState.profileId,
          catalogItemId,
          "watchlistEntries",
          knownCatalogItemIds,
          skippedEntries,
        ) ||
        !canAddUniqueEntry(
          profileState.profileId,
          catalogItemId,
          "watchlistEntries",
          seenWatchlist,
          skippedEntries,
        )
      ) {
        continue;
      }

      records.watchlistEntries.push({
        profileId: profileState.profileId,
        catalogItemId,
        createdAt: options.migratedAt,
      });
    }

    for (const progress of Object.values(profileState.progress)) {
      if (
        !canMigrateCatalogItem(
          profileState.profileId,
          progress.itemId,
          "playbackProgress",
          knownCatalogItemIds,
          skippedEntries,
        ) ||
        !canAddUniqueEntry(
          profileState.profileId,
          progress.itemId,
          "playbackProgress",
          seenProgress,
          skippedEntries,
        )
      ) {
        continue;
      }

      records.playbackProgress.push({
        profileId: profileState.profileId,
        catalogItemId: progress.itemId,
        seconds: progress.seconds,
        updatedAt: progress.updatedAt,
      });
    }

    for (const curationCheck of Object.values(profileState.curationChecks)) {
      if (
        !canMigrateCatalogItem(
          profileState.profileId,
          curationCheck.itemId,
          "curationChecks",
          knownCatalogItemIds,
          skippedEntries,
        ) ||
        !canAddUniqueEntry(
          profileState.profileId,
          curationCheck.itemId,
          "curationChecks",
          seenCurationChecks,
          skippedEntries,
        )
      ) {
        continue;
      }

      records.curationChecks.push({
        profileId: profileState.profileId,
        catalogItemId: curationCheck.itemId,
        authorizedFileConfirmed: curationCheck.authorizedFileConfirmed,
        updatedAt: curationCheck.updatedAt,
      });
    }

    for (const playbackAcceptance of Object.values(
      profileState.playbackAcceptance,
    )) {
      if (
        !canMigrateCatalogItem(
          profileState.profileId,
          playbackAcceptance.itemId,
          "playbackAcceptance",
          knownCatalogItemIds,
          skippedEntries,
        ) ||
        !canAddUniqueEntry(
          profileState.profileId,
          playbackAcceptance.itemId,
          "playbackAcceptance",
          seenPlaybackAcceptance,
          skippedEntries,
        )
      ) {
        continue;
      }

      records.playbackAcceptance.push({
        profileId: profileState.profileId,
        catalogItemId: playbackAcceptance.itemId,
        sourceReadyConfirmed: playbackAcceptance.sourceReadyConfirmed,
        refreshProgressConfirmed: playbackAcceptance.refreshProgressConfirmed,
        profileIsolationConfirmed: playbackAcceptance.profileIsolationConfirmed,
        updatedAt: playbackAcceptance.updatedAt,
      });
    }
  }

  return {
    source: "media-local-storage",
    selectedProfileId: snapshot.selectedProfileId,
    migratedAt: options.migratedAt,
    profileCount: snapshot.profileStates.length,
    records,
    skippedEntries,
  };
}
