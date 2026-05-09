// ── DemoProfilePreview - Spirit profile / personality / memory (visual) ──────
// > Visual-only mock. Real Spirit Profile lives in /chat panel + localStorage.
// > Nothing here writes to localStorage or modifies real personalisation.
import { ChatIcon, ShieldIcon, SparkleIcon, UserIcon } from "./DemoIcons";

const stats = [
  { label: "Curiosity", value: 78 },
  { label: "Directness", value: 92 },
  { label: "Patience", value: 64 },
  { label: "Sass", value: 41 },
];

const modes = [
  { id: "peer", name: "Peer", hint: "Grounded friend" },
  { id: "teacher", name: "Teacher", hint: "Step-by-step" },
  { id: "researcher", name: "Researcher", hint: "Cite-or-die" },
  { id: "brutal", name: "Brutal", hint: "Toxic Grader" },
  { id: "sassy", name: "Sassy", hint: "Off-the-cuff" },
];

const facts = [
  "Builds AI tooling on a sovereign home server",
  "Prefers JetBrains Mono for code; Inter for prose",
  "Lives close to Atlanta · GA timezone",
  "Voice default · ElevenLabs fable · en-GB",
];

export function DemoProfilePreview() {
  return (
    <section
      id="demo-profile"
      className="demo-section"
      aria-labelledby="demo-profile-title"
    >
      <header className="demo-section__header">
        <span className="demo-section__eyebrow">
          <UserIcon size={11} />
          Spirit profile · memory
        </span>
        <h2 id="demo-profile-title" className="demo-section__title">
          Local memory. Editable. Yours.
        </h2>
        <p className="demo-section__lede">
          Personalisation summary, mode tuning, and what Spirit knows. Stored
          locally, edited locally - visualised here as a paper prototype.
        </p>
      </header>

      <div className="demo-grid-2">
        <article
          className="demo-card demo-card--feature"
          aria-label="Spirit profile · mock"
        >
          <div className="demo-profile">
            <header className="demo-profile__head">
              <span className="demo-profile__avatar" aria-hidden="true">
                S
              </span>
              <div>
                <p className="demo-profile__meta-name">Source</p>
                <p className="demo-profile__meta-id">spirit-os · local</p>
              </div>
            </header>

            <div>
              <div className="demo-card__eyebrow">Personality</div>
              <div
                style={{
                  display: "grid",
                  gap: "0.6rem",
                  marginTop: "0.5rem",
                }}
              >
                {stats.map((s) => (
                  <div key={s.label} className="demo-stat">
                    <div className="demo-stat__row">
                      <span>{s.label}</span>
                      <span className="demo-stat__value">{s.value}%</span>
                    </div>
                    <div className="demo-stat__track" aria-hidden="true">
                      <span
                        className="demo-stat__fill"
                        style={{ width: `${s.value}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <hr className="demo-divider" />

            <div>
              <div className="demo-card__eyebrow">Personalisation confidence</div>
              <div
                style={{
                  display: "flex",
                  alignItems: "baseline",
                  gap: "0.6rem",
                  marginTop: "0.4rem",
                }}
              >
                <span
                  style={{
                    fontFamily:
                      "var(--font-jetbrains-mono), ui-monospace, monospace",
                    fontSize: "var(--demo-text-h2)",
                    fontWeight: 600,
                    color: "var(--demo-cyan-strong)",
                  }}
                >
                  74%
                </span>
                <span className="demo-mock-tag">
                  37 of 50 signals captured
                </span>
              </div>
            </div>

            <span className="demo-mock-tag">
              <ShieldIcon size={11} />
              Editable · stored on this device
            </span>
          </div>
        </article>

        <article className="demo-card" aria-label="Modes · mock">
          <div className="demo-card__eyebrow">
            <SparkleIcon size={12} />
            Modes
          </div>
          <h3 className="demo-card__title">Tune the Spirit</h3>
          <p className="demo-card__body">
            Switch personas mid-thread. The active mode badge shows up in the
            workspace · the Researcher mode unlocks verified web search.
          </p>

          <div
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "0.5rem",
              marginTop: "0.5rem",
            }}
          >
            {modes.map((m, i) => (
              <button
                key={m.id}
                type="button"
                className="demo-status-row"
                aria-pressed={i === 0}
                aria-label={`${m.name} mode · ${m.hint}${
                  i === 0 ? " · active" : ""
                }`}
                style={{
                  border: i === 0
                    ? "1px solid color-mix(in oklab, var(--demo-cyan) 38%, transparent)"
                    : undefined,
                  background: i === 0
                    ? "color-mix(in oklab, var(--demo-cyan) 10%, transparent)"
                    : undefined,
                  cursor: "default",
                }}
              >
                <span className="demo-status-row__label">{m.name}</span>
                <span className="demo-status-row__value">{m.hint}</span>
                <span className="demo-status-row__hint">
                  {i === 0 ? "active" : "tap to switch"}
                </span>
              </button>
            ))}
          </div>

          <hr className="demo-divider" />

          <div className="demo-card__eyebrow">
            <ChatIcon size={12} />
            What Spirit knows
          </div>
          <ul
            style={{
              display: "flex",
              flexDirection: "column",
              gap: "0.4rem",
              marginTop: "0.5rem",
              paddingInlineStart: 0,
              listStyle: "none",
            }}
          >
            {facts.map((f) => (
              <li
                key={f}
                style={{
                  display: "flex",
                  gap: "0.5rem",
                  alignItems: "flex-start",
                  fontSize: "var(--demo-text-caption)",
                  color: "var(--demo-text-muted)",
                }}
              >
                <span
                  aria-hidden="true"
                  style={{
                    width: "0.4rem",
                    height: "0.4rem",
                    marginTop: "0.55rem",
                    flexShrink: 0,
                    borderRadius: "50%",
                    background: "var(--demo-cyan-strong)",
                  }}
                />
                <span>{f}</span>
              </li>
            ))}
          </ul>
        </article>
      </div>
    </section>
  );
}

export default DemoProfilePreview;
