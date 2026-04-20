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

  const speak = useCallback(async (text: string) => {
    // #region agent log
    fetch("http://localhost:7454/ingest/da155463-47fd-4bed-94cb-233903115f13", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "7d6688" },
      body: JSON.stringify({
        sessionId: "7d6688",
        runId: "tts-debug-1",
        hypothesisId: "H2",
        location: "useTTS.ts:speak",
        message: "speak called",
        data: { isTTSEnabled, textLen: text.trim().length },
        timestamp: Date.now(),
      }),
    }).catch(() => {});
    // #endregion
    if (!text.trim() || !isTTSEnabled) return;
    const segments = parseTtsSegments(text);
    // #region agent log
    fetch("http://localhost:7454/ingest/da155463-47fd-4bed-94cb-233903115f13", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "7d6688" },
      body: JSON.stringify({
        sessionId: "7d6688",
        runId: "tts-debug-1",
        hypothesisId: "H2",
        location: "useTTS.ts:speak",
        message: "segments parsed",
        data: {
          segmentCount: segments.length,
          speechCount: segments.filter((s) => s.type === "speech").length,
        },
        timestamp: Date.now(),
      }),
    }).catch(() => {});
    // #endregion
    if (!segments.length) return;
    try {
      await queueRef.current?.play(segments, "en");
      // #region agent log
      fetch("http://localhost:7454/ingest/da155463-47fd-4bed-94cb-233903115f13", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "7d6688" },
        body: JSON.stringify({
          sessionId: "7d6688",
          runId: "tts-debug-2",
          hypothesisId: "H9",
          location: "useTTS.ts:speak",
          message: "queue.play resolved",
          data: {},
          timestamp: Date.now(),
        }),
      }).catch(() => {});
      // #endregion
    } catch (e) {
      // #region agent log
      fetch("http://localhost:7454/ingest/da155463-47fd-4bed-94cb-233903115f13", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-Debug-Session-Id": "7d6688" },
        body: JSON.stringify({
          sessionId: "7d6688",
          runId: "tts-debug-2",
          hypothesisId: "H9",
          location: "useTTS.ts:speak",
          message: "queue.play rejected",
          data: { error: e instanceof Error ? e.message : String(e) },
          timestamp: Date.now(),
        }),
      }).catch(() => {});
      // #endregion
      throw e;
    }
  }, [isTTSEnabled]);

  return {
    speak,
    stop,
    isPlaying,
    isTTSEnabled,
    toggleTTS,
  };
}
