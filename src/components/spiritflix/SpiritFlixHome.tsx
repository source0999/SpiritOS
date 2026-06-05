// Isolated Continue Watching v1 - Dedicated gooner user lane - Z Fold optimized
"use client";

// Face Organizer integration v1 - Model sorting from sidecars + known_performers - Z Fold optimized
// Layout v2 - Model-centric + Grid/List toggle - Z Fold optimized - Codex executed 2026-06-04

import { useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  ChevronLeft,
  ChevronRight,
  Grid2X2,
  List,
  LogOut,
  Play,
  RefreshCw,
  RotateCcw,
  Search,
  Server,
  Settings,
  SlidersHorizontal,
  Shuffle,
  Sparkles,
} from "lucide-react";
import { formatRuntime, isPlayableItem, type JellyfinClient } from "@/lib/spiritflix-jellyfin-client";
import {
  getResumePositionTicks,
  getResumeProgressPercent,
  getResumeSlotLabel,
  getTimeLeftLabel,
  hasResumeProgress,
} from "@/lib/spiritflix-resume";
import type {
  FaceOrganizerMetadataResponse,
  FaceOrganizerStatus,
  FaceOrganizerVideoMatch,
  JellyfinItem,
  SpiritFlixHomeData,
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
  onOpenDetails: (item: JellyfinItem) => void;
  onPlay: (item: JellyfinItem, queueItems?: JellyfinItem[], sourceTitle?: string, startPositionTicks?: number) => void;
}

type LibraryViewMode = "grid" | "list";
type LibrarySortMode = "model" | "title" | "dateAdded" | "duration";
type LibrarySortDirection = "asc" | "desc";

interface ModelGroup {
  name: string;
  count: number;
  items: JellyfinItem[];
  representative: JellyfinItem;
  source: "face-organizer" | "jellyfin";
  status: FaceOrganizerStatus;
  confidence?: number;
}

const LIBRARY_VIEW_MODE_KEY = "spiritflix_library_view_mode";
const LIBRARY_SORT_MODE_KEY = "spiritflix_library_sort_mode";
const LIBRARY_SORT_DIRECTION_KEY = "spiritflix_library_sort_direction";
const FACE_METADATA_CACHE_KEY = "spiritflix_face_metadata_v1";
const TEMP_LIBRARY_NAME = "Home Videos and Photos";
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
  const faceMatch = getFaceMatch(item, faceMetadata);
  if (hasIdentifiedFace(faceMatch)) return normalizeModelName(faceMatch?.primaryPerformer?.name ?? "Unknown");
  return normalizeModelName(getModelName(item));
}

function getStatusRank(status?: FaceOrganizerStatus): number {
  if (status === "confirmed") return 0;
  if (status === "needs_review") return 1;
  if (status === "unknown") return 2;
  return 3;
}

