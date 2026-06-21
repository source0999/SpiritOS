"use client";

import { useCallback, useEffect, useMemo, useRef, useState, type CSSProperties } from "react";
import {
  ChevronsDown,
  Heart,
  ListMusic,
  Maximize,
  Minimize,
  Pause,
  PictureInPicture2,
  Play,
  RefreshCw,
  Repeat,
  Repeat1,
  Shuffle,
  SkipBack,
  SkipForward,
  Volume2,
  VolumeX,
  X,
} from "lucide-react";
import { ticksToSeconds, type JellyfinClient } from "@/lib/spiritflix-jellyfin-client";
import type { JellyfinItem } from "@/lib/spiritflix-types";
import type { SpiritFlixPlaybackProgress, SpiritFlixPlaybackQueue } from "./SpiritFlixApp";

interface SpiritFlixPlayerProps {
  client: JellyfinClient;
  item: JellyfinItem;
  queue: SpiritFlixPlaybackQueue | null;
  startPositionTicks?: number;
  onPlaybackProgress: (progress: SpiritFlixPlaybackProgress) => void;
  onToggleFavorite: (item: JellyfinItem, isFavorite: boolean) => void;
  onSelectItem: (item: JellyfinItem) => void;
  onShuffleQueue: (currentItemId: string) => void;
  onClose: () => void;
}

type FitMode = "fit" | "fill";
type RepeatMode = "off" | "queue" | "one";

const FIT_STORAGE_KEY = "spiritflix_player_fit_mode";
const REPEAT_STORAGE_KEY = "spiritflix_player_repeat_mode";
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

