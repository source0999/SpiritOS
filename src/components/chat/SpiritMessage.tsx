"use client";

// ── SpiritMessage - bubble-first layout; actions in-bubble (Prompt 9B) ───────────
// > GPT-adjacent polish: calm assistant surface (no lateral glow smear), compact user rail.
import type { UIMessage } from "ai";
import { motion } from "framer-motion";
import { memo, useCallback, useMemo, useState } from "react";

import { EditableUserMessage } from "@/components/chat/EditableUserMessage";
import { MessageActions } from "@/components/chat/MessageActions";
import { MessageMarkdown } from "@/components/chat/MessageMarkdown";
import type { SpiritWebSourcesHeaderPayload } from "@/lib/spirit/spirit-web-sources";
import { SectionLabel } from "@/components/ui/SectionLabel";
import { StreamingCursor } from "@/components/chat/StreamingCursor";
import { cn } from "@/lib/cn";
import { textFromParts } from "@/lib/chat-utils";
import { copyTextToClipboard } from "@/lib/clipboard";
import { sanitizeAssistantVisibleText } from "@/lib/spirit/assistant-output-sanitizer";
import { stripFakeCitationsWhenNoSources } from "@/lib/spirit/research-source-enforcement";

export type SpiritMessageProps = {
  message: UIMessage;
  isStreamingLatest?: boolean;
  isBusy?: boolean;
  canRegenerate?: boolean;
  onDelete?: () => void;
  onEditSave?: (text: string) => void;
  onRegenerate?: () => void;
  onSpeak?: () => void | Promise<void>;
  /** Prompt 10B - read full assistant reply in TTS-safe chunks */
  onSpeakFullChunks?: () => void | Promise<void>;
  assistantLongVoice?: boolean;
  speakDisabled?: boolean;
  actionDisabled?: boolean;
  /** Dexie workspace: message actions use a portal sheet below the `lg` breakpoint. */
  useActionSheetBelowLg?: boolean;
  onCopyFeedback?: (ok: boolean) => void;
  /** Prompt 10C-C - strip fake [n] / Sources when Researcher had zero verified URLs */
  stripFakeResearchCitations?: boolean;
  /** When assistant had verified web sources, rewrite degenerate ## Sources from header JSON */
  webSourcesSnapshot?: SpiritWebSourcesHeaderPayload | null;
};