function buildModelGroups(items: JellyfinItem[], faceMetadata: FaceOrganizerMetadataResponse | null): ModelGroup[] {
  const groups = new Map<string, JellyfinItem[]>();
  const metaByName = new Map<string, { source: ModelGroup["source"]; status: FaceOrganizerStatus; confidence?: number }>();

  items.filter(isPlayableItem).forEach((item) => {
    const faceMatch = getFaceMatch(item, faceMetadata);
    const isFaceIdentified = hasIdentifiedFace(faceMatch);
    const rawModelName = isFaceIdentified ? faceMatch?.primaryPerformer?.name ?? getModelName(item) : getModelName(item);
    const modelName = normalizeModelName(rawModelName);
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

  return Array.from(groups.entries())
    .map(([name, modelItems]) => ({
      name,
      count: modelItems.length,
      items: modelItems,
      representative: modelItems.find((item) => item.ImageTags?.Primary || item.ImageTags?.Thumb) ?? modelItems[0],
      source: metaByName.get(name)?.source ?? "jellyfin",
      status: metaByName.get(name)?.status ?? "unscanned",
      confidence: metaByName.get(name)?.confidence,
    }))
    .sort(
      (left, right) =>
        getStatusRank(left.status) - getStatusRank(right.status) ||
        Number(right.source === "face-organizer") - Number(left.source === "face-organizer") ||
        right.count - left.count ||
        left.name.localeCompare(right.name),
    );
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
  playOnPrimaryTap: boolean;
  onOpenDetails: (item: JellyfinItem) => void;
  onPlay: (item: JellyfinItem, startPositionTicks?: number) => void;
}

function LibraryFeedCard({ client, item, playOnPrimaryTap, onOpenDetails, onPlay }: LibraryFeedCardProps) {
  const hasProgress = hasResumeProgress(item);
  const progress = getResumeProgressPercent(item);
  const resumeTicks = item.UserData?.PlaybackPositionTicks;
  const canPlay = isPlayableItem(item);

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
  onOpenDetails,
  onPlay,
}: SpiritFlixHomeProps) {
  const [viewMode, setViewMode] = useState<LibraryViewMode>("grid");
  const [sortMode, setSortMode] = useState<LibrarySortMode>("model");
  const [sortDirection, setSortDirection] = useState<LibrarySortDirection>("desc");
  const [filtersOpen, setFiltersOpen] = useState(false);
  const [selectedModel, setSelectedModel] = useState<string | null>(null);
  const [faceMetadata, setFaceMetadata] = useState<FaceOrganizerMetadataResponse | null>(null);
  const [faceMetadataError, setFaceMetadataError] = useState("");
  const [playPrimaryTapOnMobile, setPlayPrimaryTapOnMobile] = useState(false);
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
  const modelGroups = useMemo(() => buildModelGroups(data.libraryItems, faceMetadata), [data.libraryItems, faceMetadata]);
  const selectedModelGroup = selectedModel ? modelGroups.find((model) => model.name === selectedModel) : null;
  const playableLibraryItems = useMemo(() => data.libraryItems.filter(isPlayableItem), [data.libraryItems]);
  const visibleLibraryItems = useMemo(() => {
    const sourceItems = selectedModelGroup?.items ?? playableLibraryItems;
    const direction = sortDirection === "asc" ? 1 : -1;

    return [...sourceItems].sort((left, right) => {
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
  }, [faceMetadata, playableLibraryItems, selectedModelGroup, sortDirection, sortMode]);
  const continueWatchingItems = useMemo(() => {
    const sourceItems = selectedModelGroup?.items ?? playableLibraryItems;
    const allowedIds = selectedModelGroup ? new Set(sourceItems.map((item) => item.Id)) : null;
    const seen = new Set<string>();
    return [...data.continueWatching, ...sourceItems]
      .filter((item) => {
        if (allowedIds && !allowedIds.has(item.Id)) return false;
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
  }, [data.continueWatching, playableLibraryItems, selectedModelGroup]);
  const favoriteItems = useMemo(() => {
    const sourceItems = selectedModelGroup?.items ?? playableLibraryItems;
    const allowedIds = selectedModelGroup ? new Set(sourceItems.map((item) => item.Id)) : null;
    const seen = new Set<string>();
    return data.favorites
      .filter((item) => isPlayableItem(item) && item.UserData?.IsFavorite)
      .filter((item) => {
        if (allowedIds && !allowedIds.has(item.Id)) return false;
        if (seen.has(item.Id)) return false;
        seen.add(item.Id);
        return true;
      })
      .sort((left, right) => left.Name.localeCompare(right.Name));
  }, [data.favorites, playableLibraryItems, selectedModelGroup]);
  const libraryStats = [
    { label: "Videos", value: playableLibraryItems.length },
    { label: "Models", value: modelGroups.length },
    { label: "Selected", value: selectedModelGroup?.count ?? playableLibraryItems.length },
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

  useEffect(() => {
    const stored = window.localStorage.getItem(LIBRARY_VIEW_MODE_KEY);
    if (stored === "grid" || stored === "list") setViewMode(stored);
    const storedSort = window.localStorage.getItem(LIBRARY_SORT_MODE_KEY);
    if (storedSort === "model" || storedSort === "title" || storedSort === "dateAdded" || storedSort === "duration") setSortMode(storedSort);
    const storedDirection = window.localStorage.getItem(LIBRARY_SORT_DIRECTION_KEY);
    if (storedDirection === "asc" || storedDirection === "desc") setSortDirection(storedDirection);
  }, []);

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
    setSelectedModel(null);
  }, [data.selectedLibraryId, searchTerm]);

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
    const sourceItems = scope === "model" && selectedModelGroup ? selectedModelGroup.items : playableLibraryItems;
    const shuffled = shuffleItems(sourceItems);
    const firstItem = shuffled[0];
    if (firstItem) {
      onPlay(firstItem, shuffled, scope === "model" && selectedModelGroup ? `${selectedModelGroup.name} Shuffle` : `${libraryTitle} Shuffle`);
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
          <button className="spiritflix-source-pill" type="button" onClick={onRefresh} title="Refresh Jellyfin source">
            <Server size={15} aria-hidden="true" />
            <span>{serverInfo?.ServerName ?? "Jellyfin"}</span>
          </button>
          <button className="spiritflix-icon-button" type="button" onClick={onRefresh} aria-label="Refresh library">
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
                <h2>{selectedModelGroup?.name ?? "All Models"}</h2>
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
              </div>
            </div>

            <div className="spiritflix-library-modebar">
              <button
                type="button"
                className="spiritflix-filter-trigger"
                aria-expanded={filtersOpen}
                onClick={() => setFiltersOpen((current) => !current)}
              >
                <SlidersHorizontal size={18} aria-hidden="true" />
                <span>{getSortModeLabel(sortMode)} / {getSortDirectionLabel(sortDirection)}</span>
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
                          onClick={() => setSortMode(value as LibrarySortMode)}
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
                        onClick={() => setSortDirection("desc")}
                      >
                        Descending
                      </button>
                      <button
                        type="button"
                        className={sortDirection === "asc" ? "is-active" : undefined}
                        aria-pressed={sortDirection === "asc"}
                        onClick={() => setSortDirection("asc")}
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
            {faceMetadataError ? <p className="spiritflix-face-note">{faceMetadataError}</p> : null}

            {continueWatchingItems.length ? (
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
                        onClick={() => onPlay(item, visibleLibraryItems, "Continue Watching", resumeTicks)}
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
                  onClick={() => setSelectedModel(null)}
                >
                  All Models
                </button>
                {modelGroups.map((model) => (
                  <motion.button
                    layout
                    key={model.name}
                    type="button"
                    className={`spiritflix-model-card ${selectedModel === model.name ? "is-active" : ""}`}
                    onClick={() => setSelectedModel(model.name)}
                    whileTap={{ scale: 0.98 }}
                  >
                    <SpiritFlixImage client={client} item={model.representative} type="Primary" width={260} alt="" />
                    <span>
                      <strong>{model.name}</strong>
                      <small>{model.count} videos</small>
                    </span>
                  </motion.button>
                ))}
              </div>
            </section>

            <AnimatePresence mode="wait">
              {viewMode === "grid" ? (
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
                      playOnPrimaryTap={playPrimaryTapOnMobile}
                      onOpenDetails={onOpenDetails}
                      onPlay={(selectedItem, startPositionTicks) =>
                        onPlay(selectedItem, visibleLibraryItems, selectedModelGroup?.name ?? libraryTitle, startPositionTicks)
                      }
                    />
                  ))}
                </motion.div>
              ) : (
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
              )}
            </AnimatePresence>

            {!visibleLibraryItems.length ? <p className="spiritflix-empty">{libraryTitle} has no indexed videos yet.</p> : null}

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
              disabled={!playableLibraryItems.length}
              whileTap={{ scale: 0.97 }}
              aria-label={
                selectedModelGroup
                  ? `Shuffle ${libraryTitle}; long press to shuffle ${selectedModelGroup.name}`
                  : `Shuffle ${libraryTitle}`
              }
            >
              <Shuffle size={21} aria-hidden="true" />
              <span>
                <strong>Shuffle Gooner Mix</strong>
                <small>{selectedModelGroup ? `Hold: ${selectedModelGroup.name}` : "Whole library"}</small>
              </span>
            </motion.button>
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
    </section>
  );
}
