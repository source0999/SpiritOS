import type {
  JellyfinAuthResponse,
  JellyfinItem,
  JellyfinItemsResponse,
  JellyfinLibrary,
  FaceOrganizerMetadataResponse,
  SpiritFlixServerInfo,
  SpiritFlixSession,
} from "./spiritflix-types";

export const SPIRITFLIX_DEFAULT_SERVER = "http://spirit.tailb69ea6.ts.net:8096";
export const SPIRITFLIX_FALLBACK_SERVER = "http://100.111.32.31:8096";

const CLIENT_NAME = "SpiritFlix";
const CLIENT_VERSION = "0.1.0";
const DEVICE_NAME = "SpiritFlix Web";
const DEVICE_ID_KEY = "spiritflix_device_id";
const SESSION_KEY = "spiritflix_private_gooner_session";
const GOONER_ITEM_FIELDS =
  "Path,SeriesName,DateCreated,IndexNumber,ParentIndexNumber,Overview,ProductionYear,RunTimeTicks,Genres,People,UserData,PrimaryImageAspectRatio,MediaStreams,MediaSources,ChildCount";

export function getStoredSession(): SpiritFlixSession | null {
  if (typeof window === "undefined") return null;
  const raw = window.localStorage.getItem(SESSION_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as SpiritFlixSession;
    if (!parsed.accessToken || !parsed.userId || !parsed.serverUrl) return null;
    return parsed;
  } catch {
    return null;
  }
}

export function storeSession(session: SpiritFlixSession): void {
  window.localStorage.setItem(SESSION_KEY, JSON.stringify(session));
}

export function clearStoredSession(): void {
  window.localStorage.removeItem(SESSION_KEY);
}

function getDeviceId(): string {
  if (typeof window === "undefined") return "spiritflix-server-render";
  const existing = window.localStorage.getItem(DEVICE_ID_KEY);
  if (existing) return existing;
  const generated =
    typeof crypto !== "undefined" && "randomUUID" in crypto
      ? `spiritflix-${crypto.randomUUID()}`
      : `spiritflix-${Math.random().toString(36).slice(2)}`;
  window.localStorage.setItem(DEVICE_ID_KEY, generated);
  return generated;
}

function authHeader(token?: string): string {
  const parts = [
    `MediaBrowser Client="${CLIENT_NAME}"`,
    `Device="${DEVICE_NAME}"`,
    `DeviceId="${getDeviceId()}"`,
    `Version="${CLIENT_VERSION}"`,
  ];
  if (token) parts.push(`Token="${token}"`);
  return parts.join(", ");
}

export function normalizeJellyfinServerUrl(serverUrl: string): string {
  const trimmed = serverUrl.trim().replace(/\/+$/, "");
  try {
    const parsed = new URL(trimmed);
    const path = parsed.pathname.replace(/\/+$/, "");
    if (!path || path === "/" || path === "/web" || path.startsWith("/web/")) {
      return parsed.origin;
    }
    return `${parsed.origin}${path}`;
  } catch {
    return trimmed;
  }
}

function toQuery(params: Record<string, string | number | boolean | undefined>): string {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") query.set(key, String(value));
  });
  return query.toString();
}

export class JellyfinClient {
  readonly serverUrl: string;
  readonly token?: string;
  readonly userId?: string;

  constructor(serverUrl: string, token?: string, userId?: string) {
    this.serverUrl = normalizeJellyfinServerUrl(serverUrl || SPIRITFLIX_DEFAULT_SERVER);
    this.token = token;
    this.userId = userId;
  }

  withSession(session: SpiritFlixSession): JellyfinClient {
    return new JellyfinClient(session.serverUrl, session.accessToken, session.userId);
  }

