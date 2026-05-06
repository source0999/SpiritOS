"use client";

// ── MessageActions - desktop hover rail; persisted mobile = bottom sheet (9E-A) ──
import { Check, Copy, MoreHorizontal, Pencil, RotateCcw, Trash2, Volume2, X } from "lucide-react";
import { memo, useCallback, useEffect, useRef, useState, type ReactNode } from "react";

import { MobileSheet } from "@/components/chat/MobileSheet";
import { cn } from "@/lib/cn";
import { useMediaMinWidthLg } from "@/lib/hooks/useMediaMinWidthLg";

export type MessageActionsPlacement = "bubble-assistant" | "bubble-user";

export type MessageActionsProps = {
  role: "user" | "assistant";
  placement?: MessageActionsPlacement;
  onCopy: () => void;
  onDelete: () => void;
  onSpeak?: () => void | Promise<void>;
  speakDisabled?: boolean;
  onEdit?: () => void;
  onRegenerate?: () => void;
  regenerateDisabled?: boolean;
  regenerateTitle?: string;
  actionDisabled?: boolean;
  /** Workspace / Dexie chat: below `lg`, open actions in a portal sheet instead of a fat inline row. */
  useActionSheetBelowLg?: boolean;
  /** Long assistant text: split Speak into summary vs chunked full read (Prompt 10B). */
  assistantLongTts?: boolean;
  onSpeakFullChunks?: () => void | Promise<void>;
};

type ActionBtnProps = {
  label: string;
  onClick: () => void | Promise<void>;
  disabled?: boolean;
  icon: ReactNode;
  variant?: "default" | "danger";
  /** When true, label stays visible (mobile expanded / desktop dense). */
  showLabel?: boolean;
};

const ActionBtn = memo(function ActionBtn({
  label,
  onClick,
  disabled,
  icon,
  variant = "default",
  showLabel = false,
}: ActionBtnProps) {
  return (
    <div className="relative flex flex-col items-center">
      <button
        type="button"
        disabled={disabled}
        title={label}
        aria-label={label}
        onClick={() => void onClick()}
        className={cn(
          "group/btn touch-manipulation flex flex-col items-center justify-center gap-0.5 rounded-md px-1.5 py-1 transition",
          "min-h-[36px] min-w-[36px] sm:min-h-[34px] sm:min-w-[34px]",
          variant === "danger"
            ? "text-chalk/55 hover:bg-rose-500/15 hover:text-rose-200 disabled:opacity-30"
            : "text-chalk/55 hover:bg-white/[0.1] hover:text-chalk disabled:opacity-30",
        )}
      >
        <span className="flex items-center justify-center [&>svg]:h-3.5 [&>svg]:w-3.5 [&>svg]:shrink-0">
          {icon}
        </span>
        <span
          className={cn(
            "font-mono text-[8px] font-semibold uppercase tracking-wide text-chalk/75",
            !showLabel && "sm:sr-only",
          )}
        >
          {label}
        </span>
        {!showLabel ? (
          <span
            aria-hidden
            className={cn(
              "pointer-events-none absolute left-1/2 top-full z-30 mt-1 hidden -translate-x-1/2 whitespace-nowrap rounded-md bg-black/90 px-2 py-1 font-mono text-[10px] text-chalk/95 opacity-0 shadow-lg ring-1 ring-white/10 transition-opacity",
              "max-sm:hidden sm:block sm:group-hover/btn:opacity-100 sm:group-focus-visible/btn:opacity-100",
            )}
          >
            {label}
          </span>
        ) : null}
      </button>
    </div>
  );
});

