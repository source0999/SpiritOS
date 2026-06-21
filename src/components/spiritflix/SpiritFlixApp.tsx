"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  clearStoredSession,
  getStoredSession,
  JellyfinClient,
  isPlayableItem,
  isVisibleSpiritFlixItem,
  normalizeJellyfinServerUrl,
  SPIRITFLIX_DEFAULT_SERVER,
  storeSession,
} from "@/lib/spiritflix-jellyfin-client";
import type {
  JellyfinItem,
  SpiritFlixHomeData,
  SpiritFlixManualModelRecord,
  SpiritFlixServerInfo,
  SpiritFlixSession,
} from "@/lib/spiritflix-types";
import { hasResumeProgress } from "@/lib/spiritflix-resume";
import { filterItemsByVideoOrientation, getOrientationFilterLabel, type SpiritFlixVideoOrientation } from "@/lib/spiritflix-orientation";
import { SpiritFlixHome } from "./SpiritFlixHome";
import { SpiritFlixLogin } from "./SpiritFlixLogin";
import { SpiritFlixDetailsModal } from "./SpiritFlixDetailsModal";
import { SpiritFlixPlayer } from "./SpiritFlixPlayer";

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
};

const OTHER_LIBRARY_NAME = "Other";
const PLAYLIST_LIBRARY_NAME = "Playlists";
const HIDDEN_LIBRARY_NAMES = new Set(["music"]);

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
  return items
    .map((item) => ({ item, sort: Math.random() }))
    .sort((left, right) => left.sort - right.sort)
    .map(({ item }) => item);
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

