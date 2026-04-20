"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import { useStream } from "@/hooks/useStream";
import { useThread } from "@/hooks/useThread";
import { useThreadCRUD } from "@/hooks/useThreadCRUD";
import { Paperclip, Send, Zap, Plus, Search, PanelLeft, X, ChevronRight } from "lucide-react";
import { MessageBubble } from "@/components/chat/MessageBubble";
import { SortableThreadItem } from "@/components/sidebar/SortableThreadItem";
import { ThreadDragOverlay } from "@/components/sidebar/ThreadDragOverlay";
import {
  DndContext,
  DragOverlay,
  PointerSensor,
  useSensor,
  useSensors,
  closestCenter,
  type DragStartEvent,
  type DragEndEvent,
  type DragOverEvent,
} from "@dnd-kit/core";
import {
  SortableContext,
  verticalListSortingStrategy,
  arrayMove,
} from "@dnd-kit/sortable";

import {
  db,
  seedDatabase,
  createThread,
  addMessage,
  touchThread,
  getSetting,
  setSetting,
  getCustomDirective,
  clearCustomDirective,
} from "@/lib/db";
import type { Folder, Thread, Message, SarcasmLevel } from "@/lib/db.types";

// ─── Utility ──────────────────────────────────────────────────────────────────

function cn(...classes: (string | undefined | false | null)[]) {
  return classes.filter(Boolean).join(" ");
}

// ── Meta-prompt detection regex ───────────────────────────────────────────────
// Matches: "Spirit, change your mission to X"
//          "Spirit, update your directive: X"
//          "Spirit, set your instructions to X"
// Case-insensitive. Captures the new directive text after "to" or ":".
const META_PROMPT_RE =
  /^spirit[,.]?\s+(change|update|set|rewrite)\s+your\s+(mission|directive|system\s*prompt|instructions?|persona)\s*(?:to|:)\s*([\s\S]+)/i;

// ─── Sarcasm config ───────────────────────────────────────────────────────────

const SARCASM_LEVELS: { id: SarcasmLevel; label: string }[] = [
  { id: "chill",    label: "Focus"  },
  { id: "peer",     label: "Mirror" },
  { id: "unhinged", label: "Chaos"  },
];

const SARCASM_ACTIVE: Record<SarcasmLevel, string> = {
  chill:    "border-zinc-600      bg-zinc-700/60    text-zinc-200",
  peer:     "border-violet-500/40 bg-violet-500/20  text-violet-300",
  unhinged: "border-red-500/40    bg-red-500/15     text-red-300",
};

// Mode-aware copy — changes the empty state and input placeholder to
// match the active persona. Makes the mode switch feel meaningful.
const MODE_EMPTY_STATE: Record<SarcasmLevel, string> = {
  chill:    "Ready to work. What are we solving?",
  peer:     "What's on your mind?",
  unhinged: "Go ahead. Make my day.",
};

