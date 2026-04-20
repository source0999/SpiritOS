// ─── Spirit OS · ThreadItem ───────────────────────────────────────────────────
//
// A single thread row in the sidebar. Handles three internal states:
//
//   "idle"      — normal display: title + timestamp, hover reveals ⋯ button
//   "renaming"  — inline <input> replaces the title text
//   "confirming"— a compact "Delete? Yes / No" confirmation replaces the row
//
// Props are minimal by design — all Dexie mutations are delegated upward via
// onRename and onDelete callbacks. This keeps the component pure and testable.
//
// The ⋯ menu is intentionally NOT a real dropdown/portal — it's an inline
// state toggle. Portals add z-index complexity inside the sidebar scroll
// container. The inline approach is simpler and works equally well.
//
// ─────────────────────────────────────────────────────────────────────────────

"use client";

import { useState, useRef, useEffect } from "react";
import { MoreHorizontal, Pencil, Trash2, Check, X } from "lucide-react";
import type { Thread } from "@/lib/db.types";

function cn(...classes: (string | undefined | false | null)[]) {
  return classes.filter(Boolean).join(" ");
}

// ── Internal states ───────────────────────────────────────────────────────────
type RowState = "idle" | "menu" | "renaming" | "confirming";

// ── Props ─────────────────────────────────────────────────────────────────────
export interface ThreadItemProps {
  thread:   Thread;
  active:   boolean;
  onSelect: (id: string) => void;
  onRename: (id: string, newTitle: string) => Promise<void>;
  onDelete: (id: string) => Promise<void>;
  /** Optional: passed by DnD wrapper in Step 5 */
  dragHandleProps?: React.HTMLAttributes<HTMLDivElement>;
}

