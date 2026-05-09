// ── DemoDiagnosticsPreview - runtime telemetry cards (mock data) ─────────────
// > Visual-only. Does NOT call /api/spirit/health or any other real endpoint.
// > The real diagnostics surface lives in the dashboard rail and is untouched.
import { ActivityIcon, MicIcon, OrbIcon, SparkleIcon } from "./DemoIcons";

type Diag = {
  name: string;
  detail: string;
  state: "online" | "warn" | "offline";
  hint: string;
};

const diagnostics: Diag[] = [
  {
    name: "Ollama runtime",
    detail: "ollama:rocm · gfx803 · 32 GB",
    state: "online",
    hint: "spirit-os · 8B · loaded",
  },
  {
    name: "Hermes router",
    detail: "first-token · p95 · 142ms",
    state: "online",
    hint: "cyan lane · streaming",
  },
  {
    name: "Oracle voice loop",
    detail: "hands-free · idle",
    state: "online",
    hint: "1200ms VAD · 0.035 floor",
  },
  {
    name: "Whisper STT",
    detail: "small.en · CPU pool",
    state: "warn",
    hint: "P95 transcribe · 980ms",
  },
  {
    name: "ElevenLabs TTS",
    detail: "fable · en-GB · medium",
    state: "online",
    hint: "fallback · piper alba",
  },
  {
    name: "Web search",
    detail: "openai · researcher only",
    state: "online",
    hint: "verified-http · 2 sources",
  },
  {
    name: "Local memory",
    detail: "Dexie · spirit-os.chat-db",
    state: "online",
    hint: "128 threads · 7 folders",
  },
  {
    name: "Source scan",
    detail: "research-source-enforcement",
    state: "warn",
    hint: "1 unverified URL skipped",
  },
];

const stateClasses: Record<Diag["state"], string> = {
  online: "demo-pulse-dot",
  warn: "demo-pulse-dot demo-pulse-dot--warn",
  offline: "demo-pulse-dot demo-pulse-dot--rose",
};

const stateLabels: Record<Diag["state"], string> = {
  online: "Online",
  warn: "Warn",
  offline: "Offline",
};

const stateBadges: Record<Diag["state"], string> = {
  online: "demo-badge--emerald",
  warn: "demo-badge--warn",
  offline: "demo-badge--rose",
};

export function DemoDiagnosticsPreview() {
  return (
    <section
      id="demo-diagnostics"
      className="demo-section"
      aria-labelledby="demo-diagnostics-title"
    >
      <header className="demo-section__header">
        <span className="demo-section__eyebrow">
          <ActivityIcon size={11} />
          Diagnostics · runtime
        </span>
        <h2
          id="demo-diagnostics-title"
          className="demo-section__title"
        >
          Telemetry without the seance.
        </h2>
        <p className="demo-section__lede">
          One tile per surface. Mock values - no real polling - so reviewers
          can read the layout without thinking about probe traffic.
        </p>
      </header>

      <div className="demo-grid-4" aria-label="Diagnostics tiles · mock">
        {diagnostics.map((d, i) => (
          <article
            key={d.name}
            className={`demo-diag demo-motion-fade-up demo-motion-fade-up--delay-${
              Math.min(i + 1, 5)
            }`}
            aria-label={`${d.name} · ${stateLabels[d.state]} · ${d.detail}`}
          >
            <header className="demo-diag__head">
              <span className="demo-diag__name">{d.name}</span>
              <span className={stateClasses[d.state]} aria-hidden="true" />
            </header>
            <p className="demo-diag__detail">{d.detail}</p>
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: "0.5rem",
              }}
            >
              <span className={`demo-badge ${stateBadges[d.state]}`}>
                {stateLabels[d.state]}
              </span>
              <span
                style={{
                  fontFamily:
                    "var(--font-jetbrains-mono), ui-monospace, monospace",
                  fontSize: "var(--demo-text-eyebrow)",
                  letterSpacing: "0.04em",
                  color: "var(--demo-text-faint)",
                  textAlign: "right",
                }}
              >
                {d.hint}
              </span>
            </div>
          </article>
        ))}
      </div>

      {/* - -  Voice + STT detail row - -  */}
      <div className="demo-grid-2" style={{ marginTop: "1.25rem" }}>
        <article
          className="demo-card"
          aria-label="Voice provider · mock"
        >
          <div className="demo-card__eyebrow">
            <MicIcon size={12} />
            Voice provider
          </div>
          <h3 className="demo-card__title">ElevenLabs · fable</h3>
          <p className="demo-card__body">
            Primary TTS for chat + Oracle. Piper en-GB Alba is the local
            fallback when ElevenLabs is unavailable.
          </p>
          <div className="demo-status-row">
            <span className="demo-status-row__label">Latency</span>
            <span className="demo-status-row__value">312 ms</span>
            <span className="demo-status-row__hint">
              first-byte · cloud edge
            </span>
          </div>
          <div className="demo-status-row">
            <span className="demo-status-row__label">Format</span>
            <span className="demo-status-row__value">mp3 · 44.1 kHz</span>
            <span className="demo-status-row__hint">eleven_turbo_v2_5</span>
          </div>
        </article>

        <article
          className="demo-card"
          aria-label="STT provider · mock"
        >
          <div className="demo-card__eyebrow">
            <OrbIcon size={12} />
            STT provider
          </div>
          <h3 className="demo-card__title">Whisper · small.en</h3>
          <p className="demo-card__body">
            Local CPU pool with optional cloud fallback. Whisper headers stamp
            duration on every transcript for budget-aware downstream UI.
          </p>
          <div className="demo-status-row">
            <span className="demo-status-row__label">P95</span>
            <span className="demo-status-row__value">980 ms</span>
            <span className="demo-status-row__hint">3-second utterance</span>
          </div>
          <div className="demo-status-row">
            <span className="demo-status-row__label">Floor</span>
            <span className="demo-status-row__value">0.035</span>
            <span className="demo-status-row__hint">amplitude VAD</span>
          </div>
        </article>
      </div>

      <p style={{ marginTop: "1rem" }}>
        <span className="demo-mock-tag">
          <SparkleIcon size={11} /> Demo values · live diagnostics live in the
          dashboard rail
        </span>
      </p>
    </section>
  );
}

export default DemoDiagnosticsPreview;
