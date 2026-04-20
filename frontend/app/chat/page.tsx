"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useStream } from "@/hooks/useStream";
import { useLiveQuery } from "dexie-react-hooks";
import { Paperclip, Send, Zap, Plus, Search, PanelLeft, X, ChevronRight } from "lucide-react";
import { MessageBubble } from "@/components/chat/MessageBubble";

import {
  db,
  seedDatabase,
  createThread,
  addMessage,
  touchThread,
  getSetting,
  setSetting,
} from "@/lib/db";
import type { Folder, Thread, Message, SarcasmLevel } from "@/lib/db.types";

// ─── Utility ──────────────────────────────────────────────────────────────────

function cn(...classes: (string | undefined | false | null)[]) {
  return classes.filter(Boolean).join(" ");
}

// ─── Sarcasm config ───────────────────────────────────────────────────────────

const SARCASM_LEVELS: { id: SarcasmLevel; label: string }[] = [
  { id: "chill",    label: "Chill"    },
  { id: "peer",     label: "Peer"     },
  { id: "unhinged", label: "Unhinged" },
];

const SARCASM_ACTIVE: Record<SarcasmLevel, string> = {
  chill:    "border-zinc-600    bg-zinc-700/60   text-zinc-200",
  peer:     "border-violet-500/40 bg-violet-500/20 text-violet-300",
  unhinged: "border-red-500/40   bg-red-500/15    text-red-300",
};

