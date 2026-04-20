// ─── Spirit OS · MessageBubble ────────────────────────────────────────────────
//
// Renders a single conversation turn. Handles two distinct modes:
//
//   "complete"  — a finalized, Dexie-persisted message. Spirit messages are
//                 rendered as Markdown (react-markdown). User messages are
//                 plain text in a pill bubble. Acoustic stage directions like
//                 [sighs] are rendered as italic violet spans.
//
//   "streaming" — live token output from useStream. Renders the accumulating
//                 text with parseAcousticMarkers + a trailing StreamingCursor.
//                 react-markdown is intentionally NOT used here because the
//                 Markdown AST cannot be built incrementally — mid-stream the
//                 content is always partial and the parser produces garbage
//                 nodes. Plain text rendering is correct for the streaming phase.
//                 On stream completion the parent swaps this for a "complete"
//                 bubble, which then renders the full Markdown cleanly.
//
// Architecture note (cross-referenced against open-webui MessageItem.svelte):
//   The cursor is a child component, not a CSS ::after pseudo-element, so React
//   unmounts it atomically when `isStreaming` flips to false. This eliminates
//   the 1-frame cursor flicker that occurs when a pseudo-element outlives its
//   parent's re-render cycle.
//
// ─────────────────────────────────────────────────────────────────────────────

"use client";

import ReactMarkdown from "react-markdown";
import type { Message } from "@/lib/db.types";
import { StreamingCursor } from "./StreamingCursor";

function cn(...classes: (string | undefined | false | null)[]) {
  return classes.filter(Boolean).join(" ");
}

// ── Acoustic Marker Parser ────────────────────────────────────────────────────
//
// Splits a plain-text string on XTTS v2 stage directions ([sighs], [groan], etc.)
// and returns a mixed array of strings and styled <span> elements.
// Used during STREAMING only (where react-markdown is not active).
//
function parseAcousticMarkers(text: string): (string | React.ReactElement)[] {
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

const MD_COMPONENTS: React.ComponentProps<typeof ReactMarkdown>["components"] = {
  p: ({ children }) => (
    <p className="mb-3 last:mb-0 leading-relaxed">{children}</p>
  ),
  code: ({ children, className }) => {
    const isBlock = className?.startsWith("language-");
    if (isBlock) {
      return <code className={className}>{children}</code>;
    }
    return (
      <code className="rounded-md border border-violet-500/20 bg-violet-500/10 px-1.5 py-0.5 font-mono text-[0.8em] text-violet-300">
        {children}
      </code>
    );
  },
  pre: ({ children }) => (
    <pre className="my-3 overflow-x-auto rounded-xl border border-white/[0.07] bg-zinc-900 p-4 font-mono text-xs leading-relaxed text-zinc-200">
      {children}
    </pre>
  ),
  strong: ({ children }) => (
    <strong className="font-semibold text-zinc-100">{children}</strong>
  ),
  em: ({ children }) => (
    <em className="italic text-violet-300/80">{children}</em>
  ),
  ul: ({ children }) => (
    <ul className="mb-3 ml-4 list-disc space-y-1 last:mb-0">{children}</ul>
  ),
  ol: ({ children }) => (
    <ol className="mb-3 ml-4 list-decimal space-y-1 last:mb-0">{children}</ol>
  ),
  li: ({ children }) => (
    <li className="leading-relaxed text-zinc-300">{children}</li>
  ),
  blockquote: ({ children }) => (
    <blockquote className="my-3 border-l-2 border-violet-500/40 pl-4 italic text-zinc-400">
      {children}
    </blockquote>
  ),
  h1: ({ children }) => (
    <h1 className="mb-3 mt-4 font-mono text-base font-bold text-zinc-100 first:mt-0">
      {children}
    </h1>
  ),
  h2: ({ children }) => (
    <h2 className="mb-2 mt-4 font-mono text-sm font-semibold text-zinc-100 first:mt-0">
      {children}
    </h2>
  ),
  h3: ({ children }) => (
    <h3 className="mb-2 mt-3 font-mono text-sm font-medium text-zinc-200 first:mt-0">
      {children}
    </h3>
  ),
  hr: () => <hr className="my-4 border-white/[0.07]" />,
  a: ({ href, children }) => (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="text-violet-400 underline underline-offset-2 hover:text-violet-300"
    >
      {children}
    </a>
  ),
};

interface CompleteBubbleProps {
  mode: "complete";
  message: Message;
}

interface StreamingBubbleProps {
  mode: "streaming";
  text: string;
}

type MessageBubbleProps = CompleteBubbleProps | StreamingBubbleProps;

export function MessageBubble(props: MessageBubbleProps) {
  if (props.mode === "streaming") {
    const { text } = props;
    return (
      <div className="flex flex-col items-start">
        <p className="mb-1.5 text-[10px] font-semibold uppercase tracking-widest text-zinc-600">
          Spirit
        </p>
        <div className="max-w-[90%] break-words font-mono text-sm leading-relaxed text-zinc-300 sm:max-w-2xl">
          {text ? (
            <>
              {parseAcousticMarkers(text)}
              <StreamingCursor />
            </>
          ) : (
            <span className="text-zinc-500">
              <span className="italic text-violet-500/60">[processing]</span>{" "}
              <StreamingCursor />
            </span>
          )}
        </div>
      </div>
    );
  }

  const { message: msg } = props;
  const isUser = msg.role === "user";

  return (
    <div className={cn("flex flex-col", isUser ? "items-end" : "items-start")}>
      <p className="mb-1.5 text-[10px] font-semibold uppercase tracking-widest text-zinc-600">
        {isUser ? "Source" : "Spirit"}
      </p>

      {isUser ? (
        <div className="max-w-[85%] break-words rounded-2xl rounded-tr-sm border border-white/[0.07] bg-zinc-900 px-4 py-3 text-sm leading-relaxed text-zinc-100 sm:max-w-xl">
          {msg.text}
        </div>
      ) : (
        <div className="max-w-[90%] break-words font-mono text-sm leading-relaxed text-zinc-300 sm:max-w-2xl">
          <ReactMarkdown components={MD_COMPONENTS}>
            {msg.text}
          </ReactMarkdown>
        </div>
      )}

      <p className="mt-1.5 text-[10px] text-zinc-700">{msg.ts}</p>
    </div>
  );
}
