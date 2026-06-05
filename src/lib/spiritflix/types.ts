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
  latestAdded: JellyfinItem[];
  favorites: JellyfinItem[];
}
