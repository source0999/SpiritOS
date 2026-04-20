// ─── Spirit OS · IndexedDB Type Definitions ──────────────────────────────────
//
// All Dexie table rows are defined here. Each interface maps 1:1 to a Dexie
// table. The `id` field is always a string UUID generated client-side so
// records can be constructed offline before the write is committed.
//
// Keep this file free of any Dexie imports — it is consumed by both the
// database class (lib/db.ts) and UI components without pulling in Dexie.
// ─────────────────────────────────────────────────────────────────────────────

export type SarcasmLevel = "chill" | "peer" | "unhinged";
export type MessageRole  = "user" | "spirit";

// ── Folder ────────────────────────────────────────────────────────────────────
// A workspace folder that groups related threads by topic.
// `accent` is a full Tailwind bg-* class (e.g. "bg-emerald-500") stored as a
// string so the compiler sees it and keeps it in the purge-safe bundle.
export interface Folder {
  id:        string;
  name:      string;
  accent:    string;
  order:     number;   // display order; rewritten by dnd-kit on drag-end
  createdAt: number;   // Unix ms
}

// ── Thread ────────────────────────────────────────────────────────────────────
// A single conversation thread, optionally nested inside a Folder.
// folderId === null → the thread is uncategorized and floats in "Threads".
export interface Thread {
  id:        string;
  folderId:  string | null;
  title:     string;
  preview:   string;   // last message truncated to ~60 chars; updated on send
  order?:    number;   // persisted sidebar order (Step 5 dnd-kit)
  updatedAt: number;   // Unix ms; sidebar sorts threads by this descending
  createdAt: number;
}

// ── Message ───────────────────────────────────────────────────────────────────
// A single turn inside a Thread.
// `audioUrl` is set by the XTTS pipeline (Module 4) once TTS audio is cached;
// null means no audio has been generated or XTTS is disabled.
export interface Message {
  id:        string;
  threadId:  string;
  role:      MessageRole;
  text:      string;
  ts:        string;   // display time, "HH:MM" format
  audioUrl:  string | null;
  createdAt: number;
}

// ── Settings ──────────────────────────────────────────────────────────────────
// Key/value store for user preferences. Typed values are JSON-serialised.
// Known keys and their value shapes are listed below for reference:
//
//   "sarcasm"   → SarcasmLevel           default: "peer"
//   "ttsEnabled"→ boolean                default: false
//   "model"     → string                 default: "dolphin3"
//   "seeded"    → boolean                seed guard — set after first-run seed
//
export interface Setting {
  key:   string;
  value: string;   // JSON.stringify'd so every primitive fits a single type
}

// ── Personality event ─────────────────────────────────────────────────────────
// Append-only log for Step C (Mem0-style learning). Indexed in Dexie by `type`
// and `createdAt` for range queries.
export interface PersonalityEvent {
  id:        string;
  type:      string;
  createdAt: number;
  /** Optional structured payload (topics, tone hints, etc.) */
  payload?:  Record<string, unknown>;
}

// ── Mission Override ──────────────────────────────────────────────────────────
// Append-only audit log for every directive change Source makes via
// "Spirit, change your mission to X". Complements the live settings key
// (which stores only the current active directive) with a full history.
// This lets Spirit reference past mission states in future Mem0 integration.
export interface MissionOverride {
  id:        string;
  directive: string;   // the raw directive text as written by Source
  active:    boolean;  // true = currently injected into system prompt
  createdAt: number;   // Unix ms
}
