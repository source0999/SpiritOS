// ─── Spirit OS · useThread Hook ───────────────────────────────────────────────
//
// Owns all thread and message loading logic for the chat page.
//
// Responsibilities:
//   1. Live-query folders, threads, and messages from Dexie — re-rendering
//      automatically on any insert, update, or delete.
//   2. Expose loading + error states for each query so the UI can show
//      skeleton states instead of empty flashes.
//   3. Provide autoTitle() — a fire-and-forget background call to Ollama that
//      generates a 3-word thread title from the first user message and writes
//      it to Dexie. Runs once per new thread; guarded by a Set to prevent
//      double-fires on React StrictMode double-invocation.
//
// Architecture notes:
//   • Uses useLiveQuery from dexie-react-hooks. The compound index
//     [threadId+createdAt] added in db.ts v2 makes the messages query
//     O(messages_in_thread) instead of O(total_messages).
//   • autoTitle() is intentionally not awaited by the caller. It writes to
//     Dexie on completion, which triggers the live query and updates the
//     sidebar title with zero additional state management.
//   • The titledThreads Set lives outside the hook so it survives React
//     StrictMode's double-mount. In production this is a non-issue, but in
//     dev it prevents two simultaneous Ollama calls for the same thread.
//
// ─────────────────────────────────────────────────────────────────────────────

"use client";

import { useCallback } from "react";
import { useLiveQuery } from "dexie-react-hooks";

import { db, updateThreadTitle } from "@/lib/db";
import type { Folder, Thread, Message } from "@/lib/db.types";

// ── StrictMode guard ──────────────────────────────────────────────────────────
// Tracks which thread IDs have already been submitted for auto-titling.
// Module-level so it survives React StrictMode's double-mount in development.
const titledThreads = new Set<string>();

// ── Return type ───────────────────────────────────────────────────────────────

export interface UseThreadReturn {
  // Data
  folders:  Folder[]  | undefined;
  threads:  Thread[]  | undefined;
  messages: Message[] | undefined;

  // Loading states — undefined means the live query hasn't resolved yet.
  // Components should treat undefined as loading, [] as genuinely empty.
  foldersLoading:  boolean;
  threadsLoading:  boolean;
  messagesLoading: boolean;

  // Auto-titling
  // Call once after the first user message is persisted to Dexie.
  // Safe to call multiple times — internally guarded against double-fires.
  autoTitle: (threadId: string, firstUserMessage: string) => void;
}

// ── Hook ──────────────────────────────────────────────────────────────────────

export function useThread(activeThreadId: string): UseThreadReturn {
  // ── Live queries ───────────────────────────────────────────────────────────
  // Each useLiveQuery returns `undefined` while the initial read is in flight,
  // then the resolved array. Subsequent writes trigger automatic re-renders.

  const folders = useLiveQuery(
    () => db.folders.orderBy("order").toArray(),
    [],
  );

  const threads = useLiveQuery(
    () => db.threads.orderBy("updatedAt").reverse().toArray(),
    [],
  );

  // Uses the [threadId+createdAt] compound index added in db.ts v2.
  // Dexie's .where() with a compound index performs a range scan:
  // it finds the lower bound [threadId, 0] and upper bound [threadId, ∞]
  // without touching rows from other threads.
  const messages = useLiveQuery(
    () =>
      db.messages
        .where("[threadId+createdAt]")
        .between(
          [activeThreadId, 0],
          [activeThreadId, Infinity],
        )
        .toArray(),
    [activeThreadId],
  );

  // ── autoTitle ─────────────────────────────────────────────────────────────
  const autoTitle = useCallback((threadId: string, firstUserMessage: string) => {
    // Guard: never title the same thread twice.
    if (titledThreads.has(threadId)) return;
    // Guard: never attempt to title seed/placeholder threads.
    if (threadId.startsWith("new-") || threadId.startsWith("t")) return;
    titledThreads.add(threadId);

    // Fire and forget — runs in the background while the stream is active.
    void (async () => {
      try {
        // Let the GPU / Ollama slot cool down after the main reply stream so titling
        // does not contend with the next user message on single-slot setups (e.g. RX 580).
        await new Promise((resolve) => setTimeout(resolve, 3_000));

        const res = await fetch("/api/spirit", {
          method:  "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            prompt: [
              "Generate a 3-to-5 word title for a chat thread that starts with this message:",
              `"${firstUserMessage.slice(0, 200)}"`,
              "Reply with ONLY the title. No quotes, no punctuation at the end, no explanation.",
              "Example output: Homelab DNS Hardening Plan",
            ].join("\n"),
            sarcasm: "chill", // use the clean persona for titling — no roasting needed
          }),
        });

        if (!res.ok || !res.body) return;

        // Consume the stream fully to get the complete title text.
        const reader  = res.body.getReader();
        const decoder = new TextDecoder();
        let title = "";

        for (;;) {
          const { done, value } = await reader.read();
          if (done) break;
          title += decoder.decode(value, { stream: true });
        }
        reader.releaseLock();

        // Strip any stray quotes or newlines the model might output.
        const cleaned = title
          .replace(/^["'\s]+|["'\s]+$/g, "")
          .replace(/\n.*/g, "") // take only first line if model adds explanation
          .trim();

        if (cleaned.length >= 3) {
          await updateThreadTitle(threadId, cleaned);
        }
      } catch {
        // Silently swallow — auto-title failure is non-critical.
        // The thread keeps its first-message truncation as the title.
      }
    })();
  }, []); // stable — reads no component state

  // ── Return ─────────────────────────────────────────────────────────────────
  return {
    folders,
    threads,
    messages,
    foldersLoading:  folders === undefined,
    threadsLoading:  threads === undefined,
    messagesLoading: messages === undefined,
    autoTitle,
  };
}
