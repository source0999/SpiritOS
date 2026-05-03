"use client";

// ── SpiritMessage — one bubble, two roles, Dark Node glass rules ─────────────
// > Extracted from: _blueprints/design_system.md — chalk/cyan via @theme, no emerald cosplay
import type { UIMessage } from "ai";
import { motion } from "framer-motion";
import { memo } from "react";

import { SectionLabel } from "@/components/ui/SectionLabel";
import { cn } from "@/lib/cn";
import { textFromParts } from "@/lib/chat-utils";

export type SpiritMessageProps = {
  message: UIMessage;
};

export const SpiritMessage = memo(function SpiritMessage({
  message,
}: SpiritMessageProps) {
  const isUser = message.role === "user";

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.22, ease: [0.22, 1, 0.36, 1] }}
      className={cn("flex", isUser ? "justify-end" : "justify-start")}
      data-role={message.role}
    >
      <div
        className={cn(
          !isUser && [
            "w-full border-l-2 border-l-[color:var(--spirit-accent)]",
            "bg-[linear-gradient(90deg,color-mix(in_oklab,var(--spirit-glow)_55%,transparent)_0%,transparent_55%)]",
            "rounded-r-2xl py-3 pl-4 pr-3 lg:max-w-[min(100%,42rem)] lg:rounded-2xl",
          ],
          isUser && [
            "max-w-[min(100%,42rem)] rounded-3xl border border-[color:var(--spirit-border)]",
            "bg-white/[0.04] px-4 py-3 backdrop-blur-xl shadow-[inset_0_0_0_1px_rgba(255,255,255,0.04)]",
            "leading-relaxed",
          ],
        )}
      >
        {isUser ? (
          <SectionLabel className="mb-1 block text-[11px] font-medium tracking-wider">
            You
          </SectionLabel>
        ) : (
          <SectionLabel className="mb-1 block font-mono text-[10px] tracking-[0.28em] text-[color:var(--spirit-accent-strong)] [text-shadow:0_0_12px_color-mix(in_oklab,var(--spirit-glow)_70%,transparent)]">
            Spirit
          </SectionLabel>
        )}
        <p
          className={cn(
            "whitespace-pre-wrap break-words font-sans text-[15px] text-chalk/90 leading-relaxed",
          )}
        >
          {textFromParts(message)}
        </p>
      </div>
    </motion.div>
  );
});
