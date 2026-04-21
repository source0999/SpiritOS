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
    // #region agent log
    fetch("http://localhost:7454/ingest/da155463-47fd-4bed-94cb-233903115f13", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "c26fba" },
      body: JSON.stringify({
        sessionId: "c26fba",
        runId: "pre-fix",
        hypothesisId: "H2",
        location: "useTTS.ts:speak",
        message: "manual speak invoked",
        data: {
          textLen: text.length,
          segmentCount: segments.length,
          speechCount: segments.filter((s) => s.type === "speech").length,
        },
        timestamp: Date.now(),
      }),
    }).catch(() => {});
    // #endregion
    queueRef.current?.stop();
    for (const seg of segments) {
      if (seg.type === "speech") queueRef.current?.enqueue(seg.text);
    }
    // #region agent log
    fetch("http://localhost:7454/ingest/da155463-47fd-4bed-94cb-233903115f13", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "c26fba" },
      body: JSON.stringify({
        sessionId: "c26fba",
        runId: "pre-fix",
        hypothesisId: "H2",
        location: "useTTS.ts:speak",
        message: "manual speak enqueue loop done",
        data: {},
        timestamp: Date.now(),
      }),
    }).catch(() => {});
    // #endregion
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
