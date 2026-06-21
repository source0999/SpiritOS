"use client";

import {
  closestCenter,
  DndContext,
  PointerSensor,
  TouchSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
  type DragOverEvent,
} from "@dnd-kit/core";
import {
  SortableContext,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { useCallback, useEffect, useMemo, useRef, useState, type CSSProperties } from "react";
import {
  ChevronsDown,
  GripVertical,
  Heart,
  Languages,
  ListMusic,
  Maximize,
  Minimize,
  Pause,
  PictureInPicture2,
  Play,
  RefreshCw,
  Repeat,
  Repeat1,
  SlidersHorizontal,
  Shuffle,
  SkipBack,
  SkipForward,
  Tag,
  Trash2,
  UserRound,
  Volume2,
  VolumeX,
  X,
} from "lucide-react";
import {
  isPlayableItem,
  ticksToSeconds,
  type JellyfinClient,
  type MobileOptimizedSource,
  type SpiritFlixSystemDiagnostics,
} from "@/lib/spiritflix-jellyfin-client";
import {
  countItemsByVideoOrientation,
  getOrientationFilterLabel,
  type SpiritFlixVideoOrientation,
} from "@/lib/spiritflix-orientation";
import { getSpiritFlixManualTagScope } from "@/lib/spiritflix/manual-tag-scope";
import type {
  FaceOrganizerMetadataResponse,
  FaceOrganizerVideoMatch,
  JellyfinItem,
  SpiritFlixFaceLearningRecord,
  SpiritFlixManualModelIndex,
  SpiritFlixManualModelRecord,
  SpiritFlixManualTagIndex,
  SpiritFlixManualTagRecord,
} from "@/lib/spiritflix-types";
import type { SpiritFlixPlaybackProgress, SpiritFlixPlaybackQueue } from "./SpiritFlixApp";
import { SpiritFlixImage } from "./SpiritFlixImage";

interface SpiritFlixPlayerProps {
  client: JellyfinClient;
  item: JellyfinItem;
  queue: SpiritFlixPlaybackQueue | null;
  libraryItems?: JellyfinItem[];
  startPositionTicks?: number;
  onPlaybackProgress: (progress: SpiritFlixPlaybackProgress) => void;
  onToggleFavorite: (item: JellyfinItem, isFavorite: boolean) => void;
  onSelectItem: (item: JellyfinItem) => void;
  onShuffleQueue: (currentItemId: string, orientation?: SpiritFlixVideoOrientation) => void;
  onPlayModelShuffle: (currentItem: JellyfinItem, modelName: string, modelItems: JellyfinItem[]) => void;
  onReorderQueue: (activeItemId: string, overItemId: string) => void;
  onDeleteItem: (deletedItem: JellyfinItem, nextItem: JellyfinItem | null) => void;
  onClose: () => void;
}

interface SpiritFlixDeletePreview {
  schema: "spiritflix-admin-action/v1";
  action: "softDelete";
  phase: "preview" | "execute";
  previewId: string;
  allowed: boolean;
  message: string;
  preview?: {
    sourcePath?: string;
    targetPath?: string;
    affectedPaths: string[];
    warnings: string[];
    reversible?: boolean;
  };
}

type FitMode = "fit" | "fill";
type RepeatMode = "off" | "queue" | "one";
type SeriesAudioPreference = "sub" | "dub";
type PlaybackSourceMode = "direct stream" | "proxied stream" | "HLS" | "mobile optimized";
type PlaybackSourceClass =
  | "mac_optimized_mp4"
  | "canonical_mp4"
  | "jellyfin_direct_mp4"
  | "jellyfin_hls_fallback"
  | "jellyfin_transcode_fallback";

const FIT_STORAGE_KEY = "spiritflix_player_fit_mode";
const REPEAT_STORAGE_KEY = "spiritflix_player_repeat_mode";
const SERIES_AUDIO_PREFS_STORAGE_KEY = "spiritflix_series_audio_preferences";
const VOLUME_STORAGE_KEY = "spiritflix_player_volume";
const MUTED_STORAGE_KEY = "spiritflix_player_muted";
const TAP_MAX_MOVEMENT = 26;
const TAP_MAX_MS = 420;
const DOUBLE_TAP_MAX_MS = 480;
const DOUBLE_TAP_MAX_DISTANCE = 96;
const DOUBLE_TAP_EDGE_ZONE = 0.3;
const CENTER_TAP_MIN = 0.38;
const CENTER_TAP_MAX = 0.62;
const TOUCH_SEEK_ACTIVATION_PX = 34;
const TOUCH_SEEK_HOLD_MS = 90;
const TOUCH_SEEK_VERTICAL_RATIO = 1.35;
const TOUCH_SEEK_MAX_SECONDS = 90;
const TOUCH_SEEK_PX_PER_SECOND = 7.5;
const PINCH_TOGGLE_THRESHOLD = 0.08;
const PINCH_GESTURE_SUPPRESS_MS = 450;
const HLS_MANIFEST_TIMEOUT_MS = 8000;
const PLAYBACK_FEEDBACK_MS = 1150;
const APP_WIDGET_IDLE_CLOSE_MS = 60000;
const AUTO_FACE_MODEL_CONFIDENCE = 0.8;
const QUEUE_DND_PREFIX = "spiritflix-queue:";
const SHOW_PLAYER_DIAGNOSTICS = process.env.NODE_ENV !== "production";
const MANUAL_TAG_CHANGED_EVENT = "spiritflix:manual-tags-changed";
const MANUAL_MODEL_CHANGED_EVENT = "spiritflix:manual-models-changed";

interface HlsController {
  loadSource: (source: string) => void;
  attachMedia: (media: HTMLMediaElement) => void;
  on: (event: string, listener: (event: string, data?: { fatal?: boolean; details?: string }) => void) => void;
  destroy: () => void;
}

type MiniPlayerDocument = Document;

type MiniPlayerVideo = HTMLVideoElement & {
  webkitPresentationMode?: "inline" | "picture-in-picture" | "fullscreen";
  webkitSetPresentationMode?: (mode: "inline" | "picture-in-picture") => void;
  webkitSupportsPresentationMode?: (mode: "picture-in-picture") => boolean;
};

interface SpiritFlixAudioTrack {
  id?: string;
  label?: string;
  language?: string;
  enabled: boolean;
}

interface SpiritFlixAudioTrackList {
  length: number;
  [index: number]: SpiritFlixAudioTrack | undefined;
}

type AudioTrackVideo = HTMLVideoElement & {
  audioTracks?: SpiritFlixAudioTrackList;
};
const TOUCH_MOUSE_REVEAL_SUPPRESS_MS = 1200;
const UI_TIME_UPDATE_MS = 500;
const PLAYBACK_REPORT_MS = 15000;
const DEFAULT_AUDIBLE_VOLUME = 0.8;
const PORTRAIT_VIDEO_ASPECT_CUTOFF = 0.9;
const PORTRAIT_SAFE_FILL_SCALE = 1.12;
const WIDE_SAFE_FILL_SCALE = 1.24;
const MODERATE_SAFE_FILL_SCALE = 1.34;

type PlaybackFeedbackInput =
  | { kind: "play" | "pause" }
  | { kind: "seek-back" | "seek-forward"; seconds: number };

type PlaybackFeedback =
  | { id: number; kind: "play" | "pause" }
  | { id: number; kind: "seek-back" | "seek-forward"; seconds: number };

type SeekTapZone = "left-seek" | "right-seek";
type PlayerTapZone = SeekTapZone | "center" | "surface";

function getQueueDndId(itemId: string): string {
  return `${QUEUE_DND_PREFIX}${itemId}`;
}

function getItemIdFromQueueDndId(id: string): string | null {
  return id.startsWith(QUEUE_DND_PREFIX) ? id.slice(QUEUE_DND_PREFIX.length) : null;
}

function secondsToTicks(seconds: number): number {
  return Math.max(0, Math.round(seconds * 10000000));
}

function formatTime(seconds: number): string {
  if (!Number.isFinite(seconds)) return "0:00";
  const whole = Math.max(0, Math.floor(seconds));
  const hours = Math.floor(whole / 3600);
  const minutes = Math.floor((whole % 3600) / 60);
  const rest = whole % 60;
  return hours
    ? `${hours}:${String(minutes).padStart(2, "0")}:${String(rest).padStart(2, "0")}`
    : `${minutes}:${String(rest).padStart(2, "0")}`;
}

function canonicalizeManualModelName(value: string): string {
  return value.trim().replace(/\s+/g, " ");
}

function getModelOptionKey(value: string): string {
  return canonicalizeManualModelName(value).toLowerCase();
}

function getCompactModelOptionKey(value: string): string {
  return getModelOptionKey(value).replace(/[^a-z0-9]+/g, "");
}

function getTitleMatchText(item: JellyfinItem): string {
  return [item.Name, item.SeriesName, item.Path, ...(item.MediaSources?.map((source) => source.Path) ?? [])]
    .filter(Boolean)
    .join(" ");
}

function getTitlePrefixAlias(value: string): string {
  const prefix = value
    .split(/\s+-\s+| - |\[/)[0]
    ?.replace(/[^\p{L}\p{N}\s._-]+/gu, " ")
    .trim()
    .replace(/\s+/g, " ");
  return prefix ?? "";
}

function getTrustedTitleAliasesForModel(modelName: string, modelItems: JellyfinItem[]): string[] {
  const aliases = new Map<string, string>();
  const addAlias = (alias: string) => {
    const normalized = alias.trim().replace(/\s+/g, " ");
    const compact = getCompactModelOptionKey(normalized);
    if (compact.length >= 4 && !aliases.has(compact)) aliases.set(compact, normalized);
  };
  addAlias(modelName);
  addAlias(modelName.replace(/\s*x\s*/i, "x"));
  addAlias(modelName.replace(/\s*x\s*/i, " x "));
  modelItems.forEach((modelItem) => addAlias(getTitlePrefixAlias(modelItem.Name)));
  return Array.from(aliases.values());
}

function itemTitleMatchesModelAlias(item: JellyfinItem, aliases: string[]): boolean {
  const sourceText = getTitleMatchText(item).toLowerCase();
  const compactSourceText = sourceText.replace(/[^a-z0-9]+/g, "");
  return aliases.some((alias) => {
    const compactAlias = getCompactModelOptionKey(alias);
    if (compactAlias.length < 4) return false;
    if (compactSourceText.includes(compactAlias)) return true;
    const escaped = alias.toLowerCase().replace(/[.*+?^${}()|[\]\\]/g, "\\$&").replace(/\s+/g, "\\s+");
    return new RegExp(`(^|[^a-z0-9])${escaped}([^a-z0-9]|$)`, "i").test(sourceText);
  });
}

export function getTitleMatchedModelItems(modelName: string, candidates: JellyfinItem[], currentItem: JellyfinItem): JellyfinItem[] {
  const modelKey = getModelOptionKey(modelName);
  if (!modelKey) return [];
  const byId = new Map<string, JellyfinItem>();
  candidates.forEach((candidate) => {
    if (candidate?.Id && isPlayableItem(candidate) && !byId.has(candidate.Id)) byId.set(candidate.Id, candidate);
  });
  const modelItems = Array.from(byId.values()).filter(
    (candidate) => candidate.Id === currentItem.Id || getModelOptionKey(candidate.ManualModelName || "") === modelKey,
  );
  const aliases = getTrustedTitleAliasesForModel(modelName, [currentItem, ...modelItems]);
  if (!aliases.length) return [];
  return Array.from(byId.values()).filter((candidate) => {
    if (candidate.Id === currentItem.Id) return false;
    const candidateModelKey = getModelOptionKey(candidate.ManualModelName || "");
    if (candidateModelKey && candidateModelKey !== modelKey) return false;
    return itemTitleMatchesModelAlias(candidate, aliases);
  });
}

function formatFaceConfidence(match?: FaceOrganizerVideoMatch): string {
  const confidence = getFaceConfidenceValue(match);
  return typeof confidence === "number" ? `${Math.round(confidence * 100)}%` : "unknown";
}

function getFaceConfidenceValue(match?: FaceOrganizerVideoMatch): number | undefined {
  return match?.confidence ?? match?.primaryPerformer?.confidence ?? match?.primaryPerformer?.similarity;
}

function getInferredModelName(item: JellyfinItem): string {
  if (item.ManualModelName) return item.ManualModelName;
  const person = item.People?.find((entry) =>
    ["actor", "actress", "performer", "artist"].includes(entry.Type?.toLowerCase() ?? ""),
  );
  if (person?.Name) return person.Name;
  if (item.SeriesName) return item.SeriesName;
  if (item.Path) {
    const parts = item.Path.split(/[\\/]+/).filter(Boolean);
    return parts.at(-2) ?? "";
  }
  return "";
}

function getItemSourcePath(item: JellyfinItem): string {
  return item.MediaSources?.[0]?.Path ?? item.Path ?? "";
}

function normalizeSpiritFlixMediaPath(sourcePath: string): string {
  return sourcePath.replace(/\\/g, "/").replace(/^\/media(?=\/)/i, "/mnt/spirit-8tb/media");
}

function isYesFolderVideoPath(sourcePath: string): boolean {
  const normalized = normalizeSpiritFlixMediaPath(sourcePath).toLowerCase();
  return normalized.startsWith("/mnt/spirit-8tb/media/yes/") && !normalized.includes("/.trash/");
}

function isAnimePath(sourcePath: string): boolean {
  const normalized = sourcePath.replace(/\\/g, "/").toLowerCase();
  return normalized.includes("/media/anime/") || normalized.includes("/anime/");
}

function isSeriesPlaybackItem(item: JellyfinItem): boolean {
  return item.Type?.toLowerCase() === "episode" || isAnimePath(getItemSourcePath(item)) || item.MediaSources?.some((source) => isAnimePath(source.Path ?? "")) === true;
}

function getSeriesPlaybackKey(item: JellyfinItem): string {
  if (!isSeriesPlaybackItem(item)) return "";
  if (item.SeriesName?.trim()) return item.SeriesName.trim().toLowerCase();
  const parts = getItemSourcePath(item).replace(/\\/g, "/").split("/").filter(Boolean);
  const seasonIndex = parts.findIndex((part) => /^season\s+\d+/i.test(part));
  if (seasonIndex > 0) return parts[seasonIndex - 1]?.toLowerCase() ?? "";
  const animeIndex = parts.findIndex((part) => part.toLowerCase() === "anime");
  return animeIndex >= 0 ? parts[animeIndex + 1]?.toLowerCase() ?? "" : "";
}

function getSeriesPlaybackQueue(item: JellyfinItem, candidates: JellyfinItem[]): JellyfinItem[] {
  const seriesKey = getSeriesPlaybackKey(item);
  if (!seriesKey) return [];
  const byId = new Map<string, JellyfinItem>();
  [item, ...candidates].forEach((candidate) => {
    if (candidate?.Id && isPlayableItem(candidate) && getSeriesPlaybackKey(candidate) === seriesKey && !byId.has(candidate.Id)) {
      byId.set(candidate.Id, candidate);
    }
  });
  return Array.from(byId.values()).sort(
    (left, right) =>
      (left.ParentIndexNumber ?? 0) - (right.ParentIndexNumber ?? 0) ||
      (left.IndexNumber ?? 0) - (right.IndexNumber ?? 0) ||
      left.Name.localeCompare(right.Name),
  );
}

function getStoredSeriesAudioPreference(seriesKey: string): SeriesAudioPreference {
  if (typeof window === "undefined" || !seriesKey) return "sub";
  try {
    const stored = JSON.parse(window.localStorage.getItem(SERIES_AUDIO_PREFS_STORAGE_KEY) ?? "{}") as Record<string, SeriesAudioPreference>;
    return stored[seriesKey] === "dub" || stored[seriesKey] === "sub" ? stored[seriesKey] : "sub";
  } catch {
    return "sub";
  }
}

function storeSeriesAudioPreference(seriesKey: string, preference: SeriesAudioPreference): void {
  if (typeof window === "undefined" || !seriesKey) return;
  try {
    const stored = JSON.parse(window.localStorage.getItem(SERIES_AUDIO_PREFS_STORAGE_KEY) ?? "{}") as Record<string, SeriesAudioPreference>;
    window.localStorage.setItem(SERIES_AUDIO_PREFS_STORAGE_KEY, JSON.stringify({ ...stored, [seriesKey]: preference }));
  } catch {
    window.localStorage.setItem(SERIES_AUDIO_PREFS_STORAGE_KEY, JSON.stringify({ [seriesKey]: preference }));
  }
}

function getAudioMatchText(value: { language?: string; label?: string; DisplayTitle?: string; Title?: string; Codec?: string }): string {
  return [value.language, value.label, value.DisplayTitle, value.Title, value.Codec].filter(Boolean).join(" ").toLowerCase();
}

function matchesAudioPreference(value: { language?: string; label?: string; DisplayTitle?: string; Title?: string; Codec?: string }, preference: SeriesAudioPreference): boolean {
  const text = getAudioMatchText(value);
  if (preference === "dub") {
    return /\b(en|eng|english)\b/.test(text) || text.includes("dub");
  }
  return /\b(ja|jpn|japanese)\b/.test(text) || text.includes("sub");
}

function getVideoAudioTracks(video: HTMLVideoElement | null): SpiritFlixAudioTrack[] {
  const tracks = (video as AudioTrackVideo | null)?.audioTracks;
  if (!tracks?.length) return [];
  return Array.from({ length: tracks.length }, (_, index) => tracks[index]).filter((track): track is SpiritFlixAudioTrack => Boolean(track));
}

function applyAudioPreferenceToVideo(video: HTMLVideoElement | null, preference: SeriesAudioPreference): boolean {
  const tracks = getVideoAudioTracks(video);
  if (tracks.length < 2) return false;
  const matchedIndex = tracks.findIndex((track) => matchesAudioPreference(track, preference));
  const fallbackIndex = preference === "dub" ? Math.min(1, tracks.length - 1) : 0;
  const selectedIndex = matchedIndex >= 0 ? matchedIndex : fallbackIndex;
  tracks.forEach((track, index) => {
    track.enabled = index === selectedIndex;
  });
  return true;
}

function renderPlaybackFeedback(feedback: PlaybackFeedback) {
  switch (feedback.kind) {
    case "pause":
      return <Pause size={58} aria-hidden="true" />;
    case "play":
      return <Play size={58} fill="currentColor" aria-hidden="true" />;
    case "seek-back":
      return (
        <>
          <SkipBack size={36} aria-hidden="true" />
          <strong>{feedback.seconds}s</strong>
        </>
      );
    case "seek-forward":
      return (
        <>
          <strong>{feedback.seconds}s</strong>
          <SkipForward size={36} aria-hidden="true" />
        </>
      );
  }
}

function getStoredFitMode(): FitMode {
  if (typeof window === "undefined") return "fit";
  const stored = window.localStorage.getItem(FIT_STORAGE_KEY);
  return stored === "fill" || stored === "fit" ? stored : "fit";
}

function isRepeatMode(value: string | null): value is RepeatMode {
  return value === "off" || value === "queue" || value === "one";
}

function getStoredRepeatMode(): RepeatMode {
  if (typeof window === "undefined") return "off";
  const stored = window.localStorage.getItem(REPEAT_STORAGE_KEY);
  return isRepeatMode(stored) ? stored : "off";
}

function getStoredVolume(): number {
  if (typeof window === "undefined") return 1;
  const stored = Number(window.localStorage.getItem(VOLUME_STORAGE_KEY));
  return Number.isFinite(stored) ? Math.max(0, Math.min(1, stored)) : 1;
}

function getStoredMuted(): boolean {
  if (typeof window === "undefined") return false;
  return window.localStorage.getItem(MUTED_STORAGE_KEY) === "true";
}

export function getSmartFillScale(shellAspectRatio: number, videoAspectRatio: number): number {
  if (
    !Number.isFinite(shellAspectRatio) ||
    !Number.isFinite(videoAspectRatio) ||
    shellAspectRatio <= 0 ||
    videoAspectRatio <= 0
  ) {
    return 1;
  }

  const coverScale =
    shellAspectRatio > videoAspectRatio
      ? shellAspectRatio / videoAspectRatio
      : videoAspectRatio / shellAspectRatio;

  if (coverScale <= 1.04) return 1;

  const safeScale =
    videoAspectRatio < PORTRAIT_VIDEO_ASPECT_CUTOFF
      ? PORTRAIT_SAFE_FILL_SCALE
      : coverScale >= 1.45
        ? WIDE_SAFE_FILL_SCALE
        : MODERATE_SAFE_FILL_SCALE;

  return Math.max(1, Math.min(coverScale, safeScale));
}

function isInteractiveTarget(target: EventTarget | null): boolean {
  return target instanceof Element && Boolean(target.closest("button, input, a, [role='button']"));
}

function getTouchAt(
  touches: { length: number; item?: (index: number) => { clientX: number; clientY: number } | null; [index: number]: { clientX: number; clientY: number } | undefined },
  index: number,
): { clientX: number; clientY: number } | null {
  return touches.item?.(index) ?? touches[index] ?? null;
}

function getPlayerTapZone(x: number, shellWidth: number): PlayerTapZone {
  const width = Math.max(1, shellWidth);
  const ratio = x / width;
  if (ratio <= DOUBLE_TAP_EDGE_ZONE) return "left-seek";
  if (ratio >= 1 - DOUBLE_TAP_EDGE_ZONE) return "right-seek";
  if (ratio >= CENTER_TAP_MIN && ratio <= CENTER_TAP_MAX) return "center";
  return "surface";
}

function supportsMiniPlayer(video: MiniPlayerVideo | null): boolean {
  if (typeof document === "undefined" || !video) return false;
  const pictureDocument = document as MiniPlayerDocument;
  return Boolean(
    (pictureDocument.pictureInPictureEnabled && typeof video.requestPictureInPicture === "function") ||
      video.webkitSupportsPresentationMode?.("picture-in-picture"),
  );
}

function shouldPreferAppMiniPlayer(): boolean {
  if (typeof window === "undefined") return false;
  if (typeof window.matchMedia !== "function") return false;
  return window.matchMedia("(max-width: 760px), (pointer: coarse)").matches;
}

function getContainerLabel(item: JellyfinItem): string {
  const sourcePath = item.MediaSources?.[0]?.Path ?? item.Path ?? "";
  const extension = sourcePath.split(/[?#]/)[0]?.split(".").pop();
  return extension ? extension.toLowerCase() : "unknown";
}

function getMediaCodecSummary(item: JellyfinItem): { container: string; video: string; audio: string; transcodeLikely: boolean } {
  const container = getContainerLabel(item);
  const streams = item.MediaStreams ?? [];
  const videoStream = streams.find((stream) => stream.Type?.toLowerCase() === "video");
  const audioStream = streams.find((stream) => stream.Type?.toLowerCase() === "audio");
  const video = [videoStream?.Codec, videoStream?.Width && videoStream?.Height ? `${videoStream.Width}x${videoStream.Height}` : ""]
    .filter(Boolean)
    .join(" ") || "unknown";
  const audio = [audioStream?.Codec, audioStream?.Channels ? `${audioStream.Channels}ch` : ""].filter(Boolean).join(" ") || "unknown";
  const videoCodec = videoStream?.Codec?.toLowerCase() ?? "";
  const audioCodec = audioStream?.Codec?.toLowerCase() ?? "";
  const directFriendly = container === "mp4" && (!videoCodec || videoCodec === "h264" || videoCodec === "avc1") && (!audioCodec || ["aac", "mp3", "ac3"].includes(audioCodec));
  return { container, video, audio, transcodeLikely: !directFriendly };
}

function getRouteHint(): string {
  if (typeof window === "undefined") return "unknown";
  const host = window.location.hostname.toLowerCase();
  if (host.includes("tail") || host.startsWith("100.")) return "Tailscale";
  if (host === "localhost" || host === "127.0.0.1") return "local";
  if (/^(10\.|192\.168\.|172\.(1[6-9]|2\d|3[0-1])\.)/.test(host)) return "LAN";
  return host || "unknown";
}

function getInitialPlaybackMode(): PlaybackSourceMode {
  if (typeof window !== "undefined" && window.location.protocol === "https:") return "proxied stream";
  return "direct stream";
}

function getDirectPlaybackSourceClass(item: JellyfinItem, directUrl: string): PlaybackSourceClass {
  const sourcePath = item.MediaSources?.[0]?.Path ?? item.Path ?? "";
  const isMp4 = sourcePath.toLowerCase().split(/[?#]/)[0].endsWith(".mp4") || getContainerLabel(item) === "mp4";
  if (directUrl.startsWith("/api/spiritflix/stream")) return "canonical_mp4";
  if (isMp4) return "jellyfin_direct_mp4";
  return "jellyfin_direct_mp4";
}

function isPlaybackAbort(error: unknown): boolean {
  return error instanceof DOMException && error.name === "AbortError";
}

function SortableQueueItem({
  client,
  item,
  index,
  isCurrent,
  onSelect,
}: {
  client: JellyfinClient;
  item: JellyfinItem;
  index: number;
  isCurrent: boolean;
  onSelect: () => void;
}) {
  const {
    attributes,
    listeners,
    setActivatorNodeRef,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({
    id: getQueueDndId(item.Id),
    animateLayoutChanges: () => false,
    transition: {
      duration: 115,
      easing: "cubic-bezier(0.2, 0, 0, 1)",
    },
  });

  const style: CSSProperties = {
    transform: CSS.Transform.toString(transform),
    transition: transition ?? undefined,
    opacity: isDragging ? 0.58 : 1,
    pointerEvents: isDragging ? "none" : undefined,
    willChange: transform ? "transform" : undefined,
  };

  return (
    <div
      className={`spiritflix-player__queue-item ${isCurrent ? "is-current" : ""}`}
      ref={setNodeRef}
      style={style}
      {...attributes}
      role="group"
      tabIndex={-1}
    >
      <button
        className="spiritflix-player__queue-drag"
        type="button"
        ref={setActivatorNodeRef}
        aria-label={`Drag ${item.Name} to reorder queue`}
        title="Drag to reorder"
        {...listeners}
      >
        <GripVertical size={17} aria-hidden="true" />
      </button>
      <button
        className="spiritflix-player__queue-select"
        type="button"
        onClick={onSelect}
        aria-label={`${String(index + 1).padStart(2, "0")} ${item.Name}`}
        aria-current={isCurrent ? "true" : undefined}
      >
        <span className="spiritflix-player__queue-index">{String(index + 1).padStart(2, "0")}</span>
        <span className="spiritflix-player__queue-thumb" aria-hidden="true">
          <SpiritFlixImage
            client={client}
            item={item}
            type="Primary"
            width={112}
            alt=""
            fallback={<span className="spiritflix-player__queue-thumb-fallback" />}
          />
        </span>
        <strong title={item.Name}>{item.Name}</strong>
      </button>
    </div>
  );
}

export function SpiritFlixPlayer({
  client,
  item,
  queue,
  libraryItems = [],
  startPositionTicks,
  onPlaybackProgress,
  onToggleFavorite,
  onSelectItem,
  onShuffleQueue,
  onPlayModelShuffle,
  onReorderQueue,
  onDeleteItem,
  onClose,
}: SpiritFlixPlayerProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const shellRef = useRef<HTMLElement | null>(null);
  const lastReportedTicksRef = useRef(0);
  const lastUiProgressAtRef = useRef(0);
  const lastUiTimeAtRef = useRef(0);
  const lastPlaybackReportAtRef = useRef(0);
  const firstNonZeroReportRef = useRef(false);
  const endedRef = useRef(false);
  const hideTimer = useRef<number | null>(null);
  const volumeHideTimer = useRef<number | null>(null);
  const feedbackTimer = useRef<number | null>(null);
  const appWidgetHideTimer = useRef<number | null>(null);
  const tapRevealTimer = useRef<number | null>(null);
  const feedbackIdRef = useRef(0);
  const usingHlsRef = useRef(false);
  const playbackModeRef = useRef<PlaybackSourceMode>(getInitialPlaybackMode());
  const waitingSinceRef = useRef<number | null>(null);
  const itemRef = useRef(item);
  const previousItemIdRef = useRef(item.Id);
  const pointerStartRef = useRef<{ x: number; y: number; time: number; currentTime: number } | null>(null);
  const lastTapRef = useRef<{ time: number; x: number; y: number; zone: SeekTapZone } | null>(null);
  const lastPointerTapAtRef = useRef(0);
  const touchTapStartRef = useRef<{ x: number; y: number; time: number; currentTime: number; isSeeking: boolean } | null>(null);
  const pinchStartRef = useRef<{ startDistance: number; currentDistance: number } | null>(null);
  const suppressPointerUntilRef = useRef(0);
  const suppressTouchUntilRef = useRef(0);
  const lastTouchInteractionAtRef = useRef(0);
  const volumeRef = useRef(getStoredVolume());
  const mutedRef = useRef(getStoredMuted());
  const repeatModeRef = useRef<RepeatMode>(getStoredRepeatMode());
  const lastQueueDragPairRef = useRef<string | null>(null);
  const manualTagDraftDirtyRef = useRef(false);
  const manualModelDraftDirtyRef = useRef(false);
  const isTagEditorOpenRef = useRef(false);
  const isModelEditorOpenRef = useRef(false);
  const shuffleHoldTimerRef = useRef<number | null>(null);
  const didHoldShuffleRef = useRef(false);
  const autoFaceModelApplyKeyRef = useRef("");
  const saveManualModelRef = useRef<(modelNameInput?: string) => Promise<void>>(async () => undefined);

  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(() => getStoredMuted());
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showControls, setShowControls] = useState(true);
  const [controlsHiddenByUser, setControlsHiddenByUser] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(() => getStoredVolume());
  const [isVolumeOpen, setIsVolumeOpen] = useState(false);
  const [fitMode, setFitMode] = useState<FitMode>(() => getStoredFitMode());
  const [videoAspectRatio, setVideoAspectRatio] = useState(16 / 9);
  const [shellSize, setShellSize] = useState({ width: 0, height: 0 });
  const [streamError, setStreamError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [usingHls, setUsingHls] = useState(false);
  const [playbackMode, setPlaybackMode] = useState<PlaybackSourceMode>(getInitialPlaybackMode);
  const [playbackSourceClass, setPlaybackSourceClass] = useState<PlaybackSourceClass>(() =>
    getInitialPlaybackMode() === "proxied stream" ? "canonical_mp4" : "jellyfin_direct_mp4",
  );
  const [playbackSourceReason, setPlaybackSourceReason] = useState("initial direct MP4 preference");
  const [mobileOptimizedSource, setMobileOptimizedSource] = useState<MobileOptimizedSource | null>(null);
  const [systemDiagnostics, setSystemDiagnostics] = useState<SpiritFlixSystemDiagnostics | null>(null);
  const [diagnosticsOpen, setDiagnosticsOpen] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const [endedAtQueueEnd, setEndedAtQueueEnd] = useState(false);
  const [repeatMode, setRepeatMode] = useState<RepeatMode>(() => getStoredRepeatMode());
  const [miniPlayerSupported, setMiniPlayerSupported] = useState(false);
  const [isNativeMiniPlayer, setIsNativeMiniPlayer] = useState(false);
  const [isAppMiniPlayer, setIsAppMiniPlayer] = useState(false);
  const [isQueueOpen, setIsQueueOpen] = useState(false);
  const [isShufflePickerOpen, setIsShufflePickerOpen] = useState(false);
  const [isToolDrawerOpen, setIsToolDrawerOpen] = useState(false);
  const [playbackFeedback, setPlaybackFeedback] = useState<PlaybackFeedback | null>(null);
  const [isTagEditorOpen, setIsTagEditorOpen] = useState(false);
  const [manualTagIndex, setManualTagIndex] = useState<SpiritFlixManualTagIndex | null>(null);
  const [manualTagRecord, setManualTagRecord] = useState<SpiritFlixManualTagRecord | null>(null);
  const [draftManualTags, setDraftManualTags] = useState<string[]>([]);
  const [newManualTag, setNewManualTag] = useState("");
  const [manualTagsLoading, setManualTagsLoading] = useState(false);
  const [manualTagsSaving, setManualTagsSaving] = useState(false);
  const [manualTagsError, setManualTagsError] = useState("");
  const [manualTagsSavedAt, setManualTagsSavedAt] = useState("");
  const [isModelEditorOpen, setIsModelEditorOpen] = useState(false);
  const [manualModelIndex, setManualModelIndex] = useState<SpiritFlixManualModelIndex | null>(null);
  const [manualModelRecord, setManualModelRecord] = useState<SpiritFlixManualModelRecord | null>(null);
  const [draftModelName, setDraftModelName] = useState("");
  const [manualModelLoading, setManualModelLoading] = useState(false);
  const [manualModelSaving, setManualModelSaving] = useState(false);
  const [manualModelError, setManualModelError] = useState("");
  const [manualModelSavedAt, setManualModelSavedAt] = useState("");
  const [faceMetadata, setFaceMetadata] = useState<FaceOrganizerMetadataResponse | null>(null);
  const [faceLearningRecord, setFaceLearningRecord] = useState<SpiritFlixFaceLearningRecord | null>(null);
  const [faceLearningError, setFaceLearningError] = useState("");
  const [isDeleteEditorOpen, setIsDeleteEditorOpen] = useState(false);
  const [deletePreview, setDeletePreview] = useState<SpiritFlixDeletePreview | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [deleteExecuting, setDeleteExecuting] = useState(false);
  const [deleteError, setDeleteError] = useState("");

  const isSeriesPlayback = isSeriesPlaybackItem(item);
  const seriesKey = getSeriesPlaybackKey(item);
  const [seriesAudioState, setSeriesAudioState] = useState<{ seriesKey: string; preference: SeriesAudioPreference }>(() => {
    const initialSeriesKey = getSeriesPlaybackKey(item);
    return { seriesKey: initialSeriesKey, preference: getStoredSeriesAudioPreference(initialSeriesKey) };
  });
  const [audioTrackSwitchAvailable, setAudioTrackSwitchAvailable] = useState(false);
  const seriesAudioPreference =
    seriesAudioState.seriesKey === seriesKey ? seriesAudioState.preference : getStoredSeriesAudioPreference(seriesKey);
  const seriesQueueItems = useMemo(
    () => getSeriesPlaybackQueue(item, [...(queue?.items ?? []), ...libraryItems]),
    [item, libraryItems, queue?.items],
  );
  const queueItems = useMemo(
    () => (isSeriesPlayback && seriesQueueItems.length ? seriesQueueItems : queue?.items ?? [item]),
    [isSeriesPlayback, item, queue?.items, seriesQueueItems],
  );
  const originalQueueItems = useMemo(
    () => (queue?.originalItems?.length ? queue.originalItems : queueItems),
    [queue, queueItems],
  );
  const orientationCounts = useMemo(() => countItemsByVideoOrientation(originalQueueItems), [originalQueueItems]);
  const queueIndex = queueItems.findIndex((queueItem) => queueItem.Id === item.Id);
  const currentIndex = queueIndex >= 0 ? queueIndex : queue?.currentIndex ?? 0;
  const previousItem = currentIndex > 0 ? queueItems[currentIndex - 1] : null;
  const nextItem = currentIndex < queueItems.length - 1 ? queueItems[currentIndex + 1] : null;
  const upNextTitle = nextItem?.Name ?? null;
  const audioStreams = useMemo(() => item.MediaStreams?.filter((stream) => stream.Type?.toLowerCase() === "audio") ?? [], [item.MediaStreams]);
  const hasSeriesAudioChoices =
    isSeriesPlayback && (audioStreams.length >= 2 || (seriesAudioState.seriesKey === seriesKey && audioTrackSwitchAvailable));
  const nextSeriesAudioPreference: SeriesAudioPreference = seriesAudioPreference === "dub" ? "sub" : "dub";
  const previousLabel = isSeriesPlayback ? "Previous episode" : "Previous video";
  const nextLabel = isSeriesPlayback ? "Next episode" : "Next video";
  const showLibraryPlayerTools = !isSeriesPlayback;
  const showQueueTool = queueItems.length >= 2;
  const showToolOverflow = showLibraryPlayerTools || showQueueTool;
  const isFavorite = Boolean(item.UserData?.IsFavorite);
  const repeatLabel =
    repeatMode === "one" ? "Repeat current video" : repeatMode === "queue" ? "Repeat queue" : "Repeat off";
  const isShuffled = Boolean(queue?.isShuffled);
  const shuffleLabel = isShuffled
    ? `Shuffle on for ${queue?.sourceTitle ?? "current queue"}`
    : `Shuffle off for ${queue?.sourceTitle ?? "current queue"}`;
  const isMiniPlayerActive = isNativeMiniPlayer || isAppMiniPlayer;
  const miniPlayerLabel = isMiniPlayerActive ? "Exit mini player" : "Mini player";
  const sourcePath = getItemSourcePath(item);
  const deleteSourcePath = normalizeSpiritFlixMediaPath(sourcePath);
  const canDeleteFromYes = isPlayableItem(item) && isYesFolderVideoPath(sourcePath);
  const currentFaceMatch = faceMetadata?.videos[item.Id];
  const faceModelSuggestion = currentFaceMatch?.primaryPerformer?.name && currentFaceMatch.primaryPerformer.name !== "unknown performer"
    ? currentFaceMatch
    : undefined;
  const faceSuggestionConfidence = getFaceConfidenceValue(faceModelSuggestion);
  const shouldAutoApplyFaceModel = Boolean(
    faceModelSuggestion?.primaryPerformer?.name &&
      typeof faceSuggestionConfidence === "number" &&
      faceSuggestionConfidence > AUTO_FACE_MODEL_CONFIDENCE,
  );
  const activeModelName = manualModelRecord?.modelName || item.ManualModelName || getInferredModelName(item);
  const knownCurrentModelName =
    manualModelRecord?.modelName ||
    item.ManualModelName ||
    (shouldAutoApplyFaceModel || faceModelSuggestion?.status === "confirmed"
      ? faceModelSuggestion?.primaryPerformer?.name ?? ""
      : "");
  const hasSavedManualModel = Boolean(manualModelRecord?.modelName);
  const faceSuggestionMatchesCurrentModel =
    Boolean(faceModelSuggestion?.primaryPerformer?.name) &&
    getModelOptionKey(faceModelSuggestion?.primaryPerformer?.name ?? "") === getModelOptionKey(activeModelName);
  const faceSuggestionConfirmed = faceSuggestionMatchesCurrentModel && faceModelSuggestion?.status === "confirmed";
  const faceSuggestionAutoApplied = shouldAutoApplyFaceModel && faceSuggestionMatchesCurrentModel && hasSavedManualModel;
  const modelSystemStatus = hasSavedManualModel
    ? faceSuggestionConfirmed
      ? "Saved + face confirmed"
      : faceSuggestionAutoApplied
        ? "Auto-saved face match"
      : "Saved in system"
    : faceModelSuggestion?.primaryPerformer
      ? "Face suggestion only"
      : "Not saved";
  const showFaceLearningStatus = Boolean(faceLearningRecord && !faceSuggestionConfirmed);
  const sortTagOptions = useCallback((tags: string[]) => (
    tags.sort((left, right) => {
      const leftSelected = draftManualTags.includes(left);
      const rightSelected = draftManualTags.includes(right);
      return Number(rightSelected) - Number(leftSelected) || left.localeCompare(right);
    })
  ), [draftManualTags]);
  const actionManualTags = useMemo(() => {
    const tagSet = new Set<string>();
    manualTagIndex?.tags.forEach((tag) => tagSet.add(tag.tag));
    draftManualTags.filter((tag) => getSpiritFlixManualTagScope(tag) === "video").forEach((tag) => tagSet.add(tag));
    return sortTagOptions(Array.from(tagSet));
  }, [draftManualTags, manualTagIndex, sortTagOptions]);
  const modelAttributeTags = useMemo(() => {
    const tagSet = new Set<string>();
    manualTagIndex?.modelAttributes?.forEach((tag) => tagSet.add(tag.tag));
    draftManualTags.filter((tag) => getSpiritFlixManualTagScope(tag) === "model").forEach((tag) => tagSet.add(tag));
    return sortTagOptions(Array.from(tagSet));
  }, [draftManualTags, manualTagIndex, sortTagOptions]);
  const knownModelOptions = useMemo(() => {
    const options = new Map<string, string>();
    const addOption = (name: string) => {
      const modelName = canonicalizeManualModelName(name);
      if (!modelName) return;
      const key = getModelOptionKey(modelName);
      if (!options.has(key)) options.set(key, modelName);
    };
    manualModelIndex?.models.forEach((model) => addOption(model.modelName));
    addOption(faceModelSuggestion?.primaryPerformer?.name ?? "");
    originalQueueItems.forEach((queueItem) => addOption(getInferredModelName(queueItem)));
    addOption(getInferredModelName(item));
    addOption(draftModelName);
    return Array.from(options.values()).sort((left, right) => {
      const leftSelected = getModelOptionKey(left) === getModelOptionKey(draftModelName);
      const rightSelected = getModelOptionKey(right) === getModelOptionKey(draftModelName);
      return Number(rightSelected) - Number(leftSelected) || left.localeCompare(right);
    });
  }, [draftModelName, faceModelSuggestion?.primaryPerformer?.name, item, manualModelIndex, originalQueueItems]);
  const modelShuffleItems = useMemo(() => {
    const currentModelKey = getModelOptionKey(knownCurrentModelName);
    if (!currentModelKey) return [];
    const candidates = new Map<string, JellyfinItem>();
    [item, ...libraryItems, ...originalQueueItems, ...queueItems].forEach((candidate) => {
      if (candidate?.Id && isPlayableItem(candidate) && !candidates.has(candidate.Id)) candidates.set(candidate.Id, candidate);
    });
    return Array.from(candidates.values()).filter((candidate) => {
      const faceMatch = faceMetadata?.videos[candidate.Id];
      const candidateModelName =
        candidate.Id === item.Id
          ? knownCurrentModelName
          : candidate.ManualModelName ||
            (faceMatch?.status === "confirmed" || (getFaceConfidenceValue(faceMatch) ?? 0) > AUTO_FACE_MODEL_CONFIDENCE
              ? faceMatch?.primaryPerformer?.name ?? ""
              : "");
      return getModelOptionKey(candidateModelName) === currentModelKey;
    });
  }, [faceMetadata, item, knownCurrentModelName, libraryItems, originalQueueItems, queueItems]);
  const relatedModelTagItems = useMemo(() => {
    const modelName = getModelOptionKey(manualModelRecord?.modelName || item.ManualModelName || getInferredModelName(item));
    if (!modelName) return [];
    const candidates = libraryItems.length ? libraryItems : originalQueueItems;
    return candidates
      .filter((candidate) => candidate.Id !== item.Id && getModelOptionKey(candidate.ManualModelName || getInferredModelName(candidate)) === modelName)
      .map((candidate) => ({
        itemId: candidate.Id,
        filePath: candidate.MediaSources?.[0]?.Path ?? candidate.Path,
      }));
  }, [item, libraryItems, manualModelRecord?.modelName, originalQueueItems]);
  const getRelatedItemsForModelName = useCallback(
    (modelNameInput: string) => {
      const modelName = getModelOptionKey(modelNameInput);
      if (!modelName) return [];
      const candidates = libraryItems.length ? libraryItems : originalQueueItems;
      return candidates
        .filter((candidate) => candidate.Id !== item.Id && getModelOptionKey(candidate.ManualModelName || getInferredModelName(candidate)) === modelName)
        .map((candidate) => ({
          itemId: candidate.Id,
          filePath: candidate.MediaSources?.[0]?.Path ?? candidate.Path,
        }));
    },
    [item.Id, libraryItems, originalQueueItems],
  );
  const getTitleMatchedItemsForModelName = useCallback(
    (modelNameInput: string) =>
      getTitleMatchedModelItems(modelNameInput, [item, ...libraryItems, ...originalQueueItems, ...queueItems], item),
    [item, libraryItems, originalQueueItems, queueItems],
  );
  const mediaDiagnostics = useMemo(() => getMediaCodecSummary(item), [item]);
  const routeHint = typeof window === "undefined" ? "unknown" : getRouteHint();
  const canonicalMp4Present = mediaDiagnostics.container === "mp4";
  const rangeSupport = playbackSourceClass === "mac_optimized_mp4" || playbackSourceClass === "canonical_mp4";
  const queueDndIds = useMemo(() => queueItems.map((queueItem) => getQueueDndId(queueItem.Id)), [queueItems]);
  const queueDndSensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 5 },
    }),
    useSensor(TouchSensor, {
      activationConstraint: { delay: 150, tolerance: 6 },
    }),
  );

  useEffect(() => {
    isTagEditorOpenRef.current = isTagEditorOpen;
  }, [isTagEditorOpen]);

  useEffect(() => {
    isModelEditorOpenRef.current = isModelEditorOpen;
  }, [isModelEditorOpen]);

  useEffect(() => {
    itemRef.current = item;
    if (previousItemIdRef.current === item.Id) return undefined;
    previousItemIdRef.current = item.Id;
    const resetTimer = window.setTimeout(() => {
      setIsTagEditorOpen(false);
      setManualTagRecord(null);
      setDraftManualTags([]);
      setNewManualTag("");
      setManualTagsError("");
      setManualTagsSavedAt("");
      setIsModelEditorOpen(false);
      setManualModelRecord(null);
      setDraftModelName("");
      setManualModelError("");
      setManualModelSavedAt("");
      setFaceMetadata(null);
      setFaceLearningRecord(null);
      setFaceLearningError("");
      setIsDeleteEditorOpen(false);
      setDeletePreview(null);
      setDeleteError("");
      manualTagDraftDirtyRef.current = false;
      manualModelDraftDirtyRef.current = false;
    }, 0);
    return () => window.clearTimeout(resetTimer);
  }, [item]);

  const emitPlaybackProgress = useCallback(
    (positionTicks: number, isEnded = false) => {
      onPlaybackProgress({
        itemId: item.Id,
        item: itemRef.current,
        positionTicks,
        isEnded,
      });
    },
    [item.Id, onPlaybackProgress],
  );

  const flushPlaybackProgress = useCallback(
    (
      event: "Progress" | "Stopped" = "Progress",
      options: { isPaused?: boolean; keepalive?: boolean; updateUi?: boolean } = {},
    ) => {
      const video = videoRef.current;
      const positionSeconds = video?.currentTime || ticksToSeconds(lastReportedTicksRef.current);
      const positionTicks = secondsToTicks(positionSeconds);
      if (positionTicks <= 0) return;

      lastReportedTicksRef.current = positionTicks;
      lastPlaybackReportAtRef.current = performance.now();
      if (options.updateUi) {
        setCurrentTime(positionSeconds);
        emitPlaybackProgress(positionTicks, false);
      }
      void client.reportPlayback(
        item.Id,
        event,
        positionTicks,
        options.isPaused ?? video?.paused ?? false,
        { keepalive: options.keepalive },
      );
    },
    [client, emitPlaybackProgress, item.Id],
  );

  const scheduleControlsHide = useCallback(() => {
    if (hideTimer.current) window.clearTimeout(hideTimer.current);
    const video = videoRef.current;
    const shouldHide = video ? !video.paused && !video.ended : isPlaying;
    if (!shouldHide) return;
    hideTimer.current = window.setTimeout(() => {
      if (isTagEditorOpenRef.current || isModelEditorOpenRef.current) return;
      const activeElement = document.activeElement;
      if (activeElement instanceof HTMLElement && shellRef.current?.contains(activeElement)) {
        activeElement.blur();
      }
      setShowControls(false);
      setIsVolumeOpen(false);
      setIsShufflePickerOpen(false);
      setIsToolDrawerOpen(false);
    }, 2600);
  }, [isPlaying]);

  const closeAppWidgets = useCallback(() => {
    if (appWidgetHideTimer.current) {
      window.clearTimeout(appWidgetHideTimer.current);
      appWidgetHideTimer.current = null;
    }
    setIsTagEditorOpen(false);
    setIsModelEditorOpen(false);
    setIsDeleteEditorOpen(false);
  }, [setIsDeleteEditorOpen, setIsModelEditorOpen, setIsTagEditorOpen]);

  const appWidgetContainsFocus = useCallback(() => {
    const activeElement = document.activeElement;
    return (
      activeElement instanceof HTMLElement &&
      Boolean(activeElement.closest(".spiritflix-tag-editor, .spiritflix-model-editor"))
    );
  }, []);

  const scheduleAppWidgetClose = useCallback(() => {
    if (appWidgetHideTimer.current) window.clearTimeout(appWidgetHideTimer.current);
    appWidgetHideTimer.current = window.setTimeout(() => {
      appWidgetHideTimer.current = null;
      if (appWidgetContainsFocus()) {
        return;
      }
      closeAppWidgets();
      scheduleControlsHide();
    }, APP_WIDGET_IDLE_CLOSE_MS);
  }, [appWidgetContainsFocus, closeAppWidgets, scheduleControlsHide]);

  const keepAppWidgetInteraction = useCallback(
    (event: React.SyntheticEvent<HTMLElement>) => {
      event.stopPropagation();
      scheduleAppWidgetClose();
    },
    [scheduleAppWidgetClose],
  );

  const revealControls = useCallback(
    (keepVisible = false) => {
      setControlsHiddenByUser(false);
      setShowControls(true);
      if (hideTimer.current) window.clearTimeout(hideTimer.current);
      if (!keepVisible) scheduleControlsHide();
    },
    [scheduleControlsHide],
  );

  const scheduleVolumeClose = useCallback(() => {
    if (volumeHideTimer.current) window.clearTimeout(volumeHideTimer.current);
    volumeHideTimer.current = window.setTimeout(() => {
      const activeElement = document.activeElement;
      if (activeElement instanceof HTMLElement && shellRef.current?.contains(activeElement)) {
        activeElement.blur();
      }
      setIsVolumeOpen(false);
      volumeHideTimer.current = null;
    }, 3000);
  }, []);

  const clearTapRevealTimer = useCallback(() => {
    if (!tapRevealTimer.current) return;
    window.clearTimeout(tapRevealTimer.current);
    tapRevealTimer.current = null;
  }, []);

  const scheduleTapReveal = useCallback(() => {
    clearTapRevealTimer();
    tapRevealTimer.current = window.setTimeout(() => {
      tapRevealTimer.current = null;
      revealControls();
    }, DOUBLE_TAP_MAX_MS);
  }, [clearTapRevealTimer, revealControls]);

  const hideControls = useCallback(() => {
    if (hideTimer.current) window.clearTimeout(hideTimer.current);
    if (volumeHideTimer.current) window.clearTimeout(volumeHideTimer.current);
    const activeElement = document.activeElement;
    if (activeElement instanceof HTMLElement && shellRef.current?.contains(activeElement)) {
      activeElement.blur();
    }
    setControlsHiddenByUser(true);
    setShowControls(false);
    setIsVolumeOpen(false);
    setIsShufflePickerOpen(false);
    setIsToolDrawerOpen(false);
    closeAppWidgets();
  }, [closeAppWidgets]);

  const flashPlaybackFeedback = useCallback((feedback: PlaybackFeedbackInput) => {
    feedbackIdRef.current += 1;
    setPlaybackFeedback({ id: feedbackIdRef.current, ...feedback } as PlaybackFeedback);
    if (feedbackTimer.current) window.clearTimeout(feedbackTimer.current);
    feedbackTimer.current = window.setTimeout(() => setPlaybackFeedback(null), PLAYBACK_FEEDBACK_MS);
  }, []);

  const flashTapFeedback = useCallback(
    (kind: "play" | "pause") => {
      flashPlaybackFeedback({ kind });
    },
    [flashPlaybackFeedback],
  );

  const flashSeekFeedback = useCallback(
    (seconds: number) => {
      const roundedSeconds = Math.max(1, Math.abs(Math.round(seconds)));
      flashPlaybackFeedback({
        kind: seconds < 0 ? "seek-back" : "seek-forward",
        seconds: roundedSeconds,
      });
    },
    [flashPlaybackFeedback],
  );

  const seekTo = useCallback((seconds: number) => {
    const video = videoRef.current;
    if (!video) return;
    video.currentTime = Math.max(0, Math.min(video.duration || Number.MAX_SAFE_INTEGER, seconds));
    setCurrentTime(video.currentTime);
  }, []);

  const seekBy = useCallback(
    (seconds: number, options: { feedback?: boolean } = {}) => {
      const video = videoRef.current;
      if (!video) return;
      seekTo(video.currentTime + seconds);
      if (options.feedback !== false) flashSeekFeedback(seconds);
      revealControls();
    },
    [flashSeekFeedback, revealControls, seekTo],
  );

  const seekFromTouchDelta = useCallback(
    (startTime: number, dx: number) => {
      const secondsDelta = Math.max(
        -TOUCH_SEEK_MAX_SECONDS,
        Math.min(TOUCH_SEEK_MAX_SECONDS, dx / TOUCH_SEEK_PX_PER_SECOND),
      );
      seekTo(startTime + secondsDelta);
      flashSeekFeedback(secondsDelta || (dx < 0 ? -1 : 1));
    },
    [flashSeekFeedback, seekTo],
  );

  const togglePlay = useCallback(() => {
    const video = videoRef.current;
    if (!video) return;
    if (video.paused) {
      flashTapFeedback("play");
      void video.play().then(() => {
        scheduleControlsHide();
      }).catch(() => setShowControls(true));
    } else {
      flashTapFeedback("pause");
      video.pause();
    }
    revealControls();
  }, [flashTapFeedback, revealControls, scheduleControlsHide]);

  const setFit = useCallback((mode: FitMode) => {
    setFitMode(mode);
    window.localStorage.setItem(FIT_STORAGE_KEY, mode);
  }, []);

  const toggleFullscreen = useCallback(() => {
    const shell = shellRef.current;
    const video = videoRef.current as (HTMLVideoElement & { webkitEnterFullscreen?: () => void }) | null;
    if (document.fullscreenElement) {
      void document.exitFullscreen();
      return;
    }
    if (shell?.requestFullscreen) {
      void shell.requestFullscreen();
      return;
    }
    video?.webkitEnterFullscreen?.();
  }, []);

  const toggleMiniPlayer = useCallback(() => {
    const video = videoRef.current as MiniPlayerVideo | null;
    if (!video) return;
    const pictureDocument = document as MiniPlayerDocument;

    const enterAppMiniPlayer = () => {
      setIsAppMiniPlayer(true);
      setIsQueueOpen(false);
      setIsTagEditorOpen(false);
      setIsModelEditorOpen(false);
      setIsDeleteEditorOpen(false);
      setIsToolDrawerOpen(false);
      setIsShufflePickerOpen(false);
      hideControls();
    };

    const toggle = async () => {
      if (isAppMiniPlayer) {
        setIsAppMiniPlayer(false);
        revealControls();
        return;
      }

      if (pictureDocument.pictureInPictureElement) {
        await pictureDocument.exitPictureInPicture?.();
        setIsNativeMiniPlayer(false);
        revealControls();
        return;
      }

      if (video.webkitPresentationMode === "picture-in-picture") {
        video.webkitSetPresentationMode?.("inline");
        setIsNativeMiniPlayer(false);
        revealControls();
        return;
      }

      if (shouldPreferAppMiniPlayer()) {
        enterAppMiniPlayer();
        return;
      }

      if (pictureDocument.pictureInPictureEnabled && video.requestPictureInPicture) {
        await video.requestPictureInPicture();
        setIsNativeMiniPlayer(true);
        revealControls();
        return;
      }

      if (video.webkitSupportsPresentationMode?.("picture-in-picture")) {
        video.webkitSetPresentationMode?.("picture-in-picture");
        setIsNativeMiniPlayer(true);
        revealControls();
        return;
      }

      enterAppMiniPlayer();
    };

    void toggle().catch(() => {
      enterAppMiniPlayer();
    });
  }, [
    hideControls,
    isAppMiniPlayer,
    revealControls,
    setIsAppMiniPlayer,
    setIsDeleteEditorOpen,
    setIsModelEditorOpen,
    setIsNativeMiniPlayer,
    setIsQueueOpen,
    setIsShufflePickerOpen,
    setIsTagEditorOpen,
    setIsToolDrawerOpen,
  ]);

  const selectQueueItem = useCallback(
    (target: JellyfinItem | null) => {
      if (!target) return;
      setEndedAtQueueEnd(false);
      onSelectItem(target);
    },
    [onSelectItem],
  );

  const cycleRepeatMode = () => {
    setRepeatMode((current) => {
      const next = current === "off" ? "queue" : current === "queue" ? "one" : "off";
      repeatModeRef.current = next;
      window.localStorage.setItem(REPEAT_STORAGE_KEY, next);
      if (videoRef.current) videoRef.current.loop = next === "one";
      return next;
    });
    revealControls();
  };

  const shuffleCurrentQueue = () => {
    onShuffleQueue(item.Id);
    setIsShufflePickerOpen(false);
    revealControls();
  };

  const shuffleCurrentQueueByOrientation = (orientation: SpiritFlixVideoOrientation) => {
    onShuffleQueue(item.Id, orientation);
    setIsShufflePickerOpen(false);
    revealControls();
  };

  const playKnownModelShuffle = () => {
    const modelName = canonicalizeManualModelName(knownCurrentModelName);
    if (!modelName || !modelShuffleItems.length) return;
    onPlayModelShuffle(item, modelName, modelShuffleItems);
    setIsModelEditorOpen(false);
    revealControls();
  };

  const clearShuffleHoldTimer = () => {
    if (shuffleHoldTimerRef.current) {
      window.clearTimeout(shuffleHoldTimerRef.current);
      shuffleHoldTimerRef.current = null;
    }
  };

  const startShuffleHold = () => {
    didHoldShuffleRef.current = false;
    clearShuffleHoldTimer();
    if (queueItems.length < 2) return;
    shuffleHoldTimerRef.current = window.setTimeout(() => {
      shuffleHoldTimerRef.current = null;
      didHoldShuffleRef.current = true;
      setIsShufflePickerOpen(true);
      revealControls();
    }, 520);
  };

  const handleShuffleButtonClick = () => {
    if (didHoldShuffleRef.current) {
      didHoldShuffleRef.current = false;
      return;
    }
    shuffleCurrentQueue();
  };

  const toggleQueueDrawer = () => {
    setIsQueueOpen((open) => !open);
    revealControls();
  };

  const toggleSeriesAudioPreference = () => {
    const nextPreference = nextSeriesAudioPreference;
    setSeriesAudioState({ seriesKey, preference: nextPreference });
    storeSeriesAudioPreference(seriesKey, nextPreference);
    setAudioTrackSwitchAvailable(applyAudioPreferenceToVideo(videoRef.current, nextPreference));
    revealControls();
  };

  const toggleToolDrawer = () => {
    setIsToolDrawerOpen((open) => !open);
    revealControls();
  };

  const canonicalizeManualTag = (value: string) => value.trim().replace(/\s+/g, " ").toLowerCase();

  const loadManualTags = async () => {
    setManualTagsLoading(true);
    setManualTagsError("");
    try {
      const [indexResponse, itemResponse] = await Promise.all([
        fetch("/api/spiritflix/tags", { cache: "no-store" }),
        fetch(`/api/spiritflix/videos/${encodeURIComponent(item.Id)}/tags`, { cache: "no-store" }),
      ]);
      if (!indexResponse.ok || !itemResponse.ok) throw new Error("Manual tags could not be loaded.");
      const index = (await indexResponse.json()) as SpiritFlixManualTagIndex;
      const record = (await itemResponse.json()) as SpiritFlixManualTagRecord;
      setManualTagIndex(index);
      const safeRecord = { ...record, manualTags: Array.isArray(record.manualTags) ? record.manualTags : [] };
      setManualTagRecord(safeRecord);
      if (!manualTagDraftDirtyRef.current) {
        setDraftManualTags(safeRecord.manualTags);
      }
      if (item.ManualModelName) {
        void mergeKnownModelTagsIntoCurrentItem(item.ManualModelName, safeRecord.manualTags);
      }
    } catch {
      setManualTagsError("Manual tags could not be loaded.");
    } finally {
      setManualTagsLoading(false);
    }
  };

  const openTagEditor = () => {
    setIsTagEditorOpen(true);
    setIsModelEditorOpen(false);
    setIsDeleteEditorOpen(false);
    setNewManualTag("");
    manualTagDraftDirtyRef.current = false;
    revealControls(true);
    scheduleAppWidgetClose();
    void loadManualTags();
  };

  const saveManualTags = async (nextManualTags: string[]) => {
    manualTagDraftDirtyRef.current = true;
    setDraftManualTags(nextManualTags);
    setManualTagsSaving(true);
    setManualTagsError("");
    try {
      const response = await fetch(`/api/spiritflix/videos/${encodeURIComponent(item.Id)}/tags`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          filePath: item.MediaSources?.[0]?.Path ?? item.Path,
          manualTags: nextManualTags,
        }),
      });
      if (!response.ok) {
        const body = (await response.json().catch(() => null)) as { error?: string } | null;
        throw new Error(body?.error ?? "Manual tags could not be saved.");
      }
      const body = (await response.json()) as { record: SpiritFlixManualTagRecord; index: SpiritFlixManualTagIndex };
      const safeRecord = { ...body.record, manualTags: Array.isArray(body.record.manualTags) ? body.record.manualTags : [] };
      setManualTagRecord(safeRecord);
      setManualTagIndex(body.index);
      setDraftManualTags(safeRecord.manualTags);
      manualTagDraftDirtyRef.current = false;
      setManualTagsSavedAt(new Date().toISOString());
      scheduleAppWidgetClose();
      window.dispatchEvent(new CustomEvent(MANUAL_TAG_CHANGED_EVENT, { detail: { itemId: item.Id, manualTags: safeRecord.manualTags } }));
    } catch (error) {
      setManualTagsError(error instanceof Error ? error.message : "Manual tags could not be saved.");
    } finally {
      setManualTagsSaving(false);
    }
  };

  const mergeKnownModelTagsIntoCurrentItem = async (modelName: string, existingManualTags?: string[]) => {
    try {
      const modelTagResponse = await fetch(`/api/spiritflix/tags?modelName=${encodeURIComponent(modelName)}`, { cache: "no-store" });
      if (!modelTagResponse.ok) return;
      const modelTagBody = (await modelTagResponse.json().catch(() => null)) as { modelTags?: unknown } | null;
      const modelTags = Array.isArray(modelTagBody?.modelTags)
        ? modelTagBody.modelTags
            .map(canonicalizeManualTag)
            .filter((tag) => tag && getSpiritFlixManualTagScope(tag) === "model")
        : [];
      if (!modelTags.length) return;

      let currentManualTags = existingManualTags ?? (manualTagRecord?.itemId === item.Id ? manualTagRecord.manualTags : null);
      if (!currentManualTags) {
        const currentTagResponse = await fetch(`/api/spiritflix/videos/${encodeURIComponent(item.Id)}/tags`, { cache: "no-store" });
        if (!currentTagResponse.ok) return;
        const currentTagRecord = (await currentTagResponse.json().catch(() => null)) as { manualTags?: unknown } | null;
        currentManualTags = Array.isArray(currentTagRecord?.manualTags)
          ? currentTagRecord.manualTags.map(canonicalizeManualTag).filter(Boolean)
          : [];
      }

      const mergedTags = Array.from(new Set([...currentManualTags.map(canonicalizeManualTag).filter(Boolean), ...modelTags]))
        .sort((left, right) => left.localeCompare(right));
      if (mergedTags.join("\u0000") === currentManualTags.join("\u0000")) return;
      await saveManualTags(mergedTags);
    } catch {
      // Model assignment should still succeed if known attribute adoption cannot be loaded.
    }
  };

  const toggleManualTag = (tag: string) => {
    const nextManualTags = draftManualTags.includes(tag)
      ? draftManualTags.filter((existing) => existing !== tag)
      : [...draftManualTags, tag].sort((left, right) => left.localeCompare(right));
    void saveManualTags(nextManualTags);
  };

  const addDraftManualTag = () => {
    const tag = canonicalizeManualTag(newManualTag);
    if (!tag) {
      setManualTagsError("Enter a tag first.");
      return;
    }
    const nextManualTags = draftManualTags.includes(tag)
      ? draftManualTags
      : [...draftManualTags, tag].sort((left, right) => left.localeCompare(right));
    setNewManualTag("");
    void saveManualTags(nextManualTags);
  };

  const loadManualModel = useCallback(async () => {
    setManualModelLoading(true);
    setManualModelError("");
    try {
      const [indexResponse, itemResponse] = await Promise.all([
        fetch("/api/spiritflix/model-index", { cache: "no-store" }),
        fetch(`/api/spiritflix/videos/${encodeURIComponent(item.Id)}/model`, { cache: "no-store" }),
      ]);
      if (!itemResponse.ok) throw new Error("Manual model could not be loaded.");
      const index = indexResponse.ok
        ? ((await indexResponse.json()) as SpiritFlixManualModelIndex)
        : { schema: "spiritflix-manual-model-index/v1" as const, updatedAt: new Date(0).toISOString(), models: [] };
      const record = (await itemResponse.json()) as SpiritFlixManualModelRecord;
      setManualModelIndex(index);
      setManualModelRecord(record);
      if (!manualModelDraftDirtyRef.current) {
        setDraftModelName(record.modelName || item.ManualModelName || getInferredModelName(item));
      }
    } catch {
      setManualModelError("Manual model could not be loaded.");
    } finally {
      setManualModelLoading(false);
    }
  }, [item]);

  const loadPlayerFaceMetadata = useCallback(async () => {
    const byId = new Map<string, JellyfinItem>();
    [item, ...originalQueueItems, ...libraryItems].forEach((candidate) => {
      if (candidate?.Id && !byId.has(candidate.Id)) byId.set(candidate.Id, candidate);
    });
    try {
      const metadata = await client.getFaceOrganizerMetadata(Array.from(byId.values()));
      setFaceMetadata(metadata);
      setFaceLearningError("");
    } catch {
      setFaceLearningError("Face metadata is unavailable.");
    }
  }, [client, item, libraryItems, originalQueueItems]);

  const requestFaceLearning = useCallback(
    async (modelName: string, faceMatch?: FaceOrganizerVideoMatch, relatedItems = relatedModelTagItems) => {
      setFaceLearningError("");
      try {
        const response = await fetch(`/api/spiritflix/videos/${encodeURIComponent(item.Id)}/face-learning`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            filePath: item.MediaSources?.[0]?.Path ?? item.Path,
            modelName,
            sidecarPath: faceMatch?.sidecarPath,
            faceGuess: faceMatch?.primaryPerformer,
            relatedItems,
          }),
        });
        const body = (await response.json().catch(() => null)) as { record?: SpiritFlixFaceLearningRecord; error?: string } | null;
        if (!response.ok || !body?.record) throw new Error(body?.error ?? "Face learning could not be queued.");
        setFaceLearningRecord(body.record);
      } catch (error) {
        setFaceLearningError(error instanceof Error ? error.message : "Face learning could not be queued.");
      }
    },
    [item, relatedModelTagItems],
  );

  const openModelEditor = () => {
    setIsModelEditorOpen(true);
    setIsTagEditorOpen(false);
    setIsDeleteEditorOpen(false);
    manualModelDraftDirtyRef.current = false;
    setDraftModelName(manualModelRecord?.modelName || item.ManualModelName || getInferredModelName(item));
    revealControls(true);
    scheduleAppWidgetClose();
    void loadManualModel();
    void loadPlayerFaceMetadata();
  };

  const saveManualModel = async (modelNameInput = draftModelName) => {
    const modelName = canonicalizeManualModelName(modelNameInput);
    if (!modelName) {
      setManualModelError("Enter a model name first.");
      return;
    }
    manualModelDraftDirtyRef.current = true;
    setDraftModelName(modelName);
    setManualModelSaving(true);
    setManualModelError("");
    try {
      const response = await fetch(`/api/spiritflix/videos/${encodeURIComponent(item.Id)}/model`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          filePath: item.MediaSources?.[0]?.Path ?? item.Path,
          modelName,
          knownModelNames: knownModelOptions,
        }),
      });
      if (!response.ok) {
        const body = (await response.json().catch(() => null)) as { error?: string } | null;
        throw new Error(body?.error ?? "Manual model could not be saved.");
      }
      const body = (await response.json()) as { record: SpiritFlixManualModelRecord; index: SpiritFlixManualModelIndex };
      setManualModelRecord(body.record);
      setManualModelIndex(body.index);
      setDraftModelName(body.record.modelName);
      manualModelDraftDirtyRef.current = false;
      setManualModelSavedAt(new Date().toISOString());
      scheduleAppWidgetClose();
      window.dispatchEvent(new CustomEvent(MANUAL_MODEL_CHANGED_EVENT, { detail: { itemId: item.Id, modelName: body.record.modelName } }));
      void mergeKnownModelTagsIntoCurrentItem(body.record.modelName);
      const titleMatchedItems = getTitleMatchedItemsForModelName(body.record.modelName);
      if (titleMatchedItems.length) {
        void Promise.allSettled(
          titleMatchedItems.map(async (matchedItem) => {
            const matchedResponse = await fetch(`/api/spiritflix/videos/${encodeURIComponent(matchedItem.Id)}/model`, {
              method: "PUT",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                filePath: matchedItem.MediaSources?.[0]?.Path ?? matchedItem.Path,
                modelName: body.record.modelName,
                knownModelNames: knownModelOptions,
              }),
            });
            if (!matchedResponse.ok) throw new Error("Title-matched model could not be saved.");
            window.dispatchEvent(
              new CustomEvent(MANUAL_MODEL_CHANGED_EVENT, {
                detail: { itemId: matchedItem.Id, modelName: body.record.modelName },
              }),
            );
          }),
        );
      }
      const shouldQueueFaceLearning =
        !currentFaceMatch ||
        currentFaceMatch.status !== "confirmed" ||
        getModelOptionKey(currentFaceMatch.primaryPerformer?.name ?? "") !== getModelOptionKey(body.record.modelName);
      if (shouldQueueFaceLearning) {
        const relatedItems = [
          ...getRelatedItemsForModelName(body.record.modelName),
          ...titleMatchedItems.map((matchedItem) => ({
            itemId: matchedItem.Id,
            filePath: matchedItem.MediaSources?.[0]?.Path ?? matchedItem.Path,
          })),
        ];
        void requestFaceLearning(body.record.modelName, currentFaceMatch, relatedItems).then(() =>
          loadPlayerFaceMetadata(),
        );
      } else {
        setFaceLearningRecord(null);
        void loadPlayerFaceMetadata();
      }
    } catch (error) {
      setManualModelError(error instanceof Error ? error.message : "Manual model could not be saved.");
    } finally {
      setManualModelSaving(false);
    }
  };
  useEffect(() => {
    saveManualModelRef.current = saveManualModel;
  });

  useEffect(() => {
    const suggestedModelName = faceModelSuggestion?.primaryPerformer?.name ?? "";
    if (!shouldAutoApplyFaceModel || !suggestedModelName || faceSuggestionMatchesCurrentModel || manualModelSaving) return;
    if (manualModelDraftDirtyRef.current) return;
    const applyKey = [
      item.Id,
      getModelOptionKey(suggestedModelName),
      Math.round((faceSuggestionConfidence ?? 0) * 1000),
    ].join(":");
    if (autoFaceModelApplyKeyRef.current === applyKey) return;
    autoFaceModelApplyKeyRef.current = applyKey;
    void saveManualModelRef.current(suggestedModelName);
  }, [
    faceModelSuggestion?.primaryPerformer?.name,
    faceSuggestionConfidence,
    faceSuggestionMatchesCurrentModel,
    item.Id,
    manualModelSaving,
    shouldAutoApplyFaceModel,
  ]);

  const previewDeleteVideo = async () => {
    if (!canDeleteFromYes) {
      setDeleteError("Only videos under the yes folder can be deleted here.");
      return;
    }
    setDeleteLoading(true);
    setDeleteError("");
    setDeletePreview(null);
    try {
      const response = await fetch("/api/spiritflix/admin/actions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action: "softDelete",
          mode: "preview",
          sourcePath: deleteSourcePath,
        }),
      });
      const body = (await response.json()) as SpiritFlixDeletePreview | { error?: string };
      if (!response.ok || !("allowed" in body) || !body.allowed) {
        throw new Error("error" in body && body.error ? body.error : "Delete preview was blocked.");
      }
      setDeletePreview(body);
    } catch (error) {
      setDeleteError(error instanceof Error ? error.message : "Delete preview failed.");
    } finally {
      setDeleteLoading(false);
    }
  };

  const openDeleteEditor = () => {
    if (!canDeleteFromYes) {
      setDeleteError("Only videos under the yes folder can be deleted here.");
      return;
    }
    setIsDeleteEditorOpen(true);
    setIsTagEditorOpen(false);
    setIsModelEditorOpen(false);
    revealControls(true);
    scheduleAppWidgetClose();
    void previewDeleteVideo();
  };

  const confirmDeleteVideo = async () => {
    if (!deletePreview?.previewId) return;
    setDeleteExecuting(true);
    setDeleteError("");
    try {
      const response = await fetch("/api/spiritflix/admin/actions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          action: "softDelete",
          mode: "execute",
          confirmToken: deletePreview.previewId,
        }),
      });
      const body = (await response.json()) as SpiritFlixDeletePreview | { error?: string };
      if (!response.ok || !("allowed" in body) || !body.allowed) {
        throw new Error("error" in body && body.error ? body.error : "Delete was blocked.");
      }
      setDeletePreview(body);
      onDeleteItem(item, nextItem ?? previousItem ?? null);
    } catch (error) {
      setDeleteError(error instanceof Error ? error.message : "Delete failed.");
    } finally {
      setDeleteExecuting(false);
    }
  };

  const reorderQueueFromDrag = useCallback(
    (event: DragEndEvent | DragOverEvent, options: { reveal?: boolean } = {}) => {
      const activeItemId = getItemIdFromQueueDndId(String(event.active.id));
      const overItemId = event.over ? getItemIdFromQueueDndId(String(event.over.id)) : null;
      if (!activeItemId || !overItemId || activeItemId === overItemId) return;
      const pairKey = `${activeItemId}:${overItemId}`;
      if (lastQueueDragPairRef.current === pairKey) {
        if (options.reveal) revealControls(true);
        return;
      }
      lastQueueDragPairRef.current = pairKey;
      onReorderQueue(activeItemId, overItemId);
      if (options.reveal) revealControls(true);
    },
    [onReorderQueue, revealControls],
  );

  const handleQueueDragOver = useCallback(
    (event: DragOverEvent) => {
      reorderQueueFromDrag(event);
    },
    [reorderQueueFromDrag],
  );

  const handleQueueDragEnd = useCallback(
    (event: DragEndEvent) => {
      reorderQueueFromDrag(event, { reveal: true });
      lastQueueDragPairRef.current = null;
    },
    [reorderQueueFromDrag],
  );

  const selectNextItem = () => {
    if (nextItem) {
      selectQueueItem(nextItem);
      return;
    }
    if (repeatModeRef.current === "queue" && queueItems.length > 0) {
      selectQueueItem(queueItems[0] ?? item);
    }
  };

  const updateVolume = useCallback((nextVolume: number) => {
    const video = videoRef.current;
    const clamped = Math.max(0, Math.min(1, nextVolume));
    setVolume(clamped);
    volumeRef.current = clamped;
    window.localStorage.setItem(VOLUME_STORAGE_KEY, String(clamped));
    if (video) {
      video.volume = clamped;
      video.muted = clamped === 0;
      mutedRef.current = video.muted;
      window.localStorage.setItem(MUTED_STORAGE_KEY, String(video.muted));
      setIsMuted(video.muted);
    }
  }, []);

  const updateMuted = useCallback((nextMuted: boolean) => {
    const video = videoRef.current;
    mutedRef.current = nextMuted;
    window.localStorage.setItem(MUTED_STORAGE_KEY, String(nextMuted));
    setIsMuted(nextMuted);
    if (video) video.muted = nextMuted;
  }, []);

  const toggleMuted = useCallback(() => {
    const video = videoRef.current;
    const currentlySilent = (video?.muted ?? mutedRef.current) || volumeRef.current <= 0;
    if (isVolumeOpen) {
      setIsVolumeOpen(false);
      revealControls();
      return;
    }

    if (currentlySilent) {
      const audibleVolume = volumeRef.current > 0 ? volumeRef.current : DEFAULT_AUDIBLE_VOLUME;
      setVolume(audibleVolume);
      volumeRef.current = audibleVolume;
      window.localStorage.setItem(VOLUME_STORAGE_KEY, String(audibleVolume));
      if (video) {
        video.volume = audibleVolume;
        video.muted = false;
      }
      mutedRef.current = false;
      window.localStorage.setItem(MUTED_STORAGE_KEY, "false");
      setIsMuted(false);
      setIsVolumeOpen(true);
      scheduleVolumeClose();
      revealControls();
      void video?.play().catch(() => undefined);
      return;
    }

    setIsVolumeOpen(true);
    scheduleVolumeClose();
    revealControls();
  }, [isVolumeOpen, revealControls, scheduleVolumeClose]);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return undefined;
    const directUrl = client.getStreamUrl(item.Id);
    const hlsUrl = client.getHlsUrl(item.Id);
    let hlsInstance: HlsController | null = null;
    let cancelled = false;

    const resetVideo = () => {
      setStreamError("");
      setUsingHls(false);
      setPlaybackMode(getInitialPlaybackMode());
      setPlaybackSourceClass(getInitialPlaybackMode() === "proxied stream" ? "canonical_mp4" : "jellyfin_direct_mp4");
      setPlaybackSourceReason("reset to direct MP4 preference");
      setMobileOptimizedSource(null);
      setIsLoading(true);
      setEndedAtQueueEnd(false);
      endedRef.current = false;
      lastUiProgressAtRef.current = 0;
      lastUiTimeAtRef.current = 0;
      lastPlaybackReportAtRef.current = performance.now();
      firstNonZeroReportRef.current = false;
      usingHlsRef.current = false;
      playbackModeRef.current = getInitialPlaybackMode();
      waitingSinceRef.current = null;
      video.pause();
      video.removeAttribute("src");
      video.load();
      video.volume = volumeRef.current;
      video.muted = mutedRef.current;
      video.loop = repeatModeRef.current === "one";
    };

    const startHls = async (): Promise<boolean> => {
      if (cancelled || usingHlsRef.current) return usingHlsRef.current;
      try {
        const { default: Hls } = await import("hls.js");
        if (Hls.isSupported()) {
          const instance = new Hls();
          const controller = instance as unknown as HlsController;
          const manifestReady = new Promise<void>((resolve, reject) => {
            const timeoutId = window.setTimeout(() => reject(new Error("HLS manifest timed out.")), HLS_MANIFEST_TIMEOUT_MS);
            controller.on(Hls.Events.MANIFEST_PARSED, () => {
              window.clearTimeout(timeoutId);
              resolve();
            });
            controller.on(Hls.Events.ERROR, (_event, data) => {
              if (!data?.fatal) return;
              window.clearTimeout(timeoutId);
              reject(new Error(data.details ?? "HLS playback failed."));
            });
          });
          controller.loadSource(hlsUrl);
          controller.attachMedia(video);
          hlsInstance = controller;
          await manifestReady;
        } else if (video.canPlayType("application/vnd.apple.mpegurl")) {
          video.src = hlsUrl;
          video.load();
        } else {
          setStreamError("This browser could not play the Jellyfin stream.");
          setIsLoading(false);
          return false;
        }
        usingHlsRef.current = true;
        setUsingHls(true);
        playbackModeRef.current = "HLS";
        setPlaybackMode("HLS");
        setPlaybackSourceClass(mediaDiagnostics.transcodeLikely ? "jellyfin_transcode_fallback" : "jellyfin_hls_fallback");
        setPlaybackSourceReason("direct MP4 path failed; HLS fallback started");
        setStreamError("");
        return true;
      } catch (error) {
        hlsInstance?.destroy();
        hlsInstance = null;
        setStreamError(error instanceof Error ? error.message : "Direct playback failed and HLS fallback could not start.");
        setIsLoading(false);
        return false;
      }
    };

    const startPlayback = async () => {
      try {
        await video.play();
      } catch (error) {
        if (cancelled || isPlaybackAbort(error)) return;
        if (!usingHlsRef.current && !video.muted) {
          video.muted = true;
          mutedRef.current = true;
          setIsMuted(true);
          window.localStorage.setItem(MUTED_STORAGE_KEY, "true");
          try {
            await video.play();
            return;
          } catch (retryError) {
            if (cancelled || isPlaybackAbort(retryError)) return;
            setShowControls(true);
            if (retryError instanceof DOMException && retryError.name !== "NotAllowedError") {
              setStreamError(retryError.message);
            }
            return;
          }
        }
        setShowControls(true);
        if (error instanceof DOMException && error.name !== "NotAllowedError") {
          setStreamError(error.message);
        }
      }
    };

    const setup = async () => {
      resetVideo();
      void client.getSystemDiagnostics?.()
        .then((diagnostics) => {
          if (!cancelled) setSystemDiagnostics(diagnostics);
        })
        .catch(() => undefined);
      const mobileSource: MobileOptimizedSource = await client
        .getMobileOptimizedSource(itemRef.current)
        .catch((): MobileOptimizedSource => ({ available: false }));
      if (cancelled) return;
      if (mobileSource.available && mobileSource.url) {
        setMobileOptimizedSource(mobileSource);
        setPlaybackMode("mobile optimized");
        setPlaybackSourceClass("mac_optimized_mp4");
        setPlaybackSourceReason("valid Mac optimized MP4 receipt and output found");
        playbackModeRef.current = "mobile optimized";
        video.src = mobileSource.url;
        video.load();
      } else {
        video.src = directUrl;
        video.load();
        const directMode = directUrl.startsWith("/api/") ? "proxied stream" : "direct stream";
        const directClass = getDirectPlaybackSourceClass(itemRef.current, directUrl);
        playbackModeRef.current = directMode;
        setPlaybackMode(directMode);
        setPlaybackSourceClass(directClass);
        setPlaybackSourceReason(mobileSource.available ? "optimized MP4 unavailable or missing URL; using direct MP4" : "no optimized MP4 receipt found; using direct MP4");
      }
      const resumeAt = ticksToSeconds(startPositionTicks ?? item.UserData?.PlaybackPositionTicks);
      if (resumeAt) video.currentTime = resumeAt;
      const startTicks = resumeAt ? secondsToTicks(resumeAt) : 0;
      lastReportedTicksRef.current = startTicks;
      await client.reportPlayback(item.Id, "Start", startTicks, false);
      emitPlaybackProgress(startTicks, false);
      if (cancelled) return;
      await startPlayback();
    };

    setup().catch(() => {
      setIsLoading(false);
      setStreamError("Could not prepare this Jellyfin stream.");
    });

    const handleDirectError = async () => {
      if (cancelled || usingHlsRef.current) return;
      const previousMode = playbackModeRef.current;
      setStreamError("");
      const hlsReady = await startHls();
      if (hlsReady) await startPlayback();
      if (!hlsReady && previousMode === "mobile optimized") {
        setStreamError("The mobile optimized copy failed to play and Jellyfin fallback could not start.");
      }
    };

    video.addEventListener("error", handleDirectError);
    return () => {
      cancelled = true;
      video.removeEventListener("error", handleDirectError);
      const stopTicks = secondsToTicks(video.currentTime || ticksToSeconds(lastReportedTicksRef.current));
      void client.reportPlayback(item.Id, "Stopped", stopTicks, video.paused, { keepalive: true });
      emitPlaybackProgress(endedRef.current ? secondsToTicks(video.duration || ticksToSeconds(item.RunTimeTicks)) : stopTicks, endedRef.current);
      hlsInstance?.destroy();
    };
  }, [client, emitPlaybackProgress, item.Id, item.RunTimeTicks, item.UserData?.PlaybackPositionTicks, mediaDiagnostics.transcodeLikely, retryCount, startPositionTicks]);

  useEffect(() => {
    const flushForMobileSuspend = () => {
      if (endedRef.current) return;
      flushPlaybackProgress("Progress", { isPaused: true, keepalive: true });
    };
    const handleVisibilityChange = () => {
      if (document.visibilityState === "hidden") flushForMobileSuspend();
    };

    window.addEventListener("pagehide", flushForMobileSuspend);
    window.addEventListener("beforeunload", flushForMobileSuspend);
    document.addEventListener("visibilitychange", handleVisibilityChange);
    return () => {
      window.removeEventListener("pagehide", flushForMobileSuspend);
      window.removeEventListener("beforeunload", flushForMobileSuspend);
      document.removeEventListener("visibilitychange", handleVisibilityChange);
    };
  }, [flushPlaybackProgress]);

  useEffect(() => {
    repeatModeRef.current = repeatMode;
    window.localStorage.setItem(REPEAT_STORAGE_KEY, repeatMode);
    if (videoRef.current) videoRef.current.loop = repeatMode === "one";
  }, [repeatMode]);

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(Boolean(document.fullscreenElement));
      revealControls();
    };
    document.addEventListener("fullscreenchange", handleFullscreenChange);
    return () => document.removeEventListener("fullscreenchange", handleFullscreenChange);
  }, [revealControls]);

  useEffect(() => {
    const video = videoRef.current as MiniPlayerVideo | null;
    const pictureDocument = document as MiniPlayerDocument;

    const updateMiniPlayerState = () => {
      setMiniPlayerSupported(supportsMiniPlayer(video));
      setIsNativeMiniPlayer(
        Boolean(pictureDocument.pictureInPictureElement && pictureDocument.pictureInPictureElement === video) ||
          video?.webkitPresentationMode === "picture-in-picture",
      );
    };

    updateMiniPlayerState();
    video?.addEventListener("enterpictureinpicture", updateMiniPlayerState);
    video?.addEventListener("leavepictureinpicture", updateMiniPlayerState);
    video?.addEventListener("webkitpresentationmodechanged", updateMiniPlayerState);
    return () => {
      video?.removeEventListener("enterpictureinpicture", updateMiniPlayerState);
      video?.removeEventListener("leavepictureinpicture", updateMiniPlayerState);
      video?.removeEventListener("webkitpresentationmodechanged", updateMiniPlayerState);
    };
  }, [item.Id, retryCount]);

  useEffect(() => {
    const shell = shellRef.current;
    if (!shell) return undefined;

    const updateShellSize = () => {
      setShellSize({
        width: shell.clientWidth || window.innerWidth,
        height: shell.clientHeight || window.innerHeight,
      });
    };

    updateShellSize();
    const observer = new ResizeObserver(updateShellSize);
    observer.observe(shell);
    window.addEventListener("orientationchange", updateShellSize);
    window.addEventListener("resize", updateShellSize);

    return () => {
      observer.disconnect();
      window.removeEventListener("orientationchange", updateShellSize);
      window.removeEventListener("resize", updateShellSize);
    };
  }, []);

  useEffect(() => {
    return () => {
      if (hideTimer.current) window.clearTimeout(hideTimer.current);
      if (volumeHideTimer.current) window.clearTimeout(volumeHideTimer.current);
      if (feedbackTimer.current) window.clearTimeout(feedbackTimer.current);
      if (appWidgetHideTimer.current) window.clearTimeout(appWidgetHideTimer.current);
      if (tapRevealTimer.current) window.clearTimeout(tapRevealTimer.current);
    };
  }, []);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.target instanceof HTMLInputElement) return;
      const key = event.key.toLowerCase();
      if (key === " " || key === "k") {
        event.preventDefault();
        togglePlay();
      } else if (key === "arrowleft") {
        event.preventDefault();
        seekBy(-10);
      } else if (key === "arrowright") {
        event.preventDefault();
        seekBy(10);
      } else if (key === "arrowup") {
        event.preventDefault();
        updateVolume(volume + 0.08);
      } else if (key === "arrowdown") {
        event.preventDefault();
        updateVolume(volume - 0.08);
      } else if (key === "m") {
        event.preventDefault();
        const video = videoRef.current;
        if (video) {
          updateMuted(!video.muted);
        }
      } else if (key === "f") {
        event.preventDefault();
        toggleFullscreen();
      } else if (key === "escape") {
        event.preventDefault();
        if (document.fullscreenElement) {
          void document.exitFullscreen();
        } else {
          onClose();
        }
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose, seekBy, toggleFullscreen, togglePlay, updateMuted, updateVolume, volume]);

  const handlePointerDown = (event: React.PointerEvent<HTMLElement>) => {
    if (event.pointerType === "touch") {
      lastTouchInteractionAtRef.current = Date.now();
      return;
    }
    if (Date.now() < suppressPointerUntilRef.current || pinchStartRef.current) return;
    if (isInteractiveTarget(event.target)) return;
    event.currentTarget.setPointerCapture?.(event.pointerId);
    pointerStartRef.current = {
      x: event.clientX,
      y: event.clientY,
      time: Date.now(),
      currentTime: videoRef.current?.currentTime ?? 0,
    };
  };

  const handlePlayerTap = useCallback(
    (x: number, y: number) => {
      const shellWidth = shellRef.current?.clientWidth ?? window.innerWidth;
      const zone = getPlayerTapZone(x, shellWidth);
      const activeElement = document.activeElement;
      const controlsHaveFocus =
        activeElement instanceof HTMLElement &&
        Boolean(activeElement.closest(".spiritflix-player__top, .spiritflix-player__controls"));
      const controlsAreVisible = !controlsHiddenByUser && (showControls || !isPlaying || controlsHaveFocus);

      const lastTap = lastTapRef.current;
      if (
        (zone === "left-seek" || zone === "right-seek") &&
        lastTap &&
        lastTap.zone === zone &&
        Date.now() - lastTap.time < DOUBLE_TAP_MAX_MS &&
        Math.abs(x - lastTap.x) < DOUBLE_TAP_MAX_DISTANCE &&
        Math.abs(y - lastTap.y) < DOUBLE_TAP_MAX_DISTANCE
      ) {
        lastTapRef.current = null;
        clearTapRevealTimer();
        seekBy(zone === "left-seek" ? -10 : 10);
        return;
      }

      if (zone === "center") {
        lastTapRef.current = null;
        clearTapRevealTimer();
        setControlsHiddenByUser(false);
        revealControls();
        togglePlay();
      } else if (controlsAreVisible) {
        clearTapRevealTimer();
        if (zone === "left-seek" || zone === "right-seek") {
          lastTapRef.current = { time: Date.now(), x, y, zone };
        } else {
          lastTapRef.current = null;
        }
        hideControls();
      } else if (zone === "left-seek" || zone === "right-seek") {
        lastTapRef.current = { time: Date.now(), x, y, zone };
        scheduleTapReveal();
      } else {
        lastTapRef.current = null;
        clearTapRevealTimer();
        revealControls();
      }
    },
    [
      clearTapRevealTimer,
      controlsHiddenByUser,
      hideControls,
      isPlaying,
      revealControls,
      scheduleTapReveal,
      seekBy,
      showControls,
      togglePlay,
    ],
  );

  const handlePointerUp = (event: React.PointerEvent<HTMLElement>) => {
    if (event.pointerType === "touch") {
      lastTouchInteractionAtRef.current = Date.now();
      pointerStartRef.current = null;
      return;
    }
    if (Date.now() < suppressPointerUntilRef.current || pinchStartRef.current) {
      pointerStartRef.current = null;
      return;
    }
    if (isInteractiveTarget(event.target)) return;
    event.currentTarget.releasePointerCapture?.(event.pointerId);
    const start = pointerStartRef.current;
    pointerStartRef.current = null;
    if (!start) {
      revealControls();
      return;
    }

    const dx = event.clientX - start.x;
    const dy = event.clientY - start.y;
    const elapsed = Date.now() - start.time;
    const absX = Math.abs(dx);
    const absY = Math.abs(dy);
    const isTap = absX <= TAP_MAX_MOVEMENT && absY <= TAP_MAX_MOVEMENT && elapsed <= TAP_MAX_MS;

    if (absY > 120 && absY > absX * 1.2 && dy > 0) {
      onClose();
      return;
    }

    if (absX > 70 && absX > absY * 1.35) {
      const seconds = Math.max(-45, Math.min(45, Math.round(dx / 8)));
      seekBy(seconds);
      return;
    }

    if (isTap) {
      lastPointerTapAtRef.current = Date.now();
      handlePlayerTap(event.clientX, event.clientY);
      return;
    }

    revealControls();
  };

  const touchDistance = (touches: { length: number; item(index: number): { clientX: number; clientY: number } | null }) => {
    if (touches.length < 2) return 0;
    const first = getTouchAt(touches, 0);
    const second = getTouchAt(touches, 1);
    if (!first || !second) return 0;
    return Math.hypot(second.clientX - first.clientX, second.clientY - first.clientY);
  };

  const playerStyle = useMemo(
    () => {
      const shellAspectRatio =
        shellSize.width > 0 && shellSize.height > 0 ? shellSize.width / shellSize.height : videoAspectRatio;
      const neededFillScale = getSmartFillScale(shellAspectRatio, videoAspectRatio);

      return {
        "--spiritflix-fill-scale": neededFillScale.toFixed(3),
        "--spiritflix-video-aspect": videoAspectRatio.toFixed(6),
      } as CSSProperties;
    },
    [shellSize.height, shellSize.width, videoAspectRatio],
  );

  return (
    <section
      className={`spiritflix-player is-fit-${fitMode} ${
        !controlsHiddenByUser && (showControls || !isPlaying || isTagEditorOpen || isModelEditorOpen) ? "is-awake" : "is-idle"
      } ${controlsHiddenByUser ? "is-controls-hidden" : ""} ${isAppMiniPlayer ? "is-app-mini" : ""}`}
      ref={shellRef}
      style={playerStyle}
      aria-label={`${item.Name} player`}
      onPointerDown={handlePointerDown}
      onPointerUp={handlePointerUp}
      onPointerCancel={() => {
        pointerStartRef.current = null;
      }}
      onPointerMove={(event) => {
        if (
          event.pointerType === "mouse" &&
          Date.now() - lastTouchInteractionAtRef.current > TOUCH_MOUSE_REVEAL_SUPPRESS_MS
        ) {
          revealControls();
        }
      }}
      onMouseMove={() => {
        if (Date.now() - lastTouchInteractionAtRef.current > TOUCH_MOUSE_REVEAL_SUPPRESS_MS) {
          revealControls();
        }
      }}
      onTouchStart={(event) => {
        lastTouchInteractionAtRef.current = Date.now();
        if (event.touches.length === 2) {
          event.preventDefault();
          const distance = touchDistance(event.touches);
          pinchStartRef.current = { startDistance: distance, currentDistance: distance };
          pointerStartRef.current = null;
          touchTapStartRef.current = null;
          lastTapRef.current = null;
        } else if (event.touches.length === 1 && !isInteractiveTarget(event.target)) {
          const touch = getTouchAt(event.touches, 0);
          if (touch) {
            touchTapStartRef.current = {
              x: touch.clientX,
              y: touch.clientY,
              time: Date.now(),
              currentTime: videoRef.current?.currentTime ?? 0,
              isSeeking: false,
            };
          }
        }
      }}
      onTouchMove={(event) => {
        const pinch = pinchStartRef.current;
        if (pinch && event.touches.length === 2) {
          const nextDistance = touchDistance(event.touches);
          if (!nextDistance) return;
          event.preventDefault();
          pinchStartRef.current = { ...pinch, currentDistance: nextDistance };
          return;
        }

        const start = touchTapStartRef.current;
        const touch = getTouchAt(event.touches, 0);
        if (!start || !touch || event.touches.length !== 1 || Date.now() < suppressTouchUntilRef.current) return;

        const dx = touch.clientX - start.x;
        const dy = touch.clientY - start.y;
        const absX = Math.abs(dx);
        const absY = Math.abs(dy);
        const hasHeldLongEnough = Date.now() - start.time >= TOUCH_SEEK_HOLD_MS;
        const isHorizontalSeek =
          start.isSeeking ||
          (hasHeldLongEnough && absX >= TOUCH_SEEK_ACTIVATION_PX && absX > absY * TOUCH_SEEK_VERTICAL_RATIO);
        if (!isHorizontalSeek) return;

        event.preventDefault();
        touchTapStartRef.current = { ...start, isSeeking: true };
        lastTapRef.current = null;
        seekFromTouchDelta(start.currentTime, dx);
        revealControls(true);
      }}
      onTouchEnd={(event) => {
        lastTouchInteractionAtRef.current = Date.now();
        const pinch = pinchStartRef.current;
        if (pinch && event.touches.length < 2) {
          const distanceRatio = pinch.currentDistance / pinch.startDistance;
          if (distanceRatio >= 1 + PINCH_TOGGLE_THRESHOLD && fitMode !== "fill") {
            setFit("fill");
            revealControls();
          } else if (distanceRatio <= 1 - PINCH_TOGGLE_THRESHOLD && fitMode !== "fit") {
            setFit("fit");
            revealControls();
          }
          suppressPointerUntilRef.current = Date.now() + PINCH_GESTURE_SUPPRESS_MS;
          suppressTouchUntilRef.current = Date.now() + PINCH_GESTURE_SUPPRESS_MS;
          touchTapStartRef.current = null;
        } else {
          const start = touchTapStartRef.current;
          const touch = getTouchAt(event.changedTouches, 0);
          touchTapStartRef.current = null;
          if (start?.isSeeking) {
            suppressPointerUntilRef.current = Date.now() + PINCH_GESTURE_SUPPRESS_MS;
            suppressTouchUntilRef.current = Date.now() + PINCH_GESTURE_SUPPRESS_MS;
            revealControls();
            return;
          }
          if (
            start &&
            touch &&
            Date.now() >= suppressTouchUntilRef.current &&
            Date.now() - lastPointerTapAtRef.current > PINCH_GESTURE_SUPPRESS_MS
          ) {
            const dx = touch.clientX - start.x;
            const dy = touch.clientY - start.y;
            const elapsed = Date.now() - start.time;
            if (Math.abs(dx) <= TAP_MAX_MOVEMENT && Math.abs(dy) <= TAP_MAX_MOVEMENT && elapsed <= TAP_MAX_MS) {
              suppressPointerUntilRef.current = Date.now() + PINCH_GESTURE_SUPPRESS_MS;
              handlePlayerTap(touch.clientX, touch.clientY);
            }
          }
        }
        pinchStartRef.current = null;
      }}
    >
      {isAppMiniPlayer ? (
        <div className="spiritflix-player__mini-actions" aria-label="Mini player controls">
          <button
            className="spiritflix-player__mini-back"
            type="button"
            onClick={toggleMiniPlayer}
            aria-label="Back to tab"
            title="Back to tab"
          >
            <Maximize size={16} aria-hidden="true" />
            <span>Back to tab</span>
          </button>
        </div>
      ) : null}
      <div className="spiritflix-player__stage">
        <video
          key={`${item.Id}-${retryCount}`}
          ref={videoRef}
          playsInline
          controls={false}
          loop={repeatMode === "one"}
          controlsList="nodownload noplaybackrate noremoteplayback"
          preload="metadata"
          onWaiting={() => {
            setIsLoading(true);
            if (!waitingSinceRef.current) {
              waitingSinceRef.current = performance.now();
            }
          }}
          onCanPlay={() => {
            setStreamError("");
            setIsLoading(false);
            if (waitingSinceRef.current) {
              waitingSinceRef.current = null;
            }
          }}
          onPlaying={() => {
            setIsPlaying(true);
            setIsLoading(false);
            scheduleControlsHide();
            if (waitingSinceRef.current) {
              waitingSinceRef.current = null;
            }
          }}
          onPlay={() => setIsPlaying(true)}
          onPause={() => {
            setIsPlaying(false);
            flushPlaybackProgress("Progress", { isPaused: true, updateUi: true });
          }}
          onTimeUpdate={(event) => {
            const video = event.currentTarget;
            const positionTicks = secondsToTicks(video.currentTime);
            const now = Date.now();
            if (now - lastUiTimeAtRef.current >= UI_TIME_UPDATE_MS) {
              lastUiTimeAtRef.current = now;
              setCurrentTime(video.currentTime);
            }
            if (now - lastUiProgressAtRef.current >= PLAYBACK_REPORT_MS) {
              lastUiProgressAtRef.current = now;
              emitPlaybackProgress(positionTicks, false);
            }
            if (!firstNonZeroReportRef.current && video.currentTime >= 3) {
              firstNonZeroReportRef.current = true;
              lastReportedTicksRef.current = positionTicks;
              lastPlaybackReportAtRef.current = performance.now();
              void client.reportPlayback(item.Id, "Progress", positionTicks, false);
            }
            if (performance.now() - lastPlaybackReportAtRef.current >= PLAYBACK_REPORT_MS) {
              lastPlaybackReportAtRef.current = performance.now();
              lastReportedTicksRef.current = positionTicks;
              void client.reportPlayback(item.Id, "Progress", positionTicks, false);
            }
          }}
          onLoadedMetadata={(event) => {
            const video = event.currentTarget;
            setDuration(Number.isFinite(video.duration) ? video.duration : ticksToSeconds(item.RunTimeTicks));
            setAudioTrackSwitchAvailable(applyAudioPreferenceToVideo(video, seriesAudioPreference));
            if (video.videoWidth > 0 && video.videoHeight > 0) {
              setVideoAspectRatio(video.videoWidth / video.videoHeight);
            }
          }}
          onEnded={() => {
            setIsPlaying(false);
            endedRef.current = true;
            void client.reportPlayback(item.Id, "Stopped", secondsToTicks(videoRef.current?.duration || duration), false, { keepalive: true });
            emitPlaybackProgress(secondsToTicks(videoRef.current?.duration || duration), true);
            const currentRepeatMode = repeatModeRef.current;
            if (currentRepeatMode === "one") {
              const video = videoRef.current;
              if (video) {
                video.currentTime = 0;
                void video.play();
              }
            } else if (nextItem) {
              selectQueueItem(nextItem);
            } else if (currentRepeatMode === "queue" && queueItems.length > 0) {
              selectQueueItem(queueItems[0] ?? item);
            } else {
              setEndedAtQueueEnd(true);
              revealControls(true);
            }
          }}
        />
      </div>

      {isLoading && !streamError && !isPlaying ? (
        <div className="spiritflix-player__loading" aria-live="polite">
          <span />
        </div>
      ) : null}

      {playbackFeedback ? (
        <div
          className={`spiritflix-player__tap-feedback is-${playbackFeedback.kind}`}
          aria-hidden="true"
          key={playbackFeedback.id}
        >
          {renderPlaybackFeedback(playbackFeedback)}
        </div>
      ) : null}

      <div className="spiritflix-player__top">
        <button type="button" onClick={onClose} aria-label="Close player" title="Close">
          <X size={22} aria-hidden="true" />
        </button>
        <div className="spiritflix-player__title">
          <strong>{item.Name}</strong>
          <span>{queue?.sourceTitle ?? playbackMode}</span>
        </div>
        <button className="spiritflix-player__collapse" type="button" onClick={onClose} aria-label="Exit player" title="Exit player">
          <ChevronsDown size={22} aria-hidden="true" />
        </button>
      </div>

      {SHOW_PLAYER_DIAGNOSTICS ? (
        <aside className={`spiritflix-player__diagnostics ${diagnosticsOpen ? "is-open" : ""}`} aria-label="Playback diagnostics">
          <div>
            <strong>{playbackMode}</strong>
            <button type="button" onClick={() => setDiagnosticsOpen((open) => !open)}>
              {diagnosticsOpen ? "Hide" : "Details"}
            </button>
          </div>
          {diagnosticsOpen ? (
            <dl>
              <div>
                <dt>Selected source</dt>
                <dd>{playbackSourceClass}</dd>
              </div>
              <div>
                <dt>Reason</dt>
                <dd>{playbackSourceReason}</dd>
              </div>
              <div>
                <dt>Optimized receipt</dt>
                <dd>{mobileOptimizedSource?.available ? "yes" : "no"}</dd>
              </div>
              <div>
                <dt>Optimized path</dt>
                <dd title={mobileOptimizedSource?.url ?? "none"}>{mobileOptimizedSource?.url ? "mobile optimized API" : "none"}</dd>
              </div>
              <div>
                <dt>Canonical MP4</dt>
                <dd>{canonicalMp4Present ? "yes" : "no"}</dd>
              </div>
              <div>
                <dt>Range support</dt>
                <dd>{rangeSupport ? "yes" : "unknown"}</dd>
              </div>
              <div>
                <dt>HLS fallback</dt>
                <dd>{usingHls ? "yes" : "no"}</dd>
              </div>
              <div>
                <dt>Dell ffmpeg active</dt>
                <dd>{systemDiagnostics ? (systemDiagnostics.dellFfmpegActive ? "yes" : "no") : "unknown"}</dd>
              </div>
              <div>
                <dt>Source URL</dt>
                <dd>{playbackSourceClass === "mac_optimized_mp4" ? "mobile-optimized-api" : usingHls ? "hls-api" : playbackMode === "proxied stream" ? "stream-api" : "jellyfin-direct"}</dd>
              </div>
              <div>
                <dt>Item</dt>
                <dd title={item.Id}>{item.Id}</dd>
              </div>
              <div>
                <dt>Route</dt>
                <dd>{routeHint}</dd>
              </div>
              <div>
                <dt>Container</dt>
                <dd>{mediaDiagnostics.container}</dd>
              </div>
              <div>
                <dt>Video</dt>
                <dd>{mobileOptimizedSource?.receipt?.ffprobe?.videoCodec ?? mediaDiagnostics.video}</dd>
              </div>
              <div>
                <dt>Audio</dt>
                <dd>{mobileOptimizedSource?.receipt?.ffprobe?.audioCodec ?? mediaDiagnostics.audio}</dd>
              </div>
              <div>
                <dt>Live transcode</dt>
                <dd>{playbackMode === "mobile optimized" ? "unlikely" : mediaDiagnostics.transcodeLikely || usingHls ? "likely" : "unlikely"}</dd>
              </div>
            </dl>
          ) : null}
        </aside>
      ) : null}

      {streamError ? (
        <div className="spiritflix-player__error" role="alert">
          <strong>Stream unavailable</strong>
          <p>{streamError}</p>
          <div>
            <button type="button" onClick={() => setRetryCount((count) => count + 1)}>
              <RefreshCw size={18} aria-hidden="true" />
              Retry
            </button>
            <button type="button" onClick={onClose}>Back</button>
          </div>
        </div>
      ) : null}

      {endedAtQueueEnd ? (
        <div className="spiritflix-player__ended">
          <strong>End of queue</strong>
          <div>
            <button type="button" onClick={() => seekTo(0)}>
              <RefreshCw size={18} aria-hidden="true" />
              Replay
            </button>
            <button type="button" onClick={onClose}>Close</button>
          </div>
        </div>
      ) : null}

      <div className="spiritflix-player__controls">
        <div className="spiritflix-player__scrub-row">
          <span className="spiritflix-player__time">{formatTime(currentTime)}</span>
          <input
            className="spiritflix-player__scrub"
            aria-label="Seek"
            type="range"
            min={0}
            max={duration || ticksToSeconds(item.RunTimeTicks) || 0}
            step={0.1}
            value={Math.min(currentTime, duration || currentTime)}
            onPointerDown={() => revealControls(true)}
            onChange={(event) => seekTo(Number(event.target.value))}
          />
          <span className="spiritflix-player__time">{formatTime(duration || ticksToSeconds(item.RunTimeTicks))}</span>
        </div>

        <div className="spiritflix-player__button-row">
          <div className="spiritflix-player__transport">
            <button type="button" onClick={() => selectQueueItem(previousItem)} disabled={!previousItem} aria-label={previousLabel} title={previousLabel}>
              <SkipBack size={20} aria-hidden="true" />
            </button>
            <button className="spiritflix-player__play" type="button" onClick={togglePlay} aria-label={isPlaying ? "Pause" : "Play"} title={isPlaying ? "Pause" : "Play"}>
              {isPlaying ? <Pause size={30} aria-hidden="true" /> : <Play size={30} fill="currentColor" aria-hidden="true" />}
            </button>
            <button type="button" onClick={selectNextItem} disabled={!nextItem && repeatMode !== "queue"} aria-label={nextLabel} title={nextLabel}>
              <SkipForward size={20} aria-hidden="true" />
            </button>
          </div>

          <div className={`spiritflix-player__tools ${isToolDrawerOpen ? "is-open" : ""}`}>
            {showToolOverflow ? (
              <button
                className="spiritflix-player__tools-toggle spiritflix-player__tool spiritflix-player__tool--more"
                type="button"
                onClick={toggleToolDrawer}
                aria-label={isToolDrawerOpen ? "Hide player tools" : "More player controls"}
                aria-expanded={isToolDrawerOpen}
                title={isToolDrawerOpen ? "Hide tools" : "More controls"}
              >
                <SlidersHorizontal size={20} aria-hidden="true" />
              </button>
            ) : null}
            {showLibraryPlayerTools ? (
              <button
                className={`spiritflix-player__tool spiritflix-player__tool--repeat ${repeatMode !== "off" ? "is-active" : ""}`}
                type="button"
                onClick={cycleRepeatMode}
                aria-label={repeatLabel}
                aria-pressed={repeatMode !== "off"}
                title={repeatLabel}
              >
                {repeatMode === "one" ? <Repeat1 size={20} aria-hidden="true" /> : <Repeat size={20} aria-hidden="true" />}
              </button>
            ) : null}
            {showLibraryPlayerTools ? (
              <button
                className={`spiritflix-player__tool spiritflix-player__tool--shuffle ${isShuffled ? "is-active" : ""}`}
                type="button"
                onClick={handleShuffleButtonClick}
                onPointerDown={startShuffleHold}
                onPointerUp={clearShuffleHoldTimer}
                onPointerCancel={clearShuffleHoldTimer}
                onPointerLeave={clearShuffleHoldTimer}
                onContextMenu={(event) => {
                  event.preventDefault();
                  if (queueItems.length >= 2) {
                    setIsShufflePickerOpen(true);
                    revealControls(true);
                  }
                }}
                disabled={queueItems.length < 2}
                aria-label={shuffleLabel}
                aria-pressed={isShuffled}
                title={shuffleLabel}
              >
                <Shuffle size={20} aria-hidden="true" />
              </button>
            ) : null}
            {showLibraryPlayerTools && isShufflePickerOpen ? (
              <div className="spiritflix-player__shuffle-picker" role="menu" aria-label="Shuffle by video orientation">
                {(["portrait", "landscape"] as const).map((orientation) => (
                  <button
                    key={orientation}
                    type="button"
                    role="menuitem"
                    disabled={orientationCounts[orientation] < 2}
                    onClick={() => shuffleCurrentQueueByOrientation(orientation)}
                  >
                    <span className="spiritflix-player__shuffle-picker-label">{getOrientationFilterLabel(orientation)}</span>
                    <span className="spiritflix-player__shuffle-picker-count">{orientationCounts[orientation]}</span>
                  </button>
                ))}
              </div>
            ) : null}
            {showLibraryPlayerTools ? (
              <button
                className={`spiritflix-player__tool spiritflix-player__tool--favorite ${isFavorite ? "is-active" : ""}`}
                type="button"
                onClick={() => {
                  onToggleFavorite(item, !isFavorite);
                  revealControls();
                }}
                aria-label={isFavorite ? "Remove favorite" : "Add favorite"}
                aria-pressed={isFavorite}
                title={isFavorite ? "Remove favorite" : "Add favorite"}
              >
                <Heart size={20} fill={isFavorite ? "currentColor" : "none"} aria-hidden="true" />
              </button>
            ) : null}
            {hasSeriesAudioChoices ? (
              <button
                className="spiritflix-player__tool spiritflix-player__tool--audio"
                type="button"
                onClick={toggleSeriesAudioPreference}
                aria-label={`Switch audio to ${nextSeriesAudioPreference === "dub" ? "English dub" : "Japanese sub"}`}
                aria-pressed={seriesAudioPreference === "dub"}
                title={`Audio: ${seriesAudioPreference === "dub" ? "Dub" : "Sub"}`}
              >
                <Languages size={20} aria-hidden="true" />
                <span>{seriesAudioPreference === "dub" ? "Dub" : "Sub"}</span>
              </button>
            ) : null}
            <div className={`spiritflix-player__volume spiritflix-player__tool spiritflix-player__tool--volume ${isVolumeOpen ? "is-expanded" : ""}`}>
              <button
                type="button"
                onClick={toggleMuted}
                aria-label={isVolumeOpen ? "Close volume" : "Open volume"}
                aria-controls="spiritflix-player-volume"
                aria-expanded={isVolumeOpen}
                title={isVolumeOpen ? "Close volume" : "Volume"}
              >
                {isMuted ? <VolumeX size={20} aria-hidden="true" /> : <Volume2 size={20} aria-hidden="true" />}
              </button>
              <input
                id="spiritflix-player-volume"
                aria-label="Volume"
                type="range"
                min={0}
                max={1}
                step={0.01}
                value={isMuted ? 0 : volume}
                onPointerDown={() => {
                  setIsVolumeOpen(true);
                  scheduleVolumeClose();
                  revealControls();
                }}
                onFocus={() => {
                  setIsVolumeOpen(true);
                  scheduleVolumeClose();
                  revealControls();
                }}
                onChange={(event) => {
                  updateVolume(Number(event.target.value));
                  scheduleVolumeClose();
                  revealControls();
                }}
              />
            </div>
            <button
              className={`spiritflix-player__tool spiritflix-player__tool--mini ${isMiniPlayerActive ? "is-active" : ""}`}
              type="button"
              onClick={toggleMiniPlayer}
              aria-label={miniPlayerLabel}
              aria-pressed={isMiniPlayerActive}
              title={miniPlayerSupported ? miniPlayerLabel : `${miniPlayerLabel} (app overlay)`}
            >
              <PictureInPicture2 size={20} aria-hidden="true" />
            </button>
            <button className="spiritflix-player__tool spiritflix-player__tool--fullscreen" type="button" onClick={toggleFullscreen} aria-label={isFullscreen ? "Exit fullscreen" : "Fullscreen"} title={isFullscreen ? "Exit fullscreen" : "Fullscreen"}>
              {isFullscreen ? <Minimize size={20} aria-hidden="true" /> : <Maximize size={20} aria-hidden="true" />}
            </button>

            {showToolOverflow ? (
              <div className="spiritflix-player__tools-overflow" aria-label="Secondary player controls">
                {showLibraryPlayerTools ? (
                  <button
                    className={`spiritflix-player__tool spiritflix-player__tool--model-mix ${knownCurrentModelName && modelShuffleItems.length ? "is-active" : ""}`}
                    type="button"
                    onClick={playKnownModelShuffle}
                    disabled={!knownCurrentModelName || !modelShuffleItems.length}
                    aria-label={
                      knownCurrentModelName
                        ? `Shuffle ${canonicalizeManualModelName(knownCurrentModelName)} model mix`
                        : "Shuffle model mix unavailable"
                    }
                    title={
                      knownCurrentModelName && modelShuffleItems.length
                        ? `Shuffle ${canonicalizeManualModelName(knownCurrentModelName)} (${modelShuffleItems.length})`
                        : "No saved model mix"
                    }
                  >
                    <Shuffle size={20} aria-hidden="true" />
                  </button>
                ) : null}
                {showLibraryPlayerTools ? (
                  <button
                    className={`spiritflix-player__tool spiritflix-player__tool--model ${manualModelRecord?.modelName ? "is-active" : ""}`}
                    type="button"
                    onClick={openModelEditor}
                    aria-label="Edit model name"
                    aria-expanded={isModelEditorOpen}
                    title="Edit model"
                  >
                    <UserRound size={20} aria-hidden="true" />
                  </button>
                ) : null}
                {showLibraryPlayerTools ? (
                  <button
                    className={`spiritflix-player__tool spiritflix-player__tool--tags ${manualTagRecord?.manualTags?.length ? "is-active" : ""}`}
                    type="button"
                    onClick={openTagEditor}
                    aria-label="Edit manual tags"
                    aria-expanded={isTagEditorOpen}
                    title="Edit tags"
                  >
                    <Tag size={20} aria-hidden="true" />
                  </button>
                ) : null}
                {showLibraryPlayerTools ? (
                  <button
                    className={`spiritflix-player__tool spiritflix-player__tool--delete ${isDeleteEditorOpen ? "is-active" : ""}`}
                    type="button"
                    onClick={openDeleteEditor}
                    disabled={!canDeleteFromYes}
                    aria-label="Delete video"
                    aria-expanded={isDeleteEditorOpen}
                    title={canDeleteFromYes ? "Delete video" : "Delete is only available for yes folder videos"}
                  >
                    <Trash2 size={20} aria-hidden="true" />
                  </button>
                ) : null}
              <button
                className={`spiritflix-player__tool spiritflix-player__tool--queue ${isQueueOpen ? "is-active" : ""}`}
                type="button"
                onClick={toggleQueueDrawer}
                disabled={queueItems.length < 2}
                aria-label={isQueueOpen ? "Close queue" : "Open queue"}
                aria-expanded={isQueueOpen}
                aria-controls="spiritflix-player-queue"
                title={isQueueOpen ? "Close queue" : "Open queue"}
              >
                <ListMusic size={20} aria-hidden="true" />
              </button>
              </div>
            ) : null}
          </div>
        </div>

        {upNextTitle ? (
          <div className="spiritflix-player__up-next">
            <span>{isSeriesPlayback ? "Next episode" : "Up next"}</span>
            <strong>{upNextTitle}</strong>
          </div>
        ) : null}
      </div>

      {isModelEditorOpen ? (
        <aside
          className="spiritflix-model-editor"
          role="dialog"
          aria-modal="true"
          aria-label={`Edit model for ${item.Name}`}
          onPointerDownCapture={keepAppWidgetInteraction}
          onPointerUpCapture={keepAppWidgetInteraction}
          onTouchStartCapture={keepAppWidgetInteraction}
          onTouchEndCapture={keepAppWidgetInteraction}
          onFocus={scheduleAppWidgetClose}
        >
          <div className="spiritflix-tag-editor__header">
            <div>
              <span>Model</span>
              <strong>{item.Name}</strong>
            </div>
            <button type="button" onClick={() => setIsModelEditorOpen(false)} aria-label="Close model editor" title="Close">
              <X size={18} aria-hidden="true" />
            </button>
          </div>
          {manualModelLoading ? <p className="spiritflix-tag-editor__note">Loading models...</p> : null}
          {manualModelError ? <p className="spiritflix-tag-editor__error" role="alert">{manualModelError}</p> : null}
          <div className="spiritflix-model-editor__current">
            <div>
              <span>Current model</span>
              <strong>{activeModelName || "Unassigned"}</strong>
            </div>
            <em className={hasSavedManualModel ? "is-saved" : "is-unsaved"}>{modelSystemStatus}</em>
          </div>
          {faceModelSuggestion?.primaryPerformer ? (
            <div className={`spiritflix-model-editor__face-hint is-${faceModelSuggestion.status}`}>
              <div>
                <span>
                  {faceSuggestionConfirmed
                    ? "Face confirmed saved model"
                    : faceSuggestionAutoApplied
                      ? "Auto-used face match"
                      : faceModelSuggestion.status === "confirmed"
                        ? "Face match not saved"
                        : "Face suggestion"}
                </span>
                <strong>{faceModelSuggestion.primaryPerformer.name}</strong>
                <em>{formatFaceConfidence(faceModelSuggestion)} confidence</em>
              </div>
              {!faceSuggestionMatchesCurrentModel ? (
                <button type="button" disabled={manualModelSaving} onClick={() => void saveManualModel(faceModelSuggestion.primaryPerformer?.name ?? "")}>
                  Use
                </button>
              ) : null}
            </div>
          ) : null}
          {showFaceLearningStatus && faceLearningRecord ? (
            <p className="spiritflix-model-editor__learning" aria-live="polite">
              Face learning queued{faceLearningRecord.actions.pendingCorrectionWritten ? " with sidecar correction" : ""}.
            </p>
          ) : null}
          {faceLearningError ? <p className="spiritflix-tag-editor__error" role="alert">{faceLearningError}</p> : null}
          <div className="spiritflix-model-editor__section spiritflix-model-editor__section--assign">
            <span className="spiritflix-model-editor__section-label">Known models</span>
            <div className="spiritflix-tag-editor__chips" aria-label="Known model names">
              {knownModelOptions.map((modelName) => {
                const selected = getModelOptionKey(modelName) === getModelOptionKey(draftModelName);
                return (
                  <button
                    key={modelName}
                    type="button"
                    className={selected ? "is-selected" : undefined}
                    aria-pressed={selected}
                    disabled={manualModelSaving}
                    onClick={() => void saveManualModel(modelName)}
                  >
                    {modelName}
                  </button>
                );
              })}
            </div>
            <form
              className="spiritflix-tag-editor__add"
              onSubmit={(event) => {
                event.preventDefault();
                void saveManualModel();
              }}
            >
              <input
                value={draftModelName}
                onChange={(event) => {
                  manualModelDraftDirtyRef.current = true;
                  setDraftModelName(event.target.value);
                  scheduleAppWidgetClose();
                }}
                placeholder="Model name"
                aria-label="Model name"
                disabled={manualModelSaving}
                list="spiritflix-player-model-options"
              />
              <datalist id="spiritflix-player-model-options">
                {knownModelOptions.map((modelName) => (
                  <option key={modelName} value={modelName} />
                ))}
              </datalist>
              <button type="submit" disabled={manualModelSaving}>Save</button>
            </form>
          </div>
          <div className="spiritflix-tag-editor__actions">
            <span aria-live="polite">
              {manualModelSaving ? "Saving..." : manualModelSavedAt ? `Saved as ${activeModelName}` : hasSavedManualModel ? "Saved in system" : "Save to update system"}
            </span>
            <button type="button" onClick={() => setIsModelEditorOpen(false)}>
              Close
            </button>
          </div>
        </aside>
      ) : null}

      {isTagEditorOpen ? (
        <aside
          className="spiritflix-tag-editor"
          role="dialog"
          aria-modal="true"
          aria-label={`Edit tags for ${item.Name}`}
          onPointerDownCapture={keepAppWidgetInteraction}
          onPointerUpCapture={keepAppWidgetInteraction}
          onTouchStartCapture={keepAppWidgetInteraction}
          onTouchEndCapture={keepAppWidgetInteraction}
          onFocus={scheduleAppWidgetClose}
        >
          <div className="spiritflix-tag-editor__header">
            <div>
              <span>Manual tags</span>
              <strong>{item.Name}</strong>
            </div>
            <button type="button" onClick={() => setIsTagEditorOpen(false)} aria-label="Close tag editor" title="Close">
              <X size={18} aria-hidden="true" />
            </button>
          </div>
          {manualTagsLoading ? <p className="spiritflix-tag-editor__note">Loading tags...</p> : null}
          {manualTagsError ? <p className="spiritflix-tag-editor__error" role="alert">{manualTagsError}</p> : null}
          <div className="spiritflix-tag-editor__chips" aria-label="Action tags">
            <span className="spiritflix-tag-editor__section-label">Action tags</span>
            {actionManualTags.map((tag) => {
              const selected = draftManualTags.includes(tag);
              return (
                <button
                  key={tag}
                  type="button"
                  className={`${selected ? "is-selected" : ""} is-video-scope`.trim()}
                  aria-pressed={selected}
                  disabled={manualTagsSaving}
                  onClick={() => toggleManualTag(tag)}
                >
                  {tag}
                </button>
              );
            })}
          </div>
          {modelAttributeTags.length ? (
            <div className="spiritflix-tag-editor__chips" aria-label="Model attributes">
              <span className="spiritflix-tag-editor__section-label">Model attributes</span>
              {modelAttributeTags.map((tag) => {
                const selected = draftManualTags.includes(tag);
                return (
                  <button
                    key={tag}
                    type="button"
                    className={`${selected ? "is-selected" : ""} is-model-scope`.trim()}
                    aria-pressed={selected}
                    disabled={manualTagsSaving}
                    onClick={() => toggleManualTag(tag)}
                  >
                    {tag}
                  </button>
                );
              })}
            </div>
          ) : null}
          <form
            className="spiritflix-tag-editor__add"
            onSubmit={(event) => {
              event.preventDefault();
              addDraftManualTag();
            }}
          >
            <input
              value={newManualTag}
              onChange={(event) => {
                setNewManualTag(event.target.value);
                scheduleAppWidgetClose();
              }}
              placeholder="Add tag"
              aria-label="Add manual tag"
              disabled={manualTagsSaving}
            />
            <button type="submit" disabled={manualTagsSaving}>Add</button>
          </form>
          <div className="spiritflix-tag-editor__actions">
            <span aria-live="polite">
              {manualTagsSaving ? "Saving..." : manualTagsSavedAt ? "Saved" : "Auto-save on"}
            </span>
            <button type="button" onClick={() => setIsTagEditorOpen(false)}>
              Close
            </button>
          </div>
        </aside>
      ) : null}

      {isDeleteEditorOpen ? (
        <aside
          className="spiritflix-delete-editor"
          role="dialog"
          aria-modal="true"
          aria-label={`Delete ${item.Name}`}
          onPointerDownCapture={keepAppWidgetInteraction}
          onPointerUpCapture={keepAppWidgetInteraction}
          onTouchStartCapture={keepAppWidgetInteraction}
          onTouchEndCapture={keepAppWidgetInteraction}
          onFocus={scheduleAppWidgetClose}
        >
          <div className="spiritflix-tag-editor__header">
            <div>
              <span>Delete video</span>
              <strong>{item.Name}</strong>
            </div>
            <button type="button" onClick={() => setIsDeleteEditorOpen(false)} aria-label="Close delete editor" title="Close">
              <X size={18} aria-hidden="true" />
            </button>
          </div>
          <div className="spiritflix-delete-editor__body">
            <strong>Move this video to trash?</strong>
            <span>{sourcePath || "No source path available"}</span>
          </div>
          {deleteLoading ? <p className="spiritflix-tag-editor__note">Checking delete...</p> : null}
          {deletePreview?.preview?.targetPath ? (
            <p className="spiritflix-tag-editor__note">Trash target: {deletePreview.preview.targetPath}</p>
          ) : null}
          {deleteError ? <p className="spiritflix-tag-editor__error" role="alert">{deleteError}</p> : null}
          <div className="spiritflix-tag-editor__actions">
            <span aria-live="polite">
              {deleteExecuting ? "Deleting..." : deletePreview?.allowed ? "Ready" : "Preview required"}
            </span>
            <button type="button" onClick={() => setIsDeleteEditorOpen(false)}>
              Cancel
            </button>
            <button
              className="spiritflix-delete-editor__confirm"
              type="button"
              disabled={!deletePreview?.allowed || deleteLoading || deleteExecuting}
              onClick={() => void confirmDeleteVideo()}
            >
              Delete
            </button>
          </div>
        </aside>
      ) : null}

      {isQueueOpen ? (
        <aside className="spiritflix-player__queue" id="spiritflix-player-queue" aria-label="Playback queue">
          <div className="spiritflix-player__queue-header">
            <div>
              <span>{queue?.sourceTitle ?? "Queue"}</span>
              <strong>{queueItems.length} videos</strong>
            </div>
            <button type="button" onClick={() => setIsQueueOpen(false)} aria-label="Close queue" title="Close queue">
              <X size={18} aria-hidden="true" />
            </button>
          </div>
          <DndContext
            sensors={queueDndSensors}
            collisionDetection={closestCenter}
            autoScroll={false}
            onDragStart={() => {
              lastQueueDragPairRef.current = null;
              revealControls(true);
            }}
            onDragOver={handleQueueDragOver}
            onDragEnd={handleQueueDragEnd}
            onDragCancel={() => {
              lastQueueDragPairRef.current = null;
            }}
          >
            <SortableContext items={queueDndIds} strategy={verticalListSortingStrategy}>
              <div className="spiritflix-player__queue-list">
                {queueItems.map((queueItem, index) => {
                  const isCurrent = queueItem.Id === item.Id;
                  return (
                    <SortableQueueItem
                      client={client}
                      item={queueItem}
                      index={index}
                      isCurrent={isCurrent}
                      key={queueItem.Id}
                      onSelect={() => {
                        if (!isCurrent) selectQueueItem(queueItem);
                        setIsQueueOpen(false);
                      }}
                    />
                  );
                })}
              </div>
            </SortableContext>
          </DndContext>
        </aside>
      ) : null}
    </section>
  );
}
