import type {
  JellyfinAuthResponse,
  JellyfinItem,
  JellyfinItemsResponse,
  JellyfinLibrary,
  FaceOrganizerMetadataResponse,
  SpiritFlixGalleryResponse,
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
const CARD_ITEM_FIELDS =
  "Path,SeriesName,DateCreated,IndexNumber,ParentIndexNumber,ProductionYear,RunTimeTicks,UserData,PrimaryImageAspectRatio,MediaStreams,MediaSources,ChildCount";

export interface HlsPlaybackProfile {
  maxWidth: number;
  maxHeight: number;
  videoBitrate: number;
  audioBitrate: number;
}

const MOBILE_SOURCE_CACHE_TTL_MS = 5 * 60 * 1000;
const mobileSourceCache = new Map<string, { at: number; value: MobileOptimizedSource }>();

export function clearMobileOptimizedSourceCache(): void {
  mobileSourceCache.clear();
}

export interface MobileOptimizedSource {
  available: boolean;
  mode?: "mobile optimized";
  url?: string;
  key?: string;
  receipt?: {
    itemId?: string;
    sourcePathSha256?: string;
      encoder?: string;
      profile?: string;
      workerHost?: string;
      outputSize?: number;
      percentSaved?: number;
      ffprobe?: {
      container?: string;
      videoCodec?: string;
      audioCodec?: string;
      width?: number;
      height?: number;
      duration?: number;
    };
  };
}

export interface JellyfinItemPage {
  items: JellyfinItem[];
  totalRecordCount: number | null;
  startIndex: number;
  limit: number;
  hasMore: boolean;
}

export interface JellyfinItemPageOptions {
  searchTerm?: string;
  limit?: number;
  startIndex?: number;
  fields?: "card" | "full";
  signal?: AbortSignal;
}

export interface SpiritFlixSystemDiagnostics {
  dellFfmpegActive: boolean;
  dellFfmpegProcesses: Array<{
    pid: number;
    command: string;
    pathClass: "media_processing" | "jellyfin_transcode" | "other";
  }>;
  checkedAt: string;
}

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

function isHttpsPage(): boolean {
  return typeof window !== "undefined" && window.location.protocol === "https:";
}

function getDirectServerUrl(serverUrl: string): string {
  return typeof window !== "undefined" && window.location.hostname && !["localhost", "127.0.0.1"].includes(window.location.hostname)
    ? `http://${window.location.hostname}:8096`
    : serverUrl;
}

function itemPathValues(item: JellyfinItem): string[] {
  return [
    item.Path,
    ...(item.MediaSources ?? []).map((source) => source.Path),
  ].filter((value): value is string => Boolean(value));
}

export function isSpiritFlixTrashPath(value?: string): boolean {
  if (!value) return false;
  const normalized = value.replaceAll("\\", "/").toLowerCase();
  return normalized.includes("/.trash/");
}

export function isVisibleSpiritFlixItem(item: JellyfinItem): boolean {
  return !itemPathValues(item).some(isSpiritFlixTrashPath);
}

function visibleItems(items?: JellyfinItem[]): JellyfinItem[] {
  return (items ?? []).filter(isVisibleSpiritFlixItem);
}

function uniqueItemsById(items: JellyfinItem[]): JellyfinItem[] {
  const seen = new Set<string>();
  return items.filter((item) => {
    if (seen.has(item.Id)) return false;
    seen.add(item.Id);
    return true;
  });
}

function getItemFields(fields: "card" | "full" = "card"): string {
  return fields === "full" ? GOONER_ITEM_FIELDS : CARD_ITEM_FIELDS;
}

function pageFromResponse(
  data: JellyfinItemsResponse<JellyfinItem>,
  { startIndex = 0, limit = 20 }: { startIndex?: number; limit?: number },
): JellyfinItemPage {
  const items = visibleItems(data.Items);
  const totalRecordCount = typeof data.TotalRecordCount === "number" ? data.TotalRecordCount : null;
  const loaded = startIndex + items.length;
  return {
    items,
    totalRecordCount,
    startIndex,
    limit,
    hasMore: totalRecordCount == null ? items.length >= limit : loaded < totalRecordCount,
  };
}

function emptyItemPage({ startIndex = 0, limit = 20 }: { startIndex?: number; limit?: number } = {}): JellyfinItemPage {
  return {
    items: [],
    totalRecordCount: 0,
    startIndex,
    limit,
    hasMore: false,
  };
}

export function getHlsPlaybackProfile(): HlsPlaybackProfile {
  const baseProfile: HlsPlaybackProfile = {
    maxWidth: 1280,
    maxHeight: 720,
    videoBitrate: 4000000,
    audioBitrate: 192000,
  };
  if (typeof window === "undefined") return baseProfile;

  const dpr = Math.max(1, Math.min(3, window.devicePixelRatio || 1));
  const cssLongEdge = Math.max(window.innerWidth || 0, window.innerHeight || 0);
  const cssShortEdge = Math.min(window.innerWidth || 0, window.innerHeight || 0);
  const longEdge = cssLongEdge * dpr;
  const shortEdge = cssShortEdge * dpr;

  if (cssShortEdge >= 720 && longEdge >= 1800 && shortEdge >= 900) {
    return {
      maxWidth: 1920,
      maxHeight: 1080,
      videoBitrate: 10000000,
      audioBitrate: 256000,
    };
  }

  if (cssShortEdge >= 600 && longEdge >= 1400 && shortEdge >= 760) {
    return {
      maxWidth: 1600,
      maxHeight: 900,
      videoBitrate: 6500000,
      audioBitrate: 224000,
    };
  }

  return baseProfile;
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
      signal: init.signal,
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

  async getLibraryItemsPage(parentId: string, options: JellyfinItemPageOptions = {}): Promise<JellyfinItemPage> {
    const {
      searchTerm = "",
      limit = 20,
      startIndex = 0,
      fields = "card",
      signal,
    } = options;
    if (!this.userId) return emptyItemPage({ startIndex, limit });
    const query = toQuery({
      ParentId: parentId,
      Recursive: true,
      IncludeItemTypes: "Movie,Series,Season,Episode,Video,Folder",
      Fields: getItemFields(fields),
      ImageTypeLimit: 1,
      EnableImageTypes: "Primary,Backdrop,Thumb,Logo",
      SortBy: "SortName",
      SortOrder: "Ascending",
      SearchTerm: searchTerm,
      Limit: limit,
      StartIndex: startIndex,
    });
    const data = await this.request<JellyfinItemsResponse<JellyfinItem>>(
      `/Users/${this.userId}/Items?${query}`,
      { signal },
    );
    if (data.Items?.length || searchTerm) return pageFromResponse(data, { startIndex, limit });

    const fallbackQuery = toQuery({
      ParentId: parentId,
      Recursive: true,
      Fields: getItemFields(fields),
      ImageTypeLimit: 1,
      EnableImageTypes: "Primary,Backdrop,Thumb,Logo",
      SortBy: "SortName",
      SortOrder: "Ascending",
      Limit: limit,
      StartIndex: startIndex,
    });
    const fallbackData = await this.request<JellyfinItemsResponse<JellyfinItem>>(
      `/Users/${this.userId}/Items?${fallbackQuery}`,
      { signal },
    );
    return pageFromResponse(fallbackData, { startIndex, limit });
  }

  async getLibraryItems(parentId: string, searchTerm = "", limit?: number): Promise<JellyfinItem[]> {
    const page = await this.getLibraryItemsPage(parentId, {
      searchTerm,
      limit: limit ?? 10_000,
      startIndex: 0,
      fields: "full",
    });
    return page.items;
  }

  async getAllLibraryItems(
    parentId: string,
    options: Pick<JellyfinItemPageOptions, "searchTerm" | "fields" | "signal"> & { pageSize?: number; maxItems?: number } = {},
  ): Promise<JellyfinItem[]> {
    const { searchTerm = "", fields = "full", signal, pageSize = 500, maxItems } = options;
    const items: JellyfinItem[] = [];
    let startIndex = 0;

    for (;;) {
      const remaining = typeof maxItems === "number" ? maxItems - items.length : pageSize;
      if (remaining <= 0) return uniqueItemsById(items);
      const page = await this.getLibraryItemsPage(parentId, {
        searchTerm,
        startIndex,
        limit: Math.min(pageSize, remaining),
        fields,
        signal,
      });
      items.push(...page.items);
      if (!page.hasMore || page.items.length === 0) return uniqueItemsById(items);
      startIndex = page.startIndex + page.items.length;
    }
  }

  async getItem(itemId: string): Promise<JellyfinItem | null> {
    if (!this.userId || !itemId) return null;
    const query = toQuery({
      Fields: GOONER_ITEM_FIELDS,
      ImageTypeLimit: 3,
      EnableImageTypes: "Primary,Backdrop,Thumb,Logo",
    });
    const item = await this.request<JellyfinItem>(
      `/Users/${this.userId}/Items/${encodeURIComponent(itemId)}?${query}`,
    );
    return isVisibleSpiritFlixItem(item) ? item : null;
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
    return visibleItems(data.Items);
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
    return visibleItems(data.Items);
  }

  async getContinueWatchingPage(parentId?: string, options: JellyfinItemPageOptions = {}): Promise<JellyfinItemPage> {
    const { limit = 18, startIndex = 0, fields = "card", signal } = options;
    if (!this.userId) return emptyItemPage({ startIndex, limit });
    const query = toQuery({
      Recursive: true,
      ParentId: parentId,
      Fields: getItemFields(fields),
      ImageTypeLimit: 1,
      EnableImageTypes: "Primary,Backdrop,Thumb,Logo",
      Limit: limit,
      StartIndex: startIndex,
    });
    const data = await this.request<JellyfinItemsResponse<JellyfinItem>>(
      `/Users/${this.userId}/Items/Resume?${query}`,
      { signal },
    );
    return pageFromResponse(data, { startIndex, limit });
  }

  async getContinueWatching(parentId?: string): Promise<JellyfinItem[]> {
    return (await this.getContinueWatchingPage(parentId, { limit: 18, fields: "full" })).items;
  }

  async getLibraryResumeItemsPage(parentId: string, options: JellyfinItemPageOptions = {}): Promise<JellyfinItemPage> {
    const { limit = 24, startIndex = 0, fields = "card", signal } = options;
    if (!this.userId) return emptyItemPage({ startIndex, limit });
    const query = toQuery({
      ParentId: parentId,
      Recursive: true,
      IncludeItemTypes: "Movie,Episode,Video",
      Fields: getItemFields(fields),
      Filters: "IsResumable",
      ImageTypeLimit: 1,
      EnableImageTypes: "Primary,Backdrop,Thumb,Logo",
      SortBy: "DatePlayed",
      SortOrder: "Descending",
      Limit: limit,
      StartIndex: startIndex,
    });
    const data = await this.request<JellyfinItemsResponse<JellyfinItem>>(
      `/Users/${this.userId}/Items?${query}`,
      { signal },
    );
    return pageFromResponse(data, { startIndex, limit });
  }

  async getLibraryResumeItems(parentId: string): Promise<JellyfinItem[]> {
    return (await this.getLibraryResumeItemsPage(parentId, { limit: 24, fields: "full" })).items;
  }

  async getWatchHistoryPage(parentId?: string, options: JellyfinItemPageOptions = {}): Promise<JellyfinItemPage> {
    const { limit = 60, startIndex = 0, fields = "card", signal } = options;
    if (!this.userId) return emptyItemPage({ startIndex, limit });
    const query = toQuery({
      ParentId: parentId,
      Recursive: true,
      IncludeItemTypes: "Movie,Episode,Video",
      Fields: getItemFields(fields),
      ImageTypeLimit: 1,
      EnableImageTypes: "Primary,Backdrop,Thumb,Logo",
      SortBy: "DatePlayed",
      SortOrder: "Descending",
      Limit: limit,
      StartIndex: startIndex,
    });
    const data = await this.request<JellyfinItemsResponse<JellyfinItem>>(
      `/Users/${this.userId}/Items?${query}`,
      { signal },
    );
    return pageFromResponse(data, { startIndex, limit });
  }

  async getWatchHistory(parentId?: string): Promise<JellyfinItem[]> {
    return (await this.getWatchHistoryPage(parentId, { limit: 60, fields: "full" })).items;
  }

  async getLatestAdded(): Promise<JellyfinItem[]> {
    return (await this.getLatestAddedPage()).items;
  }

  async getLatestAddedPage(options: JellyfinItemPageOptions = {}): Promise<JellyfinItemPage> {
    return this.getItemsPageByQuery(
      { SortBy: "DateCreated", SortOrder: "Descending" },
      { limit: 18, ...options },
    );
  }

  async getLibraryLatestAddedPage(parentId: string, options: JellyfinItemPageOptions = {}): Promise<JellyfinItemPage> {
    if (!this.userId) return emptyItemPage({ startIndex: options.startIndex, limit: options.limit });
    const { limit = 18, startIndex = 0, fields = "card", signal } = options;
    const query = toQuery({
      ParentId: parentId,
      Recursive: true,
      IncludeItemTypes: "Movie,Episode,Video",
      Fields: getItemFields(fields),
      ImageTypeLimit: 1,
      EnableImageTypes: "Primary,Backdrop,Thumb,Logo",
      SortBy: "DateCreated",
      SortOrder: "Descending",
      Limit: limit,
      StartIndex: startIndex,
    });
    const data = await this.request<JellyfinItemsResponse<JellyfinItem>>(
      `/Users/${this.userId}/Items?${query}`,
      { signal },
    );
    return pageFromResponse(data, { startIndex, limit });
  }

  async getFavorites(): Promise<JellyfinItem[]> {
    return (await this.getFavoritesPage({ limit: 200, fields: "full" })).items;
  }

  async getFavoritesPage(options: JellyfinItemPageOptions = {}): Promise<JellyfinItemPage> {
    return this.getItemsPageByQuery(
      { Filters: "IsFavorite", SortBy: "SortName" },
      { limit: 18, ...options },
    );
  }

  async getLibraryFavoriteItemsPage(parentId: string, options: JellyfinItemPageOptions = {}): Promise<JellyfinItemPage> {
    const { limit = 18, startIndex = 0, fields = "card", signal } = options;
    if (!this.userId) return emptyItemPage({ startIndex, limit });
    const query = toQuery({
      ParentId: parentId,
      Recursive: true,
      IncludeItemTypes: "Movie,Episode,Video",
      Fields: getItemFields(fields),
      Filters: "IsFavorite",
      ImageTypeLimit: 1,
      EnableImageTypes: "Primary,Backdrop,Thumb,Logo",
      SortBy: "SortName",
      SortOrder: "Ascending",
      Limit: limit,
      StartIndex: startIndex,
    });
    const data = await this.request<JellyfinItemsResponse<JellyfinItem>>(
      `/Users/${this.userId}/Items?${query}`,
      { signal },
    );
    return pageFromResponse(data, { startIndex, limit });
  }

  async getLibraryFavoriteItems(parentId: string): Promise<JellyfinItem[]> {
    return (await this.getLibraryFavoriteItemsPage(parentId, { limit: 200, fields: "full" })).items;
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
      cache: "no-store",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
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

  async getGallery(): Promise<SpiritFlixGalleryResponse> {
    const response = await fetch("/api/spiritflix/gallery", {
      method: "GET",
      cache: "no-store",
      headers: {
        Accept: "application/json",
        "Cache-Control": "no-cache",
      },
    });

    if (!response.ok) {
      throw new Error("SpiritFlix gallery is unavailable.");
    }

    return (await response.json()) as SpiritFlixGalleryResponse;
  }

  private async getItemsPageByQuery(
    extra: Record<string, string | number>,
    options: JellyfinItemPageOptions = {},
  ): Promise<JellyfinItemPage> {
    const { limit = 18, startIndex = 0, fields = "card", signal } = options;
    if (!this.userId) return emptyItemPage({ startIndex, limit });
    const query = toQuery({
      Recursive: true,
      IncludeItemTypes: "Movie,Episode,Video",
      Fields: getItemFields(fields),
      ImageTypeLimit: 1,
      EnableImageTypes: "Primary,Backdrop,Thumb,Logo",
      Limit: limit,
      StartIndex: startIndex,
      ...extra,
    });
    const data = await this.request<JellyfinItemsResponse<JellyfinItem>>(
      `/Users/${this.userId}/Items?${query}`,
      { signal },
    );
    return pageFromResponse(data, { startIndex, limit });
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

  getImageProxyUrl(item: JellyfinItem, type: "Primary" | "Backdrop" | "Thumb" = "Primary", width = 500): string {
    const imageUrl = new URL(this.getImageUrl(item, type, width));
    const query = toQuery({
      serverUrl: this.serverUrl,
      path: `${imageUrl.pathname}${imageUrl.search}`,
      token: this.token,
    });
    return `/api/spiritflix/jellyfin-image?${query}`;
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

  getStreamUrl(itemId: string, options: { audioStreamIndex?: number } = {}): string {
    const directServerUrl = getDirectServerUrl(this.serverUrl);
    const query = toQuery({
      serverUrl: directServerUrl,
      itemId,
      token: this.token,
      audioStreamIndex: options.audioStreamIndex,
    });
    if (isHttpsPage()) return `/api/spiritflix/stream?${query}`;

    const directQuery = toQuery({
      Static: "true",
      api_key: this.token,
      PlaySessionId: `spiritflix-${itemId}`,
      AudioStreamIndex: options.audioStreamIndex,
    });
    return `${directServerUrl}/Videos/${encodeURIComponent(itemId)}/Stream?${directQuery}`;
  }

  getHlsUrl(itemId: string, options: { audioStreamIndex?: number } = {}): string {
    const directServerUrl = getDirectServerUrl(this.serverUrl);
    const playbackProfile = getHlsPlaybackProfile();
    const query = toQuery({
      api_key: this.token,
      PlaySessionId: `spiritflix-${itemId}`,
      MediaSourceId: itemId,
      VideoCodec: "h264",
      AudioCodec: "aac,mp3,ac3",
      SegmentContainer: "ts",
      MinSegments: 1,
      VideoBitrate: playbackProfile.videoBitrate,
      AudioBitrate: playbackProfile.audioBitrate,
      MaxWidth: playbackProfile.maxWidth,
      MaxHeight: playbackProfile.maxHeight,
      AudioStreamIndex: options.audioStreamIndex,
    });
    const path = `/Videos/${encodeURIComponent(itemId)}/master.m3u8?${query}`;
    if (isHttpsPage()) {
      const proxyQuery = toQuery({
        serverUrl: directServerUrl,
        token: this.token,
        path,
      });
      return `/api/spiritflix/hls?${proxyQuery}`;
    }
    return `${directServerUrl}${path}`;
  }

  getCachedMobileOptimizedSource(itemId: string): MobileOptimizedSource | null {
    const entry = mobileSourceCache.get(itemId);
    if (!entry || Date.now() - entry.at > MOBILE_SOURCE_CACHE_TTL_MS) return null;
    return entry.value;
  }

  async getMobileOptimizedSource(item: JellyfinItem): Promise<MobileOptimizedSource> {
    const cached = this.getCachedMobileOptimizedSource(item.Id);
    if (cached) return cached;

    const query = toQuery({ itemId: item.Id });
    const response = await fetch(`/api/spiritflix/mobile-optimized?${query}`, {
      method: "GET",
      cache: "default",
      headers: {
        Accept: "application/json",
      },
    });
    const result: MobileOptimizedSource =
      response.status === 404
        ? { available: false }
        : response.ok
          ? ((await response.json()) as MobileOptimizedSource)
          : (() => {
              throw new Error(`Mobile optimized lookup failed with status ${response.status}.`);
            })();
    mobileSourceCache.set(item.Id, { at: Date.now(), value: result });
    return result;
  }

  async getSystemDiagnostics(): Promise<SpiritFlixSystemDiagnostics> {
    const response = await fetch("/api/spiritflix/system-diagnostics", {
      method: "GET",
      cache: "no-store",
      headers: {
        Accept: "application/json",
        "Cache-Control": "no-cache",
      },
    });
    if (!response.ok) throw new Error(`System diagnostics failed with status ${response.status}.`);
    return (await response.json()) as SpiritFlixSystemDiagnostics;
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
  return isVisibleSpiritFlixItem(item) && (item.MediaType === "Video" || ["Movie", "Episode", "Video"].includes(item.Type));
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