// ─── Conversation Sidebar ─────────────────────────────────────────────────────
//
// Consumes live Dexie queries passed in as props so the sidebar never owns its
// own async state — data flows down from the page, making re-renders cheap.
//
function ConversationSidebar({
  folders,
  threads,
  activeId,
  onSelect,
  onNewChat,
  onClose,
}: {
  folders:    Folder[];
  threads:    Thread[];
  activeId:   string;
  onSelect:   (id: string) => void;
  onNewChat:  () => void;
  onClose?:   () => void;
}) {
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(
    () => new Set(["f1"]),
  );

  function toggleFolder(id: string) {
    setExpandedFolders((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function selectThread(id: string) {
    onSelect(id);
    onClose?.();
  }

  const uncategorized = threads.filter((t) => t.folderId === null);

  return (
    <div className="flex h-full flex-col">

      {/* ── Header ── */}
      <div className="flex flex-shrink-0 items-center justify-between px-4 pb-2 pt-4">
        <div className="flex items-center gap-2">
          <div className="flex h-5 w-5 items-center justify-center rounded-md border border-violet-500/30 bg-violet-500/15">
            <Zap size={10} className="text-violet-400" aria-hidden />
          </div>
          <span className="text-[11px] font-semibold tracking-tight text-zinc-400">Spirit OS</span>
        </div>
        {onClose && (
          <button
            type="button"
            onClick={onClose}
            aria-label="Close sidebar"
            className="flex h-7 w-7 cursor-pointer touch-manipulation items-center justify-center rounded-lg text-zinc-600 transition-colors hover:text-zinc-300"
          >
            <X size={14} className="pointer-events-none" aria-hidden />
          </button>
        )}
      </div>

      {/* ── New Sovereign Chat CTA ── */}
      <div className="flex-shrink-0 px-3 pb-3">
        <button
          type="button"
          onClick={onNewChat}
          className="group flex w-full cursor-pointer touch-manipulation items-center gap-2.5 rounded-xl border border-white/[0.07] bg-white/[0.04] px-3 py-2.5 text-left transition-all hover:border-violet-500/25 hover:bg-violet-500/[0.07]"
        >
          <div className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-lg border border-violet-500/30 bg-violet-500/15 transition-colors group-hover:border-violet-500/50 group-hover:bg-violet-500/25">
            <Plus size={12} className="pointer-events-none text-violet-400" aria-hidden />
          </div>
          <span className="text-[12px] font-semibold text-zinc-400 transition-colors group-hover:text-zinc-100">
            New Sovereign Chat
          </span>
        </button>
      </div>

      {/* ── Search ── */}
      <div className="flex-shrink-0 border-t border-white/[0.05] px-3 py-2.5">
        <div className="flex items-center gap-2 rounded-xl border border-white/5 bg-white/[0.03] px-3 py-2">
          <Search size={12} className="flex-shrink-0 text-zinc-700" aria-hidden />
          <input
            placeholder="Search workspace..."
            className="min-w-0 flex-1 bg-transparent text-[11px] text-zinc-400 outline-none placeholder:text-zinc-700"
            readOnly
          />
        </div>
      </div>

      {/* ── Scrollable list ── */}
      <div className="flex-1 overflow-y-auto px-2 pb-4">

        {/* ── FOLDERS ──────────────────────────────────────────────────────── */}
        <div className="mb-4 mt-1">
          <div className="mb-1 flex items-center justify-between px-2">
            <span className="text-[9px] font-semibold uppercase tracking-widest text-zinc-700">
              Folders
            </span>
            <button
              type="button"
              title="New folder"
              className="flex h-4 w-4 cursor-pointer items-center justify-center rounded text-zinc-700 transition-colors hover:text-zinc-500"
            >
              <Plus size={10} className="pointer-events-none" aria-hidden />
            </button>
          </div>

          {folders.map((folder) => {
            const isOpen         = expandedFolders.has(folder.id);
            const folderThreads  = threads.filter((t) => t.folderId === folder.id);
            const hasActiveChild = folderThreads.some((t) => t.id === activeId);

            return (
              <div key={folder.id}>
                <button
                  type="button"
                  onClick={() => toggleFolder(folder.id)}
                  className={cn(
                    "flex w-full cursor-pointer touch-manipulation items-center gap-2 rounded-xl px-3 py-2 transition-colors hover:bg-white/[0.04] active:bg-white/[0.06]",
                    hasActiveChild && !isOpen && "bg-white/[0.04]",
                  )}
                >
                  <span className={cn("h-2 w-2 flex-shrink-0 rounded-sm", folder.accent)} />
                  <span className={cn(
                    "flex-1 truncate text-[12px] font-medium transition-colors",
                    hasActiveChild ? "text-zinc-200" : "text-zinc-500",
                  )}>
                    {folder.name}
                  </span>
                  <span className="flex-shrink-0 tabular-nums text-[10px] text-zinc-700">
                    {folderThreads.length}
                  </span>
                  <ChevronRight
                    size={12}
                    className={cn(
                      "flex-shrink-0 text-zinc-700 transition-transform duration-150",
                      isOpen && "rotate-90",
                    )}
                    aria-hidden
                  />
                </button>

                {isOpen && (
                  <div className="mb-1 ml-[22px] border-l border-white/[0.06]">
                    {folderThreads.map((thread) => {
                      const active = activeId === thread.id;
                      return (
                        <button
                          key={thread.id}
                          type="button"
                          onClick={() => selectThread(thread.id)}
                          className={cn(
                            "relative w-full rounded-xl py-2 pl-3 pr-2 text-left touch-manipulation transition-colors",
                            active ? "bg-white/[0.08]" : "hover:bg-white/[0.04] active:bg-white/[0.06]",
                          )}
                        >
                          {active && (
                            <span className="absolute left-0 top-1/2 h-4 w-0.5 -translate-y-1/2 rounded-full bg-violet-500/70" />
                          )}
                          <div className="flex items-baseline justify-between gap-2">
                            <p className={cn(
                              "truncate text-[11px] font-medium leading-snug",
                              active ? "text-zinc-100" : "text-zinc-500",
                            )}>
                              {thread.title}
                            </p>
                            <span className="flex-shrink-0 text-[10px] text-zinc-700">
                              {new Date(thread.updatedAt).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false })}
                            </span>
                          </div>
                        </button>
                      );
                    })}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* ── THREADS (uncategorized) ───────────────────────────────────────── */}
        {uncategorized.length > 0 && (
          <div>
            <p className="mb-1 px-2 text-[9px] font-semibold uppercase tracking-widest text-zinc-700">
              Threads
            </p>
            {uncategorized.map((thread) => {
              const active = activeId === thread.id;
              return (
                <button
                  key={thread.id}
                  type="button"
                  onClick={() => selectThread(thread.id)}
                  className={cn(
                    "relative w-full rounded-xl px-3 py-2.5 text-left touch-manipulation transition-colors",
                    active ? "bg-white/[0.08]" : "hover:bg-white/[0.04] active:bg-white/[0.06]",
                  )}
                >
                  {active && (
                    <span className="absolute left-0 top-1/2 h-5 w-0.5 -translate-y-1/2 rounded-full bg-violet-500/70" />
                  )}
                  <div className="flex items-start justify-between gap-2">
                    <p className={cn(
                      "truncate text-[12px] font-medium leading-snug",
                      active ? "text-zinc-100" : "text-zinc-400",
                    )}>
                      {thread.title}
                    </p>
                    <span className="mt-px flex-shrink-0 text-[10px] text-zinc-700">
                      {new Date(thread.updatedAt).toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false })}
                    </span>
                  </div>
                  <p className="mt-0.5 truncate text-[11px] text-zinc-600">{thread.preview}</p>
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* ── Footer ── */}
      <div className="flex-shrink-0 border-t border-white/5 px-4 py-3">
        <p className="font-mono text-[10px] text-zinc-700">Spirit · Workspace v1</p>
        <p className="mt-0.5 font-mono text-[10px] text-zinc-700">dolphin3 · Ollama</p>
      </div>
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function SovereignChatPage() {
  const [activeThreadId,    setActiveThreadId]  = useState<string>("t13");
  const [input,             setInput]           = useState("");
  const [sarcasm,           setSarcasm]         = useState<SarcasmLevel>("peer");
  const [mobileSidebarOpen, setMobileOpen]      = useState(false);
  const [seeded,            setSeeded]          = useState(false);
  // Holds the Dexie message id of the assistant bubble currently streaming.
  // null when idle. Used to swap the streaming placeholder for persisted text.
  const [streamingMsgId,    setStreamingMsgId]  = useState<string | null>(null);

  // Capture activeThreadId in a ref so the onComplete closure always sees the
  // current value even though it's created inside useStream (stale closure trap).
  const activeThreadIdRef = useRef(activeThreadId);
  useEffect(() => { activeThreadIdRef.current = activeThreadId; }, [activeThreadId]);

  // ── useStream ─────────────────────────────────────────────────────────────
  const { streamingText, isStreaming, startStream } = useStream({
    onComplete: useCallback(async (fullText: string) => {
      const threadId = activeThreadIdRef.current;
      try {
        const saved = await addMessage(threadId, "spirit", fullText);
        await touchThread(threadId, fullText);
        setStreamingMsgId(null);
        // Scroll after the persisted bubble replaces the streaming one.
        requestAnimationFrame(() => {
          bottomRef.current?.scrollIntoView({ behavior: "smooth" });
        });
        void saved; // suppress unused-var lint
      } catch (e) {
        console.error("[Spirit OS] Failed to persist assistant message:", e);
      }
    }, []), // stable — reads threadId via ref, not closure
  });

  // Derived: are we in any kind of "busy" state?
  const thinking = isStreaming || streamingMsgId !== null;

  const bottomRef   = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // ── Seed on first mount ────────────────────────────────────────────────────
  useEffect(() => {
    seedDatabase().then(() => setSeeded(true)).catch(console.error);
  }, []);

  // ── Load persisted sarcasm setting ────────────────────────────────────────
  useEffect(() => {
    getSetting<SarcasmLevel>("sarcasm", "peer").then(setSarcasm).catch(console.error);
  }, []);

  // ── Live queries ──────────────────────────────────────────────────────────
  // useLiveQuery re-renders the component automatically whenever the queried
  // Dexie table changes — inserts, updates, and deletes all trigger a re-render.

  const folders  = useLiveQuery(() => db.folders.orderBy("order").toArray(), []);
  const threads  = useLiveQuery(() => db.threads.orderBy("updatedAt").reverse().toArray(), []);
  const messages = useLiveQuery(
    () => db.messages.where("threadId").equals(activeThreadId).sortBy("createdAt"),
    [activeThreadId],
  );

  // ── Auto-scroll ────────────────────────────────────────────────────────────
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, thinking]);

  // ── Dev reminder ──────────────────────────────────────────────────────────
  useEffect(() => {
    if (process.env.NODE_ENV === "development") {
      console.info(
        "%c[Spirit OS · Dev Reminder]%c\n" +
        "• Serving to LAN?  →  npx next dev -H 0.0.0.0\n" +
        "• CSS stale on iOS?  →  rm -rf .next && npx next dev -H 0.0.0.0",
        "color:#a78bfa;font-weight:bold",
        "color:#a1a1aa",
      );
    }
  }, []);

  // ── Textarea auto-resize ──────────────────────────────────────────────────
  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    const ta = e.target;
    ta.style.height = "auto";
    ta.style.height = `${Math.min(ta.scrollHeight, 160)}px`;
  };

  // ── Sarcasm toggle (persists to Dexie) ────────────────────────────────────
  const handleSarcasmChange = useCallback((level: SarcasmLevel) => {
    setSarcasm(level);
    setSetting("sarcasm", level).catch(console.error);
  }, []);

  // ── Send ──────────────────────────────────────────────────────────────────
  // ── Send ──────────────────────────────────────────────────────────────────
  const send = useCallback(async () => {
    const text = input.trim();
    if (!text || thinking) return;

    setInput("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";

    let threadId = activeThreadId;

    // Create the DB thread record on first send (never persist empty threads).
    const existingThread = await db.threads.get(threadId);
    if (!existingThread) {
      const newThread = await createThread(null, text);
      threadId = newThread.id;
      setActiveThreadId(threadId);
      activeThreadIdRef.current = threadId;
    }

    // Persist the user message immediately so it appears in the live query.
    await addMessage(threadId, "user", text);
    await touchThread(threadId, text);

    // Kick off the stream. useStream's onComplete callback handles the
    // Dexie write for the assistant message when the stream finishes.
    setStreamingMsgId("streaming");
    startStream(text, sarcasm);
  }, [input, thinking, activeThreadId, sarcasm, startStream]);

  // ── New Chat ──────────────────────────────────────────────────────────────
  // Creates a placeholder threadId. The actual DB record is created on first send
  // so empty threads are never persisted (mirrors LobeChat / Open-WebUI pattern).
  const handleNewChat = useCallback(() => {
    setActiveThreadId(`new-${Date.now()}`);
    setMobileOpen(false);
  }, []);

  // Wait for seed to complete before rendering live data to avoid a flash of
  // empty UI. The seed is fast (IndexedDB bulk write) so this is imperceptible.
  if (!seeded) {
    return (
      <div className="flex h-[calc(100dvh-60px)] items-center justify-center bg-zinc-950 md:h-[100dvh]">
        <div className="h-5 w-5 animate-spin rounded-full border-2 border-violet-500/30 border-t-violet-500" />
      </div>
    );
  }

  return (
    <div className="relative flex h-[calc(100dvh-60px)] flex-row bg-zinc-950 md:h-[100dvh]">

      {/* ── Desktop Sidebar ────────────────────────────────────────────────── */}
      <aside
        className="hidden md:flex md:w-64 md:flex-shrink-0 md:flex-col border-r border-white/5"
        style={{ background: "#09090b" }}
      >
        <ConversationSidebar
          folders={folders ?? []}
          threads={threads ?? []}
          activeId={activeThreadId}
          onSelect={setActiveThreadId}
          onNewChat={handleNewChat}
        />
      </aside>

      {/* ── Chat Panel ─────────────────────────────────────────────────────── */}
      <div className="flex min-w-0 flex-1 flex-col">

        {/* ── Chat Header ── */}
        <header className="flex flex-shrink-0 items-center justify-between border-b border-white/[0.07] px-4 py-3">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setMobileOpen(true)}
              onTouchEnd={(e) => { e.preventDefault(); setMobileOpen(true); }}
              aria-label="Open conversations"
              className="flex h-9 w-9 cursor-pointer touch-manipulation items-center justify-center rounded-xl border border-white/[0.07] bg-white/5 text-zinc-500 transition-colors hover:text-zinc-300 md:hidden"
            >
              <PanelLeft size={15} className="pointer-events-none" aria-hidden />
            </button>

            <div className="flex items-center gap-2.5">
              <div className="relative flex h-7 w-7 flex-shrink-0 items-center justify-center rounded-full border border-violet-500/30 bg-violet-500/10">
                <Zap size={12} className="text-violet-400" />
                <span className="absolute -right-0.5 -top-0.5 flex h-2.5 w-2.5">
                  <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-60" />
                  <span className="relative inline-flex h-2.5 w-2.5 rounded-full border-2 border-zinc-950 bg-emerald-400" />
                </span>
              </div>
              <div className="min-w-0">
                <p className="truncate font-mono text-xs font-semibold leading-none text-zinc-100">
                  dolphin3
                </p>
                <p className="mt-0.5 text-[10px] font-semibold text-emerald-500">Online</p>
              </div>
            </div>
          </div>

          {/* Sarcasm toggle */}
          <div className="flex items-center gap-1.5">
            <span className="mr-1 hidden text-[10px] font-semibold uppercase tracking-widest text-zinc-600 sm:block">
              Sarcasm
            </span>
            {SARCASM_LEVELS.map(({ id, label }) => (
              <button
                key={id}
                type="button"
                onClick={() => handleSarcasmChange(id)}
                className={cn(
                  "rounded-lg border px-2.5 py-1 text-[11px] font-semibold touch-manipulation transition-colors",
                  sarcasm === id
                    ? SARCASM_ACTIVE[id]
                    : "border-white/[0.07] bg-transparent text-zinc-600 hover:text-zinc-400",
                )}
              >
                {label}
              </button>
            ))}
          </div>
        </header>

        {/* ── Message Arena ── */}
        <div className="min-w-0 flex-1 overflow-y-auto px-4 py-6">
          <div className="mx-auto flex max-w-3xl flex-col gap-6">

            {(messages?.length ?? 0) === 0 && !thinking && (
              <div className="flex flex-col items-center justify-center gap-3 py-20 text-center">
                <div className="flex h-10 w-10 items-center justify-center rounded-full border border-violet-500/20 bg-violet-500/10">
                  <Zap size={16} className="text-violet-400" />
                </div>
                <p className="text-sm font-medium text-zinc-500">Issue a directive, Source.</p>
              </div>
            )}

            {(messages ?? []).map((msg: Message) => (
              <MessageBubble key={msg.id} mode="complete" message={msg} />
            ))}

            {/* ── Streaming bubble (live tokens) ── */}
            {isStreaming && (
              <MessageBubble mode="streaming" text={streamingText} />
            )}

            <div ref={bottomRef} />
          </div>
        </div>

        {/* ── Input Bar ──────────────────────────────────────────────────────── */}
        <div
          className="flex-shrink-0 border-t border-white/[0.07] bg-zinc-950 px-4 pt-3"
          style={{ paddingBottom: "max(12px, env(safe-area-inset-bottom))" }}
        >
          <div className="mx-auto max-w-3xl">
            <div className="flex items-end gap-2 rounded-2xl border border-white/[0.07] bg-zinc-900 px-3 py-2.5">
              <button
                type="button"
                aria-label="Attach file"
                className="mb-0.5 flex h-8 w-8 flex-shrink-0 touch-manipulation items-center justify-center rounded-xl text-zinc-600 transition-colors hover:text-zinc-400 active:scale-95"
              >
                <Paperclip size={16} className="pointer-events-none" aria-hidden />
              </button>

              <textarea
                ref={textareaRef}
                value={input}
                onChange={handleTextareaChange}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); void send(); }
                }}
                placeholder="Issue a directive..."
                rows={1}
                className="min-h-[36px] flex-1 resize-none bg-transparent py-1 font-mono text-sm text-zinc-100 outline-none placeholder:text-zinc-700"
                style={{ maxHeight: "160px" }}
              />

              <button
                type="button"
                onClick={() => void send()}
                disabled={!input.trim() || thinking}
                aria-label="Send"
                className="mb-0.5 flex h-9 w-9 flex-shrink-0 cursor-pointer touch-manipulation items-center justify-center rounded-xl border border-violet-500/30 bg-violet-500/20 text-violet-300 transition-colors hover:bg-violet-500/30 disabled:opacity-30 active:scale-95"
              >
                <Send size={14} className="pointer-events-none" aria-hidden />
              </button>
            </div>

            <p className="mt-2 text-center font-mono text-[10px] text-zinc-700">
              Spirit · dolphin3 · XTTS v2 · Sarcasm:{" "}
              <span className={sarcasm === "chill" ? "text-zinc-500" : sarcasm === "peer" ? "text-violet-600" : "text-red-700"}>
                {sarcasm}
              </span>
            </p>
          </div>
        </div>
      </div>

      {/* ── Mobile Sidebar Overlay ──────────────────────────────────────────── */}
      {mobileSidebarOpen && (
        <>
          <div
            className="absolute inset-0 z-[490] bg-black/80 md:hidden"
            onClick={() => setMobileOpen(false)}
            onTouchEnd={(e) => { e.preventDefault(); setMobileOpen(false); }}
          />
          <aside
            className="absolute left-0 top-0 z-[491] flex h-full w-[280px] flex-col border-r border-white/5 md:hidden"
            style={{ background: "#09090b" }}
          >
            <ConversationSidebar
              folders={folders ?? []}
              threads={threads ?? []}
              activeId={activeThreadId}
              onSelect={setActiveThreadId}
              onNewChat={handleNewChat}
              onClose={() => setMobileOpen(false)}
            />
          </aside>
        </>
      )}
    </div>
  );
}
