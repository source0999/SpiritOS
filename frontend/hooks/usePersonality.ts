// ─── Spirit OS · usePersonality Hook ─────────────────────────────────────────
//
// Step C: Mem0-style local learning layer.
//
// Captures behavioral signals from every send() and edit, synthesises them
// into a plain-English "Source Profile" string, and passes it to Mirror and
// Chaos mode API calls as `userContext`.
//
// CAPTURED SIGNALS:
//   sarcasm_selected   — which mode Source used (reveals preferred persona)
//   time_of_day        — hour bracket (reveals usage patterns)
//   message_length     — terse vs verbose communication style
//   keyword_frequency  — recurring topics (reveals what Source cares about)
//   correction_made    — Source edited a Spirit message (disagreement signal)
//
// ARCHITECTURE:
//   Pure utility layer — no React state, no re-renders. Every write is
//   fire-and-forget. buildUserContext() is called once per send(), async,
//   reads directly from Dexie, and returns "" if data is insufficient.
//
//   Future Mem0/ChromaDB upgrade: replace the Dexie aggregation in
//   buildUserContext() with a vector similarity query. captureEvent()
//   interface stays identical.
//
// ─────────────────────────────────────────────────────────────────────────────

"use client";

import { useCallback } from "react";
import { db, writePersonalityEvent } from "@/lib/db";
import type { PersonalityEvent } from "@/lib/db.types";

// ── Constants ─────────────────────────────────────────────────────────────────

// Minimum events before we synthesise a context string.
// Avoids injecting meaningless single-sample "profiles".
const MIN_EVENTS_FOR_CONTEXT = 5;

// How many recent events to read per synthesis call.
const CONTEXT_WINDOW = 100;

// Common English words stripped before keyword extraction.
const STOPWORDS = new Set([
  "a","an","the","and","or","but","in","on","at","to","for","of","with",
  "is","it","its","was","are","be","been","being","have","has","had",
  "do","does","did","will","would","could","should","may","might","shall",
  "i","my","me","we","our","you","your","he","his","she","her","they",
  "this","that","these","those","what","how","why","when","where","which",
  "so","if","as","by","from","up","about","into","than","then","just",
  "can","get","got","also","not","no","yes","ok","hi","hey","yeah","like",
]);

// ── Utility functions ─────────────────────────────────────────────────────────

