// ─── Spirit OS · useStream Hook ───────────────────────────────────────────────
//
// Consumes a raw UTF-8 ReadableStream from /api/spirit and surfaces three
// pieces of state to the caller:
//
//   streamingText  — the live, accumulating token string (drives the UI)
//   isStreaming    — true while the pump is running
//   error          — set if the fetch or stream fails
//
// Architecture decisions (cross-referenced against open-webui + lobe-chat):
//
//  1. ACCUMULATOR REF + rAF FLUSH
//     Tokens are appended to a `useRef` string, NOT directly to React state.
//     A `requestAnimationFrame` loop reads the ref and flushes to state once
//     per frame (~60fps). This fully decouples stream speed from React's render
//     cycle and eliminates the back-pressure stutter seen when setState() is
//     called inside a tight pump loop.
//
//  2. SINGLE DEXIE WRITE ON COMPLETION
//     The `onComplete` callback is invoked exactly once — after the reader
//     signals `done: true`. This avoids IndexedDB transaction lock contention
//     that occurs when writes happen mid-stream.
//
//  3. ABORT CONTROLLER
//     Every stream is tied to an AbortController. Calling `abort()` (or
//     unmounting the component) cancels the fetch and breaks the pump loop
//     cleanly without leaving dangling readers.
//
// ─────────────────────────────────────────────────────────────────────────────

"use client";

import { useState, useRef, useCallback } from "react";

// ── Types ─────────────────────────────────────────────────────────────────────

export interface StreamOptions {
  /** Called with the fully accumulated text once the stream closes. */
  onComplete?: (fullText: string) => void;
  /** Called immediately if the fetch or stream pump throws. */
  onError?: (err: Error) => void;
}

export interface StreamState {
  /** Live token string. Empty string when not streaming. */
  streamingText: string;
  /** True from first token until stream closes or errors. */
  isStreaming: boolean;
  /** Non-null if the stream failed. Reset to null on next `startStream` call. */
  error: Error | null;
  /** Fire-and-forget: starts the stream. Safe to call while a stream is running
   *  (it aborts the previous one first). */
  startStream: (prompt: string, sarcasm: string) => void;
  /** Imperatively abort an in-flight stream (e.g. user clicks Stop). */
  abort: () => void;
}

// ── Hook ──────────────────────────────────────────────────────────────────────

export function useStream(options: StreamOptions = {}): StreamState {
  const { onComplete, onError } = options;

  const [streamingText, setStreamingText] = useState("");
  const [isStreaming,   setIsStreaming]   = useState(false);
  const [error,         setError]         = useState<Error | null>(null);

  // Accumulator: tokens land here first; rAF loop flushes to state.
  const accRef        = useRef("");
  // Dirty flag: true when accRef has new content not yet flushed to state.
  const dirtyRef      = useRef(false);
  // rAF handle so we can cancel on abort/unmount.
  const rafHandleRef  = useRef<number | null>(null);
  // AbortController for the current in-flight fetch.
  const abortCtrlRef  = useRef<AbortController | null>(null);

  // ── rAF flush loop ────────────────────────────────────────────────────────
  // Runs every animation frame while streaming. Only calls setState when the
  // accumulator has changed, keeping idle frames at zero cost.
  const startRafLoop = useCallback(() => {
    function tick() {
      if (dirtyRef.current) {
        setStreamingText(accRef.current);
        dirtyRef.current = false;
      }
      rafHandleRef.current = requestAnimationFrame(tick);
    }
    rafHandleRef.current = requestAnimationFrame(tick);
  }, []);

  const stopRafLoop = useCallback(() => {
    if (rafHandleRef.current !== null) {
      cancelAnimationFrame(rafHandleRef.current);
      rafHandleRef.current = null;
    }
  }, []);

  // ── abort ─────────────────────────────────────────────────────────────────
  const abort = useCallback(() => {
    abortCtrlRef.current?.abort();
    stopRafLoop();
    setIsStreaming(false);
  }, [stopRafLoop]);

  // ── startStream ───────────────────────────────────────────────────────────
  const startStream = useCallback(
    (prompt: string, sarcasm: string) => {
      // Abort any previous in-flight stream.
      abortCtrlRef.current?.abort();
      stopRafLoop();

      // Reset all transient state.
      accRef.current   = "";
      dirtyRef.current = false;
      setStreamingText("");
      setError(null);
      setIsStreaming(true);

      const ctrl = new AbortController();
      abortCtrlRef.current = ctrl;

      // Kick off the rAF flush loop before the first await so the UI
      // updates as soon as the first token arrives.
      startRafLoop();

      // ── Async pump (IIFE — no async in useCallback body) ────────────────
      void (async () => {
        try {
          const res = await fetch("/api/spirit", {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({ prompt, sarcasm }),
            signal:  ctrl.signal,
          });

          if (!res.ok) {
            // Non-streaming error (4xx/5xx JSON body from the proxy).
            const errData = await res.json().catch(() => ({})) as { error?: string };
            throw new Error(errData.error ?? `Spirit API error ${res.status}`);
          }

          if (!res.body) {
            throw new Error("No stream body returned from /api/spirit.");
          }

          // ── Token pump ──────────────────────────────────────────────────
          // Each chunk is raw UTF-8 text (token deltas), NOT JSON.
          // The /api/spirit route already strips the Ollama NDJSON envelope.
          const reader  = res.body.getReader();
          const decoder = new TextDecoder();

          for (;;) {
            const { done, value } = await reader.read();
            if (done) break;
            const chunk = decoder.decode(value, { stream: true });
            accRef.current  += chunk;
            dirtyRef.current = true;
          }

          reader.releaseLock();

          // ── Final flush: ensure last tokens reach state before onComplete ─
          setStreamingText(accRef.current);

        } catch (err) {
          // AbortError is expected on user-initiated abort — not a real error.
          if (err instanceof DOMException && err.name === "AbortError") return;

          const wrapped = err instanceof Error ? err : new Error(String(err));
          setError(wrapped);
          onError?.(wrapped);

        } finally {
          // Only runs if we didn't early-return on AbortError.
          stopRafLoop();
          setIsStreaming(false);

          // Fire onComplete with the full accumulated text.
          // The caller (page.tsx) uses this to write to Dexie exactly once.
          const fullText = accRef.current;
          if (fullText) {
            onComplete?.(fullText);
          }

          abortCtrlRef.current = null;
        }
      })();
    },
    [onComplete, onError, startRafLoop, stopRafLoop],
  );

  return { streamingText, isStreaming, error, startStream, abort };
}
