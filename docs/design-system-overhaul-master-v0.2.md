# SpiritOS Design System Overhaul Master Plan v0.2

Status: planning and diagnostics only, no implementation authorized

Status date: 2026-05-20

## 1. Current State Summary

This v0.2 plan reassesses the current SpiritOS design intelligence stack and the live UI design surface. The design intelligence side is strong for a v0.1 manual-first system. The reusable app-facing design system is still early and scattered across global CSS, feature components, route-scoped styles, palette files, and an internal Design Vault pack.

Design intelligence planning: A-

The v0.1 docs are clear, safety-aware, and Source Proxy gated. They define Design Vault, Reverse Designer, Design Blender, Scout intake, visual verification, and Source Proxy apply boundaries. The main gap is that these documents are ahead of implementation and need a v0.2 spine that turns them into smaller safe increments.

Actual reusable design system: C

There are a few reusable primitives in `src/components/ui/`, a palette registry, theme hook, global CSS variables, and many feature components. The reusable primitive contract is not yet broad enough to support generated UI work safely. Route-specific CSS and feature-local styling still carry too much design logic.

Design Vault: B

`data/design-vault/` exists with a manual-first README, source-card template, approval checklist, token model, and an internal `internal-dashboard-demo-v4` pack. It is useful as evidence, but it is not yet a runtime-backed vault or full design-system source of truth.

Reverse Designer readiness: B-

The approved-inputs contract exists and is clear. The runtime agent, analysis schema, source-risk flags, and manual import path are not implemented.

Design Coding Agent readiness: C

The Source Proxy design apply lane doc defines the future safety contract, but a design-specific coding task lane is not yet represented as a complete Source Proxy task flow with allowed-file derivation, preview evidence, checks, and post-apply verification.

Visual verification readiness: C+

`playwright.config.mjs` exists and `@playwright/test` is listed in docs, but it is not installed in `package.json`. Existing Vitest visual-style component tests exist, and one e2e spec exists under `tests/e2e/`. Screenshot baselines, capture commands, visual diff reports, and approved viewport evidence are not fully active.

Scout bridge readiness: B-

The Scout design intake bridge doc exists and keeps Scout candidate-only and manual-gated. Runtime integration is intentionally not present.

Source Proxy apply lane readiness: B-

The design apply lane contract exists and correctly keeps Source Proxy as the only apply path. The actual design lane implementation, safety reasons, evidence attachment, and bounded UI diff preview flow are not implemented.

## 2. Current Assets Found

Docs found:

- `docs/design-systems-master-v0.1.md`
- `docs/design-blender-style-alchemist-v0.1.md`
- `docs/design-pack-authoring-v0.1.md`
- `docs/design-visual-verification-v0.1.md`
- `docs/reverse-designer-approved-inputs-v0.1.md`
- `docs/scout-design-intake-bridge-v0.1.md`
- `docs/source-proxy-design-apply-lane-v0.1.md`
- `docs/plan-index.md`

Design Vault artifacts found:

- `data/design-vault/README.md`
- `data/design-vault/token-model-v0.1.md`
- `data/design-vault/source-cards/index.json`
- `data/design-vault/source-cards/source-card.template.json`
- `data/design-vault/source-cards/approval-checklist.md`
- `data/design-vault/source-cards/internal-dashboard-demo-v4.json`
- `data/design-vault/packs/internal-dashboard-demo-v4/README.md`
- `data/design-vault/packs/internal-dashboard-demo-v4/tokens.raw.json`
- `data/design-vault/packs/internal-dashboard-demo-v4/tokens.json`
- `data/design-vault/packs/internal-dashboard-demo-v4/theme.css`
- `data/design-vault/packs/internal-dashboard-demo-v4/components-map.json`
- `data/design-vault/packs/internal-dashboard-demo-v4/match-report.json`
- `data/design-vault/packs/internal-dashboard-demo-v4/reference/.gitkeep`
- `data/design-vault/packs/internal-dashboard-demo-v4/generated/.gitkeep`

UI primitives found:

- `src/components/ui/GlassPanel.tsx`
- `src/components/ui/SectionLabel.tsx`
- `src/components/ui/SpiritButton.tsx`
- `src/components/ui/index.ts`

Theme and token files found:

- `src/theme/spiritPalettes.ts`
- `src/theme/useSpiritTheme.ts`
- `src/app/globals.css`
- `src/styles/dashboard-demo-v4.css`
- `src/styles/spirit-demo.tokens.css`
- `src/styles/spirit-demo.components.css`
- `src/styles/spirit-demo.layout.css`
- `src/styles/spirit-demo.animations.css`
- `src/styles/spirit-demo.effects.css`
- `src/styles/spirit-trinity-chat.css`

Route-specific and feature surfaces found:

- `src/app/(dashboard)/page.tsx`
- `src/app/chat/page.tsx`
- `src/app/coding/page.tsx`
- `src/app/coding/design-demo/page.tsx`
- `src/app/design-demo/page.tsx`
- `src/app/design-demo/coding/page.tsx`
- `src/app/oracle/page.tsx`
- `src/components/dashboard/`
- `src/components/dashboard/demo-v4/`
- `src/components/chat/`
- `src/components/coding/`
- `src/components/oracle/`

Existing tests and visual tooling found:

- `vitest.config.mjs`
- `playwright.config.mjs`
- `tests/e2e/coding-ui.spec.mjs`
- component tests under `src/components/**/__tests__/`
- style test `src/styles/__tests__/spirit-trinity-chat-thread-rows.test.ts`
- no Storybook config found in inspected paths
- no Chromatic config found in inspected paths
- no screenshot baseline lane found
- no `@playwright/test` dependency found in `package.json`

Source Proxy design docs found:

- `docs/source-proxy-design-apply-lane-v0.1.md`
- existing Source Proxy safety and regression docs in `docs/`

Scout bridge docs found:

- `docs/scout-design-intake-bridge-v0.1.md`

## 3. Gaps and Risks

- Too much design logic is spread across route-specific CSS and feature component files.
- Too few reusable primitives exist for a future generated UI workflow.
- Token drift is likely between `:root` variables in `src/app/globals.css`, `src/theme/spiritPalettes.ts`, route CSS variables, and Design Vault token artifacts.
- Design docs are ahead of implementation.
- Visual verification is planned but not fully active.
- Reverse Designer is not runtime-backed.
- Design Coding Agent is not fully represented as a Source Proxy task lane.
- Adding more UI before simplifying the spine would increase drift and make future review harder.
- Copying external designs instead of creating original SpiritOS packs would create legal, brand, and product-risk problems.
- Storybook is not present, so any preview-surface recommendation must remain optional until explicitly approved.
- Playwright config exists, but local package dependencies do not currently list `@playwright/test`, so screenshot work should be planned before installation.

## 4. Core Architecture Direction

The desired design spine is:

```text
Design references
-> Approved Source Cards
-> Reverse Designer notes
-> Design Vault tokens and patterns
-> Design Pack
-> Visual Verification
-> Design Coding Agent proposal
-> Source Proxy bounded diff preview
-> Human approval
-> Apply
-> Post-apply verification
-> Cartographer documentation update
```

Every design-related agent is proposal-first. No design agent can directly apply changes. Source Proxy remains the only bounded app-write lane, and it still requires explicit human approval before apply.

The v0.2 strategy is to make the design system the spine for future UI work, not to add more random UI. The immediate goal is to inventory, classify, normalize, and define contracts before implementing production changes.

## 5. Authority Model

Design Vault:

Stores approved design evidence, source cards, tokens, pattern cards, screenshots, generated pack evidence, and match reports. It does not apply changes.

Reverse Designer:

Reads approved inputs and produces notes, token drafts, risk flags, and maps only. It does not scrape random sites and does not write production UI.

Design Blender / Style Alchemist:

Creates original SpiritOS design packs from approved ingredients. It must preserve provenance, originality boundaries, and reject conditions.

Visual Verifier:

Captures evidence and reports visual deltas only. It does not approve, apply, or modify app code.

Design Coding Agent:

Proposes bounded UI changes only. It must produce a task spec, allowed files, expected output, checks, rollback notes, and a diff preview path.

Source Proxy:

Owns diff preview, safety checks, allowed files, approval binding, apply, and post-apply reporting.

Cartographer:

Documents system state and updates blueprints after approval. It does not gain apply, commit, push, or approval authority from this plan.

Forbidden actions for all design agents:

- No direct apply.
- No commit.
- No push.
- No deletion.
- No unapproved route creation.
- No scraping random sites.
- No cloning external brands.
- No touching secrets or protected paths.
- No bypassing Source Proxy.
- No autonomous promotion from Scout to coding context.

## 6. Master Phases and Small Increments

### Phase 0.1: Repo and design docs inventory

Goal:
Record the current repo state, design docs, Design Vault artifacts, primitives, theme files, routes, and verification tooling.

Allowed files:
`docs/design-system-overhaul-master-v0.2.md`

