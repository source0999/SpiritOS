// Isolated Continue Watching v1 - Dedicated gooner user lane - Z Fold optimized
"use client";

// Face Organizer integration v1 - Model sorting from sidecars + known_performers - Z Fold optimized
// Layout v2 - Model-centric + Grid/List toggle - Z Fold optimized - Codex executed 2026-06-04

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  ChevronLeft,
  ChevronRight,
  Clock3,
  Grid2X2,
  Heart,
  Images,
  List,
  LogOut,
  Maximize2,
  Pause,
  Play,
  RefreshCw,
  RotateCcw,
  Search,
  Server,
  Settings,
  SlidersHorizontal,
  Shuffle,
  Sparkles,
  Tag,
  Timer,
  X,
} from "lucide-react";
import { formatRuntime, isPlayableItem, type JellyfinClient } from "@/lib/spiritflix-jellyfin-client";
import { getSpiritFlixManualTagScope } from "@/lib/spiritflix/manual-tag-scope";
import {
  getResumePositionTicks,
  getResumeProgressPercent,
  getResumeSlotLabel,
  getTimeLeftLabel,
  hasResumeProgress,
} from "@/lib/spiritflix-resume";
import {
  countItemsByVideoOrientation,
  filterItemsByVideoOrientation,
  getOrientationFilterLabel,
  itemMatchesVideoOrientation,
  type SpiritFlixOrientationFilter,
} from "@/lib/spiritflix-orientation";
import type {
  FaceOrganizerMetadataResponse,
  FaceOrganizerStatus,
  FaceOrganizerVideoMatch,
  JellyfinItem,
  SpiritFlixGalleryItem,
  SpiritFlixGalleryResponse,
  SpiritFlixHomeData,
  SpiritFlixManualModelIndex,
  SpiritFlixManualModelSummary,
  SpiritFlixManualModelRecord,
  SpiritFlixManualTagIndex,
  SpiritFlixManualTagRecord,
  SpiritFlixServerInfo,
  SpiritFlixSession,
} from "@/lib/spiritflix-types";
import { SpiritFlixRail } from "./SpiritFlixRail";
import { SpiritFlixImage } from "./SpiritFlixImage";

interface SpiritFlixHomeProps {
  client: JellyfinClient;
  data: SpiritFlixHomeData;
  loading: boolean;
  error: string;
  session: SpiritFlixSession;
  searchTerm: string;
  serverInfo: SpiritFlixServerInfo | null;
  onLogout: () => void;
  onRefresh: () => void;
  onSearch: (term: string) => void;
  onSelectHome: () => void;
  onSelectLibrary: (libraryId: string) => void;
  loadingMore?: Partial<Record<"library" | "continueWatching" | "latestAdded" | "favorites", boolean>>;
  onLoadMoreLibrary?: () => void;
  onLoadMoreContinueWatching?: () => void;
  onLoadMoreLatestAdded?: () => void;
  onLoadMoreFavorites?: () => void;
  initialModelName?: string | null;
  initialManualTag?: string | null;
  onSelectModel: (modelName: string | null) => void;
  onOpenDetails: (item: JellyfinItem) => void;
  onPlay: (item: JellyfinItem, queueItems?: JellyfinItem[], sourceTitle?: string, startPositionTicks?: number) => void;
}

type LibraryViewMode = "grid" | "list" | "history" | "favorites" | "gallery" | "models";
type LibrarySortMode = "model" | "title" | "dateAdded" | "duration";
type LibrarySortDirection = "asc" | "desc";
type LibrarySmartRescanState = {
  status: "idle" | "running" | "completed" | "failed";
  startedAt?: string;
  updatedAt?: string;
  completedAt?: string;
  error?: string;
  phase?: string;
  phaseLabel?: string;
  progress?: {
    total?: number;
    completed?: number;
    percent?: number;
  };
  modelProgress?: {
    total?: number;
    completed?: number;
    accepted?: number;
    skipped?: number;
  };
  currentItem?: {
    kind?: string;
    name?: string;
    path?: string;
    preview?: string;
  };
  summary?: {
    videos_scanned?: number;
    smart_accepts?: unknown[];
    smart_accept_skips?: unknown[];
  };
};

function normalizeSmartRescanState(value: unknown): LibrarySmartRescanState {
  if (!value || typeof value !== "object") return { status: "idle" };
  const candidate = value as Partial<LibrarySmartRescanState>;
  const status = candidate.status;
  if (status !== "idle" && status !== "running" && status !== "completed" && status !== "failed") {
    return { status: "idle" };
  }
  return {
    status,
    startedAt: typeof candidate.startedAt === "string" ? candidate.startedAt : undefined,
    updatedAt: typeof candidate.updatedAt === "string" ? candidate.updatedAt : undefined,
    completedAt: typeof candidate.completedAt === "string" ? candidate.completedAt : undefined,
    error: typeof candidate.error === "string" ? candidate.error : undefined,
    phase: typeof candidate.phase === "string" ? candidate.phase : undefined,
    phaseLabel: typeof candidate.phaseLabel === "string" ? candidate.phaseLabel : undefined,
    progress: candidate.progress,
    modelProgress: candidate.modelProgress,
    currentItem: candidate.currentItem,
    summary: candidate.summary,
  };
}

interface ModelGroup {
  name: string;
  count: number;
  indexedCount: number;
  liveSourceCount?: number;
  items: JellyfinItem[];
  representative?: JellyfinItem;
  source: "face-organizer" | "jellyfin";
  status: FaceOrganizerStatus;
  confidence?: number;
}

const LIBRARY_VIEW_MODE_KEY = "spiritflix_library_view_mode";
const LIBRARY_SORT_MODE_KEY = "spiritflix_library_sort_mode";
const LIBRARY_SORT_DIRECTION_KEY = "spiritflix_library_sort_direction";
const LIBRARY_ORIENTATION_FILTER_KEY = "spiritflix_library_orientation_filter";
const LIBRARY_UI_STATE_KEY = "spiritflix_library_ui_state";
const FACE_METADATA_CACHE_KEY = "spiritflix_face_metadata_v5";
const GALLERY_INTERVAL_KEY = "spiritflix_gallery_interval_seconds";
const LIBRARY_PAGE_SIZE = 20;
const TEMP_LIBRARY_NAME = "Home Videos and Photos";
const TWITTER_SOURCE_MODEL_NAME = "Twitter";
const MODEL_NAME_ALIASES: Record<string, string> = {
  aaliyahyasan: "Aaliyah Yasan",
  alannasworlx: "Alannasworldx",
  alannasworldx: "Alannasworldx",
  cutegeekie: "Cute Geekie",
  cutegeeky: "Cute Geekie",
  cutelittlepearl: "Cute Geekie",
  gemthejewels: "Gem The Jewels",
  gemthejewls: "Gem The Jewels",
  izzygreen: "Izzy Green",
  jakarababy: "Jakara Mitchell",
  jakaramitchell: "Jakara Mitchell",
  jazmanjafar: "Jazmen Jafar",
  jazmenjafar: "Jazmen Jafar",
  jazmenjarfar: "Jazmen Jafar",
  kinkykttn: "Kinkykttn",
  kinkyktn: "Kinkykttn",
  mackzjones: "Mackzjones",
  misslilu: "Miss LiLu",
  puffypink: "Puffy Pink",
  ruthlce: "Ruth Lee",
  ruthlee: "Ruth Lee",
  savaschultz: "Sava Schultz",
  savaschult: "Sava Schultz",
  savaschu: "Sava Schultz",
  savaschyltz: "Sava Schultz",
  siennaababi: "Sienna Ababi",
  siennaabab: "Sienna Ababi",
  sendnudes: "Sendnudesx",
  sendnudesx: "Sendnudesx",
  sendnudexx: "Sendnudesx",
  sendnudesxx: "Sendnudesx",
  whoahannahjo: "Whoahannahjo",
};

interface StoredLibraryUiState {
  selectedLibraryId: string | null;
  selectedModel: string | null;
  selectedManualTag: string | null;
  excludedCategories: string[];
  viewMode: LibraryViewMode;
  sortMode: LibrarySortMode;
  sortDirection: LibrarySortDirection;
  orientationFilter: SpiritFlixOrientationFilter;
  filtersOpen: boolean;
  pageIndex: number;
}

function getStoredLibraryUiState(): Partial<StoredLibraryUiState> {
  if (typeof window === "undefined") return {};
  try {
    const parsed = JSON.parse(window.localStorage.getItem(LIBRARY_UI_STATE_KEY) ?? "{}") as Partial<StoredLibraryUiState>;
    return parsed && typeof parsed === "object" ? parsed : {};
  } catch {
    return {};
  }
}

function isLibraryViewMode(value: unknown): value is LibraryViewMode {
  return value === "grid" || value === "list" || value === "history" || value === "favorites" || value === "gallery" || value === "models";
}

function isLibrarySortMode(value: unknown): value is LibrarySortMode {
  return value === "model" || value === "title" || value === "dateAdded" || value === "duration";
}

function isLibrarySortDirection(value: unknown): value is LibrarySortDirection {
  return value === "asc" || value === "desc";
}

function isOrientationFilter(value: unknown): value is SpiritFlixOrientationFilter {
  return value === "all" || value === "portrait" || value === "landscape";
}

function scheduleDeferredHomeTask(task: () => void): () => void {
  let canceled = false;
  const timer = window.setTimeout(() => {
    if (!canceled) task();
  }, 16);
  return () => {
    canceled = true;
    window.clearTimeout(timer);
  };
}

function getStoredExcludedCategories(state: Partial<StoredLibraryUiState>): string[] {
  return Array.isArray(state.excludedCategories)
    ? state.excludedCategories.filter((category): category is string => typeof category === "string")
    : [];
}
const NON_MODEL_FOLDER_NAMES = new Set(["yes", "other"]);

function displayLibraryName(name?: string): string {
  return name === TEMP_LIBRARY_NAME ? "Library" : name ?? "Library";
}

function getModelAliasKey(name: string): string {
  return name.toLowerCase().replace(/[^a-z0-9]/g, "");
}

function normalizeModelName(name: string): string {
  return MODEL_NAME_ALIASES[getModelAliasKey(name)] ?? name;
}

function getOrganizerModelName(name: string, faceMetadata: FaceOrganizerMetadataResponse | null): string | undefined {
  return faceMetadata?.enrolledSources?.[getModelAliasKey(name)]?.name;
}

function getCanonicalModelName(name: string, faceMetadata: FaceOrganizerMetadataResponse | null): string {
  return getOrganizerModelName(name, faceMetadata) ?? normalizeModelName(name);
}

function getLiveSourceCount(name: string, faceMetadata: FaceOrganizerMetadataResponse | null): number | undefined {
  return faceMetadata?.enrolledSources?.[getModelAliasKey(name)]?.candidateVideos;
}

function isNonModelFolderName(name?: string): boolean {
  return Boolean(name && NON_MODEL_FOLDER_NAMES.has(getModelAliasKey(name)));
}

function getModelName(item: JellyfinItem): string {
  const person = item.People?.find((entry) =>
    ["actor", "actress", "performer", "artist"].includes(entry.Type?.toLowerCase() ?? ""),
  );
  if (person?.Name) return person.Name;
  if (item.SeriesName && !isNonModelFolderName(item.SeriesName)) return item.SeriesName;
  if (item.Path) {
    const parts = item.Path.split(/[\\/]+/).filter(Boolean);
    const fileName = parts.at(-1);
    const folderName = parts.at(-2);
    if (folderName && folderName !== fileName && !isNonModelFolderName(folderName)) return folderName;
  }
  return "unknown";
}

function getFaceMatch(item: JellyfinItem, faceMetadata: FaceOrganizerMetadataResponse | null): FaceOrganizerVideoMatch | undefined {
  return faceMetadata?.videos[item.Id];
}

function hasIdentifiedFace(match?: FaceOrganizerVideoMatch): boolean {
  return Boolean(match?.primaryPerformer?.name && match.primaryPerformer.name !== "unknown performer" && match.status === "confirmed");
}

function getDisplayModelName(item: JellyfinItem, faceMetadata: FaceOrganizerMetadataResponse | null): string {
  if (item.ManualModelName) return getCanonicalModelName(item.ManualModelName, faceMetadata);
  const faceMatch = getFaceMatch(item, faceMetadata);
  if (hasIdentifiedFace(faceMatch)) return getCanonicalModelName(faceMatch?.primaryPerformer?.name ?? "Unknown", faceMetadata);
  return getCanonicalModelName(getModelName(item), faceMetadata);
}

function getStatusRank(status?: FaceOrganizerStatus): number {
  if (status === "confirmed") return 0;
  if (status === "needs_review") return 1;
  if (status === "unknown") return 2;
  return 3;
}

