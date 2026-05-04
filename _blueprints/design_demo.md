# Spirit OS · Design Demo Blueprint

> **Status:** Visual-only preview. The production app is **not** rewired. This
> demo is a sandbox for art direction we can selectively port into real
> routes later.

---

## Purpose

`/design-demo` is a standalone, mobile-first design demo of what the Spirit
OS command center can look like when fully polished. It exists so we can:

- review a high-fidelity vision in-app, on a real phone, without breaking
  anything;
- iterate on motion, glass language, and layout in isolation;
- decide what to port piece-by-piece into `/`, `/chat`, `/oracle`, and
  `/quarantine`.

Nothing in this demo touches production transports, persistence, runtimes,
or APIs.

---

## How to view it

1. `npm run dev`
2. Open `/design-demo` on a mobile-sized viewport (or use device tools).
3. Production routes (`/`, `/chat`, `/oracle`, `/quarantine`) keep working
   unchanged. The demo even links to them where the real lane is the
   correct destination.

---

## Files added

### Route

- `src/app/design-demo/page.tsx` — server component that imports the demo
  CSS layers and mounts the client shell. Sets `<title>` metadata.

### Components (`src/components/design-demo/`)

- `SpiritDesignDemo.tsx` — top-level shell. Renders `.spirit-demo-root`,
  the atmospheric layer, the desktop side rail, the top bar, the demo
  banner, the six preview sections, the footer, and the mobile dock.
- `DemoCommandCenter.tsx` — hero panel, telemetry strip, quick-launch
  grid. Real CTAs link out to `/chat`, `/oracle`, `/quarantine`; demo-only
  cards are tagged "Demo · not wired".
- `DemoChatPreview.tsx` — visual ChatGPT-style workspace shell with
  folder/thread rail, mode bar, mock bubbles, fake composer, and a
  workflow visualizer strip. Links to the real `/chat`.
- `DemoOraclePreview.tsx` — Oracle voice stage with the animated orb,
  fake waveform, listening / transcribing / thinking / speaking telemetry
  rows, and a device card. Links to the real `/oracle`.
- `DemoQuarantinePreview.tsx` — six experimental lab cards (Deep
  Research, RAG · local, Model Lab, Local Agent, Terminal Mode, Sigil
  Editor). All visibly marked as not wired. Links to the real
  `/quarantine`.
- `DemoDiagnosticsPreview.tsx` — eight diagnostic tiles with online /
  warn / offline pulse dots, plus a voice + STT detail row. **All values
  are mocked.** No real probes run from this preview.
- `DemoProfilePreview.tsx` — Spirit profile preview, personality stats,
  modes, and a "What Spirit knows" list. Editable-looking but read-only.
- `DemoMotionOrb.tsx` — pure-presentational Oracle orb (halo + three
  rings + gradient core). All animation lives in CSS.
- `DemoMobileDock.tsx` — sticky bottom dock for mobile. Tracks the
  active section via `IntersectionObserver` and respects
  `prefers-reduced-motion` when scrolling.
- `DemoIcons.tsx` — small inline SVG icon set so we don't couple the
  demo to a specific `lucide-react` version.

### Styles (`src/styles/`)

- `spirit-demo.tokens.css` — color aliases, glow strengths, radii,
  blur, spacing rhythm, typography rhythm, z-index scale, motion
  durations. **All variables defined under `.spirit-demo-root`** to avoid
  bleeding into production tokens.
- `spirit-demo.layout.css` — shell, atmospheric layer, section bands,
  hero grid, 2/3/4-up grids, chat split, oracle split, mobile dock,
  desktop rail, top bar.
- `spirit-demo.effects.css` — glass surfaces, scanlines, shimmer line,
  orb ring system, audio waveform, pulse dots, corner caret marks.
- `spirit-demo.components.css` — cards, buttons, badges, tabs, chat
  bubbles, profile bars, status rows, stat tiles, dividers, mock-tags.
- `spirit-demo.animations.css` — keyframes (`demo*` prefix), motion
  utility classes, focus-visible rings, and the
  `prefers-reduced-motion` override that zeroes loop animations.

### Tests

- `src/components/design-demo/__tests__/SpiritDesignDemo.test.tsx` —
  renders the demo, asserts the six section ids exist, asserts the demo
  links point at the real production routes, and asserts the
  reduced-motion media query exists in the animations stylesheet.

### Docs

- `_blueprints/design_demo.md` — this file.

---

## Files **not** changed

This demo is purely additive. The following were intentionally left alone:

- All API routes under `src/app/api/**`.
- Production page routes: `src/app/page.tsx`, `src/app/chat/**`,
  `src/app/oracle/**`, `src/app/quarantine/**`.
- Chat transport, Oracle voice loop, TTS / STT runtime, Dexie
  persistence, middleware, theme engine.
- Existing UI primitives (`GlassPanel`, `SpiritButton`, `SectionLabel`),
  the dashboard shell, and any production component.
- `globals.css`, environment variables, build/test config.

The optional "link from `/quarantine` to `/design-demo`" mentioned in the
brief was deferred — touching the live `/quarantine` page risks the "do
not modify production" constraint. Add it later in a tiny follow-up PR
once we're happy with the demo.

---

## What is visual-only

Everything inside `.spirit-demo-root` is presentational. Specifically:

- Telemetry numbers, status badges, model names, latency figures,
  diagnostic states — all hard-coded mocks.
- Chat threads and bubbles — static strings, no Dexie reads, no LLM
  calls.
- Oracle waveform — sixteen `<span>` bars animated by CSS.
- Personality stats — fixed percentages.
- The mobile dock and desktop rail only scroll the page; they don't
  navigate.

