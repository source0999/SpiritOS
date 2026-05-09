import React, { useMemo, useState } from "react";

type SpiritState = "idle" | "listening" | "thinking" | "speaking" | "error";
type IconName = "mic" | "spark" | "voice" | "wave" | "user" | "settings" | "external" | "lock" | "check" | "warn";

const PREVIEW_STATES: Array<{ id: SpiritState; label: string; pill: string }> = [
  { id: "idle", label: "Idle", pill: "Ready" },
  { id: "listening", label: "Listening", pill: "Mic live" },
  { id: "thinking", label: "Thinking", pill: "Processing" },
  { id: "speaking", label: "Speaking", pill: "Speaking" },
  { id: "error", label: "Signal Drift", pill: "Check signal" },
];

const SPECS = [
  ["Secure context", "OK"],
  ["Mic capability", "Available"],
  ["STT", "Whisper backend"],
  ["TTS", "/api/tts"],
  ["Runtime", "Oracle"],
  ["Model", "hermes4"],
];

function cx(...classes: Array<string | false | null | undefined>) {
  return classes.filter(Boolean).join(" ");
}

function Icon({ name, className = "" }: { name: IconName; className?: string }) {
  const common = {
    className,
    viewBox: "0 0 24 24",
    fill: "none",
    stroke: "currentColor",
    strokeWidth: 2,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
    "aria-hidden": true,
  };

  return (
    <svg {...common}>
      {name === "mic" && <><path d="M12 3a3 3 0 0 0-3 3v6a3 3 0 0 0 6 0V6a3 3 0 0 0-3-3Z" /><path d="M19 10v2a7 7 0 0 1-14 0v-2" /><path d="M12 19v3" /><path d="M8 22h8" /></>}
      {name === "spark" && <><path d="M12 3l1.35 4.15L17.5 8.5l-4.15 1.35L12 14l-1.35-4.15L6.5 8.5l4.15-1.35L12 3Z" /><path d="M19 14l.8 2.2L22 17l-2.2.8L19 20l-.8-2.2L16 17l2.2-.8L19 14Z" /></>}
      {name === "voice" && <><path d="M4 9v6h4l5 4V5L8 9H4Z" /><path d="M16 9.5a4 4 0 0 1 0 5" /><path d="M18.5 7a8 8 0 0 1 0 10" /></>}
      {name === "wave" && <><path d="M4 12h2" /><path d="M8 8v8" /><path d="M12 5v14" /><path d="M16 9v6" /><path d="M20 11v2" /></>}
      {name === "user" && <><circle cx="12" cy="8" r="3.5" /><path d="M4.5 21a7.5 7.5 0 0 1 15 0" /></>}
      {name === "settings" && <><circle cx="12" cy="12" r="3" /><path d="M4 12h2m12 0h2M12 4v2m0 12v2M6.6 6.6 8 8m8 8 1.4 1.4M17.4 6.6 16 8m-8 8-1.4 1.4" /></>}
      {name === "external" && <><path d="M7 17 17 7" /><path d="M9 7h8v8" /><path d="M19 19H5V5" /></>}
      {name === "lock" && <><rect x="5" y="10" width="14" height="10" rx="2" /><path d="M8 10V7a4 4 0 0 1 8 0v3" /></>}
      {name === "check" && <path d="M5 12l4 4L19 6" />}
      {name === "warn" && <><path d="M10.3 4.2 2.8 17a2 2 0 0 0 1.7 3h15a2 2 0 0 0 1.7-3L13.7 4.2a2 2 0 0 0-3.4 0Z" /><path d="M12 9v4" /><path d="M12 17h.01" /></>}
    </svg>
  );
}

