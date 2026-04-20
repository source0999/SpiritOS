// ─── Spirit OS · Dexie Database ───────────────────────────────────────────────
//
// Browser-local IndexedDB via Dexie v4. All chat state — folders, threads,
// messages, settings, and personality telemetry — lives here.
// No server sync; fully sovereign.
//
// Schema versioning:
//   v1 — initial schema: folders, threads, messages, settings
//   v2 — compound index [threadId+createdAt], order index on threads
//   v3 — DATA RESET: wipes all mock seed data, adds personality_events table
//   v4 — mission_overrides audit log for directive history
//
// Usage:
//   import { db } from "@/lib/db";
//   const threads = await db.threads.orderBy("updatedAt").reverse().toArray();
//
// ─────────────────────────────────────────────────────────────────────────────

import Dexie, { type Table } from "dexie";
import type {
  Folder,
  Thread,
  Message,
  Setting,
  PersonalityEvent,
  MissionOverride,
} from "./db.types";

// ── UUID helper ───────────────────────────────────────────────────────────────
export function uid(): string {
  if (typeof crypto !== "undefined" && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

// ── Display time helper ───────────────────────────────────────────────────────
export function nowHHMM(): string {
  return new Date().toLocaleTimeString("en-US", {
    hour:   "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}

// ── SpiritDB ──────────────────────────────────────────────────────────────────
class SpiritDB extends Dexie {
  folders!:            Table<Folder,           string>;
  threads!:            Table<Thread,           string>;
  messages!:           Table<Message,          string>;
  settings!:           Table<Setting,          string>;
  personality_events!: Table<PersonalityEvent, string>;
  mission_overrides!:  Table<MissionOverride,  string>;

  constructor() {
    super("spirit-os");

    // ── v1: initial schema ──────────────────────────────────────────────────
    this.version(1).stores({
      folders:  "id, order, createdAt",
      threads:  "id, folderId, updatedAt, createdAt",
      messages: "id, threadId, createdAt",
      settings: "key",
    });

    // ── v2: compound index + thread order ───────────────────────────────────
    // Adds [threadId+createdAt] compound index for O(k) message queries.
    // Adds order index on threads for dnd-kit persistence.
    this.version(2).stores({
      folders:  "id, order, createdAt",
      threads:  "id, folderId, order, updatedAt, createdAt",
      messages: "id, threadId, [threadId+createdAt], createdAt",
      settings: "key",
    });

    // ── v3: data reset + personality_events table ───────────────────────────
    //
    // WHAT THIS MIGRATION DOES:
    //   1. Clears all mock/seed data (folders, threads, messages) so the DB
    //      starts completely clean. Real conversations replace the demo data.
    //   2. Deletes the "seeded" flag so seedDatabase() writes fresh defaults.
    //   3. Adds the personality_events table — the foundation for Mem0-style
    //      continuous learning of Source's communication patterns and interests.
    //
    // WHY A MIGRATION (not indexedDB.deleteDatabase):
    //   Deleting the database destroys the version history, causing Dexie to
    //   re-run ALL migrations from v1 on next open — which would re-seed the
    //   mock data. The upgrade() function runs exactly once per browser profile,
    //   inside Dexie's own transaction, with no risk of partial state.
    //
    this.version(3)
      .stores({
        folders:            "id, order, createdAt",
        threads:            "id, folderId, order, updatedAt, createdAt",
        messages:           "id, threadId, [threadId+createdAt], createdAt",
        settings:           "key",
        // Personality event log — indexed by type and createdAt for fast
        // range queries (e.g. "last 50 events", "all topic_mentioned events").
        personality_events: "id, type, createdAt",
      })
      .upgrade(async (tx) => {
        // Wipe all mock content atomically. If the tab closes mid-upgrade,
        // Dexie rolls back and retries on next open — no partial wipe.
        await tx.table("folders").clear();
        await tx.table("threads").clear();
        await tx.table("messages").clear();

        // Lift the seed guard so seedDatabase() can write clean defaults.
        await tx.table("settings").delete("seeded");

        // personality_events is a new table — no data to migrate.
      });

    // ── v4: mission_overrides audit log ────────────────────────────────────
    // Adds an append-only history table for every directive Source sets via
    // "Spirit, change your mission to X". The active directive is still
    // stored in settings["customDirective"] for fast reads on every send;
    // this table provides the full history for future Mem0 integration.
    // No data migration needed — new table, existing rows unaffected.
    this.version(4).stores({
      folders:            "id, order, createdAt",
      threads:            "id, folderId, order, updatedAt, createdAt",
      messages:           "id, threadId, [threadId+createdAt], createdAt",
      settings:           "key",
      personality_events: "id, type, createdAt",
      mission_overrides:  "id, active, createdAt",
    });
  }
}

// ── Singleton export ──────────────────────────────────────────────────────────
export const db = new SpiritDB();

// ── Default settings ──────────────────────────────────────────────────────────
// Written by seedDatabase() on first run after the v3 wipe.
// No mock folders, threads, or messages — Source's real conversations are
// the only content in the DB from this point forward.
const DEFAULT_SETTINGS: Setting[] = [
  { key: "sarcasm",    value: JSON.stringify("peer")     },
  { key: "ttsEnabled", value: JSON.stringify(false)      },
  { key: "model",      value: JSON.stringify("dolphin3") },
];

// ── seedDatabase ──────────────────────────────────────────────────────────────
// Writes default settings on first run (after v3 wipe clears the "seeded" key).
// Intentionally writes NO content — no demo folders, threads, or messages.
// The UI opens to a fresh new chat. That's the correct starting state.
export async function seedDatabase(): Promise<void> {
  const alreadySeeded = await db.settings.get("seeded");
  if (alreadySeeded) return;

  await db.transaction("rw", db.settings, async () => {
    // bulkPut (not bulkAdd) so re-runs after a failed seed don't throw
    // on duplicate key errors for any settings that got partially written.
    await db.settings.bulkPut(DEFAULT_SETTINGS);
    await db.settings.put({ key: "seeded", value: JSON.stringify(true) });
  });
}

// ── Thread helpers ────────────────────────────────────────────────────────────

export async function createThread(
  folderId: string | null,
  firstUserText: string,
): Promise<Thread> {
  const now = Date.now();
  const thread: Thread = {
    id:        uid(),
    folderId,
    title:     firstUserText.slice(0, 50) || "New thread",
    preview:   firstUserText.slice(0, 60),
    updatedAt: now,
    createdAt: now,
  };
  await db.threads.add(thread);
  return thread;
}

export async function touchThread(threadId: string, preview: string): Promise<void> {
  await db.threads.update(threadId, {
    preview:   preview.slice(0, 60),
    updatedAt: Date.now(),
  });
}

// ── Message helpers ───────────────────────────────────────────────────────────

export async function addMessage(
  threadId: string,
  role: Message["role"],
  text: string,
): Promise<Message> {
  const msg: Message = {
    id:        uid(),
    threadId,
    role,
    text,
    ts:        nowHHMM(),
    audioUrl:  null,
    createdAt: Date.now(),
  };
  await db.messages.add(msg);
  return msg;
}

// ── Settings helpers ──────────────────────────────────────────────────────────

export async function getSetting<T>(key: string, fallback: T): Promise<T> {
  const row = await db.settings.get(key);
  if (!row) return fallback;
  try {
    return JSON.parse(row.value) as T;
  } catch {
    return fallback;
  }
}

export async function setSetting(key: string, value: unknown): Promise<void> {
  await db.settings.put({ key, value: JSON.stringify(value) });
}

// ── Thread title helper ───────────────────────────────────────────────────────
// Called by useThread's autoTitle() after the background Ollama title stream
// resolves. Updates the thread title in the sidebar live query immediately.
export async function updateThreadTitle(threadId: string, title: string): Promise<void> {
  const trimmed = title.trim().slice(0, 60);
  if (!trimmed) return;
  await db.threads.update(threadId, { title: trimmed });
}

// ── Personality event helper ──────────────────────────────────────────────────
// Fire-and-forget write. Called by usePersonality's captureEvent().
// Returns the written event's id so callers can reference it if needed,
// but errors are swallowed — telemetry must never block the UI.
export async function writePersonalityEvent(
  event: Omit<PersonalityEvent, "id" | "createdAt">,
): Promise<void> {
  try {
    await db.personality_events.add({
      ...event,
      id:        uid(),
      createdAt: Date.now(),
    });
  } catch {
    // Swallow silently — telemetry failure must not surface to the user.
  }
}

// ── Custom directive helper ───────────────────────────────────────────────────
// Reads the active custom directive set by Source via "Spirit, change your
// mission to X". Returns null if no directive has been set.
// Called by page.tsx send() on every message to inject into the API payload.
export async function getCustomDirective(): Promise<string | null> {
  const row = await db.settings.get("customDirective");
  if (!row) return null;
  try {
    const val = JSON.parse(row.value) as unknown;
    return typeof val === "string" && val.trim() ? val.trim() : null;
  } catch {
    return null;
  }
}

// Clears the custom directive.
export async function clearCustomDirective(): Promise<void> {
  await db.settings.delete("customDirective");
}

// ── Mission override audit log ────────────────────────────────────────────────
// Called whenever Source sets a new directive. Marks all previous overrides
// as inactive, then inserts the new one as active.
// Fire-and-forget safe — errors are swallowed so they never block send().
export async function logMissionOverride(directive: string): Promise<void> {
  try {
    await db.transaction("rw", db.mission_overrides, async () => {
      const previous = await db.mission_overrides.filter((o) => o.active).toArray();
      for (const prev of previous) {
        await db.mission_overrides.update(prev.id, { active: false });
      }
      await db.mission_overrides.add({
        id:        uid(),
        directive: directive.trim(),
        active:    true,
        createdAt: Date.now(),
      });
    });
  } catch {
    // Swallow — audit log failure must never block the directive being set.
  }
}
