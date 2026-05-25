import { mediaDb, type SpiritMediaDB } from "@/lib/media/media-db";
import {
  createMediaDbReadRepository,
  type MediaDbAsyncReadRepository,
  type MediaDbReadableTables,
} from "@/lib/media/media-db-read";
import type { DurableMediaAdapterResult } from "@/lib/media/media-durable-types";

export type MediaDbBrowserReadResult =
  | {
      status: "unavailable";
      reason: "indexeddb-unavailable";
    }
  | {
      status: "ready";
      repository: MediaDbAsyncReadRepository;
      adapterResult: DurableMediaAdapterResult;
    };

function toReadableTables(db: SpiritMediaDB): MediaDbReadableTables {
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

export async function readMediaDbWhenAvailable(
  db: SpiritMediaDB | null | undefined = mediaDb,
): Promise<MediaDbBrowserReadResult> {
  if (!db) {
    return {
      status: "unavailable",
      reason: "indexeddb-unavailable",
    };
  }

  const repository = createMediaDbReadRepository(toReadableTables(db));

  return {
    status: "ready",
    repository,
    adapterResult: await repository.getAdapterResult(),
  };
}
