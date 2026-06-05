"use client";

import { useCallback, useEffect, useMemo, useRef, useState, type CSSProperties } from "react";
import {
  Activity,
  ChevronsDown,
  Heart,
  Maximize,
  Minimize,
  Pause,
  Play,
  RefreshCw,
  Repeat,
  Repeat1,
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
  onClose: () => void;
}

type FitMode = "fit" | "fill";
type RepeatMode = "off" | "queue" | "one";

const FIT_STORAGE_KEY = "spiritflix_player_fit_mode";
const REPEAT_STORAGE_KEY = "spiritflix_player_repeat_mode";
const TAP_MAX_MOVEMENT = 18;
const TAP_MAX_MS = 420;
const DOUBLE_TAP_MAX_MS = 320;
const DOUBLE_TAP_MAX_DISTANCE = 48;
const PINCH_TOGGLE_THRESHOLD = 0.08;
const PINCH_GESTURE_SUPPRESS_MS = 450;
const UI_TIME_UPDATE_MS = 500;
const PLAYBACK_REPORT_MS = 15000;
const DIAGNOSTIC_SAMPLE_MS = 2000;

interface PlaybackDiagnostics {
  bufferedAheadSeconds: number;
  droppedFrames: number;
  decodedFrames: number;
  networkState: number;
  readyState: number;
  playbackRate: number;
  stallCount: number;
  totalStallMs: number;
  serverDelayMs: number | null;
  streamMode: "direct" | "hls";
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

function getStoredFitMode(): FitMode {
  if (typeof window === "undefined") return "fit";
  window.localStorage.setItem(FIT_STORAGE_KEY, "fit");
  return "fit";
}

function isRepeatMode(value: string | null): value is RepeatMode {
  return value === "off" || value === "queue" || value === "one";
}

function getStoredRepeatMode(): RepeatMode {
  if (typeof window === "undefined") return "off";
  const stored = window.localStorage.getItem(REPEAT_STORAGE_KEY);
  return isRepeatMode(stored) ? stored : "off";
}

function isInteractiveTarget(target: EventTarget | null): boolean {
  return target instanceof Element && Boolean(target.closest("button, input, a, [role='button']"));
}

function getBufferedAheadSeconds(video: HTMLVideoElement): number {
  for (let index = 0; index < video.buffered.length; index += 1) {
    const start = video.buffered.start(index);
    const end = video.buffered.end(index);
    if (video.currentTime >= start && video.currentTime <= end) {
      return Math.max(0, end - video.currentTime);
    }
  }
  return 0;
}

function getFrameStats(video: HTMLVideoElement): { droppedFrames: number; decodedFrames: number } {
  const qualityVideo = video as HTMLVideoElement & {
    getVideoPlaybackQuality?: () => { droppedVideoFrames?: number; totalVideoFrames?: number };
    webkitDroppedFrameCount?: number;
    webkitDecodedFrameCount?: number;
  };
  const quality = qualityVideo.getVideoPlaybackQuality?.();
  return {
    droppedFrames: quality?.droppedVideoFrames ?? qualityVideo.webkitDroppedFrameCount ?? 0,
    decodedFrames: quality?.totalVideoFrames ?? qualityVideo.webkitDecodedFrameCount ?? 0,
  };
}

export function SpiritFlixPlayer({
  client,
  item,
  queue,
  startPositionTicks,
  onPlaybackProgress,
  onToggleFavorite,
  onSelectItem,
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
  const diagnosticTimer = useRef<ReturnType<typeof setInterval> | null>(null);
  const usingHlsRef = useRef(false);
  const waitingSinceRef = useRef<number | null>(null);
  const stallCountRef = useRef(0);
  const totalStallMsRef = useRef(0);
  const serverDelayMsRef = useRef<number | null>(null);
  const pointerStartRef = useRef<{ x: number; y: number; time: number; currentTime: number } | null>(null);
  const lastTapRef = useRef<{ time: number; x: number; y: number } | null>(null);
  const lastPointerTapAtRef = useRef(0);
  const touchTapStartRef = useRef<{ x: number; y: number; time: number } | null>(null);
  const pinchStartRef = useRef<{ startDistance: number; currentDistance: number } | null>(null);
  const suppressPointerUntilRef = useRef(0);
  const volumeRef = useRef(1);
  const mutedRef = useRef(false);
  const repeatModeRef = useRef<RepeatMode>(getStoredRepeatMode());

  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showControls, setShowControls] = useState(true);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [volume, setVolume] = useState(1);
  const [fitMode, setFitMode] = useState<FitMode>(() => getStoredFitMode());
  const [videoAspectRatio, setVideoAspectRatio] = useState(16 / 9);
  const [shellSize, setShellSize] = useState({ width: 0, height: 0 });
  const [streamError, setStreamError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [usingHls, setUsingHls] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const [endedAtQueueEnd, setEndedAtQueueEnd] = useState(false);
  const [repeatMode, setRepeatMode] = useState<RepeatMode>(() => getStoredRepeatMode());
  const [tapFeedback, setTapFeedback] = useState<"play" | "pause" | null>(null);
  const [diagnosticsOpen, setDiagnosticsOpen] = useState(false);
  const [diagnostics, setDiagnostics] = useState<PlaybackDiagnostics>({
    bufferedAheadSeconds: 0,
    droppedFrames: 0,
    decodedFrames: 0,
    networkState: 0,
    readyState: 0,
    playbackRate: 1,
    stallCount: 0,
    totalStallMs: 0,
    serverDelayMs: null,
    streamMode: "direct",
  });

  const queueItems = queue?.items ?? [item];
  const queueIndex = queueItems.findIndex((queueItem) => queueItem.Id === item.Id);
  const currentIndex = queueIndex >= 0 ? queueIndex : queue?.currentIndex ?? 0;
  const previousItem = currentIndex > 0 ? queueItems[currentIndex - 1] : null;
  const nextItem = currentIndex < queueItems.length - 1 ? queueItems[currentIndex + 1] : null;
  const upNextTitle = nextItem?.Name ?? null;
  const isFavorite = Boolean(item.UserData?.IsFavorite);
  const repeatLabel =
    repeatMode === "one" ? "Repeat current video" : repeatMode === "queue" ? "Repeat queue" : "Repeat off";

  const emitPlaybackProgress = useCallback(
    (positionTicks: number, isEnded = false) => {
      onPlaybackProgress({
        itemId: item.Id,
        item,
        positionTicks,
        isEnded,
      });
    },
    [item, onPlaybackProgress],
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
      setShowControls(true);
      if (hideTimer.current) window.clearTimeout(hideTimer.current);
      if (!keepVisible && isPlaying) {
        hideTimer.current = window.setTimeout(() => setShowControls(false), 2600);
      }
    },
    [isPlaying],
  );

  const hideControls = useCallback(() => {
    if (hideTimer.current) window.clearTimeout(hideTimer.current);
    setShowControls(false);
  }, []);

  const flashTapFeedback = useCallback((kind: "play" | "pause") => {
    setTapFeedback(kind);
    if (feedbackTimer.current) window.clearTimeout(feedbackTimer.current);
    feedbackTimer.current = window.setTimeout(() => setTapFeedback(null), 850);
  }, []);

  const seekTo = useCallback((seconds: number) => {
    const video = videoRef.current;
    if (!video) return;
    video.currentTime = Math.max(0, Math.min(video.duration || Number.MAX_SAFE_INTEGER, seconds));
    setCurrentTime(video.currentTime);
  }, []);

  const seekBy = useCallback(
    (seconds: number) => {
      const video = videoRef.current;
      if (!video) return;
      seekTo(video.currentTime + seconds);
      revealControls();
    },
    [revealControls, seekTo],
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

  const selectNextItem = () => {
    if (nextItem) {
      selectQueueItem(nextItem);
      return;
    }
    if (repeatModeRef.current === "queue" && queueItems.length > 0) {
      selectQueueItem(queueItems[0] ?? item);
    }
  };

  const updateVolume = (nextVolume: number) => {
    const video = videoRef.current;
    const clamped = Math.max(0, Math.min(1, nextVolume));
    setVolume(clamped);
    volumeRef.current = clamped;
    if (video) {
      video.volume = clamped;
      video.muted = clamped === 0;
      mutedRef.current = video.muted;
      setIsMuted(video.muted);
    }
  };

  const collectDiagnostics = useCallback(() => {
    const video = videoRef.current;
    if (!video) return;
    const frameStats = getFrameStats(video);
    setDiagnostics({
      bufferedAheadSeconds: getBufferedAheadSeconds(video),
      droppedFrames: frameStats.droppedFrames,
      decodedFrames: frameStats.decodedFrames,
      networkState: video.networkState,
      readyState: video.readyState,
      playbackRate: video.playbackRate,
      stallCount: stallCountRef.current,
      totalStallMs: totalStallMsRef.current,
      serverDelayMs: serverDelayMsRef.current,
      streamMode: usingHlsRef.current ? "hls" : "direct",
    });
  }, []);

  const runServerDiagnostic = useCallback(async () => {
    const startedAt = performance.now();
    try {
      await client.checkPublicInfo();
      serverDelayMsRef.current = Math.round(performance.now() - startedAt);
    } catch {
      serverDelayMsRef.current = -1;
    }
    collectDiagnostics();
  }, [client, collectDiagnostics]);

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return undefined;
    const directUrl = client.getStreamUrl(item.Id);
    let hlsInstance: {
      loadSource: (source: string) => void;
      attachMedia: (media: HTMLMediaElement) => void;
      destroy: () => void;
    } | null = null;
    let cancelled = false;

    const setup = async () => {
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
      stallCountRef.current = 0;
      totalStallMsRef.current = 0;
      video.pause();
      video.removeAttribute("src");
      video.load();
      video.src = directUrl;
      video.volume = volumeRef.current;
      video.muted = mutedRef.current;
      video.loop = repeatModeRef.current === "one";
      video.load();
      const resumeAt = ticksToSeconds(startPositionTicks ?? item.UserData?.PlaybackPositionTicks);
      if (resumeAt) video.currentTime = resumeAt;
      const startTicks = resumeAt ? secondsToTicks(resumeAt) : 0;
      lastReportedTicksRef.current = startTicks;
      await client.reportPlayback(item.Id, "Start", startTicks, false);
      emitPlaybackProgress(startTicks, false);
      await video.play().catch(() => setShowControls(true));
    };

    setup().catch(() => {
      setIsLoading(false);
      setStreamError("Could not prepare this Jellyfin stream.");
    });

    const handleDirectError = async () => {
      if (cancelled || usingHlsRef.current) return;
      try {
        const { default: Hls } = await import("hls.js");
        if (!Hls.isSupported()) {
          setStreamError("This browser could not play the Jellyfin stream.");
          setIsLoading(false);
          return;
        }
        hlsInstance = new Hls();
        hlsInstance.loadSource(client.getHlsUrl(item.Id));
        hlsInstance.attachMedia(video);
        usingHlsRef.current = true;
        setUsingHls(true);
        setStreamError("");
      } catch {
        setStreamError("Direct playback failed and HLS fallback could not start.");
        setIsLoading(false);
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
    if (!diagnosticsOpen) {
      if (diagnosticTimer.current) clearInterval(diagnosticTimer.current);
      diagnosticTimer.current = null;
      return undefined;
    }
    collectDiagnostics();
    void runServerDiagnostic();
    diagnosticTimer.current = setInterval(collectDiagnostics, DIAGNOSTIC_SAMPLE_MS);
    return () => {
      if (diagnosticTimer.current) clearInterval(diagnosticTimer.current);
      diagnosticTimer.current = null;
    };
  }, [collectDiagnostics, diagnosticsOpen, runServerDiagnostic]);

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
          video.muted = !video.muted;
          mutedRef.current = video.muted;
          setIsMuted(video.muted);
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
  }, [onClose, seekBy, toggleFullscreen, togglePlay, volume]);