function OracleSprite({ state = "idle", size = "large" }: { state?: SpiritState; size?: "small" | "medium" | "large" }) {
  const motes = useMemo(
    () =>
      Array.from({ length: size === "small" ? 14 : 28 }, (_, i) => ({
        id: i,
        cx: 160 + Math.sin(i * 1.31) * (size === "small" ? 86 : 118),
        cy: 154 + Math.cos(i * 1.77) * (size === "small" ? 66 : 96),
        r: 1.15 + (i % 4) * 0.7,
        delay: `${(i % 10) * 0.18}s`,
      })),
    [size],
  );

  return (
    <div className={cx("spriteShell", `sprite-${size}`, `spriteState-${state}`)} aria-label="Abstract glowing Oracle sprite">
      <svg className="spriteSvg" viewBox="0 0 320 320" role="img">
        <defs>
          <radialGradient id="orbCore" cx="42%" cy="35%" r="65%">
            <stop offset="0%" stopColor="#ffffff" />
            <stop offset="18%" stopColor="#CDF7F6" />
            <stop offset="42%" stopColor="#67AAF9" />
            <stop offset="78%" stopColor="#B14AED" stopOpacity="0.25" />
            <stop offset="100%" stopColor="#2EC0F9" stopOpacity="0" />
          </radialGradient>
          <linearGradient id="leftWingClean" x1="154" x2="28" y1="174" y2="70" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#CDF7F6" stopOpacity="0.5" />
            <stop offset="48%" stopColor="#67AAF9" stopOpacity="0.22" />
            <stop offset="100%" stopColor="#B14AED" stopOpacity="0" />
          </linearGradient>
          <linearGradient id="rightWingClean" x1="166" x2="292" y1="174" y2="70" gradientUnits="userSpaceOnUse">
            <stop offset="0%" stopColor="#CDF7F6" stopOpacity="0.5" />
            <stop offset="48%" stopColor="#67AAF9" stopOpacity="0.22" />
            <stop offset="100%" stopColor="#B14AED" stopOpacity="0" />
          </linearGradient>
          <filter id="bigGlow" x="-60%" y="-60%" width="220%" height="220%">
            <feGaussianBlur stdDeviation="6" result="blur" />
            <feColorMatrix in="blur" type="matrix" values="0 0 0 0 0.44 0 0 0 0 0.82 0 0 0 0 1 0 0 0 0.78 0" result="glow" />
            <feMerge><feMergeNode in="glow" /><feMergeNode in="SourceGraphic" /></feMerge>
          </filter>
        </defs>

        <ellipse className="spriteOrbit orbitA" cx="160" cy="158" rx="118" ry="52" />
        <ellipse className="spriteOrbit orbitB" cx="160" cy="158" rx="88" ry="118" />
        <ellipse className="spriteOrbit orbitC" cx="160" cy="158" rx="132" ry="80" />

        {motes.map((mote) => (
          <circle key={mote.id} className="spriteMote" cx={mote.cx} cy={mote.cy} r={mote.r} style={{ animationDelay: mote.delay }} />
        ))}

        <g className="wingGroup wingLeft" filter="url(#bigGlow)">
          <path className="energyWing" d="M154 174 C128 163 92 142 50 106 C32 90 20 72 14 58 C58 64 104 86 135 118 C150 136 154 154 154 174 Z" fill="url(#leftWingClean)" />
          <path className="wingVein" d="M148 168 C124 140 92 105 34 62" />
          <path className="wingVein thin" d="M138 153 C113 130 87 106 62 82" />
        </g>

        <g className="wingGroup wingRight" filter="url(#bigGlow)">
          <path className="energyWing" d="M166 174 C192 163 228 142 270 106 C288 90 300 72 306 58 C262 64 216 86 185 118 C170 136 166 154 166 174 Z" fill="url(#rightWingClean)" />
          <path className="wingVein" d="M172 168 C196 140 228 105 286 62" />
          <path className="wingVein thin" d="M182 153 C207 130 233 106 258 82" />
        </g>

        <g className="orbGroup" filter="url(#bigGlow)">
          <circle className="orbOuter" cx="160" cy="158" r="40" fill="url(#orbCore)" />
          <circle className="orbGlass" cx="151" cy="146" r="16" />
          <circle className="orbHot" cx="160" cy="158" r="7" />
        </g>
      </svg>
    </div>
  );
}

function VoiceVisualizer({ state, compact = false }: { state: SpiritState; compact?: boolean }) {
  const bars = useMemo(
    () => Array.from({ length: compact ? 18 : 26 }, (_, i) => ({
      id: i,
      h: 8 + ((i * 9) % (compact ? 18 : 32)),
      delay: `${(i % 9) * 0.055}s`,
    })),
    [compact],
  );

  return (
    <div className={cx("voiceVisualizer", compact && "voiceVisualizerCompact", `viz-${state}`)} aria-label="Oracle voice visualizer">
      {bars.map((bar) => (
        <span key={bar.id} style={{ "--bar-h": `${bar.h}px`, "--bar-delay": bar.delay } as React.CSSProperties} />
      ))}
    </div>
  );
}

function HomelabOracleWidget({ state }: { state: SpiritState }) {
  return (
    <section className="widgetCard">
      <div className="widgetGlow" />
      <div className="widgetSpriteCol">
        <OracleSprite state={state} size="medium" />
        <VoiceVisualizer state={state} compact />
      </div>

      <div className="widgetContent">
        <div className="widgetTopline">
          <p><span className="liveDot" />SPIRIT · ORACLE VOICE</p>
          <span className="readyPill"><span />READY</span>
        </div>
        <h2>ORACLE<br />VOICE</h2>
        <p className="widgetSubcopy">Hands-free · Whisper STT · TTS · text fallback</p>
        <dl className="specGrid">
          {SPECS.map(([label, value]) => (
            <div key={label}>
              <dt>{label}</dt>
              <dd className={cx(value === "OK" || value === "Available" ? "cyanValue" : value === "Oracle" ? "purpleValue" : undefined)}>{value}</dd>
            </div>
          ))}
        </dl>
        <button className="openButton" type="button">
          <span className="buttonGlyph"><Icon name="spark" /></span>
          OPEN ORACLE
          <span className="buttonArrow">→</span>
        </button>
      </div>
    </section>
  );
}