Forbidden actions:
No implementation, no route creation, no file deletion, no commit, no push.

Implementation notes:
Use read-only diagnostics and summarize what exists, what is missing, what is docs-only, what is live code, what is safe to build next, and what should wait.

Manual checks:

```bash
cd /home/source/SpiritOS
git status -sb
find docs -maxdepth 1 -type f | sort | grep -Ei 'design|designer|visual|style|scout-design|source-proxy-design|plan-index' || true
find data/design-vault -maxdepth 5 -type f | sort || true
find src/components/ui -maxdepth 2 -type f | sort || true
git diff --check -- docs/design-system-overhaul-master-v0.2.md docs/plan-index.md
```

Expected output:
The plan records real files and marks missing pieces as gaps. Diff check reports no whitespace errors.

Rollback:
Revert only the v0.2 plan file if it was added in this increment.

Stop condition:
Stop if diagnostics show unexpected production UI changes are required.

Next increment title:
Phase 0.2: Classify design docs as active, draft, deprecated, or superseded

### Phase 0.2: Classify design docs as active, draft, deprecated, or superseded

Goal:
Create a reviewable status map for design-related documents.

Allowed files:
`docs/design-system-overhaul-master-v0.2.md`, `docs/plan-index.md`

Forbidden actions:
No deletion, no archive movement, no implementation.

Implementation notes:
Classify docs without changing their content unless a later docs-only increment approves status banners.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -n "design-systems-master-v0.1\|design-blender-style-alchemist\|design-visual-verification\|reverse-designer-approved-inputs" docs/design-system-overhaul-master-v0.2.md
git status -sb
git diff --check -- docs/design-system-overhaul-master-v0.2.md docs/plan-index.md
```

Expected output:
The v0.2 plan identifies which docs are active planning inputs and which are draft or scaffold-only.

Rollback:
Revert only classification text added in this increment.

Stop condition:
Stop if a classification conflicts with the active plan index authority.

Next increment title:
Phase 0.3: Add design-system status summary to plan index

### Phase 0.3: Add design-system status summary to plan index

Goal:
Make the v0.2 plan discoverable in the plan index.

Allowed files:
`docs/plan-index.md`

Forbidden actions:
No removal of existing entries unless a duplicate is clearly documented.

Implementation notes:
Add a short active-plans entry that says the v0.2 doc is planning-only and does not authorize implementation.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -n "design-system-overhaul-master-v0.2" docs/plan-index.md
git diff -- docs/plan-index.md
git diff --check -- docs/plan-index.md
```

Expected output:
Plan index references the v0.2 plan and preserves existing entries.

Rollback:
Remove only the v0.2 plan-index entry.

Stop condition:
Stop if the index would create conflicting implementation authority.

Next increment title:
Phase 0.4: Define source of truth for v0.2

### Phase 0.4: Define source of truth for v0.2

Goal:
Declare that v0.2 is the active design-system overhaul planning spine while v0.1 docs remain supporting references.

Allowed files:
`docs/design-system-overhaul-master-v0.2.md`, `docs/plan-index.md`

Forbidden actions:
No edits to runtime code or production UI.