function ActionRow({
  role,
  copyLabel,
  onCopy,
  onDelete,
  onSpeak,
  speakDisabled,
  onEdit,
  onRegenerate,
  regenerateDisabled,
  regenerateTitle,
  actionDisabled,
  showLabels,
  assistantLongTts,
  onSpeakFullChunks,
}: {
  role: "user" | "assistant";
  copyLabel: string;
  onCopy: () => void;
  onDelete: () => void;
  onSpeak?: () => void | Promise<void>;
  speakDisabled?: boolean;
  onEdit?: () => void;
  onRegenerate?: () => void;
  regenerateDisabled?: boolean;
  regenerateTitle?: string;
  actionDisabled?: boolean;
  showLabels: boolean;
  assistantLongTts?: boolean;
  onSpeakFullChunks?: () => void | Promise<void>;
}) {
  return (
    <div
      className="flex flex-wrap items-center justify-end gap-0.5 rounded-md border border-white/[0.08] bg-black/25 px-1 py-1 shadow-sm backdrop-blur-sm"
      onPointerDown={(e) => e.stopPropagation()}
    >
      <ActionBtn
        label={copyLabel}
        disabled={actionDisabled}
        onClick={onCopy}
        showLabel={showLabels}
        icon={
          copyLabel === "Copied" ? (
            <Check className="text-emerald-400/90" aria-hidden />
          ) : (
            <Copy aria-hidden />
          )
        }
      />
      {onSpeak ? (
        assistantLongTts && onSpeakFullChunks ? (
          <>
            <ActionBtn
              label="Speak summary"
              disabled={actionDisabled || speakDisabled}
              onClick={() => {
                if (actionDisabled || speakDisabled) return;
                void onSpeak();
              }}
              showLabel={showLabels}
              icon={<Volume2 aria-hidden />}
            />
            <ActionBtn
              label="Read full (chunks)"
              disabled={actionDisabled || speakDisabled}
              onClick={() => {
                if (actionDisabled || speakDisabled) return;
                void onSpeakFullChunks();
              }}
              showLabel={showLabels}
              icon={<Volume2 aria-hidden />}
            />
          </>
        ) : (
          <ActionBtn
            label="Speak"
            disabled={actionDisabled || speakDisabled}
            onClick={() => {
              if (actionDisabled || speakDisabled) return;
              void onSpeak();
            }}
            showLabel={showLabels}
            icon={<Volume2 aria-hidden />}
          />
        )
      ) : null}
      {role === "assistant" && onRegenerate ? (
        <div className="relative flex flex-col items-center">
          <button
            type="button"
            disabled={actionDisabled || regenerateDisabled}
            title={regenerateTitle ?? "Regenerate"}
            aria-label="Regenerate"
            onClick={onRegenerate}
            className="group/btn touch-manipulation flex min-h-[36px] min-w-[36px] flex-col items-center justify-center gap-0.5 rounded-md px-1.5 py-1 text-chalk/55 transition hover:bg-white/[0.1] hover:text-chalk disabled:cursor-not-allowed disabled:opacity-30"
          >
            <RotateCcw className="h-3.5 w-3.5" aria-hidden />
            <span
              className={cn(
                "font-mono text-[8px] font-semibold uppercase tracking-wide text-chalk/75",
                !showLabels && "sm:sr-only",
              )}
            >
              Regenerate
            </span>
            {!showLabels ? (
              <span
                aria-hidden
                className="pointer-events-none absolute left-1/2 top-full z-30 mt-1 hidden -translate-x-1/2 whitespace-nowrap rounded-md bg-black/90 px-2 py-1 font-mono text-[10px] text-chalk/95 opacity-0 shadow-lg ring-1 ring-white/10 transition-opacity max-sm:hidden sm:block sm:group-hover/btn:opacity-100 sm:group-focus-visible/btn:opacity-100"
              >
                Regenerate
              </span>
            ) : null}
          </button>
        </div>
      ) : null}
      {role === "user" && onEdit ? (
        <ActionBtn
          label="Edit"
          disabled={actionDisabled}
          onClick={onEdit}
          showLabel={showLabels}
          icon={<Pencil aria-hidden />}
        />
      ) : null}
      <ActionBtn
        label="Delete"
        disabled={actionDisabled}
        onClick={onDelete}
        showLabel={showLabels}
        variant="danger"
        icon={<Trash2 aria-hidden />}
      />
    </div>
  );
}

