"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { getSetting, setSetting } from "@/lib/db";
import { AudioQueue } from "@/lib/audioQueue";
import { parseTtsSegments } from "@/lib/ttsParser";

export function useTTS() {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isTTSEnabled, setIsTTSEnabled] = useState(false);
  const queueRef = useRef<AudioQueue | null>(null);

  useEffect(() => {
    queueRef.current = new AudioQueue({
      onPlayingChange: setIsPlaying,
    });
    return () => {
      queueRef.current?.stop();
      queueRef.current = null;
    };
  }, []);

  useEffect(() => {
    getSetting<boolean>("ttsEnabled", false)
      .then(setIsTTSEnabled)
      .catch(() => setIsTTSEnabled(false));
  }, []);

  const toggleTTS = useCallback(() => {
    setIsTTSEnabled((prev) => {
      const next = !prev;
      void setSetting("ttsEnabled", next);
      if (!next) queueRef.current?.stop();
      return next;
    });
  }, []);

  const stop = useCallback(() => {
    queueRef.current?.stop();
  }, []);

  /** Mid-stream chat: one sentence per call, queued without cancelling prior audio. */
  const enqueue = useCallback((text: string) => {
    if (!text.trim() || !isTTSEnabled) return;
    queueRef.current?.enqueue(text);
  }, [isTTSEnabled]);

  const drain = useCallback(() => queueRef.current?.drain() ?? Promise.resolve(), []);

  /** Manual replay: stop once, enqueue speech segments only (pause markers dropped). */
  const speak = useCallback((text: string) => {
    if (!text.trim() || !isTTSEnabled) return;
    const segments = parseTtsSegments(text);
    if (!segments.length) return;
    queueRef.current?.stop();
    for (const seg of segments) {
      if (seg.type === "speech") queueRef.current?.enqueue(seg.text);
    }
  }, [isTTSEnabled]);

  return {
    speak,
    enqueue,
    drain,
    stop,
    isPlaying,
    isTTSEnabled,
    toggleTTS,
  };
}
