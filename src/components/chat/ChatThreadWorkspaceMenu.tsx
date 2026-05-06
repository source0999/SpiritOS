"use client";

// ── ChatThreadWorkspaceMenu - current thread actions without sidebar spelunking ─
import { FolderInput, Pencil, Pin, PinOff, Trash2, X } from "lucide-react";
import { memo, useEffect, useRef } from "react";

import type { ChatFolder } from "@/lib/chat-db.types";
import { getModelProfile } from "@/lib/spirit/model-profiles";
import type { ModelProfileId } from "@/lib/spirit/model-profile.types";
import { cn } from "@/lib/cn";

export type ChatThreadWorkspaceMenuProps = {
  open: boolean;
  onClose: () => void;
  variant: "popover" | "sheet";
  modelProfileId: ModelProfileId;
  threadTitle: string;
  threadId: string | null;
  draftActive: boolean;
  isPinned: boolean;
  folders: ChatFolder[];
  folderId: string | null | undefined;
  onRename: () => void;
  onDelete: () => void;
  onTogglePin: () => void;
  onMoveToFolder: (folderId: string | null) => void;
};

export const ChatThreadWorkspaceMenu = memo(function ChatThreadWorkspaceMenu({
  open,
  onClose,
  variant,
  modelProfileId,
  threadTitle,
  threadId,
  draftActive,
  isPinned,
  folders,
  folderId,
  onRename,
  onDelete,
  onTogglePin,
  onMoveToFolder,
}: ChatThreadWorkspaceMenuProps) {
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  useEffect(() => {
    if (!open) return;
    const onPointer = (e: PointerEvent) => {
      const el = panelRef.current;
      if (!el || el.contains(e.target as Node)) return;
      onClose();
    };
    window.addEventListener("pointerdown", onPointer, true);
    return () => window.removeEventListener("pointerdown", onPointer, true);
  }, [open, onClose]);

  if (!open) return null;

  const sheet = variant === "sheet";
  const mode = getModelProfile(modelProfileId);
  const moveValue =
    folderId && folders.some((f) => f.id === folderId) ? folderId : "__root__";

  return (
    <>
      <button
        type="button"
        aria-label="Close thread menu"
        className="fixed inset-0 z-[140] bg-black/55 backdrop-blur-[2px]"
        onClick={onClose}
      />
      <div
        ref={panelRef}
        className={cn(
          "fixed z-[150] flex w-[min(100vw-1.5rem,20rem)] flex-col overflow-hidden rounded-xl border border-[color:var(--spirit-border)] bg-[color:color-mix(in_oklab,var(--spirit-bg)_94%,black)] shadow-[0_24px_80px_-24px_rgba(0,0,0,0.75)]",
          sheet
            ? "inset-x-0 bottom-0 mx-auto max-h-[70dvh] w-full max-w-md rounded-b-none rounded-t-2xl border-b-0 pb-[env(safe-area-inset-bottom,0px)]"
            : "right-3 top-[3.25rem] max-lg:right-2 max-lg:top-24",
        )}
        role="dialog"
        aria-modal="true"
        aria-labelledby="thread-menu-heading"
      >
        <div className="flex items-center justify-between gap-2 border-b border-[color:var(--spirit-border)] px-3 py-2">
          <h2 id="thread-menu-heading" className="min-w-0 truncate font-mono text-[11px] font-semibold uppercase tracking-wider text-chalk">
            Thread settings
          </h2>
          <button
            type="button"
            onClick={onClose}
            className="inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-chalk/60 transition hover:bg-white/[0.06]"
            aria-label="Close"
          >
            <X className="h-4 w-4" aria-hidden />
          </button>
        </div>
        <div className="space-y-2 px-3 py-3 font-mono text-[11px] text-chalk/80">
          <p className="text-[10px] text-chalk/45">
            Current mode ·{" "}
            <span className="text-chalk/85">{mode.shortLabel}</span>
          </p>
          <p className="truncate text-[10px] text-chalk/50" title={threadTitle}>
            {draftActive ? "Draft (unsaved)" : threadTitle}
          </p>
          <div className="flex flex-col gap-1.5 pt-1">
            <button
              type="button"
              disabled={draftActive || !threadId}
              onClick={() => {
                onRename();
                onClose();
              }}
              className="flex items-center gap-2 rounded-lg border border-[color:color-mix(in_oklab,var(--spirit-border)_50%,transparent)] bg-white/[0.03] px-2 py-2 text-left transition hover:bg-white/[0.06] disabled:opacity-35"
            >
              <Pencil className="h-3.5 w-3.5 shrink-0" aria-hidden />
              Rename chat
            </button>
            <button
              type="button"
              disabled={draftActive || !threadId}
              onClick={() => {
                onTogglePin();
                onClose();
              }}
              className="flex items-center gap-2 rounded-lg border border-[color:color-mix(in_oklab,var(--spirit-border)_50%,transparent)] bg-white/[0.03] px-2 py-2 text-left transition hover:bg-white/[0.06] disabled:opacity-35"
            >
              {isPinned ? (
                <PinOff className="h-3.5 w-3.5 shrink-0" aria-hidden />
              ) : (
                <Pin className="h-3.5 w-3.5 shrink-0" aria-hidden />
              )}
              {isPinned ? "Unpin chat" : "Pin chat"}
            </button>
            <button
              type="button"
              disabled={draftActive || !threadId}
              onClick={() => {
                onDelete();
                onClose();
              }}
              className="flex items-center gap-2 rounded-lg border border-rose-500/25 bg-rose-500/10 px-2 py-2 text-left text-rose-100/95 transition hover:bg-rose-500/15 disabled:opacity-35"
            >
              <Trash2 className="h-3.5 w-3.5 shrink-0" aria-hidden />
              Delete chat
            </button>
          </div>
          {folders.length > 0 && !draftActive && threadId ? (
            <label className="mt-1 flex flex-col gap-1">
              <span className="flex items-center gap-1 text-[9px] font-semibold uppercase tracking-[0.16em] text-chalk/40">
                <FolderInput className="h-3 w-3" aria-hidden />
                Move to folder
              </span>
              <select
                value={moveValue}
                onChange={(e) => {
                  const v = e.target.value;
                  onMoveToFolder(v === "__root__" ? null : v);
                  onClose();
                }}
                className="w-full cursor-pointer rounded-lg border border-[color:color-mix(in_oklab,var(--spirit-border)_50%,transparent)] bg-black/30 px-2 py-2 text-[10px] text-chalk/80 outline-none"
              >
                <option value="__root__">Chats (root)</option>
                {folders.map((f) => (
                  <option key={f.id} value={f.id}>
                    {f.name}
                  </option>
                ))}
              </select>
            </label>
          ) : null}
        </div>
      </div>
    </>
  );
});
