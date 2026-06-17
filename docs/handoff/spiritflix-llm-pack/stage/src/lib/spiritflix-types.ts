export interface SpiritFlixSession {
  serverUrl: string;
  accessToken: string;
  userId: string;
  username: string;
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
}