function isTwitterSourceItem(item: JellyfinItem): boolean {
  const sourceText = [
    item.Name,
    item.SeriesName,
    item.Overview,
    item.Path,
    ...(item.ManualTags ?? []),
    ...(item.MediaSources?.map((source) => source.Path) ?? []),
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();

  return /\btwitter\b|twitter\.com|\bx\.com\b|twimg|\btweet\b|\btweets\b|\bvideos from x\b|\bfrom x\b/.test(sourceText);
}

function isTwitterSourceGroupName(name: string): boolean {
  const normalized = getModelAliasKey(name);
  return normalized === "twitter" || normalized === "videosfromx" || normalized === "fromx";
}

function getItemCategoryKeys(item: JellyfinItem): string[] {
  return isTwitterSourceItem(item) ? ["twitter"] : [];
}

function buildModelGroups(
  items: JellyfinItem[],
  faceMetadata: FaceOrganizerMetadataResponse | null,
  modelCatalog: SpiritFlixManualModelSummary[] = [],
): ModelGroup[] {
  const groups = new Map<string, JellyfinItem[]>();
  const metaByName = new Map<string, { source: ModelGroup["source"]; status: FaceOrganizerStatus; confidence?: number }>();

  items.filter(isPlayableItem).forEach((item) => {
    const faceMatch = getFaceMatch(item, faceMetadata);
    const isFaceIdentified = hasIdentifiedFace(faceMatch);
    const rawModelName = item.ManualModelName ?? (isFaceIdentified ? faceMatch?.primaryPerformer?.name ?? getModelName(item) : getModelName(item));
    const modelName = getCanonicalModelName(rawModelName, faceMetadata);
    groups.set(modelName, [...(groups.get(modelName) ?? []), item]);
    const current = metaByName.get(modelName);
    const next = {
      source: isFaceIdentified ? "face-organizer" : "jellyfin",
      status: faceMatch?.status ?? "unscanned",
      confidence: faceMatch?.confidence,
    } as const;
    if (!current || getStatusRank(next.status) < getStatusRank(current.status)) {
      metaByName.set(modelName, next);
    }
  });

  const catalogByName = new Map(modelCatalog.map((model) => [getModelAliasKey(model.modelName), model]));
  const regularGroups = Array.from(new Set([...Array.from(groups.keys()), ...modelCatalog.map((model) => getCanonicalModelName(model.modelName, faceMetadata))]))
    .map((name) => {
      const modelItems = groups.get(name) ?? [];
      const catalogEntry = catalogByName.get(getModelAliasKey(name));
      const indexedCount = Math.max(modelItems.length, catalogEntry?.count ?? 0);
      const liveSourceCount = getLiveSourceCount(name, faceMetadata);
      return {
        name,
        count: indexedCount,
        indexedCount,
        liveSourceCount,
        items: modelItems,
        representative: modelItems.find((item) => item.ImageTags?.Primary || item.ImageTags?.Thumb) ?? modelItems[0],
        source: metaByName.get(name)?.source ?? "jellyfin",
        status: metaByName.get(name)?.status ?? "unscanned",
        confidence: metaByName.get(name)?.confidence,
      };
    })
    .sort(
      (left, right) =>
        right.indexedCount - left.indexedCount ||
        (right.liveSourceCount ?? 0) - (left.liveSourceCount ?? 0) ||
        getStatusRank(left.status) - getStatusRank(right.status) ||
        Number(right.source === "face-organizer") - Number(left.source === "face-organizer") ||
        left.name.localeCompare(right.name),
    );

  const twitterItems = items.filter((item) => isPlayableItem(item) && isTwitterSourceItem(item));
  if (!twitterItems.length) return regularGroups;

  return [
    {
      name: TWITTER_SOURCE_MODEL_NAME,
      count: twitterItems.length,
      indexedCount: twitterItems.length,
      items: twitterItems,
      representative: twitterItems.find((item) => item.ImageTags?.Primary || item.ImageTags?.Thumb) ?? twitterItems[0],
      source: "jellyfin",
      status: "unscanned",
    },
    ...regularGroups.filter((group) => !isTwitterSourceGroupName(group.name)),
  ];
}

function shuffleItems(items: JellyfinItem[]): JellyfinItem[] {
  const shuffled = [...items];
  for (let index = shuffled.length - 1; index > 0; index -= 1) {
    const swapIndex = Math.floor(Math.random() * (index + 1));
    [shuffled[index], shuffled[swapIndex]] = [shuffled[swapIndex], shuffled[index]];
  }
  return shuffled;
}

function applyManualModelMapToItems(items: JellyfinItem[], manualModelMap: Map<string, string>): JellyfinItem[] {
  return items.map((item) => {
    const manualModelName = manualModelMap.get(item.Id);
    return manualModelName ? { ...item, ManualModelName: manualModelName } : item;
  });
}

function markItemAsFavorite(item: JellyfinItem): JellyfinItem {
  if (item.UserData?.IsFavorite) return item;
  return {
    ...item,
    UserData: {
      ...(item.UserData ?? {}),
      IsFavorite: true,
    },
  };
}

function getNewThisWeekCount(items: JellyfinItem[]): number {
  const now = Date.now();
  const weekMs = 7 * 24 * 60 * 60 * 1000;
  return items.filter((item) => {
    if (!item.DateCreated) return false;
    const createdAt = new Date(item.DateCreated).getTime();
    return Number.isFinite(createdAt) && now - createdAt <= weekMs;
  }).length;
}

function getVideoCountLabel(count: number): string {
  return `${count} ${count === 1 ? "video" : "videos"}`;
}

function getDateCreatedMs(item: JellyfinItem): number {
  if (!item.DateCreated) return 0;
  const value = new Date(item.DateCreated).getTime();
  return Number.isFinite(value) ? value : 0;
}

function getLastPlayedMs(item: JellyfinItem): number {
  if (!item.UserData?.LastPlayedDate) return 0;
  const value = new Date(item.UserData.LastPlayedDate).getTime();
  return Number.isFinite(value) ? value : 0;
}

function getLastPlayedLabel(item: JellyfinItem): string {
  const playedAt = getLastPlayedMs(item);
  if (!playedAt) return "No recent play date";
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(playedAt));
}

function getModelSlug(name: string): string {
  return name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "") || getModelAliasKey(name);
}

function galleryItemMatchesModel(item: SpiritFlixGalleryItem, modelName: string): boolean {
  const modelKey = getModelAliasKey(modelName);
  const modelSlug = getModelSlug(modelName);
  return item.modelKey === modelKey || item.modelSlug === modelSlug || getModelAliasKey(item.modelName) === modelKey;
}

function getGalleryDateLabel(item: SpiritFlixGalleryItem): string {
  if (!item.uploadedAt) return "Gallery";
  const value = new Date(item.uploadedAt).getTime();
  if (!Number.isFinite(value)) return "Gallery";
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
  }).format(new Date(value));
}

function getDurationTicks(item: JellyfinItem): number {
  if (typeof item.RunTimeTicks === "number" && item.RunTimeTicks > 0) return item.RunTimeTicks;
  const sourceTicks =
    item.MediaSources?.map((source) => source.RunTimeTicks ?? 0)
      .filter((ticks) => ticks > 0)
      .sort((left, right) => right - left)[0] ?? 0;
  return sourceTicks;
}

function getItemSourcePath(item: JellyfinItem): string {
  return item.MediaSources?.[0]?.Path ?? item.Path ?? "";
}

function getNormalizedItemSourcePath(item: JellyfinItem): string {
  return getItemSourcePath(item).replace(/\\/g, "/");
}

function getAnimePathParts(item: JellyfinItem): string[] {
  return getNormalizedItemSourcePath(item).split("/").filter(Boolean);
}

function getAnimeSeriesName(item: JellyfinItem): string {
  const parts = getAnimePathParts(item);
  const seasonIndex = parts.findIndex((part) => /^season\s+\d+/i.test(part));
  if (seasonIndex > 0) return parts[seasonIndex - 1] ?? "Anime";
  const animeIndex = parts.findIndex((part) => part.toLowerCase() === "anime");
  if (animeIndex >= 0 && parts[animeIndex + 1]) return parts[animeIndex + 1];
  if (item.SeriesName?.trim()) return item.SeriesName.trim();
  return "Anime";
}

function getAnimeSeriesKey(item: JellyfinItem): string {
  return getModelAliasKey(getAnimeSeriesName(item));
}

function getAnimeSeasonNumber(item: JellyfinItem): number {
  if (typeof item.ParentIndexNumber === "number" && item.ParentIndexNumber > 0) return item.ParentIndexNumber;
  const pathMatch = getNormalizedItemSourcePath(item).match(/season\s+(\d+)/i);
  if (pathMatch?.[1]) return Number(pathMatch[1]);
  const titleMatch = item.Name.match(/\bS(\d{1,2})E\d{1,3}\b/i);
  if (titleMatch?.[1]) return Number(titleMatch[1]);
  return 1;
}

function getAnimeEpisodeNumber(item: JellyfinItem): number {
  if (typeof item.IndexNumber === "number" && item.IndexNumber > 0) return item.IndexNumber;
  const titleMatch = item.Name.match(/\bS\d{1,2}E(\d{1,3})\b/i);
  if (titleMatch?.[1]) return Number(titleMatch[1]);
  const pathMatch = getItemSourcePath(item).match(/\bS\d{1,2}E(\d{1,3})\b/i);
  if (pathMatch?.[1]) return Number(pathMatch[1]);
  const leadingMatch = item.Name.match(/(?:^|\s-\s)(\d{1,3})(?:\s-\s|$)/);
  if (leadingMatch?.[1]) return Number(leadingMatch[1]);
  return 0;
}

function compareAnimeEpisodes(left: JellyfinItem, right: JellyfinItem): number {
  return (
    getAnimeSeasonNumber(left) - getAnimeSeasonNumber(right) ||
    getAnimeEpisodeNumber(left) - getAnimeEpisodeNumber(right) ||
    left.Name.localeCompare(right.Name)
  );
}

function formatAnimeEpisodeLabel(item: JellyfinItem): string {
  const episodeNumber = getAnimeEpisodeNumber(item);
  return episodeNumber > 0 ? `Episode ${episodeNumber}` : "Episode";
}

function getAnimeEpisodeTitle(item: JellyfinItem): string {
  const seriesName = getAnimeSeriesName(item);
  const withoutSeriesPrefix = item.Name
    .replace(new RegExp(`^${escapeRegExp(seriesName)}\\s*-\\s*`, "i"), "")
    .replace(/^\s*S\d{1,2}E\d{1,3}\s*[-:]\s*/i, "")
    .trim();
  return withoutSeriesPrefix || item.Name;
}