function TrayActionTile({
  label,
  icon,
  onClick,
  disabled,
  variant = "default",
  compact,
}: {
  label: string;
  icon: ReactNode;
  onClick: () => void | Promise<void>;
  disabled?: boolean;
  variant?: "default" | "danger";
  /** Horizontal compact tray - shorter tiles, still ≥44px touch. */
  compact?: boolean;
}) {
  return (
    <button
      type="button"
      disabled={disabled}
      aria-label={label}
      onClick={() => void onClick()}
      className={cn(
        "touch-manipulation flex min-h-[44px] min-w-0 flex-col items-center justify-center gap-0.5 rounded-xl border px-1.5 font-mono text-[9px] font-semibold uppercase tracking-wide transition active:scale-[0.98]",
        compact ? "flex-1 basis-0 py-1.5 sm:max-w-[5.5rem]" : "gap-1 px-2 py-2",
        variant === "danger"
          ? "border-[color:color-mix(in_oklab,var(--color-rose)_38%,transparent)] bg-rose-500/10 text-rose-100/90 disabled:opacity-35"
          : "border-[color:var(--spirit-border)] bg-white/[0.04] text-chalk/85 hover:bg-white/[0.07] disabled:opacity-35",
      )}
    >
      <span
        className={cn(
          "flex shrink-0 items-center justify-center [&>svg]:h-4 [&>svg]:w-4",
          compact && "[&>svg]:h-[18px] [&>svg]:w-[18px]",
        )}
      >
        {icon}
      </span>
      <span className="max-w-full truncate leading-tight">{label}</span>
    </button>
  );
}

