"use client";

import { lazy, Suspense, useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  clearStoredSession,
  getStoredSession,
  JellyfinClient,
  isPlayableItem,
  isVisibleSpiritFlixItem,
  normalizeJellyfinServerUrl,
  SPIRITFLIX_DEFAULT_SERVER,
  storeSession,
  type JellyfinItemPage,
} from "@/lib/spiritflix-jellyfin-client";
import type {
  JellyfinItem,
  SpiritFlixHomeData,
  SpiritFlixManualModelRecord,
  SpiritFlixPagingState,
  SpiritFlixServerInfo,
  SpiritFlixSession,
} from "@/lib/spiritflix-types";
import { hasResumeProgress } from "@/lib/spiritflix-resume";
import { filterItemsByVideoOrientation, getOrientationFilterLabel, type SpiritFlixVideoOrientation } from "@/lib/spiritflix-orientation";
import { SpiritFlixHome } from "./SpiritFlixHome";
import { SpiritFlixLogin } from "./SpiritFlixLogin";
import { SpiritFlixSplash, type SpiritFlixLoadProgress } from "./SpiritFlixSplash";

const SpiritFlixDetailsModal = lazy(() =>
  import("./SpiritFlixDetailsModal").then((module) => ({
    default: module.SpiritFlixDetailsModal,
  })),
);

const SpiritFlixPlayer = lazy(() =>
  import("./SpiritFlixPlayer").then((module) => ({
    default: module.SpiritFlixPlayer,
  })),
);

export interface SpiritFlixPlaybackQueue {
  items: JellyfinItem[];
  originalItems?: JellyfinItem[];
  currentIndex: number;
  sourceTitle: string;
  startPositionTicks?: number;
  isShuffled?: boolean;
}

export interface SpiritFlixPlaybackProgress {
  itemId: string;
  item?: JellyfinItem;
  positionTicks: number;
  isEnded?: boolean;
}

const emptyHome: SpiritFlixHomeData = {
  libraries: [],
  playlists: [],
  selectedLibraryId: null,
  featuredItems: [],
  libraryItems: [],
  continueWatching: [],
  watchHistory: [],
  latestAdded: [],
  favorites: [],
  modelCountItems: [],
};

const OTHER_LIBRARY_NAME = "Other";
const PLAYLIST_LIBRARY_NAME = "Playlists";
const HIDDEN_LIBRARY_NAMES = new Set(["music"]);
const MOBILE_LIBRARY_PAGE_SIZE = 24;
const DESKTOP_LIBRARY_PAGE_SIZE = 48;
const MOBILE_SHELF_PAGE_SIZE = 10;
const DESKTOP_SHELF_PAGE_SIZE = 18;
const MOBILE_HISTORY_PAGE_SIZE = 16;
const DESKTOP_HISTORY_PAGE_SIZE = 32;

function isMediaLibrary(library: { Name: string; CollectionType?: string }): boolean {
  const name = library.Name.toLowerCase();
  const collectionType = library.CollectionType?.toLowerCase();
  return (
    !HIDDEN_LIBRARY_NAMES.has(name) &&
    name !== PLAYLIST_LIBRARY_NAME.toLowerCase() &&
    collectionType !== "playlists" &&
    collectionType !== "music"
  );
}

function uniqueItems(items: JellyfinItem[]): JellyfinItem[] {
  const seen = new Set<string>();
  return items.filter((item) => {
    if (seen.has(item.Id)) return false;
    seen.add(item.Id);
    return true;
  });
}

function shuffleItems(items: JellyfinItem[]): JellyfinItem[] {
  const shuffled = [...items];
  for (let index = shuffled.length - 1; index > 0; index -= 1) {
    const swapIndex = Math.floor(Math.random() * (index + 1));
    [shuffled[index], shuffled[swapIndex]] = [shuffled[swapIndex], shuffled[index]];
  }
  return shuffled;
}

function shuffleQueueAfterCurrent(items: JellyfinItem[], currentItemId: string): JellyfinItem[] {
  const currentItem = items.find((item) => item.Id === currentItemId);
  const remainingItems = items.filter((item) => item.Id !== currentItemId);
  return currentItem ? [currentItem, ...shuffleItems(remainingItems)] : shuffleItems(items);
}

export function reorderQueueItems(items: JellyfinItem[], activeItemId: string, overItemId: string): JellyfinItem[] {
  const activeIndex = items.findIndex((item) => item.Id === activeItemId);
  const overIndex = items.findIndex((item) => item.Id === overItemId);
  if (activeIndex < 0 || overIndex < 0 || activeIndex === overIndex) return items;
  const nextItems = [...items];
  const [activeItem] = nextItems.splice(activeIndex, 1);
  if (!activeItem) return items;
  nextItems.splice(overIndex, 0, activeItem);
  return nextItems;
}

export function removeDeletedItemFromHomeData(homeData: SpiritFlixHomeData, itemId: string): SpiritFlixHomeData {
  const withoutDeleted = (items: JellyfinItem[]) => items.filter((candidate) => candidate.Id !== itemId && isVisibleSpiritFlixItem(candidate));
  return {
    ...homeData,
    featuredItems: withoutDeleted(homeData.featuredItems),
    libraryItems: withoutDeleted(homeData.libraryItems),
    continueWatching: withoutDeleted(homeData.continueWatching),
    watchHistory: withoutDeleted(homeData.watchHistory),
    latestAdded: withoutDeleted(homeData.latestAdded),
    favorites: withoutDeleted(homeData.favorites),
    modelCountItems: withoutDeleted(homeData.modelCountItems ?? []),
  };
}

export function removeDeletedItemFromQueue(
  queue: SpiritFlixPlaybackQueue,
  itemId: string,
  requestedNextItem?: JellyfinItem | null,
): { queue: SpiritFlixPlaybackQueue | null; nextItem: JellyfinItem | null } {
  const items = queue.items.filter((queueItem) => queueItem.Id !== itemId && isVisibleSpiritFlixItem(queueItem));
  const originalItems = (queue.originalItems ?? queue.items).filter((queueItem) => queueItem.Id !== itemId && isVisibleSpiritFlixItem(queueItem));
  if (!items.length) return { queue: null, nextItem: null };
  const nextItem =
    (requestedNextItem ? items.find((queueItem) => queueItem.Id === requestedNextItem.Id) : null) ??
    items[Math.min(queue.currentIndex, Math.max(0, items.length - 1))] ??
    null;
  if (!nextItem) return { queue: null, nextItem: null };
  return {
    nextItem,
    queue: {
      ...queue,
      items,
      originalItems,
      currentIndex: Math.max(0, items.findIndex((queueItem) => queueItem.Id === nextItem.Id)),
    },
  };
}

function getLastPlayedMs(item: JellyfinItem): number {
  if (!item.UserData?.LastPlayedDate) return 0;
  const value = new Date(item.UserData.LastPlayedDate).getTime();
  return Number.isFinite(value) ? value : 0;
}

function sortByLastPlayed(items: JellyfinItem[]): JellyfinItem[] {
  return [...items].sort((left, right) => getLastPlayedMs(right) - getLastPlayedMs(left));
}

function hasWatchActivity(item: JellyfinItem): boolean {
  return Boolean(
    item.UserData?.LastPlayedDate ||
      item.UserData?.Played ||
      (item.UserData?.PlaybackPositionTicks && item.UserData.PlaybackPositionTicks > 0) ||
      (item.UserData?.PlayCount && item.UserData.PlayCount > 0),
  );
}

function isMobileSpiritFlixViewport(): boolean {
  if (typeof window === "undefined" || typeof window.matchMedia !== "function") return false;
  return window.matchMedia("(max-width: 980px), (pointer: coarse)").matches;
}

function getInitialPageSizes() {
  const mobile = isMobileSpiritFlixViewport();
  return {
    library: mobile ? MOBILE_LIBRARY_PAGE_SIZE : DESKTOP_LIBRARY_PAGE_SIZE,
    shelf: mobile ? MOBILE_SHELF_PAGE_SIZE : DESKTOP_SHELF_PAGE_SIZE,
    history: mobile ? MOBILE_HISTORY_PAGE_SIZE : DESKTOP_HISTORY_PAGE_SIZE,
  };
}

function pagingFromPage(page: JellyfinItemPage): SpiritFlixPagingState {
  return {
    loaded: page.startIndex + page.items.length,
    total: page.totalRecordCount,
    pageSize: page.limit,
    hasMore: page.hasMore,
  };
}

