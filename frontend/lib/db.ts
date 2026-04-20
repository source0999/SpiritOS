// ─── Spirit OS · Dexie Database ───────────────────────────────────────────────
//
// Browser-local IndexedDB via Dexie v4. All chat state — folders, threads,
// messages, and user settings — lives here. No server sync; fully sovereign.
//
// Schema versioning:
//   v1 — initial schema: folders, threads, messages, settings
//
// Usage:
//   import { db } from "@/lib/db";
//   const threads = await db.threads.where({ folderId: "f1" }).toArray();
//
// ─────────────────────────────────────────────────────────────────────────────

import Dexie, { type Table } from "dexie";
import type { Folder, Thread, Message, Setting } from "./db.types";

// ── UUID helper ───────────────────────────────────────────────────────────────
// crypto.randomUUID() is available in all modern browsers and in Node 18+.
// Falls back to a timestamp+random string if called in a context without
// crypto (e.g. Jest without jsdom).
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
  folders!:  Table<Folder,  string>;
  threads!:  Table<Thread,  string>;
  messages!: Table<Message, string>;
  settings!: Table<Setting, string>;

  constructor() {
    super("spirit-os");

    this.version(1).stores({
      // Indexed fields only — Dexie stores the full object regardless.
      // Primary key is listed first; compound/secondary indexes follow.
      folders:  "id, order, createdAt",
      threads:  "id, folderId, updatedAt, createdAt",
      messages: "id, threadId, createdAt",
      settings: "key",
    });
  }
}

// ── Singleton export ──────────────────────────────────────────────────────────
// One instance shared across the entire app. Dexie opens the connection lazily
// on first use; subsequent imports receive the same object.
export const db = new SpiritDB();

// ── Seed data ─────────────────────────────────────────────────────────────────
// Mirrors the mock arrays that were previously hardcoded in chat/page.tsx.
// The data is written exactly once — guarded by the "seeded" settings flag.
// Call `seedDatabase()` from a client component useEffect on first mount.

const SEED_FOLDERS: Omit<Folder, "createdAt">[] = [
  { id: "f1", name: "Homelab Configs",     accent: "bg-emerald-500", order: 0 },
  { id: "f2", name: "Prompt Engineering",  accent: "bg-violet-500",  order: 1 },
  { id: "f3", name: "Philosophy",          accent: "bg-amber-500",   order: 2 },
  { id: "f4", name: "System Architecture", accent: "bg-sky-500",     order: 3 },
];

const SEED_THREADS: Omit<Thread, "createdAt" | "updatedAt">[] = [
  // ── Homelab Configs ──────────────────────────────────────────────────────
  { id: "t1",  folderId: "f1", title: "Dell BIOS Above 4G Decoding",   preview: "MMIO window remap confirmed on X570."            },
  { id: "t2",  folderId: "f1", title: "Ghost Node DNS Hardening",       preview: "DoH config pushed to Pi successfully."           },
  { id: "t3",  folderId: "f1", title: "Tesla P40 PSU Mod Planning",     preview: "Server PSU → ATX adapter wattage math."          },
  { id: "t4",  folderId: "f1", title: "Proxmox VM Bridging Issue",      preview: "vmbr0 not forwarding on VLAN tag 20."            },
  // ── Prompt Engineering ───────────────────────────────────────────────────
  { id: "t5",  folderId: "f2", title: "Langfuse SQLite Integration",    preview: "Tracing pipeline wired to local SQLite."         },
  { id: "t6",  folderId: "f2", title: "RAG Pipeline Architecture",      preview: "Three retrieval strategies evaluated."           },
  { id: "t7",  folderId: "f2", title: "System Prompt Abliteration",     preview: "Abliterated Llama 3 benchmark vs base."          },
  { id: "t8",  folderId: "f2", title: "Context Window Benchmarks",      preview: "128k vs 32k — retrieval degradation rate."       },
  // ── Philosophy ───────────────────────────────────────────────────────────
  { id: "t9",  folderId: "f3", title: "Nietzsche vs Stoicism",          preview: "Amor fati as productive nihilism."               },
  { id: "t10", folderId: "f3", title: "Post-AGI Identity Crisis",       preview: "What does authorship mean after 2025?"           },
  // ── System Architecture ──────────────────────────────────────────────────
  { id: "t11", folderId: "f4", title: "Cinema Engine Config",           preview: "Plex transcoding is a crime against compute."    },
  { id: "t12", folderId: "f4", title: "Spirit OS Bento Grid",           preview: "The bento grid looks crispy, I suppose."        },
  // ── Uncategorized ────────────────────────────────────────────────────────
  { id: "t13", folderId: null, title: "Homelab Threat Assessment",      preview: "Running nmap passive fingerprint now..."         },
  { id: "t14", folderId: null, title: "Privacy Hardening Session",      preview: "CCPA compliance for homelab services."           },
  { id: "t15", folderId: null, title: "Local LLM Benchmark Run",        preview: "Llama 3.3 Q4_K_M on DDR5 — results."            },
];

