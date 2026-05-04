// ── DemoCommandCenter — hero command surface (visual-only) ───────────────────
// > Quick-launch CTAs link to existing real routes (/chat, /oracle, /quarantine)
// > because those routes are already shipped. Other CTAs are clearly labeled
// > demo and do not navigate; nothing here wires unfinished features.
import type { ReactElement } from "react";
import Link from "next/link";

import {
  ActivityIcon,
  ArrowRightIcon,
  ChatIcon,
  FlaskIcon,
  OrbIcon,
  ShieldIcon,
  SparkleIcon,
  UserIcon,
} from "./DemoIcons";

type QuickLaunch = {
  label: string;
  description: string;
  href?: string; // present → real route; absent → demo-only
  tone: "cyan" | "violet" | "rose" | "neutral";
  Icon: (props: { size?: number }) => ReactElement;
};

const launches: QuickLaunch[] = [
  {
    label: "Open Chat",
    description: "Saved threads, folders, modes — the canonical workspace.",
    href: "/chat",
    tone: "cyan",
    Icon: ChatIcon,
  },
  {
    label: "Open Oracle",
    description: "Hands-free voice loop · listen → think → speak.",
    href: "/oracle",
    tone: "violet",
    Icon: OrbIcon,
  },
  {
    label: "Enter Quarantine",
    description: "Experimental lane · containment for noisy ideas.",
    href: "/quarantine",
    tone: "rose",
    Icon: FlaskIcon,
  },
  {
    label: "Review Memory",
    description: "Spirit profile, modes, personalisation confidence.",
    tone: "neutral",
    Icon: UserIcon,
  },
  {
    label: "Diagnostics",
    description: "Ollama, Hermes, Whisper, TTS — runtime telemetry.",
    tone: "neutral",
    Icon: ActivityIcon,
  },
  {
    label: "Sigil Lab",
    description: "Future surface · sigils, agents, terminal mode.",
    tone: "neutral",
    Icon: SparkleIcon,
  },
];

function LaunchCard({ item }: { item: QuickLaunch }) {
  const { label, description, href, Icon, tone } = item;
  const toneClass =
    tone === "cyan"
      ? "demo-card--feature"
      : tone === "violet"
      ? "demo-card--oracle"
      : tone === "rose"
      ? "demo-card--quarantine"
      : "";

  const eyebrow =
    tone === "cyan"
      ? "Workspace"
      : tone === "violet"
      ? "Oracle"
      : tone === "rose"
      ? "Lab"
      : "System";

  const inner = (
    <>
      <div className="demo-card__eyebrow">
        <Icon size={12} />
        <span>{eyebrow}</span>
      </div>
      <h3 className="demo-card__title">{label}</h3>
      <p className="demo-card__body">{description}</p>
      <div className="demo-card__footer">
        {href ? (
          <span
            className={`demo-btn demo-btn--sm ${
              tone === "violet"
                ? "demo-btn--violet"
                : tone === "rose"
                ? "demo-btn--rose"
                : "demo-btn--primary"
            }`}
          >
            <span>Open</span>
            <ArrowRightIcon size={12} />
          </span>
        ) : (
          <span className="demo-mock-tag">Demo · not wired</span>
        )}
      </div>
    </>
  );

  if (href) {
    return (
      <Link
        href={href}
        className={`demo-card ${toneClass}`}
        aria-label={`${label} — open route`}
      >
        {inner}
      </Link>
    );
  }
  return (
    <article
      className={`demo-card ${toneClass}`}
      aria-label={`${label} — visual only`}
    >
      {inner}
    </article>
  );
}

