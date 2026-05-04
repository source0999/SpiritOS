// ── DemoOraclePreview — orb + listening cycle visual (no real mic) ───────────
// > Visual-only. The real Oracle voice loop lives in /oracle and is untouched.
// > MediaRecorder, Whisper, TTS, AnalyserNode — none are touched here.
import Link from "next/link";

import { DemoMotionOrb } from "./DemoMotionOrb";
import {
  ArrowRightIcon,
  MicIcon,
  OrbIcon,
  PauseIcon,
  PlayIcon,
} from "./DemoIcons";

const cycle = [
  { phase: "Listening", value: "78%", hint: "amplitude · live" },
  { phase: "Transcribing", value: "Whisper", hint: "small.en · CPU pool" },
  { phase: "Thinking", value: "Hermes", hint: "first-token · 142ms" },
  { phase: "Speaking", value: "ElevenLabs", hint: "fable · en-GB" },
];

export function DemoOraclePreview() {
  return (
    <section
      id="demo-oracle"
      className="demo-section"
      aria-labelledby="demo-oracle-title"
    >
      <header className="demo-section__header">
        <span className="demo-section__eyebrow">
          <OrbIcon size={11} />
          Oracle voice · preview
        </span>
        <h2 id="demo-oracle-title" className="demo-section__title">
          Listening, thinking, speaking — as one breath.
        </h2>
        <p className="demo-section__lede">
          Hands-free voice loop visual rehearsal. The real loop —
          MediaRecorder, amplitude VAD, Whisper, ElevenLabs — runs at{" "}
          <Link
            href="/oracle"
            className="demo-btn demo-btn--ghost demo-btn--sm"
            style={{ marginInline: "0.25rem" }}
          >
            /oracle <ArrowRightIcon size={11} />
          </Link>
          . Here we just show the shape.
        </p>
      </header>

      <div className="demo-oracle-split">
        {/* —— Orb stage —— */}
        <article
          className="demo-card demo-card--oracle"
          aria-label="Oracle orb stage · visual"
          style={{
            display: "flex",
            flexDirection: "column",
            gap: "1.25rem",
            justifyContent: "space-between",
            position: "relative",
            minHeight: "22rem",
          }}
        >
          <span className="demo-shimmer" aria-hidden="true" />

          <div
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
              gap: "0.5rem",
              flexWrap: "wrap",
            }}
          >
            <span className="demo-card__eyebrow">
              <span className="demo-pulse-dot" aria-hidden="true" />
              Hands-free · listening
            </span>
            <span className="demo-badge demo-badge--violet">
              session · 02:14
            </span>
          </div>

          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              gap: "1rem",
              flex: 1,
            }}
          >
            <DemoMotionOrb />
            <p
              style={{
                fontFamily:
                  "var(--font-jetbrains-mono), ui-monospace, monospace",
                fontSize: "var(--demo-text-eyebrow)",
                letterSpacing: "var(--demo-tracking-rail)",
                textTransform: "uppercase",
                color: "var(--demo-text-faint)",
              }}
            >
              Ambient resonance · no audio wired
            </p>
          </div>

          {/* Mock waveform — the visual proxy for the live audio meter */}
          <div className="demo-wave" aria-hidden="true">
            {Array.from({ length: 16 }).map((_, i) => (
              <span key={i} className="demo-wave__bar" />
            ))}
          </div>

          <div
            style={{
              display: "flex",
              gap: "0.4rem",
              flexWrap: "wrap",
              justifyContent: "center",
            }}
          >
            <span className="demo-btn demo-btn--violet">
              <MicIcon size={14} />
              Stop session
            </span>
            <span className="demo-btn demo-btn--ghost">
              <PauseIcon size={14} />
              Finish now
            </span>
          </div>

          <span className="demo-corners" aria-hidden="true" />
        </article>

        {/* —— Telemetry / device card —— */}
        <article
          className="demo-card"
          aria-label="Oracle telemetry · mock"
          style={{ minHeight: "22rem" }}
        >
          <div className="demo-card__eyebrow">
            <PlayIcon size={11} />
            Loop status
          </div>

          <div>
            {cycle.map((row) => (
              <div
                key={row.phase}
                className="demo-status-row"
                aria-label={`${row.phase} · ${row.value} · ${row.hint}`}
              >
                <span className="demo-status-row__label">{row.phase}</span>
                <span className="demo-status-row__value">{row.value}</span>
                <span className="demo-status-row__hint">{row.hint}</span>
              </div>
            ))}
          </div>

          <hr className="demo-divider" />

          <div className="demo-card__eyebrow">Input device</div>
          <div className="demo-status-row">
            <span className="demo-status-row__label">Mic</span>
            <span className="demo-status-row__value">
              MacBook Air microphone
            </span>
            <span className="demo-status-row__hint">default</span>
          </div>
          <div className="demo-status-row">
            <span className="demo-status-row__label">Silence</span>
            <span className="demo-status-row__value">1200ms</span>
            <span className="demo-status-row__hint">VAD threshold</span>
          </div>
          <div className="demo-status-row">
            <span className="demo-status-row__label">Sensitivity</span>
            <span className="demo-status-row__value">0.035</span>
            <span className="demo-status-row__hint">amplitude floor</span>
          </div>

          <div className="demo-card__footer">
            <span className="demo-mock-tag">
              Real Oracle loop lives in /oracle
            </span>
            <Link
              href="/oracle"
              className="demo-btn demo-btn--violet demo-btn--sm"
              aria-label="Open Oracle (real route)"
            >
              <span>Open Oracle</span>
              <ArrowRightIcon size={11} />
            </Link>
          </div>
        </article>
      </div>
    </section>
  );
}

export default DemoOraclePreview;
