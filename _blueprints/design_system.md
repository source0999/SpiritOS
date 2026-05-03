# Spirit OS Design System — "Dark Node" Editorial Luxury

> **Extracted from:** Refactor.txt + Spirit OS Master Blueprint (PDF)  
> **Design language:** Editorial luxury meets cybernetic sovereignty. Unhurried, high-legibility, zero corporate SaaS gloss. Brutally honest yet visually prestigious.

## Core Philosophy
- **Tone**: Sovereign, recursive, sarcastic when appropriate (Toxic Grader), professionally clean for Intelligence Reader.
- **Mood**: Dark void with precise neon/cyan accents. Feels like a physical cybernetic extension of the Source.
- **Rhythm**: Fluid, mathematical typography + generous vertical space. Never rushed.
- **Hierarchy**: Opacity-driven (never hard-coded color variants). Works perfectly on ultra-wide monitors and Tailscale mobile.

## Color Palette (Tailwind v4 @theme)
```css
@theme {
  --color-ink: #0a0a0a;           /* base void */
  --color-void: #111113;
  --color-glass: #1a1a1e;
  --color-cyan: #22d3ee;
  --color-violet: #a855f7;
  --color-rose: #f43f5e;          /* Toxic Grader accents */
  --color-emerald: #10b981;       /* live / online */
}

Primary text: text-ink/100, text-ink/80, text-ink/60, text-ink/40
Dark Card rule: On dark backgrounds, flip opacities (text-ink/100 → text-ink/20 for subtle metadata)
Accent logic: Cyan for Oracle Orb energy, Violet for Spirit presence, Rose for Toxic Grader roasts.

Typography (Fluid + Editorial)
CSS--font-sans: "Inter", system-ui, sans-serif;
--font-mono: "JetBrains Mono", ui-monospace, monospace;

/* Fluid scales — no media queries */
--text-display: clamp(2.5rem, 8vw, 6rem);
--text-h1: clamp(2rem, 5vw, 3.5rem);
--text-h2: clamp(1.5rem, 4vw, 2.5rem);
--text-body: clamp(1rem, 2.5vw, 1.125rem);

Oracle Orb & TTS: Large, glowing mono labels with subtle pulse animation.
Toxic Grader: Strict monospace, terminal green/red accents, scan-line subtle effect optional.
Intelligence Reader: Generous line-height (1.8), py-24 vertical rhythm, clean prose.

Component Guidelines

Oracle Orb: Framer Motion sphere with Web Audio API reactive waveforms. Glow intensity tied to XTTS emotional delivery.
Toxic Grader: Full-bleed terminal container (bg-void border-rose/30). Roast text in font-mono text-rose-300.
Mission Briefing / Intelligence Reader: Two layout modes via LayoutOrchestrator:
Dense grid (telemetry cards)
Distraction-free Markdown reader (prose-invert max-w-3xl mx-auto)

Energy Matrix: Real-time wattage + $/hr with dynamic amber "Peak" state.
Thinking Tree (Scholar Mode): Isolated D3.js Client Component, force-directed graph with cyan nodes.

Layout Orchestrator Rules

Default: CinematicLayout (full-bleed dark)
Intelligence Reader: EditorialLayout (max-w-4xl, centered, massive padding)
Quarantine zone ((quarantine) route group): higher contrast, aggressive rose accents.

Future-Proofing

All tokens defined as CSS variables inside @theme block in src/app/globals.css.
Every component must include intentionality comments for AI parsing.
No hardcoded hex values anywhere — only Tailwind opacity modifiers.

## Implemented primitives (Phase 4)

Static, tiny building blocks in `src/components/ui/` — not a full component library.

- **GlassPanel** + **`glassPanelSurfaceClasses`** — default glass card seam (`glass`, `rounded-2xl`, `spirit-border`, `bg-white/[0.02]`). Use the component for `div`/`section`/`aside`/`article`, or the exported class string on `motion.*` / custom wrappers.
- **SectionLabel** + **`sectionLabelClasses`** — mono uppercase metadata (`text-[10px]`, `tracking-widest`, `text-chalk/45`). Supports `as` (`p` | `span` | `dt`); override with `className` for tracking/color/weight.
- **SpiritButton** + **`spiritPrimaryCtaClasses`** — cyan pill CTA; same classes on `Link` where a button element is wrong.