export function SpiritFlixPlayer({
  client,
  item,
  queue,
  startPositionTicks,
  onPlaybackProgress,
  onToggleFavorite,
  onSelectItem,
  onShuffleQueue,
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
  const feedbackTimer = useRef<number | null>(null);
  const tapRevealTimer = useRef<number | null>(null);
  const feedbackIdRef = useRef(0);
  const usingHlsRef = useRef(false);
  const waitingSinceRef = useRef<number | null>(null);
  const itemRef = useRef(item);
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
  const [retryCount, setRetryCount] = useState(0);
  const [endedAtQueueEnd, setEndedAtQueueEnd] = useState(false);
  const [repeatMode, setRepeatMode] = useState<RepeatMode>(() => getStoredRepeatMode());
  const [miniPlayerSupported, setMiniPlayerSupported] = useState(false);
  const [isMiniPlayer, setIsMiniPlayer] = useState(false);
  const [isQueueOpen, setIsQueueOpen] = useState(false);
  const [playbackFeedback, setPlaybackFeedback] = useState<PlaybackFeedback | null>(null);

  const queueItems = queue?.items ?? [item];
  const queueIndex = queueItems.findIndex((queueItem) => queueItem.Id === item.Id);
  const currentIndex = queueIndex >= 0 ? queueIndex : queue?.currentIndex ?? 0;
  const previousItem = currentIndex > 0 ? queueItems[currentIndex - 1] : null;
  const nextItem = currentIndex < queueItems.length - 1 ? queueItems[currentIndex + 1] : null;
  const upNextTitle = nextItem?.Name ?? null;
  const isFavorite = Boolean(item.UserData?.IsFavorite);
  const repeatLabel =
    repeatMode === "one" ? "Repeat current video" : repeatMode === "queue" ? "Repeat queue" : "Repeat off";
  const isShuffled = Boolean(queue?.isShuffled);
  const shuffleLabel = isShuffled
    ? `Shuffle on for ${queue?.sourceTitle ?? "current queue"}`
    : `Shuffle off for ${queue?.sourceTitle ?? "current queue"}`;
  const miniPlayerLabel = miniPlayerSupported ? (isMiniPlayer ? "Exit mini player" : "Mini player") : "Mini player unavailable";

  useEffect(() => {
    itemRef.current = item;
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

  const revealControls = useCallback(
    (keepVisible = false) => {
      setControlsHiddenByUser(false);
      setShowControls(true);
      if (hideTimer.current) window.clearTimeout(hideTimer.current);
      if (!keepVisible && isPlaying) {
        hideTimer.current = window.setTimeout(() => setShowControls(false), 2600);
      }
    },
    [isPlaying],
  );

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
    const activeElement = document.activeElement;
    if (activeElement instanceof HTMLElement && shellRef.current?.contains(activeElement)) {
      activeElement.blur();
    }
    setControlsHiddenByUser(true);
    setShowControls(false);
  }, []);

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
        if (hideTimer.current) window.clearTimeout(hideTimer.current);
        hideTimer.current = window.setTimeout(() => setShowControls(false), 2600);
      }).catch(() => setShowControls(true));
    } else {
      flashTapFeedback("pause");
      video.pause();
    }
    revealControls();
  }, [flashTapFeedback, revealControls]);

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

    const toggle = async () => {
      if (pictureDocument.pictureInPictureElement) {
        await pictureDocument.exitPictureInPicture?.();
        setIsMiniPlayer(false);
        revealControls(true);
        return;
      }

      if (video.webkitPresentationMode === "picture-in-picture") {
        video.webkitSetPresentationMode?.("inline");
        setIsMiniPlayer(false);
        revealControls(true);
        return;
      }

      if (pictureDocument.pictureInPictureEnabled && video.requestPictureInPicture) {
        await video.requestPictureInPicture();
        setIsMiniPlayer(true);
        revealControls(true);
        return;
      }

      if (video.webkitSupportsPresentationMode?.("picture-in-picture")) {
        video.webkitSetPresentationMode?.("picture-in-picture");
        setIsMiniPlayer(true);
        revealControls(true);
      }
    };

    void toggle().catch(() => {
      setMiniPlayerSupported(false);
      setIsMiniPlayer(false);
      revealControls(true);
    });
  }, [revealControls]);

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
    revealControls(true);
  };

  const shuffleCurrentQueue = () => {
    onShuffleQueue(item.Id);
    revealControls(true);
  };

  const toggleQueueDrawer = () => {
    setIsQueueOpen((open) => !open);
    revealControls(true);
  };

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
      revealControls(true);
      void video?.play().catch(() => undefined);
      return;
    }

    updateMuted(true);
    setIsVolumeOpen(true);
    revealControls(true);
  }, [revealControls, updateMuted]);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return undefined;
    const directUrl = client.getStreamUrl(item.Id);
    const hlsUrl = client.getHlsUrl(item.Id);
    const preferHls = typeof window !== "undefined" && window.location.protocol === "https:";
    let hlsInstance: HlsController | null = null;
    let cancelled = false;

    const resetVideo = () => {
      setStreamError("");
      setUsingHls(false);
      setIsLoading(true);
      setEndedAtQueueEnd(false);
      endedRef.current = false;
      lastUiProgressAtRef.current = 0;
      lastUiTimeAtRef.current = 0;
      lastPlaybackReportAtRef.current = performance.now();
      firstNonZeroReportRef.current = false;
      usingHlsRef.current = false;
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
        if (preferHls && !video.muted) {
          video.muted = true;
          mutedRef.current = true;
          setIsMuted(true);
          window.localStorage.setItem(MUTED_STORAGE_KEY, "true");
          await video.play().catch(() => undefined);
        }
        setShowControls(true);
        if (error instanceof DOMException && error.name !== "NotAllowedError") {
          setStreamError(error.message);
        }
      }
    };

    const setup = async () => {
      resetVideo();
      if (preferHls) {
        const hlsReady = await startHls();
        if (!hlsReady) {
          video.src = directUrl;
          video.load();
          setStreamError("");
          setUsingHls(false);
          usingHlsRef.current = false;
        }
      } else {
        video.src = directUrl;
        video.load();
      }
      const resumeAt = ticksToSeconds(startPositionTicks ?? item.UserData?.PlaybackPositionTicks);
      if (resumeAt) video.currentTime = resumeAt;
      const startTicks = resumeAt ? secondsToTicks(resumeAt) : 0;
      lastReportedTicksRef.current = startTicks;
      await client.reportPlayback(item.Id, "Start", startTicks, false);
      emitPlaybackProgress(startTicks, false);
      await startPlayback();
    };

    setup().catch(() => {
      setIsLoading(false);
      setStreamError("Could not prepare this Jellyfin stream.");
    });

    const handleDirectError = async () => {
      if (cancelled || usingHlsRef.current) return;
      const hlsReady = await startHls();
      if (hlsReady) await startPlayback();
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
  }, [client, emitPlaybackProgress, item.Id, item.RunTimeTicks, item.UserData?.PlaybackPositionTicks, retryCount, startPositionTicks]);

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
      setIsMiniPlayer(
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
      if (feedbackTimer.current) window.clearTimeout(feedbackTimer.current);
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
        !controlsHiddenByUser && (showControls || !isPlaying) ? "is-awake" : "is-idle"
      } ${controlsHiddenByUser ? "is-controls-hidden" : ""}`}
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
          <span>{queue?.sourceTitle ?? (usingHls ? "HLS fallback" : "Direct stream")}</span>
        </div>
        <button className="spiritflix-player__collapse" type="button" onClick={onClose} aria-label="Exit player" title="Exit player">
          <ChevronsDown size={22} aria-hidden="true" />
        </button>
      </div>

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
            <button type="button" onClick={() => selectQueueItem(previousItem)} disabled={!previousItem} aria-label="Previous video" title="Previous">
              <SkipBack size={20} aria-hidden="true" />
            </button>
            <button className="spiritflix-player__play" type="button" onClick={togglePlay} aria-label={isPlaying ? "Pause" : "Play"} title={isPlaying ? "Pause" : "Play"}>
              {isPlaying ? <Pause size={30} aria-hidden="true" /> : <Play size={30} fill="currentColor" aria-hidden="true" />}
            </button>
            <button type="button" onClick={selectNextItem} disabled={!nextItem && repeatMode !== "queue"} aria-label="Next video" title="Next">
              <SkipForward size={20} aria-hidden="true" />
            </button>
            <button
              className={repeatMode !== "off" ? "is-active" : undefined}
              type="button"
              onClick={cycleRepeatMode}
              aria-label={repeatLabel}
              aria-pressed={repeatMode !== "off"}
              title={repeatLabel}
            >
              {repeatMode === "one" ? <Repeat1 size={20} aria-hidden="true" /> : <Repeat size={20} aria-hidden="true" />}
            </button>
            <button
              className={isShuffled ? "is-active" : undefined}
              type="button"
              onClick={shuffleCurrentQueue}
              disabled={queueItems.length < 2}
              aria-label={shuffleLabel}
              aria-pressed={isShuffled}
              title={shuffleLabel}
            >
              <Shuffle size={20} aria-hidden="true" />
            </button>
            <button
              className={isFavorite ? "is-active" : undefined}
              type="button"
              onClick={() => {
                onToggleFavorite(item, !isFavorite);
                revealControls(true);
              }}
              aria-label={isFavorite ? "Remove favorite" : "Add favorite"}
              aria-pressed={isFavorite}
              title={isFavorite ? "Remove favorite" : "Add favorite"}
            >
              <Heart size={20} fill={isFavorite ? "currentColor" : "none"} aria-hidden="true" />
            </button>
          </div>

          <div className="spiritflix-player__tools">
            <div className={`spiritflix-player__volume ${isVolumeOpen ? "is-expanded" : ""}`}>
              <button
                type="button"
                onClick={toggleMuted}
                aria-label={isMuted ? "Unmute" : "Mute"}
                aria-controls="spiritflix-player-volume"
                aria-expanded={isVolumeOpen}
                title={isMuted ? "Unmute" : "Mute"}
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
                  revealControls(true);
                }}
                onFocus={() => {
                  setIsVolumeOpen(true);
                  revealControls(true);
                }}
                onChange={(event) => updateVolume(Number(event.target.value))}
              />
            </div>

            <button
              className={isMiniPlayer ? "is-active" : undefined}
              type="button"
              onClick={toggleMiniPlayer}
              disabled={!miniPlayerSupported}
              aria-label={miniPlayerLabel}
              aria-pressed={isMiniPlayer}
              title={miniPlayerLabel}
            >
              <PictureInPicture2 size={20} aria-hidden="true" />
            </button>
            <button
              className={isQueueOpen ? "is-active" : undefined}
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
            <button type="button" onClick={toggleFullscreen} aria-label={isFullscreen ? "Exit fullscreen" : "Fullscreen"} title={isFullscreen ? "Exit fullscreen" : "Fullscreen"}>
              {isFullscreen ? <Minimize size={20} aria-hidden="true" /> : <Maximize size={20} aria-hidden="true" />}
            </button>
          </div>
        </div>

        {upNextTitle ? (
          <div className="spiritflix-player__up-next">
            <span>Up next</span>
            <strong>{upNextTitle}</strong>
          </div>
        ) : null}
      </div>

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
          <div className="spiritflix-player__queue-list">
            {queueItems.map((queueItem, index) => {
              const isCurrent = queueItem.Id === item.Id;
              return (
                <button
                  className={isCurrent ? "is-current" : undefined}
                  type="button"
                  key={`${queueItem.Id}-${index}`}
                  onClick={() => {
                    if (!isCurrent) selectQueueItem(queueItem);
                    setIsQueueOpen(false);
                  }}
                  aria-current={isCurrent ? "true" : undefined}
                >
                  <span>{String(index + 1).padStart(2, "0")}</span>
                  <strong>{queueItem.Name}</strong>
                </button>
              );
            })}
          </div>
        </aside>
      ) : null}
    </section>
  );
}