// ── Component ─────────────────────────────────────────────────────────────────
export function ThreadItem({
  thread,
  active,
  onSelect,
  onRename,
  onDelete,
  dragHandleProps,
}: ThreadItemProps) {
  const [rowState, setRowState] = useState<RowState>("idle");
  const [draft, setDraft] = useState(thread.title);
  const inputRef = useRef<HTMLInputElement>(null);

  // Keep draft in sync if auto-title updates the thread externally.
  useEffect(() => {
    if (rowState !== "renaming") setDraft(thread.title);
  }, [thread.title, rowState]);

  // Focus the input when entering rename state.
  useEffect(() => {
    if (rowState === "renaming") {
      inputRef.current?.focus();
      inputRef.current?.select();
    }
  }, [rowState]);

  // ── Handlers ────────────────────────────────────────────────────────────
  function commitRename() {
    const trimmed = draft.trim();
    if (trimmed && trimmed !== thread.title) {
      void onRename(thread.id, trimmed);
    }
    setRowState("idle");
  }

  function cancelRename() {
    setDraft(thread.title);
    setRowState("idle");
  }

  async function confirmDelete() {
    await onDelete(thread.id);
    // Parent will handle activeThread switch — no local state needed.
  }

  // ── Renaming state ───────────────────────────────────────────────────────
  if (rowState === "renaming") {
    return (
      <div className="relative flex w-full items-center gap-1 rounded-xl bg-white/[0.06] px-2 py-1.5">
        <input
          ref={inputRef}
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter")  { e.preventDefault(); commitRename(); }
            if (e.key === "Escape") { e.preventDefault(); cancelRename(); }
          }}
          onBlur={commitRename}
          maxLength={60}
          className="min-w-0 flex-1 rounded-lg border border-violet-500/30 bg-zinc-900 px-2 py-1 font-mono text-[11px] text-zinc-100 outline-none focus:border-violet-500/60"
        />
        <button
          type="button"
          onMouseDown={(e) => { e.preventDefault(); commitRename(); }}
          aria-label="Confirm rename"
          className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-lg text-violet-400 hover:bg-violet-500/20"
        >
          <Check size={11} aria-hidden />
        </button>
        <button
          type="button"
          onMouseDown={(e) => { e.preventDefault(); cancelRename(); }}
          aria-label="Cancel rename"
          className="flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-lg text-zinc-600 hover:text-zinc-300"
        >
          <X size={11} aria-hidden />
        </button>
      </div>
    );
  }

  // ── Delete confirmation state ────────────────────────────────────────────
  if (rowState === "confirming") {
    return (
      <div className="flex w-full items-center gap-2 rounded-xl border border-red-500/20 bg-red-500/[0.07] px-3 py-2">
        <span className="min-w-0 flex-1 truncate text-[11px] text-red-400">
          Delete &ldquo;{thread.title}&rdquo;?
        </span>
        <button
          type="button"
          onClick={() => void confirmDelete()}
          className="flex-shrink-0 rounded-lg border border-red-500/30 bg-red-500/20 px-2 py-0.5 text-[10px] font-semibold text-red-300 transition-colors hover:bg-red-500/30"
        >
          Delete
        </button>
        <button
          type="button"
          onClick={() => setRowState("idle")}
          className="flex-shrink-0 rounded-lg border border-white/[0.07] px-2 py-0.5 text-[10px] font-semibold text-zinc-500 transition-colors hover:text-zinc-300"
        >
          Cancel
        </button>
      </div>
    );
  }

  // ── Menu state (⋯ expanded) ──────────────────────────────────────────────
  if (rowState === "menu") {
    return (
      <div className="relative flex w-full flex-col gap-0.5 rounded-xl bg-white/[0.06] px-2 py-1.5">
        <p className="mb-1 truncate px-1 text-[11px] font-medium text-zinc-300">
          {thread.title}
        </p>
        <button
          type="button"
          onClick={() => setRowState("renaming")}
          className="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-[11px] text-zinc-400 transition-colors hover:bg-white/[0.06] hover:text-zinc-100"
        >
          <Pencil size={11} aria-hidden />
          Rename
        </button>
        <button
          type="button"
          onClick={() => setRowState("confirming")}
          className="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-[11px] text-red-500/80 transition-colors hover:bg-red-500/10 hover:text-red-400"
        >
          <Trash2 size={11} aria-hidden />
          Delete
        </button>
        <button
          type="button"
          onClick={() => setRowState("idle")}
          className="flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-[11px] text-zinc-600 transition-colors hover:text-zinc-400"
        >
          <X size={11} aria-hidden />
          Cancel
        </button>
      </div>
    );
  }

  // ── Idle state (default) ─────────────────────────────────────────────────
  return (
    <div
      className={cn(
        "group relative flex w-full items-center rounded-xl transition-colors",
        active ? "bg-white/[0.08]" : "hover:bg-white/[0.04] active:bg-white/[0.06]",
      )}
      {...dragHandleProps}
    >
      {active && (
        <span className="absolute left-0 top-1/2 h-5 w-0.5 -translate-y-1/2 rounded-full bg-violet-500/70" />
      )}

      {/* Main click target */}
      <button
        type="button"
        onClick={() => onSelect(thread.id)}
        className="min-w-0 flex-1 px-3 py-2.5 text-left"
      >
        <div className="flex items-start justify-between gap-2">
          <p className={cn(
            "truncate text-[12px] font-medium leading-snug",
            active ? "text-zinc-100" : "text-zinc-400",
          )}>
            {thread.title}
          </p>
          <span className="mt-px flex-shrink-0 text-[10px] text-zinc-700">
            {new Date(thread.updatedAt).toLocaleTimeString("en-US", {
              hour: "2-digit",
              minute: "2-digit",
              hour12: false,
            })}
          </span>
        </div>
        {thread.preview && (
          <p className="mt-0.5 truncate text-[11px] text-zinc-600">
            {thread.preview}
          </p>
        )}
      </button>

      {/* ⋯ action button — visible on hover */}
      <button
        type="button"
        onClick={(e) => { e.stopPropagation(); setRowState("menu"); }}
        aria-label={`Options for ${thread.title}`}
        className="mr-1.5 flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-lg text-zinc-700 opacity-0 transition-all group-hover:opacity-100 hover:bg-white/[0.08] hover:text-zinc-400 focus-visible:opacity-100"
      >
        <MoreHorizontal size={13} aria-hidden />
      </button>
    </div>
  );
}
