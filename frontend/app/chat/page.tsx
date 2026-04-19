"use client";

import { useState, useRef, useEffect } from "react";
import { Paperclip, Send, Zap, Plus, Search, PanelLeft, X, ChevronRight } from "lucide-react";

// ─── Dev Network Reminder ────────────────────────────────────────────────────
//
// To test on a physical iOS device over LAN:
//   1.  npx next dev -H 0.0.0.0          (bind to all interfaces)
//   2.  Open http://<your-LAN-IP>:3000   (e.g. http://10.0.0.126:3000)
//   3.  If CSS looks stale, delete .next/ and restart the dev server:
//         rm -rf .next && npx next dev -H 0.0.0.0
//   4.  allowedDevOrigins in next.config.ts must include your device's IP.
//
// ─────────────────────────────────────────────────────────────────────────────

// ─── Utility ─────────────────────────────────────────────────────────────────

function cn(...classes: (string | undefined | false | null)[]) {
  return classes.filter(Boolean).join(" ");
}

// ─── Types ────────────────────────────────────────────────────────────────────

type Role = "user" | "spirit";
type SarcasmLevel = "chill" | "peer" | "unhinged";

interface Message {
  id: string;
  role: Role;
  text: string;
  ts: string;
}

// A workspace folder that groups related threads by topic.
interface Folder {
  id: string;
  name: string;
  // Tailwind bg class for the color dot — set at the data level so the
  // compiler sees the full class string and keeps it in the purge-safe bundle.
  accent: string;
}

// A single conversation thread, optionally nested inside a Folder.
// folderId === null → the thread is uncategorized and floats in "Threads".
interface Thread {
  id: string;
  folderId: string | null;
  title: string;
  preview: string;
  ts: string;
}

// ─── Acoustic Marker Parser ───────────────────────────────────────────────────
//
// Parses XTTS v2 stage directions like [sighs], [scoffs], [groan] and renders
// them in italic violet so they visually separate from the monospace body text.
//
function parseAcousticMarkers(text: string): (string | JSX.Element)[] {
  const parts = text.split(/(\[[^\]]+\])/g);
  return parts.map((part, i) => {
    if (/^\[[^\]]+\]$/.test(part)) {
      return (
        <span key={i} className="italic text-violet-500/70">
          {part}
        </span>
      );
    }
    return part;
  });
}

// ─── Mock Data ────────────────────────────────────────────────────────────────

const INITIAL_MESSAGES: Message[] = [
  { id: "1", role: "user",   text: "Run a full threat assessment on the homelab network.", ts: "06:14" },
  { id: "2", role: "spirit", text: "[sighs] Alright. Scanning the usual suspects on your subnet — you really need to rotate those credentials, by the way. Running nmap passive fingerprint now.", ts: "06:14" },
  { id: "3", role: "user",   text: "What's the verdict on the Ghost Node?", ts: "06:15" },
  { id: "4", role: "spirit", text: "[scoffs] The Pi 3 is running DNS over port 53 unencrypted. Cute. I'm also seeing an open port 22 with password auth enabled. [groan] This is fine, I guess, if you enjoy chaos.", ts: "06:15" },
  { id: "5", role: "user",   text: "Fix it.", ts: "06:16" },
  { id: "6", role: "spirit", text: "On it. Generating hardened sshd_config now. You're welcome. [exhales] I'll also push DoH config to the Pi. This will take approximately 40 seconds. Try not to break anything else while you wait.", ts: "06:16" },
];

// ─── Workspace Folders ───────────────────────────────────────────────────────

const MOCK_FOLDERS: Folder[] = [
  { id: "f1", name: "Homelab Configs",     accent: "bg-emerald-500" },
  { id: "f2", name: "Prompt Engineering",  accent: "bg-violet-500"  },
  { id: "f3", name: "Philosophy",          accent: "bg-amber-500"   },
  { id: "f4", name: "System Architecture", accent: "bg-sky-500"     },
];