export const MessageActions = memo(function MessageActions({
  role,
  placement = "bubble-assistant",
  onCopy,
  onDelete,
  onSpeak,
  speakDisabled = false,
  onEdit,
  onRegenerate,
  regenerateDisabled = false,
  regenerateTitle,
  actionDisabled = false,
  useActionSheetBelowLg = false,
  assistantLongTts = false,
  onSpeakFullChunks,
}: MessageActionsProps) {
  const isLg = useMediaMinWidthLg();
  const [copied, setCopied] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [sheetOpen, setSheetOpen] = useState(false);
  const copiedTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      if (copiedTimerRef.current) clearTimeout(copiedTimerRef.current);
    };
  }, []);

  const handleCopy = useCallback(() => {
    if (actionDisabled) return;
    onCopy();
    setCopied(true);
    if (copiedTimerRef.current) clearTimeout(copiedTimerRef.current);
    copiedTimerRef.current = setTimeout(() => setCopied(false), 1200);
  }, [actionDisabled, onCopy]);

  const copyLabel = copied ? "Copied" : "Copy";

  const closeSheet = useCallback(() => setSheetOpen(false), []);

  const bubbleLegacy =
    placement === "bubble-assistant"
      ? "mt-1.5 sm:mt-0 sm:absolute sm:right-1.5 sm:top-1.5 sm:z-20"
      : "mt-1.5 sm:mt-0 sm:absolute sm:bottom-1.5 sm:right-1.5 sm:top-auto sm:z-20";

  const bubbleLgSheet =
    placement === "bubble-assistant"
      ? "mt-1.5 lg:mt-0 lg:absolute lg:right-1.5 lg:top-1.5 lg:z-20"
      : "mt-1.5 lg:mt-0 lg:absolute lg:bottom-1.5 lg:right-1.5 lg:top-auto lg:z-20";

  const useActionSheetMode = useActionSheetBelowLg;
  const bubble = useActionSheetBelowLg ? bubbleLgSheet : bubbleLegacy;

  const sheetCopy = useCallback(() => {
    handleCopy();
    closeSheet();
  }, [handleCopy, closeSheet]);

  const sheetSpeak = useCallback(async () => {
    if (actionDisabled || speakDisabled || !onSpeak) return;
    await onSpeak();
    closeSheet();
  }, [actionDisabled, speakDisabled, onSpeak, closeSheet]);

  const sheetSpeakChunks = useCallback(async () => {
    if (actionDisabled || speakDisabled || !onSpeakFullChunks) return;
    await onSpeakFullChunks();
    closeSheet();
  }, [actionDisabled, speakDisabled, onSpeakFullChunks, closeSheet]);

  const sheetEdit = useCallback(() => {
    if (actionDisabled || !onEdit) return;
    onEdit();
    closeSheet();
  }, [actionDisabled, onEdit, closeSheet]);

  const sheetRegenerate = useCallback(() => {
    if (actionDisabled || regenerateDisabled || !onRegenerate) return;
    onRegenerate();
    closeSheet();
  }, [actionDisabled, regenerateDisabled, onRegenerate, closeSheet]);

  const sheetDelete = useCallback(() => {
    if (actionDisabled) return;
    if (typeof window !== "undefined" && !window.confirm("Delete this message?")) return;
    onDelete();
    closeSheet();
  }, [actionDisabled, onDelete, closeSheet]);

  if (useActionSheetMode && !isLg) {
    const sheetTriggerWrap =
      role === "user"
        ? "absolute right-1 top-1 z-20 sm:right-1.5 sm:top-1.5"
        : cn("block", bubble);

    return (
      <>
        <div className={sheetTriggerWrap}>
          <button
            type="button"
            onClick={() => setSheetOpen(true)}
            aria-expanded={sheetOpen}
            aria-label="Message actions"
            className="touch-manipulation inline-flex min-h-[44px] min-w-[44px] items-center justify-center rounded-full border border-white/[0.08] bg-black/25 text-chalk/50 shadow-sm backdrop-blur-sm transition hover:border-white/12 hover:bg-black/35 hover:text-chalk/70 active:scale-[0.96]"
          >
            <MoreHorizontal className="h-4 w-4" aria-hidden strokeWidth={2} />
          </button>
        </div>

        <MobileSheet
          open={sheetOpen}
          title="Actions"
          onClose={closeSheet}
          side="bottom"
          variant="trayCompact"
        >
          <div
            className="flex flex-nowrap items-stretch justify-center gap-2 overflow-x-auto pb-0.5"
            onPointerDown={(e) => e.stopPropagation()}
          >
            <TrayActionTile
              label={copyLabel}
              compact
              icon={
                copyLabel === "Copied" ? (
                  <Check className="text-emerald-400/90" aria-hidden />
                ) : (
                  <Copy aria-hidden />
                )
              }
              onClick={sheetCopy}
              disabled={actionDisabled}
            />
            {onSpeak && assistantLongTts && onSpeakFullChunks ? (
              <>
                <TrayActionTile
                  label="Summary"
                  compact
                  icon={<Volume2 aria-hidden />}
                  onClick={sheetSpeak}
                  disabled={actionDisabled || speakDisabled}
                />
                <TrayActionTile
                  label="Full chunks"
                  compact
                  icon={<Volume2 aria-hidden />}
                  onClick={sheetSpeakChunks}
                  disabled={actionDisabled || speakDisabled}
                />
              </>
            ) : onSpeak ? (
              <TrayActionTile
                label="Speak"
                compact
                icon={<Volume2 aria-hidden />}
                onClick={sheetSpeak}
                disabled={actionDisabled || speakDisabled}
              />
            ) : null}
            {role === "user" && onEdit ? (
              <TrayActionTile
                label="Edit"
                compact
                icon={<Pencil aria-hidden />}
                onClick={sheetEdit}
                disabled={actionDisabled}
              />
            ) : null}
            {role === "assistant" && onRegenerate ? (
              <TrayActionTile
                label="Regenerate"
                compact
                icon={<RotateCcw aria-hidden />}
                onClick={sheetRegenerate}
                disabled={actionDisabled || regenerateDisabled}
              />
            ) : null}
            <TrayActionTile
              label="Delete"
              compact
              icon={<Trash2 aria-hidden />}
              onClick={sheetDelete}
              disabled={actionDisabled}
              variant="danger"
            />
          </div>
        </MobileSheet>
      </>
    );
  }

  if (useActionSheetMode && isLg) {
    return (
      <div
        className={cn(
          "flex flex-wrap items-center justify-end gap-0.5 rounded-md border border-white/[0.08] bg-black/25 px-0.5 py-0.5 shadow-sm backdrop-blur-sm",
          "pointer-events-auto opacity-0 transition-opacity duration-150",
          "group-hover/message:opacity-100 group-focus-within/message:opacity-100",
          bubble,
        )}
      >
        <ActionRow
          role={role}
          copyLabel={copyLabel}
          onCopy={handleCopy}
          onDelete={onDelete}
          onSpeak={onSpeak}
          speakDisabled={speakDisabled}
          onEdit={onEdit}
          onRegenerate={onRegenerate}
          regenerateDisabled={regenerateDisabled}
          regenerateTitle={regenerateTitle}
          actionDisabled={actionDisabled}
          showLabels={false}
          assistantLongTts={assistantLongTts}
          onSpeakFullChunks={onSpeakFullChunks}
        />
      </div>
    );
  }

  return (
    <>
      <div className={cn("max-sm:block sm:hidden", bubble)}>
        {!mobileOpen ? (
          <button
            type="button"
            onClick={() => setMobileOpen(true)}
            aria-expanded={false}
            aria-label="Message actions"
            className="touch-manipulation inline-flex items-center gap-1 rounded-md border border-white/[0.12] bg-black/30 px-2 py-1 font-mono text-[9px] font-semibold uppercase tracking-wide text-chalk/65"
          >
            <MoreHorizontal className="h-3.5 w-3.5" aria-hidden />
            Actions
          </button>
        ) : (
          <div className="flex flex-col gap-1.5 rounded-lg border border-white/[0.1] bg-black/40 p-2">
            <div className="flex justify-end">
              <button
                type="button"
                onClick={() => setMobileOpen(false)}
                aria-label="Close actions"
                className="inline-flex h-8 w-8 items-center justify-center rounded-md border border-[color:var(--spirit-border)] text-chalk/60"
              >
                <X className="h-3.5 w-3.5" aria-hidden />
              </button>
            </div>
            <ActionRow
              role={role}
              copyLabel={copyLabel}
              onCopy={handleCopy}
              onDelete={onDelete}
              onSpeak={onSpeak}
              speakDisabled={speakDisabled}
              onEdit={onEdit}
              onRegenerate={onRegenerate}
              regenerateDisabled={regenerateDisabled}
              regenerateTitle={regenerateTitle}
              actionDisabled={actionDisabled}
              showLabels
              assistantLongTts={assistantLongTts}
              onSpeakFullChunks={onSpeakFullChunks}
            />
          </div>
        )}
      </div>

      <div
        className={cn(
          "hidden sm:flex sm:flex-wrap sm:items-center sm:justify-end sm:gap-0.5 sm:rounded-md sm:border sm:border-white/[0.08] sm:bg-black/25 sm:px-0.5 sm:py-0.5 sm:shadow-sm sm:backdrop-blur-sm",
          "sm:pointer-events-auto sm:opacity-0 sm:transition-opacity sm:duration-150",
          "sm:group-hover/message:opacity-100 sm:group-focus-within/message:opacity-100",
          bubble,
        )}
      >
        <ActionRow
          role={role}
          copyLabel={copyLabel}
          onCopy={handleCopy}
          onDelete={onDelete}
          onSpeak={onSpeak}
          speakDisabled={speakDisabled}
          onEdit={onEdit}
          onRegenerate={onRegenerate}
          regenerateDisabled={regenerateDisabled}
          regenerateTitle={regenerateTitle}
          actionDisabled={actionDisabled}
          showLabels={false}
          assistantLongTts={assistantLongTts}
          onSpeakFullChunks={onSpeakFullChunks}
        />
      </div>
    </>
  );
});

