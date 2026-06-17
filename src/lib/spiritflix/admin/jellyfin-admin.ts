import { normalizeJellyfinServerUrl } from "@/lib/spiritflix-jellyfin-client";
import type { JellyfinItem, JellyfinLibrary } from "@/lib/spiritflix-types";
import type {
  JellyfinAdminItemsResponse,
  SpiritFlixAdminItem,
  SpiritFlixAdminLibraryRequest,
  SpiritFlixAdminLibraryResponse,
  SpiritFlixAdminSortBy,
  SpiritFlixAdminSortOrder,
} from "./types";

const CLIENT_NAME = "SpiritFlix Admin";
const CLIENT_VERSION = "0.1.0";
const DEVICE_NAME = "SpiritFlix Admin API";
const DEVICE_ID = "spiritflix-admin-api";
const DEFAULT_INCLUDE_ITEM_TYPES = "Movie,Series,Season,Episode,Video,Folder";
const ITEM_FIELDS =
  "Path,SeriesName,DateCreated,DateLastMediaAdded,DateLastSaved,IndexNumber,ParentIndexNumber,Overview,ProductionYear,RunTimeTicks,Genres,People,UserData,PrimaryImageAspectRatio,MediaSources,ChildCount";

const allowedHosts = new Set([
  "spirit.tailb69ea6.ts.net:8096",
  "100.111.32.31:8096",
  "127.0.0.1:8096",
  "localhost:8096",
]);

const sortMap: Record<SpiritFlixAdminSortBy, string> = {
  dateAdded: "DateCreated",
  dateModified: "DateLastSaved",
  title: "SortName",
  runtime: "Runtime",
  size: "Size",
  path: "Path",
  library: "SortName",
  watched: "PlayCount",
  favorite: "SortName",
};

function isAllowedServer(serverUrl: string): boolean {
  try {
    const parsed = new URL(serverUrl);
    return (parsed.protocol === "http:" || parsed.protocol === "https:") && allowedHosts.has(parsed.host);
  } catch {
    return false;
  }
}

function authHeader(token: string): string {
  return [
    `MediaBrowser Client="${CLIENT_NAME}"`,
    `Device="${DEVICE_NAME}"`,
    `DeviceId="${DEVICE_ID}"`,
    `Version="${CLIENT_VERSION}"`,
    `Token="${token}"`,
  ].join(", ");
}

function queryString(params: Record<string, string | number | boolean | undefined>): string {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== "") query.set(key, String(value));
  });
  return query.toString();
}

async function jellyfinRequest<T>(serverUrl: string, token: string, path: string): Promise<T> {
  const response = await fetch(`${serverUrl}${path}`, {
    method: "GET",
    headers: {
      Accept: "application/json",
      "X-Emby-Authorization": authHeader(token),
    },
    cache: "no-store",
  });

  if (!response.ok) {
    throw new Error(`Jellyfin admin request failed with status ${response.status}.`);
  }

  return (await response.json()) as T;
}

function parentPathFor(item: JellyfinItem): string | undefined {
  const sourcePath = item.Path ?? item.MediaSources?.find((source) => source.Path)?.Path;
  if (!sourcePath) return undefined;
  const slash = Math.max(sourcePath.lastIndexOf("/"), sourcePath.lastIndexOf("\\"));
  return slash > 0 ? sourcePath.slice(0, slash) : undefined;
}

function extensionFor(item: JellyfinItem): string | undefined {
  const sourcePath = item.Path ?? item.MediaSources?.find((source) => source.Path)?.Path;
  const match = sourcePath?.match(/(\.[a-z0-9]+)$/i);
  return match?.[1]?.toLowerCase();
}

