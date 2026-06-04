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
  Overview?: string;
  ProductionYear?: number;
  RunTimeTicks?: number;
  Genres?: string[];
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
  libraryItems: JellyfinItem[];
  continueWatching: JellyfinItem[];
  latestAdded: JellyfinItem[];
  favorites: JellyfinItem[];
}
