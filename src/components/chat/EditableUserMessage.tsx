"use client";

// ── EditableUserMessage - inline textarea: ⌃/⌘+Enter save, Esc cancel ───────────
import {
  memo,
  useCallback,
  useEffect,
  useRef,
  useState,
  type KeyboardEvent,
} from "react";

import { EditMessageToolbar } from "@/components/chat/MessageActions";
import { cn } from "@/lib/cn";

export type EditableUserMessageProps = {
  initialText: string;
  onSave: (text: string) => void;
  onCancel: () => void;
  disabled?: boolean;
};

export const EditableUserMessage = memo(function EditableUserMessage({
  initialText,
  onSave,
  onCancel,
  disabled = false,
}: EditableUserMessageProps) {
  const [draft, setDraft] = useState(initialText);
  const taRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    setDraft(initialText);
  }, [initialText]);

  useEffect(() => {
    const el = taRef.current;
    if (!el) return;
    el.focus();
    el.setSelectionRange(el.value.length, el.value.length);
  }, []);

  const commit = useCallback(() => {
    if (disabled) return;
    onSave(draft);
  }, [disabled, draft, onSave]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.nativeEvent.isComposing) return;
      if (e.key === "Escape") {
        e.preventDefault();
        onCancel();
        return;
      }
      if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        commit();
      }
    },
    [commit, onCancel],
  );

  return (
    <div className="flex w-full min-w-0 flex-col">
      <textarea
        ref={taRef}
        value={draft}
        disabled={disabled}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={handleKeyDown}
        rows={3}
        aria-label="Edit message"
        className={cn(
          "scrollbar-hide w-full min-h-[4.5rem] resize-y rounded-xl border border-[color:color-mix(in_oklab,var(--spirit-accent)_35%,transparent)] bg-black/35 px-3 py-2 font-sans text-[15px] text-chalk outline-none",
          "focus:ring-1 focus:ring-[color:color-mix(in_oklab,var(--spirit-accent)_30%,transparent)]",
          "disabled:opacity-40",
        )}
      />
      <EditMessageToolbar onSave={commit} onCancel={onCancel} disabled={disabled} />
    </div>
  );
});