export function DemoCommandCenter() {
  return (
    <section
      id="demo-command-center"
      className="demo-section"
      aria-labelledby="demo-command-center-title"
    >
      <header className="demo-section__header">
        <span className="demo-section__eyebrow">
          <span className="demo-pulse-dot" aria-hidden="true" />
          Command surface
        </span>
        <h2
          id="demo-command-center-title"
          className="demo-section__title"
        >
          A console that listens, not a dashboard.
        </h2>
        <p className="demo-section__lede">
          Everything below is a visual rehearsal — a place to feel the OS
          before we wire any of it. The three quick-launch cards link into
          existing routes; the rest are demo-only surfaces awaiting review.
        </p>
      </header>

      {/* —— Hero panel with title + status + actions —— */}
      <article
        className="demo-hero demo-motion-fade-up"
        aria-label="Spirit OS hero status"
      >
        <span className="demo-shimmer" aria-hidden="true" />

        <div className="demo-hero__head">
          <div className="demo-badge demo-badge--cyan">
            <span className="demo-pulse-dot" aria-hidden="true" />
            Mode · Peer
          </div>
          <div className="demo-badge demo-badge--violet">
            <SparkleIcon size={10} />
            Hermes online
          </div>
        </div>

        <div>
          <p className="demo-section__eyebrow" style={{ color: "inherit" }}>
            <ShieldIcon size={11} />
            Sovereign · local-first
          </p>
          <h1 className="demo-hero__title">
            Spirit OS — <em>cybernetic</em> command center.
          </h1>
          <p className="demo-hero__sub">
            Hermes locally on Ollama. Whisper for ears, ElevenLabs / Piper for
            voice. Memory stays on the device. This rehearsal screen shows the
            shape; the real lanes already work.
          </p>
        </div>

        <div className="demo-hero__ctas">
          <Link
            href="/chat"
            className="demo-btn demo-btn--primary"
            aria-label="Start chat (real route)"
          >
            <ChatIcon size={14} />
            <span>Start chat</span>
          </Link>
          <Link
            href="/oracle"
            className="demo-btn demo-btn--violet"
            aria-label="Open Oracle (real route)"
          >
            <OrbIcon size={14} />
            <span>Open Oracle</span>
          </Link>
          <Link
            href="/quarantine"
            className="demo-btn demo-btn--rose"
            aria-label="Enter Quarantine (real route)"
          >
            <FlaskIcon size={14} />
            <span>Enter Quarantine</span>
          </Link>
        </div>

        {/* Decorative cinematic corner marks */}
        <span className="demo-corners" aria-hidden="true" />
      </article>

      {/* —— Telemetry strip (mock data) —— */}
      <div
        className="demo-grid-4"
        style={{ marginTop: "1.5rem" }}
        aria-label="System telemetry (mock values)"
      >
        <article className="demo-stat-tile demo-motion-fade-up demo-motion-fade-up--delay-1">
          <span className="demo-stat-tile__label">Hermes</span>
          <span className="demo-stat-tile__value">142ms</span>
          <span className="demo-stat-tile__hint">first token · cyan lane</span>
        </article>
        <article className="demo-stat-tile demo-motion-fade-up demo-motion-fade-up--delay-2">
          <span className="demo-stat-tile__label">Voice</span>
          <span className="demo-stat-tile__value">eleven · fable</span>
          <span className="demo-stat-tile__hint">en-GB · medium</span>
        </article>
        <article className="demo-stat-tile demo-motion-fade-up demo-motion-fade-up--delay-3">
          <span className="demo-stat-tile__label">Memory</span>
          <span className="demo-stat-tile__value">37 / 50</span>
          <span className="demo-stat-tile__hint">Spirit profile saturation</span>
        </article>
        <article className="demo-stat-tile demo-motion-fade-up demo-motion-fade-up--delay-4">
          <span className="demo-stat-tile__label">Threads</span>
          <span className="demo-stat-tile__value">128</span>
          <span className="demo-stat-tile__hint">Dexie · local only</span>
        </article>
      </div>

      {/* —— Quick launch grid —— */}
      <h3
        className="demo-section__title"
        style={{
          fontSize: "var(--demo-text-h3)",
          marginTop: "2rem",
          marginBottom: "1rem",
        }}
      >
        Quick launch
      </h3>
      <div className="demo-grid-3" aria-label="Quick launch cards">
        {launches.map((item, i) => (
          <div
            key={item.label}
            className={`demo-motion-fade-up demo-motion-fade-up--delay-${
              Math.min(i + 1, 5)
            }`}
          >
            <LaunchCard item={item} />
          </div>
        ))}
      </div>
    </section>
  );
}

export default DemoCommandCenter;