function emptyJellyfinPage(limit: number): JellyfinItemPage {
  return {
    items: [],
    totalRecordCount: 0,
    startIndex: 0,
    limit,
    hasMore: false,
  };
}

function appendUniqueItems(current: JellyfinItem[], incoming: JellyfinItem[]): JellyfinItem[] {
  return uniqueItems([...current, ...incoming]);
}

function mergeContinueWatchingItems({
  continueWatching,
  watchHistory,
  libraryItems,
  isNotDeleted,
}: {
  continueWatching: JellyfinItem[];
  watchHistory: JellyfinItem[];
  libraryItems: JellyfinItem[];
  isNotDeleted: (item: JellyfinItem) => boolean;
}): JellyfinItem[] {
  const watchHistoryItems = sortByLastPlayed(uniqueItems(watchHistory.filter(isNotDeleted).filter(hasWatchActivity)));
  return sortByLastPlayed(
    uniqueItems([
      ...continueWatching.filter(isNotDeleted),
      ...watchHistoryItems.filter(hasResumeProgress),
      ...libraryItems.filter(hasResumeProgress),
    ]),
  );
}

function byEpisodeOrder(left: JellyfinItem, right: JellyfinItem): number {
  return (
    (left.ParentIndexNumber ?? 0) - (right.ParentIndexNumber ?? 0) ||
    (left.IndexNumber ?? 0) - (right.IndexNumber ?? 0) ||
    left.Name.localeCompare(right.Name)
  );
}

function normalizeSpiritFlixPath(value?: string): string {
  return (value ?? "").replace(/\\/g, "/");
}

function isAnimePath(value?: string): boolean {
  const normalized = normalizeSpiritFlixPath(value).toLowerCase();
  return normalized.includes("/media/anime/") || normalized.includes("/anime/");
}

function isSeriesPlaybackItem(item: JellyfinItem): boolean {
  return item.Type?.toLowerCase() === "episode" || isAnimePath(item.Path) || item.MediaSources?.some((source) => isAnimePath(source.Path)) === true;
}

function getSeriesNameFromPath(item: JellyfinItem): string {
  const sourcePath = normalizeSpiritFlixPath(item.MediaSources?.[0]?.Path ?? item.Path);
  const parts = sourcePath.split("/").filter(Boolean);
  const seasonIndex = parts.findIndex((part) => /^season\s+\d+/i.test(part));
  if (seasonIndex > 0) return parts[seasonIndex - 1]?.toLowerCase() ?? "";
  const animeIndex = parts.findIndex((part) => part.toLowerCase() === "anime");
  return animeIndex >= 0 ? parts[animeIndex + 1]?.toLowerCase() ?? "" : "";
}

function getSeriesPlaybackKey(item: JellyfinItem): string {
  if (!isSeriesPlaybackItem(item)) return "";
  const pathSeriesName = getSeriesNameFromPath(item);
  if (isAnimePath(item.Path) || item.MediaSources?.some((source) => isAnimePath(source.Path)) === true) {
    return pathSeriesName || item.SeriesName?.trim().toLowerCase() || "";
  }
  if (item.SeriesName?.trim()) return item.SeriesName.trim().toLowerCase();
  return pathSeriesName;
}

function getSeriesPlaybackQueue(item: JellyfinItem, candidates: JellyfinItem[]): JellyfinItem[] {
  const seriesKey = getSeriesPlaybackKey(item);
  if (!seriesKey) return [];
  return uniqueItems([item, ...candidates])
    .filter((candidate) => isPlayableItem(candidate) && getSeriesPlaybackKey(candidate) === seriesKey)
    .sort(byEpisodeOrder);
}

function applyPlaybackProgress(item: JellyfinItem, progress: SpiritFlixPlaybackProgress): JellyfinItem {
  if (item.Id !== progress.itemId) return item;
  const runtimeTicks = item.RunTimeTicks ?? 0;
  const clampedTicks = progress.isEnded ? 0 : Math.max(0, progress.positionTicks);
  const playedPercentage = progress.isEnded
    ? 100
    : runtimeTicks > 0
      ? Math.max(0, Math.min(100, (clampedTicks / runtimeTicks) * 100))
      : item.UserData?.PlayedPercentage;

  return {
    ...item,
    UserData: {
      ...item.UserData,
      PlaybackPositionTicks: clampedTicks,
      Played: progress.isEnded ? true : false,
      PlayedPercentage: playedPercentage,
      LastPlayedDate: new Date().toISOString(),
    },
  };
}

function upsertPlaybackItem(items: JellyfinItem[], item: JellyfinItem): JellyfinItem[] {
  const nextItems = items.filter((candidate) => candidate.Id !== item.Id);
  if (item.UserData?.Played || !(item.UserData?.PlaybackPositionTicks && item.UserData.PlaybackPositionTicks > 0)) {
    return nextItems;
  }
  return [item, ...nextItems];
}

function upsertWatchHistoryItem(items: JellyfinItem[], item: JellyfinItem): JellyfinItem[] {
  const nextItems = items.filter((candidate) => candidate.Id !== item.Id);
  if (!hasWatchActivity(item)) return nextItems;
  return sortByLastPlayed([item, ...nextItems]);
}

function applyFavoriteState(item: JellyfinItem, itemId: string, isFavorite: boolean): JellyfinItem {
  if (item.Id !== itemId) return item;
  return {
    ...item,
    UserData: {
      ...item.UserData,
      IsFavorite: isFavorite,
    },
  };
}

function upsertFavoriteItem(items: JellyfinItem[], item: JellyfinItem): JellyfinItem[] {
  const nextItems = items.filter((candidate) => candidate.Id !== item.Id);
  if (!item.UserData?.IsFavorite) return nextItems;
  return [item, ...nextItems].sort((left, right) => left.Name.localeCompare(right.Name));
}

export function inferPlaybackQueueForItem(
  item: JellyfinItem,
  homeData: SpiritFlixHomeData,
): { items: JellyfinItem[]; sourceTitle: string } | null {
  const sources: Array<{ items: JellyfinItem[]; sourceTitle: string }> = [
    { items: homeData.continueWatching, sourceTitle: "Continue Watching" },
    { items: homeData.latestAdded, sourceTitle: "Latest Added" },
    { items: homeData.featuredItems, sourceTitle: "Featured Anime" },
    { items: homeData.favorites, sourceTitle: "Favorites" },
    { items: homeData.watchHistory, sourceTitle: "Watch History" },
    { items: homeData.libraryItems, sourceTitle: "Library" },
  ];

  return sources.find((source) => source.items.some((sourceItem) => sourceItem.Id === item.Id)) ?? null;
}

interface SpiritFlixBrowseRoute {
  libraryId: string | null;
  modelName: string | null;
  tag?: string | null;
}

const LIBRARY_UI_STATE_KEY = "spiritflix_library_ui_state";
const MANUAL_MODEL_CHANGED_EVENT = "spiritflix:manual-models-changed";
const HOME_CACHE_KEY = "spiritflix_home_cache_v1";
const HOME_CACHE_TTL_MS = 10 * 60 * 1000;
const LIVE_LIBRARY_LOAD_MIN_MS = 50;
const LIVE_LIBRARY_LOAD_TIMEOUT_MS = 12000;
const LIVE_LIBRARY_LOAD_DEDUPE_MS = 10 * 1000;
const PLAYBACK_REFRESH_INTERVAL_MS = 5 * 60 * 1000;
const PLAYBACK_FOCUS_REFRESH_THROTTLE_MS = 30 * 1000;
const BLOCKING_LOAD_STARTED_AT_KEY = "spiritflix_blocking_load_started_at";

const initialLoadProgress: SpiritFlixLoadProgress = { percent: 0, label: "Connecting to Jellyfin" };

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

function readCachedHomeData(): SpiritFlixHomeData | null {
  if (typeof window === "undefined") return null;
  try {
    const parsed = JSON.parse(window.sessionStorage.getItem(HOME_CACHE_KEY) ?? "null") as {
      at?: number;
      data?: SpiritFlixHomeData;
    } | null;
    if (!parsed?.data || !parsed.at || Date.now() - parsed.at > HOME_CACHE_TTL_MS) return null;
    return parsed.data;
  } catch {
    return null;
  }
}

function writeCachedHomeData(data: SpiritFlixHomeData): void {
  if (typeof window === "undefined") return;
  try {
    window.sessionStorage.setItem(HOME_CACHE_KEY, JSON.stringify({ at: Date.now(), data }));
  } catch {
    // sessionStorage can fail in private mode — non-fatal.
  }
}

