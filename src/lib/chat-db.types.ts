// ── chat-db.types - Dexie chat workspace (threads + folders, Prompt 5) ───────────
// > folderId / order are optional on older rows - v2 migration is additive only.

import type { ModelProfileId } from "@/lib/spirit/model-profile.types";
import type { SpiritRuntimeSurface } from "@/lib/spirit/spirit-runtime-surface";

/** Reserved for threaded system prompts if we ever hydrate them locally. */
export type ChatRole = "user" | "assistant" | "system";

export type ChatFolder = {
  id: string;
  name: string;
  createdAt: number;
  updatedAt: number;
  order: number;
  collapsed?: boolean;
};

export type ChatThread = {
  id: string;
  title: string;
  createdAt: number;
  updatedAt: number;
  archived?: boolean;
  /** null / undefined ⇒ root “Chats” bucket */
  folderId?: string | null;
  /** Optional sort key within a folder; falls back to updatedAt in UI */
  order?: number;
  /** Prompt 7 - persona preset; missing ⇒ normal-peer id at runtime (UI label: Peer) */
  modelProfileId?: ModelProfileId;
  pinned?: boolean;
  pinnedAt?: number;
};

export type ChatMessage = {
  id: string;
  threadId: string;
  role: ChatRole;
  text: string;
  createdAt: number;
  updatedAt?: number;
};

export type NewChatThreadInput = {
  title?: string;
  archived?: boolean;
  folderId?: string | null;
  order?: number;
  modelProfileId?: ModelProfileId;
};

export type NewChatMessageInput = {
  /** When set, aligns Dexie row id with AI SDK UIMessage id (Prompt 3 hydration). */
  id?: string;
  threadId: string;
  role: ChatRole;
  text: string;
};

/** Oracle voice session memory event - persisted only when NEXT_PUBLIC_SPIRIT_ENABLE_ORACLE_MEMORY=true. */
export type OracleMemoryEvent = {
  id: string;
  createdAt: number;
  /** Short summary of the exchange (≤120 chars) - used in the prompt context block. */
  summary: string;
  /** Trimmed user text that triggered this exchange (≤500 chars). */
  userText?: string;
  /** Trimmed first-pass assistant reply (≤500 chars). */
  assistantText?: string;
  /** Profile active during this exchange. */
  modelProfileId?: string;
  /** Where this row was captured (Dexie is local; this disambiguates future writers). */
  source?: string;
  /** Runtime surface active when the exchange was logged (matches /api/spirit body). */
  runtimeSurface?: SpiritRuntimeSurface;
};
