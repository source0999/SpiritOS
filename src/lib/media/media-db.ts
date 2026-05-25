import Dexie, { type Table } from "dexie";

import type {
  MediaDbAccount,
  MediaDbCatalogItem,
  MediaDbCatalogItemGenre,
  MediaDbCurationCheck,
  MediaDbEpisodePlacement,
  MediaDbGenre,
  MediaDbPlaybackAcceptanceEvidence,
  MediaDbPlaybackProgress,
  MediaDbProfile,
  MediaDbSeason,
  MediaDbShow,
  MediaDbSource,
  MediaDbWatchlistEntry,
} from "@/lib/media/media-db.types";

export const MEDIA_DB_NAME = "SpiritMediaDB";
export const MEDIA_DB_VERSION = 1;

export const MEDIA_DB_STORES = {
  accounts: "id, updatedAt",
  profiles: "id, accountId, sortOrder, updatedAt",
  sources: "id, accountId, sourceKind, updatedAt",
  catalogItems: "id, accountId, mediaSourceId, type, updatedAt",
  genres: "id, accountId, name, updatedAt",
  catalogItemGenres:
    "[catalogItemId+genreId], catalogItemId, genreId, sortOrder",
  shows: "id, accountId, updatedAt",
  seasons: "id, showId, seasonNumber, updatedAt",
  episodePlacements: "catalogItemId, showId, seasonId, episodeNumber",
  watchlistEntries:
    "[profileId+catalogItemId], profileId, catalogItemId, createdAt",
  playbackProgress:
    "[profileId+catalogItemId], profileId, catalogItemId, updatedAt",
  curationChecks:
    "[profileId+catalogItemId], profileId, catalogItemId, updatedAt",
  playbackAcceptance:
    "[profileId+catalogItemId], profileId, catalogItemId, updatedAt",
} as const;

export function isBrowserMediaDbAvailable(): boolean {
  return typeof window !== "undefined" && "indexedDB" in window;
}

export class SpiritMediaDB extends Dexie {
  accounts!: Table<MediaDbAccount, string>;
  profiles!: Table<MediaDbProfile, string>;
  sources!: Table<MediaDbSource, string>;
  catalogItems!: Table<MediaDbCatalogItem, string>;
  genres!: Table<MediaDbGenre, string>;
  catalogItemGenres!: Table<MediaDbCatalogItemGenre, [string, string]>;
  shows!: Table<MediaDbShow, string>;
  seasons!: Table<MediaDbSeason, string>;
  episodePlacements!: Table<MediaDbEpisodePlacement, string>;
  watchlistEntries!: Table<MediaDbWatchlistEntry, [string, string]>;
  playbackProgress!: Table<MediaDbPlaybackProgress, [string, string]>;
  curationChecks!: Table<MediaDbCurationCheck, [string, string]>;
  playbackAcceptance!: Table<
    MediaDbPlaybackAcceptanceEvidence,
    [string, string]
  >;

  constructor() {
    super(MEDIA_DB_NAME);
    this.version(MEDIA_DB_VERSION).stores(MEDIA_DB_STORES);
  }
}

export const mediaDb: SpiritMediaDB | null = isBrowserMediaDbAvailable()
  ? new SpiritMediaDB()
  : null;