function readBlockingLoadStartedAt(): number | null {
  if (typeof window === "undefined") return null;
  const startedAt = Number(window.sessionStorage.getItem(BLOCKING_LOAD_STARTED_AT_KEY));
  return Number.isFinite(startedAt) && startedAt > 0 ? startedAt : null;
}

function writeBlockingLoadStartedAt(startedAt: number): void {
  if (typeof window === "undefined") return;
  window.sessionStorage.setItem(BLOCKING_LOAD_STARTED_AT_KEY, String(startedAt));
}

function clearBlockingLoadStartedAt(): void {
  if (typeof window === "undefined") return;
  window.sessionStorage.removeItem(BLOCKING_LOAD_STARTED_AT_KEY);
}

function hasUsefulHomeContent(data: SpiritFlixHomeData): boolean {
  return Boolean(
    data.libraries.length ||
      data.libraryItems.length ||
      data.continueWatching.length ||
      data.latestAdded.length ||
      data.featuredItems.length,
  );
}

export function buildLiveLibraryLoadingHomeData(data: SpiritFlixHomeData, selectedLibraryId: string): SpiritFlixHomeData {
  return {
    ...emptyHome,
    libraries: data.libraries,
    playlists: data.playlists,
    selectedLibraryId,
  };
}

function applyManualModelRecordsToItems(
  items: JellyfinItem[],
  manualModelRecords: SpiritFlixManualModelRecord[],
): JellyfinItem[] {
  const modelByItemId = new Map<string, string>();
  manualModelRecords.forEach((record) => {
    if (record.itemId && record.modelName) modelByItemId.set(record.itemId, record.modelName);
  });
  return items.map((item) => {
    const manualModelName = modelByItemId.get(item.Id);
    return manualModelName ? { ...item, ManualModelName: manualModelName } : item;
  });
}

function applyManualModelRecordsToHomeData(
  homeData: SpiritFlixHomeData,
  manualModelRecords: SpiritFlixManualModelRecord[],
): SpiritFlixHomeData {
  return {
    ...homeData,
    libraryItems: applyManualModelRecordsToItems(homeData.libraryItems, manualModelRecords),
    featuredItems: applyManualModelRecordsToItems(homeData.featuredItems, manualModelRecords),
    continueWatching: applyManualModelRecordsToItems(homeData.continueWatching, manualModelRecords),
    watchHistory: applyManualModelRecordsToItems(homeData.watchHistory, manualModelRecords),
    latestAdded: applyManualModelRecordsToItems(homeData.latestAdded, manualModelRecords),
    favorites: applyManualModelRecordsToItems(homeData.favorites, manualModelRecords),
    modelCountItems: applyManualModelRecordsToItems(homeData.modelCountItems ?? [], manualModelRecords),
  };
}

export function applyManualModelNameToItem(item: JellyfinItem, itemId: string, modelName: string): JellyfinItem {
  return item.Id === itemId ? { ...item, ManualModelName: modelName } : item;
}

export function applyManualModelNameToHomeData(
  homeData: SpiritFlixHomeData,
  itemId: string,
  modelName: string,
): SpiritFlixHomeData {
  return {
    ...homeData,
    libraryItems: homeData.libraryItems.map((item) => applyManualModelNameToItem(item, itemId, modelName)),
    featuredItems: homeData.featuredItems.map((item) => applyManualModelNameToItem(item, itemId, modelName)),
    continueWatching: homeData.continueWatching.map((item) => applyManualModelNameToItem(item, itemId, modelName)),
    watchHistory: homeData.watchHistory.map((item) => applyManualModelNameToItem(item, itemId, modelName)),
    latestAdded: homeData.latestAdded.map((item) => applyManualModelNameToItem(item, itemId, modelName)),
    favorites: homeData.favorites.map((item) => applyManualModelNameToItem(item, itemId, modelName)),
    modelCountItems: (homeData.modelCountItems ?? []).map((item) => applyManualModelNameToItem(item, itemId, modelName)),
  };
}

export function applyManualModelNameToQueue(
  queue: SpiritFlixPlaybackQueue | null,
  itemId: string,
  modelName: string,
): SpiritFlixPlaybackQueue | null {
  if (!queue) return queue;
  return {
    ...queue,
    items: queue.items.map((item) => applyManualModelNameToItem(item, itemId, modelName)),
    originalItems: queue.originalItems?.map((item) => applyManualModelNameToItem(item, itemId, modelName)),
  };
}

function getStoredSpiritFlixBrowseRoute(): SpiritFlixBrowseRoute | null {
  if (typeof window === "undefined") return null;
  try {
    const parsed = JSON.parse(window.localStorage.getItem(LIBRARY_UI_STATE_KEY) ?? "{}") as {
      selectedLibraryId?: unknown;
      selectedModel?: unknown;
      selectedManualTag?: unknown;
    };
    const libraryId = typeof parsed.selectedLibraryId === "string" ? parsed.selectedLibraryId : null;
    return {
      libraryId,
      modelName: typeof parsed.selectedModel === "string" ? parsed.selectedModel : null,
      tag: typeof parsed.selectedManualTag === "string" ? parsed.selectedManualTag : null,
    };
  } catch {
    return null;
  }
}

function getSpiritFlixBrowseRoute(): SpiritFlixBrowseRoute {
  if (typeof window === "undefined") {
    return { libraryId: null, modelName: null, tag: null };
  }
  const query = new URLSearchParams(window.location.search);
  if (!query.has("library") && !query.has("model") && !query.has("tag")) {
    return getStoredSpiritFlixBrowseRoute() ?? { libraryId: null, modelName: null, tag: null };
  }
  return {
    libraryId: query.get("library"),
    modelName: query.get("model"),
    tag: query.get("tag"),
  };
}

export function buildSpiritFlixBrowsePath({ libraryId, modelName, tag }: SpiritFlixBrowseRoute): string {
  const query = new URLSearchParams();
  if (libraryId) query.set("library", libraryId);
  if (libraryId && modelName) query.set("model", modelName);
  if (libraryId && tag) query.set("tag", tag);
  const queryText = query.toString();
  return queryText ? `/spiritflix?${queryText}` : "/spiritflix";
}

function setSpiritFlixBrowseRoute(
  { libraryId, modelName, tag }: SpiritFlixBrowseRoute,
  mode: "push" | "replace" = "push",
) {
  if (typeof window === "undefined") return;
  const nextPath = buildSpiritFlixBrowsePath({ libraryId, modelName, tag });
  if (`${window.location.pathname}${window.location.search}` === nextPath) return;
  if (mode === "replace") {
    window.history.replaceState(window.history.state, "", nextPath);
    return;
  }
  window.history.pushState(window.history.state, "", nextPath);
}

