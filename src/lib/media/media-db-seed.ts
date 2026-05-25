import { durableDemoMediaRecords } from "@/lib/media/media-durable-demo-records";
import type { DurableMediaLibraryRecords } from "@/lib/media/media-durable-types";

export type MediaDbSeedTableName = keyof DurableMediaLibraryRecords;

export type MediaDbSeedPlanEntry = {
  tableName: MediaDbSeedTableName;
  recordCount: number;
};

export type MediaDbSeedPlan = {
  source: "durable-demo-media-records";
  entries: MediaDbSeedPlanEntry[];
};

export const MEDIA_DB_SEED_ORDER: MediaDbSeedTableName[] = [
  "accounts",
  "profiles",
  "sources",
  "catalogItems",
  "genres",
  "catalogItemGenres",
  "shows",
  "seasons",
  "episodePlacements",
  "watchlistEntries",
  "playbackProgress",
  "curationChecks",
  "playbackAcceptance",
];

export function createMediaDbSeedPlan(
  records: DurableMediaLibraryRecords = durableDemoMediaRecords,
): MediaDbSeedPlan {
  return {
    source: "durable-demo-media-records",
    entries: MEDIA_DB_SEED_ORDER.map((tableName) => ({
      tableName,
      recordCount: records[tableName].length,
    })),
  };
}

export function getMediaDbSeedRecords(): DurableMediaLibraryRecords {
  return durableDemoMediaRecords;
}
