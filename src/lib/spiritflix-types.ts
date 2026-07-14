export interface SpiritFlixSession {
  serverUrl: string;
  userId: string;
  username: string;
  csrf?: string;
  /** @deprecated Browser-held Jellyfin tokens are ignored by the canonical BFF client. */
  accessToken?: string;
}

export interface SpiritFlixServerInfo {
  LocalAddress?: string;
  ServerName?: string;
  Version?: string;
  ProductName?: string;
  OperatingSystem?: string;
}

export interface JellyfinAuthResponse {
  AccessToken: string;
  User: {
    Id: string;
    Name: string;
  };
}

export interface JellyfinItem {
  Id: string;
  Name: string;
  Type: string;
  ChildCount?: number;
  MediaType?: string;
  Path?: string;
  SeriesName?: string;
  Overview?: string;
  ProductionYear?: number;
  DateCreated?: string;
  IndexNumber?: number;
  ParentIndexNumber?: number;
  RunTimeTicks?: number;
  PrimaryImageAspectRatio?: number;
  Genres?: string[];
  People?: {
    Id?: string;
    Name: string;
    Type?: string;
    Role?: string;
  }[];
  ImageTags?: {
    Primary?: string;
    Thumb?: string;
    Logo?: string;
  };
  BackdropImageTags?: string[];
  UserData?: {
    PlaybackPositionTicks?: number;
    IsFavorite?: boolean;
    Played?: boolean;
    PlayedPercentage?: number;
    PlayCount?: number;
    LastPlayedDate?: string;
  };
  MediaSources?: {
    Id?: string;
    Path?: string;
    RunTimeTicks?: number;
    Size?: number;
  }[];
  MediaStreams?: {
    Index?: number;
    Type?: string;
    Codec?: string;
    Language?: string;
    Title?: string;
    DisplayTitle?: string;
    Width?: number;
    Height?: number;
    BitRate?: number;
    Channels?: number;
    SampleRate?: number;
  }[];
  ManualTags?: string[];
  ManualModelName?: string;
}

export interface SpiritFlixCaptionTrack {
  id: string;
  jellyfinItemId?: string;
  mediaPath: string;
  sourceType: "embedded" | "external" | "generated";
  format: "srt" | "ass" | "ssa" | "vtt" | "mov_text" | "pgs" | "unknown";
  language?: string;
  label: string;
  kind: "subtitles" | "captions";
  default?: boolean;
  forced?: boolean;
  sdh?: boolean;
  streamIndex?: number;
  sourcePath?: string;
  generatedBy?: string;
  reviewStatus: "source" | "draft" | "reviewed" | "approved";
}

export interface SpiritFlixCaptionManifestTrack extends Omit<SpiritFlixCaptionTrack, "format"> {
  sourceFormat: SpiritFlixCaptionTrack["format"] | string;
  outputFormat: "vtt";
  cachePath?: string;
  publicUrl?: string;
}

export interface SpiritFlixCaptionManifest {
  mediaPath: string;
  mediaKey: string;
  generatedAt: string;
  tracks: SpiritFlixCaptionManifestTrack[];
}

export interface SpiritFlixManualTagSummary {
  tag: string;
  label: string;
  count: number;
}

export interface SpiritFlixManualTagRecord {
  schema: "spiritflix-manual-tags/v1";
  itemId: string;
  filePath?: string;
  manualTags: string[];
  updatedAt: string;
  source: "manual";
  createdBy?: "local-user";
}

export interface SpiritFlixManualTagIndex {
  schema: "spiritflix-manual-tag-index/v1";
  updatedAt: string;
  tags: SpiritFlixManualTagSummary[];
  modelAttributes?: SpiritFlixManualTagSummary[];
}

export interface SpiritFlixManualModelSummary {
  modelName: string;
  count: number;
  catalogCount?: number;
  assignedCount?: number;
  aliases?: string[];
  catalogStatus?: string;
  source?: "manual" | "registry" | "merged";
}

export interface SpiritFlixManualModelRecord {
  schema: "spiritflix-manual-model/v1";
  itemId: string;
  filePath?: string;
  modelName: string;
  updatedAt: string;
  source: "manual";
  createdBy?: "local-user";
}