function OraclePageDemo({ state, setState }: { state: SpiritState; setState: (state: SpiritState) => void }) {
  const active = PREVIEW_STATES.find((item) => item.id === state) ?? PREVIEW_STATES[0];

  return (
    <section className="oraclePage">
      <div className="oracleTopbar">
        <div className="brand"><span className="brandGem" />SPIRIT · ORACLE VOICE</div>
        <span className="readyPill"><span />{active.pill}</span>
        <div className="topbarPills">
          <span><Icon name="wave" />Whisper STT</span>
          <span><Icon name="mic" />Hands-free session</span>
          <span><Icon name="lock" />Secure context</span>
          <button type="button" aria-label="Settings"><Icon name="settings" /></button>
        </div>
      </div>

      <div className="oracleMainGrid">
        <aside className="oracleIntro">
          <h1>ORACLE<br />VOICE</h1>
          <p>Your voice bridge to SpiritOS. Hands-free intelligence for natural, secure interaction.</p>
          <div className="modePanel">
            <label>MODE</label>
            <select defaultValue="Peer"><option>Peer</option><option>Guide</option><option>Analyst</option></select>
            <p>Grounded friend. Conversational support with empathy and clarity.</p>
            <div className="modeActions"><button type="button"><Icon name="wave" /></button><button type="button"><Icon name="user" /></button></div>
          </div>
        </aside>

        <main className="oracleHero">
          <div className="heroHalo" />
          <OracleSprite state={state} size="large" />
          <VoiceVisualizer state={state} />
          <div className="heroControls">
            <button className="micButton" type="button" onClick={() => setState(state === "listening" ? "thinking" : "listening")}>
              <Icon name="mic" />{state === "listening" ? "LISTENING" : "GRANT MIC ACCESS"}
            </button>
            <div className="voiceControl"><span>OUTPUT VOICE</span><button type="button" onClick={() => setState("speaking")}><Icon name="voice" /> SPEAK</button></div>
          </div>
          <p className="micNote"><Icon name="lock" /> Microphone access is required to begin</p>
        </main>

        <aside className="systemPanel">
          <h3>System Status</h3>
          <StatusRow label="STT" value="Whisper backend" state="ok" />
          <StatusRow label="MIC" value="Permission needed" state="warn" />
          <StatusRow label="SECURITY" value="Secure OK" state="ok" />
          <StatusRow label="CONTEXT" value="Oracle session" state="ok" />
          <div className="inputLevel"><div><span>Input level</span><b>0%</b></div><div className="levelTrack"><span /></div><p>Idle</p></div>
        </aside>
      </div>

      <div className="oracleBottomGrid">
        <section className="sessionPanel">
          <h3>Oracle Session</h3>
          <Message role="ORACLE" icon="spark" text="Hello. I’m Oracle. What would you like to explore today?" time="10:42:11" />
          <Message role="YOU" icon="user" text="What’s on my schedule this afternoon?" time="10:42:18" user />
          <Message role="ORACLE" icon="spark" text="You have a project sync at 2:00 PM, design review at 3:30 PM, and a 1:1 with Alex at 4:15 PM." time="10:42:24" />
          <div className="listeningRow"><Icon name="wave" /> Listening... <span>ⓘ</span></div>
        </section>
        <section className="advancedPanel">
          <h3>Advanced</h3>
          {["Silence sensitivity", "Auto-end session", "Wake word", "Noise suppression", "Language"].map((label, i) => (
            <div className="advancedRow" key={label}><span>{label}</span><b>{["Medium", "10 min", "Oracle", "On", "Auto"][i]}</b></div>
          ))}
          <button type="button">Open full settings <Icon name="external" /></button>
        </section>
      </div>
    </section>
  );
}

function StatusRow({ label, value, state }: { label: string; value: string; state: "ok" | "warn" }) {
  return <div className="statusRow"><span>{label}</span><b>{value}</b><Icon name={state === "ok" ? "check" : "warn"} className={state === "ok" ? "okIcon" : "warnIcon"} /></div>;
}

function Message({ role, text, time, icon, user = false }: { role: string; text: string; time: string; icon: IconName; user?: boolean }) {
  return <div className={cx("messageRow", user && "messageUser")}><span className="msgIcon"><Icon name={icon} /></span><b>{role}</b><p>{text}</p><time>{time}</time></div>;
}