  const handlePointerDown = (event: React.PointerEvent<HTMLElement>) => {
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
      const isCenterTap = x > shellWidth * 0.32 && x < shellWidth * 0.68;

      if (showControls && isPlaying) {
        hideControls();
        return;
      }

      const lastTap = lastTapRef.current;
      if (
        lastTap &&
        Date.now() - lastTap.time < DOUBLE_TAP_MAX_MS &&
        Math.abs(x - lastTap.x) < DOUBLE_TAP_MAX_DISTANCE &&
        Math.abs(y - lastTap.y) < DOUBLE_TAP_MAX_DISTANCE
      ) {
        lastTapRef.current = null;
        if (x < shellWidth * 0.4) {
          seekBy(-10);
        } else if (x > shellWidth * 0.6) {
          seekBy(10);
        } else {
          togglePlay();
        }
        return;
      }

      lastTapRef.current = { time: Date.now(), x, y };
      if (isCenterTap) {
        togglePlay();
      } else if (showControls) {
        hideControls();
      } else {
        revealControls();
      }
    },
    [hideControls, isPlaying, revealControls, seekBy, showControls, togglePlay],
  );

  const handlePointerUp = (event: React.PointerEvent<HTMLElement>) => {
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
      seekTo(start.currentTime + seconds);
      revealControls();
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
    const first = touches.item(0);
    const second = touches.item(1);
    if (!first || !second) return 0;
    return Math.hypot(second.clientX - first.clientX, second.clientY - first.clientY);
  };

  const playerStyle = useMemo(
    () => {
      const shellAspectRatio =
        shellSize.width > 0 && shellSize.height > 0 ? shellSize.width / shellSize.height : videoAspectRatio;
      const neededFillScale =
        shellAspectRatio > videoAspectRatio
          ? shellAspectRatio / videoAspectRatio
          : videoAspectRatio / shellAspectRatio;

      return {
        "--spiritflix-fill-scale": neededFillScale.toFixed(3),
        "--spiritflix-video-aspect": videoAspectRatio.toFixed(6),
      } as CSSProperties;
    },
    [shellSize.height, shellSize.width, videoAspectRatio],
  );

  return (
    <section
      className={`spiritflix-player is-fit-${fitMode} ${showControls || !isPlaying ? "is-awake" : "is-idle"}`}
      ref={shellRef}
      style={playerStyle}
      aria-label={`${item.Name} player`}
      onPointerDown={handlePointerDown}
      onPointerUp={handlePointerUp}
      onPointerCancel={() => {
        pointerStartRef.current = null;
      }}
      onPointerMove={(event) => {
        if (event.pointerType === "mouse") revealControls();
      }}
      onMouseMove={() => revealControls()}
      onTouchStart={(event) => {
        if (event.touches.length === 2) {
          event.preventDefault();
          const distance = touchDistance(event.touches);
          pinchStartRef.current = { startDistance: distance, currentDistance: distance };
          pointerStartRef.current = null;
          touchTapStartRef.current = null;
          lastTapRef.current = null;
        } else if (event.touches.length === 1 && !isInteractiveTarget(event.target)) {
          const touch = event.touches.item(0);
          if (touch) {
            touchTapStartRef.current = { x: touch.clientX, y: touch.clientY, time: Date.now() };
          }
        }
      }}
      onTouchMove={(event) => {
        const pinch = pinchStartRef.current;
        if (!pinch || event.touches.length !== 2) return;
        const nextDistance = touchDistance(event.touches);
        if (!nextDistance) return;
        event.preventDefault();
        pinchStartRef.current = { ...pinch, currentDistance: nextDistance };
      }}
      onTouchEnd={(event) => {
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
          touchTapStartRef.current = null;
        } else {
          const start = touchTapStartRef.current;
          const touch = event.changedTouches.item(0);
          touchTapStartRef.current = null;
          if (
            start &&
            touch &&
            Date.now() >= suppressPointerUntilRef.current &&
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
          disablePictureInPicture
          controlsList="nodownload noplaybackrate noremoteplayback"
          preload="metadata"
          onWaiting={() => {
            setIsLoading(true);
            if (!waitingSinceRef.current) {
              waitingSinceRef.current = performance.now();
              stallCountRef.current += 1;
            }
          }}
          onCanPlay={() => {
            setStreamError("");
            setIsLoading(false);
            if (waitingSinceRef.current) {
              totalStallMsRef.current += performance.now() - waitingSinceRef.current;
              waitingSinceRef.current = null;
            }
          }}
          onPlaying={() => {
            setIsPlaying(true);
            setIsLoading(false);
            if (waitingSinceRef.current) {
              totalStallMsRef.current += performance.now() - waitingSinceRef.current;
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

      {tapFeedback ? (
        <div className="spiritflix-player__tap-feedback" aria-hidden="true" key={tapFeedback}>
          {tapFeedback === "pause" ? <Pause size={58} aria-hidden="true" /> : <Play size={58} fill="currentColor" aria-hidden="true" />}
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

      {diagnosticsOpen ? (
        <div className="spiritflix-player__diagnostics" aria-label="Playback diagnostics">
          <div>
            <strong>Playback diagnostics</strong>
            <button type="button" onClick={runServerDiagnostic}>Refresh</button>
          </div>
          <dl>
            <div>
              <dt>Mode</dt>
              <dd>{diagnostics.streamMode.toUpperCase()}</dd>
            </div>
            <div>
              <dt>Buffer</dt>
              <dd>{diagnostics.bufferedAheadSeconds.toFixed(1)}s</dd>
            </div>
            <div>
              <dt>Dropped</dt>
              <dd>{diagnostics.droppedFrames} / {diagnostics.decodedFrames}</dd>
            </div>
            <div>
              <dt>Stalls</dt>
              <dd>{diagnostics.stallCount} ({Math.round(diagnostics.totalStallMs)}ms)</dd>
            </div>
            <div>
              <dt>Ready</dt>
              <dd>{diagnostics.readyState}</dd>
            </div>
            <div>
              <dt>Network</dt>
              <dd>{diagnostics.networkState}</dd>
            </div>
            <div>
              <dt>Server</dt>
              <dd>
                {diagnostics.serverDelayMs === null
                  ? "not checked"
                  : diagnostics.serverDelayMs < 0
                    ? "offline"
                    : `${diagnostics.serverDelayMs}ms`}
              </dd>
            </div>
          </dl>
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
            <div className="spiritflix-player__volume">
              <button
                type="button"
                onClick={() => {
                  const video = videoRef.current;
                  if (!video) return;
                  video.muted = !video.muted;
                  mutedRef.current = video.muted;
                  setIsMuted(video.muted);
                }}
                aria-label={isMuted ? "Unmute" : "Mute"}
                title={isMuted ? "Unmute" : "Mute"}
              >
                {isMuted ? <VolumeX size={20} aria-hidden="true" /> : <Volume2 size={20} aria-hidden="true" />}
              </button>
              <input
                aria-label="Volume"
                type="range"
                min={0}
                max={1}
                step={0.01}
                value={isMuted ? 0 : volume}
                onChange={(event) => updateVolume(Number(event.target.value))}
              />
            </div>

            <button
              className={diagnosticsOpen ? "is-active" : undefined}
              type="button"
              onClick={() => {
                setDiagnosticsOpen((open) => !open);
                revealControls(true);
              }}
              aria-label="Playback diagnostics"
              aria-pressed={diagnosticsOpen}
              title="Playback diagnostics"
            >
              <Activity size={20} aria-hidden="true" />
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
    </section>
  );
}