export interface SpiritFlixManualModelIndex {
  schema: "spiritflix-manual-model-index/v1";
  updatedAt: string;
  models: SpiritFlixManualModelSummary[];
}

export type FaceOrganizerStatus = "confirmed" | "needs_review" | "unknown" | "unscanned";

export interface FaceOrganizerPerformer {
  id?: string;
  name: string;
  aliases?: string[];
  confidence?: number;
  similarity?: number;
  status?: string;
  verificationNeeded?: boolean;
  source?: "known_performers" | "sidecar" | "jellyfin";
}

export interface FaceOrganizerVideoMatch {
  itemId: string;
  itemPath?: string;
  sidecarPath?: string;
  videoPath?: string;
  primaryPerformer?: FaceOrganizerPerformer;
  performers: FaceOrganizerPerformer[];
  status: FaceOrganizerStatus;
  label: string;
  confidence?: number;
  verificationNeeded: boolean;
  facesDetected?: number;
  generatedAt?: string;
}

export interface FaceOrganizerMetadataResponse {
  knownPerformers: FaceOrganizerPerformer[];
  enrolledSources?: Record<
    string,
    {
      name: string;
      slug?: string;
      candidateVideos: number;
      enrolledScreens?: number;
      recommendationSourceVideos?: string[];
      refreshedAt?: string;
      source?: "enrolled" | "model_index";
    }
  >;
  videos: Record<string, FaceOrganizerVideoMatch>;
  scannedCount: number;
  generatedAt: string;
}

export interface SpiritFlixFaceLearningRecord {
  schema: "spiritflix-face-learning-request/v1";
  itemId: string;
  filePath?: string;
  modelName: string;
  sidecarPath?: string;
  faceGuess?: FaceOrganizerPerformer;
  relatedItems: Array<{ itemId: string; filePath?: string }>;
  requestedAt: string;
  status: "queued";
  actions: {
    pendingCorrectionWritten: boolean;
    scanCurrentVideoRequested: boolean;
    scanLibraryMatchesRequested: boolean;
    faceEnrollmentAttempted?: boolean;
    faceEnrollmentPerformed?: boolean;
    faceEnrollmentError?: string;
    enrolledCropPath?: string;
    organizerCorrectionConfirmed?: boolean;
  };
  source: "player-model-widget";
}

export interface SpiritFlixGalleryItem {
  id: string;
  modelName: string;
  modelKey: string;
  modelSlug: string;
  fileName: string;
  src: string;
  thumbnailSrc?: string;
  collection?: string;
  uploadedAt?: string;
  sizeBytes?: number;
  contentType?: string;
}

export interface SpiritFlixGalleryGroup {
  name: string;
  modelKey: string;
  modelSlug: string;
  itemCount: number;
}

export interface SpiritFlixGalleryResponse {
  schema: "spiritflix-model-gallery/v1";
  generatedAt: string;
  items: SpiritFlixGalleryItem[];
  groups: SpiritFlixGalleryGroup[];
  summary: {
    galleryItems: number;
    modelsWithGallery: number;
  };
}

export interface JellyfinLibrary {
  Id: string;
  Name: string;
  Type?: string;
  CollectionType?: string;
}

export interface JellyfinItemsResponse<T> {
  Items?: T[];
  TotalRecordCount?: number;
}

export interface SpiritFlixPagingState {
  loaded: number;
  total: number | null;
  pageSize: number;
  hasMore: boolean;
}

export interface SpiritFlixHomeData {
  libraries: JellyfinLibrary[];
  playlists: JellyfinItem[];
  selectedLibraryId: string | null;
  featuredItems: JellyfinItem[];
  libraryItems: JellyfinItem[];
  continueWatching: JellyfinItem[];
  watchHistory: JellyfinItem[];
  latestAdded: JellyfinItem[];
  favorites: JellyfinItem[];
  libraryPaging?: SpiritFlixPagingState;
  continueWatchingPaging?: SpiritFlixPagingState;
  watchHistoryPaging?: SpiritFlixPagingState;
  latestAddedPaging?: SpiritFlixPagingState;
  favoritesPaging?: SpiritFlixPagingState;
}