  private async request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const method = init.method ?? "GET";
    const response = await fetch("/api/spiritflix/jellyfin", {
      method: "POST",
      keepalive: init.keepalive,
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        serverUrl: this.serverUrl,
        path,
        method,
        authorization: authHeader(this.token),
        body: init.body ? JSON.parse(String(init.body)) : undefined,
      }),
    });

    if (!response.ok) {
      if (response.status === 401) {
        throw new Error("Jellyfin rejected that username or password.");
      }
      if (response.status === 404) {
        throw new Error("That Jellyfin server URL did not expose the expected API path.");
      }
      if (response.status >= 500) {
        throw new Error(`Jellyfin server returned ${response.status}.`);
      }
      throw new Error(`Jellyfin request failed with status ${response.status}.`);
    }

    if (response.status === 204) return undefined as T;
    return (await response.json()) as T;
  }

  async checkPublicInfo(): Promise<SpiritFlixServerInfo> {
    return this.request<SpiritFlixServerInfo>("/System/Info/Public");
  }

  async login(username: string, password: string): Promise<SpiritFlixSession> {
    const data = await this.request<JellyfinAuthResponse>("/Users/AuthenticateByName", {
      method: "POST",
      body: JSON.stringify({ Username: username, Pw: password }),
    });

    return {
      serverUrl: this.serverUrl,
      accessToken: data.AccessToken,
      userId: data.User.Id,
      username: data.User.Name,
    };
  }

  async getLibraries(): Promise<JellyfinLibrary[]> {
    if (!this.userId) return [];
    const data = await this.request<JellyfinItemsResponse<JellyfinLibrary>>(
      `/Users/${this.userId}/Views`,
    );
    return data.Items ?? [];
  }

  async getLibraryItems(parentId: string, searchTerm = "", limit?: number): Promise<JellyfinItem[]> {
    if (!this.userId) return [];
    const query = toQuery({
      ParentId: parentId,
      Recursive: true,
      IncludeItemTypes: "Movie,Series,Season,Episode,Video,Folder",
      Fields: GOONER_ITEM_FIELDS,
      ImageTypeLimit: 1,
      EnableImageTypes: "Primary,Backdrop,Thumb,Logo",
      SortBy: "SortName",
      SortOrder: "Ascending",
      SearchTerm: searchTerm,
      Limit: limit,
    });
    const data = await this.request<JellyfinItemsResponse<JellyfinItem>>(
      `/Users/${this.userId}/Items?${query}`,
    );
    if (data.Items?.length || searchTerm) return data.Items ?? [];

    const fallbackQuery = toQuery({
      ParentId: parentId,
      Recursive: true,
      Fields: GOONER_ITEM_FIELDS,
      ImageTypeLimit: 1,
      EnableImageTypes: "Primary,Backdrop,Thumb,Logo",
      SortBy: "SortName",
      SortOrder: "Ascending",
      Limit: limit,
    });
    const fallbackData = await this.request<JellyfinItemsResponse<JellyfinItem>>(
      `/Users/${this.userId}/Items?${fallbackQuery}`,
    );
    return fallbackData.Items ?? [];
  }

  async getPlaylistItems(playlistId: string): Promise<JellyfinItem[]> {
    if (!this.userId) return [];
    const query = toQuery({
      userId: this.userId,
      Fields: "Overview,ProductionYear,RunTimeTicks,Genres,UserData,PrimaryImageAspectRatio,MediaStreams,MediaSources",
      ImageTypeLimit: 1,
      EnableImageTypes: "Primary,Backdrop,Thumb,Logo",
    });
    const data = await this.request<JellyfinItemsResponse<JellyfinItem>>(
      `/Playlists/${playlistId}/Items?${query}`,
    );
    return data.Items ?? [];
  }

  async getPlaylists(): Promise<JellyfinItem[]> {
    if (!this.userId) return [];
    const query = toQuery({
      Recursive: true,
      IncludeItemTypes: "Playlist",
      Fields: "Overview,ProductionYear,RunTimeTicks,Genres,UserData,PrimaryImageAspectRatio,MediaStreams,MediaSources,ChildCount",
      ImageTypeLimit: 1,
      EnableImageTypes: "Primary,Backdrop,Thumb,Logo",
      SortBy: "SortName",
      SortOrder: "Ascending",
      Limit: 100,
    });
    const data = await this.request<JellyfinItemsResponse<JellyfinItem>>(
      `/Users/${this.userId}/Items?${query}`,
    );
    return data.Items ?? [];
  }

  async getContinueWatching(parentId?: string): Promise<JellyfinItem[]> {
    if (!this.userId) return [];
    const query = toQuery({
      Recursive: true,
      ParentId: parentId,
      Fields: GOONER_ITEM_FIELDS,
      ImageTypeLimit: 3,
      EnableImageTypes: "Primary,Backdrop,Thumb,Logo",
      Limit: 18,
    });
    const data = await this.request<JellyfinItemsResponse<JellyfinItem>>(
      `/Users/${this.userId}/Items/Resume?${query}`,
    );
    return data.Items ?? [];
  }

  async getLibraryResumeItems(parentId: string): Promise<JellyfinItem[]> {
    if (!this.userId) return [];
    const query = toQuery({
      ParentId: parentId,
      Recursive: true,
      IncludeItemTypes: "Movie,Episode,Video",
      Fields: GOONER_ITEM_FIELDS,
      Filters: "IsResumable",
      ImageTypeLimit: 3,
      EnableImageTypes: "Primary,Backdrop,Thumb,Logo",
      SortBy: "DatePlayed",
      SortOrder: "Descending",
      Limit: 24,
    });
    const data = await this.request<JellyfinItemsResponse<JellyfinItem>>(
      `/Users/${this.userId}/Items?${query}`,
    );
    return data.Items ?? [];
  }

  async getWatchHistory(parentId?: string): Promise<JellyfinItem[]> {
    if (!this.userId) return [];
    const query = toQuery({
      ParentId: parentId,
      Recursive: true,
      IncludeItemTypes: "Movie,Episode,Video",
      Fields: GOONER_ITEM_FIELDS,
      Filters: "IsPlayed",
      ImageTypeLimit: 3,
      EnableImageTypes: "Primary,Backdrop,Thumb,Logo",
      SortBy: "DatePlayed",
      SortOrder: "Descending",
      Limit: 60,
    });
    const data = await this.request<JellyfinItemsResponse<JellyfinItem>>(
      `/Users/${this.userId}/Items?${query}`,
    );
    return data.Items ?? [];
  }

  async getLatestAdded(): Promise<JellyfinItem[]> {
    return this.getItemsByQuery({ SortBy: "DateCreated", SortOrder: "Descending", Limit: 18 });
  }

  async getFavorites(): Promise<JellyfinItem[]> {
    return this.getItemsByQuery({ Filters: "IsFavorite", SortBy: "SortName", Limit: 18 });
  }

  async getLibraryFavoriteItems(parentId: string): Promise<JellyfinItem[]> {
    if (!this.userId) return [];
    const query = toQuery({
      ParentId: parentId,
      Recursive: true,
      IncludeItemTypes: "Movie,Episode,Video",
      Fields: GOONER_ITEM_FIELDS,
      Filters: "IsFavorite",
      ImageTypeLimit: 3,
      EnableImageTypes: "Primary,Backdrop,Thumb,Logo",
      SortBy: "SortName",
      SortOrder: "Ascending",
      Limit: 24,
    });
    const data = await this.request<JellyfinItemsResponse<JellyfinItem>>(
      `/Users/${this.userId}/Items?${query}`,
    );
    return data.Items ?? [];
  }

  async setFavorite(itemId: string, isFavorite: boolean): Promise<void> {
    if (!this.userId) return;
    await this.request<void>(`/Users/${this.userId}/FavoriteItems/${itemId}`, {
      method: isFavorite ? "POST" : "DELETE",
    });
  }

  async getFaceOrganizerMetadata(items: JellyfinItem[]): Promise<FaceOrganizerMetadataResponse> {
    if (!items.length) {
      return {
        knownPerformers: [],
        videos: {},
        scannedCount: 0,
        generatedAt: new Date().toISOString(),
      };
    }

    const response = await fetch("/api/spiritflix/face-metadata", {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        items: items.map((item) => ({
          id: item.Id,
          name: item.Name,
          path: item.Path,
        })),
      }),
    });

    if (!response.ok) {
      throw new Error("Face Organizer metadata is unavailable.");
    }

    return (await response.json()) as FaceOrganizerMetadataResponse;
  }

  private async getItemsByQuery(extra: Record<string, string | number>): Promise<JellyfinItem[]> {
    if (!this.userId) return [];
    const query = toQuery({
      Recursive: true,
      IncludeItemTypes: "Movie,Episode,Video",
      Fields: GOONER_ITEM_FIELDS,
      ImageTypeLimit: 3,
      EnableImageTypes: "Primary,Backdrop,Thumb,Logo",
      Limit: 18,
      ...extra,
    });
    const data = await this.request<JellyfinItemsResponse<JellyfinItem>>(
      `/Users/${this.userId}/Items?${query}`,
    );
    return data.Items ?? [];
  }

  getImageUrl(item: JellyfinItem, type: "Primary" | "Backdrop" | "Thumb" = "Primary", width = 500): string {
    const tag =
      type === "Backdrop"
        ? item.BackdropImageTags?.[0]
        : item.ImageTags?.[type as keyof JellyfinItem["ImageTags"]];
    const query = toQuery({
      maxWidth: width,
      quality: 88,
      tag,
    });
    return `${this.serverUrl}/Items/${item.Id}/Images/${type}?${query}`;
  }

  async getImageObjectUrl(item: JellyfinItem, type: "Primary" | "Backdrop" | "Thumb" = "Primary", width = 500): Promise<string> {
    const response = await fetch("/api/spiritflix/jellyfin-image", {
      method: "POST",
      headers: {
        Accept: "image/*",
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        serverUrl: this.serverUrl,
        path: new URL(this.getImageUrl(item, type, width)).pathname + new URL(this.getImageUrl(item, type, width)).search,
        authorization: authHeader(this.token),
      }),
    });
    if (!response.ok) throw new Error("Image unavailable");
    return URL.createObjectURL(await response.blob());
  }

  getStreamUrl(itemId: string): string {
    const query = toQuery({
      serverUrl: this.serverUrl,
      itemId,
      token: this.token,
    });
    return `/api/spiritflix/stream?${query}`;
  }

  getHlsUrl(itemId: string): string {
    const query = toQuery({
      api_key: this.token,
      PlaySessionId: `spiritflix-${itemId}`,
      MediaSourceId: itemId,
      VideoCodec: "h264",
      AudioCodec: "aac,mp3,ac3",
      SegmentContainer: "ts",
      MinSegments: 1,
    });
    return `${this.serverUrl}/Videos/${itemId}/master.m3u8?${query}`;
  }

  async reportPlayback(
    itemId: string,
    event: "Start" | "Progress" | "Stopped",
    positionTicks: number,
    isPaused = false,
    options: { keepalive?: boolean } = {},
  ): Promise<void> {
    if (!this.token) return;
    const path =
      event === "Start"
        ? "/Sessions/Playing"
        : event === "Progress"
          ? "/Sessions/Playing/Progress"
          : "/Sessions/Playing/Stopped";
    const playSessionId = `spiritflix-${itemId}`;

    await this.request<void>(path, {
      method: "POST",
      keepalive: options.keepalive,
      body: JSON.stringify({
        ItemId: itemId,
        MediaSourceId: itemId,
        PlaySessionId: playSessionId,
        PositionTicks: positionTicks,
        IsPaused: isPaused,
        PlayMethod: "DirectStream",
        CanSeek: true,
      }),
    }).catch(() => undefined);
  }
}

export function isPlayableItem(item: JellyfinItem): boolean {
  return item.MediaType === "Video" || ["Movie", "Episode", "Video"].includes(item.Type);
}

export function isPlaylistItem(item: JellyfinItem): boolean {
  return item.Type === "Playlist";
}

export function ticksToSeconds(ticks?: number): number {
  return ticks ? Math.max(0, Math.floor(ticks / 10000000)) : 0;
}

export function formatRuntime(ticks?: number): string {
  const totalMinutes = Math.round(ticksToSeconds(ticks) / 60);
  if (!totalMinutes) return "Unknown runtime";
  const hours = Math.floor(totalMinutes / 60);
  const minutes = totalMinutes % 60;
  return hours ? `${hours}h ${minutes}m` : `${minutes}m`;
}
