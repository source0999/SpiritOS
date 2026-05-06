"use client";

// ── MessageMarkdown - assistant-only markdown (react-markdown + GFM, no raw HTML) ─
import type { Components } from "react-markdown";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { memo, useMemo } from "react";

import { cn } from "@/lib/cn";
import { hydrateDegenerateSourcesMarkdown } from "@/components/chat/hydrate-sources-markdown";
import type { SpiritWebSourcesHeaderPayload } from "@/lib/spirit/spirit-web-sources";

export type MessageMarkdownProps = {
  text: string;
  className?: string;
  /** When set, degenerate `## Sources` stubs are rewritten from server header (Prompt 10B). */
  webSourcesSnapshot?: SpiritWebSourcesHeaderPayload | null;
};

export const MessageMarkdown = memo(function MessageMarkdown({
  text,
  className,
  webSourcesSnapshot,
}: MessageMarkdownProps) {
  const displayText = useMemo(
    () => hydrateDegenerateSourcesMarkdown(text, webSourcesSnapshot ?? null),
    [text, webSourcesSnapshot],
  );

  const components = useMemo<Components>(
    () => ({
      a: ({ href, children, ...rest }) => (
        <a
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          className="font-medium text-[color:var(--spirit-accent-strong)] underline decoration-[color:color-mix(in_oklab,var(--spirit-accent)_55%,transparent)] underline-offset-2 hover:decoration-[color:var(--spirit-accent-strong)]"
          {...rest}
        >
          {children}
        </a>
      ),
      p: ({ children, ...rest }) => (
        <p className="mb-2 max-lg:mb-1.5 max-lg:leading-snug last:mb-0 leading-relaxed" {...rest}>
          {children}
        </p>
      ),
      ul: ({ children, ...rest }) => (
        <ul className="mb-2 list-disc space-y-1 pl-5 last:mb-0" {...rest}>
          {children}
        </ul>
      ),
      ol: ({ children, ...rest }) => (
        <ol className="mb-2 list-decimal space-y-1 pl-5 last:mb-0" {...rest}>
          {children}
        </ol>
      ),
      li: ({ children, ...rest }) => (
        <li className="leading-relaxed" {...rest}>
          {children}
        </li>
      ),
      blockquote: ({ children, ...rest }) => (
        <blockquote
          className="mb-2 border-l-2 border-[color:color-mix(in_oklab,var(--spirit-accent)_45%,transparent)] pl-3 text-chalk/80 last:mb-0"
          {...rest}
        >
          {children}
        </blockquote>
      ),
      pre: ({ children, ...rest }) => (
        <pre
          className="mb-2 max-w-full overflow-x-auto rounded-lg border border-[color:color-mix(in_oklab,var(--spirit-border)_55%,transparent)] bg-black/55 p-3 text-[13px] last:mb-0"
          {...rest}
        >
          {children}
        </pre>
      ),
      code: ({ className: codeClass, children, ...rest }) => {
        const isBlock = Boolean(codeClass?.includes("language-"));
        if (isBlock) {
          return (
            <code
              className={cn(
                "block font-mono text-[13px] leading-relaxed text-chalk/92",
                codeClass,
              )}
              {...rest}
            >
              {children}
            </code>
          );
        }
        return (
          <code
            className={cn(
              "rounded px-1 py-0.5 font-mono text-[13px]",
              "border border-[color:color-mix(in_oklab,var(--spirit-border)_40%,transparent)] bg-black/40 text-[color:color-mix(in_oklab,var(--spirit-accent-strong)_88%,var(--spirit-fg))]",
            )}
            {...rest}
          >
            {children}
          </code>
        );
      },
      strong: ({ children, ...rest }) => (
        <strong className="font-semibold text-chalk" {...rest}>
          {children}
        </strong>
      ),
      em: ({ children, ...rest }) => (
        <em className="italic text-chalk/90" {...rest}>
          {children}
        </em>
      ),
    }),
    [],
  );

  return (
    <div
      className={cn(
        "prose-spirit max-w-none break-words font-sans text-[15px] text-chalk/90 max-lg:text-[16px] max-lg:leading-snug",
        className,
      )}
    >
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={components}>
        {displayText}
      </ReactMarkdown>
    </div>
  );
});