/** Tiny affordance when inline-editing user text */
export const EditMessageToolbar = memo(function EditMessageToolbar({
  onSave,
  onCancel,
  disabled,
}: {
  onSave: () => void;
  onCancel: () => void;
  disabled?: boolean;
}) {
  return (
    <div className="mt-1 flex justify-end gap-1">
      <button
        type="button"
        disabled={disabled}
        onClick={onCancel}
        aria-label="Cancel edit"
        className="touch-manipulation inline-flex items-center gap-1 rounded-md border border-[color:var(--spirit-border)] px-2 py-1 font-mono text-[10px] uppercase tracking-wide text-chalk/60 transition hover:bg-white/[0.06] disabled:opacity-40"
      >
        <X className="h-3 w-3" aria-hidden />
        Esc
      </button>
      <button
        type="button"
        disabled={disabled}
        onClick={onSave}
        aria-label="Save edit"
        className="touch-manipulation inline-flex items-center gap-1 rounded-md border border-[color:color-mix(in_oklab,var(--spirit-accent)_42%,transparent)] bg-[color:color-mix(in_oklab,var(--spirit-accent)_12%,transparent)] px-2 py-1 font-mono text-[10px] font-semibold uppercase tracking-wide text-[color:var(--spirit-accent-strong)] transition hover:brightness-110 disabled:opacity-40"
      >
        <Check className="h-3 w-3" aria-hidden />
        ⌃↵
      </button>
    </div>
  );
});
