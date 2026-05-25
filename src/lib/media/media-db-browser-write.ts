import { mediaDb } from "@/lib/media/media-db";
import type { SpiritMediaDB } from "@/lib/media/media-db";
import {
  writeMediaDbSeedRecords,
  type MediaDbWritableTables,
  type MediaDbWriteSummary,
} from "@/lib/media/media-db-write";
import { durableDemoMediaRecords } from "@/lib/media/media-durable-demo-records";
import type { DurableMediaLibraryRecords } from "@/lib/media/media-durable-types";

export type MediaDbBrowserWriteResult =
  | {
      status: "unavailable";
      reason: "indexeddb-unavailable";
    }
  | {
      status: "seeded";
      summary: MediaDbWriteSummary;
    };

function toWritableTables(db: SpiritMediaDB): MediaDbWritableTables {
  return {
    accounts: db.accounts,
    profiles: db.profiles,
    sources: db.sources,
    catalogItems: db.catalogItems,
    genres: db.genres,
    catalogItemGenres: db.catalogItemGenres,
    shows: db.shows,
    seasons: db.seasons,
    episodePlacements: db.episodePlacements,
    watchlistEntries: db.watchlistEntries,
    playbackProgress: db.playbackProgress,
    curationChecks: db.curationChecks,
    playbackAcceptance: db.playbackAcceptance,
  };
}

export async function seedMediaDbWhenAvailable(
  db: SpiritMediaDB | null = mediaDb,
  records: DurableMediaLibraryRecords = durableDemoMediaRecords,
): Promise<MediaDbBrowserWriteResult> {
  if (!db) {
    return {
      status: "unavailable",
      reason: "indexeddb-unavailable",
    };
  }

  return {
    status: "seeded",
    summary: await writeMediaDbSeedRecords(toWritableTables(db), records),
  };
}
