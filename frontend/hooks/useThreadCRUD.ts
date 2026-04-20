// ─── Spirit OS · useThreadCRUD Hook ──────────────────────────────────────────
//
// Provides all mutating Dexie operations for the chat workspace:
//
//   renameThread(id, title)   — updates thread title in place
//   deleteThread(id)          — atomic transaction: deletes thread + all its
//                               messages in a single IndexedDB transaction.
//                               Returns the id of the next thread to select
//                               (or null if no threads remain).
//   editMessage(id, text)     — updates a single message's text content
//
// Architecture notes:
//   • deleteThread uses a Dexie transaction so a tab-crash mid-delete never
//     leaves orphaned messages. Without the transaction, two sequential awaits
//     could leave messages in the DB with no parent thread.
//   • All functions are stable useCallback refs — safe to pass as props
//     without triggering re-renders in memo'd children.
//   • threads is passed in rather than queried internally so this hook stays
//     pure and doesn't duplicate the live query owned by useThread.
//
// ─────────────────────────────────────────────────────────────────────────────

"use client";

import { useCallback } from "react";
import { db } from "@/lib/db";
import type { Thread } from "@/lib/db.types";

export interface UseThreadCRUDReturn {
  renameThread: (id: string, newTitle: string) => Promise<void>;
  deleteThread: (id: string, threads: Thread[]) => Promise<string | null>;
  editMessage: (id: string, newText: string) => Promise<void>;
}

export function useThreadCRUD(): UseThreadCRUDReturn {
  // ── renameThread ──────────────────────────────────────────────────────────
  const renameThread = useCallback(async (id: string, newTitle: string) => {
    const trimmed = newTitle.trim().slice(0, 60);
    if (!trimmed) return; // reject empty titles silently
    await db.threads.update(id, { title: trimmed });
  }, []);

  // ── deleteThread ──────────────────────────────────────────────────────────
  // Returns the id of the thread the UI should switch to after deletion,
  // or null if no threads remain. The caller is responsible for updating
  // activeThreadId — the hook stays free of UI state.
  const deleteThread = useCallback(async (
    id: string,
    threads: Thread[],
  ): Promise<string | null> => {
    // Determine next thread BEFORE the delete so we can return it.
    const currentIndex = threads.findIndex((t) => t.id === id);
    const next =
      threads[currentIndex + 1] ??
      threads[currentIndex - 1] ??
      null;

    // Atomic transaction: thread + all its messages, or nothing.
    await db.transaction("rw", db.threads, db.messages, async () => {
      await db.threads.delete(id);
      await db.messages.where("threadId").equals(id).delete();
    });

    return next?.id ?? null;
  }, []);

  // ── editMessage ───────────────────────────────────────────────────────────
  const editMessage = useCallback(async (id: string, newText: string) => {
    const trimmed = newText.trim();
    if (!trimmed) return;
    await db.messages.update(id, { text: trimmed });
  }, []);

  return { renameThread, deleteThread, editMessage };
}
