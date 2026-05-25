export type MediaProfileId = "britton" | "friend" | "guest";

export type MediaProfile = {
  id: MediaProfileId;
  name: string;
};

export type LocalLibraryMetadata = {
  releaseYear: number;
  genres: string[];
  rating: "G" | "PG" | "PG-13" | "TV-G" | "TV-PG" | "TV-14" | "Unrated";
  libraryStatus: "demo-placeholder" | "ready-for-owned-file";
  localFileStrategy: "manual-public-media-match";
  curation: {
    expectedFileName: string;
    rightsReminder: string;
    checklist: string[];
  };
};

export type BaseCatalogItem = {
  id: string;
  type: "movie" | "episode";
  title: string;
  description: string;
  runtimeMinutes: number;
  posterPath: string;
  mediaSource: string;
  sourceKind: "authorized-local-sample";
  sourceLabel: string;
  metadata: LocalLibraryMetadata;
};

export type MovieItem = BaseCatalogItem & {
  type: "movie";
};

export type EpisodeItem = BaseCatalogItem & {
  type: "episode";
  showId: string;
  seasonId: string;
  episodeNumber: number;
};

export type Season = {
  id: string;
  seasonNumber: number;
  title: string;
  episodes: EpisodeItem[];
};

export type ShowItem = {
  id: string;
  type: "show";
  title: string;
  description: string;
  posterPath: string;
  seasons: Season[];
};

export type CatalogItem = MovieItem | EpisodeItem;

export type CatalogGroup = {
  movies: MovieItem[];
  shows: ShowItem[];
};

export type PlaybackProgress = {
  itemId: string;
  seconds: number;
  updatedAt: string;
};

export type CurationCheck = {
  itemId: string;
  authorizedFileConfirmed: boolean;
  updatedAt: string;
};

export type PlaybackAcceptanceEvidence = {
  itemId: string;
  sourceReadyConfirmed: boolean;
  refreshProgressConfirmed: boolean;
  profileIsolationConfirmed: boolean;
  updatedAt: string;
};

export type MediaProfileState = {
  profileId: MediaProfileId;
  watchlistIds: string[];
  progress: Record<string, PlaybackProgress>;
  curationChecks: Record<string, CurationCheck>;
  playbackAcceptance: Record<string, PlaybackAcceptanceEvidence>;
};