export default function SpiritOracleFairyDemo() {
  const [state, setState] = useState<SpiritState>("idle");
  return (
    <main className="demoRoot">
      <style>{css}</style>
      <section className="demoHero">
        <div>
          <p className="eyebrow"><Icon name="spark" /> SPIRITOS DEMO</p>
          <h1>Oracle sprite demo</h1>
          <p>Coded demo with cleaned-up energy wings, no tail, and smaller action buttons.</p>
        </div>
        <div className="previewControls" aria-label="Animation preview controls">
          {PREVIEW_STATES.map((item) => <button key={item.id} type="button" onClick={() => setState(item.id)} className={cx(state === item.id && "active")}>{item.label}</button>)}
        </div>
      </section>
      <section className="widgetStage"><div className="stageLabel">Standalone desktop homelab widget</div><HomelabOracleWidget state={state} /></section>
      <section className="pageStage"><div className="stageLabel">Standalone /oracle page demo</div><OraclePageDemo state={state} setState={setState} /></section>
    </main>
  );
}

const css = `
  :root {
    --bg: #03050d; --bg2: #070b18; --line: rgba(205,247,246,0.14); --cyan: #cdf7f6; --cyan2: #67aaf9; --lav: #9a94bc; --purple: #b14aed; --text: #eef8ff; --muted: rgba(238,248,255,0.58); --muted2: rgba(238,248,255,0.38);
  }
  * { box-sizing: border-box; }
  .demoRoot { min-height: 100vh; padding: 28px; color: var(--text); background: radial-gradient(circle at 22% 8%, rgba(46,192,249,0.16), transparent 28%), radial-gradient(circle at 86% 22%, rgba(177,74,237,0.16), transparent 32%), linear-gradient(135deg, #02030a, #070b18 48%, #050610); font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", monospace; }
  .demoHero { max-width: 1420px; margin: 0 auto 28px; display: flex; justify-content: space-between; align-items: end; gap: 20px; padding: 22px; border: 1px solid rgba(255,255,255,0.08); background: rgba(255,255,255,0.035); border-radius: 28px; backdrop-filter: blur(18px); }
  .demoHero h1 { margin: 8px 0; font-size: clamp(32px, 5vw, 68px); line-height: .92; letter-spacing: -.06em; text-transform: uppercase; }
  .demoHero p { max-width: 720px; margin: 0; color: var(--muted); line-height: 1.65; }
  .eyebrow { display: flex; align-items: center; gap: 10px; font-size: 11px; letter-spacing: .28em; color: var(--cyan) !important; font-weight: 900; }
  .eyebrow svg { width: 16px; height: 16px; }
  .previewControls { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: 8px; min-width: 300px; }
  .previewControls button { min-height: 40px; border: 1px solid rgba(255,255,255,0.1); border-radius: 999px; background: rgba(255,255,255,0.045); color: var(--muted); padding: 0 14px; font: inherit; font-size: 11px; font-weight: 900; letter-spacing: .12em; text-transform: uppercase; cursor: pointer; }
  .previewControls button.active { color: var(--cyan); border-color: rgba(205,247,246,0.42); background: rgba(205,247,246,0.11); box-shadow: 0 0 30px rgba(46,192,249,0.14); }
  .widgetStage, .pageStage { max-width: 1420px; margin: 0 auto 34px; }
  .stageLabel { margin: 0 0 12px; color: var(--cyan); font-size: 11px; letter-spacing: .24em; text-transform: uppercase; font-weight: 900; }

  .widgetCard { position: relative; overflow: hidden; display: grid; grid-template-columns: minmax(260px, .92fr) minmax(360px, 1.1fr); gap: 30px; min-height: 500px; padding: 40px; border-radius: 38px; border: 1px solid var(--line); background: radial-gradient(circle at 18% 42%, rgba(46,192,249,0.2), transparent 36%), linear-gradient(135deg, rgba(12,18,34,0.92), rgba(5,7,16,0.95)); box-shadow: 0 40px 90px rgba(0,0,0,0.45), inset 0 0 0 1px rgba(255,255,255,0.035), 0 0 0 1px rgba(170,125,206,0.12); }
  .widgetCard::before { content: ""; position: absolute; inset: 0; border-radius: inherit; padding: 1px; background: linear-gradient(135deg, rgba(205,247,246,0.42), transparent 42%, rgba(177,74,237,0.62)); -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0); -webkit-mask-composite: xor; mask-composite: exclude; pointer-events: none; }
  .widgetGlow { position: absolute; inset: auto auto -30% -12%; width: 52%; aspect-ratio: 1; border-radius: 50%; background: rgba(46,192,249,0.14); filter: blur(80px); }
  .widgetSpriteCol { position: relative; display: grid; place-items: center; min-height: 410px; }
  .widgetContent { position: relative; z-index: 2; align-self: center; }
  .widgetTopline, .oracleTopbar { display: flex; align-items: center; justify-content: space-between; gap: 16px; }
  .widgetTopline p, .brand { margin: 0; color: var(--lav); font-size: 13px; font-weight: 900; letter-spacing: .24em; text-transform: uppercase; display: flex; align-items: center; gap: 10px; }
  .liveDot, .brandGem { width: 10px; height: 10px; border-radius: 50%; background: var(--cyan); box-shadow: 0 0 18px var(--cyan2); display: inline-block; }
  .brandGem { background: var(--purple); box-shadow: 0 0 18px var(--purple); }
  .readyPill { display: inline-flex; align-items: center; gap: 9px; border: 1px solid rgba(205,247,246,0.48); background: rgba(205,247,246,0.08); color: var(--cyan); border-radius: 999px; padding: 9px 14px; font-weight: 900; letter-spacing: .18em; font-size: 11px; text-transform: uppercase; box-shadow: 0 0 24px rgba(46,192,249,0.13); }
  .readyPill span { width: 8px; height: 8px; border-radius: 50%; background: var(--cyan); box-shadow: 0 0 14px var(--cyan2); }
  .widgetContent h2, .oracleIntro h1 { margin: 30px 0 16px; font-size: clamp(42px, 6vw, 74px); line-height: .94; letter-spacing: -.055em; text-transform: uppercase; text-shadow: 0 0 26px rgba(103,170,249,0.25); background: linear-gradient(180deg, #f3fbff, #8fdcff 62%, #9a94bc); -webkit-background-clip: text; color: transparent; }
  .widgetSubcopy { max-width: 520px; color: var(--muted); font-size: 17px; line-height: 1.6; margin: 0 0 26px; }
  .specGrid { display: grid; margin: 0 0 26px; border-top: 1px solid rgba(255,255,255,0.08); }
  .specGrid div { display: grid; grid-template-columns: 1fr 1.05fr; gap: 22px; padding: 12px 0; border-bottom: 1px solid rgba(255,255,255,0.08); }
  .specGrid dt { color: var(--lav); text-transform: uppercase; letter-spacing: .11em; font-weight: 900; }
  .specGrid dd { margin: 0; color: var(--text); text-transform: uppercase; font-weight: 900; letter-spacing: .07em; }
  .specGrid .cyanValue { color: #43e9ff; }
  .specGrid .purpleValue { color: #bd8cff; }

  .openButton, .micButton { position: relative; width: 100%; min-height: 54px; display: flex; align-items: center; justify-content: center; gap: 12px; border: 1px solid rgba(205,247,246,0.42); border-radius: 16px; background: linear-gradient(135deg, rgba(46,192,249,0.1), rgba(177,74,237,0.08)); color: #43e9ff; font: inherit; font-size: 13px; font-weight: 900; letter-spacing: .14em; text-transform: uppercase; cursor: pointer; box-shadow: inset 0 0 18px rgba(46,192,249,0.06), 0 0 18px rgba(177,74,237,0.08); }
  .buttonGlyph { width: 30px; height: 30px; display: grid; place-items: center; border: 1px solid rgba(67,233,255,0.38); border-radius: 10px; }
  .buttonGlyph svg, .micButton svg { width: 16px; height: 16px; }
  .buttonArrow { margin-left: 4px; font-size: 16px; }
  .tinyMeter { position: absolute; bottom: 52px; display: flex; gap: 8px; align-items: end; }
  .tinyMeter span { width: 4px; height: 7px; border-radius: 999px; background: var(--muted2); animation: meter 1.8s ease-in-out infinite; }
  .tinyMeter span:nth-child(2) { height: 12px; background: var(--cyan2); animation-delay: .18s; }
  .tinyMeter span:nth-child(3) { height: 16px; background: var(--cyan); animation-delay: .34s; }
  .tinyMeter span:nth-child(4) { height: 18px; background: var(--purple); animation-delay: .5s; }

  .oraclePage { overflow: hidden; border: 1px solid var(--line); border-radius: 34px; background: radial-gradient(circle at 50% 30%, rgba(46,192,249,0.14), transparent 30%), linear-gradient(135deg, rgba(6,10,21,0.96), rgba(2,3,8,0.98)); box-shadow: 0 44px 120px rgba(0,0,0,0.52); }
  .oracleTopbar { min-height: 76px; padding: 0 28px; border-bottom: 1px solid rgba(255,255,255,0.08); background: rgba(255,255,255,0.035); }
  .topbarPills { margin-left: auto; display: flex; align-items: center; gap: 10px; }
  .topbarPills span, .topbarPills button { min-height: 38px; display: inline-flex; align-items: center; gap: 8px; border: 1px solid rgba(255,255,255,0.1); background: rgba(255,255,255,0.045); color: var(--muted); border-radius: 999px; padding: 0 14px; font: inherit; font-size: 12px; font-weight: 800; }
  .topbarPills svg { width: 16px; height: 16px; }
  .topbarPills button { width: 42px; padding: 0; justify-content: center; border-radius: 14px; }
  .oracleMainGrid { display: grid; grid-template-columns: 300px minmax(360px, 1fr) 330px; gap: 26px; align-items: center; padding: 48px 48px 18px; }
  .oracleIntro p { color: var(--muted); line-height: 1.7; margin: 0 0 34px; }
  .modePanel, .systemPanel, .sessionPanel, .advancedPanel { border: 1px solid rgba(255,255,255,0.08); background: rgba(255,255,255,0.038); border-radius: 24px; box-shadow: inset 0 0 40px rgba(46,192,249,0.035); }
  .modePanel { padding: 22px; }
  .modePanel label, .systemPanel h3, .sessionPanel h3, .advancedPanel h3, .voiceControl span { color: var(--lav); font-size: 12px; letter-spacing: .17em; text-transform: uppercase; font-weight: 900; }
  .modePanel select { margin: 10px 0 12px; width: 100%; min-height: 46px; border: 1px solid rgba(255,255,255,0.12); border-radius: 14px; background: rgba(2,3,8,0.58); color: var(--text); padding: 0 14px; font: inherit; }
  .modeActions { display: flex; gap: 10px; }
  .modeActions button { width: 48px; height: 48px; border: 1px solid rgba(255,255,255,0.1); background: rgba(255,255,255,0.045); color: var(--muted); border-radius: 14px; }
  .modeActions button:first-child { border-color: rgba(67,233,255,0.44); color: var(--cyan); }
  .modeActions svg { width: 20px; height: 20px; }
  .oracleHero { position: relative; min-height: 480px; display: grid; place-items: center; text-align: center; }
  .heroHalo { position: absolute; width: 70%; aspect-ratio: 1; border-radius: 50%; background: radial-gradient(circle, rgba(46,192,249,0.16), transparent 62%); filter: blur(28px); }
  .heroControls { width: min(100%, 560px); display: grid; grid-template-columns: 1fr 180px; gap: 16px; align-items: end; margin-top: -18px; z-index: 4; }
  .micButton { min-height: 58px; font-size: 13px; }
  .voiceControl { display: grid; gap: 9px; text-align: left; }
  .voiceControl button { min-height: 42px; border: 1px solid rgba(67,233,255,0.42); border-radius: 14px; background: rgba(46,192,249,0.08); color: #43e9ff; font: inherit; font-size: 12px; font-weight: 900; letter-spacing: .1em; text-transform: uppercase; padding: 0 14px; }
  .voiceControl svg { width: 15px; height: 15px; vertical-align: -3px; margin-right: 8px; }
  .micNote { grid-column: 1 / -1; color: var(--muted2); display: flex; justify-content: center; align-items: center; gap: 8px; margin: -8px 0 0; font-size: 12px; }
  .micNote svg { width: 14px; height: 14px; }
  .systemPanel { padding: 24px; }
  .statusRow { display: grid; grid-template-columns: 72px 1fr 22px; gap: 12px; align-items: center; padding: 15px 0; border-bottom: 1px solid rgba(255,255,255,0.08); }
  .statusRow span { color: var(--lav); font-weight: 900; letter-spacing: .12em; text-transform: uppercase; }
  .statusRow b { color: var(--text); font-size: 13px; }
  .okIcon { color: #63ff9d; width: 18px; height: 18px; }
  .warnIcon { color: #f6c95c; width: 18px; height: 18px; }
  .inputLevel { margin-top: 26px; }
  .inputLevel div:first-child { display: flex; justify-content: space-between; color: var(--lav); text-transform: uppercase; font-weight: 900; letter-spacing: .12em; font-size: 12px; }
  .levelTrack { margin: 16px 0 10px; height: 9px; border-radius: 999px; background: rgba(255,255,255,0.14); overflow: hidden; }
  .levelTrack span { display: block; width: 3%; height: 100%; background: var(--cyan); }
  .inputLevel p { color: var(--muted); margin: 0; }
  .oracleBottomGrid { display: grid; grid-template-columns: minmax(0, 1fr) 420px; gap: 20px; padding: 0 48px 44px; }
  .sessionPanel, .advancedPanel { padding: 22px; }
  .messageRow { display: grid; grid-template-columns: 34px 100px 1fr 72px; gap: 14px; align-items: center; padding: 14px 0; border-bottom: 1px solid rgba(255,255,255,0.07); }
  .msgIcon { width: 30px; height: 30px; display: grid; place-items: center; color: var(--purple); border: 1px solid rgba(177,74,237,0.38); border-radius: 10px; }
  .msgIcon svg { width: 16px; height: 16px; }
  .messageUser .msgIcon { color: var(--cyan); border-color: rgba(67,233,255,0.38); }
  .messageRow b { color: var(--purple); font-size: 12px; letter-spacing: .12em; }
  .messageUser b { color: var(--cyan2); }
  .messageRow p { margin: 0; color: var(--muted); line-height: 1.55; }
  .messageRow time { color: var(--muted2); font-size: 12px; }
  .listeningRow { margin-top: 10px; min-height: 48px; display: flex; align-items: center; gap: 12px; border: 1px solid rgba(255,255,255,0.08); background: rgba(0,0,0,0.18); border-radius: 16px; padding: 0 16px; color: var(--muted2); }
  .listeningRow svg { width: 20px; height: 20px; }
  .listeningRow span { margin-left: auto; }
  .advancedRow { display: flex; justify-content: space-between; gap: 18px; padding: 14px 0; border-bottom: 1px solid rgba(255,255,255,0.07); color: var(--muted); }
  .advancedRow b { color: var(--lav); }
  .advancedPanel button { margin-top: 18px; width: 100%; min-height: 46px; display: flex; align-items: center; justify-content: space-between; border: 1px solid rgba(255,255,255,0.1); background: rgba(255,255,255,0.035); color: var(--muted); border-radius: 14px; padding: 0 14px; font: inherit; }
  .advancedPanel button svg { width: 16px; height: 16px; }

  .spriteShell { position: relative; z-index: 2; display: grid; place-items: center; filter: drop-shadow(0 0 30px rgba(46,192,249,0.2)); }
  .sprite-small { width: 170px; height: 170px; }
  .sprite-medium { width: min(100%, 390px); max-width: 400px; min-width: 280px; aspect-ratio: 1; }
  .sprite-large { width: min(70vw, 570px); max-width: 580px; min-width: 340px; aspect-ratio: 1; }
  .oracleHero .sprite-large { width: min(44vw, 410px); max-width: 410px; min-width: 240px; }
  .spriteSvg { width: 100%; height: 100%; overflow: visible; }
  .spriteOrbit { fill: none; stroke: rgba(205,247,246,0.14); stroke-width: 1; transform-origin: 160px 158px; }
  .orbitA { animation: orbitSpinA 10s linear infinite; }
  .orbitB { animation: orbitSpinB 13s linear infinite reverse; stroke: rgba(177,74,237,0.14); }
  .orbitC { animation: orbitSpinC 16s linear infinite; stroke-dasharray: 7 12; opacity: .75; }
  .wingGroup { transform-origin: 160px 174px; }
  .wingLeft { animation: leftWingBreath 4.2s ease-in-out infinite; }
  .wingRight { animation: rightWingBreath 4.2s ease-in-out infinite; }
  .energyWing { stroke: rgba(205,247,246,0.18); stroke-width: 1; }
  .wingVein { fill: none; stroke: rgba(255,255,255,0.24); stroke-width: 1.25; stroke-linecap: round; opacity: .58; }
  .wingVein.thin { stroke-width: .85; opacity: .36; }
  .orbGroup { transform-origin: 160px 158px; animation: orbHover 4s ease-in-out infinite; }
  .orbOuter { opacity: .96; animation: orbPulse 2.8s ease-in-out infinite; }
  .orbGlass { fill: rgba(255,255,255,0.34); filter: blur(.2px); }
  .orbHot { fill: white; filter: drop-shadow(0 0 12px white) drop-shadow(0 0 28px #67aaf9); animation: hotPulse 1.8s ease-in-out infinite; }
  .spriteMote { fill: rgba(205,247,246,0.62); filter: drop-shadow(0 0 8px rgba(205,247,246,.78)); animation: moteFloat 4.8s ease-in-out infinite; }
  .spriteState-listening .spriteMote { animation-name: moteIn; }
  .spriteState-thinking .orbitA { animation-duration: 3.8s; }
  .spriteState-thinking .orbitB { animation-duration: 5.2s; }
  .spriteState-speaking .wingLeft, .spriteState-speaking .wingRight { animation-duration: 2.2s; }
  .spriteState-error .orbOuter { filter: hue-rotate(118deg) saturate(1.3); }
  .spriteState-error .spriteOrbit { stroke: rgba(246,201,92,0.24); }

  .voiceVisualizer { position: relative; z-index: 4; width: min(100%, 360px); min-height: 50px; display: flex; align-items: center; justify-content: center; gap: 6px; padding: 10px 16px; border: 1px solid rgba(205,247,246,0.18); border-radius: 18px; background: linear-gradient(135deg, rgba(205,247,246,0.06), rgba(177,74,237,0.045)); box-shadow: inset 0 0 22px rgba(46,192,249,0.045), 0 0 24px rgba(46,192,249,0.08); }
  .voiceVisualizerCompact { position: absolute; bottom: 38px; width: min(82%, 260px); min-height: 34px; gap: 4px; padding: 6px 10px; border-radius: 14px; }
  .voiceVisualizer span { width: 4px; height: var(--bar-h); min-height: 5px; border-radius: 999px; background: linear-gradient(180deg, #cdf7f6, #67aaf9 62%, #b14aed); box-shadow: 0 0 10px rgba(205,247,246,0.46); opacity: .62; animation: vizIdle 2.2s ease-in-out infinite; animation-delay: var(--bar-delay); transform-origin: center; }
  .voiceVisualizerCompact span { width: 3px; }
  .viz-speaking span { animation-name: vizSpeaking; animation-duration: .62s; opacity: .95; }
  .viz-listening span { animation-name: vizListening; animation-duration: 1.05s; }
  .viz-thinking span { animation-name: vizThinking; animation-duration: 1.4s; }
  .viz-error span { background: linear-gradient(180deg, #ffe3a3, #f6c95c 58%, #b14aed); animation-name: vizError; animation-duration: .9s; }

  @keyframes meter { 0%,100% { opacity: .42; transform: scaleY(.6); } 50% { opacity: 1; transform: scaleY(1.15); } }
  @keyframes orbitSpinA { from { transform: rotate(0deg) skewX(-16deg); } to { transform: rotate(360deg) skewX(-16deg); } }
  @keyframes orbitSpinB { from { transform: rotate(0deg) skewY(24deg); } to { transform: rotate(360deg) skewY(24deg); } }
  @keyframes orbitSpinC { from { transform: rotate(0deg) scale(.95); } to { transform: rotate(-360deg) scale(.95); } }
  @keyframes leftWingBreath { 0%,100% { transform: rotate(-2deg) scale(.98); opacity: .74; } 50% { transform: rotate(-8deg) scale(1.04); opacity: .98; } }
  @keyframes rightWingBreath { 0%,100% { transform: rotate(2deg) scale(.98); opacity: .74; } 50% { transform: rotate(8deg) scale(1.04); opacity: .98; } }
  @keyframes orbHover { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-8px); } }
  @keyframes orbPulse { 0%,100% { transform: scale(.96); } 50% { transform: scale(1.05); } }
  @keyframes hotPulse { 0%,100% { transform: scale(.8); opacity: .78; } 50% { transform: scale(1.28); opacity: 1; } }
  @keyframes moteFloat { 0%,100% { opacity: .26; transform: translateY(0) scale(.75); } 50% { opacity: .82; transform: translateY(-10px) scale(1.08); } }
  @keyframes moteIn { 0%,100% { opacity: .25; transform: scale(.75); } 50% { opacity: .9; transform: translate(7px, 7px) scale(1.2); } }
  @keyframes vizIdle { 0%,100% { transform: scaleY(.42); opacity: .35; } 50% { transform: scaleY(.72); opacity: .62; } }
  @keyframes vizListening { 0%,100% { transform: scaleY(.48); opacity: .52; } 45% { transform: scaleY(1.05); opacity: .85; } }
  @keyframes vizThinking { 0%,100% { transform: scaleY(.5); opacity: .44; filter: hue-rotate(0deg); } 50% { transform: scaleY(.9); opacity: .78; filter: hue-rotate(35deg); } }
  @keyframes vizSpeaking { 0%,100% { transform: scaleY(.38); opacity: .62; } 35% { transform: scaleY(1.45); opacity: 1; } 65% { transform: scaleY(.88); opacity: .9; } }
  @keyframes vizError { 0%,100% { transform: scaleY(.35); opacity: .45; } 50% { transform: scaleY(1.12); opacity: .92; } }

  @media (max-width: 1080px) {
    .widgetCard { grid-template-columns: 1fr; padding: 28px; }
    .widgetSpriteCol { min-height: 330px; }
    .oracleMainGrid { grid-template-columns: 1fr; padding: 34px 24px 20px; }
    .oracleIntro { text-align: center; }
    .modePanel { max-width: 460px; margin: 0 auto; text-align: left; }
    .systemPanel { max-width: 520px; margin: 0 auto; width: 100%; }
    .oracleBottomGrid { grid-template-columns: 1fr; padding: 0 24px 34px; }
    .topbarPills { display: none; }
  }
  @media (max-width: 760px) {
    .demoRoot { padding: 14px; }
    .demoHero { align-items: stretch; flex-direction: column; }
    .previewControls { min-width: 0; justify-content: flex-start; }
    .widgetCard { padding: 20px; border-radius: 28px; }
    .widgetTopline { align-items: flex-start; flex-direction: column; }
    .widgetContent h2 { font-size: 44px; }
    .specGrid div { grid-template-columns: 1fr; gap: 4px; }
    .openButton, .micButton { font-size: 12px; min-height: 52px; }
    .sprite-medium { min-width: 230px; }
    .sprite-large { min-width: 280px; width: 88vw; }
    .oracleTopbar { align-items: flex-start; flex-direction: column; padding: 18px; }
    .oracleHero { min-height: 460px; }
    .oracleHero .sprite-large { width: min(82vw, 330px); max-width: 330px; min-width: 230px; }
    .heroControls { grid-template-columns: 1fr; }
    .messageRow { grid-template-columns: 30px 72px 1fr; }
    .messageRow time { display: none; }
  }
  @media (prefers-reduced-motion: reduce) { *, *::before, *::after { animation-duration: .001ms !important; animation-iteration-count: 1 !important; scroll-behavior: auto !important; } }
`;
