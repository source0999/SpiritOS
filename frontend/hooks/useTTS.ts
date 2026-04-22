"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { getSetting, setSetting } from "@/lib/db";
import { AudioQueue } from "@/lib/audioQueue";
import { parseTtsSegments } from "@/lib/ttsParser";

export type UseTTSOptions = { alwaysOn?: boolean };

export function useTTS(config?: { alwaysOn?: boolean }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [isTTSEnabled, setIsTTSEnabled] = useState(() => (config?.alwaysOn ? true : false));
  const [state, setState] = useState<AudioContextState>("suspended");
  const [queueLength, setQueueLength] = useState(0);
  const queueRef = useRef<AudioQueue | null>(null);

  useEffect(() => {
    queueRef.current = new AudioQueue({
      onPlayingChange: setIsPlaying,
      onQueuedDepthChange: setQueueLength,
      onContextStateChange: setState,
    });
    setState(queueRef.current.peekContextState());
    return () => {
      queueRef.current?.stop();
      queueRef.current = null;
    };
  }, []);

  useEffect(() => {
    if (config?.alwaysOn) return;
    getSetting<boolean>("ttsEnabled", false)
      .then(setIsTTSEnabled)
      .catch(() => setIsTTSEnabled(false));
  }, [config?.alwaysOn]);

  const toggleTTS = useCallback(() => {
    if (config?.alwaysOn) return;
    setIsTTSEnabled((prev) => {
      const next = !prev;
      void setSetting("ttsEnabled", next);
      if (!next) queueRef.current?.stop();
      return next;
    });
  }, [config?.alwaysOn]);

  const stop = useCallback(() => {
    queueRef.current?.stop();
  }, []);

  const prime = useCallback(() => {
    queueRef.current?.prime();
  }, []);

  /** Mid-stream chat: one sentence per call, queued without cancelling prior audio. */
  const enqueue = useCallback(
    (text: string) => {
      if (!text.trim()) return;
      if (config?.alwaysOn || isTTSEnabled) {
        queueRef.current?.enqueue(text);
      }
    },
    [isTTSEnabled, config?.alwaysOn],
  );

  const drain = useCallback(() => queueRef.current?.drain() ?? Promise.resolve(), []);

  /** Manual replay: stop once, enqueue speech segments only (pause markers dropped). */
  const speak = useCallback(
    (text: string) => {
      const isEnabled = config?.alwaysOn || isTTSEnabled;
      if (!text.trim() || !isEnabled) return;
      const segments = parseTtsSegments(text);
      if (!segments.length) return;
      queueRef.current?.stop();
      for (const seg of segments) {
        if (seg.type === "speech") queueRef.current?.enqueue(seg.text);
      }
    },
    [config?.alwaysOn, isTTSEnabled],
  );

  return {
    speak,
    enqueue,
    drain,
    stop,
    prime,
    state,
    queueLength,
    isPlaying,
    isTTSEnabled,
    toggleTTS,
  };
}
