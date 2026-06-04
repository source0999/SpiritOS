"use client";

import { useEffect, useRef, useState } from "react";
import { Maximize, Pause, Play, RotateCcw, RotateCw, Volume2, VolumeX, X } from "lucide-react";
import { ticksToSeconds, type JellyfinClient } from "@/lib/spiritflix/jellyfin-client";
import type { JellyfinItem } from "@/lib/spiritflix/types";

interface SpiritFlixPlayerProps {
  client: JellyfinClient;
  item: JellyfinItem;
  onClose: () => void;
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

export function SpiritFlixPlayer({ client, item, onClose }: SpiritFlixPlayerProps) {
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const shellRef = useRef<HTMLDivElement | null>(null);
  const progressTimer = useRef<ReturnType<typeof setInterval> | null>(null);
  const usingHlsRef = useRef(false);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [duration, setDuration] = useState(0);
  const [streamError, setStreamError] = useState("");
  const [usingHls, setUsingHls] = useState(false);

  const seek = (seconds: number) => {
    const video = videoRef.current;
    if (!video) return;
    video.currentTime = Math.max(0, Math.min(video.duration || Number.MAX_SAFE_INTEGER, video.currentTime + seconds));
  };

  const togglePlay = () => {
    const video = videoRef.current;
    if (!video) return;
    if (video.paused) {
      void video.play();
    } else {
      video.pause();
    }
  };

  const toggleFullscreen = () => {
    const shell = shellRef.current;
    if (!shell) return;
    if (document.fullscreenElement) {
      void document.exitFullscreen();
    } else {
      void shell.requestFullscreen();
    }
  };

  useEffect(() => {
    const video = videoRef.current;
    if (!video) return;
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
      usingHlsRef.current = false;
      video.src = directUrl;
      video.load();
      const resumeAt = ticksToSeconds(item.UserData?.PlaybackPositionTicks);
      if (resumeAt) video.currentTime = resumeAt;
      await client.reportPlayback(item.Id, "Start", resumeAt ? secondsToTicks(resumeAt) : 0, false);
    };

    setup().catch(() => {
      setStreamError("Could not prepare the Jellyfin stream.");
    });

    const handleDirectError = async () => {
      if (cancelled || usingHlsRef.current) return;
      try {
        const { default: Hls } = await import("hls.js");
        if (!Hls.isSupported()) {
          setStreamError("This browser could not play the direct Jellyfin stream.");
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
      }
    };

    video.addEventListener("error", handleDirectError);
    progressTimer.current = setInterval(() => {
      if (!video.paused) {
        void client.reportPlayback(item.Id, "Progress", secondsToTicks(video.currentTime), false);
      }
    }, 10000);

    return () => {
      cancelled = true;
      video.removeEventListener("error", handleDirectError);
      if (progressTimer.current) clearInterval(progressTimer.current);
      void client.reportPlayback(item.Id, "Stopped", secondsToTicks(video.currentTime), false);
      hlsInstance?.destroy();
    };
  }, [client, item.Id, item.UserData?.PlaybackPositionTicks]);

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.target instanceof HTMLInputElement) return;
      const key = event.key.toLowerCase();
      if (key === " " || key === "k") {
        event.preventDefault();
        togglePlay();
      }
      if (key === "arrowleft") {
        event.preventDefault();
        seek(-10);
      }
      if (key === "arrowright") {
        event.preventDefault();
        seek(10);
      }
      if (key === "m") {
        event.preventDefault();
        const video = videoRef.current;
        if (video) video.muted = !video.muted;
      }
      if (key === "f") {
        event.preventDefault();
        toggleFullscreen();
      }
      if (key === "escape") {
        event.preventDefault();
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  return (
    <section className="spiritflix-player" ref={shellRef} aria-label={`${item.Name} player`}>
      <video
        ref={videoRef}
        playsInline
        controls={false}
        onCanPlay={() => setStreamError("")}
        onPlay={() => setIsPlaying(true)}
        onPause={() => {
          setIsPlaying(false);
          void client.reportPlayback(item.Id, "Progress", secondsToTicks(videoRef.current?.currentTime ?? 0), true);
        }}
        onTimeUpdate={(event) => setCurrentTime(event.currentTarget.currentTime)}
        onLoadedMetadata={(event) => setDuration(event.currentTarget.duration)}
      />

      <div className="spiritflix-player__top">
        <button type="button" onClick={onClose} aria-label="Close player">
          <X size={21} aria-hidden="true" />
        </button>
        <div>
          <strong>{item.Name}</strong>
          <span>{usingHls ? "HLS fallback" : "Direct stream"}</span>
        </div>
      </div>

      {streamError ? <div className="spiritflix-player__error">{streamError}</div> : null}

      <div className="spiritflix-player__controls">
        <button type="button" onClick={() => seek(-10)} aria-label="Seek back 10 seconds">
          <RotateCcw size={20} aria-hidden="true" />
        </button>
        <button className="spiritflix-player__play" type="button" onClick={togglePlay} aria-label="Play or pause">
          {isPlaying ? <Pause size={28} aria-hidden="true" /> : <Play size={28} aria-hidden="true" />}
        </button>
        <button type="button" onClick={() => seek(10)} aria-label="Seek forward 10 seconds">
          <RotateCw size={20} aria-hidden="true" />
        </button>
        <span className="spiritflix-player__time">{formatTime(currentTime)}</span>
        <input
          aria-label="Seek"
          type="range"
          min={0}
          max={duration || 0}
          value={Math.min(currentTime, duration || currentTime)}
          onChange={(event) => {
            const video = videoRef.current;
            if (video) video.currentTime = Number(event.target.value);
          }}
        />
        <span className="spiritflix-player__time">{formatTime(duration)}</span>
        <button
          type="button"
          onClick={() => {
            const video = videoRef.current;
            if (!video) return;
            video.muted = !video.muted;
            setIsMuted(video.muted);
          }}
          aria-label="Mute"
        >
          {isMuted ? <VolumeX size={20} aria-hidden="true" /> : <Volume2 size={20} aria-hidden="true" />}
        </button>
        <button type="button" onClick={toggleFullscreen} aria-label="Fullscreen">
          <Maximize size={20} aria-hidden="true" />
        </button>
      </div>
    </section>
  );
}