// Seed messages for the default active thread (t13 — Homelab Threat Assessment)
// so the chat panel is not empty on first load.
const SEED_MESSAGES: Omit<Message, "createdAt">[] = [
  { id: "m1", threadId: "t13", role: "user",   text: "Run a full threat assessment on the homelab network.", ts: "06:14", audioUrl: null },
  { id: "m2", threadId: "t13", role: "spirit", text: "[sighs] Alright. Scanning the usual suspects on your subnet — you really need to rotate those credentials, by the way. Running nmap passive fingerprint now.", ts: "06:14", audioUrl: null },
  { id: "m3", threadId: "t13", role: "user",   text: "What's the verdict on the Ghost Node?", ts: "06:15", audioUrl: null },
  { id: "m4", threadId: "t13", role: "spirit", text: "[scoffs] The Pi 3 is running DNS over port 53 unencrypted. Cute. I'm also seeing an open port 22 with password auth enabled. [groan] This is fine, I guess, if you enjoy chaos.", ts: "06:15", audioUrl: null },
  { id: "m5", threadId: "t13", role: "user",   text: "Fix it.", ts: "06:16", audioUrl: null },
  { id: "m6", threadId: "t13", role: "spirit", text: "On it. Generating hardened sshd_config now. You're welcome. [exhales] I'll also push DoH config to the Pi. This will take approximately 40 seconds. Try not to break anything else while you wait.", ts: "06:16", audioUrl: null },
];

const DEFAULT_SETTINGS: Setting[] = [
  { key: "sarcasm",    value: JSON.stringify("peer")     },
  { key: "ttsEnabled", value: JSON.stringify(false)      },
  { key: "model",      value: JSON.stringify("dolphin3") },
];

export async function seedDatabase(): Promise<void> {
  // Guard: only seed once per browser profile.
  const alreadySeeded = await db.settings.get("seeded");
  if (alreadySeeded) return;

  const now = Date.now();

  // Use a transaction so the seed is atomic — either all tables are written
  // or none are (prevents a half-seeded state on tab crash mid-seed).
  await db.transaction("rw", db.folders, db.threads, db.messages, db.settings, async () => {
    await db.folders.bulkAdd(
      SEED_FOLDERS.map((f) => ({ ...f, createdAt: now })),
    );

    // Threads: newer threads (lower index) get a more recent updatedAt so they
    // sort to the top of the sidebar when sorted by updatedAt descending.
    await db.threads.bulkAdd(
      SEED_THREADS.map((t, i) => ({
        ...t,
        createdAt: now - i * 60_000,
        updatedAt: now - i * 60_000,
      })),
    );

    await db.messages.bulkAdd(
      SEED_MESSAGES.map((m) => ({ ...m, createdAt: now })),
    );

    await db.settings.bulkAdd(DEFAULT_SETTINGS);

    // Mark as seeded — this is the last write in the transaction.
    await db.settings.put({ key: "seeded", value: JSON.stringify(true) });
  });
}

// ── Thread helpers ────────────────────────────────────────────────────────────

export async function createThread(folderId: string | null, firstUserText: string): Promise<Thread> {
  const now    = Date.now();
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
  await db.threads.update(threadId, { preview: preview.slice(0, 60), updatedAt: Date.now() });
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
