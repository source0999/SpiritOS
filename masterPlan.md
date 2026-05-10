You are working in my SpiritOS repo on the /chat visual overhaul.

This is a planned multi-phase polish project. Do NOT execute all phases at once.
Use this document as the reference plan. Only execute the specific phase prompt I provide after this.

High-level goal:
Overhaul /chat into a futuristic, clean, glassy, shiny interface inspired by the reference screens:
- screen #3: clean minimal transcript/sidebar structure
- screen #4/#5: shiny liquid-glass controls, specular highlights, soft depth, premium rounded surfaces

Design target:
The chat window should feel glassy, shiny, futuristic, premium, and alive.
It should NOT feel:
- flat
- pale white
- icy washed out
- admin-panel-like
- chunky
- boxy
- rigid
- cluttered

Core design principles:
1. Glass is not white blur.
   Use transparent/partially transparent surfaces over real atmosphere.
   Do not make large surfaces opaque white or pale blue.
   Use smoke/gray/translucent glass, edge highlights, darker border contrast, and internal glow.

2. Keep readability.
   Thread titles, timestamps, controls, and placeholder text must have enough contrast.
   Do not sacrifice legibility for glass effects.

3. Work in small increments.
   One phase at a time.
   Do not run a giant redesign pass.
   Do not touch unrelated routes or runtime logic.

4. Preserve what Cursor already discovered:
   - CSS must target the actual DOM classes.
   - No dead selectors like old __bg-* layers.
   - Keep real trinity atmosphere layers.
   - Keep full-height desktop app nav.
   - Keep mobile pill nav.
   - Keep desktop nav/sidebar separation.
   - Keep debug instrumentation removed.

5. Do not create runtime probes unless explicitly asked.
   No localhost ingest probes.
   No hotpink debug leftovers.
   No #region agent log.
   No trinity-dom-css-probe.
   No computed-style client instrumentation.

General no-loop rules:
- Do not run npm install.
- Do not edit package.json or package-lock.json.
- Do not start a dev server unless one is already running and I explicitly ask.
- Do not run Docker/backend services.
- Do not use networkidle.
- Do not run broad test suites.
- If Vitest fails with local native binding/resolver issues, record it and do not loop.
- Use scoped git diff and scoped git diff --check only.
- Never claim screenshots were checked unless you actually captured one.

Allowed common files:
- src/styles/spirit-trinity-chat.css
- src/components/chat/SpiritTrinityChatShell.tsx only for shell/layout hooks
- src/components/chat/SpiritChat.tsx only for chat layout/composer hooks
- src/components/chat/ChatThreadSidebar.tsx only for sidebar structure/hooks
- src/components/chat/ChatThreadListItem.tsx only for thread row structure/hooks
- src/components/chat/SpiritMessage.tsx only in bubble phase
- src/components/chat/__tests__/SpiritTrinityChatShell.visual.test.tsx only for lightweight static guards

Usually do not touch:
- package files
- API routes
- backend/TTS/STT/research logic
- chat persistence/runtime logic
- dashboard widgets
- oracle runtime
- telemetry
- unrelated routes

Known current state:
- /chat background is finally moving in the right direction.
- The sidebar is cleaner but still not fully reference-quality.
- The main issue now is controlled product polish, not “is CSS applying?”
- The input/composer still needs a complete overhaul later.
- The main nav and chat sidebar/window still need better proportion and spacing.
- The glass language needs more shiny/liquid controls, not more white blur.

Phase 1 — Layout scale and nav/sidebar separation
Goal:
Make the entire /chat workspace feel better proportioned:
- chat window slightly smaller
- more breathing room
- main app nav and chat sidebar not touching
- sidebar card no longer feels crammed against the app rail
- center chat canvas retains atmosphere and clean inset
- no weird top/bottom clipping

Scope:
Layout and sizing only.
No color redesign, no typography redesign, no composer redesign.

Deliverables:
- cleaner app-nav-to-chat-sidebar gap
- slightly smaller sidebar/window footprint
- better top/right/bottom breathing room
- stable desktop-only layout rules
- mobile drawer unchanged

Phase 2 — Chat sidebar top rebuild
Goal:
Make the top of the chat sidebar clean and minimal like reference screen #3.

Scope:
- CHATS header
- saved count
- New chat button
- Folder button
- Search input
- draft/new chat card

Direction:
- simple
- readable
- minimal
- less chunky
- no awkward top layout
- New chat should not look like a disabled slab unless it is actually disabled
- Folder should be secondary but readable

Phase 3 — Folder / Recent list refinement
Goal:
Make the folder/recent area feel like a clean product nav, not a chunky list.

Scope:
- section labels
- thread row rhythm
- row spacing
- title/meta typography
- row hover
- row actions

Direction:
Use screen #3 for structure:
- calm list
- subtle rows
- actions hidden/faint until hover/focus on desktop
- no visible drag/grid marker boxes
- readable, minimal thread list

Phase 4 — Liquid-glass control language
Goal:
Add shiny liquid-glass features inspired by screen #4/#5.

Scope:
- buttons
- pills
- chips
- search field
- selected states
- folder/new-chat controls
- small action controls

Direction:
- edge highlights
- inner shine
- subtle cyan/violet/pearl reflections
- soft shadows
- translucent glass body
- no cartoon neon overload
- no huge chunky Dribbble-only shapes

Phase 5 — Composer/input bar overhaul
Goal:
Completely overhaul the input bar.

Current problem:
The composer always looks rigid, boxy, and admin-like.

Scope:
- composer shell
- textarea/input surface
- send button
- lower chips: Deep think, mode selector, Thread settings, Voice/Speak controls
- focus/hover states

Direction:
- sleek liquid-glass pill/rounded capsule
- premium edge highlight
- less boxy
- less heavy
- readable placeholder
- integrated send button
- lower controls feel like polished glass chips

Phase 6 — Conversation surface and message bubble polish
Goal:
Make the main chat area and bubbles feel premium and alive.

Scope:
- empty state
- assistant/user bubbles
- message action controls
- bubble depth and role distinction
- spacing

Direction:
- no identical printed rectangles
- assistant/user distinct
- glass cards with subtle depth
- text remains readable
- do not overdo blur/white

Phase 7 — Regression guards and cleanup
Goal:
Lock the design wins.

Tasks:
- remove any accidental debug leftovers
- add static guards for key visual hooks
- guard against pale full-page backgrounds
- guard against nav/sidebar touching
- guard against dead selector mismatch
- preserve mobile safety
- preserve real voice controls and runtime behavior

Final verification style:
For each phase, run only scoped commands:
git diff -- <touched files>
git diff --check -- <touched files>

Optional Vitest:
Only run targeted visual/unit tests if the local environment is healthy.
If the known resolver/native-binding failure appears, record it and stop.

Final response format for every phase:
1. Files changed
2. What changed
3. What stayed intentionally unchanged
4. Scoped checks run
5. Known limitations
6. Screenshot path if captured