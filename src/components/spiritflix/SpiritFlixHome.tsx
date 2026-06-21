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
  initialModelName?: string | null;
  initialManualTag?: string | null;
  onSelectModel: (modelName: string | null) => void;
  onOpenDetails: (item: JellyfinItem) => void;
  onPlay: (item: JellyfinItem, queueItems?: JellyfinItem[], sourceTitle?: string, startPositionTicks?: number) => void;
}

type LibraryViewMode = "grid" | "list" | "history" | "gallery" | "models";
type LibrarySortMode = "model" | "title" | "dateAdded" | "duration";
type LibrarySortDirection = "asc" | "desc";

interface ModelGroup {
  name: string;
  count: number;
  indexedCount: number;
  liveSourceCount?: number;
  items: JellyfinItem[];
  representative: JellyfinItem;
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
  return value === "grid" || value === "list" || value === "history" || value === "gallery" || value === "models";
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

function buildModelGroups(items: JellyfinItem[], faceMetadata: FaceOrganizerMetadataResponse | null): ModelGroup[] {
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

  const regularGroups = Array.from(groups.entries())
    .map(([name, modelItems]) => {
      const indexedCount = modelItems.length;
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
  return items
    .map((item) => ({ item, sort: Math.random() }))
    .sort((left, right) => left.sort - right.sort)
    .map(({ item }) => item);
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
  onOpenDetails: (item: JellyfinItem) => void;
  onPlay: (item: JellyfinItem, startPositionTicks?: number) => void;
}

function LibraryFeedCard({ client, item, manualTags = [], playOnPrimaryTap, onOpenDetails, onPlay }: LibraryFeedCardProps) {
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
        <SpiritFlixImage client={client} item={item} type="Primary" width={620} alt={item.Name} />
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
  const [manualModelRecords, setManualModelRecords] = useState<SpiritFlixManualModelRecord[]>([]);
  const [faceMetadataError, setFaceMetadataError] = useState("");
  const [galleryData, setGalleryData] = useState<SpiritFlixGalleryResponse | null>(null);
  const [galleryError, setGalleryError] = useState("");
  const [galleryLightbox, setGalleryLightbox] = useState<{ items: SpiritFlixGalleryItem[]; index: number } | null>(null);
  const [playPrimaryTapOnMobile, setPlayPrimaryTapOnMobile] = useState(false);
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
  const hero = isHomeView
    ? data.featuredItems[0] ?? data.continueWatching[0] ?? data.latestAdded[0] ?? data.libraryItems[0] ?? null
    : data.libraryItems[0] ?? data.latestAdded[0] ?? data.continueWatching[0] ?? null;
  const selectedLibrary = data.libraries.find((library) => library.Id === data.selectedLibraryId);
  const libraryTitle = isHomeView ? "Home" : displayLibraryName(selectedLibrary?.Name);
  const manualModelMap = useMemo(() => {
    const map = new Map<string, string>();
    manualModelRecords.forEach((record) => {
      if (record.modelName) map.set(record.itemId, record.modelName);
    });
    return map;
  }, [manualModelRecords]);
  const modelAwareLibraryItems = useMemo(
    () =>
      data.libraryItems.map((item) => {
        const manualModelName = manualModelMap.get(item.Id);
        return manualModelName ? { ...item, ManualModelName: manualModelName } : item;
      }),
    [data.libraryItems, manualModelMap],
  );
  const modelGroups = useMemo(() => buildModelGroups(modelAwareLibraryItems, faceMetadata), [modelAwareLibraryItems, faceMetadata]);
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
    return data.favorites
      .filter((item) => isPlayableItem(item) && item.UserData?.IsFavorite)
      .filter((item) => {
        if (!itemMatchesActiveVideoFilters(item)) return false;
        if (seen.has(item.Id)) return false;
        seen.add(item.Id);
        return true;
      })
      .sort((left, right) => left.Name.localeCompare(right.Name));
  }, [data.favorites, itemMatchesActiveVideoFilters]);
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
    { label: "Videos", value: playableLibraryItems.length },
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
      const body = (await response.json()) as { items?: SpiritFlixManualModelRecord[] };
      setManualModelRecords(body.items ?? []);
    } catch {
      setManualModelRecords([]);
    }
  }, []);

  const handleRefresh = () => {
    onRefresh();
    void loadGallery();
    void loadManualTags();
    void loadManualModels();
  };

  const closeFiltersOnCoarsePointer = () => {
    if (typeof window.matchMedia === "function" && window.matchMedia("(max-width: 760px), (pointer: coarse)").matches) {
      setFiltersOpen(false);
    }
  };

  useEffect(() => {
    void loadGallery();
  }, [loadGallery]);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void loadManualTags();
      void loadManualModels();
    }, 0);
    const handleManualTagsChanged = () => {
      void loadManualTags();
    };
    const handleManualModelsChanged = () => {
      void loadManualModels();
    };
    window.addEventListener("spiritflix:manual-tags-changed", handleManualTagsChanged);
    window.addEventListener("spiritflix:manual-models-changed", handleManualModelsChanged);
    return () => {
      window.clearTimeout(timer);
      window.removeEventListener("spiritflix:manual-tags-changed", handleManualTagsChanged);
      window.removeEventListener("spiritflix:manual-models-changed", handleManualModelsChanged);
    };
  }, [loadManualModels, loadManualTags]);

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
    if (!data.libraries.length) return;
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
    if (isHomeView || !playableLibraryItems.length) {
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
  }, [client, data.selectedLibraryId, isHomeView, playableLibraryItems]);

  const playShuffle = (scope: "library" | "model") => {
    const sourceItems =
      scope === "model" && selectedModelGroup
        ? filterItemsByVideoOrientation(selectedModelGroup.items, orientationFilter).filter((item) =>
            getItemCategoryKeys(item).every((category) => !excludedCategorySet.has(category)) &&
            (manualTagItemIds ? manualTagItemIds.has(item.Id) : true),
          )
        : filteredLibraryItems;
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
      playShuffle("model");
    }, 520);
  };

  const handleShuffleClick = () => {
    if (didLongPressShuffleRef.current) {
      didLongPressShuffleRef.current = false;
      return;
    }
    playShuffle("library");
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

      <section className={`spiritflix-hero ${hero ? "" : "spiritflix-hero--empty"}`}>
        {hero ? (
          <>
            <SpiritFlixImage client={client} item={hero} type="Primary" width={700} className="spiritflix-hero__ambient" />
            <SpiritFlixImage client={client} item={hero} type="Backdrop" width={1600} className="spiritflix-hero__image" />
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

      {error ? <p className="spiritflix-error spiritflix-error--home">{error}</p> : null}
      {loading ? <div className="spiritflix-loading">Loading Jellyfin rows...</div> : null}

      <div className="spiritflix-rows">
        {!isHomeView ? (
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
                    : viewMode === "gallery"
                      ? selectedModelGroup
                        ? `${selectedModelGroup.name} Pics`
                        : "Gallery"
                      : selectedModelGroup?.name ?? "All Models"}
                </h2>
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
                </div>
              ))}
            </div>
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

            {viewMode !== "gallery" && viewMode !== "models" && continueWatchingItems.length ? (
              <section className="spiritflix-resume-section" aria-label="Continue Watching">
                <div className="spiritflix-resume-section__header">
                  <div>
                    <h3>Continue Watching</h3>
                    <span>Private Jellyfin lane / {selectedModelGroup?.name ?? libraryTitle}</span>
                  </div>
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

            {viewMode !== "gallery" && viewMode !== "models" ? (
              <SpiritFlixRail
                title="Favorites"
                variant="poster"
                client={client}
                items={favoriteItems}
                playOnPrimaryTap={playPrimaryTapOnMobile}
                onOpenDetails={onOpenDetails}
                onPlay={onPlay}
                emptyText={`No favorites in ${selectedModelGroup?.name ?? libraryTitle} yet.`}
              />
            ) : null}

            <section className="spiritflix-model-section" aria-label="Model filters">
              <div className="spiritflix-model-section__header">
                <span>Models</span>
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
                      <SpiritFlixImage client={client} item={model.representative} type="Primary" width={260} alt="" />
                      <span>
                        <strong>{model.name}</strong>
                        <small>{model.indexedCount} videos{galleryCount ? ` / ${galleryCount} pics` : ""}</small>
                      </span>
                    </motion.button>
                  );
                })}
              </div>
            </section>

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
                        <SpiritFlixImage client={client} item={model.representative} type="Primary" width={320} alt="" />
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
              ) : viewMode === "grid" ? (
                <motion.div
                  key="grid"
                  className="spiritflix-library-grid"
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -8 }}
                  transition={{ duration: 0.18 }}
                >
                  {visibleLibraryItems.map((item) => (
                    <LibraryFeedCard
                      key={item.Id}
                      client={client}
                      item={item}
                      manualTags={manualTagMap.get(item.Id)}
                      playOnPrimaryTap={playPrimaryTapOnMobile}
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

            {viewMode !== "gallery" && viewMode !== "history" && viewMode !== "models" && sortedLibraryItems.length > LIBRARY_PAGE_SIZE ? (
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
                  Page {clampedLibraryPageIndex + 1} of {libraryPageCount} / {libraryPageStart}-{libraryPageEnd} of {sortedLibraryItems.length}
                </span>
                <button
                  type="button"
                  onClick={() => setLibraryPageIndex((page) => Math.min(libraryPageCount - 1, page + 1))}
                  disabled={clampedLibraryPageIndex >= libraryPageCount - 1}
                  aria-label="Next video page"
                >
                  <ChevronRight size={20} aria-hidden="true" />
                </button>
              </div>
            ) : null}

            {viewMode === "models" && !modelGroups.length ? (
              <p className="spiritflix-empty">No model groups found in {libraryTitle} yet.</p>
            ) : viewMode === "gallery" && !visibleGalleryItems.length ? (
              <p className="spiritflix-empty">No gallery pictures found for {selectedModelGroup?.name ?? "any model"} yet.</p>
            ) : viewMode === "history" && !historyItems.length ? (
              <p className="spiritflix-empty">No private watch history has synced for {selectedModelGroup?.name ?? libraryTitle} yet.</p>
            ) : viewMode !== "history" && !visibleLibraryItems.length ? (
              <p className="spiritflix-empty">{libraryTitle} has no indexed videos yet.</p>
            ) : null}

            {viewMode !== "gallery" && viewMode !== "models" ? (
              <motion.button
                type="button"
                className="spiritflix-shuffle-fab"
                onClick={handleShuffleClick}
                onPointerDown={startShuffleLongPress}
                onPointerUp={clearLongPressTimer}
                onPointerCancel={clearLongPressTimer}
                onContextMenu={(event) => {
                  event.preventDefault();
                  if (selectedModelGroup) playShuffle("model");
                }}
                disabled={!filteredLibraryItems.length}
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
        {isHomeView ? (
          <>
            <SpiritFlixRail
              title="Continue Watching"
              variant="landscape"
              client={client}
              items={data.continueWatching}
              playOnPrimaryTap={playPrimaryTapOnMobile}
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
              onOpenDetails={onOpenDetails}
              onPlay={onPlay}
              emptyText="No recent videos found."
            />
            <SpiritFlixRail
              title="Favorites"
              variant="poster"
              client={client}
              items={data.favorites}
              playOnPrimaryTap={playPrimaryTapOnMobile}
              onOpenDetails={onOpenDetails}
              onPlay={onPlay}
              emptyText="No favorite videos yet."
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