const MODE_PLACEHOLDER: Record<SarcasmLevel, string> = {
  chill:    "What do you need to build, debug, or understand?",
  peer:     "Talk to me...",
  unhinged: "Say something I can work with...",
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
  onRename,
  onDelete,
  // DnD props — wired from the page-level DndContext
  activelyDraggingId,
  overFolderId,
  expandedFolders,
  onToggleFolder,
}: {
  folders:            Folder[];
  threads:            Thread[];
  activeId:           string;
  onSelect:           (id: string) => void;
  onNewChat:          () => void;
  onClose?:           () => void;
  onRename:           (id: string, newTitle: string) => Promise<void>;
  onDelete:           (id: string) => Promise<void>;
  activelyDraggingId: string | null;
  overFolderId:       string | null;
  expandedFolders:    Set<string>;
  onToggleFolder:     (id: string) => void;
}) {
  function toggleFolder(id: string) {
    onToggleFolder(id);
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
            // Visual drop target: highlight when a thread is being dragged over this folder
            const isDropTarget   = overFolderId === folder.id && activelyDraggingId !== null;

            return (
              <div key={folder.id}>
                {/* Folder header — acts as drop target via data-folder-id */}
                <button
                  type="button"
                  onClick={() => toggleFolder(folder.id)}
                  data-folder-id={folder.id}
                  className={cn(
                    "flex w-full cursor-pointer touch-manipulation items-center gap-2 rounded-xl px-3 py-2 transition-colors hover:bg-white/[0.04] active:bg-white/[0.06]",
                    hasActiveChild && !isOpen && "bg-white/[0.04]",
                    isDropTarget && "border border-violet-500/40 bg-violet-500/[0.08]",
                  )}
                >
                  <span className={cn("h-2 w-2 flex-shrink-0 rounded-sm", folder.accent)} />
                  <span className={cn(
                    "flex-1 truncate text-[12px] font-medium transition-colors",
                    hasActiveChild ? "text-zinc-200" : "text-zinc-500",
                    isDropTarget && "text-violet-300",
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
                    <SortableContext
                      items={folderThreads.map((t) => t.id)}
                      strategy={verticalListSortingStrategy}
                    >
                      {folderThreads.map((thread) => (
                        <SortableThreadItem
                          key={thread.id}
                          thread={thread}
                          active={activeId === thread.id}
                          onSelect={selectThread}
                          onRename={onRename}
                          onDelete={onDelete}
                        />
                      ))}
                    </SortableContext>
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
            <SortableContext
              items={uncategorized.map((t) => t.id)}
              strategy={verticalListSortingStrategy}
            >
              {uncategorized.map((thread) => (
                <SortableThreadItem
                  key={thread.id}
                  thread={thread}
                  active={activeId === thread.id}
                  onSelect={selectThread}
                  onRename={onRename}
                  onDelete={onDelete}
                />
              ))}
            </SortableContext>
          </div>
        )}
      </div>

      {/* ── Footer ── */}
      <div className="flex-shrink-0 border-t border-white/5 px-4 py-3">
        <p className="font-mono text-[10px] text-zinc-700">Spirit OS · v0.2</p>
        <p className="mt-0.5 font-mono text-[10px] text-zinc-700">dolphin3 · Ollama</p>
      </div>
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function SovereignChatPage() {
  const [activeThreadId,    setActiveThreadId]  = useState<string>(() => `new-${Date.now()}`);
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

  // Stores the autoTitle args from send() so onComplete can fire it AFTER
  // the main stream finishes — not before — preventing Ollama slot contention.
  const autoTitlePendingRef = useRef<{ threadId: string; text: string } | null>(null);

  // Cache of the active custom directive — read from Dexie once per send()
  // and passed to the API. Cached in a ref so we don't block send() with
  // an async Dexie read on the hot path; it's refreshed on each send.
  const customDirectiveRef = useRef<string | null>(null);

  // ── Thread + message data (useThread hook) ────────────────────────────────
  // Placed before useStream so autoTitle is available to onComplete.
  const {
    folders,
    threads,
    messages,
    messagesLoading,
    autoTitle,
  } = useThread(activeThreadId);

  // ── useStream ─────────────────────────────────────────────────────────────
  const { streamingText, isStreaming, error: streamError, startStream } = useStream({
    onError: useCallback(() => {
      // Stream failed before any assistant text was persisted — clear the
      // "streaming" placeholder id so `thinking` unlocks and the user can retry.
      setStreamingMsgId(null);
      autoTitlePendingRef.current = null;
    }, []),
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

      // ── Fire autoTitle AFTER the main stream completes ─────────────────
      // autoTitle makes a second Ollama call. Firing it here (not in send())
      // means it runs sequentially, never competing for the inference slot.
      const pending = autoTitlePendingRef.current;
      if (pending) {
        autoTitlePendingRef.current = null;
        autoTitle(pending.threadId, pending.text);
      }
    }, [autoTitle]),
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

  // ── CRUD operations ───────────────────────────────────────────────────────
  const { renameThread, deleteThread, editMessage } = useThreadCRUD();

  // Tracks which message id is currently open for inline editing.
  // null = no message is being edited.
  const [editingMessageId, setEditingMessageId] = useState<string | null>(null);

  // Folder expand state lifted here so the DnD hover-expand timer can open
  // folders programmatically during a drag operation.
  const [expandedFolders, setExpandedFoldersGlobal] = useState<Set<string>>(
    () => new Set(["f1"]),
  );

  const handleToggleFolder = useCallback((id: string) => {
    setExpandedFoldersGlobal((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }, []);

  // ── Delete handler (switches active thread if needed) ─────────────────────
  const handleDeleteThread = useCallback(async (id: string) => {
    const nextId = await deleteThread(id, threads ?? []);
    if (id === activeThreadId) {
      if (nextId) {
        setActiveThreadId(nextId);
      } else {
        setActiveThreadId(`new-${Date.now()}`);
      }
    }
  }, [deleteThread, threads, activeThreadId]);

  // ── Drag-and-Drop state ────────────────────────────────────────────────────
  // activelyDraggingId — the thread.id being dragged right now (null = idle)
  // overFolderId       — the folder.id the ghost is hovering over (null = none)
  const [activelyDraggingId, setActivelyDraggingId] = useState<string | null>(null);
  const [overFolderId, setOverFolderId] = useState<string | null>(null);

  // Ref to the hover-expand timer so we can cancel it on drag leave.
  const folderExpandTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // The Thread object for the item being dragged — fed to DragOverlay.
  const draggingThread = activelyDraggingId
    ? (threads ?? []).find((t) => t.id === activelyDraggingId) ?? null
    : null;

  // Configure sensors: PointerSensor with a 5px activation distance so
  // normal clicks on ThreadItem don't accidentally start a drag.
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 5 },
    }),
  );

  // ── onDragStart ──────────────────────────────────────────────────────────
  const handleDragStart = useCallback((event: DragStartEvent) => {
    setActivelyDraggingId(event.active.id as string);
  }, []);

  // ── onDragOver ───────────────────────────────────────────────────────────
  // Detects when the drag ghost moves over a folder header (via data-folder-id).
  // Uses a 300ms hover-expand timer — the folder opens if the ghost lingers,
  // letting the user drop the thread inside a collapsed folder.
  const handleDragOver = useCallback((event: DragOverEvent) => {
    // Walk up the DOM from the pointer target to find a [data-folder-id] element.
    const target = event.activatorEvent?.target as HTMLElement | null;
    let el: HTMLElement | null = target;
    let foundFolderId: string | null = null;

    while (el) {
      const fid = el.getAttribute?.("data-folder-id");
      if (fid) { foundFolderId = fid; break; }
      el = el.parentElement;
    }

    if (foundFolderId !== overFolderId) {
      // Clear any pending expand timer from a previous folder.
      if (folderExpandTimerRef.current) {
        clearTimeout(folderExpandTimerRef.current);
        folderExpandTimerRef.current = null;
      }
      setOverFolderId(foundFolderId);

      // Schedule folder auto-expand after 300ms of hovering.
      if (foundFolderId) {
        folderExpandTimerRef.current = setTimeout(() => {
          setExpandedFoldersGlobal((prev) => {
            const next = new Set(prev);
            next.add(foundFolderId!);
            return next;
          });
        }, 300);
      }
    }
  }, [overFolderId]);

  // ── onDragEnd ────────────────────────────────────────────────────────────
  const handleDragEnd = useCallback(async (event: DragEndEvent) => {
    const { active, over } = event;

    // Clear all drag state.
    if (folderExpandTimerRef.current) {
      clearTimeout(folderExpandTimerRef.current);
      folderExpandTimerRef.current = null;
    }
    setActivelyDraggingId(null);
    setOverFolderId(null);

    if (!active || !over) return;

    const draggedId = active.id as string;
    const overId    = over.id as string;
    if (draggedId === overId) return;

    const allThreads = threads ?? [];
    const draggedThread = allThreads.find((t) => t.id === draggedId);
    if (!draggedThread) return;

    // Case 1: dropped onto a folder header (overId is a folder id).
    const isFolder = (folders ?? []).some((f) => f.id === overId);
    if (isFolder) {
      // Move thread into this folder and set order to end of folder.
      const folderThreads = allThreads.filter((t) => t.folderId === overId);
      const newOrder = folderThreads.length;
      await db.threads.update(draggedId, { folderId: overId, order: newOrder });
      return;
    }

    // Case 2: dropped onto another thread — reorder within the same list.
    const overThread = allThreads.find((t) => t.id === overId);
    if (!overThread) return;

    // Only reorder within the same folderId scope.
    if (draggedThread.folderId !== overThread.folderId) {
      // Cross-scope drop: move to the over thread's folder at its position.
      await db.threads.update(draggedId, {
        folderId: overThread.folderId,
        order: overThread.order ?? 0,
      });
      return;
    }

    // Same-scope reorder: use arrayMove to compute the new order array
    // then batch-update all affected thread order values.
    const scopeThreads = allThreads
      .filter((t) => t.folderId === draggedThread.folderId)
      .sort((a, b) => (a.order ?? 0) - (b.order ?? 0));

    const oldIndex = scopeThreads.findIndex((t) => t.id === draggedId);
    const newIndex = scopeThreads.findIndex((t) => t.id === overId);
    if (oldIndex === -1 || newIndex === -1) return;

    const reordered = arrayMove(scopeThreads, oldIndex, newIndex);

    // Batch write: update order for each thread that moved.
    await Promise.all(
      reordered.map((t, i) =>
        t.order !== i ? db.threads.update(t.id, { order: i }) : Promise.resolve(),
      ),
    );
  }, [threads, folders]);

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
  const send = useCallback(async () => {
    const text = input.trim();
    if (!text || thinking) return;

    setInput("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";

    // ── Meta-prompt intercept ──────────────────────────────────────────────
    // Check if Source is issuing a directive change before touching the DB
    // or firing any API call. This is handled entirely locally — no Ollama
    // call needed, no stream started.
    const metaMatch = META_PROMPT_RE.exec(text);
    if (metaMatch) {
      const newDirective = metaMatch[3].trim();

      // Persist to Dexie settings.
      await setSetting("customDirective", newDirective);
      customDirectiveRef.current = newDirective;

      // Ensure a thread exists so the confirmation message has somewhere to live.
      let threadId = activeThreadId;
      const existingThread = await db.threads.get(threadId);
      if (!existingThread) {
        const newThread = await createThread(null, text);
        threadId = newThread.id;
        setActiveThreadId(threadId);
        activeThreadIdRef.current = threadId;
      }

      // Persist the user's directive message.
      await addMessage(threadId, "user", text);
      await touchThread(threadId, text);

      // Inject a synthetic Spirit confirmation — no API call needed.
      const confirmationText =
        `Directive updated. From now on: "${newDirective}"\n\n` +
        `This is saved to your local DB and will persist across sessions. ` +
        `To clear it, say "Spirit, clear your directive".`;
      await addMessage(threadId, "spirit", confirmationText);
      await touchThread(threadId, confirmationText);
      return;
    }

    // ── Directive clear intercept ──────────────────────────────────────────
    if (/^spirit[,.]?\s+clear\s+your\s+(directive|mission|instructions?)/i.test(text)) {
      await clearCustomDirective();
      customDirectiveRef.current = null;

      let threadId = activeThreadId;
      const existingThread = await db.threads.get(threadId);
      if (!existingThread) {
        const newThread = await createThread(null, text);
        threadId = newThread.id;
        setActiveThreadId(threadId);
        activeThreadIdRef.current = threadId;
      }

      await addMessage(threadId, "user", text);
      await touchThread(threadId, text);
      await addMessage(threadId, "spirit", "Directive cleared. Back to factory defaults.");
      await touchThread(threadId, "Directive cleared. Back to factory defaults.");
      return;
    }

    // ── Normal send flow ───────────────────────────────────────────────────
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

    // Refresh the custom directive from Dexie on every send.
    // Cheap read — settings table is tiny. Ensures the directive is always
    // current even if it was changed in another tab or session.
    customDirectiveRef.current = await getCustomDirective();

    // Queue autoTitle to fire AFTER the stream completes (via onComplete).
    autoTitlePendingRef.current = { threadId, text };

    // Kick off the stream. userContext will be added in Step C.
    setStreamingMsgId("streaming");
    startStream(text, sarcasm, undefined, customDirectiveRef.current ?? undefined);
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
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragStart={handleDragStart}
      onDragOver={handleDragOver}
      onDragEnd={(e) => { void handleDragEnd(e); }}
    >
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
          onRename={renameThread}
          onDelete={handleDeleteThread}
          activelyDraggingId={activelyDraggingId}
          overFolderId={overFolderId}
          expandedFolders={expandedFolders}
          onToggleFolder={handleToggleFolder}
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

          {/* Mode toggle */}
          <div className="flex items-center gap-1.5">
            <span className="mr-1 hidden text-[10px] font-semibold uppercase tracking-widest text-zinc-600 sm:block">
              Mode
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

            {!messagesLoading && (messages?.length ?? 0) === 0 && !thinking && (
              <div className="flex flex-col items-center justify-center gap-3 py-20 text-center">
                <div className="flex h-10 w-10 items-center justify-center rounded-full border border-violet-500/20 bg-violet-500/10">
                  <Zap size={16} className="text-violet-400" />
                </div>
                <p className="text-sm font-medium text-zinc-500">{MODE_EMPTY_STATE[sarcasm]}</p>
              </div>
            )}

            {(messages ?? []).map((msg: Message) => (
              <MessageBubble
                key={msg.id}
                mode="complete"
                message={msg}
                isEditing={editingMessageId === msg.id}
                onStartEdit={msg.role === "spirit"
                  ? () => setEditingMessageId(msg.id)
                  : undefined}
                onSaveEdit={async (newText) => {
                  await editMessage(msg.id, newText);
                  setEditingMessageId(null);
                }}
                onCancelEdit={() => setEditingMessageId(null)}
              />
            ))}

            {/* ── Streaming bubble (live tokens) ── */}
            {isStreaming && (
              <MessageBubble mode="streaming" text={streamingText} />
            )}

            {streamError && !isStreaming && (
              <div
                role="alert"
                className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 font-mono text-sm leading-relaxed text-red-300"
              >
                {streamError.message}
              </div>
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
                placeholder={MODE_PLACEHOLDER[sarcasm]}
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
              Spirit OS · dolphin3 · XTTS v2 · Mode:{" "}
              <span className={
                sarcasm === "chill"
                  ? "text-zinc-400"
                  : sarcasm === "peer"
                  ? "text-violet-500"
                  : "text-red-500"
              }>
                {SARCASM_LEVELS.find((l) => l.id === sarcasm)?.label ?? sarcasm}
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
              onRename={renameThread}
              onDelete={handleDeleteThread}
              activelyDraggingId={activelyDraggingId}
              overFolderId={overFolderId}
              expandedFolders={expandedFolders}
              onToggleFolder={handleToggleFolder}
            />
          </aside>
        </>
      )}
    </div>

      {/* ── DragOverlay: ghost card that floats under the cursor ── */}
      <DragOverlay dropAnimation={{ duration: 150, easing: "ease" }}>
        {draggingThread ? (
          <ThreadDragOverlay thread={draggingThread} />
        ) : null}
      </DragOverlay>
    </DndContext>
  );
}