// ─── Workspace Threads ────────────────────────────────────────────────────────
//
// folderId matches a MOCK_FOLDERS entry.
// folderId === null → uncategorized; floats in the flat "Threads" section.
//
const MOCK_THREADS: Thread[] = [
  // ── Homelab Configs ──────────────────────────────────────────────────────
  { id: "t1",  folderId: "f1", title: "Dell BIOS Above 4G Decoding",   preview: "MMIO window remap confirmed on X570.",            ts: "06:16"  },
  { id: "t2",  folderId: "f1", title: "Ghost Node DNS Hardening",       preview: "DoH config pushed to Pi successfully.",           ts: "Yesterday" },
  { id: "t3",  folderId: "f1", title: "Tesla P40 PSU Mod Planning",     preview: "Server PSU → ATX adapter wattage math.",         ts: "Mon"    },
  { id: "t4",  folderId: "f1", title: "Proxmox VM Bridging Issue",      preview: "vmbr0 not forwarding on VLAN tag 20.",            ts: "Sun"    },
  // ── Prompt Engineering ───────────────────────────────────────────────────
  { id: "t5",  folderId: "f2", title: "Langfuse SQLite Integration",    preview: "Tracing pipeline wired to local SQLite.",         ts: "Mar 15" },
  { id: "t6",  folderId: "f2", title: "RAG Pipeline Architecture",      preview: "Three retrieval strategies evaluated.",           ts: "Mar 12" },
  { id: "t7",  folderId: "f2", title: "System Prompt Abliteration",     preview: "Abliterated Llama 3 benchmark vs base.",          ts: "Mar 10" },
  { id: "t8",  folderId: "f2", title: "Context Window Benchmarks",      preview: "128k vs 32k — retrieval degradation rate.",      ts: "Mar 8"  },
  // ── Philosophy ───────────────────────────────────────────────────────────
  { id: "t9",  folderId: "f3", title: "Nietzsche vs Stoicism",          preview: "Amor fati as productive nihilism.",               ts: "Mar 7"  },
  { id: "t10", folderId: "f3", title: "Post-AGI Identity Crisis",       preview: "What does authorship mean after 2025?",           ts: "Mar 5"  },
  // ── System Architecture ──────────────────────────────────────────────────
  { id: "t11", folderId: "f4", title: "Cinema Engine Config",           preview: "Plex transcoding is a crime against compute.",    ts: "Mar 3"  },
  { id: "t12", folderId: "f4", title: "Spirit OS Bento Grid",           preview: "The bento grid looks crispy, I suppose.",        ts: "Mar 1"  },
  // ── Uncategorized (folderId: null) ───────────────────────────────────────
  { id: "t13", folderId: null, title: "Homelab Threat Assessment",      preview: "Running nmap passive fingerprint now...",         ts: "06:14"  },
  { id: "t14", folderId: null, title: "Privacy Hardening Session",      preview: "CCPA compliance for homelab services.",           ts: "Mar 15" },
  { id: "t15", folderId: null, title: "Local LLM Benchmark Run",        preview: "Llama 3.3 Q4_K_M on DDR5 — results.",           ts: "Mar 3"  },
];

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
// Used twice: once as an inline desktop aside, once inside the mobile overlay.
// `onClose` is only passed in the mobile context — it wires the X button and
// auto-closes on thread selection.
//
function ConversationSidebar({
  activeId,
  onSelect,
  onNewChat,
  onClose,
}: {
  activeId: string;
  onSelect: (id: string) => void;
  onNewChat: () => void;
  onClose?: () => void;
}) {
  // Tracks which folders have their thread list expanded.
  // "f1" (Homelab Configs) is open by default to demonstrate the pattern.
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
    onClose?.(); // auto-close the mobile overlay on selection
  }

  const uncategorized = MOCK_THREADS.filter((t) => t.folderId === null);

  return (
    <div className="flex h-full flex-col">

      {/* ── Header: Spirit OS branding + mobile close ── */}
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
      {/*
        Full-width, prominent call-to-action matching Open-WebUI / LobeChat
        conventions for offline chat interfaces. The icon bubble intensifies
        on hover so the interaction target is unmistakably clear.
      */}
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

        {/* ── FOLDERS ─────────────────────────────────────────────────── */}
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

          {MOCK_FOLDERS.map((folder) => {
            const isOpen        = expandedFolders.has(folder.id);
            const threads       = MOCK_THREADS.filter((t) => t.folderId === folder.id);
            // When a thread inside a collapsed folder is active, the folder row
            // itself gets a faint background so the user knows where they are.
            const hasActiveChild = threads.some((t) => t.id === activeId);

            return (
              <div key={folder.id}>
                {/* Folder row */}
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
                    {threads.length}
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

                {/* Thread tree — connector line establishes hierarchy visually */}
                {isOpen && (
                  <div className="mb-1 ml-[22px] border-l border-white/[0.06]">
                    {threads.map((thread) => {
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
                            <span className="flex-shrink-0 text-[10px] text-zinc-700">{thread.ts}</span>
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

        {/* ── THREADS (uncategorized) ──────────────────────────────────── */}
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
                    <span className="mt-px flex-shrink-0 text-[10px] text-zinc-700">{thread.ts}</span>
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
        <p className="mt-0.5 font-mono text-[10px] text-zinc-700">Llama-3-Abliterated</p>
      </div>
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function SovereignChatPage() {
  const [messages, setMessages]           = useState<Message[]>(INITIAL_MESSAGES);
  const [input, setInput]                 = useState("");
  const [sarcasm, setSarcasm]             = useState<SarcasmLevel>("peer");
  const [thinking, setThinking]           = useState(false);
  const [mobileSidebarOpen, setMobileOpen] = useState(false);
  const [activeConvId, setActiveConvId]   = useState("t13");

  const bottomRef   = useRef<HTMLDivElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Dev-only network reminder — fires once on mount in development.
  useEffect(() => {
    if (process.env.NODE_ENV === "development") {
      console.info(
        "%c[Spirit OS · Dev Reminder]%c\n" +
        "• Serving to LAN?  →  npx next dev -H 0.0.0.0\n" +
        "• CSS stale on iOS?  →  rm -rf .next && npx next dev -H 0.0.0.0\n" +
        "• Check next.config.ts allowedDevOrigins includes your device IP.",
        "color:#a78bfa;font-weight:bold",
        "color:#a1a1aa",
      );
    }
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, thinking]);

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    const ta = e.target;
    ta.style.height = "auto";
    ta.style.height = `${Math.min(ta.scrollHeight, 160)}px`;
  };

  const nowHHMM = () =>
    new Date().toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false });

  const send = async () => {
    const text = input.trim();
    if (!text || thinking) return;
    setInput("");
    if (textareaRef.current) textareaRef.current.style.height = "auto";

    setMessages((m) => [...m, { id: Date.now().toString(), role: "user", text, ts: nowHHMM() }]);
    setThinking(true);

    try {
      const res  = await fetch("/api/spirit", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ prompt: text, sarcasm }) });
      const data = await res.json().catch(() => ({}));
      const reply: string = (data as { reply?: string }).reply ?? "";
      setMessages((m) => [...m, { id: (Date.now() + 1).toString(), role: "spirit", text: reply || "[silence] Nothing came back. Suspicious.", ts: nowHHMM() }]);
    } catch {
      setMessages((m) => [...m, { id: (Date.now() + 1).toString(), role: "spirit", text: "[sighs] Network error. The irony of a homelab failing its own AI.", ts: nowHHMM() }]);
    } finally {
      setThinking(false);
    }
  };

  const handleNewChat = () => {
    setMessages([]);
    setMobileOpen(false);
  };

  return (
    /*
      relative — anchors the absolute-positioned mobile sidebar overlay.
      flex-row — desktop sidebar + chat panel sit side by side.
      h-[calc(100dvh-60px)] — subtracts the fixed 60px mobile nav header.
      md:h-[100dvh] — desktop: main has no padding-top, full viewport height.
      No h-screen, no backdrop-blur, no overflow-hidden on ancestors.
    */
    <div className="relative flex h-[calc(100dvh-60px)] flex-row bg-zinc-950 md:h-[100dvh]">

      {/* ── Desktop Conversation Sidebar ─────────────────────────────────── */}
      {/*
        Inline flex child on md+. Always in the document, no mounting cost.
        hidden on mobile so it never competes with the chat panel for space.
      */}
      <aside
        className="hidden md:flex md:w-64 md:flex-shrink-0 md:flex-col border-r border-white/5"
        style={{ background: "#09090b" }}
      >
        <ConversationSidebar
          activeId={activeConvId}
          onSelect={setActiveConvId}
          onNewChat={handleNewChat}
        />
      </aside>

      {/* ── Chat Panel ───────────────────────────────────────────────────── */}
      <div className="flex min-w-0 flex-1 flex-col">

        {/* ── Chat Header ── */}
        <header className="flex flex-shrink-0 items-center justify-between border-b border-white/[0.07] px-4 py-3">

          <div className="flex items-center gap-3">
            {/* Mobile sidebar toggle — hidden on desktop since sidebar is always visible */}
            <button
              type="button"
              onClick={() => setMobileOpen(true)}
              onTouchEnd={(e) => { e.preventDefault(); setMobileOpen(true); }}
              aria-label="Open conversations"
              className="flex h-9 w-9 cursor-pointer touch-manipulation items-center justify-center rounded-xl border border-white/[0.07] bg-white/5 text-zinc-500 transition-colors hover:text-zinc-300 md:hidden"
            >
              <PanelLeft size={15} className="pointer-events-none" aria-hidden />
            </button>

            {/* Model status */}
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
                  Llama-3-Abliterated
                </p>
                <p className="mt-0.5 text-[10px] font-semibold text-emerald-500">Online</p>
              </div>
            </div>
          </div>

          {/* Sarcasm Level toggle */}
          <div className="flex items-center gap-1.5">
            <span className="mr-1 hidden text-[10px] font-semibold uppercase tracking-widest text-zinc-600 sm:block">
              Sarcasm
            </span>
            {SARCASM_LEVELS.map(({ id, label }) => (
              <button
                key={id}
                type="button"
                onClick={() => setSarcasm(id)}
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

            {messages.map((msg) => (
              <div
                key={msg.id}
                className={cn("flex flex-col", msg.role === "user" ? "items-end" : "items-start")}
              >
                <p className="mb-1.5 text-[10px] font-semibold uppercase tracking-widest text-zinc-600">
                  {msg.role === "user" ? "Source" : "Spirit"}
                </p>

                {msg.role === "user" ? (
                  <div className="max-w-[85%] break-words rounded-2xl rounded-tr-sm border border-white/[0.07] bg-zinc-900 px-4 py-3 text-sm leading-relaxed text-zinc-100 sm:max-w-xl">
                    {msg.text}
                  </div>
                ) : (
                  <div className="max-w-[90%] break-words font-mono text-sm leading-relaxed text-zinc-300 sm:max-w-2xl">
                    {parseAcousticMarkers(msg.text)}
                  </div>
                )}

                <p className="mt-1.5 text-[10px] text-zinc-700">{msg.ts}</p>
              </div>
            ))}

            {thinking && (
              <div className="flex flex-col items-start">
                <p className="mb-1.5 text-[10px] font-semibold uppercase tracking-widest text-zinc-600">Spirit</p>
                <p className="font-mono text-sm text-zinc-500">
                  <span className="italic text-violet-500/60">[processing]</span>
                  {" "}
                  <span className="animate-pulse text-violet-400">▌</span>
                </p>
              </div>
            )}

            <div ref={bottomRef} />
          </div>
        </div>

        {/* ── Input Matrix ──────────────────────────────────────────────────
          paddingBottom uses max(12px, env(safe-area-inset-bottom)).
          • env(safe-area-inset-bottom) is the iOS home indicator inset.
            It requires viewportFit:"cover" in app/layout.tsx (already set).
          • Tailwind cannot express env() without a plugin, so this stays
            as an inline style.
          • bg-zinc-950 is explicit so the safe-area padding region is
            painted with the app's background color, not resolved by climbing
            the compositor tree (which can produce wrong colors on iOS).
        ──────────────────────────────────────────────────────────────────── */}
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
              Spirit · Llama-3-Abliterated · XTTS v2 · Sarcasm:{" "}
              <span className={sarcasm === "chill" ? "text-zinc-500" : sarcasm === "peer" ? "text-violet-600" : "text-red-700"}>
                {sarcasm}
              </span>
            </p>
          </div>
        </div>
      </div>

      {/* ── Mobile Sidebar Overlay ────────────────────────────────────────── */}
      {/*
        Conditionally mounted — fresh DOM nodes on every open, bypasses the
        WebKit compositor cache. No CSS opacity/visibility toggle.

        absolute inset-0 — positions within the chat container (below the
        60px mobile nav), not full-screen. The conversation list stays within
        the app chrome, not covering the system nav bar.

        md:hidden — safety valve: even if state is true on desktop, the overlay
        does not render over the already-visible inline sidebar.
      */}
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
              activeId={activeConvId}
              onSelect={setActiveConvId}
              onNewChat={handleNewChat}
              onClose={() => setMobileOpen(false)}
            />
          </aside>
        </>
      )}
    </div>
  );
}
