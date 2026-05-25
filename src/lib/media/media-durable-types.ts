import type {
  CatalogGroup,
  CatalogItem,
  MediaProfileId,
  MediaProfileState,
} from "@/components/media/media-types";

export type DurableMediaSourceKind = "authorized-local-sample";

export type DurableLocalFileStrategy = "manual-public-media-match";

export type DurableMediaLibraryStatus =
  | "demo-placeholder"
  | "ready-for-owned-file";

export type DurableMediaRating =
  | "G"
  | "PG"
  | "PG-13"
  | "TV-G"
  | "TV-PG"
  | "TV-14"
  | "Unrated";

export type DurableMediaAccountRecord = {
  id: string;
  displayName: string;
  createdAt: string;
  updatedAt: string;
};

export type DurableMediaProfileRecord = {
  id: MediaProfileId;
  accountId: string;
  name: string;
  sortOrder: number;
  createdAt: string;
  updatedAt: string;
};

export type DurableMediaSourceRecord = {
  id: string;
  accountId: string;
  sourceKind: DurableMediaSourceKind;
  sourcePath: string;
  sourceLabel: string;
  localFileStrategy: DurableLocalFileStrategy;
  expectedFileName: string;
  rightsReminder: string;
  curationChecklist: string[];
  createdAt: string;
  updatedAt: string;
};

export type DurableMediaCatalogItemRecord = {
  id: string;
  accountId: string;
  mediaSourceId: string;
  type: "movie" | "episode";
  title: string;
  description: string;
  runtimeMinutes: number;
  posterPath: string;
  releaseYear: number;
  rating: DurableMediaRating;
  libraryStatus: DurableMediaLibraryStatus;
  createdAt: string;
  updatedAt: string;
};

export type DurableMediaGenreRecord = {
  id: string;
  accountId: string;
  name: string;
  createdAt: string;
  updatedAt: string;
};

export type DurableMediaCatalogItemGenreRecord = {
  catalogItemId: string;
  genreId: string;
  sortOrder: number;
};

export type DurableMediaShowRecord = {
  id: string;
  accountId: string;
  title: string;
  description: string;
  posterPath: string;
  createdAt: string;
  updatedAt: string;
};

export type DurableMediaSeasonRecord = {
  id: string;
  showId: string;
  seasonNumber: number;
  title: string;
  createdAt: string;
  updatedAt: string;
};

export type DurableMediaEpisodePlacementRecord = {
  catalogItemId: string;
  showId: string;
  seasonId: string;
  episodeNumber: number;
};

export type DurableMediaWatchlistEntryRecord = {
  profileId: MediaProfileId;
  catalogItemId: string;
  createdAt: string;
};

export type DurableMediaPlaybackProgressRecord = {
  profileId: MediaProfileId;
  catalogItemId: string;
  seconds: number;
  updatedAt: string;
};

export type DurableMediaCurationCheckRecord = {
  profileId: MediaProfileId;
  catalogItemId: string;
  authorizedFileConfirmed: boolean;
  updatedAt: string;
};

export type DurableMediaPlaybackAcceptanceEvidenceRecord = {
  profileId: MediaProfileId;
  catalogItemId: string;
  sourceReadyConfirmed: boolean;
  refreshProgressConfirmed: boolean;
  profileIsolationConfirmed: boolean;
  updatedAt: string;
};

export type DurableMediaLibraryRecords = {
  accounts: DurableMediaAccountRecord[];
  profiles: DurableMediaProfileRecord[];
  sources: DurableMediaSourceRecord[];
  catalogItems: DurableMediaCatalogItemRecord[];
  genres: DurableMediaGenreRecord[];
  catalogItemGenres: DurableMediaCatalogItemGenreRecord[];
  shows: DurableMediaShowRecord[];
  seasons: DurableMediaSeasonRecord[];
  episodePlacements: DurableMediaEpisodePlacementRecord[];
  watchlistEntries: DurableMediaWatchlistEntryRecord[];
  playbackProgress: DurableMediaPlaybackProgressRecord[];
  curationChecks: DurableMediaCurationCheckRecord[];
  playbackAcceptance: DurableMediaPlaybackAcceptanceEvidenceRecord[];
};

export type DurableMediaAdapterResult = {
  mediaProfiles: Array<{ id: MediaProfileId; name: string }>;
  demoCatalog: CatalogGroup;
  flattenedCatalogItems: CatalogItem[];
  profileStates: Record<MediaProfileId, MediaProfileState>;
  getCatalogItemById: (itemId: string) => CatalogItem | undefined;
  loadProfileState: (profileId: MediaProfileId) => MediaProfileState;
};