function escapeRegExp(value: string): string {
  return value.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

function getUnwatchedAnimeEpisode(items: JellyfinItem[]): JellyfinItem | null {
  return items.find((item) => !item.UserData?.Played && (item.UserData?.PlayedPercentage ?? 0) < 90) ?? null;
}

function compareOptionalNumber(left: number, right: number, direction: LibrarySortDirection): number {
  const leftHasValue = left > 0;
  const rightHasValue = right > 0;
  if (leftHasValue && !rightHasValue) return -1;
  if (!leftHasValue && rightHasValue) return 1;
  if (!leftHasValue && !rightHasValue) return 0;
  return direction === "asc" ? left - right : right - left;
}

function getSortModeLabel(sortMode: LibrarySortMode): string {
  if (sortMode === "model") return "Model";
  if (sortMode === "dateAdded") return "Last added";
  if (sortMode === "duration") return "Duration";
  return "Title";
}

function getSortDirectionLabel(sortDirection: LibrarySortDirection): string {
  return sortDirection === "asc" ? "Ascending" : "Descending";
}

interface LibraryFeedCardProps {
  client: JellyfinClient;
  item: JellyfinItem;
  manualTags?: string[];
  playOnPrimaryTap: boolean;
  imagePriority?: boolean;
  onOpenDetails: (item: JellyfinItem) => void;
  onPlay: (item: JellyfinItem, startPositionTicks?: number) => void;
}

function LibraryFeedCard({ client, item, manualTags = [], playOnPrimaryTap, imagePriority = false, onOpenDetails, onPlay }: LibraryFeedCardProps) {
  const hasProgress = hasResumeProgress(item);
  const progress = getResumeProgressPercent(item);
  const resumeTicks = item.UserData?.PlaybackPositionTicks;
  const canPlay = isPlayableItem(item);
  const actionTags = manualTags.filter((tag) => getSpiritFlixManualTagScope(tag) === "video");

  return (
    <motion.article
      className="spiritflix-feed-card"
      whileHover={{ y: -3 }}
      transition={{ duration: 0.16 }}
    >
      <button
        className="spiritflix-feed-card__media"
        type="button"
        onClick={() => {
          if (playOnPrimaryTap && canPlay) {
            onPlay(item, hasProgress ? resumeTicks : undefined);
          } else {
            onOpenDetails(item);
          }
        }}
      >
        <SpiritFlixImage client={client} item={item} type="Primary" width={620} alt={item.Name} priority={imagePriority} />
        <span className="spiritflix-feed-card__shade" aria-hidden="true" />
        {actionTags.length ? (
          <span className="spiritflix-feed-card__tags" aria-label="Manual tags">
            {actionTags.slice(0, 3).map((tag) => (
              <span key={tag}>{tag}</span>
            ))}
          </span>
        ) : null}
        {progress > 0 ? (
          <span className="spiritflix-feed-card__progress" aria-hidden="true">
            <span style={{ width: `${Math.min(100, progress)}%` }} />
          </span>
        ) : null}
      </button>
      {canPlay ? (
        <button
          className="spiritflix-feed-card__play"
          type="button"
          onClick={() => onPlay(item, hasProgress ? resumeTicks : undefined)}
          aria-label={`${hasProgress ? "Resume" : "Play"} ${item.Name}`}
        >
          <Play size={24} fill="currentColor" aria-hidden="true" />
        </button>
      ) : null}
    </motion.article>
  );
}

interface GalleryCardProps {
  item: SpiritFlixGalleryItem;
  onOpen: () => void;
}

function GalleryCard({ item, onOpen }: GalleryCardProps) {
  return (
    <motion.button
      type="button"
      className="spiritflix-gallery-card"
      onClick={onOpen}
      whileTap={{ scale: 0.985 }}
    >
      <img src={item.thumbnailSrc ?? item.src} alt={`${item.modelName} gallery`} loading="lazy" decoding="async" />
      <span className="spiritflix-gallery-card__shade" aria-hidden="true" />
      <span className="spiritflix-gallery-card__meta">
        <strong>{item.modelName}</strong>
        <small>{item.collection || getGalleryDateLabel(item)}</small>
      </span>
    </motion.button>
  );
}

interface GalleryLightboxProps {
  items: SpiritFlixGalleryItem[];
  initialIndex: number;
  onClose: () => void;
}

function GalleryLightbox({ items, initialIndex, onClose }: GalleryLightboxProps) {
  const [activeIndex, setActiveIndex] = useState(initialIndex);
  const [isPlaying, setIsPlaying] = useState(items.length > 1);
  const [intervalSeconds, setIntervalSeconds] = useState(() => {
    if (typeof window === "undefined") return 5;
    const stored = window.localStorage.getItem(GALLERY_INTERVAL_KEY);
    const value = stored ? Number(stored) : 5;
    return Number.isFinite(value) ? Math.min(30, Math.max(2, value)) : 5;
  });
  const rootRef = useRef<HTMLDivElement | null>(null);
  const activeItem = items[activeIndex] ?? items[0];

  const goToOffset = useCallback(
    (offset: number) => {
      setActiveIndex((current) => {
        if (!items.length) return 0;
        return (current + offset + items.length) % items.length;
      });
    },
    [items.length],
  );

  useEffect(() => {
    setActiveIndex(Math.min(Math.max(initialIndex, 0), Math.max(0, items.length - 1)));
    setIsPlaying(items.length > 1);
  }, [initialIndex, items.length]);

  useEffect(() => {
    window.localStorage.setItem(GALLERY_INTERVAL_KEY, String(intervalSeconds));
  }, [intervalSeconds]);

  useEffect(() => {
    if (!isPlaying || items.length <= 1) return undefined;
    const timer = window.setInterval(() => goToOffset(1), intervalSeconds * 1000);
    return () => window.clearInterval(timer);
  }, [goToOffset, intervalSeconds, isPlaying, items.length]);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") onClose();
      if (event.key === "ArrowLeft") goToOffset(-1);
      if (event.key === "ArrowRight") goToOffset(1);
      if (event.key === " ") {
        event.preventDefault();
        setIsPlaying((current) => !current);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [goToOffset, onClose]);

  const toggleFullscreen = async () => {
    if (document.fullscreenElement) {
      await document.exitFullscreen().catch(() => undefined);
      return;
    }
    await rootRef.current?.requestFullscreen().catch(() => undefined);
  };

  if (!activeItem) return null;

  return (
    <div className="spiritflix-gallery-viewer" ref={rootRef} role="dialog" aria-modal="true">
      <div className="spiritflix-gallery-viewer__stage">
        <img src={activeItem.src} alt={`${activeItem.modelName} gallery picture`} />
      </div>
      <div className="spiritflix-gallery-viewer__top">
        <button type="button" onClick={onClose} aria-label="Close gallery">
          <X size={22} aria-hidden="true" />
        </button>
        <div className="spiritflix-gallery-viewer__title">
          <strong>{activeItem.modelName}</strong>
          <span>
            {activeIndex + 1} / {items.length}
            {activeItem.collection ? ` / ${activeItem.collection}` : ""}
          </span>
        </div>
        <button type="button" onClick={toggleFullscreen} aria-label="Fullscreen gallery">
          <Maximize2 size={21} aria-hidden="true" />
        </button>
      </div>
      <div className="spiritflix-gallery-viewer__controls">
        <button type="button" onClick={() => goToOffset(-1)} disabled={items.length <= 1} aria-label="Previous picture">
          <ChevronLeft size={24} aria-hidden="true" />
        </button>
        <button type="button" onClick={() => setIsPlaying((current) => !current)} disabled={items.length <= 1} aria-label={isPlaying ? "Pause gallery" : "Play gallery"}>
          {isPlaying ? <Pause size={22} aria-hidden="true" /> : <Play size={22} fill="currentColor" aria-hidden="true" />}
        </button>
        <label className="spiritflix-gallery-viewer__timer">
          <Timer size={18} aria-hidden="true" />
          <input
            type="number"
            min={2}
            max={30}
            step={1}
            value={intervalSeconds}
            onChange={(event) => {
              const value = Number(event.target.value);
              if (Number.isFinite(value)) setIntervalSeconds(Math.min(30, Math.max(2, value)));
            }}
            aria-label="Gallery seconds per picture"
          />
        </label>
        <button type="button" onClick={() => goToOffset(1)} disabled={items.length <= 1} aria-label="Next picture">
          <ChevronRight size={24} aria-hidden="true" />
        </button>
      </div>
    </div>
  );
}

export function SpiritFlixHome({
  client,
  data,
  loading,
  error,
  session,
  searchTerm,
  serverInfo,
  onLogout,
  onRefresh,
  onSearch,
  onSelectHome,
  onSelectLibrary,
  loadingMore = {},
  onLoadMoreLibrary,
  onLoadMoreContinueWatching,
  onLoadMoreLatestAdded,
  onLoadMoreFavorites,
  initialModelName = null,
  initialManualTag = null,
  onSelectModel,
  onOpenDetails,
  onPlay,
}: SpiritFlixHomeProps) {
  const [storedLibraryUiState] = useState(() => getStoredLibraryUiState());
  const [viewMode, setViewMode] = useState<LibraryViewMode>(() => isLibraryViewMode(storedLibraryUiState.viewMode) ? storedLibraryUiState.viewMode : "grid");
  const [sortMode, setSortMode] = useState<LibrarySortMode>(() => isLibrarySortMode(storedLibraryUiState.sortMode) ? storedLibraryUiState.sortMode : "model");
  const [sortDirection, setSortDirection] = useState<LibrarySortDirection>(() => isLibrarySortDirection(storedLibraryUiState.sortDirection) ? storedLibraryUiState.sortDirection : "desc");
  const [orientationFilter, setOrientationFilter] = useState<SpiritFlixOrientationFilter>(() => isOrientationFilter(storedLibraryUiState.orientationFilter) ? storedLibraryUiState.orientationFilter : "all");
  const [filtersOpen, setFiltersOpen] = useState(() => storedLibraryUiState.filtersOpen === true);
  const [selectedModel, setSelectedModel] = useState<string | null>(() => initialModelName ?? storedLibraryUiState.selectedModel ?? null);
  const [selectedManualTag, setSelectedManualTag] = useState<string | null>(() => initialManualTag ?? storedLibraryUiState.selectedManualTag ?? null);
  const [excludedCategories, setExcludedCategories] = useState<string[]>(() => getStoredExcludedCategories(storedLibraryUiState));
  const [faceMetadata, setFaceMetadata] = useState<FaceOrganizerMetadataResponse | null>(null);
  const [manualTagIndex, setManualTagIndex] = useState<SpiritFlixManualTagIndex | null>(null);
  const [manualTagRecords, setManualTagRecords] = useState<SpiritFlixManualTagRecord[]>([]);
  const [manualTagsError, setManualTagsError] = useState("");
  const [manualModelIndex, setManualModelIndex] = useState<SpiritFlixManualModelIndex | null>(null);
  const [manualModelRecords, setManualModelRecords] = useState<SpiritFlixManualModelRecord[]>([]);
  const [faceMetadataError, setFaceMetadataError] = useState("");
  const [galleryData, setGalleryData] = useState<SpiritFlixGalleryResponse | null>(null);
  const [galleryError, setGalleryError] = useState("");
  const [galleryLightbox, setGalleryLightbox] = useState<{ items: SpiritFlixGalleryItem[]; index: number } | null>(null);
  const [playPrimaryTapOnMobile, setPlayPrimaryTapOnMobile] = useState(false);
  const [smartRescan, setSmartRescan] = useState<LibrarySmartRescanState>({ status: "idle" });
  const [smartRescanError, setSmartRescanError] = useState("");
  const [isLibraryShuffleLoading, setIsLibraryShuffleLoading] = useState(false);
  const [fullLibraryItems, setFullLibraryItems] = useState<JellyfinItem[]>([]);
  const [libraryPageIndex, setLibraryPageIndex] = useState(() => {
    const storedPageIndex = Number(storedLibraryUiState.pageIndex);
    return Number.isInteger(storedPageIndex) && storedPageIndex >= 0 ? storedPageIndex : 0;
  });
  const didRunPageResetRef = useRef(false);
  const longPressTimerRef = useRef<number | null>(null);
  const didLongPressShuffleRef = useRef(false);
  const resumeTrackRef = useRef<HTMLDivElement | null>(null);
  const modelStripRef = useRef<HTMLDivElement | null>(null);
  const isHomeView = data.selectedLibraryId === null;
  const hasUsefulHomeContent = useMemo(
    () =>
      Boolean(
        (isHomeView && data.libraries.length) ||
          data.libraryItems.length ||
          data.continueWatching.length ||
          data.latestAdded.length ||
          data.featuredItems.length,
      ),
    [data.continueWatching.length, data.featuredItems.length, data.latestAdded.length, data.libraries.length, data.libraryItems.length, isHomeView],
  );
  const isPendingInitialContent = loading && !hasUsefulHomeContent;
  const selectedLibrary = data.libraries.find((library) => library.Id === data.selectedLibraryId);
  const libraryTitle = isHomeView ? "Home" : displayLibraryName(selectedLibrary?.Name);
  const isAnimeView = !isHomeView && selectedLibrary?.Name.toLowerCase() === "anime";
  const isLibraryDashboardView = !isHomeView && !isAnimeView;
  const hero = isAnimeView
    ? null
    : isHomeView
    ? data.featuredItems[0] ?? data.continueWatching[0] ?? data.latestAdded[0] ?? data.libraryItems[0] ?? null
    : data.libraryItems[0] ?? data.latestAdded[0] ?? data.continueWatching[0] ?? null;
  const manualModelMap = useMemo(() => {
    const map = new Map<string, string>();
    manualModelRecords.forEach((record) => {
      if (record.modelName) map.set(record.itemId, record.modelName);
    });
    return map;
  }, [manualModelRecords]);
  const libraryModelSourceItems = fullLibraryItems.length ? fullLibraryItems : data.libraryItems;
  const modelAwareLibraryItems = useMemo(
    () => applyManualModelMapToItems(libraryModelSourceItems, manualModelMap),
    [libraryModelSourceItems, manualModelMap],
  );
  const animeSeriesGroups = useMemo(() => {
    const seriesMap = new Map<string, Map<number, JellyfinItem[]>>();
    modelAwareLibraryItems.filter(isPlayableItem).forEach((item) => {
      const seriesName = getAnimeSeriesName(item);
      const seasonNumber = getAnimeSeasonNumber(item);
      const seasons = seriesMap.get(seriesName) ?? new Map<number, JellyfinItem[]>();
      seasons.set(seasonNumber, [...(seasons.get(seasonNumber) ?? []), item]);
      seriesMap.set(seriesName, seasons);
    });
    return Array.from(seriesMap.entries())
      .map(([seriesName, seasons]) => ({
        seriesName,
        seasons: Array.from(seasons.entries())
          .sort(([left], [right]) => left - right)
          .map(([seasonNumber, items]) => ({
            seasonNumber,
            items: [...items].sort(compareAnimeEpisodes),
          })),
      }))
      .map((series) => {
        const episodes = series.seasons.flatMap((season) => season.items);
        const resumeItem = [...episodes]
          .filter(hasResumeProgress)
          .sort((left, right) => getLastPlayedMs(right) - getLastPlayedMs(left))[0] ?? null;
        return {
          ...series,
          episodeCount: episodes.length,
          latestPlayedMs: Math.max(0, ...episodes.map(getLastPlayedMs)),
          representative: resumeItem ?? episodes.find((item) => item.ImageTags?.Primary || item.ImageTags?.Thumb) ?? episodes[0],
          resumeItem,
        };
      })
      .sort((left, right) => right.latestPlayedMs - left.latestPlayedMs || left.seriesName.localeCompare(right.seriesName));
  }, [modelAwareLibraryItems]);
  const [selectedAnimeSeriesName, setSelectedAnimeSeriesName] = useState<string | null>(null);
  const activeAnimeSeries = useMemo(() => {
    if (!animeSeriesGroups.length) return null;
    if (selectedAnimeSeriesName) {
      const selected = animeSeriesGroups.find((series) => series.seriesName === selectedAnimeSeriesName);
      if (selected) return selected;
    }
    return animeSeriesGroups[0] ?? null;
  }, [animeSeriesGroups, selectedAnimeSeriesName]);
  useEffect(() => {
    if (!selectedAnimeSeriesName) return;
    if (!animeSeriesGroups.some((series) => series.seriesName === selectedAnimeSeriesName)) {
      setSelectedAnimeSeriesName(null);
    }
  }, [animeSeriesGroups, selectedAnimeSeriesName]);
  const activeAnimeEpisodes = useMemo(
    () => activeAnimeSeries?.seasons.flatMap((season) => season.items) ?? [],
    [activeAnimeSeries],
  );
  const activeAnimeCurrentEpisode = useMemo(
    () => activeAnimeSeries?.resumeItem ?? getUnwatchedAnimeEpisode(activeAnimeEpisodes) ?? activeAnimeEpisodes[0] ?? null,
    [activeAnimeEpisodes, activeAnimeSeries],
  );
  const activeAnimeLastWatchedItem = useMemo(
    () => [...activeAnimeEpisodes].sort((left, right) => getLastPlayedMs(right) - getLastPlayedMs(left))[0] ?? null,
    [activeAnimeEpisodes],
  );
  const activeAnimeHero = activeAnimeSeries?.representative ?? activeAnimeCurrentEpisode;
  const modelGroups = useMemo(
    () => buildModelGroups(modelAwareLibraryItems, faceMetadata, manualModelIndex?.models ?? []),
    [faceMetadata, manualModelIndex?.models, modelAwareLibraryItems],
  );
  const selectedModelGroup = selectedModel ? modelGroups.find((model) => model.name === selectedModel) : null;
  const playableLibraryItems = useMemo(() => modelAwareLibraryItems.filter(isPlayableItem), [modelAwareLibraryItems]);
  const orientationCounts = useMemo(() => countItemsByVideoOrientation(playableLibraryItems), [playableLibraryItems]);
  const categoryFilters = useMemo(
    () => [
      {
        key: "twitter",
        label: "Twitter / X",
        count: playableLibraryItems.filter((item) => getItemCategoryKeys(item).includes("twitter")).length,
      },
    ],
    [playableLibraryItems],
  );
  const excludedCategorySet = useMemo(() => new Set(excludedCategories), [excludedCategories]);
  const manualTagMap = useMemo(() => {
    const map = new Map<string, string[]>();
    manualTagRecords.forEach((record) => map.set(record.itemId, record.manualTags));
    return map;
  }, [manualTagRecords]);
  const manualTagItemIds = useMemo(() => {
    if (!selectedManualTag) return null;
    return new Set(
      manualTagRecords
        .filter((record) => record.manualTags.includes(selectedManualTag))
        .map((record) => record.itemId),
    );
  }, [manualTagRecords, selectedManualTag]);
  const galleryItems = useMemo(() => galleryData?.items ?? [], [galleryData]);
  const selectedModelGalleryItems = useMemo(
    () => (selectedModelGroup ? galleryItems.filter((item) => galleryItemMatchesModel(item, selectedModelGroup.name)) : []),
    [galleryItems, selectedModelGroup],
  );
  const visibleGalleryItems = selectedModelGroup ? selectedModelGalleryItems : galleryItems;
  const scopedLibraryItems = useMemo(
    () => filterItemsByVideoOrientation(selectedModelGroup?.items ?? playableLibraryItems, orientationFilter),
    [orientationFilter, playableLibraryItems, selectedModelGroup],
  );
  const filteredLibraryItems = useMemo(
    () =>
      scopedLibraryItems
        .filter((item) => getItemCategoryKeys(item).every((category) => !excludedCategorySet.has(category)))
        .filter((item) => (manualTagItemIds ? manualTagItemIds.has(item.Id) : true)),
    [excludedCategorySet, manualTagItemIds, scopedLibraryItems],
  );
  const filteredLibraryItemIds = useMemo(
    () => new Set(filteredLibraryItems.map((item) => item.Id)),
    [filteredLibraryItems],
  );
  const itemMatchesActiveVideoFilters = useCallback(
    (item: JellyfinItem) => {
      if (selectedModelGroup && !filteredLibraryItemIds.has(item.Id)) return false;
      if (manualTagItemIds && !manualTagItemIds.has(item.Id)) return false;
      if (getItemCategoryKeys(item).some((category) => excludedCategorySet.has(category))) return false;
      return itemMatchesVideoOrientation(item, orientationFilter);
    },
    [excludedCategorySet, filteredLibraryItemIds, manualTagItemIds, orientationFilter, selectedModelGroup],
  );
  const sortedLibraryItems = useMemo(() => {
    const direction = sortDirection === "asc" ? 1 : -1;

    return [...filteredLibraryItems].sort((left, right) => {
      if (sortMode === "title") {
        return direction * left.Name.localeCompare(right.Name);
      }

      if (sortMode === "dateAdded") {
        return direction * (getDateCreatedMs(left) - getDateCreatedMs(right)) || left.Name.localeCompare(right.Name);
      }

      if (sortMode === "duration") {
        return compareOptionalNumber(getDurationTicks(left), getDurationTicks(right), sortDirection) || left.Name.localeCompare(right.Name);
      }

      const modelCompare = getDisplayModelName(left, faceMetadata).localeCompare(getDisplayModelName(right, faceMetadata));
      if (modelCompare) return direction * modelCompare;
      const leftMatch = getFaceMatch(left, faceMetadata);
      const rightMatch = getFaceMatch(right, faceMetadata);
      return getStatusRank(leftMatch?.status) - getStatusRank(rightMatch?.status) || left.Name.localeCompare(right.Name);
    });
  }, [faceMetadata, filteredLibraryItems, sortDirection, sortMode]);
  const libraryPageCount = Math.max(1, Math.ceil(sortedLibraryItems.length / LIBRARY_PAGE_SIZE));
  const clampedLibraryPageIndex = Math.min(libraryPageIndex, libraryPageCount - 1);
  const visibleLibraryItems = useMemo(() => {
    const start = clampedLibraryPageIndex * LIBRARY_PAGE_SIZE;
    return sortedLibraryItems.slice(start, start + LIBRARY_PAGE_SIZE);
  }, [clampedLibraryPageIndex, sortedLibraryItems]);
  const libraryPageStart = sortedLibraryItems.length ? clampedLibraryPageIndex * LIBRARY_PAGE_SIZE + 1 : 0;
  const libraryPageEnd = Math.min(sortedLibraryItems.length, (clampedLibraryPageIndex + 1) * LIBRARY_PAGE_SIZE);
  const hasMoreLibraryItems = Boolean(data.libraryPaging?.hasMore);
  const loadedLibraryTotalLabel =
    data.libraryPaging?.total != null && data.libraryPaging.total > data.libraryItems.length
      ? `${data.libraryItems.length} loaded of ${data.libraryPaging.total}`
      : `${sortedLibraryItems.length}`;
  const isFullLibraryStatsScope =
    !selectedModelGroup &&
    !manualTagItemIds &&
    orientationFilter === "all" &&
    excludedCategorySet.size === 0;
  const knownLibraryVideoTotal =
    isFullLibraryStatsScope && typeof data.libraryPaging?.total === "number"
      ? data.libraryPaging.total
      : playableLibraryItems.length;
  const loadedLibraryVideoCount = playableLibraryItems.length;
  const continueWatchingItems = useMemo(() => {
    const seen = new Set<string>();
    return [...data.continueWatching, ...data.watchHistory, ...filteredLibraryItems]
      .filter((item) => {
        if (!itemMatchesActiveVideoFilters(item)) return false;
        if (seen.has(item.Id)) return false;
        seen.add(item.Id);
        return true;
      })
      .filter(hasResumeProgress)
      .sort((left, right) => {
        const leftDate = left.UserData?.LastPlayedDate ? new Date(left.UserData.LastPlayedDate).getTime() : 0;
        const rightDate = right.UserData?.LastPlayedDate ? new Date(right.UserData.LastPlayedDate).getTime() : 0;
        return rightDate - leftDate;
      })
      .slice(0, 14);
  }, [data.continueWatching, data.watchHistory, filteredLibraryItems, itemMatchesActiveVideoFilters]);
  const favoriteItems = useMemo(() => {
    const seen = new Set<string>();
    const sourceItems = [
      ...applyManualModelMapToItems(data.favorites.map(markItemAsFavorite), manualModelMap),
      ...modelAwareLibraryItems.filter((item) => item.UserData?.IsFavorite),
    ];
    return sourceItems
      .filter(isPlayableItem)
      .filter((item) => {
        if (!itemMatchesActiveVideoFilters(item)) return false;
        if (seen.has(item.Id)) return false;
        seen.add(item.Id);
        return true;
      })
      .sort((left, right) => left.Name.localeCompare(right.Name));
  }, [data.favorites, itemMatchesActiveVideoFilters, manualModelMap, modelAwareLibraryItems]);
  const favoritePageCount = Math.max(1, Math.ceil(favoriteItems.length / LIBRARY_PAGE_SIZE));
  const clampedFavoritePageIndex = Math.min(libraryPageIndex, favoritePageCount - 1);
  const visibleFavoriteItems = useMemo(() => {
    const start = clampedFavoritePageIndex * LIBRARY_PAGE_SIZE;
    return favoriteItems.slice(start, start + LIBRARY_PAGE_SIZE);
  }, [clampedFavoritePageIndex, favoriteItems]);
  const favoritePageStart = favoriteItems.length ? clampedFavoritePageIndex * LIBRARY_PAGE_SIZE + 1 : 0;
  const favoritePageEnd = Math.min(favoriteItems.length, (clampedFavoritePageIndex + 1) * LIBRARY_PAGE_SIZE);
  const hasMoreFavoriteItems = Boolean(data.favoritesPaging?.hasMore);
  const loadedFavoriteCount = Math.max(data.favorites.length, favoriteItems.length);
  const loadedFavoriteTotalLabel =
    data.favoritesPaging?.total != null && data.favoritesPaging.total > loadedFavoriteCount
      ? `${loadedFavoriteCount} loaded of ${data.favoritesPaging.total}`
      : `${favoriteItems.length}`;
  const favoriteCountLabel =
    data.favoritesPaging?.total != null && data.favoritesPaging.total > loadedFavoriteCount
      ? `${loadedFavoriteCount} loaded of ${getVideoCountLabel(data.favoritesPaging.total)}`
      : getVideoCountLabel(favoriteItems.length);
  const historyItems = useMemo(() => {
    const seen = new Set<string>();
    return [...data.continueWatching, ...data.watchHistory, ...filteredLibraryItems]
      .filter((item) => {
        if (!itemMatchesActiveVideoFilters(item)) return false;
        if (seen.has(item.Id)) return false;
        seen.add(item.Id);
        return Boolean(
          item.UserData?.LastPlayedDate ||
            item.UserData?.Played ||
            (item.UserData?.PlaybackPositionTicks && item.UserData.PlaybackPositionTicks > 0) ||
            (item.UserData?.PlayCount && item.UserData.PlayCount > 0),
        );
      })
      .sort((left, right) => getLastPlayedMs(right) - getLastPlayedMs(left) || left.Name.localeCompare(right.Name))
      .slice(0, 80);
  }, [data.continueWatching, data.watchHistory, filteredLibraryItems, itemMatchesActiveVideoFilters]);
  const libraryStats = [
    {
      label: "Videos",
      value: knownLibraryVideoTotal,
      detail: knownLibraryVideoTotal > loadedLibraryVideoCount ? `${loadedLibraryVideoCount} loaded` : undefined,
    },
    { label: "Models", value: modelGroups.length },
    { label: "Selected", value: sortedLibraryItems.length },
    { label: "Filtered out", value: scopedLibraryItems.length - filteredLibraryItems.length },
    { label: "Portrait", value: orientationCounts.portrait },
    { label: "Landscape", value: orientationCounts.landscape },
    { label: "Pics", value: visibleGalleryItems.length },
    { label: "Identified", value: playableLibraryItems.filter((item) => hasIdentifiedFace(getFaceMatch(item, faceMetadata))).length },
    { label: "Review", value: playableLibraryItems.filter((item) => getFaceMatch(item, faceMetadata)?.status === "needs_review").length },
    { label: "Unscanned", value: playableLibraryItems.filter((item) => getFaceMatch(item, faceMetadata)?.status === "unscanned").length },
    { label: "New", value: getNewThisWeekCount(playableLibraryItems) },
  ];
  const heroMeta = hero
    ? [hero.ProductionYear, hero.Type, hero.Genres?.slice(0, 2).join(" / ")].filter(Boolean).join(" / ")
    : "";
  const heroQueue =
    hero && data.featuredItems.some((item) => item.Id === hero.Id)
      ? data.featuredItems
      : hero && data.continueWatching.some((item) => item.Id === hero.Id)
        ? data.continueWatching
        : hero && data.latestAdded.some((item) => item.Id === hero.Id)
          ? data.latestAdded
          : data.libraryItems;
  const heroSource =
    hero && data.featuredItems.some((item) => item.Id === hero.Id)
      ? "Featured Anime"
      : hero && data.continueWatching.some((item) => item.Id === hero.Id)
        ? "Continue Watching"
      : hero && data.latestAdded.some((item) => item.Id === hero.Id)
        ? "Latest Added"
        : libraryTitle;
  const canPlayHero = hero ? isPlayableItem(hero) : false;
  const smartRescanSummary = smartRescan.summary;
  const hasSmartRescanProgress = typeof smartRescan.progress?.percent === "number";
  const smartRescanPercent = Math.max(0, Math.min(100, Math.round(smartRescan.progress?.percent ?? 0)));
  const smartRescanProgressText =
    typeof smartRescan.progress?.total === "number" && smartRescan.progress.total > 0
      ? `${smartRescan.progress.completed ?? 0} of ${smartRescan.progress.total}`
      : "";
  const smartRescanModelProgressText =
    smartRescan.modelProgress && typeof smartRescan.modelProgress.total === "number"
      ? `${smartRescan.modelProgress.completed ?? 0} of ${smartRescan.modelProgress.total} models`
      : "";
  const smartRescanStatusLabel =
    smartRescan.status === "running"
      ? `${smartRescanPercent ? `${smartRescanPercent}% ` : ""}Smart scan`
      : smartRescan.status === "completed"
        ? `Smart scan done${typeof smartRescanSummary?.videos_scanned === "number" ? ` / ${smartRescanSummary.videos_scanned} videos` : ""}`
        : smartRescan.status === "failed"
          ? "Smart scan failed"
          : "Smart scan";

  const loadGallery = useCallback(async () => {
    try {
      const nextGallery = await client.getGallery();
      setGalleryData(nextGallery);
      setGalleryError("");
    } catch {
      setGalleryData(null);
      setGalleryError("Gallery is unavailable; uploaded pictures will appear after the organizer gallery index is reachable.");
    }
  }, [client]);

  const loadManualTags = useCallback(async () => {
    try {
      const response = await fetch("/api/spiritflix/tags?includeItems=1", { cache: "no-store" });
      if (!response.ok) throw new Error("Manual tags unavailable.");
      const body = (await response.json()) as SpiritFlixManualTagIndex & { items?: SpiritFlixManualTagRecord[] };
      setManualTagIndex(body);
      setManualTagRecords(body.items ?? []);
      setManualTagsError("");
    } catch {
      setManualTagIndex(null);
      setManualTagRecords([]);
      setManualTagsError("Manual tags are unavailable right now.");
    }
  }, []);

  const loadManualModels = useCallback(async () => {
    try {
      const response = await fetch("/api/spiritflix/model-index?includeItems=1", { cache: "no-store" });
      if (!response.ok) throw new Error("Manual models unavailable.");
      const body = (await response.json()) as SpiritFlixManualModelIndex & { items?: SpiritFlixManualModelRecord[] };
      setManualModelIndex(body);
      setManualModelRecords(body.items ?? []);
    } catch {
      setManualModelIndex(null);
      setManualModelRecords([]);
    }
  }, []);

  const handleRefresh = useCallback(() => {
    onRefresh();
    if (isLibraryDashboardView) {
      void loadGallery();
      void loadManualTags();
      void loadManualModels();
    }
  }, [isLibraryDashboardView, loadGallery, loadManualModels, loadManualTags, onRefresh]);

  const refreshSmartRescanStatus = useCallback(async () => {
    try {
      const response = await fetch("/api/spiritflix/library-smart-rescan", { cache: "no-store" });
      if (!response.ok) throw new Error("Smart rescan status unavailable.");
      const body = normalizeSmartRescanState(await response.json());
      setSmartRescan(body);
      setSmartRescanError("");
      if (body.status === "completed") {
        handleRefresh();
      }
    } catch {
      setSmartRescanError("Smart rescan status is unavailable.");
    }
  }, [handleRefresh]);

  const startSmartRescan = async () => {
    if (smartRescan.status === "running") return;
    setSmartRescanError("");
    setSmartRescan((current) => ({ ...current, status: "running" }));
    try {
      const response = await fetch("/api/spiritflix/library-smart-rescan", {
        method: "POST",
        cache: "no-store",
      });
      const rawBody = await response.json();
      const body = normalizeSmartRescanState(rawBody);
      if (!response.ok) throw new Error((rawBody as { error?: string })?.error || "Smart rescan could not start.");
      setSmartRescan(body);
    } catch (error) {
      setSmartRescan((current) => ({ ...current, status: "failed", error: error instanceof Error ? error.message : "Smart rescan could not start." }));
      setSmartRescanError(error instanceof Error ? error.message : "Smart rescan could not start.");
    }
  };

  useEffect(() => {
    if (!isLibraryDashboardView) return undefined;
    void refreshSmartRescanStatus();
    return undefined;
  }, [isLibraryDashboardView, refreshSmartRescanStatus]);

  useEffect(() => {
    if (!isLibraryDashboardView || smartRescan.status !== "running") return undefined;
    const timer = window.setInterval(() => {
      void refreshSmartRescanStatus();
    }, 10000);
    return () => window.clearInterval(timer);
  }, [isLibraryDashboardView, refreshSmartRescanStatus, smartRescan.status]);

  const closeFiltersOnCoarsePointer = () => {
    if (typeof window.matchMedia === "function" && window.matchMedia("(max-width: 760px), (pointer: coarse)").matches) {
      setFiltersOpen(false);
    }
  };

  useEffect(() => {
    if (!isLibraryDashboardView) return undefined;
    return scheduleDeferredHomeTask(() => {
      void loadGallery();
    });
  }, [isLibraryDashboardView, loadGallery]);

  useEffect(() => {
    if (!isLibraryDashboardView) return undefined;
    const cancelDeferredLoad = scheduleDeferredHomeTask(() => {
      void loadManualTags();
      void loadManualModels();
    });
    const handleManualTagsChanged = () => {
      void loadManualTags();
    };
    const handleManualModelsChanged = () => {
      void loadManualModels();
    };
    window.addEventListener("spiritflix:manual-tags-changed", handleManualTagsChanged);
    window.addEventListener("spiritflix:manual-models-changed", handleManualModelsChanged);
    return () => {
      cancelDeferredLoad();
      window.removeEventListener("spiritflix:manual-tags-changed", handleManualTagsChanged);
      window.removeEventListener("spiritflix:manual-models-changed", handleManualModelsChanged);
    };
  }, [isLibraryDashboardView, loadManualModels, loadManualTags]);

  useEffect(() => {
    if (!isLibraryDashboardView || !data.selectedLibraryId) {
      setFullLibraryItems([]);
      return undefined;
    }
    const controller = new AbortController();
    let cancelled = false;
    setFullLibraryItems([]);
    void client
      .getAllLibraryItems(data.selectedLibraryId, {
        searchTerm,
        fields: "full",
        signal: controller.signal,
      })
      .then((items) => {
        if (!cancelled) setFullLibraryItems(items);
      })
      .catch(() => {
        if (!cancelled) setFullLibraryItems([]);
      });
    return () => {
      cancelled = true;
      controller.abort();
    };
  }, [client, data.selectedLibraryId, isLibraryDashboardView, searchTerm]);

  useEffect(() => {
    const queries = [
      window.matchMedia("(max-width: 980px)"),
      window.matchMedia("(pointer: coarse)"),
    ];
    const updateMode = () => setPlayPrimaryTapOnMobile(queries.some((query) => query.matches));

    updateMode();
    queries.forEach((query) => query.addEventListener("change", updateMode));
    return () => queries.forEach((query) => query.removeEventListener("change", updateMode));
  }, []);

  useEffect(() => {
    window.localStorage.setItem(LIBRARY_VIEW_MODE_KEY, viewMode);
  }, [viewMode]);

  useEffect(() => {
    window.localStorage.setItem(LIBRARY_SORT_MODE_KEY, sortMode);
  }, [sortMode]);

  useEffect(() => {
    window.localStorage.setItem(LIBRARY_SORT_DIRECTION_KEY, sortDirection);
  }, [sortDirection]);

  useEffect(() => {
    window.localStorage.setItem(LIBRARY_ORIENTATION_FILTER_KEY, orientationFilter);
  }, [orientationFilter]);

  useEffect(() => {
    if (!data.libraries.length || !isLibraryDashboardView) return;
    window.localStorage.setItem(
      LIBRARY_UI_STATE_KEY,
      JSON.stringify({
        selectedLibraryId: data.selectedLibraryId,
        selectedModel,
        selectedManualTag,
        excludedCategories,
        viewMode,
        sortMode,
        sortDirection,
        orientationFilter,
        filtersOpen,
        pageIndex: clampedLibraryPageIndex,
      } satisfies StoredLibraryUiState),
    );
  }, [
    clampedLibraryPageIndex,
    data.libraries.length,
    data.selectedLibraryId,
    excludedCategories,
    filtersOpen,
    isLibraryDashboardView,
    orientationFilter,
    selectedManualTag,
    selectedModel,
    sortDirection,
    sortMode,
    viewMode,
  ]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      if (initialModelName) {
        setSelectedModel(initialModelName);
        return;
      }
      if (storedLibraryUiState.selectedLibraryId === data.selectedLibraryId) {
        setSelectedModel(storedLibraryUiState.selectedModel ?? null);
        return;
      }
      setSelectedModel(null);
    }, 0);
    return () => window.clearTimeout(timer);
  }, [data.selectedLibraryId, initialModelName, storedLibraryUiState]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      if (initialManualTag) {
        setSelectedManualTag(initialManualTag);
        return;
      }
      if (storedLibraryUiState.selectedLibraryId === data.selectedLibraryId) {
        setSelectedManualTag(storedLibraryUiState.selectedManualTag ?? null);
        return;
      }
      setSelectedManualTag(null);
    }, 0);
    return () => window.clearTimeout(timer);
  }, [data.selectedLibraryId, initialManualTag, storedLibraryUiState.selectedLibraryId, storedLibraryUiState.selectedManualTag]);

  useEffect(() => {
    if (!didRunPageResetRef.current) {
      didRunPageResetRef.current = true;
      return;
    }
    setLibraryPageIndex(0);
  }, [data.selectedLibraryId, excludedCategories, orientationFilter, selectedManualTag, selectedModel, sortDirection, sortMode, viewMode, searchTerm]);

  useEffect(() => {
    if (libraryPageIndex !== clampedLibraryPageIndex) setLibraryPageIndex(clampedLibraryPageIndex);
  }, [clampedLibraryPageIndex, libraryPageIndex]);

  useEffect(() => {
    if (!selectedModel || !modelGroups.length) return;
    if (modelGroups.some((model) => model.name === selectedModel)) return;
    setSelectedModel(null);
    onSelectModel(null);
  }, [modelGroups, onSelectModel, selectedModel]);

  const selectModel = (modelName: string | null) => {
    setSelectedModel(modelName);
    onSelectModel(modelName);
  };

  const selectManualTag = (tag: string | null) => {
    setSelectedManualTag(tag);
    if (!data.selectedLibraryId) return;
    const query = new URLSearchParams();
    query.set("library", data.selectedLibraryId);
    if (selectedModel) query.set("model", selectedModel);
    if (tag) query.set("tag", tag);
    window.history.pushState(window.history.state, "", `/spiritflix?${query.toString()}`);
  };

  const toggleExcludedCategory = (category: string) => {
    setExcludedCategories((current) =>
      current.includes(category)
        ? current.filter((candidate) => candidate !== category)
        : [...current, category],
    );
  };

  useEffect(() => {
    if (isHomeView || isAnimeView || !playableLibraryItems.length) {
      setFaceMetadata(null);
      setFaceMetadataError("");
      return undefined;
    }

    let isCancelled = false;
    const cacheKey = `${FACE_METADATA_CACHE_KEY}:${data.selectedLibraryId}:${playableLibraryItems.map((item) => item.Id).join(",")}`;
    const cached = window.localStorage.getItem(cacheKey);
    if (cached) {
      try {
        setFaceMetadata(JSON.parse(cached) as FaceOrganizerMetadataResponse);
      } catch {
        window.localStorage.removeItem(cacheKey);
      }
    }

    void client
      .getFaceOrganizerMetadata(playableLibraryItems)
      .then((metadata) => {
        if (isCancelled) return;
        setFaceMetadata(metadata);
        setFaceMetadataError("");
        window.localStorage.setItem(cacheKey, JSON.stringify(metadata));
      })
      .catch(() => {
        if (!isCancelled) setFaceMetadataError("Face Organizer metadata is unavailable; using Jellyfin model hints.");
      });

    return () => {
      isCancelled = true;
    };
  }, [client, data.selectedLibraryId, isAnimeView, isHomeView, playableLibraryItems]);

  const filterLibraryShuffleItems = useCallback(
    (items: JellyfinItem[]) => {
      const playableItems = applyManualModelMapToItems(items, manualModelMap).filter(isPlayableItem);
      const scopedItems = selectedModelGroup
        ? buildModelGroups(playableItems, faceMetadata).find((group) => group.name === selectedModelGroup.name)?.items ?? []
        : playableItems;
      return filterItemsByVideoOrientation(scopedItems, orientationFilter)
        .filter((item) => getItemCategoryKeys(item).every((category) => !excludedCategorySet.has(category)))
        .filter((item) => (manualTagItemIds ? manualTagItemIds.has(item.Id) : true));
    },
    [excludedCategorySet, faceMetadata, manualModelMap, manualTagItemIds, orientationFilter, selectedModelGroup],
  );

  const playShuffle = async (scope: "library" | "model") => {
    if (isLibraryShuffleLoading) return;
    let sourceItems =
      scope === "model" && selectedModelGroup
        ? filterItemsByVideoOrientation(selectedModelGroup.items, orientationFilter).filter((item) =>
            getItemCategoryKeys(item).every((category) => !excludedCategorySet.has(category)) &&
            (manualTagItemIds ? manualTagItemIds.has(item.Id) : true),
          )
        : filteredLibraryItems;

    if (scope === "library" && data.selectedLibraryId && data.libraryPaging?.hasMore) {
      setIsLibraryShuffleLoading(true);
      try {
        sourceItems = filterLibraryShuffleItems(
          await client.getAllLibraryItems(data.selectedLibraryId, {
            searchTerm,
            fields: "full",
          }),
        );
      } finally {
        setIsLibraryShuffleLoading(false);
      }
    }

    const shuffled = shuffleItems(sourceItems);
    const firstItem = shuffled[0];
    if (firstItem) {
      const sourceTitle = scope === "model" && selectedModelGroup ? selectedModelGroup.name : libraryTitle;
      const orientationLabel = orientationFilter === "all" ? "" : ` / ${getOrientationFilterLabel(orientationFilter)}`;
      onPlay(firstItem, shuffled, `${sourceTitle}${orientationLabel} Shuffle`);
    }
  };

  const clearLongPressTimer = () => {
    if (longPressTimerRef.current) {
      window.clearTimeout(longPressTimerRef.current);
      longPressTimerRef.current = null;
    }
  };

  const startShuffleLongPress = () => {
    didLongPressShuffleRef.current = false;
    if (!selectedModelGroup) return;
    clearLongPressTimer();
    longPressTimerRef.current = window.setTimeout(() => {
      longPressTimerRef.current = null;
      didLongPressShuffleRef.current = true;
      void playShuffle("model");
    }, 520);
  };

  const handleShuffleClick = () => {
    if (didLongPressShuffleRef.current) {
      didLongPressShuffleRef.current = false;
      return;
    }
    void playShuffle("library");
  };

  const scrollRow = (ref: { current: HTMLDivElement | null }, direction: "left" | "right") => {
    const node = ref.current;
    if (!node) return;
    const distance = Math.max(260, node.clientWidth * 0.82);
    node.scrollBy({ left: direction === "left" ? -distance : distance, behavior: "smooth" });
  };

  return (
    <section className="spiritflix-home">
      <header className="spiritflix-topbar">
        <div className="spiritflix-brand spiritflix-brand--compact">
          <span className="spiritflix-brand__sigil">SF</span>
          <span>SpiritFlix</span>
        </div>
        <nav className="spiritflix-topbar__links" aria-label="SpiritFlix sections">
          <button type="button" className={isHomeView ? "is-active" : undefined} onClick={onSelectHome}>
            Home
          </button>
          {data.libraries.map((library) => (
            <button
              key={library.Id}
              type="button"
              className={library.Id === data.selectedLibraryId ? "is-active" : undefined}
              aria-current={library.Id === data.selectedLibraryId ? "page" : undefined}
              onClick={() => onSelectLibrary(library.Id)}
            >
              {displayLibraryName(library.Name)}
            </button>
          ))}
        </nav>
        <div className="spiritflix-search">
          <Search size={17} aria-hidden="true" />
          <input
            value={searchTerm}
            onChange={(event) => onSearch(event.target.value)}
            placeholder="Search your Jellyfin library"
          />
        </div>
        <div className="spiritflix-topbar__controls">
          <button className="spiritflix-source-pill" type="button" onClick={handleRefresh} title="Refresh Jellyfin source">
            <Server size={15} aria-hidden="true" />
            <span>{serverInfo?.ServerName ?? "Jellyfin"}</span>
          </button>
          <button className="spiritflix-icon-button" type="button" onClick={handleRefresh} aria-label="Refresh library">
            <RefreshCw size={18} aria-hidden="true" />
          </button>
          <button className="spiritflix-icon-button" type="button" onClick={onLogout} aria-label="Switch source or sign out">
            <Settings size={18} aria-hidden="true" />
          </button>
          <button className="spiritflix-logout" type="button" onClick={onLogout}>
            <LogOut size={17} aria-hidden="true" />
            <span>{session.username}</span>
          </button>
        </div>
      </header>

      {!isAnimeView ? (
      <section className={`spiritflix-hero ${hero ? "" : "spiritflix-hero--empty"}`}>
        {hero ? (
          <>
            <SpiritFlixImage client={client} item={hero} type="Primary" width={700} className="spiritflix-hero__ambient" priority />
            <SpiritFlixImage client={client} item={hero} type="Backdrop" width={1600} className="spiritflix-hero__image" priority />
          </>
        ) : null}
        <div className="spiritflix-hero__shade" />
        <div className="spiritflix-hero__content">
          <span className="spiritflix-kicker">
            <Sparkles size={14} aria-hidden="true" />
            {serverInfo?.ServerName ? `${serverInfo.ServerName} / ${libraryTitle}` : libraryTitle}
          </span>
          <h1>{hero?.Name ?? "Your cinema is waiting"}</h1>
          {heroMeta ? <div className="spiritflix-hero__meta">{heroMeta}</div> : null}
          <p>{hero?.Overview || "Choose a library and stream from your real Jellyfin server."}</p>
          <div className="spiritflix-hero__actions">
            {hero ? (
              <>
                {canPlayHero ? (
                  <button
                    className="spiritflix-primary-button"
                    type="button"
                    onClick={() => onPlay(hero, heroQueue, heroSource, hasResumeProgress(hero) ? getResumePositionTicks(hero) : undefined)}
                  >
                    {hasResumeProgress(hero) ? (
                      <RotateCcw size={19} aria-hidden="true" />
                    ) : (
                      <Play size={19} fill="currentColor" aria-hidden="true" />
                    )}
                    {hasResumeProgress(hero) ? `Resume from ${getResumeSlotLabel(hero).split(" / ")[0]}` : "Play"}
                  </button>
                ) : null}
                <button className="spiritflix-secondary-button" type="button" onClick={() => onOpenDetails(hero)}>
                  Details
                </button>
              </>
            ) : null}
          </div>
        </div>
      </section>
      ) : null}

      {error ? <p className="spiritflix-error spiritflix-error--home">{error}</p> : null}
      {isPendingInitialContent ? <div className="spiritflix-loading" data-spiritflix-useful-content="pending">Loading live Jellyfin rows...</div> : null}

      <div className={`spiritflix-rows ${isAnimeView ? "spiritflix-rows--anime" : ""}`} data-spiritflix-useful-content={hasUsefulHomeContent ? "ready" : "pending"}>
        {!isPendingInitialContent && isLibraryDashboardView ? (
          <section className="spiritflix-library-v2" aria-label={`${libraryTitle} model library`}>
            <div className="spiritflix-library-v2__header">
              <div>
                <span className="spiritflix-kicker">
                  <Sparkles size={14} aria-hidden="true" />
                  {libraryTitle}
                </span>
                <h2>
                  {viewMode === "models"
                    ? "Models"
                    : viewMode === "favorites"
                      ? "Favorites"
                    : viewMode === "gallery"
                      ? selectedModelGroup
                        ? `${selectedModelGroup.name} Pics`
                        : "Gallery"
                      : selectedModelGroup?.name ?? "All Models"}
                </h2>
                {viewMode === "favorites" ? <span className="spiritflix-library-v2__count">{favoriteCountLabel}</span> : null}
              </div>
              <div className="spiritflix-view-toggle" aria-label="Library view">
                <button
                  type="button"
                  className={viewMode === "grid" ? "is-active" : undefined}
                  aria-pressed={viewMode === "grid"}
                  onClick={() => setViewMode("grid")}
                >
                  <Grid2X2 size={18} aria-hidden="true" />
                  <span>Grid</span>
                </button>
                <button
                  type="button"
                  className={viewMode === "list" ? "is-active" : undefined}
                  aria-pressed={viewMode === "list"}
                  onClick={() => setViewMode("list")}
                >
                  <List size={19} aria-hidden="true" />
                  <span>List</span>
                </button>
                <button
                  type="button"
                  className={viewMode === "history" ? "is-active" : undefined}
                  aria-pressed={viewMode === "history"}
                  onClick={() => setViewMode("history")}
                >
                  <Clock3 size={18} aria-hidden="true" />
                  <span>History</span>
                </button>
                <button
                  type="button"
                  className={viewMode === "favorites" ? "is-active" : undefined}
                  aria-pressed={viewMode === "favorites"}
                  onClick={() => setViewMode("favorites")}
                >
                  <Heart size={18} aria-hidden="true" />
                  <span>Favorites</span>
                </button>
                <button
                  type="button"
                  className={viewMode === "gallery" ? "is-active" : undefined}
                  aria-pressed={viewMode === "gallery"}
                  onClick={() => setViewMode("gallery")}
                >
                  <Images size={18} aria-hidden="true" />
                  <span>Gallery</span>
                </button>
                <button
                  type="button"
                  className={viewMode === "models" ? "is-active" : undefined}
                  aria-pressed={viewMode === "models"}
                  onClick={() => setViewMode("models")}
                >
                  <Sparkles size={18} aria-hidden="true" />
                  <span>Models</span>
                </button>
              </div>
            </div>

            {selectedModelGroup && selectedModelGalleryItems.length ? (
              <div className="spiritflix-model-tabs" aria-label={`${selectedModelGroup.name} media tabs`}>
                <button
                  type="button"
                  className={viewMode !== "gallery" ? "is-active" : undefined}
                  aria-pressed={viewMode !== "gallery"}
                  onClick={() => setViewMode("grid")}
                >
                  Videos
                </button>
                <button
                  type="button"
                  className={viewMode === "gallery" ? "is-active" : undefined}
                  aria-pressed={viewMode === "gallery"}
                  onClick={() => setViewMode("gallery")}
                >
                  Pics
                </button>
              </div>
            ) : null}

            <div className="spiritflix-library-modebar">
              <button
                type="button"
                className="spiritflix-filter-trigger"
                aria-expanded={filtersOpen}
                onClick={() => setFiltersOpen((current) => !current)}
              >
                <SlidersHorizontal size={18} aria-hidden="true" />
                <span>
                  {getOrientationFilterLabel(orientationFilter)} / {getSortModeLabel(sortMode)}
                  {excludedCategories.length ? ` / ${excludedCategories.length} off` : ""}
                </span>
              </button>
              <button
                type="button"
                className="spiritflix-smart-rescan-button"
                onClick={startSmartRescan}
                disabled={smartRescan.status === "running"}
                aria-label="Run smart model and video rescan"
              >
                <RefreshCw size={18} aria-hidden="true" className={smartRescan.status === "running" ? "is-spinning" : undefined} />
                <span>{smartRescanStatusLabel}</span>
              </button>
            </div>

            <AnimatePresence>
              {filtersOpen ? (
                <motion.div
                  className="spiritflix-filter-popout"
                  initial={{ opacity: 0, y: -8, scale: 0.98 }}
                  animate={{ opacity: 1, y: 0, scale: 1 }}
                  exit={{ opacity: 0, y: -8, scale: 0.98 }}
                  transition={{ duration: 0.16 }}
                >
                  <div className="spiritflix-filter-popout__header">
                    <strong>Filters</strong>
                    <button type="button" onClick={() => setFiltersOpen(false)} aria-label="Close filters">
                      Done
                    </button>
                  </div>
                  <div className="spiritflix-filter-popout__section">
                    <span>Video shape</span>
                    <div className="spiritflix-filter-options spiritflix-filter-options--three">
                      {([
                        ["all", "All", playableLibraryItems.length],
                        ["portrait", "Portrait", orientationCounts.portrait],
                        ["landscape", "Landscape", orientationCounts.landscape],
                      ] as const).map(([value, label, count]) => (
                        <button
                          key={value}
                          type="button"
                          className={orientationFilter === value ? "is-active" : undefined}
                          aria-pressed={orientationFilter === value}
                          onClick={() => {
                            setOrientationFilter(value);
                            closeFiltersOnCoarsePointer();
                          }}
                        >
                          {label}
                          <span>{count}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                  <div className="spiritflix-filter-popout__section">
                    <span>Exclude categories</span>
                    <div className="spiritflix-filter-options spiritflix-filter-options--two">
                      {categoryFilters.map((category) => (
                        <button
                          key={category.key}
                          type="button"
                          className={excludedCategorySet.has(category.key) ? "is-excluded" : undefined}
                          aria-pressed={excludedCategorySet.has(category.key)}
                          disabled={category.count === 0}
                          onClick={() => toggleExcludedCategory(category.key)}
                        >
                          {excludedCategorySet.has(category.key) ? "Show" : "Hide"} {category.label}
                          <span>{category.count}</span>
                        </button>
                      ))}
                    </div>
                  </div>
                  <div className="spiritflix-filter-popout__section">
                    <span>Sort</span>
                    <div className="spiritflix-filter-options">
                      {[
                        ["model", "Model"],
                        ["dateAdded", "Last added"],
                        ["duration", "Duration"],
                        ["title", "Title"],
                      ].map(([value, label]) => (
                        <button
                          key={value}
                          type="button"
                          className={sortMode === value ? "is-active" : undefined}
                          aria-pressed={sortMode === value}
                          onClick={() => {
                            setSortMode(value as LibrarySortMode);
                            closeFiltersOnCoarsePointer();
                          }}
                        >
                          {label}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div className="spiritflix-filter-popout__section">
                    <span>Order</span>
                    <div className="spiritflix-filter-options spiritflix-filter-options--two">
                      <button
                        type="button"
                        className={sortDirection === "desc" ? "is-active" : undefined}
                        aria-pressed={sortDirection === "desc"}
                        onClick={() => {
                          setSortDirection("desc");
                          closeFiltersOnCoarsePointer();
                        }}
                      >
                        Descending
                      </button>
                      <button
                        type="button"
                        className={sortDirection === "asc" ? "is-active" : undefined}
                        aria-pressed={sortDirection === "asc"}
                        onClick={() => {
                          setSortDirection("asc");
                          closeFiltersOnCoarsePointer();
                        }}
                      >
                        Ascending
                      </button>
                    </div>
                  </div>
                </motion.div>
              ) : null}
            </AnimatePresence>

            <div className="spiritflix-library-stats" aria-label="Library stats">
              {libraryStats.map((stat) => (
                <div key={stat.label} className="spiritflix-library-stat">
                  <strong>{stat.value}</strong>
                  <span>{stat.label}</span>
                  {stat.detail ? <em>{stat.detail}</em> : null}
                </div>
              ))}
            </div>
            {smartRescan.status !== "idle" || smartRescanError ? (
              <div className={`spiritflix-smart-rescan-note is-${smartRescan.status}`}>
                <div className="spiritflix-smart-rescan-note__head">
                  <strong>
                    {smartRescanError ||
                      smartRescan.error ||
                      smartRescan.phaseLabel ||
                      (smartRescan.status === "completed" ? "Smart scan completed" : "Smart model scan")}
                  </strong>
                  {smartRescan.status === "running" && hasSmartRescanProgress ? <span>{smartRescanPercent}%</span> : null}
                </div>
                {smartRescan.status === "running" ? (
                  <>
                    <div
                      className={`spiritflix-smart-rescan-progress ${hasSmartRescanProgress ? "" : "is-indeterminate"}`}
                      role="progressbar"
                      aria-valuemin={0}
                      aria-valuemax={100}
                      aria-valuenow={hasSmartRescanProgress ? smartRescanPercent : undefined}
                    >
                      <span style={{ width: hasSmartRescanProgress ? `${smartRescanPercent}%` : undefined }} />
                    </div>
                    <div className="spiritflix-smart-rescan-preview">
                      <span>{smartRescan.currentItem?.kind === "model" ? "Model" : smartRescan.currentItem?.kind === "video" ? "Video" : "Now"}</span>
                      <strong>{smartRescan.currentItem?.preview || smartRescan.currentItem?.name || "Loading next item..."}</strong>
                      {smartRescanProgressText || smartRescanModelProgressText ? (
                        <em>{[smartRescanProgressText, smartRescanModelProgressText].filter(Boolean).join(" / ")}</em>
                      ) : null}
                    </div>
                  </>
                ) : smartRescan.status === "completed" ? (
                  <span>
                    {smartRescanSummary?.smart_accepts?.length ?? 0} model face pick updates; {smartRescanSummary?.smart_accept_skips?.length ?? 0} model checks skipped.
                  </span>
                ) : null}
              </div>
            ) : null}
            {manualTagIndex?.tags.length ? (
              <section className="spiritflix-manual-tags-bar" aria-label="Manual tag filters">
                <div>
                  <Tag size={15} aria-hidden="true" />
                  <span>Manual tags</span>
                </div>
                <button
                  type="button"
                  className={!selectedManualTag ? "is-active" : undefined}
                  aria-pressed={!selectedManualTag}
                  onClick={() => selectManualTag(null)}
                >
                  All
                </button>
                {manualTagIndex.tags.map((tag) => (
                  <button
                    key={tag.tag}
                    type="button"
                    className={selectedManualTag === tag.tag ? "is-active" : undefined}
                    aria-pressed={selectedManualTag === tag.tag}
                    onClick={() => selectManualTag(tag.tag)}
                  >
                    {tag.label}
                    <span>{tag.count}</span>
                  </button>
                ))}
                {selectedManualTag ? (
                  <button type="button" className="spiritflix-manual-tags-bar__clear" onClick={() => selectManualTag(null)}>
                    <X size={14} aria-hidden="true" />
                    Clear
                  </button>
                ) : null}
              </section>
            ) : null}
            {faceMetadataError ? <p className="spiritflix-face-note">{faceMetadataError}</p> : null}
            {galleryError ? <p className="spiritflix-face-note">{galleryError}</p> : null}
            {manualTagsError ? <p className="spiritflix-face-note">{manualTagsError}</p> : null}

            {viewMode !== "gallery" && viewMode !== "history" && viewMode !== "favorites" && viewMode !== "models" && continueWatchingItems.length ? (
              <section className="spiritflix-resume-section" aria-label="Continue Watching">
                <div className="spiritflix-resume-section__header">
                  <button
                    type="button"
                    className="spiritflix-section-title-button"
                    onClick={() => setViewMode("history")}
                    aria-label="Open Continue Watching videos"
                  >
                    <h3>Continue Watching</h3>
                    <span>Private Jellyfin lane / {selectedModelGroup?.name ?? libraryTitle}</span>
                    <ChevronRight size={18} aria-hidden="true" />
                  </button>
                  <div className="spiritflix-row-controls" aria-label="Scroll Continue Watching">
                    <button type="button" onClick={() => scrollRow(resumeTrackRef, "left")} aria-label="Scroll Continue Watching left">
                      <ChevronLeft size={22} aria-hidden="true" />
                    </button>
                    <button type="button" onClick={() => scrollRow(resumeTrackRef, "right")} aria-label="Scroll Continue Watching right">
                      <ChevronRight size={22} aria-hidden="true" />
                    </button>
                  </div>
                </div>
                <div className="spiritflix-resume-track" ref={resumeTrackRef}>
                  {continueWatchingItems.map((item) => {
                    const progress = getResumeProgressPercent(item);
                    const resumeTicks = getResumePositionTicks(item);
                    const timeLeft = getTimeLeftLabel(item);
                    return (
                      <motion.button
                        key={item.Id}
                        type="button"
                        className="spiritflix-resume-card"
                        onClick={() => onPlay(item, continueWatchingItems, "Continue Watching", resumeTicks)}
                        whileTap={{ scale: 0.985 }}
                        aria-label={`Resume ${item.Name} at ${getResumeSlotLabel(item)}`}
                      >
                        <span className="spiritflix-resume-card__thumb">
                          <SpiritFlixImage client={client} item={item} type="Thumb" width={420} alt="" />
                        </span>
                          <span className="spiritflix-resume-card__copy">
                          <strong>{getDisplayModelName(item, faceMetadata)}</strong>
                          <small>{item.Name}</small>
                          <span>{getResumeSlotLabel(item)}</span>
                          {timeLeft ? <em>{timeLeft}</em> : null}
                        </span>
                        <span className="spiritflix-resume-card__progress" aria-hidden="true">
                          <span style={{ width: `${progress}%` }} />
                        </span>
                      </motion.button>
                    );
                  })}
                </div>
              </section>
            ) : null}

            {viewMode !== "gallery" && viewMode !== "history" && viewMode !== "favorites" && viewMode !== "models" ? (
              <SpiritFlixRail
                title="Favorites"
                titleMeta={favoriteCountLabel}
                variant="poster"
                client={client}
                items={favoriteItems}
                playOnPrimaryTap={playPrimaryTapOnMobile}
                hasMore={hasMoreFavoriteItems}
                loadingMore={Boolean(loadingMore.favorites)}
                onLoadMore={onLoadMoreFavorites}
                onTitleClick={() => setViewMode("favorites")}
                titleActionLabel="Open Favorites videos"
                onOpenDetails={onOpenDetails}
                onPlay={onPlay}
                emptyText={`No favorites in ${selectedModelGroup?.name ?? libraryTitle} yet.`}
              />
            ) : null}

            {viewMode !== "history" && viewMode !== "favorites" && viewMode !== "models" ? (
            <section className="spiritflix-model-section" aria-label="Model filters">
              <div className="spiritflix-model-section__header">
                <button
                  type="button"
                  className="spiritflix-section-title-button spiritflix-section-title-button--compact"
                  onClick={() => setViewMode("models")}
                  aria-label="Open Models"
                >
                  <span>Models</span>
                  <ChevronRight size={17} aria-hidden="true" />
                </button>
                <div className="spiritflix-row-controls" aria-label="Scroll Models">
                  <button type="button" onClick={() => scrollRow(modelStripRef, "left")} aria-label="Scroll Models left">
                    <ChevronLeft size={22} aria-hidden="true" />
                  </button>
                  <button type="button" onClick={() => scrollRow(modelStripRef, "right")} aria-label="Scroll Models right">
                    <ChevronRight size={22} aria-hidden="true" />
                  </button>
                </div>
              </div>
              <div className="spiritflix-model-strip" ref={modelStripRef} aria-label="Models">
                <button
                  type="button"
                  className={`spiritflix-model-pill ${selectedModel === null ? "is-active" : ""}`}
                  onClick={() => selectModel(null)}
                >
                  All Models
                </button>
                {modelGroups.map((model) => {
                  const galleryCount = galleryItems.filter((item) => galleryItemMatchesModel(item, model.name)).length;
                  return (
                    <motion.button
                      layout
                      key={model.name}
                      type="button"
                      className={`spiritflix-model-card ${selectedModel === model.name ? "is-active" : ""}`}
                      onClick={() => selectModel(model.name)}
                      whileTap={{ scale: 0.98 }}
                    >
                      {model.representative ? (
                        <SpiritFlixImage client={client} item={model.representative} type="Primary" width={260} alt="" />
                      ) : (
                        <div className="spiritflix-model-card__placeholder" aria-hidden="true">
                          <Images size={24} />
                        </div>
                      )}
                      <span>
                        <strong>{model.name}</strong>
                        <small>{model.indexedCount} videos{galleryCount ? ` / ${galleryCount} pics` : ""}</small>
                      </span>
                    </motion.button>
                  );
                })}
              </div>
            </section>
            ) : null}

            <AnimatePresence mode="wait">
              {viewMode === "models" ? (
                <motion.div
                  key="models"
                  className="spiritflix-model-directory"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.18 }}
                >
                  <button
                    type="button"
                    className={`spiritflix-model-card spiritflix-model-card--all ${selectedModel === null ? "is-active" : ""}`}
                    onClick={() => {
                      selectModel(null);
                      setViewMode("grid");
                    }}
                  >
                    <span>
                      <strong>All Models</strong>
                      <small>{playableLibraryItems.length} videos / {modelGroups.length} models</small>
                    </span>
                  </button>
                  {modelGroups.map((model) => {
                    const galleryCount = galleryItems.filter((item) => galleryItemMatchesModel(item, model.name)).length;
                    return (
                      <motion.button
                        layout
                        key={model.name}
                        type="button"
                        className={`spiritflix-model-card ${selectedModel === model.name ? "is-active" : ""}`}
                        onClick={() => {
                          selectModel(model.name);
                          setViewMode("grid");
                        }}
                        whileTap={{ scale: 0.98 }}
                      >
                        {model.representative ? (
                          <SpiritFlixImage client={client} item={model.representative} type="Primary" width={320} alt="" />
                        ) : (
                          <div className="spiritflix-model-card__placeholder" aria-hidden="true">
                            <Images size={28} />
                          </div>
                        )}
                        <span>
                          <strong>{model.name}</strong>
                          <small>{model.indexedCount} videos{galleryCount ? ` / ${galleryCount} pics` : ""}</small>
                        </span>
                      </motion.button>
                    );
                  })}
                </motion.div>
              ) : viewMode === "gallery" ? (
                <motion.div
                  key="gallery"
                  className="spiritflix-gallery-grid"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.18 }}
                >
                  {visibleGalleryItems.map((item, index) => (
                    <GalleryCard
                      key={item.id}
                      item={item}
                      onOpen={() => setGalleryLightbox({ items: visibleGalleryItems, index })}
                    />
                  ))}
                </motion.div>
              ) : viewMode === "favorites" ? (
                <motion.div
                  key="favorites"
                  className="spiritflix-library-grid"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.18 }}
                >
                  {visibleFavoriteItems.map((item, index) => (
                    <LibraryFeedCard
                      key={item.Id}
                      client={client}
                      item={item}
                      manualTags={manualTagMap.get(item.Id)}
                      playOnPrimaryTap={playPrimaryTapOnMobile}
                      imagePriority={index < 6}
                      onOpenDetails={onOpenDetails}
                      onPlay={(selectedItem, startPositionTicks) =>
                        onPlay(selectedItem, favoriteItems, "Favorites", startPositionTicks)
                      }
                    />
                  ))}
                </motion.div>
              ) : viewMode === "grid" ? (
                <motion.div
                  key="grid"
                  className="spiritflix-library-grid"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.18 }}
                >
                  {visibleLibraryItems.map((item, index) => (
                    <LibraryFeedCard
                      key={item.Id}
                      client={client}
                      item={item}
                      manualTags={manualTagMap.get(item.Id)}
                      playOnPrimaryTap={playPrimaryTapOnMobile}
                      imagePriority={index < 6}
                      onOpenDetails={onOpenDetails}
                      onPlay={(selectedItem, startPositionTicks) =>
                        onPlay(selectedItem, visibleLibraryItems, selectedModelGroup?.name ?? libraryTitle, startPositionTicks)
                      }
                    />
                  ))}
                </motion.div>
              ) : viewMode === "list" ? (
                <motion.div
                  key="list"
                  className="spiritflix-library-list"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.18 }}
                >
                  {visibleLibraryItems.map((item) => (
                    <button
                      key={item.Id}
                      type="button"
                      className="spiritflix-library-row"
                      onClick={() => {
                        if (playPrimaryTapOnMobile && isPlayableItem(item)) {
                          onPlay(
                            item,
                            visibleLibraryItems,
                            selectedModelGroup?.name ?? libraryTitle,
                            hasResumeProgress(item) ? getResumePositionTicks(item) : undefined,
                          );
                        } else {
                          onOpenDetails(item);
                        }
                      }}
                    >
                      <span className="spiritflix-library-row__thumb">
                        <SpiritFlixImage client={client} item={item} type="Thumb" width={260} alt="" />
                      </span>
                      <span className="spiritflix-library-row__copy">
                        <strong>{item.Name}</strong>
                        <small>{getDisplayModelName(item, faceMetadata)}</small>
                        {manualTagMap.get(item.Id)?.filter((tag) => getSpiritFlixManualTagScope(tag) === "video").length ? (
                          <span className="spiritflix-library-row__tags">
                            {manualTagMap.get(item.Id)?.filter((tag) => getSpiritFlixManualTagScope(tag) === "video").slice(0, 5).map((tag) => (
                              <em key={tag}>{tag}</em>
                            ))}
                          </span>
                        ) : null}
                        <em className={`spiritflix-face-badge is-${getFaceMatch(item, faceMetadata)?.status ?? "unscanned"}`}>
                          {getFaceMatch(item, faceMetadata)?.label ?? "Unscanned"}
                        </em>
                        <span>{hasResumeProgress(item) ? getResumeSlotLabel(item) : `${formatRuntime(getDurationTicks(item))} / ${item.UserData?.PlayCount ?? 0} plays`}</span>
                        {hasResumeProgress(item) ? <em>Resume from {getResumeSlotLabel(item).split(" / ")[0]}</em> : null}
                      </span>
                      {isPlayableItem(item) ? (
                        <span
                          className="spiritflix-library-row__play"
                          onClick={(event) => {
                            event.stopPropagation();
                            onPlay(
                              item,
                              visibleLibraryItems,
                              selectedModelGroup?.name ?? libraryTitle,
                              hasResumeProgress(item) ? getResumePositionTicks(item) : undefined,
                            );
                          }}
                        >
                          <Play size={18} fill="currentColor" aria-hidden="true" />
                        </span>
                      ) : null}
                    </button>
                  ))}
                </motion.div>
              ) : (
                <motion.div
                  key="history"
                  className="spiritflix-library-list spiritflix-library-list--history"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.18 }}
                >
                  {historyItems.map((item) => (
                    <button
                      key={item.Id}
                      type="button"
                      className="spiritflix-library-row spiritflix-library-row--history"
                      onClick={() => {
                        if (isPlayableItem(item)) {
                          onPlay(
                            item,
                            historyItems,
                            "Watch History",
                            hasResumeProgress(item) ? getResumePositionTicks(item) : undefined,
                          );
                        } else {
                          onOpenDetails(item);
                        }
                      }}
                    >
                      <span className="spiritflix-library-row__thumb">
                        <SpiritFlixImage client={client} item={item} type="Thumb" width={260} alt="" />
                      </span>
                      <span className="spiritflix-library-row__copy">
                        <strong>{item.Name}</strong>
                        <small>{getDisplayModelName(item, faceMetadata)}</small>
                        <em>{getLastPlayedLabel(item)}</em>
                        <span>
                          {hasResumeProgress(item)
                            ? `${getResumeSlotLabel(item)} / ${getTimeLeftLabel(item)}`
                            : `${formatRuntime(getDurationTicks(item))} / ${item.UserData?.PlayCount ?? 0} plays`}
                        </span>
                      </span>
                      {isPlayableItem(item) ? (
                        <span
                          className="spiritflix-library-row__play"
                          onClick={(event) => {
                            event.stopPropagation();
                            onPlay(
                              item,
                              historyItems,
                              "Watch History",
                              hasResumeProgress(item) ? getResumePositionTicks(item) : undefined,
                            );
                          }}
                        >
                          <Play size={18} fill="currentColor" aria-hidden="true" />
                        </span>
                      ) : null}
                    </button>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>

            {(viewMode === "grid" || viewMode === "list") && sortedLibraryItems.length > LIBRARY_PAGE_SIZE ? (
              <div className="spiritflix-library-pager" aria-label="Library video pages">
                <button
                  type="button"
                  onClick={() => setLibraryPageIndex((page) => Math.max(0, page - 1))}
                  disabled={clampedLibraryPageIndex === 0}
                  aria-label="Previous video page"
                >
                  <ChevronLeft size={20} aria-hidden="true" />
                </button>
                <span>
                  Page {clampedLibraryPageIndex + 1} of {libraryPageCount} / {libraryPageStart}-{libraryPageEnd} of {loadedLibraryTotalLabel}
                </span>
                <button
                  type="button"
                  onClick={() => setLibraryPageIndex((page) => Math.min(libraryPageCount - 1, page + 1))}
                  disabled={clampedLibraryPageIndex >= libraryPageCount - 1}
                  aria-label="Next video page"
                >
                  <ChevronRight size={20} aria-hidden="true" />
                </button>
                {hasMoreLibraryItems ? (
                  <button
                    type="button"
                    onClick={onLoadMoreLibrary}
                    disabled={loadingMore.library}
                    aria-label="Load more library videos"
                  >
                    <ChevronRight size={20} aria-hidden="true" />
                  </button>
                ) : null}
              </div>
            ) : null}

            {viewMode === "favorites" && (favoriteItems.length > LIBRARY_PAGE_SIZE || hasMoreFavoriteItems) ? (
              <div className="spiritflix-library-pager" aria-label="Favorite video pages">
                <button
                  type="button"
                  onClick={() => setLibraryPageIndex((page) => Math.max(0, page - 1))}
                  disabled={clampedFavoritePageIndex === 0}
                  aria-label="Previous favorite video page"
                >
                  <ChevronLeft size={20} aria-hidden="true" />
                </button>
                <span>
                  Favorites {favoritePageStart}-{favoritePageEnd} of {loadedFavoriteTotalLabel}
                </span>
                <button
                  type="button"
                  onClick={() => setLibraryPageIndex((page) => Math.min(favoritePageCount - 1, page + 1))}
                  disabled={clampedFavoritePageIndex >= favoritePageCount - 1}
                  aria-label="Next favorite video page"
                >
                  <ChevronRight size={20} aria-hidden="true" />
                </button>
                {hasMoreFavoriteItems ? (
                  <button
                    type="button"
                    onClick={onLoadMoreFavorites}
                    disabled={loadingMore.favorites}
                    aria-label="Load more favorite videos"
                  >
                    <ChevronRight size={20} aria-hidden="true" />
                  </button>
                ) : null}
              </div>
            ) : null}

            {viewMode === "models" && !modelGroups.length ? (
              <p className="spiritflix-empty">No model groups found in {libraryTitle} yet.</p>
            ) : viewMode === "gallery" && !visibleGalleryItems.length ? (
              <p className="spiritflix-empty">No gallery pictures found for {selectedModelGroup?.name ?? "any model"} yet.</p>
            ) : viewMode === "history" && !historyItems.length ? (
              <p className="spiritflix-empty">No private watch history has synced for {selectedModelGroup?.name ?? libraryTitle} yet.</p>
            ) : viewMode === "favorites" && !favoriteItems.length ? (
              <p className="spiritflix-empty">No favorites in {selectedModelGroup?.name ?? libraryTitle} yet.</p>
            ) : (viewMode === "grid" || viewMode === "list") && !visibleLibraryItems.length ? (
              <p className="spiritflix-empty">{libraryTitle} has no indexed videos yet.</p>
            ) : null}

            {(viewMode === "grid" || viewMode === "list") ? (
              <motion.button
                type="button"
                className="spiritflix-shuffle-fab"
                onClick={handleShuffleClick}
                onPointerDown={startShuffleLongPress}
                onPointerUp={clearLongPressTimer}
                onPointerCancel={clearLongPressTimer}
                onContextMenu={(event) => {
                  event.preventDefault();
                  if (selectedModelGroup) void playShuffle("model");
                }}
                disabled={!filteredLibraryItems.length || isLibraryShuffleLoading}
                whileTap={{ scale: 0.97 }}
                aria-label={
                  selectedModelGroup
                    ? `Shuffle ${libraryTitle} ${getOrientationFilterLabel(orientationFilter)} videos; long press to shuffle ${selectedModelGroup.name}`
                    : `Shuffle ${libraryTitle} ${getOrientationFilterLabel(orientationFilter)} videos`
                }
              >
                <Shuffle size={21} aria-hidden="true" />
                <span>
                  <strong>Shuffle Gooner Mix</strong>
                  <small>{selectedModelGroup ? `Hold: ${selectedModelGroup.name}` : getOrientationFilterLabel(orientationFilter)}</small>
                </span>
              </motion.button>
            ) : null}
          </section>
        ) : null}
        {isAnimeView ? (
          <section className="spiritflix-anime-view" aria-label="Anime seasons and episodes">
            <section className={`spiritflix-anime-hero ${activeAnimeHero ? "" : "spiritflix-anime-hero--empty"}`}>
              {activeAnimeHero ? (
                <>
                  <SpiritFlixImage client={client} item={activeAnimeHero} type="Primary" width={700} className="spiritflix-anime-hero__ambient" priority />
                  <SpiritFlixImage client={client} item={activeAnimeHero} type="Backdrop" width={1600} className="spiritflix-anime-hero__image" priority />
                </>
              ) : null}
              <div className="spiritflix-anime-hero__shade" />
              <div className="spiritflix-anime-hero__content">
                <span className="spiritflix-kicker">
                  <Sparkles size={14} aria-hidden="true" />
                  {serverInfo?.ServerName ? `${serverInfo.ServerName} / Anime` : "Anime"}
                </span>
                <h1>{activeAnimeSeries?.seriesName ?? "Anime"}</h1>
                {activeAnimeSeries ? (
                  <div className="spiritflix-anime-hero__meta">
                    <span>{activeAnimeSeries.seasons.length} {activeAnimeSeries.seasons.length === 1 ? "season" : "seasons"}</span>
                    <span>{activeAnimeSeries.episodeCount} episodes</span>
                    {activeAnimeSeries.latestPlayedMs && activeAnimeLastWatchedItem ? <span>Last watched {getLastPlayedLabel(activeAnimeLastWatchedItem)}</span> : null}
                  </div>
                ) : null}
                {activeAnimeCurrentEpisode ? (
                  <div className="spiritflix-anime-now">
                    <button
                      className="spiritflix-anime-now__play"
                      type="button"
                      onClick={() =>
                        onPlay(
                          activeAnimeCurrentEpisode,
                          activeAnimeEpisodes,
                          activeAnimeSeries?.seriesName ?? "Anime",
                          hasResumeProgress(activeAnimeCurrentEpisode) ? getResumePositionTicks(activeAnimeCurrentEpisode) : undefined,
                        )
                      }
                    >
                      {hasResumeProgress(activeAnimeCurrentEpisode) ? (
                        <RotateCcw size={19} aria-hidden="true" />
                      ) : (
                        <Play size={19} fill="currentColor" aria-hidden="true" />
                      )}
                      <span>{hasResumeProgress(activeAnimeCurrentEpisode) ? `Resume ${formatAnimeEpisodeLabel(activeAnimeCurrentEpisode)}` : `Play ${formatAnimeEpisodeLabel(activeAnimeCurrentEpisode)}`}</span>
                    </button>
                    <div className="spiritflix-anime-now__copy">
                      <strong>{getAnimeEpisodeTitle(activeAnimeCurrentEpisode)}</strong>
                      <small>
                        {hasResumeProgress(activeAnimeCurrentEpisode)
                          ? getResumeSlotLabel(activeAnimeCurrentEpisode)
                          : formatRuntime(getDurationTicks(activeAnimeCurrentEpisode))}
                      </small>
                    </div>
                  </div>
                ) : null}
              </div>
            </section>
            {animeSeriesGroups.length ? (
              <>
                <div className="spiritflix-anime-series-picker" aria-label="Anime series">
                  {animeSeriesGroups.map((series) => {
                    const isSelected = activeAnimeSeries?.seriesName === series.seriesName;
                    return (
                      <button
                        key={series.seriesName}
                        type="button"
                        className={isSelected ? "is-active" : undefined}
                        onClick={() => setSelectedAnimeSeriesName(series.seriesName)}
                        aria-current={isSelected ? "page" : undefined}
                      >
                        {series.representative ? (
                          <span className="spiritflix-anime-series-picker__art">
                            <SpiritFlixImage client={client} item={series.representative} type="Primary" width={260} alt="" />
                          </span>
                        ) : null}
                        <span className="spiritflix-anime-series-picker__shade" aria-hidden="true" />
                        <span className="spiritflix-anime-series-picker__copy">
                          <strong>{series.seriesName}</strong>
                          <span>
                            {series.seasons.length} {series.seasons.length === 1 ? "season" : "seasons"} / {series.episodeCount} episodes
                          </span>
                        </span>
                      </button>
                    );
                  })}
                </div>
                {activeAnimeSeries ? (
                  <section className="spiritflix-anime-series" aria-label={activeAnimeSeries.seriesName}>
                    <div className="spiritflix-anime-series__header">
                      <h2>{activeAnimeSeries.seriesName}</h2>
                      <span>{activeAnimeSeries.episodeCount} episodes</span>
                    </div>
                    <div className="spiritflix-anime-seasons">
                      {activeAnimeSeries.seasons.map((season) => (
                        <section key={`${activeAnimeSeries.seriesName}-${season.seasonNumber}`} className="spiritflix-anime-season" aria-label={`${activeAnimeSeries.seriesName} Season ${season.seasonNumber}`}>
                          <div className="spiritflix-anime-season__header">
                            <h3>Season {season.seasonNumber}</h3>
                            <span>{season.items.length} episodes</span>
                          </div>
                          <div className="spiritflix-anime-episodes">
                            {season.items.map((episode) => (
                              <button
                                key={episode.Id}
                                type="button"
                                className="spiritflix-anime-episode"
                                onClick={() =>
                                  onPlay(
                                    episode,
                                    activeAnimeEpisodes,
                                    `${activeAnimeSeries.seriesName} / Season ${season.seasonNumber}`,
                                    hasResumeProgress(episode) ? getResumePositionTicks(episode) : undefined,
                                  )
                                }
                              >
                                <span className="spiritflix-anime-episode__thumb">
                                  <SpiritFlixImage client={client} item={episode} type="Thumb" width={260} alt="" />
                                  {hasResumeProgress(episode) ? (
                                    <span className="spiritflix-anime-episode__progress" aria-hidden="true">
                                      <span style={{ width: `${Math.min(100, getResumeProgressPercent(episode))}%` }} />
                                    </span>
                                  ) : null}
                                </span>
                                <span className="spiritflix-anime-episode__copy">
                                  <span>{formatAnimeEpisodeLabel(episode)}</span>
                                  <strong>{getAnimeEpisodeTitle(episode)}</strong>
                                  <small>
                                    {hasResumeProgress(episode)
                                      ? `Resume from ${getResumeSlotLabel(episode).split(" / ")[0]}`
                                      : formatRuntime(getDurationTicks(episode))}
                                  </small>
                                </span>
                                <span className="spiritflix-anime-episode__play">
                                  <Play size={18} fill="currentColor" aria-hidden="true" />
                                </span>
                              </button>
                            ))}
                          </div>
                        </section>
                      ))}
                    </div>
                  </section>
                ) : null}
                {hasMoreLibraryItems ? (
                  <div className="spiritflix-library-pager" aria-label="Anime episode pages">
                    <span>{loadedLibraryTotalLabel} anime items</span>
                    <button
                      type="button"
                      onClick={onLoadMoreLibrary}
                      disabled={loadingMore.library}
                      aria-label="Load more anime episodes"
                    >
                      <ChevronRight size={20} aria-hidden="true" />
                    </button>
                  </div>
                ) : null}
              </>
            ) : (
              <p className="spiritflix-empty">No anime episodes are indexed yet.</p>
            )}
          </section>
        ) : null}
        {isHomeView ? (
          <>
            <SpiritFlixRail
              title="Continue Watching"
              variant="landscape"
              client={client}
              items={data.continueWatching}
              playOnPrimaryTap={playPrimaryTapOnMobile}
              hasMore={Boolean(data.continueWatchingPaging?.hasMore || data.watchHistoryPaging?.hasMore)}
              loadingMore={Boolean(loadingMore.continueWatching)}
              onLoadMore={onLoadMoreContinueWatching}
              onOpenDetails={onOpenDetails}
              onPlay={onPlay}
              emptyText="Nothing in progress yet."
            />
            <SpiritFlixRail
              title="Latest Added"
              variant="poster"
              client={client}
              items={data.latestAdded}
              playOnPrimaryTap={playPrimaryTapOnMobile}
              hasMore={Boolean(data.latestAddedPaging?.hasMore)}
              loadingMore={Boolean(loadingMore.latestAdded)}
              onLoadMore={onLoadMoreLatestAdded}
              onOpenDetails={onOpenDetails}
              onPlay={onPlay}
              emptyText="No recent videos found."
            />
          </>
        ) : null}
      </div>
      {galleryLightbox ? (
        <GalleryLightbox
          items={galleryLightbox.items}
          initialIndex={galleryLightbox.index}
          onClose={() => setGalleryLightbox(null)}
        />
      ) : null}
    </section>
  );
}