export function normalizeJellyfinAdminItem(item: JellyfinItem, libraries: JellyfinLibrary[]): SpiritFlixAdminItem {
  const library = libraries.find((candidate) => candidate.Id === item.Id) ?? libraries.find((candidate) => item.Path?.toLowerCase().includes(candidate.Name.toLowerCase()));
  const mediaSource = item.MediaSources?.find((source) => source.Path || source.Size || source.RunTimeTicks);
  const path = mediaSource?.Path ?? item.Path;
  const people = item.People?.filter((person) => ["actor", "actress", "artist", "performer"].includes(person.Type?.toLowerCase() ?? ""));

  return {
    id: `jellyfin:${item.Id}`,
    name: item.Name,
    type: "jellyfin-item",
    libraryName: library?.Name,
    jellyfinId: item.Id,
    jellyfinItemId: item.Id,
    jellyfinItem: item,
    path,
    parentPath: parentPathFor(item),
    jellyfinPath: item.Path,
    mediaType: item.MediaType,
    itemType: item.Type,
    extension: extensionFor(item),
    sizeBytes: mediaSource?.Size,
    dateCreated: item.DateCreated,
    dateModified: undefined,
    dateAdded: item.DateCreated,
    runtimeTicks: item.RunTimeTicks ?? mediaSource?.RunTimeTicks,
    watched: Boolean(item.UserData?.Played),
    favorite: Boolean(item.UserData?.IsFavorite),
    hasImage: Boolean(item.ImageTags?.Primary || item.ImageTags?.Thumb || item.BackdropImageTags?.length),
    imageType: item.ImageTags?.Primary ? "Primary" : item.ImageTags?.Thumb ? "Thumb" : item.BackdropImageTags?.length ? "Backdrop" : undefined,
    imageStatus: item.ImageTags?.Primary || item.ImageTags?.Thumb || item.BackdropImageTags?.length ? "available" : "missing",
    jellyfinMatchedBy: "exact-path",
    jellyfinMatchCandidateCount: 1,
    playable: item.MediaType === "Video" || ["Movie", "Episode", "Video"].includes(item.Type),
    resumePositionTicks: item.UserData?.PlaybackPositionTicks,
    modelNames: people?.map((person) => person.Name).filter(Boolean),
  };
}

export async function listJellyfinAdminItems(request: SpiritFlixAdminLibraryRequest): Promise<SpiritFlixAdminLibraryResponse> {
  const serverUrl = normalizeJellyfinServerUrl(request.serverUrl ?? "");
  const accessToken = request.accessToken ?? "";
  const userId = request.userId ?? "";

  if (!serverUrl || !accessToken || !userId) {
    throw new Error("SpiritFlix admin library requires a Jellyfin session.");
  }

  if (!isAllowedServer(serverUrl)) {
    throw new Error("That Jellyfin server is not allowed for SpiritFlix admin.");
  }

  const sortBy = request.sortBy ?? "dateAdded";
  const sortOrder = request.sortOrder ?? "desc";
  const limit = Math.max(1, Math.min(500, request.limit ?? 100));
  const startIndex = Math.max(0, request.startIndex ?? 0);
  const includeItemTypes = request.includeItemTypes || DEFAULT_INCLUDE_ITEM_TYPES;
  const libraries = (await jellyfinRequest<JellyfinAdminItemsResponse & { Items?: JellyfinLibrary[] }>(serverUrl, accessToken, `/Users/${userId}/Views`)).Items ?? [];
  const selectedLibraryId = request.libraryId ?? "";
  const parentId = request.parentId || selectedLibraryId;
  const query = queryString({
    ParentId: parentId,
    Recursive: request.recursive ?? true,
    IncludeItemTypes: includeItemTypes,
    Fields: ITEM_FIELDS,
    ImageTypeLimit: 1,
    EnableImageTypes: "Primary,Backdrop,Thumb,Logo",
    SortBy: sortMap[sortBy] ?? "DateCreated",
    SortOrder: sortOrder === "asc" ? "Ascending" : "Descending",
    SearchTerm: request.searchTerm,
    Limit: limit,
    StartIndex: startIndex,
  });
  const items = await jellyfinRequest<JellyfinAdminItemsResponse>(serverUrl, accessToken, `/Users/${userId}/Items?${query}`);

  return {
    schema: "spiritflix-admin-library/v1",
    generatedAt: new Date().toISOString(),
    libraries,
    items: (items.Items ?? []).map((item) => normalizeJellyfinAdminItem(item, libraries)),
    totalRecordCount: items.TotalRecordCount ?? items.Items?.length ?? 0,
    query: {
      searchTerm: request.searchTerm ?? "",
      libraryId: selectedLibraryId,
      parentId,
      recursive: request.recursive ?? true,
      sortBy,
      sortOrder,
      limit,
      startIndex,
      includeItemTypes,
    },
  };
}
