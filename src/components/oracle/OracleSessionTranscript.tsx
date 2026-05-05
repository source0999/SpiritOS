"use client";

// ── OracleSessionTranscript — live chat rows (UIMessage) for /oracle chamber ─────
// > Uses the same `transport.messages` the runtime already owns — zero fake copy.

import type { UIMessage } from "ai";
import { useMemo } from "react";

import { textFromParts } from "@/lib/chat-utils";

export type OracleSessionTranscriptProps = {
  messages: UIMessage[];
  /** Shown in the footer strip (e.g. “Listening…”, “Thinking…”). */
  activityLine: string;
  className?: string;
};

export function OracleSessionTranscript({
  messages,
  activityLine,
  className = "",
}: OracleSessionTranscriptProps) {
  const rows = useMemo(
    () => messages.filter((m) => m.role === "user" || m.role === "assistant"),
    [messages],
  );

  return (
    <section
      data-testid="oracle-session-transcript"
      aria-label="Oracle session"
      className={`oracle-session ${className}`.trim()}
    >
      <header className="oracle-session__head">Oracle session</header>

      <div className="oracle-session__scroll scrollbar-hide">
        {rows.length === 0 ? (
          <p className="oracle-session__empty">
            No messages yet — start a session and speak, or send text. Conversation from this
            Oracle lane appears here live.
          </p>
        ) : (
          rows.map((m, i) => {
            const text = textFromParts(m).trim();
            const isUser = m.role === "user";
            const slot = String(i + 1).padStart(2, "0");
            return (
              <article
                key={m.id}
                className={`oracle-session__row ${isUser ? "oracle-session__row--user" : ""}`}
              >
                <div className="oracle-session__icon" aria-hidden>
                  {isUser ? (
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                      <path
                        d="M12 12a4 4 0 1 0-4-4 4 4 0 0 0 4 4Z"
                        stroke="currentColor"
                        strokeWidth="1.6"
                      />
                      <path
                        d="M4 21a8 8 0 0 1 16 0"
                        stroke="currentColor"
                        strokeWidth="1.6"
                        strokeLinecap="round"
                      />
                    </svg>
                  ) : (
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none">
                      <path
                        d="M12 3 13.4 7.2 18 8.5l-3.6 2.4L15.5 16 12 13.9 8.5 16l1.1-5.1L6 8.5l4.6-1.3L12 3Z"
                        fill="currentColor"
                        opacity="0.9"
                      />
                    </svg>
                  )}
                </div>
                <div className="oracle-session__meta">
                  <span className="oracle-session__role">{isUser ? "You" : "Oracle"}</span>
                  <span className="oracle-session__time" title="Message order in this session">
                    #{slot}
                  </span>
                </div>
                <p className="oracle-session__body">{text || "…"}</p>
              </article>
            );
          })
        )}
      </div>

      <footer className="oracle-session__foot">
        <div className="oracle-session__foot-meter" aria-hidden>
          <span />
          <span />
          <span />
          <span />
        </div>
        <span className="min-w-0 truncate">{activityLine}</span>
        <span className="oracle-session__foot-info" title="Live lane status" aria-hidden>
          i
        </span>
      </footer>
    </section>
  );
}
