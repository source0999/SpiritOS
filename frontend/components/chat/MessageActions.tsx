// ─── Spirit OS · MessageActions ───────────────────────────────────────────────
//
// Hover-revealed edit controls for Spirit message bubbles.
//
// Renders in two modes:
//   "idle"    — a pencil icon button, visible only on parent hover via the
//               group/group-hover Tailwind pattern. Zero layout shift.
//   "editing" — an inline textarea replacing the bubble content, with
//               Ctrl+Enter commit and Escape cancel. A checkmark button
//               and X button flank the bottom of the textarea.
//
// The component is intentionally display-only — it surfaces the editing UI
// and calls the onSave/onCancel callbacks. The actual Dexie write is handled
// by the parent (MessageBubble → page.tsx → useThreadCRUD.editMessage).
//
// ─────────────────────────────────────────────────────────────────────────────

"use client";

import { useState, useRef, useEffect } from "react";
import { Pencil, Check, X } from "lucide-react";

// ── EditTextarea ──────────────────────────────────────────────────────────────

function EditTextarea({
  initialText,
  onSave,
  onCancel,
}: {
  initialText: string;
  onSave:      (text: string) => void;
  onCancel:    () => void;
}) {
  const [draft, setDraft] = useState(initialText);
  const ref = useRef<HTMLTextAreaElement>(null);

  // Auto-focus and place cursor at end on mount.
  useEffect(() => {
    const ta = ref.current;
    if (!ta) return;
    ta.focus();
    ta.setSelectionRange(ta.value.length, ta.value.length);
    // Auto-size to content.
    ta.style.height = "auto";
    ta.style.height = `${ta.scrollHeight}px`;
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setDraft(e.target.value);
    const ta = e.target;
    ta.style.height = "auto";
    ta.style.height = `${ta.scrollHeight}px`;
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && e.ctrlKey) {
      e.preventDefault();
      onSave(draft);
    }
    if (e.key === "Escape") {
      e.preventDefault();
      onCancel();
    }
  };

  return (
    <div className="flex w-full flex-col gap-2">
      <textarea
        ref={ref}
        value={draft}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        className="w-full resize-none rounded-xl border border-violet-500/30 bg-zinc-900 px-3 py-2.5 font-mono text-sm leading-relaxed text-zinc-200 outline-none focus:border-violet-500/60"
        style={{ minHeight: "4rem" }}
      />
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => onSave(draft)}
          className="flex items-center gap-1.5 rounded-lg border border-violet-500/30 bg-violet-500/20 px-2.5 py-1 text-[11px] font-semibold text-violet-300 transition-colors hover:bg-violet-500/30"
        >
          <Check size={11} aria-hidden />
          Save
          <span className="ml-1 text-[10px] font-normal opacity-50">Ctrl+Enter</span>
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="flex items-center gap-1.5 rounded-lg border border-white/[0.07] px-2.5 py-1 text-[11px] font-semibold text-zinc-500 transition-colors hover:text-zinc-300"
        >
          <X size={11} aria-hidden />
          Cancel
          <span className="ml-1 text-[10px] font-normal opacity-50">Esc</span>
        </button>
      </div>
    </div>
  );
}

// ── MessageActions (exported) ─────────────────────────────────────────────────

export interface MessageActionsProps {
  messageId:   string;
  messageText: string;
  isEditing:   boolean;
  onStartEdit: () => void;
  onSave:      (newText: string) => void;
  onCancel:    () => void;
}

export function MessageActions({
  messageText,
  isEditing,
  onStartEdit,
  onSave,
  onCancel,
}: MessageActionsProps) {
  if (isEditing) {
    return (
      <EditTextarea
        initialText={messageText}
        onSave={onSave}
        onCancel={onCancel}
      />
    );
  }

  // Idle mode: pencil icon, visible on group hover.
  return (
    <button
      type="button"
      onClick={onStartEdit}
      aria-label="Edit message"
      className="opacity-0 group-hover:opacity-100 flex h-6 w-6 items-center justify-center rounded-lg text-zinc-700 transition-all hover:text-violet-400 focus-visible:opacity-100"
    >
      <Pencil size={11} aria-hidden />
    </button>
  );
}