Anywhere a button or card is *not* meant to imply real wiring, it carries
a "Demo · not wired" tag (`mock-tag`) so reviewers can't be misled.

---

## What can be ported later

These elements were designed with the real app in mind and are good
candidates for incremental porting:

- The **glass layer system** (`.demo-glass`, `.demo-glass--*`) — could
  replace ad-hoc panel styling in the dashboard.
- The **Oracle orb** (`DemoMotionOrb` + `.demo-orb`) — drop-in for the
  real Oracle stage with a thin prop layer for state.
- The **mobile dock** pattern — apply once the production shell is
  ready for a bottom-nav-first mobile experience.
- The **section-band rhythm** — consistent vertical pacing for
  dashboard pages.
- The **status row stripe** — usable for live diagnostics once the data
  source is wired.
- The **shimmer line** and **scanline** — atmospheric primitives that
  should live in tokens before they spread.

Porting rule: extract into a real component under `src/components/ui/`
or `src/components/dashboard/`, add tests, then delete the demo copy.

---

## What must **not** be wired yet

- Quarantine experimental cards (Deep Research, RAG · local, Model
  Lab, Local Agent, Terminal Mode, Sigil Editor) — these are still
  product decisions, not engineering tasks.
- Diagnostics preview values — wiring this means going through the real
  diagnostics component, not duplicating its surface.
- The "voice provider" / "STT provider" detail rows — same as above.
- The personality stat bars — these need a real `useSpiritProfile`
  source before going near production.

---

## CSS organization

All five demo CSS files import once from `src/app/design-demo/page.tsx`.
Every selector is nested under `.spirit-demo-root`, including the CSS
variables themselves. That means:

- Demo styles can never bleed into production pages, even if a
  reviewer accidentally promotes a class name.
- We can drop the demo entirely by deleting the route, the components
  folder, the styles folder, and removing the CSS imports.
- `globals.css` is **not** touched. The demo deliberately doesn't use
  the global stylesheet as a delivery channel.

Suggested layering when reading the CSS:

1. `tokens` — design constants only.
2. `layout` — page geometry.
3. `effects` — glass, glow, shimmer.
4. `components` — repeating UI blocks.
5. `animations` — keyframes and reduced-motion overrides.

---

## Mobile-first notes

- Targets: 360px (Android), 375px (iPhone), 768px (tablet), 1024px+
  (desktop).
- No horizontal scroll at any breakpoint.
- All inputs use `font-size: 16px` so iOS Safari doesn't auto-zoom.
- Touch targets (`.demo-btn`, `.demo-tab`, `.demo-rail-btn`,
  `.demo-mobile-dock__tab`) are all ≥ 44px.
- The shell reserves bottom space (`padding-bottom: calc(5rem +
  env(safe-area-inset-bottom))`) so dock-overlapped content is never
  clipped.
- Desktop side rail (`.demo-rail`) only appears at `lg` (≥1024px).
  Below that, it is hidden and the mobile dock is the only nav.
- Top bar is sticky and respects `env(safe-area-inset-top)`.

---

## Accessibility / reduced-motion notes

- The shell uses semantic landmarks: `<nav>` for both rail and dock,
  `<main>` for previews, `<section>` for each preview band, and
  `aria-labelledby` pointing at each section's heading.
- Decorative elements (orb, atmospheric layer, scanlines, dividers,
  pulse dots used as glyphs, icon SVGs) are `aria-hidden="true"` so
  screen readers ignore them.
- Status is communicated by **text + color + icon**, never by color
  alone. Online / warn / offline carry distinct labels.
- Mode rows are `<button aria-pressed>` so the active mode is
  programmatic, not just visual.
- Focus-visible rings are scoped to the demo via
  `.spirit-demo-root :where(a, button, [role="button"]):focus-visible`.
- `@media (prefers-reduced-motion: reduce)` zeroes every loop
  animation (orb breathe, halo, shimmer, waveform, pulse, gradient
  pan, fade-up, blink-caret, scroll-up). Static gradients, layout, and
  glass remain.
- `DemoMobileDock` reads `prefers-reduced-motion` at click time and
  swaps `scrollIntoView({ behavior: "smooth" })` for `"auto"`.

---

## Old-repo inspirations used

The visual cues borrowed from the previous Spirit OS — adapted, not
copied verbatim, with no logic carried over:

- **Trinity Dashboard / Dashboard Shell.** The collapsible-feeling left
  rail at desktop, the compact top bar with a brand mark, and the rhythm
  of stacked section bands.
- **Oracle Orb.** Three concentric rings, a soft halo, a cyan→violet
  gradient core, and a quiet breathing animation. Reproduced in pure CSS
  rather than Canvas / WebGL so it costs nothing.
- **BriefingHub layout.** The pattern of "hero panel → status strip →
  quick-launch grid" used in `DemoCommandCenter`.
- **EnergyMatrix bars.** The thin rounded fills with subtle gradient
  tracks, reused for the personality stats in `DemoProfilePreview`.
- **Cinematic dark luxury palette.** Dark void background + cyan accent
  + violet accent + rose for quarantine + emerald for online — anchored
  to the *current* Spirit OS theme tokens, not the old hex values.
- **Scanline / shimmer atmospherics.** Light-touch only, sub-3% opacity,
  always under the content.

---

## Removal / cleanup

To remove the entire demo:

1. Delete `src/app/design-demo/`.
2. Delete `src/components/design-demo/`.
3. Delete `src/styles/spirit-demo.*.css`.
4. Delete `_blueprints/design_demo.md`.

No production references will dangle. `globals.css` was not modified, so
no edits are needed there.
