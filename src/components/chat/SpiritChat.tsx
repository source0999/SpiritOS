"use client";

// ── SpiritChat — messages + transport + input (one implementation to rule them) ─
// > Used by: dashboard neural stage, /chat, /oracle — stop cloning useChat + JSX
// > Design language: _blueprints/design_system.md — @theme chalk/cyan, glass seams
import { useChat } from "@ai-sdk/react";
import { DefaultChatTransport } from "ai";
import { motion } from "framer-motion";
import { ArrowUp } from "lucide-react";
import { memo, useCallback, useMemo, useState, type FormEvent, type ReactNode } from "react";

import { SpiritMessage } from "@/components/chat/SpiritMessage";
import { ClientFailSafe } from "@/components/system/ClientFailSafe";
import { cn } from "@/lib/cn";

export type SpiritChatProps = {
  api?: string;
  variant?: "embedded" | "standalone";
  footerHint?: ReactNode;
  emptyState?: ReactNode;
  shellClassName?: string;
  title?: string;
  subtitle?: string;
};

const SpiritChatInner = memo(function SpiritChatInner({
  api = "/api/spirit",
  variant = "embedded",
  footerHint,
  emptyState,
  shellClassName,
  title,
  subtitle,
}: SpiritChatProps) {
  const transport = useMemo(
    () => new DefaultChatTransport({ api }),
    [api],
  );
  const { messages, sendMessage, status, error } = useChat({ transport });
  const [input, setInput] = useState("");
  const isBusy = status === "submitted" || status === "streaming";
  const hasDraft = Boolean(input.trim());

  const onSubmit = useCallback(
    (e: FormEvent) => {
      e.preventDefault();
      const t = input.trim();
      if (!t || isBusy) return;
      void sendMessage({ text: t });
      setInput("");
    },
    [input, isBusy, sendMessage],
  );

  const list = useMemo(
    () => messages.map((m) => <SpiritMessage key={m.id} message={m} />),
    [messages],
  );

  const defaultEmpty = (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
      className="mx-auto max-w-lg rounded-xl border border-[color:color-mix(in_oklab,var(--spirit-accent)_22%,transparent)] bg-black/[0.18] px-6 py-5 text-center shadow-[0_0_60px_-30px_var(--spirit-glow)] backdrop-blur-sm"
    >
      <p className="font-mono text-[11px] uppercase tracking-[0.32em] text-[color:color-mix(in_oklab,var(--spirit-accent-strong)_80%,transparent)]">
        spirit / ready
      </p>
      <p className="mt-4 font-mono text-sm text-chalk/60">
        <span className="text-[color:var(--spirit-accent-strong)]/85">&gt;</span> awaiting prompt
        … <span className="animate-pulse text-[color:var(--spirit-accent-strong)]">█</span>
      </p>
    </motion.div>
  );

  const header =
    variant === "standalone" && (title ?? subtitle) ? (
      <header className="shrink-0 border-b border-[color:var(--spirit-border)] px-4 py-4 backdrop-blur-xl sm:px-6">
        {title ? (
          <h1 className="font-mono text-xs font-semibold uppercase tracking-[0.2em] text-cyan">
            {title}
          </h1>
        ) : null}
        {subtitle ? (
          <p className="mt-1 font-mono text-[10px] text-chalk/50">{subtitle}</p>
        ) : null}
      </header>
    ) : null;

  const scrollAndForm = (
    <>
      <div className="scrollbar-hide min-h-0 flex-1 space-y-5 overflow-y-auto px-4 py-5 sm:px-5">
        {messages.length === 0 ? (emptyState ?? defaultEmpty) : null}
        {list}
        {isBusy ? (
          <p className="animate-pulse text-sm text-chalk/45">Thinking…</p>
        ) : null}
      </div>
      {error ? (
        <div
          className="mx-4 flex gap-2 border-l-2 border-l-[color:var(--color-rose)]/70 py-2 pl-3 sm:mx-5"
          role="alert"
        >
          <span
            aria-hidden
            className="mt-1 h-2 w-2 shrink-0 rounded-full bg-[color:color-mix(in_oklab,var(--color-rose)_75%,transparent)] shadow-[0_0_12px_color-mix(in_oklab,var(--color-rose)_50%,transparent)]"
          />
          <p className="font-mono text-sm leading-snug text-[color:color-mix(in_oklab,var(--color-rose)_80%,transparent)]">
            Spirit backend error. Check Ollama or /api/spirit.
          </p>
        </div>
      ) : null}
      <form
        onSubmit={onSubmit}
        className={cn(
          "shrink-0 border-t border-[color:var(--spirit-border)]",
          "bg-[color:color-mix(in_oklab,var(--spirit-bg)_72%,transparent)] backdrop-blur-2xl",
          "px-3 py-3 sm:px-5",
          "lg:border-t-0 lg:bg-transparent lg:px-6 lg:pb-6 lg:pt-4",
        )}
        style={{
          paddingBottom: `calc(0.875rem + env(safe-area-inset-bottom, 0px))`,
        }}
      >
        <div
          className={cn(
            "mx-auto flex max-w-3xl gap-2",
            "lg:rounded-full lg:border lg:border-[color:var(--spirit-border)] lg:bg-white/[0.04] lg:px-3 lg:py-2 lg:backdrop-blur-2xl",
            "lg:shadow-[0_18px_56px_-24px_var(--spirit-glow),inset_0_0_0_1px_rgba(255,255,255,0.04)]",
          )}
        >
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask Spirit anything…"
            rows={1}
            aria-label="Message"
            disabled={isBusy}
            className={cn(
              "scrollbar-hide max-h-[10rem] min-h-[52px] flex-1 resize-none px-5 py-[0.875rem] text-[15px] text-chalk transition-[height] duration-150 ease-out",
              "placeholder:text-chalk/40 disabled:opacity-50",
              "rounded-full border border-[color:var(--spirit-border)] bg-black/40",
              "focus:border-[color:color-mix(in_oklab,var(--spirit-accent-strong)_42%,transparent)] focus:outline-none focus:ring-2 focus:ring-[color:color-mix(in_oklab,var(--spirit-accent)_22%,transparent)]",
              "lg:min-h-[44px] lg:rounded-2xl lg:border-transparent lg:bg-transparent lg:px-4 lg:py-3",
              "lg:focus:border-transparent lg:focus:bg-transparent lg:focus:shadow-none lg:focus:ring-0 lg:focus-visible:outline-none",
            )}
            onInput={(e) => {
              const el = e.currentTarget;
              el.style.height = "auto";
              el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
            }}
          />
          <button
            type="submit"
            disabled={isBusy || !input.trim()}
            aria-label="Send"
            className={cn(
              "inline-flex h-11 w-11 shrink-0 touch-manipulation items-center justify-center rounded-full lg:h-10 lg:w-10",
              "border border-[color:color-mix(in_oklab,var(--spirit-accent)_45%,transparent)]",
              "bg-[color:color-mix(in_oklab,var(--spirit-accent)_18%,transparent)]",
              "text-[color:var(--spirit-accent-strong)] transition disabled:cursor-not-allowed disabled:opacity-35",
              hasDraft &&
                !isBusy &&
                "shadow-[0_0_28px_-6px_var(--spirit-glow)] animate-[pulse_2.6s_ease-in-out_infinite]",
            )}
          >
            <ArrowUp className="h-5 w-5" strokeWidth={2.25} aria-hidden />
          </button>
        </div>
        {footerHint ? (
          <div className="mx-auto mt-2 max-w-3xl text-center font-mono text-[10px] text-chalk/45">
            {footerHint}
          </div>
        ) : null}
      </form>
    </>
  );

  if (variant === "embedded") {
    return (
      <div
        className={cn(
          "flex min-h-[55dvh] flex-1 flex-col px-3 pt-3 sm:px-6 sm:pt-4 lg:min-h-0",
          shellClassName,
        )}
      >
        <div className="flex min-h-0 flex-1 flex-col rounded-2xl border border-[color:var(--spirit-border)] bg-white/[0.02] shadow-[inset_0_0_0_1px_rgba(255,255,255,0.03)] backdrop-blur-xl">
          {scrollAndForm}
        </div>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "flex min-h-dvh flex-col bg-[color:var(--spirit-bg)] text-chalk/95",
        shellClassName,
      )}
    >
      {header}
      <div className="flex min-h-0 flex-1 flex-col border-t border-[color:var(--spirit-border)] bg-white/[0.02] backdrop-blur-xl">
        {scrollAndForm}
      </div>
    </div>
  );
});

export const SpiritChat = memo(function SpiritChat(props: SpiritChatProps) {
  return (
    <ClientFailSafe label="spirit-chat">
      <SpiritChatInner {...props} />
    </ClientFailSafe>
  );
});
