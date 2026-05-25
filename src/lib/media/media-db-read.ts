import { adaptDurableMediaLibrary } from "@/lib/media/media-durable-adapter";
import type {
  DurableMediaAdapterResult,
  DurableMediaLibraryRecords,
} from "@/lib/media/media-durable-types";

type ReadableTable<TRecord> = {
  toArray: () => Promise<TRecord[]>;
};

export type MediaDbReadableTables = {
  [TableName in keyof DurableMediaLibraryRecords]: ReadableTable<
    DurableMediaLibraryRecords[TableName][number]
  >;
};

export type MediaDbAsyncReadRepository = {
  getRecords: () => Promise<DurableMediaLibraryRecords>;
  getAdapterResult: () => Promise<DurableMediaAdapterResult>;
};

export async function readMediaDbRecords(
  tables: MediaDbReadableTables,
): Promise<DurableMediaLibraryRecords> {
  const [
    accounts,
    profiles,
    sources,
    catalogItems,
    genres,
    catalogItemGenres,
    shows,
    seasons,
    episodePlacements,
    watchlistEntries,
    playbackProgress,
    curationChecks,
    playbackAcceptance,
  ] = await Promise.all([
    tables.accounts.toArray(),
    tables.profiles.toArray(),
    tables.sources.toArray(),
    tables.catalogItems.toArray(),
    tables.genres.toArray(),
    tables.catalogItemGenres.toArray(),
    tables.shows.toArray(),
    tables.seasons.toArray(),
    tables.episodePlacements.toArray(),
    tables.watchlistEntries.toArray(),
    tables.playbackProgress.toArray(),
    tables.curationChecks.toArray(),
    tables.playbackAcceptance.toArray(),
  ]);

  return {
    accounts,
    profiles,
    sources,
    catalogItems,
    genres,
    catalogItemGenres,
    shows,
    seasons,
    episodePlacements,
    watchlistEntries,
    playbackProgress,
    curationChecks,
    playbackAcceptance,
  };
}

export function createMediaDbReadRepository(
  tables: MediaDbReadableTables,
): MediaDbAsyncReadRepository {
  return {
    getRecords: () => readMediaDbRecords(tables),
    getAdapterResult: async () => {
      return adaptDurableMediaLibrary(await readMediaDbRecords(tables));
    },
  };
}
