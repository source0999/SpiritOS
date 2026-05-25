import type {
  DurableMediaAccountRecord,
  DurableMediaCatalogItemGenreRecord,
  DurableMediaCatalogItemRecord,
  DurableMediaCurationCheckRecord,
  DurableMediaEpisodePlacementRecord,
  DurableMediaGenreRecord,
  DurableMediaPlaybackAcceptanceEvidenceRecord,
  DurableMediaPlaybackProgressRecord,
  DurableMediaProfileRecord,
  DurableMediaSeasonRecord,
  DurableMediaShowRecord,
  DurableMediaSourceRecord,
  DurableMediaWatchlistEntryRecord,
} from "@/lib/media/media-durable-types";

export type MediaDbAccount = DurableMediaAccountRecord;
export type MediaDbProfile = DurableMediaProfileRecord;
export type MediaDbSource = DurableMediaSourceRecord;
export type MediaDbCatalogItem = DurableMediaCatalogItemRecord;
export type MediaDbGenre = DurableMediaGenreRecord;
export type MediaDbCatalogItemGenre = DurableMediaCatalogItemGenreRecord;
export type MediaDbShow = DurableMediaShowRecord;
export type MediaDbSeason = DurableMediaSeasonRecord;
export type MediaDbEpisodePlacement = DurableMediaEpisodePlacementRecord;
export type MediaDbWatchlistEntry = DurableMediaWatchlistEntryRecord;
export type MediaDbPlaybackProgress = DurableMediaPlaybackProgressRecord;
export type MediaDbCurationCheck = DurableMediaCurationCheckRecord;
export type MediaDbPlaybackAcceptanceEvidence =
  DurableMediaPlaybackAcceptanceEvidenceRecord;