export function SpiritFlixApp() {
  const [session, setSession] = useState<SpiritFlixSession | null>(null);
  const [isRestoringSession, setIsRestoringSession] = useState(true);
  const [serverUrl, setServerUrl] = useState(SPIRITFLIX_DEFAULT_SERVER);
  const [serverInfo, setServerInfo] = useState<SpiritFlixServerInfo | null>(null);
  const [serverError, setServerError] = useState("");
  const [homeData, setHomeData] = useState<SpiritFlixHomeData>(() => {
    const route = getSpiritFlixBrowseRoute();
    const cached = readCachedHomeData() ?? emptyHome;
    if (route.libraryId && cached.selectedLibraryId !== route.libraryId) {
      return { ...emptyHome, selectedLibraryId: route.libraryId };
    }
    return cached;
  });
  const [selectedItem, setSelectedItem] = useState<JellyfinItem | null>(null);
  const [playingItem, setPlayingItem] = useState<JellyfinItem | null>(null);
  const [playingQueue, setPlayingQueue] = useState<SpiritFlixPlaybackQueue | null>(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [loadingHome, setLoadingHome] = useState(false);
  const [homeError, setHomeError] = useState("");
  const [initialModelName, setInitialModelName] = useState<string | null>(null);
  const [initialManualTag, setInitialManualTag] = useState<string | null>(null);
  const [manualModelRecords, setManualModelRecords] = useState<SpiritFlixManualModelRecord[]>([]);
  const loadedSessionKeyRef = useRef<string | null>(null);
  const initialBrowseRouteRef = useRef<SpiritFlixBrowseRoute | null>(null);
  const deletedItemIdsRef = useRef<Set<string>>(new Set());
  const homeDataRef = useRef(homeData);
  const loadHomeAbortRef = useRef<AbortController | null>(null);
  const loadHomeSequenceRef = useRef(0);
  const loadCompletionPendingRef = useRef(false);
  const loadingHomeRef = useRef(false);
  const lastPlaybackRefreshAtRef = useRef(0);
  const activeHomeLoadKeyRef = useRef<string | null>(null);
  const lastVisibleHomeLoadRef = useRef<{ key: string; completedAt: number } | null>(null);
  const lastRouteSyncKeyRef = useRef<string | null>(null);
  const [loadProgress, setLoadProgress] = useState<SpiritFlixLoadProgress>(initialLoadProgress);
  const [loadingMore, setLoadingMore] = useState<Record<string, boolean>>({});
  const [liveLibraryLoadingId, setLiveLibraryLoadingId] = useState<string | null>(null);

  useEffect(() => {
    homeDataRef.current = homeData;
  }, [homeData]);

  useEffect(() => {
    loadingHomeRef.current = loadingHome;
  }, [loadingHome]);

  const client = useMemo(
    () => new JellyfinClient(session?.serverUrl ?? serverUrl, session?.accessToken, session?.userId),
    [serverUrl, session],
  );
  const modelAwareHomeData = useMemo(
    () => applyManualModelRecordsToHomeData(homeData, manualModelRecords),
    [homeData, manualModelRecords],
  );
  const visibleHomeData = liveLibraryLoadingId
    ? buildLiveLibraryLoadingHomeData(modelAwareHomeData, liveLibraryLoadingId)
    : modelAwareHomeData;

  const modelAwareLibraryItems = visibleHomeData.libraryItems;

  const loadManualModels = useCallback(async () => {
    if (!session) return;
    try {
      const response = await fetch("/api/spiritflix/model-index?includeItems=1", { cache: "no-store" });
      if (!response.ok) throw new Error("Manual models unavailable.");
      const body = (await response.json()) as { items?: SpiritFlixManualModelRecord[] };
      setManualModelRecords(body.items ?? []);
    } catch {
      setManualModelRecords([]);
    }
  }, [session]);

  const checkServer = useCallback(
    async (target = serverUrl) => {
      setServerError("");
      try {
        const info = await new JellyfinClient(target).checkPublicInfo();
        setServerInfo(info);
        setServerUrl(normalizeJellyfinServerUrl(target));
      } catch {
        setServerInfo(null);
        setServerError("SpiritFlix cannot reach that Jellyfin server from this browser right now.");
      }
    },
    [serverUrl],
  );

  const updateLoadProgress = useCallback((next: SpiritFlixLoadProgress) => {
    setLoadProgress((current) => (next.percent >= current.percent ? next : current));
  }, []);

  const finishBlockingLoad = useCallback(() => {
    loadCompletionPendingRef.current = false;
    clearBlockingLoadStartedAt();
    setLoadProgress({ percent: 100, label: "Ready" });
    setLoadingHome(false);
    setLiveLibraryLoadingId(null);
  }, []);

  const handleVisibleMetadataReady = useCallback(() => {
    if (!loadCompletionPendingRef.current) return;
    updateLoadProgress({ percent: 90, label: "Stage 4 of 5: Reading visible face metadata" });
  }, [updateLoadProgress]);

  useEffect(() => {
    if (!loadingHome) return undefined;
    const now = Date.now();
    const startedAt = readBlockingLoadStartedAt() ?? now;
    writeBlockingLoadStartedAt(startedAt);
    const remainingMs = Math.max(0, LIVE_LIBRARY_LOAD_TIMEOUT_MS - (now - startedAt));
    const timeout = window.setTimeout(() => {
      loadHomeAbortRef.current?.abort();
      loadCompletionPendingRef.current = false;
      clearBlockingLoadStartedAt();
      setLoadProgress({ percent: 100, label: "Load failed" });
      setHomeError("Jellyfin request timed out while loading library data.");
      setLoadingHome(false);
      setLiveLibraryLoadingId(null);
    }, remainingMs);
    return () => window.clearTimeout(timeout);
  }, [loadingHome]);

  const loadHome = useCallback(
    async (libraryId?: string | null, term = searchTerm, options: { silent?: boolean; reuseLibraries?: boolean } = {}) => {
      if (!session) return;
      const requestedLibraryIdBeforeLookup = libraryId === undefined ? homeDataRef.current.selectedLibraryId : libraryId;
      const loadKey = `${requestedLibraryIdBeforeLookup ?? "home"}:${term}`;
      const previousVisibleLoad = lastVisibleHomeLoadRef.current;
      if (activeHomeLoadKeyRef.current === loadKey) return;
      if (!options.silent && previousVisibleLoad?.key === loadKey && Date.now() - previousVisibleLoad.completedAt < LIVE_LIBRARY_LOAD_DEDUPE_MS) return;
      const loadId = loadHomeSequenceRef.current + 1;
      loadHomeSequenceRef.current = loadId;
      loadHomeAbortRef.current?.abort();
      const controller = new AbortController();
      loadHomeAbortRef.current = controller;
      const pageSizes = getInitialPageSizes();
      const isStale = () => controller.signal.aborted || loadHomeSequenceRef.current !== loadId;
      activeHomeLoadKeyRef.current = loadKey;
      const shouldGateLiveLibrary = !options.silent && typeof requestedLibraryIdBeforeLookup === "string" && requestedLibraryIdBeforeLookup.length > 0;
      const startedAt = performance.now();
      const showBlockingLoader = !options.silent && (shouldGateLiveLibrary || !hasUsefulHomeContent(homeDataRef.current));
      loadCompletionPendingRef.current = false;
      if (shouldGateLiveLibrary) setLiveLibraryLoadingId(requestedLibraryIdBeforeLookup);
      if (showBlockingLoader) {
        const now = Date.now();
        const blockingStartedAt = readBlockingLoadStartedAt() ?? now;
        if (now - blockingStartedAt >= LIVE_LIBRARY_LOAD_TIMEOUT_MS) {
          clearBlockingLoadStartedAt();
          loadCompletionPendingRef.current = false;
          setLoadProgress({ percent: 100, label: "Load failed" });
          setHomeError("Jellyfin request timed out while loading library data.");
          setLoadingHome(false);
          setLiveLibraryLoadingId(null);
          controller.abort();
          if (activeHomeLoadKeyRef.current === loadKey) activeHomeLoadKeyRef.current = null;
          return;
        }
        writeBlockingLoadStartedAt(blockingStartedAt);
        setLoadProgress({ percent: 5, label: "Connecting to Jellyfin" });
        setLoadingHome(true);
      }
      setHomeError("");
      let loadFailed = false;
      let blockingLoadTimeout: number | null = null;
      if (showBlockingLoader) {
        blockingLoadTimeout = window.setTimeout(() => {
          if (loadHomeSequenceRef.current !== loadId) return;
          loadFailed = true;
          loadCompletionPendingRef.current = false;
          setLoadProgress({ percent: 100, label: "Load failed" });
          setHomeError("Jellyfin request timed out while loading library data.");
          setLoadingHome(false);
          setLiveLibraryLoadingId(null);
          controller.abort();
        }, LIVE_LIBRARY_LOAD_TIMEOUT_MS);
      }
      try {
        const reusableLibraries = options.reuseLibraries ? homeDataRef.current.libraries.filter(isMediaLibrary) : [];
        const libraries = reusableLibraries.length ? reusableLibraries : (await client.getLibraries()).filter(isMediaLibrary);
        if (isStale()) return;
        if (showBlockingLoader) updateLoadProgress({ percent: 18, label: "Stage 1 of 5: Finding libraries" });
        const otherLibrary = libraries.find((library) => library.Name.toLowerCase() === OTHER_LIBRARY_NAME.toLowerCase());
        const requestedLibraryId = libraryId === undefined ? homeData.selectedLibraryId : libraryId;
        const selectedLibraryId = requestedLibraryId && libraries.some((library) => library.Id === requestedLibraryId)
          ? requestedLibraryId
          : requestedLibraryId === null
            ? null
            : otherLibrary?.Id ?? libraries[0]?.Id ?? null;
        const animeLibrary = libraries.find((library) => library.Name.toLowerCase() === "anime");
        const selectedLibrary = libraries.find((library) => library.Id === selectedLibraryId);
        const shouldBlockForModelCounts = Boolean(
          showBlockingLoader &&
            selectedLibraryId &&
            selectedLibrary?.Name.toLowerCase() !== "anime",
        );
        const isNotDeleted = (item: JellyfinItem) => !deletedItemIdsRef.current.has(item.Id) && isVisibleSpiritFlixItem(item);

        const libraryPagePromise = selectedLibraryId
          ? client.getLibraryItemsPage(selectedLibraryId, {
              searchTerm: term,
              limit: pageSizes.library,
              fields: "card",
              signal: controller.signal,
            })
          : Promise.resolve(emptyJellyfinPage(pageSizes.library));
        const featuredPagePromise = !selectedLibraryId && animeLibrary
          ? client.getLibraryItemsPage(animeLibrary.Id, {
              limit: pageSizes.shelf,
              fields: "card",
              signal: controller.signal,
            })
          : Promise.resolve(emptyJellyfinPage(pageSizes.shelf));
        const continuePagePromise = selectedLibraryId
          ? client.getLibraryResumeItemsPage(selectedLibraryId, {
              limit: pageSizes.shelf,
              fields: "card",
              signal: controller.signal,
            })
          : client.getContinueWatchingPage(undefined, {
              limit: pageSizes.shelf,
              fields: "card",
              signal: controller.signal,
            });
        const watchHistoryPagePromise = client.getWatchHistoryPage(selectedLibraryId ?? undefined, {
          limit: pageSizes.history,
          fields: "card",
          signal: controller.signal,
        });
        const latestPagePromise = selectedLibraryId
          ? client.getLibraryLatestAddedPage(selectedLibraryId, {
              limit: pageSizes.shelf,
              fields: "card",
              signal: controller.signal,
            })
          : client.getLatestAddedPage({
              limit: pageSizes.shelf,
              fields: "card",
              signal: controller.signal,
            });
        const favoritesPagePromise = selectedLibraryId
          ? client.getLibraryFavoriteItemsPage(selectedLibraryId, {
              limit: pageSizes.shelf,
              fields: "card",
              signal: controller.signal,
            })
          : client.getFavoritesPage({
              limit: pageSizes.shelf,
              fields: "card",
              signal: controller.signal,
            });

        const libraryPage = await libraryPagePromise;
        if (isStale()) return;
        const libraryItemsUnique = uniqueItems(libraryPage.items.filter(isNotDeleted));
        const partialHome: SpiritFlixHomeData = {
          ...homeDataRef.current,
          libraries,
          playlists: [],
          selectedLibraryId,
          libraryItems: libraryItemsUnique,
          libraryPaging: pagingFromPage(libraryPage),
        };
        setHomeData(partialHome);
        if (showBlockingLoader) {
          updateLoadProgress({ percent: 48, label: "Stage 2 of 5: Painting visible grid" });
        }

        const [featuredPage, continuePage, watchHistoryPage, latestPage, favoritesPage] = await Promise.all([
          featuredPagePromise,
          continuePagePromise,
          watchHistoryPagePromise,
          latestPagePromise,
          favoritesPagePromise,
        ]);
        if (isStale()) return;
        let latestAddedItems = uniqueItems(latestPage.items.filter(isNotDeleted));
        const selectedLibraryName = selectedLibrary?.Name.toLowerCase() ?? "";
        const selectedLibraryUsesGlobalLatest =
          selectedLibraryName === "home videos and photos" ||
          selectedLibraryName === "home videos" ||
          selectedLibrary?.CollectionType?.toLowerCase() === "homevideos";
        if (selectedLibraryUsesGlobalLatest && !latestAddedItems.length) {
          const fallbackLatestPage = await client.getLatestAddedPage({
            limit: pageSizes.shelf,
            fields: "card",
            signal: controller.signal,
          });
          if (isStale()) return;
          latestAddedItems = uniqueItems(fallbackLatestPage.items.filter(isNotDeleted));
          if (!latestAddedItems.length) latestAddedItems = homeDataRef.current.latestAdded;
        }
        const watchHistoryItems = sortByLastPlayed(uniqueItems(watchHistoryPage.items.filter(isNotDeleted).filter(hasWatchActivity)));
        const continueWatchingItems = mergeContinueWatchingItems({
          continueWatching: continuePage.items,
          watchHistory: watchHistoryItems,
          libraryItems: libraryItemsUnique,
          isNotDeleted,
        });
        const nextHome: SpiritFlixHomeData = {
          libraries,
          playlists: [],
          selectedLibraryId,
          featuredItems: uniqueItems(featuredPage.items.filter(isNotDeleted).filter((item) => isPlayableItem(item) && isSeriesPlaybackItem(item)).sort(byEpisodeOrder)),
          libraryItems: libraryItemsUnique,
          libraryPaging: pagingFromPage(libraryPage),
          continueWatching: continueWatchingItems,
          watchHistory: watchHistoryItems,
          latestAdded: latestAddedItems,
          favorites: uniqueItems(favoritesPage.items.filter(isNotDeleted)),
          continueWatchingPaging: pagingFromPage(continuePage),
          watchHistoryPaging: pagingFromPage(watchHistoryPage),
          latestAddedPaging: pagingFromPage(latestPage),
          favoritesPaging: pagingFromPage(favoritesPage),
        };
        setHomeData(nextHome);
        writeCachedHomeData(nextHome);
        if (showBlockingLoader) updateLoadProgress({ percent: 76, label: "Stage 3 of 5: Loading shelves" });

        if (shouldBlockForModelCounts && selectedLibraryId) {
          updateLoadProgress({ percent: 94, label: "Stage 5 of 5: Counting models" });
          let modelCountItems = libraryItemsUnique;
          try {
            const allLibraryItems = await client.getAllLibraryItems(selectedLibraryId, {
              searchTerm: term,
              fields: "card",
              pageSize: 500,
              maxItems: 5000,
              signal: controller.signal,
            });
            if (isStale()) return;
            const allVisibleItems = uniqueItems(allLibraryItems.filter(isNotDeleted));
            if (allVisibleItems.length) modelCountItems = allVisibleItems;
          } catch (error) {
            if (controller.signal.aborted || (error instanceof DOMException && error.name === "AbortError")) return;
          }
          const modelReadyHome: SpiritFlixHomeData = {
            ...nextHome,
            modelCountItems,
          };
          setHomeData(modelReadyHome);
          writeCachedHomeData(modelReadyHome);
        }
      } catch (error) {
        if (controller.signal.aborted || (error instanceof DOMException && error.name === "AbortError")) return;
        loadFailed = true;
        loadCompletionPendingRef.current = false;
        clearBlockingLoadStartedAt();
        setLoadProgress({ percent: 100, label: "Load failed" });
        const errorMessage = error instanceof Error ? error.message : "";
        setHomeError(
          /timed out|proxy|server returned/i.test(errorMessage)
            ? errorMessage
            : "Could not load your Jellyfin library. Log out and back in if the token expired.",
        );
      } finally {
        if (blockingLoadTimeout !== null) window.clearTimeout(blockingLoadTimeout);
        if (!options.silent && !controller.signal.aborted) {
          const remainingMinLoadMs = shouldGateLiveLibrary ? Math.max(0, LIVE_LIBRARY_LOAD_MIN_MS - (performance.now() - startedAt)) : 0;
          if (remainingMinLoadMs > 0) await sleep(remainingMinLoadMs);
          if (!loadFailed && !isStale() && !loadCompletionPendingRef.current) {
            finishBlockingLoad();
          }
          if (!loadFailed && !isStale()) {
            lastVisibleHomeLoadRef.current = { key: loadKey, completedAt: Date.now() };
          }
        }
        if (activeHomeLoadKeyRef.current === loadKey) activeHomeLoadKeyRef.current = null;
      }
    },
    [client, finishBlockingLoad, homeData.selectedLibraryId, searchTerm, session, updateLoadProgress],
  );

  const setLoadingMoreKey = useCallback((key: string, value: boolean) => {
    setLoadingMore((current) => ({ ...current, [key]: value }));
  }, []);

  const loadMoreLibraryItems = useCallback(async () => {
    if (!session) return;
    const current = homeDataRef.current;
    const paging = current.libraryPaging;
    if (!current.selectedLibraryId || !paging?.hasMore || loadingMore.library) return;
    setLoadingMoreKey("library", true);
    try {
      const page = await client.getLibraryItemsPage(current.selectedLibraryId, {
        searchTerm,
        startIndex: paging.loaded,
        limit: paging.pageSize || getInitialPageSizes().library,
        fields: "card",
      });
      const isNotDeleted = (item: JellyfinItem) => !deletedItemIdsRef.current.has(item.Id) && isVisibleSpiritFlixItem(item);
      setHomeData((existing) => ({
        ...existing,
        libraryItems: appendUniqueItems(existing.libraryItems, page.items.filter(isNotDeleted)),
        libraryPaging: pagingFromPage(page),
      }));
    } finally {
      setLoadingMoreKey("library", false);
    }
  }, [client, loadingMore.library, searchTerm, session, setLoadingMoreKey]);

  const loadMoreLatestAdded = useCallback(async () => {
    if (!session) return;
    const current = homeDataRef.current;
    const paging = current.latestAddedPaging;
    if (!paging?.hasMore || loadingMore.latestAdded) return;
    setLoadingMoreKey("latestAdded", true);
    try {
      const options = {
        startIndex: paging.loaded,
        limit: paging.pageSize || getInitialPageSizes().shelf,
        fields: "card" as const,
      };
      const page = current.selectedLibraryId
        ? await client.getLibraryLatestAddedPage(current.selectedLibraryId, options)
        : await client.getLatestAddedPage(options);
      const isNotDeleted = (item: JellyfinItem) => !deletedItemIdsRef.current.has(item.Id) && isVisibleSpiritFlixItem(item);
      setHomeData((existing) => ({
        ...existing,
        latestAdded: appendUniqueItems(existing.latestAdded, page.items.filter(isNotDeleted)),
        latestAddedPaging: pagingFromPage(page),
      }));
    } finally {
      setLoadingMoreKey("latestAdded", false);
    }
  }, [client, loadingMore.latestAdded, session, setLoadingMoreKey]);

  const loadMoreFavorites = useCallback(async () => {
    if (!session) return;
    const current = homeDataRef.current;
    const paging = current.favoritesPaging;
    if (!paging?.hasMore || loadingMore.favorites) return;
    setLoadingMoreKey("favorites", true);
    try {
      const options = {
        startIndex: paging.loaded,
        limit: paging.pageSize || getInitialPageSizes().shelf,
        fields: "card" as const,
      };
      const page = current.selectedLibraryId
        ? await client.getLibraryFavoriteItemsPage(current.selectedLibraryId, options)
        : await client.getFavoritesPage(options);
      const isNotDeleted = (item: JellyfinItem) => !deletedItemIdsRef.current.has(item.Id) && isVisibleSpiritFlixItem(item);
      setHomeData((existing) => ({
        ...existing,
        favorites: appendUniqueItems(existing.favorites, page.items.filter(isNotDeleted)),
        favoritesPaging: pagingFromPage(page),
      }));
    } finally {
      setLoadingMoreKey("favorites", false);
    }
  }, [client, loadingMore.favorites, session, setLoadingMoreKey]);

  const loadMoreContinueWatching = useCallback(async () => {
    if (!session) return;
    const current = homeDataRef.current;
    const resumePaging = current.continueWatchingPaging;
    const historyPaging = current.watchHistoryPaging;
    if (!resumePaging?.hasMore && !historyPaging?.hasMore) return;
    if (loadingMore.continueWatching) return;
    setLoadingMoreKey("continueWatching", true);
    try {
      const resumePage = resumePaging?.hasMore
        ? current.selectedLibraryId
          ? await client.getLibraryResumeItemsPage(current.selectedLibraryId, {
              startIndex: resumePaging.loaded,
              limit: resumePaging.pageSize || getInitialPageSizes().shelf,
              fields: "card",
            })
          : await client.getContinueWatchingPage(undefined, {
              startIndex: resumePaging.loaded,
              limit: resumePaging.pageSize || getInitialPageSizes().shelf,
              fields: "card",
            })
        : emptyJellyfinPage(resumePaging?.pageSize ?? getInitialPageSizes().shelf);
      const historyPage = historyPaging?.hasMore
        ? await client.getWatchHistoryPage(current.selectedLibraryId ?? undefined, {
            startIndex: historyPaging.loaded,
            limit: historyPaging.pageSize || getInitialPageSizes().history,
            fields: "card",
          })
        : emptyJellyfinPage(historyPaging?.pageSize ?? getInitialPageSizes().history);
      const isNotDeleted = (item: JellyfinItem) => !deletedItemIdsRef.current.has(item.Id) && isVisibleSpiritFlixItem(item);
      setHomeData((existing) => {
        const watchHistory = sortByLastPlayed(
          appendUniqueItems(existing.watchHistory, historyPage.items.filter(isNotDeleted)).filter(hasWatchActivity),
        );
        const resumeSource = appendUniqueItems(existing.continueWatching, resumePage.items.filter(isNotDeleted));
        return {
          ...existing,
          watchHistory,
          continueWatching: mergeContinueWatchingItems({
            continueWatching: resumeSource,
            watchHistory,
            libraryItems: existing.libraryItems,
            isNotDeleted,
          }),
          continueWatchingPaging: resumePaging?.hasMore ? pagingFromPage(resumePage) : existing.continueWatchingPaging,
          watchHistoryPaging: historyPaging?.hasMore ? pagingFromPage(historyPage) : existing.watchHistoryPaging,
        };
      });
    } finally {
      setLoadingMoreKey("continueWatching", false);
    }
  }, [client, loadingMore.continueWatching, session, setLoadingMoreKey]);

  useEffect(() => {
    const initialRoute = getSpiritFlixBrowseRoute();
    initialBrowseRouteRef.current = initialRoute;
    setInitialModelName(initialRoute.modelName);
    setInitialManualTag(initialRoute.tag ?? null);
    if (window.location.pathname.startsWith("/spiritflix/watch/")) {
      setSpiritFlixBrowseRoute(initialRoute, "replace");
    }
    const stored = getStoredSession();
    if (stored) {
      setSession(stored);
      setServerUrl(stored.serverUrl);
    }
    setIsRestoringSession(false);
  }, []);

  useEffect(() => {
    if (isRestoringSession) return undefined;
    void checkServer(serverUrl);
    return undefined;
  }, [checkServer, isRestoringSession, serverUrl]);

  useEffect(() => {
    if (!session) {
      loadedSessionKeyRef.current = null;
      lastRouteSyncKeyRef.current = null;
      return undefined;
    }
    const sessionKey = `${session.serverUrl}:${session.userId}:${session.accessToken}`;
    if (loadedSessionKeyRef.current === sessionKey) return undefined;
    loadedSessionKeyRef.current = sessionKey;
    void loadHome(initialBrowseRouteRef.current?.libraryId ?? null);
    void loadManualModels();
    return undefined;
  }, [loadHome, loadManualModels, session]);

  useEffect(() => {
    if (!session || loadingHome) return undefined;
    const route = getSpiritFlixBrowseRoute();
    if (!route.libraryId) return undefined;
    if (route.libraryId === homeData.selectedLibraryId) {
      lastRouteSyncKeyRef.current = `${route.libraryId}:${searchTerm}`;
      return undefined;
    }
    const syncKey = `${route.libraryId}:${searchTerm}`;
    void loadHome(route.libraryId, searchTerm);
    const retry = window.setTimeout(() => {
      if (homeDataRef.current.selectedLibraryId !== route.libraryId) {
        void loadHome(route.libraryId, searchTerm);
      }
    }, 1000);
    const finalRetry = window.setTimeout(() => {
      if (homeDataRef.current.selectedLibraryId !== route.libraryId) {
        lastRouteSyncKeyRef.current = null;
        void loadHome(route.libraryId, searchTerm);
      }
    }, 2500);
    if (lastRouteSyncKeyRef.current === syncKey) return () => {
      window.clearTimeout(retry);
      window.clearTimeout(finalRetry);
    };
    lastRouteSyncKeyRef.current = syncKey;
    return () => {
      window.clearTimeout(retry);
      window.clearTimeout(finalRetry);
    };
  }, [homeData.selectedLibraryId, loadHome, loadingHome, searchTerm, session]);

  useEffect(() => {
    if (!session) return undefined;
    const handleManualModelsChanged = (event: Event) => {
      const detail = (event as CustomEvent<{ itemId?: unknown; modelName?: unknown }>).detail;
      if (typeof detail?.itemId === "string" && typeof detail.modelName === "string") {
        const itemId = detail.itemId;
        const modelName = detail.modelName;
        setSelectedItem((current) => (current ? applyManualModelNameToItem(current, itemId, modelName) : current));
        setPlayingItem((current) => (current ? applyManualModelNameToItem(current, itemId, modelName) : current));
        setPlayingQueue((current) => applyManualModelNameToQueue(current, itemId, modelName));
        setHomeData((current) => applyManualModelNameToHomeData(current, itemId, modelName));
        setManualModelRecords((current) => {
          const nextRecord: SpiritFlixManualModelRecord = {
            schema: "spiritflix-manual-model/v1",
            itemId,
            modelName,
            updatedAt: new Date().toISOString(),
            source: "manual",
          };
          return [nextRecord, ...current.filter((record) => record.itemId !== itemId)];
        });
      }
      void loadManualModels();
    };
    window.addEventListener(MANUAL_MODEL_CHANGED_EVENT, handleManualModelsChanged);
    return () => window.removeEventListener(MANUAL_MODEL_CHANGED_EVENT, handleManualModelsChanged);
  }, [loadManualModels, session]);

  useEffect(() => {
    if (!session) return undefined;
    const refreshPlaybackState = (source: "interval" | "visibility" | "focus") => {
      if (loadingHomeRef.current || !hasUsefulHomeContent(homeDataRef.current)) return;
      if (source !== "interval") {
        const now = Date.now();
        if (now - lastPlaybackRefreshAtRef.current < PLAYBACK_FOCUS_REFRESH_THROTTLE_MS) return;
        lastPlaybackRefreshAtRef.current = now;
      }
      void loadHome(homeData.selectedLibraryId, searchTerm, { silent: true, reuseLibraries: true });
    };
    const handleVisibilityChange = () => {
      if (document.visibilityState === "visible") refreshPlaybackState("visibility");
    };
    const timer = window.setInterval(() => refreshPlaybackState("interval"), PLAYBACK_REFRESH_INTERVAL_MS);
    const handleFocus = () => refreshPlaybackState("focus");
    window.addEventListener("focus", handleFocus);
    document.addEventListener("visibilitychange", handleVisibilityChange);
    return () => {
      window.clearInterval(timer);
      window.removeEventListener("focus", handleFocus);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [homeData.selectedLibraryId, loadHome, searchTerm, session]);

  const handleLogin = async (username: string, password: string, targetServerUrl: string) => {
    const authClient = new JellyfinClient(targetServerUrl);
    const nextSession = await authClient.login(username, password);
    storeSession(nextSession);
    setSession(nextSession);
    setServerUrl(nextSession.serverUrl);
    await checkServer(nextSession.serverUrl);
  };

  const handleLogout = () => {
    setSpiritFlixBrowseRoute({ libraryId: null, modelName: null, tag: null }, "replace");
    clearStoredSession();
    loadedSessionKeyRef.current = null;
    setSession(null);
    setHomeData(emptyHome);
    setSelectedItem(null);
    setPlayingItem(null);
    setPlayingQueue(null);
  };

  const buildQueue = (
    item: JellyfinItem,
    items: JellyfinItem[] = [item],
    sourceTitle = "Direct play",
    startPositionTicks?: number,
  ) => {
    const playableItems = uniqueItems(items.filter(isPlayableItem));
    const queueItems = playableItems.some((queueItem) => queueItem.Id === item.Id) ? playableItems : [item, ...playableItems];
    return {
      items: queueItems,
      originalItems: queueItems,
      currentIndex: Math.max(0, queueItems.findIndex((queueItem) => queueItem.Id === item.Id)),
      sourceTitle,
      startPositionTicks,
      isShuffled: /\bshuffle\b/i.test(sourceTitle),
    };
  };

  const handlePlay = (item: JellyfinItem, queueItems?: JellyfinItem[], sourceTitle?: string, startPositionTicks?: number) => {
    if (isPlayableItem(item)) {
      void client.getMobileOptimizedSource(item).catch(() => undefined);
      const preserveProvidedQueue = Boolean(queueItems?.length && sourceTitle && /\bshuffle\b/i.test(sourceTitle));
      const seriesQueue = preserveProvidedQueue
        ? []
        : getSeriesPlaybackQueue(item, [
            ...(queueItems ?? []),
            ...homeData.libraryItems,
            ...homeData.featuredItems,
            ...homeData.latestAdded,
            ...homeData.continueWatching,
            ...homeData.watchHistory,
          ]);
      const resolvedQueueItems = seriesQueue.length ? seriesQueue : queueItems;
      const resolvedSourceTitle = seriesQueue.length ? sourceTitle ?? item.SeriesName ?? "Series" : sourceTitle;
      setPlayingItem(item);
      setPlayingQueue(buildQueue(item, resolvedQueueItems, resolvedSourceTitle, startPositionTicks));
    }
  };

  const handlePlayModelShuffle = useCallback((currentItem: JellyfinItem, modelName: string, modelItems: JellyfinItem[]) => {
    const playableModelItems = uniqueItems(modelItems.filter(isPlayableItem));
    if (!playableModelItems.length) return;
    const anchorItem = playableModelItems.find((candidate) => candidate.Id === currentItem.Id) ?? playableModelItems[0];
    if (!anchorItem) return;
    const shuffledItems = shuffleQueueAfterCurrent(playableModelItems, anchorItem.Id);
    setPlayingItem(anchorItem);
    setPlayingQueue({
      items: shuffledItems,
      originalItems: playableModelItems,
      currentIndex: Math.max(0, shuffledItems.findIndex((candidate) => candidate.Id === anchorItem.Id)),
      sourceTitle: `${modelName} Shuffle`,
      isShuffled: true,
    });
  }, []);

  const handleQueueSelect = (item: JellyfinItem) => {
    setPlayingItem(item);
    setPlayingQueue((current) => {
      if (!current) return buildQueue(item);
      const currentIndex = current.items.findIndex((queueItem) => queueItem.Id === item.Id);
      return {
        ...current,
        currentIndex: currentIndex >= 0 ? currentIndex : current.currentIndex,
      };
    });
  };

  const handleShuffleQueue = useCallback((currentItemId: string, orientation?: SpiritFlixVideoOrientation) => {
    setPlayingQueue((current) => {
      if (!current) return current;
      const originalItems = current.originalItems?.length ? current.originalItems : current.items;
      const shuffleSource = orientation ? filterItemsByVideoOrientation(originalItems, orientation) : originalItems;
      if (shuffleSource.length < 2) return current;
      const anchorItem = shuffleSource.find((queueItem) => queueItem.Id === currentItemId) ?? shuffleSource[0];
      if (!anchorItem) return current;
      const items = orientation
        ? shuffleQueueAfterCurrent(shuffleSource, anchorItem.Id)
        : current.isShuffled
          ? originalItems
          : shuffleQueueAfterCurrent(originalItems, currentItemId);
      if (orientation && anchorItem.Id !== currentItemId) {
        setPlayingItem(anchorItem);
      }
      return {
        ...current,
        originalItems,
        items,
        currentIndex: Math.max(0, items.findIndex((queueItem) => queueItem.Id === anchorItem.Id)),
        sourceTitle: orientation ? `${current.sourceTitle} / ${getOrientationFilterLabel(orientation)}` : current.sourceTitle,
        isShuffled: orientation ? true : !current.isShuffled,
      };
    });
  }, []);

  const handleReorderQueue = useCallback((activeItemId: string, overItemId: string) => {
    setPlayingQueue((current) => {
      if (!current || current.items.length < 2) return current;
      const items = reorderQueueItems(current.items, activeItemId, overItemId);
      if (items === current.items) return current;
      return {
        ...current,
        items,
        originalItems: items,
        currentIndex: Math.max(0, items.findIndex((queueItem) => queueItem.Id === playingItem?.Id)),
        isShuffled: false,
      };
    });
  }, [playingItem?.Id]);

  const handlePlayerDelete = useCallback(
    (deletedItem: JellyfinItem, requestedNextItem: JellyfinItem | null) => {
      deletedItemIdsRef.current.add(deletedItem.Id);
      setSelectedItem((current) => (current?.Id === deletedItem.Id ? null : current));
      setHomeData((current) => removeDeletedItemFromHomeData(current, deletedItem.Id));
      const nextQueueState = playingQueue
        ? removeDeletedItemFromQueue(playingQueue, deletedItem.Id, requestedNextItem)
        : { queue: null, nextItem: null };
      const nextItem = nextQueueState.nextItem;
      setPlayingItem(nextItem);
      setPlayingQueue(nextQueueState.queue);
      void loadHome(homeData.selectedLibraryId, searchTerm, { silent: true, reuseLibraries: true });
    },
    [homeData.selectedLibraryId, loadHome, playingQueue, searchTerm],
  );

  const handlePlaybackProgress = useCallback(
    (progress: SpiritFlixPlaybackProgress) => {
      setSelectedItem((current) => (current?.Id === progress.itemId ? applyPlaybackProgress(current, progress) : current));

      setHomeData((current) => {
        let updatedItem: JellyfinItem | null = progress.item ? applyPlaybackProgress(progress.item, progress) : null;
        const nextLibraryItems = current.libraryItems.map((item) => {
          const nextItem = applyPlaybackProgress(item, progress);
          if (nextItem.Id === progress.itemId) updatedItem = nextItem;
          return nextItem;
        });
        const nextFeaturedItems = current.featuredItems.map((item) => applyPlaybackProgress(item, progress));
        const nextLatestAdded = current.latestAdded.map((item) => applyPlaybackProgress(item, progress));
        const nextFavorites = current.favorites.map((item) => applyPlaybackProgress(item, progress));
        const nextWatchHistory = current.watchHistory.map((item) => {
          const nextItem = applyPlaybackProgress(item, progress);
          if (nextItem.Id === progress.itemId) updatedItem = nextItem;
          return nextItem;
        });
        const nextContinueWatching = current.continueWatching.map((item) => {
          const nextItem = applyPlaybackProgress(item, progress);
          if (nextItem.Id === progress.itemId) updatedItem = nextItem;
          return nextItem;
        });
        const sourceItem = updatedItem ?? [...current.libraryItems, ...current.continueWatching, ...current.featuredItems, ...current.latestAdded, ...current.favorites].find(
          (item): item is JellyfinItem => Boolean(item && item.Id === progress.itemId),
        );
        const nextSourceItem = sourceItem ? applyPlaybackProgress(sourceItem, progress) : null;
        return {
          ...current,
          libraryItems: nextLibraryItems,
          featuredItems: nextFeaturedItems,
          latestAdded: nextLatestAdded,
          favorites: nextFavorites,
          watchHistory: nextSourceItem
            ? upsertWatchHistoryItem(nextWatchHistory, nextSourceItem)
            : nextWatchHistory,
          continueWatching: nextSourceItem
            ? upsertPlaybackItem(nextContinueWatching, nextSourceItem)
            : nextContinueWatching.filter((item) => item.Id !== progress.itemId),
        };
      });
    },
    [],
  );

  const handleToggleFavorite = useCallback(
    (item: JellyfinItem, isFavorite: boolean) => {
      const nextItem = applyFavoriteState(item, item.Id, isFavorite);
      setSelectedItem((current) => (current?.Id === item.Id ? applyFavoriteState(current, item.Id, isFavorite) : current));
      setPlayingItem((current) => (current?.Id === item.Id ? applyFavoriteState(current, item.Id, isFavorite) : current));
      setPlayingQueue((current) =>
        current
          ? {
              ...current,
              items: current.items.map((queueItem) => applyFavoriteState(queueItem, item.Id, isFavorite)),
            }
          : current,
      );
      setHomeData((current) => ({
        ...current,
        libraryItems: current.libraryItems.map((libraryItem) => applyFavoriteState(libraryItem, item.Id, isFavorite)),
        featuredItems: current.featuredItems.map((featuredItem) => applyFavoriteState(featuredItem, item.Id, isFavorite)),
        continueWatching: current.continueWatching.map((resumeItem) => applyFavoriteState(resumeItem, item.Id, isFavorite)),
        watchHistory: current.watchHistory.map((historyItem) => applyFavoriteState(historyItem, item.Id, isFavorite)),
        latestAdded: current.latestAdded.map((latestItem) => applyFavoriteState(latestItem, item.Id, isFavorite)),
        favorites: upsertFavoriteItem(
          current.favorites.map((favoriteItem) => applyFavoriteState(favoriteItem, item.Id, isFavorite)),
          nextItem,
        ),
      }));

      void client.setFavorite(item.Id, isFavorite).catch(() => {
        void loadHome(homeData.selectedLibraryId);
      });
    },
    [client, homeData.selectedLibraryId, loadHome],
  );

  const handleOpenDetails = (item: JellyfinItem) => {
    setSelectedItem(item);
  };

  const handleDetailsPlay = (item: JellyfinItem) => {
    const inferredQueue = inferPlaybackQueueForItem(item, homeData);
    setSelectedItem(null);
    handlePlay(
      item,
      inferredQueue?.items,
      inferredQueue?.sourceTitle,
      item.UserData?.PlaybackPositionTicks,
    );
  };

  const handleSearch = (term: string) => {
    setSearchTerm(term);
    void loadHome(homeData.selectedLibraryId, term);
  };

  const handleSelectHome = () => {
    initialBrowseRouteRef.current = { libraryId: null, modelName: null, tag: null };
    setInitialModelName(null);
    setInitialManualTag(null);
    setSpiritFlixBrowseRoute({ libraryId: null, modelName: null, tag: null });
    void loadHome(null);
  };

  const handleSelectLibrary = (libraryId: string) => {
    initialBrowseRouteRef.current = { libraryId, modelName: null, tag: null };
    setInitialModelName(null);
    setInitialManualTag(null);
    setSpiritFlixBrowseRoute({ libraryId, modelName: null, tag: null });
    void loadHome(libraryId);
  };

  const handleSelectModel = (modelName: string | null) => {
    const libraryId = homeData.selectedLibraryId;
    if (!libraryId) return;
    initialBrowseRouteRef.current = { libraryId, modelName, tag: null };
    setInitialModelName(modelName);
    setInitialManualTag(null);
    setSpiritFlixBrowseRoute({ libraryId, modelName, tag: null });
  };

  return (
    <main className="spiritflix-shell">
      {isRestoringSession ? (
        <SpiritFlixSplash progress={initialLoadProgress} skeleton />
      ) : !session ? (
        <SpiritFlixLogin
          serverUrl={serverUrl}
          serverInfo={serverInfo}
          serverError={serverError}
          onServerUrlChange={setServerUrl}
          onRetry={() => checkServer(serverUrl)}
          onLogin={handleLogin}
        />
      ) : (
        <SpiritFlixHome
          client={client}
          data={visibleHomeData}
          loading={loadingHome}
          loadProgress={loadProgress}
          error={homeError}
          session={session}
          searchTerm={searchTerm}
          serverInfo={serverInfo}
          onLogout={handleLogout}
          onRefresh={() => loadHome(homeData.selectedLibraryId)}
          onSearch={handleSearch}
          onSelectHome={handleSelectHome}
          onSelectLibrary={handleSelectLibrary}
          loadingMore={loadingMore}
          onLoadMoreLibrary={loadMoreLibraryItems}
          onLoadMoreContinueWatching={loadMoreContinueWatching}
          onLoadMoreLatestAdded={loadMoreLatestAdded}
          onLoadMoreFavorites={loadMoreFavorites}
          initialModelName={initialModelName}
          initialManualTag={initialManualTag}
          onSelectModel={handleSelectModel}
          onOpenDetails={handleOpenDetails}
          onPlay={handlePlay}
          onVisibleMetadataReady={handleVisibleMetadataReady}
        />
      )}

      {selectedItem ? (
        <Suspense fallback={null}>
          <SpiritFlixDetailsModal
            client={client}
            item={selectedItem}
            onClose={() => setSelectedItem(null)}
            onPlay={handleDetailsPlay}
          />
        </Suspense>
      ) : null}

      {playingItem ? (
        <Suspense fallback={null}>
          <SpiritFlixPlayer
            client={client}
            item={playingItem}
            queue={playingQueue}
            libraryItems={modelAwareLibraryItems}
            startPositionTicks={playingQueue?.startPositionTicks}
            onPlaybackProgress={handlePlaybackProgress}
            onToggleFavorite={handleToggleFavorite}
            onSelectItem={handleQueueSelect}
            onShuffleQueue={handleShuffleQueue}
            onPlayModelShuffle={handlePlayModelShuffle}
            onReorderQueue={handleReorderQueue}
            onDeleteItem={handlePlayerDelete}
            onClose={() => {
              setPlayingItem(null);
              setPlayingQueue(null);
              void loadHome(homeData.selectedLibraryId);
            }}
          />
        </Suspense>
      ) : null}
    </main>
  );
}