function getSeriesPlaybackKey(item: JellyfinItem): string {
  if (!isSeriesPlaybackItem(item)) return "";
  if (item.SeriesName?.trim()) return item.SeriesName.trim().toLowerCase();
  const sourcePath = normalizeSpiritFlixPath(item.MediaSources?.[0]?.Path ?? item.Path);
  const parts = sourcePath.split("/").filter(Boolean);
  const seasonIndex = parts.findIndex((part) => /^season\s+\d+/i.test(part));
  if (seasonIndex > 0) return parts[seasonIndex - 1]?.toLowerCase() ?? "";
  const animeIndex = parts.findIndex((part) => part.toLowerCase() === "anime");
  return animeIndex >= 0 ? parts[animeIndex + 1]?.toLowerCase() ?? "" : "";
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
  const [homeData, setHomeData] = useState<SpiritFlixHomeData>(emptyHome);
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

  const client = useMemo(
    () => new JellyfinClient(session?.serverUrl ?? serverUrl, session?.accessToken, session?.userId),
    [serverUrl, session],
  );
  const modelAwareLibraryItems = useMemo(
    () => applyManualModelRecordsToItems(homeData.libraryItems, manualModelRecords),
    [homeData.libraryItems, manualModelRecords],
  );

  const modelAwareHomeData = useMemo(
    () => ({
      ...homeData,
      libraryItems: modelAwareLibraryItems,
    }),
    [homeData, modelAwareLibraryItems],
  );

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

  const loadHome = useCallback(
    async (libraryId?: string | null, term = searchTerm, options: { silent?: boolean } = {}) => {
      if (!session) return;
      if (!options.silent) setLoadingHome(true);
      setHomeError("");
      try {
        const libraries = (await client.getLibraries()).filter(isMediaLibrary);
        const otherLibrary = libraries.find((library) => library.Name.toLowerCase() === OTHER_LIBRARY_NAME.toLowerCase());
        const requestedLibraryId = libraryId === undefined ? homeData.selectedLibraryId : libraryId;
        const selectedLibraryId = requestedLibraryId && libraries.some((library) => library.Id === requestedLibraryId)
          ? requestedLibraryId
          : requestedLibraryId === null
            ? null
            : otherLibrary?.Id ?? libraries[0]?.Id ?? null;
        const animeLibrary = libraries.find((library) => library.Name.toLowerCase() === "anime");
        const [libraryItems, featuredItems, continueWatching, watchHistory, latestAdded, favorites] = await Promise.all([
          selectedLibraryId ? client.getLibraryItems(selectedLibraryId, term) : Promise.resolve([]),
          !selectedLibraryId && animeLibrary
            ? client
                .getLibraryItems(animeLibrary.Id)
                .then((items) => items.filter((item) => isPlayableItem(item) && isSeriesPlaybackItem(item)).sort(byEpisodeOrder))
            : Promise.resolve([]),
          selectedLibraryId ? client.getLibraryResumeItems(selectedLibraryId) : client.getContinueWatching(),
          client.getWatchHistory(selectedLibraryId ?? undefined),
          selectedLibraryId ? client.getLibraryItems(selectedLibraryId, "", 18) : client.getLatestAdded(),
          selectedLibraryId ? client.getLibraryFavoriteItems(selectedLibraryId) : client.getFavorites(),
        ]);
        const isNotDeleted = (item: JellyfinItem) => !deletedItemIdsRef.current.has(item.Id) && isVisibleSpiritFlixItem(item);
        const libraryItemsUnique = uniqueItems(libraryItems.filter(isNotDeleted));
        const watchHistoryItems = sortByLastPlayed(uniqueItems(watchHistory.filter(isNotDeleted).filter(hasWatchActivity)));
        const continueWatchingItems = sortByLastPlayed(
          uniqueItems([
            ...continueWatching.filter(isNotDeleted),
            ...watchHistoryItems.filter(hasResumeProgress),
            ...libraryItemsUnique.filter(hasResumeProgress),
          ]),
        );
        setHomeData({
          libraries,
          playlists: [],
          selectedLibraryId,
          featuredItems: uniqueItems(featuredItems.filter(isNotDeleted)),
          libraryItems: libraryItemsUnique,
          continueWatching: continueWatchingItems,
          watchHistory: watchHistoryItems,
          latestAdded: uniqueItems(latestAdded.filter(isNotDeleted)),
          favorites: uniqueItems(favorites.filter(isNotDeleted)),
        });
      } catch {
        setHomeError("Could not load your Jellyfin library. Log out and back in if the token expired.");
      } finally {
        if (!options.silent) setLoadingHome(false);
      }
    },
    [client, homeData.selectedLibraryId, searchTerm, session],
  );

  useEffect(() => {
    const timer = window.setTimeout(() => {
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
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (isRestoringSession) return undefined;
    const timer = window.setTimeout(() => {
      void checkServer(serverUrl);
    }, 0);
    return () => window.clearTimeout(timer);
  }, [checkServer, isRestoringSession, serverUrl]);

  useEffect(() => {
    if (!session) {
      loadedSessionKeyRef.current = null;
      return undefined;
    }
    const sessionKey = `${session.serverUrl}:${session.userId}:${session.accessToken}`;
    if (loadedSessionKeyRef.current === sessionKey) return undefined;
    loadedSessionKeyRef.current = sessionKey;
    const timer = window.setTimeout(() => {
      void loadHome(initialBrowseRouteRef.current?.libraryId ?? null);
      void loadManualModels();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [loadHome, loadManualModels, session]);

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
    const refreshPlaybackState = () => {
      void loadHome(homeData.selectedLibraryId, searchTerm, { silent: true });
    };
    const handleVisibilityChange = () => {
      if (document.visibilityState === "visible") refreshPlaybackState();
    };
    const timer = window.setInterval(refreshPlaybackState, 30000);
    window.addEventListener("focus", refreshPlaybackState);
    document.addEventListener("visibilitychange", handleVisibilityChange);
    return () => {
      window.clearInterval(timer);
      window.removeEventListener("focus", refreshPlaybackState);
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
      isShuffled: false,
    };
  };

  const handlePlay = (item: JellyfinItem, queueItems?: JellyfinItem[], sourceTitle?: string, startPositionTicks?: number) => {
    if (isPlayableItem(item)) {
      const seriesQueue = getSeriesPlaybackQueue(item, [
        ...(queueItems ?? []),
        ...homeData.libraryItems,
        ...homeData.featuredItems,
        ...homeData.latestAdded,
        ...homeData.continueWatching,
        ...homeData.watchHistory,
      ]);
      const resolvedQueueItems = seriesQueue.length ? seriesQueue : queueItems;
      const resolvedSourceTitle = seriesQueue.length ? item.SeriesName ?? sourceTitle ?? "Series" : sourceTitle;
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
      void loadHome(homeData.selectedLibraryId, searchTerm, { silent: true });
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
        <section className="spiritflix-restore">
          <div className="spiritflix-brand">
            <span className="spiritflix-brand__sigil">SF</span>
            <span>SpiritFlix</span>
          </div>
        </section>
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
          data={modelAwareHomeData}
          loading={loadingHome}
          error={homeError}
          session={session}
          searchTerm={searchTerm}
          serverInfo={serverInfo}
          onLogout={handleLogout}
          onRefresh={() => loadHome(homeData.selectedLibraryId)}
          onSearch={handleSearch}
          onSelectHome={handleSelectHome}
          onSelectLibrary={handleSelectLibrary}
          initialModelName={initialModelName}
          initialManualTag={initialManualTag}
          onSelectModel={handleSelectModel}
          onOpenDetails={handleOpenDetails}
          onPlay={handlePlay}
        />
      )}

      {selectedItem ? (
        <SpiritFlixDetailsModal
          client={client}
          item={selectedItem}
          onClose={() => setSelectedItem(null)}
          onPlay={handleDetailsPlay}
        />
      ) : null}

      {playingItem ? (
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
      ) : null}
    </main>
  );
}