function extractKeywords(text: string, topN = 4): string[] {
  const tokens = text
    .toLowerCase()
    .replace(/[^a-z0-9\s'-]/g, " ")
    .split(/\s+/)
    .filter((w) => w.length > 3 && !STOPWORDS.has(w));

  const freq = new Map<string, number>();
  for (const token of tokens) {
    freq.set(token, (freq.get(token) ?? 0) + 1);
  }

  return [...freq.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, topN)
    .map(([word]) => word);
}

function timeOfDayBracket(hour: number): string {
  if (hour >= 5  && hour < 12) return "morning";
  if (hour >= 12 && hour < 17) return "afternoon";
  if (hour >= 17 && hour < 21) return "evening";
  return "late-night";
}

function messageLengthBracket(chars: number): "short" | "medium" | "long" {
  if (chars < 50)  return "short";
  if (chars < 300) return "medium";
  return "long";
}

// ── Hook ──────────────────────────────────────────────────────────────────────

export interface UsePersonalityReturn {
  /** Capture all per-send signals in one call. Fire-and-forget. */
  captureMessageEvents: (prompt: string, sarcasm: string) => void;
  /** Capture a correction event when Source edits a Spirit message. Fire-and-forget. */
  captureCorrectionEvent: () => void;
  /**
   * Read the last CONTEXT_WINDOW events and synthesise a plain-English
   * Source profile string for injection into Mirror/Chaos prompts.
   * Returns "" if insufficient data — callers should omit userContext in that case.
   */
  buildUserContext: () => Promise<string>;
}

export function usePersonality(): UsePersonalityReturn {

  // ── captureMessageEvents ──────────────────────────────────────────────────
  const captureMessageEvents = useCallback((prompt: string, sarcasm: string) => {
    const hour     = new Date().getHours();
    const bracket  = timeOfDayBracket(hour);
    const length   = messageLengthBracket(prompt.length);
    const keywords = extractKeywords(prompt);

    void writePersonalityEvent({
      type:    "sarcasm_selected",
      payload: { mode: sarcasm },
    });

    void writePersonalityEvent({
      type:    "time_of_day",
      payload: { bracket, hour },
    });

    void writePersonalityEvent({
      type:    "message_length",
      payload: { bracket: length, chars: prompt.length },
    });

    if (keywords.length > 0) {
      void writePersonalityEvent({
        type:    "keyword_frequency",
        payload: { keywords },
      });
    }
  }, []);

  // ── captureCorrectionEvent ────────────────────────────────────────────────
  const captureCorrectionEvent = useCallback(() => {
    void writePersonalityEvent({
      type:    "correction_made",
      payload: { ts: Date.now() },
    });
  }, []);

  // ── buildUserContext ──────────────────────────────────────────────────────
  const buildUserContext = useCallback(async (): Promise<string> => {
    let events: PersonalityEvent[];
    try {
      events = await db.personality_events
        .orderBy("createdAt")
        .reverse()
        .limit(CONTEXT_WINDOW)
        .toArray();
    } catch {
      return "";
    }

    if (events.length < MIN_EVENTS_FOR_CONTEXT) return "";

    // ── Aggregate ──────────────────────────────────────────────────────────
    const modeCounts:    Record<string, number> = {};
    const timeCounts:    Record<string, number> = {};
    const lengthCounts:  Record<string, number> = {};
    const keywordCounts: Record<string, number> = {};
    let corrections = 0;

    for (const event of events) {
      const p = event.payload ?? {};
      if (event.type === "sarcasm_selected" && typeof p.mode === "string") {
        modeCounts[p.mode] = (modeCounts[p.mode] ?? 0) + 1;
      }
      if (event.type === "time_of_day" && typeof p.bracket === "string") {
        timeCounts[p.bracket] = (timeCounts[p.bracket] ?? 0) + 1;
      }
      if (event.type === "message_length" && typeof p.bracket === "string") {
        lengthCounts[p.bracket] = (lengthCounts[p.bracket] ?? 0) + 1;
      }
      if (event.type === "keyword_frequency" && Array.isArray(p.keywords)) {
        for (const kw of p.keywords as string[]) {
          keywordCounts[kw] = (keywordCounts[kw] ?? 0) + 1;
        }
      }
      if (event.type === "correction_made") corrections++;
    }

    // ── Synthesise ─────────────────────────────────────────────────────────
    const lines: string[] = [];

    const topMode = Object.entries(modeCounts).sort((a, b) => b[1] - a[1])[0];
    if (topMode) {
      const label = topMode[0] === "chill" ? "Focus" : topMode[0] === "peer" ? "Mirror" : "Chaos";
      const pct   = Math.round((topMode[1] / events.length) * 100);
      lines.push(`Source primarily uses ${label} mode (~${pct}% of sessions).`);
    }

    const topTime = Object.entries(timeCounts).sort((a, b) => b[1] - a[1])[0];
    if (topTime) {
      lines.push(`Most active during the ${topTime[0]}.`);
    }

    const topLength = Object.entries(lengthCounts).sort((a, b) => b[1] - a[1])[0];
    if (topLength) {
      const desc = topLength[0] === "short" ? "brief prompts (terse, direct)"
        : topLength[0] === "medium" ? "medium-length prompts"
        : "long, detailed prompts (verbose, thorough)";
      lines.push(`Tends to write ${desc}.`);
    }

    const topKeywords = Object.entries(keywordCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 6)
      .map(([w]) => w);
    if (topKeywords.length > 0) {
      lines.push(`Recurring topics: ${topKeywords.join(", ")}.`);
    }

    if (corrections > 0) {
      lines.push(`Has corrected Spirit ${corrections} time${corrections !== 1 ? "s" : ""} — precision matters here.`);
    }

    return lines.join("\n");
  }, []);

  return { captureMessageEvents, captureCorrectionEvent, buildUserContext };
}