export const SpiritMessage = memo(function SpiritMessage({
  message,
  isStreamingLatest = false,
  isBusy = false,
  canRegenerate = false,
  onDelete,
  onEditSave,
  onRegenerate,
  onSpeak,
  onSpeakFullChunks,
  assistantLongVoice = false,
  speakDisabled = false,
  actionDisabled = false,
  useActionSheetBelowLg = false,
  onCopyFeedback,
  stripFakeResearchCitations = false,
  webSourcesSnapshot = null,
}: SpiritMessageProps) {
  const isUser = message.role === "user";
  const [editing, setEditing] = useState(false);
  const rawBody = textFromParts(message);
  const body = useMemo(() => {
    if (isUser) return rawBody;
    const cleaned = sanitizeAssistantVisibleText(rawBody);
    return stripFakeResearchCitations ? stripFakeCitationsWhenNoSources(cleaned) : cleaned;
  }, [isUser, rawBody, stripFakeResearchCitations]);

  const handleCopy = useCallback(async () => {
    const r = await copyTextToClipboard(body);
    onCopyFeedback?.(r.ok);
  }, [body, onCopyFeedback]);

  const actionsDisabled = Boolean(actionDisabled || (isUser && editing));

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
      className={cn(
        "group/message flex w-full min-w-0",
        isUser ? "justify-end" : "justify-start",
      )}
      data-role={message.role}
    >
      <div className="w-full max-w-[min(720px,calc(100%-0.25rem))] sm:max-w-[min(760px,calc(100%-1.5rem))]">
        <div
          className={cn(
            "relative flex min-w-0 flex-col",
            !isUser && [
              "w-full max-w-full",
              "border border-[color:color-mix(in_oklab,var(--spirit-border)_45%,transparent)] border-l-[3px] border-l-[color:var(--spirit-accent)]",
              "bg-white/[0.035]",
              "max-lg:rounded-xl max-lg:py-2 max-lg:pl-2.5 max-lg:pr-2",
              "rounded-2xl py-2.5 pl-3.5 pr-2.5 sm:py-3 sm:pl-4 sm:pr-3 lg:rounded-2xl",
            ],
            isUser && [
              "max-lg:rounded-2xl max-lg:px-3 max-lg:py-2",
              "rounded-2xl border border-[color:color-mix(in_oklab,var(--spirit-border)_70%,transparent)]",
              "bg-white/[0.045] px-3 py-2.5 backdrop-blur-xl shadow-[inset_0_0_0_1px_rgba(255,255,255,0.05)] sm:rounded-2xl sm:px-4 sm:py-2.5",
            ],
          )}
        >
          <div
            className={cn(
              "min-w-0",
            !isUser && "pr-1 sm:pr-2 lg:pr-[5.5rem]",
            isUser &&
              (useActionSheetBelowLg
                ? "pb-1 pr-1 max-lg:pr-10 sm:pr-2 sm:pb-1.5 lg:pb-8"
                : "sm:pb-8 sm:pr-2"),
            )}
          >
            {isUser ? (
              <SectionLabel className="mb-0.5 block text-[10px] font-medium tracking-wider text-chalk/42 max-lg:text-[10px] sm:mb-1 sm:text-[11px]">
                You
              </SectionLabel>
            ) : (
              <SectionLabel className="mb-0.5 block font-mono text-[9px] tracking-[0.18em] text-[color:color-mix(in_oklab,var(--spirit-accent-strong)_88%,transparent)] max-lg:text-[9px] sm:mb-1 sm:text-[10px] sm:tracking-[0.22em]">
                Spirit
              </SectionLabel>
            )}
            {isUser && editing && onEditSave ? (
              <EditableUserMessage
                initialText={body}
                disabled={isBusy}
                onSave={(next) => {
                  onEditSave(next);
                  setEditing(false);
                }}
                onCancel={() => setEditing(false)}
              />
            ) : isUser ? (
              <p className="whitespace-pre-wrap break-words [overflow-wrap:anywhere] font-sans text-[16px] leading-snug text-chalk/90 max-lg:text-[16px] sm:text-[15px] sm:leading-relaxed">
                {body}
              </p>
            ) : (
              <div className="min-w-0 max-w-full [overflow-wrap:anywhere]">
                <MessageMarkdown text={body} webSourcesSnapshot={webSourcesSnapshot} />
                {isStreamingLatest ? <StreamingCursor /> : null}
              </div>
            )}
          </div>
          {onDelete ? (
            <MessageActions
              role={isUser ? "user" : "assistant"}
              placement={isUser ? "bubble-user" : "bubble-assistant"}
              onCopy={() => void handleCopy()}
              onDelete={onDelete}
              onEdit={
                isUser && onEditSave
                  ? () => {
                      if (isBusy) return;
                      setEditing(true);
                    }
                  : undefined
              }
              onRegenerate={!isUser && onRegenerate ? onRegenerate : undefined}
              onSpeak={onSpeak}
              onSpeakFullChunks={!isUser ? onSpeakFullChunks : undefined}
              assistantLongTts={!isUser && assistantLongVoice}
              speakDisabled={speakDisabled}
              regenerateDisabled={!isUser && !canRegenerate}
              regenerateTitle={
                !isUser && !canRegenerate
                  ? "Regenerate is only available for the latest assistant reply"
                  : undefined
              }
              actionDisabled={actionsDisabled}
              useActionSheetBelowLg={useActionSheetBelowLg}
            />
          ) : null}
        </div>
      </div>
    </motion.div>
  );
});