Implementation notes:
State that implementation requires a later Source Proxy gated increment.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -n "source of truth\|planning-only\|Source Proxy" docs/design-system-overhaul-master-v0.2.md docs/plan-index.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md docs/plan-index.md
```

Expected output:
The plan and index make the authority boundary clear.

Rollback:
Revert only the source-of-truth wording added in this increment.

Stop condition:
Stop if any wording implies direct implementation approval.

Next increment title:
Phase 1.1: Audit existing tokens and CSS variables

### Phase 1.1: Audit existing tokens and CSS variables

Goal:
Inventory current token sources and identify drift between CSS variables, palette files, and Design Vault token artifacts.

Allowed files:
`docs/design-system-overhaul-master-v0.2.md`, later docs-only audit files if approved.

Forbidden actions:
No token renaming, no CSS edits, no palette edits.

Implementation notes:
Read `src/app/globals.css`, `src/theme/spiritPalettes.ts`, `src/styles/*.css`, and Design Vault token files.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -Rho -- '--[a-zA-Z0-9_-]*' src/app/globals.css src/styles src/theme data/design-vault 2>/dev/null | sort -u | head -200
git status -sb
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
A token inventory exists as planning evidence. No implementation files change.

Rollback:
Remove only the audit notes from the plan or audit doc.

Stop condition:
Stop if token ownership is unclear enough to risk accidental runtime changes.

Next increment title:
Phase 1.2: Define canonical token categories

### Phase 1.2: Define canonical token categories

Goal:
Define canonical token categories for primitive, semantic, component, motion, responsive, and accessibility tokens.

Allowed files:
Docs-only design-system planning files.

Forbidden actions:
No runtime token import, no CSS changes.

Implementation notes:
Align categories with `data/design-vault/token-model-v0.1.md` and app needs.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -n "Primitive Tokens\|Semantic Tokens\|Component Tokens\|Motion Tokens\|Responsive Tokens\|Accessibility Tokens" data/design-vault/token-model-v0.1.md docs/design-system-overhaul-master-v0.2.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Canonical categories are defined without changing live CSS.

Rollback:
Revert only the category text.

Stop condition:
Stop if categories conflict with Design Vault token model.

Next increment title:
Phase 1.3: Create token naming rules

### Phase 1.3: Create token naming rules

Goal:
Define naming rules for SpiritOS tokens and aliases.

Allowed files:
Docs-only design-system planning files.

Forbidden actions:
No token migration, no global CSS edits.

Implementation notes:
Prefer stable semantic names and document alias rules for legacy route-specific names.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -n "token naming\|legacy alias\|semantic" docs/design-system-overhaul-master-v0.2.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Token naming rules are reviewable before any rename.

Rollback:
Remove only the naming-rule section.

Stop condition:
Stop if the naming rules require immediate app changes.

Next increment title:
Phase 1.4: Create token migration map from current CSS and palette files

### Phase 1.4: Create token migration map from current CSS and palette files

Goal:
Map existing `--spirit-*`, `--ddv4-*`, `--trinity-*`, and Tailwind theme values to future canonical tokens.

Allowed files:
Docs-only migration map.

Forbidden actions:
No CSS rewrites, no palette rewrites.

Implementation notes:
Mark each mapping as keep, alias, migrate, or retire-later.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -Rho -- '--\\(spirit\\|ddv4\\|trinity\\)-[a-zA-Z0-9_-]*' src/app/globals.css src/styles data/design-vault 2>/dev/null | sort -u | wc -l
grep -n "keep\|alias\|migrate\|retire-later" docs/design-system-overhaul-master-v0.2.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Migration map is documented. No runtime token value changes.

Rollback:
Revert only the migration map.

Stop condition:
Stop if a token cannot be mapped without inspecting active UI behavior.

Next increment title:
Phase 1.5: Add accessibility token requirements for contrast, focus, motion, and touch targets

### Phase 1.5: Add accessibility token requirements for contrast, focus, motion, and touch targets

Goal:
Define token-level accessibility requirements.

Allowed files:
Docs-only design-system planning files.

Forbidden actions:
No visual changes, no CSS changes.

Implementation notes:
Cover contrast targets, focus indicators, reduced motion, hit areas, state visibility, and text scale behavior.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -n "contrast\|focus\|reduced motion\|touch target\|state visibility" docs/design-system-overhaul-master-v0.2.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Accessibility requirements are stated as future acceptance criteria.

Rollback:
Remove only accessibility requirement text.

Stop condition:
Stop if requirements are too vague to verify later.

Next increment title:
Phase 2.1: Audit current src/components/ui primitives

### Phase 2.1: Audit current src/components/ui primitives

Goal:
Audit current reusable UI primitives and identify missing primitives needed for future generated UI.

Allowed files:
Docs-only audit files.

Forbidden actions:
No component edits, no exports changed.

Implementation notes:
Inspect `GlassPanel`, `SectionLabel`, `SpiritButton`, and `index.ts`.

Manual checks:

```bash
cd /home/source/SpiritOS
find src/components/ui -maxdepth 2 -type f | sort
grep -n "GlassPanel\|SectionLabel\|SpiritButton" docs/design-system-overhaul-master-v0.2.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Primitive inventory is recorded and missing pieces are listed.

Rollback:
Revert only primitive audit text.

Stop condition:
Stop if the audit suggests immediate edits to production components.

Next increment title:
Phase 2.2: Define required primitive set

### Phase 2.2: Define required primitive set

Goal:
Define the minimum primitive set for buttons, inputs, panels, cards, badges, tabs, dialogs, menus, toolbars, rails, fields, and status indicators.

Allowed files:
Docs-only primitive contract.

Forbidden actions:
No component scaffolding yet.

Implementation notes:
Separate primitives from feature patterns.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -n "button\|input\|panel\|card\|badge\|tabs\|dialog\|menu\|toolbar\|rail" docs/design-system-overhaul-master-v0.2.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Required primitive set is documented.

Rollback:
Remove only required primitive set text.

Stop condition:
Stop if the list grows into route-specific feature design.

Next increment title:
Phase 2.3: Define component anatomy contracts

### Phase 2.3: Define component anatomy contracts

Goal:
Define anatomy contracts for primitives so generated UI can target predictable slots.

Allowed files:
Docs-only primitive contract.

Forbidden actions:
No TypeScript component changes.

Implementation notes:
Define slots such as root, header, body, footer, icon, action, state, label, helper, and error.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -n "root\|header\|body\|footer\|icon\|action\|helper\|error" docs/design-system-overhaul-master-v0.2.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Anatomy contracts are ready for later implementation.

Rollback:
Remove anatomy contract text.

Stop condition:
Stop if contracts conflict with existing component usage.

Next increment title:
Phase 2.4: Define variant rules

### Phase 2.4: Define variant rules

Goal:
Define variant rules for tone, size, density, emphasis, state, and motion.

Allowed files:
Docs-only primitive contract.

Forbidden actions:
No variant implementation yet.

Implementation notes:
Define a small stable matrix and reject one-off route-specific variants.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -n "tone\|size\|density\|emphasis\|state\|motion" docs/design-system-overhaul-master-v0.2.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Variant rules are documented and limited.

Rollback:
Remove variant rule text.

Stop condition:
Stop if variants become feature-specific.

Next increment title:
Phase 2.5: Define no-route-specific-style leakage rule

### Phase 2.5: Define no-route-specific-style leakage rule

Goal:
Prevent route CSS from becoming the source of truth for reusable primitives.

Allowed files:
Docs-only design-system planning files.

Forbidden actions:
No CSS movement yet.

Implementation notes:
Document that route CSS may consume tokens and compose patterns, but should not define reusable primitive behavior.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -n "route-specific\|leakage\|source of truth" docs/design-system-overhaul-master-v0.2.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
The leakage rule is explicit.

Rollback:
Remove only the leakage rule.

Stop condition:
Stop if the rule would require immediate route CSS edits.

Next increment title:
Phase 3.1: Define layout patterns

### Phase 3.1: Define layout patterns

Goal:
Define reusable layout patterns without adding UI bloat.

Allowed files:
Docs-only pattern plan.

Forbidden actions:
No new app routes, no preview route yet.

Implementation notes:
Cover shell, rail, split pane, dashboard grid, content stack, command surface, and responsive behavior.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -n "shell\|rail\|split pane\|dashboard grid\|content stack\|command surface" docs/design-system-overhaul-master-v0.2.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Layout patterns are documented as contracts, not components.

Rollback:
Remove layout pattern text.

Stop condition:
Stop if patterns imply unapproved route creation.

Next increment title:
Phase 3.2: Define dashboard card patterns

### Phase 3.2: Define dashboard card patterns

Goal:
Define reusable dashboard card patterns from existing dashboard components and the internal demo pack.

Allowed files:
Docs-only pattern plan.

Forbidden actions:
No production dashboard component edits.

Implementation notes:
Classify status cards, metric cards, control cards, activity cards, and health cards.

Manual checks:

```bash
cd /home/source/SpiritOS
find src/components/dashboard -maxdepth 1 -type f | sort
grep -n "status card\|metric card\|control card\|activity card\|health card" docs/design-system-overhaul-master-v0.2.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Dashboard card patterns are defined without changing dashboard code.

Rollback:
Remove dashboard pattern text.

Stop condition:
Stop if pattern definitions need product decisions.

Next increment title:
Phase 3.3: Define chat surface patterns

### Phase 3.3: Define chat surface patterns

Goal:
Define chat patterns for thread rails, message rows, composer, tool activity, model controls, and mobile drawers.

Allowed files:
Docs-only pattern plan.

Forbidden actions:
No chat component or CSS edits.

Implementation notes:
Use `src/components/chat/` and `src/styles/spirit-trinity-chat.css` as inspected references only.

Manual checks:

```bash
cd /home/source/SpiritOS
find src/components/chat -maxdepth 1 -type f | sort | head -80
grep -n "thread rail\|message row\|composer\|tool activity\|model control\|mobile drawer" docs/design-system-overhaul-master-v0.2.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Chat patterns are documented as future reusable patterns.

Rollback:
Remove chat pattern text.

Stop condition:
Stop if pattern extraction would require immediate route styling changes.

Next increment title:
Phase 3.4: Define coding console patterns

### Phase 3.4: Define coding console patterns

Goal:
Define coding console patterns for task panes, approval gates, diff previews, run output, safety states, and mobile review.

Allowed files:
Docs-only pattern plan.

Forbidden actions:
No coding UI changes.

Implementation notes:
Align with existing `/coding` Source Proxy safety boundaries.

Manual checks:

```bash
cd /home/source/SpiritOS
find src/components/coding -maxdepth 2 -type f | sort
grep -n "task pane\|approval gate\|diff preview\|run output\|safety state\|mobile review" docs/design-system-overhaul-master-v0.2.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Coding console patterns are documented and Source Proxy gated.

Rollback:
Remove coding pattern text.

Stop condition:
Stop if this conflicts with `docs/codingUI.md`.

Next increment title:
Phase 3.5: Define Oracle voice surface patterns

### Phase 3.5: Define Oracle voice surface patterns

Goal:
Define Oracle voice patterns for status, controls, transcript, visualizer, and voice surface layout.

Allowed files:
Docs-only pattern plan.

Forbidden actions:
No Oracle component or CSS edits.

Implementation notes:
Use `src/components/oracle/` as inspected reference only.

Manual checks:

```bash
cd /home/source/SpiritOS
find src/components/oracle -maxdepth 2 -type f | sort
grep -n "Oracle\|voice surface\|status\|controls\|transcript\|visualizer" docs/design-system-overhaul-master-v0.2.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Oracle voice patterns are documented.

Rollback:
Remove Oracle pattern text.

Stop condition:
Stop if accessibility or voice state requirements are unknown.

Next increment title:
Phase 3.6: Decide whether a preview route is needed, but do not create it yet

### Phase 3.6: Decide whether a preview route is needed, but do not create it yet

Goal:
Decide whether a design-system preview route is needed after contracts are stable.

Allowed files:
Docs-only decision record.

Forbidden actions:
No route creation, no Storybook install, no app imports.

Implementation notes:
Compare a local preview route, Storybook, and docs-only review. Recommend a route only as a later Source Proxy gated increment if needed.

Manual checks:

```bash
cd /home/source/SpiritOS
find src/app -maxdepth 4 -type f | sort | grep -Ei 'design|coding|dashboard|chat|oracle' || true
grep -n "preview route\|Storybook\|docs-only" docs/design-system-overhaul-master-v0.2.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Preview-route decision is documented. No route is created.

Rollback:
Remove preview decision text.

Stop condition:
Stop if stakeholders cannot choose preview surface authority.

Next increment title:
Phase 4.1: Audit Playwright readiness

### Phase 4.1: Audit Playwright readiness

Goal:
Audit Playwright, screenshot, and visual test readiness.

Allowed files:
Docs-only visual verification plan.

Forbidden actions:
No package install, no browser install, no screenshot generation.

Implementation notes:
Record that `playwright.config.mjs` exists and `@playwright/test` is not listed in `package.json`.

Manual checks:

```bash
cd /home/source/SpiritOS
ls -la playwright.config.mjs package.json vitest.config.mjs 2>/dev/null || true
grep -n "\"@playwright/test\"\\|storybook\\|chromatic\\|toHaveScreenshot\\|visual" package.json playwright.config.mjs docs/*.md 2>/dev/null || true
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Tooling state is documented without installing anything.

Rollback:
Remove Playwright readiness notes.

Stop condition:
Stop if visual verification requires dependency changes.

Next increment title:
Phase 4.2: Define screenshot target list

### Phase 4.2: Define screenshot target list

Goal:
Define future screenshot targets for dashboard, chat, coding, Oracle, and design pack previews.

Allowed files:
Docs-only visual verification plan.

Forbidden actions:
No screenshots captured.

Implementation notes:
Use existing routes and approved Design Vault packs only.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -n "dashboard\|chat\|coding\|Oracle\|screenshot target" docs/design-system-overhaul-master-v0.2.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Screenshot target list is documented.

Rollback:
Remove screenshot target list.

Stop condition:
Stop if a target route is unstable or unapproved.

Next increment title:
Phase 4.3: Add optional visual capture plan

### Phase 4.3: Add optional visual capture plan

Goal:
Define an optional capture plan that runs only when tooling is installed and explicitly approved.

Allowed files:
Docs-only visual verification plan.

Forbidden actions:
No install, no baseline creation, no automatic test lane.

Implementation notes:
Use safe detection before any Playwright command.

Manual checks:

```bash
cd /home/source/SpiritOS
if ls playwright.config.* >/dev/null 2>&1 && node -e "require.resolve('@playwright/test/package.json')" >/dev/null 2>&1; then
  npx playwright test --list
elif ls playwright.config.* >/dev/null 2>&1; then
  echo "Playwright config found, but @playwright/test is not installed locally. Skipping Playwright check for this increment."
else
  echo "Playwright config not found, skipping Playwright check for this increment."
fi
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Plan contains a skip-safe capture command.

Rollback:
Remove optional capture plan.

Stop condition:
Stop if a capture plan would require dependency installation.

Next increment title:
Phase 4.4: Add visual diff report plan

### Phase 4.4: Add visual diff report plan

Goal:
Define the shape of a visual diff report attached to design packs and Source Proxy proposals.

Allowed files:
Docs-only visual verification plan.

Forbidden actions:
No screenshot comparison implementation.

Implementation notes:
Include route, viewport, baseline, candidate, threshold, status, delta summary, and reviewer notes.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -n "visual diff\|baseline\|candidate\|threshold\|delta summary" docs/design-system-overhaul-master-v0.2.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Visual diff report shape is documented.

Rollback:
Remove visual diff report text.

Stop condition:
Stop if thresholds are treated as automatic approval.

Next increment title:
Phase 4.5: Define mobile viewport checks

### Phase 4.5: Define mobile viewport checks

Goal:
Define mobile viewport checks for overflow, touch targets, fixed bars, drawers, and readable text.

Allowed files:
Docs-only visual verification plan.

Forbidden actions:
No component edits.

Implementation notes:
Use existing Playwright project names where available.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -n "Mobile Safari\|Pixel 5\|iPad\|overflow\|touch target\|drawer" docs/design-system-overhaul-master-v0.2.md playwright.config.mjs
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Mobile checks are defined.

Rollback:
Remove mobile viewport check text.

Stop condition:
Stop if route ownership is unclear.

Next increment title:
Phase 4.6: Define accessibility smoke checks

### Phase 4.6: Define accessibility smoke checks

Goal:
Define accessibility smoke checks for keyboard order, focus visibility, reduced motion, contrast, and labeling.

Allowed files:
Docs-only visual verification plan.

Forbidden actions:
No axe install, no test implementation.

Implementation notes:
Document optional future axe or manual checks without installing dependencies.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -n "keyboard\|focus visibility\|reduced motion\|contrast\|label" docs/design-system-overhaul-master-v0.2.md
grep -n "axe" package.json docs/design-system-overhaul-master-v0.2.md 2>/dev/null || true
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Accessibility smoke checks are documented.

Rollback:
Remove accessibility smoke check text.

Stop condition:
Stop if a dependency is required before planning can proceed.

Next increment title:
Phase 5.1: Define Design Source Card schema

### Phase 5.1: Define Design Source Card schema

Goal:
Define v0.2 source-card fields and state transitions.

Allowed files:
Design Vault docs and planning docs only.

Forbidden actions:
No source approval automation, no Scout promotion.

Implementation notes:
Extend current source-card template conceptually before editing JSON schema.

Manual checks:

```bash
cd /home/source/SpiritOS
test -f data/design-vault/source-cards/source-card.template.json && sed -n '1,220p' data/design-vault/source-cards/source-card.template.json
grep -n "source-card\|approval status\|approved use mode" docs/design-system-overhaul-master-v0.2.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Source-card v0.2 schema is planned.

Rollback:
Remove source-card schema text.

Stop condition:
Stop if schema changes require migration of existing cards.

Next increment title:
Phase 5.2: Define Design Token Pack schema

### Phase 5.2: Define Design Token Pack schema

Goal:
Define the design token pack schema for canonical tokens and source traceability.

Allowed files:
Design Vault docs and planning docs only.

Forbidden actions:
No runtime token loading.

Implementation notes:
Align with existing `tokens.raw.json`, `tokens.json`, and `theme.css` pack artifacts.

Manual checks:

```bash
cd /home/source/SpiritOS
find data/design-vault/packs/internal-dashboard-demo-v4 -maxdepth 1 -type f | sort
grep -n "token pack\|source traceability\|tokens.raw.json\|tokens.json" docs/design-system-overhaul-master-v0.2.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Token pack schema is documented.

Rollback:
Remove token pack schema text.

Stop condition:
Stop if schema cannot represent current internal pack.

Next increment title:
Phase 5.3: Define Component Pattern Card schema

### Phase 5.3: Define Component Pattern Card schema

Goal:
Define component pattern cards for reusable layout and component patterns.

Allowed files:
Design Vault docs and planning docs only.

Forbidden actions:
No component implementation.

Implementation notes:
Include pattern id, source evidence, anatomy, variants, tokens, accessibility notes, and allowed use.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -n "Component Pattern Card\|pattern id\|anatomy\|variants\|accessibility notes" docs/design-system-overhaul-master-v0.2.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Pattern card schema is defined.

Rollback:
Remove pattern card schema text.

Stop condition:
Stop if pattern cards duplicate component implementation.

Next increment title:
Phase 5.4: Define Style Blend Recipe schema

### Phase 5.4: Define Style Blend Recipe schema

Goal:
Define how Design Blender records approved ingredients and generated originality constraints.

Allowed files:
Design Vault docs and planning docs only.

Forbidden actions:
No generator integration, no external asset ingestion.

Implementation notes:
Include inputs, approved use modes, avoided elements, influence notes, originality score, and reject reasons.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -n "Style Blend Recipe\|ingredients\|influence notes\|originality score\|reject reasons" docs/design-system-overhaul-master-v0.2.md docs/design-blender-style-alchemist-v0.1.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Style blend recipe schema is documented.

Rollback:
Remove recipe schema text.

Stop condition:
Stop if a recipe could imply permission laundering.

Next increment title:
Phase 5.5: Define approval and rejection states

### Phase 5.5: Define approval and rejection states

Goal:
Define draft, candidate, approved, rejected, superseded, and retired states for cards and packs.

Allowed files:
Design Vault docs and planning docs only.

Forbidden actions:
No automated state changes.

Implementation notes:
Keep approval human-controlled and separate from apply approval.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -n "draft\|candidate\|approved\|rejected\|superseded\|retired" docs/design-system-overhaul-master-v0.2.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Approval and rejection states are documented.

Rollback:
Remove state model text.

Stop condition:
Stop if states blur evidence approval and apply approval.

Next increment title:
Phase 6.1: Define approved inputs only

### Phase 6.1: Define approved inputs only

Goal:
Lock Reverse Designer to approved source cards and approved pack evidence only.

Allowed files:
Reverse Designer docs and planning docs only.

Forbidden actions:
No URL fetching, no image processing, no Figma API wiring.

Implementation notes:
Align with `docs/reverse-designer-approved-inputs-v0.1.md`.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -n "approved source card\|Accepted Input Types\|URL Boundary\|Figma Boundary" docs/reverse-designer-approved-inputs-v0.1.md docs/design-system-overhaul-master-v0.2.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Reverse Designer inputs are constrained.

Rollback:
Remove Reverse Designer input text.

Stop condition:
Stop if any input path lacks source-card approval.

Next increment title:
Phase 6.2: Define analysis output schema

### Phase 6.2: Define analysis output schema

Goal:
Define Reverse Designer output schema for notes, raw tokens, normalized token drafts, component maps, risk flags, and visual evidence links.

Allowed files:
Reverse Designer docs and planning docs only.

Forbidden actions:
No app UI writes.

Implementation notes:
Output must land in Design Vault proposal artifacts only.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -n "notes\|raw token\|normalized token\|component maps\|risk flags\|visual evidence" docs/design-system-overhaul-master-v0.2.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Analysis output schema is documented.

Rollback:
Remove schema text.

Stop condition:
Stop if outputs are not clearly docs or Design Vault artifacts.

Next increment title:
Phase 6.3: Define source risk flags

### Phase 6.3: Define source risk flags

Goal:
Define risk flags for unclear rights, protected assets, brand likeness, crawler risk, accessibility risk, and privacy risk.

Allowed files:
Reverse Designer docs and planning docs only.

Forbidden actions:
No external analysis.

Implementation notes:
Risk flags should block or downgrade analysis until reviewed.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -n "unclear rights\|protected assets\|brand likeness\|crawler risk\|accessibility risk\|privacy risk" docs/design-system-overhaul-master-v0.2.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Risk flags are documented.

Rollback:
Remove risk flag text.

Stop condition:
Stop if risk flags do not have clear review outcomes.

Next increment title:
Phase 6.4: Define no-clone originality boundary

### Phase 6.4: Define no-clone originality boundary

Goal:
Define the line between inspired analysis and cloning external brands or trade dress.

Allowed files:
Reverse Designer docs and planning docs only.

Forbidden actions:
No exact external copying without explicit rights.

Implementation notes:
Public references default to inspired-language-only.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -n "no-clone\|inspired-language-only\|trade dress\|external brands" docs/design-system-overhaul-master-v0.2.md docs/reverse-designer-approved-inputs-v0.1.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Originality boundary is explicit.

Rollback:
Remove no-clone boundary text.

Stop condition:
Stop if any language suggests laundering protected designs.

Next increment title:
Phase 6.5: Define manual import path from source card to Design Vault

### Phase 6.5: Define manual import path from source card to Design Vault

Goal:
Define how approved source-card evidence becomes Design Vault notes and pack artifacts.

Allowed files:
Reverse Designer docs, Design Vault docs, and planning docs only.

Forbidden actions:
No automated import, no Scout auto-promotion.

Implementation notes:
Manual import path must preserve source-card approval and reviewer metadata.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -n "manual import\|Design Vault\|source-card approval\|reviewer" docs/design-system-overhaul-master-v0.2.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Manual import path is defined.

Rollback:
Remove manual import text.

Stop condition:
Stop if import would bypass source-card approval.

Next increment title:
Phase 7.1: Define blend inputs

### Phase 7.1: Define blend inputs

Goal:
Define approved input types for Style Alchemist blends.

Allowed files:
Design Blender docs and planning docs only.

Forbidden actions:
No generation, no external asset ingestion.

Implementation notes:
Inputs must be approved packs, owned references, licensed references, client-approved references, open-source permitted references, or inspiration-only notes.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -n "Allowed Inputs\|approved Design Vault packs\|licensed references\|inspiration-only" docs/design-blender-style-alchemist-v0.1.md docs/design-system-overhaul-master-v0.2.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Blend inputs are constrained to approved ingredients.

Rollback:
Remove blend input text.

Stop condition:
Stop if any input lacks provenance.

Next increment title:
Phase 7.2: Define originality scoring

### Phase 7.2: Define originality scoring

Goal:
Define originality scoring for generated SpiritOS design packs.

Allowed files:
Design Blender docs and planning docs only.

Forbidden actions:
No generator implementation.

Implementation notes:
Score distinct composition, absence of protected assets, no single external source dominance, and provenance clarity.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -n "originality scoring\|single external source\|protected assets\|provenance" docs/design-system-overhaul-master-v0.2.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Originality scoring is defined.

Rollback:
Remove originality scoring text.

Stop condition:
Stop if score cannot produce reject decisions.

Next increment title:
Phase 7.3: Define SpiritOS brand fit scoring

### Phase 7.3: Define SpiritOS brand fit scoring

Goal:
Define how blended packs are evaluated for SpiritOS brand fit.

Allowed files:
Design Blender docs and planning docs only.

Forbidden actions:
No visual changes.

Implementation notes:
Score operational clarity, calm density, glass treatment discipline, contrast, state clarity, and product fit.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -n "brand fit\|operational clarity\|calm density\|glass treatment\|state clarity" docs/design-system-overhaul-master-v0.2.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Brand fit scoring is documented.

Rollback:
Remove brand fit scoring text.

Stop condition:
Stop if scoring becomes subjective without examples.

Next increment title:
Phase 7.4: Define generated design pack schema

### Phase 7.4: Define generated design pack schema

Goal:
Define generated design pack files, provenance, tokens, recipes, screenshots, and verification reports.

Allowed files:
Design Vault docs and planning docs only.

Forbidden actions:
No generated UI or preview route.

Implementation notes:
Build on current pack shape under `data/design-vault/packs/<pack-id>/`.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -n "generated design pack\|source-card.json\|tokens.json\|components-map.json\|match-report.json" docs/design-system-overhaul-master-v0.2.md docs/design-pack-authoring-v0.1.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Generated design pack schema is documented.

Rollback:
Remove generated pack schema text.

Stop condition:
Stop if generated pack output implies runtime import.

Next increment title:
Phase 7.5: Define reject conditions

### Phase 7.5: Define reject conditions

Goal:
Define when a blended style or design pack must be rejected.

Allowed files:
Design Blender docs and planning docs only.

Forbidden actions:
No automated rejection behavior.

Implementation notes:
Reject unclear rights, protected assets, brand cloning, weak accessibility, unclear provenance, and poor SpiritOS fit.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -n "reject\|unclear rights\|brand cloning\|weak accessibility\|poor SpiritOS fit" docs/design-system-overhaul-master-v0.2.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Reject conditions are explicit.

Rollback:
Remove reject condition text.

Stop condition:
Stop if reject conditions do not protect external source boundaries.

Next increment title:
Phase 8.1: Define role in agent registry, if applicable

### Phase 8.1: Define role in agent registry, if applicable

Goal:
Define whether Design Coding Agent belongs in the agent registry and what authority it has.

Allowed files:
Planning docs and agent registry docs if a later audit identifies them.

Forbidden actions:
No agent implementation, no registry code changes.

Implementation notes:
The agent proposes bounded UI work only and never applies directly.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -Rn "agent registry\\|Design Coding Agent\\|coding agent" docs _blueprints source_proxy src 2>/dev/null | head -120
grep -n "Design Coding Agent" docs/design-system-overhaul-master-v0.2.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Role and authority are documented or listed as a gap if no registry exists.

Rollback:
Remove role text.

Stop condition:
Stop if registry ownership is unclear.

Next increment title:
Phase 8.2: Define design pack to task spec handoff

### Phase 8.2: Define design pack to task spec handoff

Goal:
Define how a design pack becomes a bounded Source Proxy task spec.

Allowed files:
Planning docs and Source Proxy design lane docs.

Forbidden actions:
No Source Proxy behavior changes.

Implementation notes:
Task spec should include design pack id, source card id, target files, allowed files, expected output, checks, rollback, and stop condition.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -n "design pack id\|source card id\|target files\|allowed files\|expected output\|rollback" docs/design-system-overhaul-master-v0.2.md docs/source-proxy-design-apply-lane-v0.1.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Handoff contract is documented.

Rollback:
Remove handoff contract text.

Stop condition:
Stop if task spec cannot bind to exact allowed files.

Next increment title:
Phase 8.3: Define allowed_files derivation

### Phase 8.3: Define allowed_files derivation

Goal:
Define how allowed files are derived for a design implementation proposal.

Allowed files:
Planning docs and Source Proxy design lane docs.

Forbidden actions:
No apply-lane implementation.

Implementation notes:
Allowed files must come from human task scope, route ownership, component ownership, and explicit Source Proxy approval.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -n "allowed_files\|allowed files\|route ownership\|component ownership" docs/design-system-overhaul-master-v0.2.md docs/source-proxy-design-apply-lane-v0.1.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Allowed-file derivation is constrained.

Rollback:
Remove allowed-files text.

Stop condition:
Stop if allowed files would be broad or inferred automatically.

Next increment title:
Phase 8.4: Define diff preview requirements

### Phase 8.4: Define diff preview requirements

Goal:
Define required diff preview fields for design proposals.

Allowed files:
Planning docs and Source Proxy design lane docs.

Forbidden actions:
No Source Proxy code changes.

Implementation notes:
Diff preview should show files, hunks, design evidence, visual evidence, risk notes, checks, and approval binding.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -n "diff preview\|hunks\|design evidence\|visual evidence\|approval binding" docs/design-system-overhaul-master-v0.2.md docs/source-proxy-design-apply-lane-v0.1.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Diff preview requirements are documented.

Rollback:
Remove diff preview text.

Stop condition:
Stop if preview omits visual or rollback evidence.

Next increment title:
Phase 8.5: Define manual checks and expected output requirements

### Phase 8.5: Define manual checks and expected output requirements

Goal:
Require every design implementation proposal to include paste-ready manual checks and expected outputs.

Allowed files:
Planning docs and Source Proxy design lane docs.

Forbidden actions:
No check implementation yet.

Implementation notes:
Checks should include status, lint/type/test commands when relevant, visual checks when available, and diff check.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -n "manual checks\|Expected output\|Actual output\|Dirty files" docs/design-system-overhaul-master-v0.2.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Manual check requirements are explicit.

Rollback:
Remove manual check requirement text.

Stop condition:
Stop if a proposal lacks paste-ready verification.

Next increment title:
Phase 8.6: Define rollback and post-apply verification

### Phase 8.6: Define rollback and post-apply verification

Goal:
Define rollback notes and post-apply verification requirements for design changes.

Allowed files:
Planning docs and Source Proxy design lane docs.

Forbidden actions:
No apply behavior changes.

Implementation notes:
Rollback must name affected files and avoid reverting unrelated dirty work.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -n "rollback\|post-apply verification\|unrelated dirty" docs/design-system-overhaul-master-v0.2.md docs/source-proxy-design-apply-lane-v0.1.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Rollback and post-apply verification rules are documented.

Rollback:
Remove rollback requirement text.

Stop condition:
Stop if rollback depends on destructive git commands.

Next increment title:
Phase 9.1: Define candidate-only design source intake

### Phase 9.1: Define candidate-only design source intake

Goal:
Define Scout design intake as candidate-only metadata.

Allowed files:
Scout bridge docs and planning docs.

Forbidden actions:
No Scout runtime changes, no automatic source card creation.

Implementation notes:
Scout may suggest candidates. Humans decide whether to create source-card drafts.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -n "candidate-only\|candidate design reference\|source-card draft" docs/design-system-overhaul-master-v0.2.md docs/scout-design-intake-bridge-v0.1.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Candidate-only intake is documented.

Rollback:
Remove candidate intake text.

Stop condition:
Stop if Scout would auto-promote anything.

Next increment title:
Phase 9.2: Define approval gate before Design Vault import

### Phase 9.2: Define approval gate before Design Vault import

Goal:
Define the human approval gate required before a Scout candidate can enter Design Vault.

Allowed files:
Scout bridge docs and planning docs.

Forbidden actions:
No import implementation.

Implementation notes:
Approval must record rights basis, reviewer, reviewed date, approved use mode, and disallowed assets.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -n "approval gate\|rights basis\|reviewed date\|approved use mode\|disallowed assets" docs/design-system-overhaul-master-v0.2.md docs/scout-design-intake-bridge-v0.1.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Approval gate is explicit.

Rollback:
Remove approval gate text.

Stop condition:
Stop if approval is implied from Scout discovery.

Next increment title:
Phase 9.3: Define trust labels

### Phase 9.3: Define trust labels

Goal:
Define trust labels for internal, owned, licensed, client-approved, open-source permitted, public inspiration, unclear, and rejected.

Allowed files:
Scout bridge docs and planning docs.

Forbidden actions:
No automatic trust scoring.

Implementation notes:
Trust labels guide review and do not approve sources by themselves.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -n "trust label\|internal\|owned\|licensed\|client-approved\|open-source\|public inspiration\|unclear\|rejected" docs/design-system-overhaul-master-v0.2.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Trust labels are defined.

Rollback:
Remove trust label text.

Stop condition:
Stop if labels become automatic approval.

Next increment title:
Phase 9.4: Define no autonomous promotion rule

### Phase 9.4: Define no autonomous promotion rule

Goal:
Block autonomous promotion from Scout candidate to Design Vault, Reverse Designer, Design Blender, coding context, or Source Proxy proposal.

Allowed files:
Scout bridge docs and planning docs.

Forbidden actions:
No Scout runtime changes.

Implementation notes:
Promotion requires explicit human action at each gate.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -n "autonomous promotion\|auto-promotion\|coding context\|explicit human" docs/design-system-overhaul-master-v0.2.md docs/scout-design-intake-bridge-v0.1.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
No-autonomous-promotion rule is clear.

Rollback:
Remove promotion rule text.

Stop condition:
Stop if any wording permits automatic coding tasks.

Next increment title:
Phase 9.5: Define later bridge into Reverse Designer

### Phase 9.5: Define later bridge into Reverse Designer

Goal:
Define the later manual bridge from approved source card to Reverse Designer analysis.

Allowed files:
Scout bridge docs, Reverse Designer docs, and planning docs.

Forbidden actions:
No Reverse Designer runtime implementation.

Implementation notes:
Scout candidates must become approved source cards before Reverse Designer can read them.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -n "Reverse Designer\|approved source cards\|Scout candidates" docs/design-system-overhaul-master-v0.2.md docs/scout-design-intake-bridge-v0.1.md docs/reverse-designer-approved-inputs-v0.1.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Later bridge is manual and approval-gated.

Rollback:
Remove bridge text.

Stop condition:
Stop if Reverse Designer could read unapproved candidates.

Next increment title:
Phase 10.1: Define design-specific safety reasons

### Phase 10.1: Define design-specific safety reasons

Goal:
Define Source Proxy design-lane safety reasons.

Allowed files:
Source Proxy design docs and planning docs.

Forbidden actions:
No Source Proxy code changes.

Implementation notes:
Safety reasons should include unapproved source, broad allowed files, protected path, missing visual evidence, missing rollback, and route creation not approved.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -n "safety reasons\|unapproved source\|broad allowed files\|protected path\|missing visual evidence\|route creation" docs/design-system-overhaul-master-v0.2.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Design-specific safety reasons are documented.

Rollback:
Remove safety reason text.

Stop condition:
Stop if safety reasons cannot block apply.

Next increment title:
Phase 10.2: Define visual verification evidence attachment

### Phase 10.2: Define visual verification evidence attachment

Goal:
Define how visual evidence attaches to a Source Proxy design proposal.

Allowed files:
Source Proxy design docs and planning docs.

Forbidden actions:
No screenshot generation, no Source Proxy code changes.

Implementation notes:
Evidence should include pack id, screenshots, viewport list, match report, known deltas, and reviewer notes.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -n "visual verification evidence\|pack id\|screenshots\|viewport\|match report\|known deltas" docs/design-system-overhaul-master-v0.2.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Evidence attachment contract is documented.

Rollback:
Remove evidence attachment text.

Stop condition:
Stop if evidence is treated as apply approval.

Next increment title:
Phase 10.3: Define bounded UI diff contract

### Phase 10.3: Define bounded UI diff contract

Goal:
Define the bounded UI diff contract for design proposals.

Allowed files:
Source Proxy design docs and planning docs.

Forbidden actions:
No apply-lane implementation.

Implementation notes:
Diffs must be limited to approved files and must not include unrelated cleanup.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -n "bounded UI diff\|approved files\|unrelated cleanup\|allowed files" docs/design-system-overhaul-master-v0.2.md docs/source-proxy-design-apply-lane-v0.1.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Bounded diff contract is defined.

Rollback:
Remove bounded diff text.

Stop condition:
Stop if allowed-file scope is not exact.

Next increment title:
Phase 10.4: Define approval gate copy

### Phase 10.4: Define approval gate copy

Goal:
Define concise approval gate copy for design apply proposals.

Allowed files:
Source Proxy design docs and planning docs.

Forbidden actions:
No UI copy implementation.

Implementation notes:
Copy must show what will change, why, allowed files, evidence, checks, rollback, and what is not authorized.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -n "approval gate copy\|what will change\|what is not authorized\|rollback" docs/design-system-overhaul-master-v0.2.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Approval gate copy requirements are defined.

Rollback:
Remove approval gate copy text.

Stop condition:
Stop if copy implies commit or push authority.

Next increment title:
Phase 10.5: Define post-apply visual verification

### Phase 10.5: Define post-apply visual verification

Goal:
Define post-apply visual verification evidence for design changes.

Allowed files:
Source Proxy design docs and planning docs.

Forbidden actions:
No post-apply implementation.

Implementation notes:
Post-apply report should include changed files, commands, actual output, screenshots if available, deltas, dirty files, rollback, and follow-up status.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -n "post-apply visual verification\|changed files\|actual output\|dirty files\|follow-up" docs/design-system-overhaul-master-v0.2.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Post-apply verification is documented.

Rollback:
Remove post-apply verification text.

Stop condition:
Stop if verification requires unavailable tooling without a skip path.

Next increment title:
Phase 11.1: Define design-system blueprint updates

### Phase 11.1: Define design-system blueprint updates

Goal:
Define how Cartographer documents design-system blueprint updates after approval.

Allowed files:
Cartographer docs, blueprints, and planning docs after explicit approval.

Forbidden actions:
No Cartographer authority expansion, no automatic blueprint writes.

Implementation notes:
Blueprint updates happen after approved design-system changes, not before.

Manual checks:

```bash
cd /home/source/SpiritOS
find _blueprints docs -maxdepth 3 -type f | sort | grep -Ei 'design|component|cartographer|blueprint' | head -120
grep -n "blueprint updates\|Cartographer" docs/design-system-overhaul-master-v0.2.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Blueprint update boundary is documented.

Rollback:
Remove blueprint update text.

Stop condition:
Stop if Cartographer would gain apply authority.

Next increment title:
Phase 11.2: Define component inventory updates

### Phase 11.2: Define component inventory updates

Goal:
Define how component inventory is updated after primitives and patterns change.

Allowed files:
Cartographer docs, blueprints, and planning docs after explicit approval.

Forbidden actions:
No component edits.

Implementation notes:
Inventory should include component name, owner, route usage, token dependencies, variants, and tests.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -n "component inventory\|owner\|route usage\|token dependencies\|variants\|tests" docs/design-system-overhaul-master-v0.2.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Inventory update format is documented.

Rollback:
Remove inventory update text.

Stop condition:
Stop if inventory cannot identify ownership.

Next increment title:
Phase 11.3: Define token drift reports

### Phase 11.3: Define token drift reports

Goal:
Define token drift reports between canonical tokens, CSS variables, palette files, and route CSS.

Allowed files:
Cartographer docs, Design Vault docs, and planning docs after explicit approval.

Forbidden actions:
No token rewrites.

Implementation notes:
Report new variables, aliases, duplicate values, unmapped route variables, and accessibility gaps.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -n "token drift\|new variables\|aliases\|duplicate values\|unmapped route variables\|accessibility gaps" docs/design-system-overhaul-master-v0.2.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Token drift report format is defined.

Rollback:
Remove token drift report text.

Stop condition:
Stop if drift report starts changing tokens.

Next increment title:
Phase 11.4: Define route and layout ownership maps

### Phase 11.4: Define route and layout ownership maps

Goal:
Define route and layout ownership maps for design changes.

Allowed files:
Cartographer docs, blueprints, and planning docs after explicit approval.

Forbidden actions:
No route creation or route edits.

Implementation notes:
Map route, layout shell, component owner, style owner, test owner, and visual verification target.

Manual checks:

```bash
cd /home/source/SpiritOS
find src/app -maxdepth 4 -type f | sort | grep -Ei 'dashboard|chat|coding|oracle|design' || true
grep -n "route and layout ownership\|style owner\|test owner\|visual verification target" docs/design-system-overhaul-master-v0.2.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Ownership map shape is documented.

Rollback:
Remove ownership map text.

Stop condition:
Stop if ownership is inferred without evidence.

Next increment title:
Phase 11.5: Define closeout packet format

### Phase 11.5: Define closeout packet format

Goal:
Define a closeout packet format for every design-system increment.

Allowed files:
Planning docs and closeout docs after explicit approval.

Forbidden actions:
No commit, no push.

Implementation notes:
Closeout should list changed files, unchanged files, commands, expected output, actual output, dirty files, risks, rollback, and next increment.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -n "closeout packet\|changed files\|unchanged files\|expected output\|actual output\|dirty files\|next increment" docs/design-system-overhaul-master-v0.2.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Closeout packet format is defined.

Rollback:
Remove closeout format text.

Stop condition:
Stop if closeout omits dirty-file reporting.

Next increment title:
Phase 12.1: Define v0.2 complete criteria

### Phase 12.1: Define v0.2 complete criteria

Goal:
Define what must be true for v0.2 planning to be complete.

Allowed files:
Planning docs only.

Forbidden actions:
No implementation.

Implementation notes:
Criteria should require token spine plan, primitive spine plan, pattern plan, visual plan, agent authority model, Source Proxy lane contract, and next implementation gate.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -n "v0.2 complete\|token spine\|primitive spine\|pattern plan\|visual plan\|authority model\|Source Proxy lane" docs/design-system-overhaul-master-v0.2.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
v0.2 complete criteria are explicit.

Rollback:
Remove complete criteria text.

Stop condition:
Stop if criteria include implementation completion.

Next increment title:
Phase 12.2: Define v0.3 readiness

### Phase 12.2: Define v0.3 readiness

Goal:
Define what makes the repo ready for v0.3 design-system implementation.

Allowed files:
Planning docs only.

Forbidden actions:
No implementation.

Implementation notes:
v0.3 readiness should require approved docs, allowed-file ownership, visual verification plan, Source Proxy apply lane readiness, and first small implementation candidate.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -n "v0.3 readiness\|first small implementation candidate\|allowed-file ownership\|apply lane readiness" docs/design-system-overhaul-master-v0.2.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
v0.3 readiness is defined.

Rollback:
Remove v0.3 readiness text.

Stop condition:
Stop if readiness bypasses manual approval.

Next increment title:
Phase 12.3: Define what counts as safe to start actual implementation

### Phase 12.3: Define what counts as safe to start actual implementation

Goal:
Define the minimum gate for starting actual design-system implementation.

Allowed files:
Planning docs only.

Forbidden actions:
No implementation.

Implementation notes:
Safe start requires approved increment, allowed files, expected diff, checks, rollback, and Source Proxy approval path.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -n "safe to start actual implementation\|approved increment\|expected diff\|Source Proxy approval path" docs/design-system-overhaul-master-v0.2.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Implementation start gate is explicit.

Rollback:
Remove implementation start gate text.

Stop condition:
Stop if implementation could begin from the plan alone.

Next increment title:
Phase 12.4: Define what should wait until after proxy UI polish

### Phase 12.4: Define what should wait until after proxy UI polish

Goal:
Define which design-system work should wait until after current proxy UI polish.

Allowed files:
Planning docs only.

Forbidden actions:
No implementation.

Implementation notes:
Runtime agents, preview route creation, Storybook, screenshot baseline automation, external URL analysis, Scout runtime bridge, and Source Proxy apply-lane implementation should wait unless separately approved.

Manual checks:

```bash
cd /home/source/SpiritOS
grep -n "proxy UI polish\|runtime agents\|preview route\|Storybook\|screenshot baseline\|external URL\|Scout runtime bridge" docs/design-system-overhaul-master-v0.2.md
git diff --check -- docs/design-system-overhaul-master-v0.2.md
```

Expected output:
Wait-list is explicit and does not block docs-only planning.

Rollback:
Remove wait-list text.

Stop condition:
Stop if wait-list conflicts with `docs/codingUI.md` or Source Proxy plan authority.

Next increment title:
Phase 0.1: Repo and design docs inventory closeout

## 7. Manual Check Compression

Each Codex increment should end with one paste-ready manual check block. The block should be short enough to run as a single terminal paste and specific enough to prove that the increment stayed inside its allowed files.

Each increment closeout must report:

- What changed
- What did not change
- Commands run
- Expected output
- Actual output
- Dirty files
- Next increment title

Recommended closeout block pattern:

```bash
cd /home/source/SpiritOS
printf '\n== STATUS ==\n'
git status -sb
printf '\n== INTENDED DOC CHECK ==\n'
test -f docs/design-system-overhaul-master-v0.2.md && grep -n "SpiritOS Design System Overhaul Master Plan v0.2" docs/design-system-overhaul-master-v0.2.md
printf '\n== INDEX CHECK ==\n'
grep -n "design-system-overhaul-master-v0.2" docs/plan-index.md 2>/dev/null || true
printf '\n== DIFF CHECK ==\n'
git --no-pager diff --check -- docs/design-system-overhaul-master-v0.2.md docs/plan-index.md
```

The report should explicitly say which files were intentionally changed and which dirty files were pre-existing or unrelated.

## 8. Recommended Next Increment

Phase 0.1: Repo and design docs inventory closeout

## Phase 0.1 Closeout

Status: complete

Date: 2026-05-20

What changed:

- Recorded Phase 0.1 inventory closeout in this v0.2 plan.
- No production UI, route, component, theme, Source Proxy, Scout, Cartographer, package, or test files were changed for this increment.

What did not change:

- No implementation was performed.
- No new app route was created.
- No package was installed.
- No Playwright, Storybook, Chromatic, or axe setup was added.
- No Design Vault artifact was changed.
- No commit, push, deletion, or apply was performed.

Commands run:

```bash
cd /home/source/SpiritOS
printf '\n== PHASE 0.1 STATUS ==\n'
git status -sb
printf '\n== DESIGN DOCS ==\n'
find docs -maxdepth 1 -type f | sort | grep -Ei 'design|designer|visual|style|scout-design|source-proxy-design|plan-index' || true
printf '\n== DESIGN VAULT ==\n'
find data/design-vault -maxdepth 5 -type f | sort || true
printf '\n== UI PRIMITIVES ==\n'
find src/components/ui -maxdepth 2 -type f | sort || true
printf '\n== THEME FILES ==\n'
find src/theme src/styles -maxdepth 2 -type f | sort || true
printf '\n== DESIGN RELATED APP ROUTES ==\n'
find src/app -maxdepth 4 -type f | sort | grep -Ei 'design|coding|dashboard|chat|oracle' || true
printf '\n== TOOLING ==\n'
ls -la playwright.config.mjs package.json vitest.config.mjs 2>/dev/null || true
printf '\n== PACKAGE VISUAL TERMS ==\n'
grep -n "@playwright/test\|storybook\|chromatic\|axe\|toHaveScreenshot\|visual" package.json playwright.config.mjs docs/*.md 2>/dev/null || true
printf '\n== DIFF CHECK ==\n'
git diff --check -- docs/design-system-overhaul-master-v0.2.md docs/plan-index.md
```

Expected output:

- Design docs are listed, including this v0.2 plan.
- Design Vault files are listed under `data/design-vault/`.
- UI primitives are limited to the current `src/components/ui/` files.
- Theme files are listed under `src/theme` and `src/styles`.
- Existing design-related routes are listed without creating any route.
- Playwright config and Vitest config are visible.
- Diff check prints no whitespace errors.

Actual output:

- Design docs found included the v0.1 design intelligence docs, Scout bridge doc, Source Proxy design apply lane doc, visual verification doc, and this v0.2 plan.
- Design Vault exists with README, token model, source-card template and checklist, internal dashboard demo source card, and internal dashboard demo pack artifacts.
- UI primitives found: `GlassPanel.tsx`, `SectionLabel.tsx`, `SpiritButton.tsx`, and `index.ts`.
- Theme and style files found included `spiritPalettes.ts`, `useSpiritTheme.ts`, `dashboard-demo-v4.css`, `spirit-demo.*.css`, and `spirit-trinity-chat.css`.
- Existing design-related routes were listed under dashboard, chat, coding, design-demo, Oracle, Cartographer, and coding API paths.
- Tooling found: `package.json`, `playwright.config.mjs`, and `vitest.config.mjs`.
- `@playwright/test` appears in `playwright.config.mjs` and docs, but not as a dependency in `package.json`.
- Diff check printed no whitespace errors.

Dirty files:

- `M docs/codingUI.md`, pre-existing and not touched in this increment.
- `M docs/plan-index.md`, intentional from the v0.2 plan-index entry.
- `?? docs/cartographer-level-4-approved-push-executor-reservation.md`, unrelated and not touched in this increment.
- `?? docs/design-system-overhaul-master-v0.2.md`, intentional.

Next increment title:

Phase 0.2: Classify design docs as active, draft, deprecated, or superseded

## Phase 0.2 Design Doc Classification

Status: complete

Date: 2026-05-20

Classification rule:

- Active planning spine means the doc can guide planning, but does not authorize implementation.
- Supporting reference means the doc can be cited as evidence or boundary context.
- Contract or scaffold means the doc defines a future system shape, but the runtime system is not implemented.
- Deferred means visible but not active for implementation.
- Historical means useful as provenance, not current authority.

| File | Classification | Reason | Implementation authority |
| --- | --- | --- | --- |
| `docs/design-system-overhaul-master-v0.2.md` | Active planning spine | Current v0.2 design-system overhaul plan and increment map. | None. Future implementation requires explicit Source Proxy gated approval. |
| `docs/design-systems-master-v0.1.md` | Supporting reference, superseded for planning spine by v0.2 | v0.1 Design Intelligence Stack plan is complete and remains the base history for v0.2. | None. |
| `docs/design-pack-authoring-v0.1.md` | Supporting reference, contract/scaffold | Describes Design Vault pack shape and authoring workflow. | None. |
| `docs/design-visual-verification-v0.1.md` | Supporting reference, contract/scaffold | Defines visual verification conventions but does not capture screenshots or implement tests. | None. |
| `docs/reverse-designer-approved-inputs-v0.1.md` | Supporting reference, contract | Defines approved inputs for a future Reverse Designer. | None. |
| `docs/design-blender-style-alchemist-v0.1.md` | Supporting reference, contract | Defines originality and attribution rules for future Style Alchemist work. | None. |
| `docs/scout-design-intake-bridge-v0.1.md` | Supporting reference, contract | Defines a future manual-gated Scout design intake bridge. | None. |
| `docs/source-proxy-design-apply-lane-v0.1.md` | Supporting reference, contract | Defines design apply lane requirements while keeping Source Proxy as the only apply path. | None by itself. |
| `docs/plan-index.md` | Active index | Lists current plan authority and makes v0.2 discoverable. | Index only. |
| `docs/cartographer-level-3-local-commit-execution-design-refresh.md` | Historical or adjacent reference | Design-only Cartographer execution refresh, not part of the design-system overhaul spine. | None. |
| `docs/limited-autopilot-design.md` | Deferred adjacent reference | Autopilot design is explicitly design-only and outside this design-system increment. | None. |
| `docs/scheduled-provider-tasks-design.md` | Deferred adjacent reference | Scheduled provider tasks are outside this design-system increment. | None. |
| `docs/scout-v0-5-manual-import-audit-receipt-design.md` | Supporting Scout reference | Manual Scout-to-Proxy audit receipt planning may inform gate language, but is not a design-system authority. | None. |
| `docs/scout-v0-5-scheduled-read-only-watch-design.md` | Deferred Scout reference | Scheduled read-only watch planning is visible but outside this design-system increment. | None. |
| `docs/scout-v0-5-scout-to-proxy-manual-import-design.md` | Supporting Scout reference | Manual import planning may inform Scout bridge safety language, but does not authorize design intake runtime work. | None. |

Active design-system source of truth:

`docs/design-system-overhaul-master-v0.2.md` is the active planning source for the design-system overhaul. It supersedes `docs/design-systems-master-v0.1.md` only as the planning spine. It does not erase, deprecate, or delete the v0.1 history.

Docs-only design-system contracts:

- `docs/design-pack-authoring-v0.1.md`
- `docs/design-visual-verification-v0.1.md`
- `docs/reverse-designer-approved-inputs-v0.1.md`
- `docs/design-blender-style-alchemist-v0.1.md`
- `docs/scout-design-intake-bridge-v0.1.md`
- `docs/source-proxy-design-apply-lane-v0.1.md`

Docs that should wait:

- Runtime Reverse Designer work should wait.
- Runtime Style Alchemist work should wait.
- Scout runtime design intake should wait.
- Source Proxy design apply lane implementation should wait.
- Playwright screenshot baseline work should wait until tooling installation and capture targets are explicitly approved.
- New preview routes should wait until a later increment explicitly approves them.

What changed:

- Added this classification section to the v0.2 plan.
- Did not edit the classified docs themselves.
- Did not edit `docs/plan-index.md` during Phase 0.2.

What did not change:

- No implementation files changed for this increment.
- No production UI changed.
- No route was created.
- No package was installed.
- No Source Proxy, Scout, Cartographer, or Design Vault runtime behavior changed.

Commands run:

```bash
cd /home/source/SpiritOS
printf '\n== STATUS ==\n'
git status -sb
printf '\n== DESIGN DOC STATUS LINES ==\n'
for f in $(find docs -maxdepth 1 -type f | sort | grep -Ei 'design|designer|visual|style|scout-design|source-proxy-design|plan-index'); do
  printf '\n## %s\n' "$f"
  sed -n '1,24p' "$f" | grep -Ei '^(#|status|Status date|This document|The .*plan|Purpose)' || true
done
printf '\n== PLAN AUTHORITY ENTRIES ==\n'
sed -n '1,80p' docs/plan-index.md
printf '\n== DIFF CHECK ==\n'
git diff --check -- docs/design-system-overhaul-master-v0.2.md docs/plan-index.md
```

Expected output:

- Design-related docs are listed with their status lines.
- The plan index shows the v0.2 plan as planning active.
- Classification records active, supporting, contract, deferred, and historical handling.
- Diff check prints no whitespace errors.

Actual output:

- Design-related docs were listed and status lines were available for the v0.1 design intelligence docs, this v0.2 plan, Scout design docs, Source Proxy design apply lane, and adjacent design-only docs.
- The plan index listed `docs/design-system-overhaul-master-v0.2.md` as planning active.
- Diff check printed no whitespace errors before this closeout edit.

Dirty files:

- `M docs/codingUI.md`, pre-existing and not touched in this increment.
- `M docs/plan-index.md`, intentional prior v0.2 index entry and not edited during Phase 0.2.
- `M source_proxy/cartographer/service.py`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-4-approved-push-executor-reservation.md`, unrelated and not touched in this increment.
- `?? docs/design-system-overhaul-master-v0.2.md`, intentional.
- `?? scout/soak-logs/scout-soak-snapshot-2026-05-20T042739Z.json`, unrelated and not touched in this increment.

Next increment title:

Phase 0.3: Add design-system status summary to plan index

## Source Of Truth For v0.2

This document is the active planning spine for the SpiritOS Design System Overhaul v0.2. The v0.1 design intelligence docs remain supporting references. This document does not authorize implementation, route creation, app UI edits, Source Proxy behavior changes, Scout runtime changes, Cartographer authority expansion, commit, push, deletion, or apply.

## Safe To Build Next

Safe next work:

- Docs-only closeout of Phase 0.1 inventory.
- Docs-only classification of design docs.
- Docs-only token and primitive audits.
- Plan-index status updates that preserve current authority boundaries.

Should wait:

- Production UI component changes.
- New design-system preview routes.
- Storybook or Playwright dependency installation.
- Runtime Reverse Designer implementation.
- Runtime Design Blender implementation.
- Scout runtime bridge implementation.
- Source Proxy design apply lane implementation.
- External URL analysis and source ingestion.

## Current State Labels

Docs-only:

- v0.1 design intelligence docs.
- Design Vault authoring docs and schemas.
- Visual verification plan.
- Reverse Designer approved-input contract.
- Design Blender originality rules.
- Scout design intake bridge plan.
- Source Proxy design apply lane contract.

Live code:

- `src/components/ui/` primitives.
- `src/theme/spiritPalettes.ts`
- `src/theme/useSpiritTheme.ts`
- `src/app/globals.css`
- route and feature components under dashboard, chat, coding, and Oracle.
- route-specific CSS under `src/styles/`.

Missing or incomplete:

- Full canonical token spine in app code.
- Complete reusable primitive set.
- Component anatomy and variant contracts in code.
- Active screenshot baseline lane.
- Runtime Reverse Designer.
- Runtime Design Blender.
- Design Coding Agent task lane.
- Scout-to-Design-Vault runtime bridge.
- Source Proxy design apply lane implementation.
- Cartographer design-system closeout loop implementation.
