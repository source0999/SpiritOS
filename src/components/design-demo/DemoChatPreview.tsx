// ── DemoChatPreview - visual preview of /chat workspace ──────────────────────
// > Visual-only. Real chat lives in /chat (untouched). All bubbles, modes,
// > pinned threads, and folders are static mock content.
import Link from "next/link";

import { ArrowRightIcon, ChatIcon, MicIcon, SparkleIcon } from "./DemoIcons";

const folders = [
  {
    name: "Pinned",
    threads: [
      { title: "Sovereign hosting plan", active: true, pinned: true },
      { title: "Whisper latency tuning", pinned: true },
    ],
  },
  {
    name: "Today",
    threads: [
      { title: "Bento layout brainstorm" },
      { title: "Oracle prompt drift audit" },
      { title: "ElevenLabs voice swap" },
    ],
  },
  {
    name: "Yesterday",
    threads: [
      { title: "Refactor: chat folder utils" },
      { title: "Hermes routing rules" },
    ],
  },
];

export function DemoChatPreview() {
  return (
    <section
      id="demo-chat"
      className="demo-section"
      aria-labelledby="demo-chat-title"
    >
      <header className="demo-section__header">
        <span className="demo-section__eyebrow">
          <ChatIcon size={11} />
          Chat workspace · preview
        </span>
        <h2 id="demo-chat-title" className="demo-section__title">
          A transcript with a memory.
        </h2>
        <p className="demo-section__lede">
          Saved threads, folders, modes - the real version lives at{" "}
          <Link
            href="/chat"
            className="demo-btn demo-btn--ghost demo-btn--sm"
            style={{ marginInline: "0.25rem" }}
          >
            /chat <ArrowRightIcon size={11} />
          </Link>
          . What you see here is paper-prototype scaffolding.
        </p>
      </header>

      <div className="demo-chat-split">
        {/* - -  Sidebar rail (mock thread list) - -  */}
        <aside
          className="demo-card demo-card--feature"
          aria-label="Saved threads · mock"
          style={{ minHeight: "24rem" }}
        >
          <div className="demo-chat-rail">
            <header className="demo-chat-rail__head">
              <span className="demo-card__eyebrow">
                <span className="demo-pulse-dot" aria-hidden="true" />
                128 threads
              </span>
              <span className="demo-mock-tag">Mock</span>
            </header>

            <input
              type="search"
              placeholder="Search chats…"
              aria-label="Search chats (demo)"
              className="demo-chat-composer__field"
              style={{
                width: "100%",
                padding: "0.55rem 0.75rem",
                border: "1px solid var(--demo-border)",
                borderRadius: "var(--demo-radius-sm)",
                background: "var(--demo-glass-soft)",
                color: "var(--demo-text-muted)",
              }}
              defaultValue=""
              readOnly
            />

            {folders.map((folder) => (
              <div className="demo-chat-rail__group" key={folder.name}>
                <span className="demo-chat-rail__folder">{folder.name}</span>
                {folder.threads.map((thread) => (
                  <div
                    key={thread.title}
                    className={`demo-chat-rail__thread${
                      "active" in thread && thread.active
                        ? " demo-chat-rail__thread--active"
                        : ""
                    }`}
                  >
                    {"pinned" in thread && thread.pinned ? (
                      <span
                        className="demo-chat-rail__thread-pin"
                        aria-hidden="true"
                      />
                    ) : (
                      <span style={{ width: 6, flexShrink: 0 }} aria-hidden />
                    )}
                    <span className="demo-chat-rail__thread-title">
                      {thread.title}
                    </span>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </aside>

        {/* - -  Chat pane (mock conversation) - -  */}
        <div
          className="demo-card"
          aria-label="Conversation · mock"
          style={{ minHeight: "24rem" }}
        >
          <div className="demo-chat-pane">
            <header className="demo-chat-modebar">
              <div
                style={{
                  display: "flex",
                  flexWrap: "wrap",
                  gap: "0.4rem",
                  alignItems: "center",
                }}
              >
                <span className="demo-badge demo-badge--cyan">Mode · Peer</span>
                <span className="demo-badge">Grounded friend</span>
              </div>
              <div style={{ display: "flex", gap: "0.4rem" }}>
                <span className="demo-badge demo-badge--emerald">
                  <span className="demo-pulse-dot" aria-hidden="true" />
                  Streaming
                </span>
                <span className="demo-badge demo-badge--violet">
                  <MicIcon size={10} />
                  TTS · ready
                </span>
              </div>
            </header>

            <div className="demo-chat-stream">
              <div className="demo-bubble demo-bubble--user">
                <p className="demo-bubble__role">You</p>
                <p>
                  How should I think about Whisper latency vs accuracy when
                  the ambient room is loud?
                </p>
              </div>
              <div className="demo-bubble demo-bubble--spirit">
                <p className="demo-bubble__role">Spirit</p>
                <p>
                  Cap your decoding window first - anything over 8 seconds
                  hurts perceived latency more than accuracy buys you. Then
                  trade the smallest model that still recovers proper nouns.
                  Most rooms answer that with <code>medium.en</code> on the
                  CPU pool plus a 0.6 silence floor.
                  <span className="demo-motion-caret" aria-hidden="true">
                    {" "}
                    ▍
                  </span>
                </p>
              </div>
              <div className="demo-bubble demo-bubble--user">
                <p className="demo-bubble__role">You</p>
                <p>And if I want to keep the mic open in hands-free?</p>
              </div>
            </div>

            <div className="demo-chat-composer">
              <input
                type="text"
                placeholder="Type a message… (demo)"
                aria-label="Message Spirit (demo composer)"
                className="demo-chat-composer__field"
                readOnly
                defaultValue=""
              />
              <span
                className="demo-btn demo-btn--primary demo-btn--sm"
                aria-hidden="true"
              >
                Send
              </span>
            </div>

            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                gap: "0.5rem",
                flexWrap: "wrap",
              }}
            >
              <span className="demo-mock-tag">
                Real functionality lives in /chat
              </span>
              <Link
                href="/chat"
                className="demo-btn demo-btn--ghost demo-btn--sm"
                aria-label="Open chat (real route)"
              >
                <span>Open chat</span>
                <ArrowRightIcon size={11} />
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* - -  Workflow strip (visualizer mock) - -  */}
      <div
        className="demo-glass demo-card demo-motion-fade-up"
        style={{ marginTop: "1.25rem" }}
        aria-label="Workflow visualizer · mock"
      >
        <div className="demo-card__eyebrow">
          <SparkleIcon size={12} />
          Workflow · idle
        </div>
        <div
          style={{
            display: "flex",
            flexWrap: "wrap",
            gap: "0.4rem",
            alignItems: "center",
          }}
        >
          <span className="demo-badge demo-badge--cyan">Plan</span>
          <span style={{ color: "var(--demo-text-faint)" }}>→</span>
          <span className="demo-badge demo-badge--violet">Search</span>
          <span style={{ color: "var(--demo-text-faint)" }}>→</span>
          <span className="demo-badge demo-badge--cyan">Synthesize</span>
          <span style={{ color: "var(--demo-text-faint)" }}>→</span>
          <span className="demo-badge demo-badge--emerald">Cite</span>
        </div>
      </div>
    </section>
  );
}

export default DemoChatPreview;
