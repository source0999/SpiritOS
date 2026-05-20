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

This document is the active planning spine and source of truth for the SpiritOS Design System Overhaul v0.2.

The v0.1 design intelligence docs remain supporting references and history. They still matter for provenance, safety boundaries, and earlier decisions, but v0.2 controls the next design-system planning sequence.

If design-system planning docs conflict, use this priority order:

1. `docs/plan-index.md` for repo-level authority and active plan discovery.
2. `docs/design-system-overhaul-master-v0.2.md` for the design-system overhaul sequence.
3. v0.1 design intelligence docs for supporting contracts and historical context.

This document does not authorize implementation, route creation, app UI edits, Source Proxy behavior changes, Scout runtime changes, Cartographer authority expansion, package installation, commit, push, deletion, or apply.

Any future design-system implementation must start from a later approved increment with explicit allowed files, expected diff shape, manual checks, rollback notes, and Source Proxy gated approval.

## Phase 0.4 Source Of Truth Closeout

Status: complete

Date: 2026-05-20

What changed:

- Clarified the v0.2 design-system source-of-truth priority in this plan.
- Added source-of-truth wording to the plan index design-system status summary.

What did not change:

- No implementation files changed for this increment.
- No production UI changed.
- No route was created.
- No package was installed.
- No Source Proxy, Scout, Cartographer, or Design Vault runtime behavior changed.
- No commit, push, deletion, or apply was performed.

Commands run:

```bash
cd /home/source/SpiritOS
printf '\n== STATUS ==\n'
git status -sb
printf '\n== SOURCE OF TRUTH CHECK ==\n'
grep -n "Source Of Truth For v0.2\|source of truth\|current source of truth\|planning-only\|Source Proxy gated" docs/design-system-overhaul-master-v0.2.md docs/plan-index.md
printf '\n== PLAN INDEX DESIGN SUMMARY ==\n'
grep -n "Design System Status Summary\|design-system-overhaul-master-v0.2\|current source of truth" docs/plan-index.md
printf '\n== EM DASH CHECK ==\n'
LC_ALL=C grep -n "$(printf '\342\200\224')" docs/design-system-overhaul-master-v0.2.md docs/plan-index.md 2>/dev/null || true
printf '\n== DIFF CHECK ==\n'
git --no-pager diff --check -- docs/design-system-overhaul-master-v0.2.md docs/plan-index.md
```

Expected output:

- The v0.2 plan says it is the source of truth for design-system overhaul planning.
- The plan index says v0.2 is the current source of truth for design-system overhaul planning.
- The checks show planning-only and Source Proxy gated language.
- Em dash check prints no matches.
- Diff check prints no whitespace errors.

Actual output:

- The v0.2 plan says it is the active planning spine and source of truth for the design-system overhaul.
- The plan index says v0.2 is the current source of truth for design-system overhaul planning.
- Planning-only and Source Proxy gated language appeared in both files.
- Initial em dash check found the literal check character inside this closeout command block, so the command was changed to a byte-pattern check.
- Diff check printed no whitespace errors.

Dirty files:

- `M docs/design-system-overhaul-master-v0.2.md`, intentional.
- `M docs/plan-index.md`, intentional for v0.4 plus unrelated Scout index entries already present in the worktree.
- `M scout/src/scout/packets/synthesis.py`, unrelated and not touched in this increment.
- `M scout/src/scout/tests/test_packet_synthesis_orchestrator.py`, unrelated and not touched in this increment.
- `M source_proxy/api/cartographer.py`, unrelated and not touched in this increment.
- `M source_proxy/cartographer/service.py`, unrelated and not touched in this increment.
- `M source_proxy/tests/test_cartographer_api.py`, unrelated and not touched in this increment.
- `M src/components/coding/CodingCockpitShell.tsx`, unrelated and not touched in this increment.
- `M src/components/coding/__tests__/coding-cockpit-shell.test.tsx`, unrelated and not touched in this increment.
- `M src/components/dashboard/HomelabScoutIntelligenceWidget.tsx`, unrelated and not touched in this increment.
- `M src/components/dashboard/ScoutIntelligenceCenter.tsx`, unrelated and not touched in this increment.
- `M src/components/dashboard/__tests__/HomelabScoutIntelligenceWidget.test.tsx`, unrelated and not touched in this increment.
- `M src/lib/scout-human-readable.ts`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-3-to-6-closeout-summary.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-6-component-ownership-agent-assignment.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-6-cross-project-status-board.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-6-cross-repo-dirty-tree-classifier.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-6-multi-project-closeout-dashboard.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-7-to-10-autopilot-plan.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-7-diagnostics-summary-copy.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-7-review-ergonomics-stop-point.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-8-closeout-summary.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-8-next-lane-decision-record.md`, unrelated and not touched in this increment.

Next increment title:

Phase 1.1: Audit existing tokens and CSS variables

## Phase 1.1 Token Audit Closeout

Status: complete

Date: 2026-05-20

Scope:

This was a read-only token and CSS variable audit. No CSS, TypeScript, Design Vault, route, component, package, or test file was changed.

Token families observed:

| Family | Unique variables observed | Primary location or role |
| --- | ---: | --- |
| `--spirit-*` | 26 | Live theme and app-facing semantic paint variables in `src/app/globals.css`, `src/theme/spiritPalettes.ts`, route CSS, and Design Vault evidence. |
| `--ddv4-*` | 52 | Dashboard demo v4 and Trinity chat inherited design language variables. |
| `--trinity-*` | 43 | `/chat` Trinity route-scoped surface variables. |
| `--demo-*` | 77 | Demo token source in `src/styles/spirit-demo.tokens.css` and Design Vault pack artifacts. |
| `--design-vault-*` | 27 | Preview-only Design Vault aliases in `data/design-vault/packs/internal-dashboard-demo-v4/theme.css`. |
| `--chat-*` | 5 | Chat layout rail and composer variables. |
| Tailwind theme variables | 20 | `@theme` variables in `src/app/globals.css`, including color, font, text, leading, spacing, and radius tokens. |

Source files audited:

- `src/app/globals.css`
- `src/theme/spiritPalettes.ts`
- `src/styles/dashboard-demo-v4.css`
- `src/styles/spirit-demo.tokens.css`
- `src/styles/spirit-trinity-chat.css`
- `data/design-vault/packs/internal-dashboard-demo-v4/tokens.json`
- `data/design-vault/packs/internal-dashboard-demo-v4/theme.css`
- `data/design-vault/token-model-v0.1.md`

Key findings:

- `src/theme/spiritPalettes.ts` defines 20 `SPIRIT_DOM_CSS_KEYS` and applies them through `applySpiritPaletteDom`.
- `src/app/globals.css` defines the default `--spirit-*` root values, Tailwind theme variables, and additional dashboard or homelab utility variables.
- `src/styles/dashboard-demo-v4.css` mixes `--ddv4-*`, selected `--spirit-*`, and local preview variables.
- `src/styles/spirit-trinity-chat.css` overrides app-facing `--spirit-*` variables inside the route scope and adds `--trinity-*`, `--ddv4-*`, and `--chat-*` families.
- `src/styles/spirit-demo.tokens.css` is the largest demo token source, using `--demo-*` variables across color, spacing, type, radius, motion, glow, and z-index.
- Design Vault already mirrors part of the dashboard demo token language in `tokens.json` and preview-only aliases in `theme.css`.
- The Design Vault token model already names the right token categories: primitive, semantic, component, motion, responsive, and accessibility.

Drift risks:

- App-facing `--spirit-*` variables are partly canonical in `spiritPalettes.ts`, partly defaulted in `globals.css`, and partly overridden in route CSS.
- `--ddv4-*` variables appear in both dashboard demo and Trinity chat styling, which makes ownership unclear.
- `--demo-*` variables are rich enough to become a migration source, but they are not yet canonical app tokens.
- `--design-vault-*` variables are preview aliases and should not be imported into production UI without a later approved Source Proxy gated increment.
- Route-scoped variables such as `--trinity-*` and `--chat-*` need an explicit classification before they are promoted into reusable design-system tokens.

Safe next token work:

- Define canonical token categories in Phase 1.2 using the existing Design Vault token model as the starting point.
- Keep `--spirit-*` as the first live semantic token family to normalize.
- Treat `--ddv4-*`, `--demo-*`, and `--trinity-*` as source and migration candidates, not canonical tokens yet.
- Do not rename or move variables until a later migration map exists.

What changed:

- Added this docs-only Phase 1.1 token audit closeout to the v0.2 plan.

What did not change:

- No CSS file changed.
- No theme file changed.
- No Design Vault artifact changed.
- No route or component changed.
- No package was installed.
- No implementation, commit, push, deletion, or apply was performed.

Commands run:

```bash
cd /home/source/SpiritOS
printf '\n== PHASE 1.1 TOKEN AUDIT CHECK ==\n'
printf '\n== TOKEN FAMILY COUNTS ==\n'
for prefix in spirit ddv4 trinity demo design-vault chat color font text leading spacing radius dash; do
  printf '%s=' "$prefix"
  grep -RhoE -- "--${prefix}-[a-zA-Z0-9_-]+" src/app/globals.css src/styles src/theme data/design-vault 2>/dev/null | sort -u | wc -l
done
printf '\n== SPIRIT DOM KEYS ==\n'
grep -n "SPIRIT_DOM_CSS_KEYS\|--spirit-" src/theme/spiritPalettes.ts | head -80
printf '\n== DESIGN VAULT TOKEN MODEL HEADINGS ==\n'
grep -n "Primitive Tokens\|Semantic Tokens\|Component Tokens\|Motion Tokens\|Responsive Tokens\|Accessibility Tokens" data/design-vault/token-model-v0.1.md
printf '\n== PLAN AUDIT CHECK ==\n'
grep -n "Phase 1.1 Token Audit Closeout\|Token families observed\|Drift risks\|Safe next token work" docs/design-system-overhaul-master-v0.2.md
printf '\n== EM DASH CHECK ==\n'
LC_ALL=C grep -n "$(printf '\342\200\224')" docs/design-system-overhaul-master-v0.2.md docs/plan-index.md 2>/dev/null || true
printf '\n== DIFF CHECK ==\n'
git --no-pager diff --check -- docs/design-system-overhaul-master-v0.2.md docs/plan-index.md
```

Expected output:

- Token family counts show the major current token families.
- `SPIRIT_DOM_CSS_KEYS` appears in `src/theme/spiritPalettes.ts`.
- Design Vault token model headings appear.
- The v0.2 plan contains the Phase 1.1 token audit closeout.
- Em dash check prints no matches.
- Diff check prints no whitespace errors.

Actual output:

- Token family counts were: `spirit=26`, `ddv4=52`, `trinity=43`, `demo=77`, `design-vault=27`, `chat=5`, `color=9`, `font=4`, `text=4`, `leading=1`, `spacing=1`, `radius=1`, and `dash=2`.
- `SPIRIT_DOM_CSS_KEYS` and the 20 live palette-managed `--spirit-*` DOM keys were found in `src/theme/spiritPalettes.ts`.
- Design Vault token model headings were found for primitive, semantic, component, motion, responsive, and accessibility tokens.

Dirty files:

- `M docs/design-system-overhaul-master-v0.2.md`, intentional.
- `M docs/plan-index.md`, intentional earlier design-system index work plus unrelated Scout index entries already present in the worktree.
- `M scout/src/scout/packets/synthesis.py`, unrelated and not touched in this increment.
- `M scout/src/scout/tests/test_packet_synthesis_orchestrator.py`, unrelated and not touched in this increment.
- `M source_proxy/api/cartographer.py`, unrelated and not touched in this increment.
- `M source_proxy/cartographer/service.py`, unrelated and not touched in this increment.
- `M source_proxy/tests/test_cartographer_api.py`, unrelated and not touched in this increment.
- `M src/components/coding/CodingCockpitShell.tsx`, unrelated and not touched in this increment.
- `M src/components/coding/__tests__/coding-cockpit-shell.test.tsx`, unrelated and not touched in this increment.
- `M src/components/dashboard/HomelabScoutIntelligenceWidget.tsx`, unrelated and not touched in this increment.
- `M src/components/dashboard/ScoutIntelligenceCenter.tsx`, unrelated and not touched in this increment.
- `M src/components/dashboard/__tests__/HomelabScoutIntelligenceWidget.test.tsx`, unrelated and not touched in this increment.
- `M src/lib/scout-human-readable.ts`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-3-to-6-closeout-summary.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-6-component-ownership-agent-assignment.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-6-cross-project-status-board.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-6-cross-repo-dirty-tree-classifier.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-6-multi-project-closeout-dashboard.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-7-autopilot-boundary-contract.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-7-to-10-autopilot-plan.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-7-diagnostics-summary-copy.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-7-review-ergonomics-stop-point.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-8-closeout-summary.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-8-next-lane-decision-record.md`, unrelated and not touched in this increment.

Next increment title:

Phase 1.2: Define canonical token categories

## Phase 1.2 Canonical Token Categories Closeout

Status: complete

Date: 2026-05-20

Scope:

This increment defines canonical token categories for planning only. It does not rename, move, import, or rewrite any live CSS variables.

Canonical category model:

| Category | Purpose | Current source examples | v0.2 handling |
| --- | --- | --- | --- |
| Primitive tokens | Store direct values such as raw colors, spacing, typography sizes, radii, shadows, blur, opacity, borders, and z-index. | `--demo-*`, Tailwind `@theme` variables, raw values in `tokens.json`. | Source material only until a migration map exists. |
| Semantic tokens | Name UI intent such as background, surface, text, muted text, accent, success, warning, danger, focus, divider, and disabled. | `--spirit-bg`, `--spirit-panel`, `--spirit-accent`, Design Vault semantic aliases. | First canonical live category should start from app-facing `--spirit-*`. |
| Component tokens | Define component-level roles such as card, panel, rail, button, badge, input, dialog, composer, dashboard widget, and Oracle surface. | `--ddv4-widget-*`, `--ddv4-nav-*`, `--trinity-liquid-*`, `--chat-*`. | Must remain pattern candidates until primitive and semantic ownership is clear. |
| Motion tokens | Define timing, easing, ambient loops, hover feedback, reveal behavior, loading motion, and reduced-motion fallbacks. | `--demo-dur-*`, `--demo-ease-*`, Design Vault motion aliases. | Must include reduced-motion expectations before implementation. |
| Responsive tokens | Define breakpoints, rail widths, density, layout constraints, aspect ratios, mobile drawers, touch targets, and container behavior. | `--ddv4-app-rail-width`, `--chat-thread-rail-width`, `--chat-composer-max-width`. | Must be tied to route and layout ownership before promotion. |
| Accessibility tokens | Define contrast expectations, focus visibility, reduced motion, state visibility, hit areas, and text scale behavior. | Design Vault token model headings and future contrast/focus requirements. | Required for every canonical category before production migration. |

Category rules:

- Primitive tokens may store raw observed values, but production UI should consume semantic or component tokens where practical.
- Semantic tokens should be the first live normalization layer because they already exist as app-facing `--spirit-*` variables.
- Component tokens must not become route-specific escape hatches. They need anatomy, variant, and ownership rules first.
- Motion tokens must include a reduced-motion fallback before use in generated UI.
- Responsive tokens must include mobile and touch-target expectations, not only desktop layout values.
- Accessibility tokens are acceptance criteria, not decoration. They must be attached to token packs and component pattern cards.
- Design Vault aliases remain proposal evidence unless a later Source Proxy gated increment promotes them.

Canonical ownership direction:

- `--spirit-*`: candidate live semantic token family.
- `--demo-*`: primitive and source-token inventory candidate.
- `--ddv4-*`: component and pattern extraction candidate.
- `--trinity-*`: route-scoped component and pattern candidate.
- `--design-vault-*`: preview-only evidence, not production source of truth.
- Tailwind `@theme` variables: framework-facing primitives that need mapping, not automatic canonical authority.

What changed:

- Added this docs-only canonical token category definition to the v0.2 plan.

What did not change:

- No CSS file changed.
- No theme file changed.
- No Design Vault artifact changed.
- No route or component changed.
- No token was renamed.
- No package was installed.
- No implementation, commit, push, deletion, or apply was performed.

Commands run:

```bash
cd /home/source/SpiritOS
printf '\n== PHASE 1.2 CANONICAL CATEGORY CHECK ==\n'
printf '\n== STATUS ==\n'
git status -sb
printf '\n== TOKEN MODEL SOURCE CHECK ==\n'
grep -n "Primitive Tokens\|Semantic Tokens\|Component Tokens\|Motion Tokens\|Responsive Tokens\|Accessibility Tokens" data/design-vault/token-model-v0.1.md docs/design-system-overhaul-master-v0.2.md
printf '\n== CATEGORY CLOSEOUT CHECK ==\n'
grep -n "Phase 1.2 Canonical Token Categories Closeout\|Canonical category model\|Category rules\|Canonical ownership direction" docs/design-system-overhaul-master-v0.2.md
printf '\n== EM DASH CHECK ==\n'
LC_ALL=C grep -n "$(printf '\342\200\224')" docs/design-system-overhaul-master-v0.2.md docs/plan-index.md 2>/dev/null || true
printf '\n== DIFF CHECK ==\n'
git --no-pager diff --check -- docs/design-system-overhaul-master-v0.2.md docs/plan-index.md
```

Expected output:

- Design Vault token model categories are found.
- The v0.2 plan contains the Phase 1.2 category closeout.
- The plan defines primitive, semantic, component, motion, responsive, and accessibility categories.
- Em dash check prints no matches.
- Diff check prints no whitespace errors.

Actual output:

- Design Vault token model headings were found for primitive, semantic, component, motion, responsive, and accessibility tokens.
- The v0.2 plan contains the Phase 1.2 category closeout.
- The v0.2 plan contains the canonical category model, category rules, and ownership direction.
- Em dash check printed no matches.
- Diff check printed no whitespace errors.

Dirty files:

- `M docs/design-system-overhaul-master-v0.2.md`, intentional.
- `M docs/plan-index.md`, intentional earlier design-system index work plus unrelated Scout index entries already present in the worktree.
- `M scout/src/scout/packets/synthesis.py`, unrelated and not touched in this increment.
- `M scout/src/scout/tests/test_packet_synthesis_orchestrator.py`, unrelated and not touched in this increment.
- `M source_proxy/api/cartographer.py`, unrelated and not touched in this increment.
- `M source_proxy/cartographer/autopilot_config.py`, unrelated and not touched in this increment.
- `M source_proxy/cartographer/safety.py`, unrelated and not touched in this increment.
- `M source_proxy/cartographer/service.py`, unrelated and not touched in this increment.
- `M source_proxy/tests/test_cartographer_api.py`, unrelated and not touched in this increment.
- `M src/components/coding/CodingCockpitShell.tsx`, unrelated and not touched in this increment.
- `M src/components/coding/__tests__/coding-cockpit-shell.test.tsx`, unrelated and not touched in this increment.
- `M src/components/dashboard/HomelabScoutIntelligenceWidget.tsx`, unrelated and not touched in this increment.
- `M src/components/dashboard/ScoutIntelligenceCenter.tsx`, unrelated and not touched in this increment.
- `M src/components/dashboard/__tests__/HomelabScoutIntelligenceWidget.test.tsx`, unrelated and not touched in this increment.
- `M src/lib/scout-human-readable.ts`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-3-to-6-closeout-summary.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-6-component-ownership-agent-assignment.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-6-cross-project-status-board.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-6-cross-repo-dirty-tree-classifier.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-6-multi-project-closeout-dashboard.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-7-autopilot-boundary-contract.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-7-to-10-autopilot-plan.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-7-diagnostics-summary-copy.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-7-review-ergonomics-stop-point.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-8-closeout-summary.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-8-next-lane-decision-record.md`, unrelated and not touched in this increment.

Next increment title:

Phase 1.3: Create token naming rules

## Phase 1.3 Token Naming Rules Closeout

Status: complete

Date: 2026-05-20

Scope:

This increment defines naming rules for future token work. It does not rename, move, delete, migrate, or rewrite any token.

Naming principles:

- Token names must describe stable intent before visual flavor.
- Use lowercase kebab-case for CSS custom properties.
- Avoid abbreviations unless the abbreviation is already an established local namespace, such as `ddv4`.
- Do not encode route names into canonical tokens.
- Do not encode one-off component names into primitive or semantic tokens.
- Prefer role names such as `surface`, `text-muted`, `focus`, `divider`, `radius-card`, and `motion-fast`.
- Visual adjectives such as glass, smoke, liquid, pearl, glow, and aurora are allowed only for source, pattern, or component candidates until they are mapped to stable roles.
- New canonical names must be traceable to source tokens and Design Vault evidence.

Namespace rules:

| Namespace | Meaning | Rule |
| --- | --- | --- |
| `--spirit-*` | Live app-facing semantic token family. | Keep as the first candidate canonical semantic namespace. Add only with explicit ownership and migration notes. |
| `--demo-*` | Internal demo/source token family. | Treat as source evidence and migration input, not canonical production authority. |
| `--ddv4-*` | Dashboard demo v4 and inherited component/pattern language. | Treat as pattern/component candidate tokens until mapped. |
| `--trinity-*` | `/chat` Trinity route-scoped styling. | Keep route-scoped until pattern ownership is approved. |
| `--chat-*` | Chat layout and surface variables. | Treat as responsive or component candidates, not global tokens yet. |
| `--design-vault-*` | Preview-only Design Vault aliases. | Never import directly into production UI without later Source Proxy gated approval. |
| Tailwind `@theme` variables | Framework-facing primitive variables. | Map to canonical primitives, but do not treat as the whole design system. |

Canonical naming pattern:

```text
--spirit-<role>
--spirit-<role>-<state>
--spirit-<category>-<role>
--spirit-<component>-<part>
--spirit-<component>-<part>-<state>
```

Examples:

- `--spirit-bg`
- `--spirit-surface`
- `--spirit-surface-strong`
- `--spirit-text-muted`
- `--spirit-focus-ring`
- `--spirit-card-radius`
- `--spirit-motion-fast`
- `--spirit-rail-width`

Migration naming rules:

- Keep existing names until a migration map exists.
- Every rename must list old name, new name, category, source file, owner, and fallback.
- Aliases are allowed as temporary migration aids only when they are documented.
- Do not collapse two tokens into one unless visual verification proves they share the same role.
- Do not promote route tokens to global tokens just because they are reused in two files.
- Do not use generated names unless a human reviews them.

Forbidden naming moves:

- No new canonical token may start with `--design-vault-*`.
- No new canonical token may use external brand names.
- No token may copy a third-party design system name unless it is a generic role.
- No token may hide source provenance.
- No token may imply accessibility status unless contrast, focus, motion, and state behavior are verified.

What changed:

- Added this docs-only token naming rule closeout to the v0.2 plan.

What did not change:

- No CSS file changed.
- No theme file changed.
- No Design Vault artifact changed.
- No route or component changed.
- No token was renamed.
- No package was installed.
- No implementation, commit, push, deletion, or apply was performed.

Commands run:

```bash
cd /home/source/SpiritOS
printf '\n== PHASE 1.3 TOKEN NAMING CHECK ==\n'
printf '\n== STATUS ==\n'
git status -sb
printf '\n== TOKEN NAME SAMPLE ==\n'
grep -RhoE -- '--(spirit|ddv4|trinity|demo|design-vault|chat)-[a-zA-Z0-9_-]+' src/app/globals.css src/styles src/theme data/design-vault 2>/dev/null | sort -u | sed -n '1,180p'
printf '\n== NAMING CLOSEOUT CHECK ==\n'
grep -n "Phase 1.3 Token Naming Rules Closeout\|Naming principles\|Namespace rules\|Canonical naming pattern\|Migration naming rules\|Forbidden naming moves" docs/design-system-overhaul-master-v0.2.md
printf '\n== EM DASH CHECK ==\n'
LC_ALL=C grep -n "$(printf '\342\200\224')" docs/design-system-overhaul-master-v0.2.md docs/plan-index.md 2>/dev/null || true
printf '\n== DIFF CHECK ==\n'
git --no-pager diff --check -- docs/design-system-overhaul-master-v0.2.md docs/plan-index.md
```

Expected output:

- Token sample shows current namespaces without changing them.
- The v0.2 plan contains naming principles, namespace rules, canonical naming pattern, migration naming rules, and forbidden naming moves.
- Em dash check prints no matches.
- Diff check prints no whitespace errors.

Actual output:

- Token sample showed current `--spirit-*`, `--ddv4-*`, `--trinity-*`, `--demo-*`, `--design-vault-*`, and `--chat-*` namespaces without changing them.
- The v0.2 plan contains naming principles, namespace rules, canonical naming pattern, migration naming rules, and forbidden naming moves.
- Em dash check printed no matches.
- Diff check printed no whitespace errors.

Dirty files:

- `M docs/design-system-overhaul-master-v0.2.md`, intentional.
- `M docs/plan-index.md`, intentional earlier design-system index work plus unrelated Scout index entries already present in the worktree.
- `M scout/src/scout/packets/synthesis.py`, unrelated and not touched in this increment.
- `M scout/src/scout/tests/test_packet_synthesis_orchestrator.py`, unrelated and not touched in this increment.
- `M source_proxy/api/cartographer.py`, unrelated and not touched in this increment.
- `M source_proxy/cartographer/autopilot_config.py`, unrelated and not touched in this increment.
- `M source_proxy/cartographer/safety.py`, unrelated and not touched in this increment.
- `M source_proxy/cartographer/service.py`, unrelated and not touched in this increment.
- `M source_proxy/tests/test_cartographer_api.py`, unrelated and not touched in this increment.
- `M src/components/coding/CodingCockpitShell.tsx`, unrelated and not touched in this increment.
- `M src/components/coding/__tests__/coding-cockpit-shell.test.tsx`, unrelated and not touched in this increment.
- `M src/components/dashboard/HomelabScoutIntelligenceWidget.tsx`, unrelated and not touched in this increment.
- `M src/components/dashboard/ScoutIntelligenceCenter.tsx`, unrelated and not touched in this increment.
- `M src/components/dashboard/__tests__/HomelabScoutIntelligenceWidget.test.tsx`, unrelated and not touched in this increment.
- `M src/lib/scout-human-readable.ts`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-3-to-6-closeout-summary.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-6-component-ownership-agent-assignment.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-6-cross-project-status-board.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-6-cross-repo-dirty-tree-classifier.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-6-multi-project-closeout-dashboard.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-7-autopilot-boundary-contract.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-7-disabled-by-default-feature-flag.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-7-to-10-autopilot-plan.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-7-diagnostics-summary-copy.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-7-review-ergonomics-stop-point.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-8-closeout-summary.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-8-next-lane-decision-record.md`, unrelated and not touched in this increment.

Next increment title:

Phase 1.4: Create token migration map from current CSS and palette files

## Phase 1.4 Token Migration Map Closeout

Status: complete

Date: 2026-05-20

Scope:

This increment creates a planning migration map only. It does not rename tokens, edit CSS, change palettes, import Design Vault aliases, or alter runtime theme behavior.

Migration states:

- Keep: retain current name and role for now.
- Alias: keep current name while mapping it to a future canonical name.
- Migrate: move toward a canonical token in a later approved implementation increment.
- Retire-later: keep working for now, but avoid using for new design-system work.
- Evidence-only: keep in Design Vault or docs as proposal evidence, not production authority.

Migration map:

| Current family or token group | Observed count | Current role | v0.2 state | Proposed canonical direction |
| --- | ---: | --- | --- | --- |
| `--spirit-*` palette-managed DOM keys | 20 keys in `SPIRIT_DOM_CSS_KEYS`, 26 observed total | Live app-facing semantic paint and atmosphere variables. | Keep, then alias selectively. | First canonical semantic namespace. Normalize around background, surface, text, accent, border, focus, motion, and layout roles. |
| Extra route `--spirit-*` aliases such as `--spirit-text`, `--spirit-muted`, `--spirit-surface`, `--spirit-blur`, `--spirit-glass-bg` | included in 26 observed total | Route-scoped compatibility aliases, mostly in Trinity chat CSS. | Alias, then migrate. | Map into semantic or component tokens after route ownership is clear. |
| `--ddv4-*` | 52 | Dashboard demo v4 and inherited component/pattern tokens. | Migrate as component and pattern candidates. | Map to `--spirit-card-*`, `--spirit-rail-*`, `--spirit-nav-*`, `--spirit-surface-*`, and `--spirit-shadow-*` only after component contracts exist. |
| `--demo-*` | 77 | Internal demo primitive and source token inventory. | Evidence/source, then migrate selectively. | Map color, space, type, radius, motion, glow, and z-index values into primitive token categories. |
| `--trinity-*` | 43 | `/chat` route-scoped visual language. | Alias or retire-later depending on reuse. | Keep route-scoped until chat pattern extraction decides what becomes reusable. |
| `--chat-*` | 5 | Chat layout sizing and rail variables. | Alias, then migrate selectively. | Map to responsive or component layout tokens after route and layout ownership map exists. |
| `--design-vault-*` | 27 | Preview-only Design Vault aliases. | Evidence-only. | Do not import into production. Use as review evidence for future canonical token proposals. |
| Tailwind `@theme` variables | 20 | Framework-facing primitive tokens in `globals.css`. | Keep, then map. | Map to primitive token categories without making Tailwind the whole design-system authority. |
| Homelab and status ad hoc variables such as `--good`, `--bad`, `--warn`, `--active`, `--pending`, `--ready` | observed in globals and component styles | Local state/status helpers. | Alias or retire-later. | Map to semantic state tokens only after status semantics are audited. |

First migration candidates:

- Keep `SPIRIT_DOM_CSS_KEYS` unchanged until the canonical token set is approved.
- Add no new runtime aliases until Phase 1.4 is converted into a later Source Proxy gated implementation increment.
- Treat `--spirit-bg`, `--spirit-bg-soft`, `--spirit-panel`, `--spirit-panel-strong`, `--spirit-accent`, `--spirit-accent-strong`, `--spirit-border`, and `--spirit-glow` as the safest starting semantic set.
- Treat `--demo-space-*`, `--demo-radius-*`, `--demo-dur-*`, and `--demo-ease-*` as the cleanest primitive migration sources.
- Treat `--ddv4-widget-*`, `--ddv4-nav-*`, `--ddv4-shell-*`, and `--ddv4-surface-*` as component-token candidates, not primitive tokens.

Stop rules before implementation:

- Do not rename any token before a file-level migration map exists.
- Do not remove old names while route CSS still consumes them.
- Do not promote `--trinity-*` or `--ddv4-*` globally without component pattern ownership.
- Do not import `data/design-vault/**/theme.css` into production UI.
- Do not add aliases that make visual verification harder to reason about.

What changed:

- Added this docs-only token migration map to the v0.2 plan.

What did not change:

- No CSS file changed.
- No theme file changed.
- No Design Vault artifact changed.
- No route or component changed.
- No token was renamed, aliased, or removed.
- No package was installed.
- No implementation, commit, push, deletion, or apply was performed.

Commands run:

```bash
cd /home/source/SpiritOS
printf '\n== PHASE 1.4 TOKEN MIGRATION MAP CHECK ==\n'
printf '\n== STATUS ==\n'
git status -sb
printf '\n== TOKEN FAMILY COUNTS ==\n'
printf 'spirit_vars=' && grep -RhoE -- '--spirit-[a-zA-Z0-9_-]+' src/app/globals.css src/styles src/theme data/design-vault 2>/dev/null | sort -u | wc -l
printf 'ddv4_vars=' && grep -RhoE -- '--ddv4-[a-zA-Z0-9_-]+' src/app/globals.css src/styles src/theme data/design-vault 2>/dev/null | sort -u | wc -l
printf 'demo_vars=' && grep -RhoE -- '--demo-[a-zA-Z0-9_-]+' src/app/globals.css src/styles src/theme data/design-vault 2>/dev/null | sort -u | wc -l
printf 'trinity_vars=' && grep -RhoE -- '--trinity-[a-zA-Z0-9_-]+' src/app/globals.css src/styles src/theme data/design-vault 2>/dev/null | sort -u | wc -l
printf '\n== LIVE SPIRIT DOM KEYS ==\n'
sed -n '25,45p' src/theme/spiritPalettes.ts
printf '\n== MIGRATION MAP CHECK ==\n'
grep -n "Phase 1.4 Token Migration Map Closeout\|Migration states\|Migration map\|First migration candidates\|Stop rules before implementation\|Phase 1.5: Add accessibility token requirements" docs/design-system-overhaul-master-v0.2.md
printf '\n== EM DASH CHECK ==\n'
LC_ALL=C grep -n "$(printf '\342\200\224')" docs/design-system-overhaul-master-v0.2.md docs/plan-index.md 2>/dev/null || true
printf '\n== DIFF CHECK ==\n'
git --no-pager diff --check -- docs/design-system-overhaul-master-v0.2.md docs/plan-index.md
```

Expected output:

- Token family counts show the current `spirit`, `ddv4`, `demo`, and `trinity` families.
- `SPIRIT_DOM_CSS_KEYS` remains visible and unchanged.
- The v0.2 plan contains the Phase 1.4 token migration map.
- Em dash check prints no matches.
- Diff check prints no whitespace errors.

Actual output:

- Token family counts were `spirit_vars=26`, `ddv4_vars=52`, `demo_vars=77`, and `trinity_vars=43`.
- `SPIRIT_DOM_CSS_KEYS` remained visible in `src/theme/spiritPalettes.ts`.
- The v0.2 plan contains the Phase 1.4 token migration map, migration states, first migration candidates, and stop rules.
- Em dash check printed no matches.
- Diff check printed no whitespace errors.

Dirty files:

- `M docs/design-system-overhaul-master-v0.2.md`, intentional.
- `M docs/plan-index.md`, intentional earlier design-system index work plus unrelated Scout index entries already present in the worktree.
- `M scout/src/scout/packets/synthesis.py`, unrelated and not touched in this increment.
- `M scout/src/scout/tests/test_packet_synthesis_orchestrator.py`, unrelated and not touched in this increment.
- `M source_proxy/api/cartographer.py`, unrelated and not touched in this increment.
- `M source_proxy/cartographer/autopilot_config.py`, unrelated and not touched in this increment.
- `M source_proxy/cartographer/safety.py`, unrelated and not touched in this increment.
- `M source_proxy/cartographer/service.py`, unrelated and not touched in this increment.
- `M source_proxy/tests/test_cartographer_api.py`, unrelated and not touched in this increment.
- `M src/components/coding/CodingCockpitShell.tsx`, unrelated and not touched in this increment.
- `M src/components/coding/__tests__/coding-cockpit-shell.test.tsx`, unrelated and not touched in this increment.
- `M src/components/dashboard/HomelabScoutIntelligenceWidget.tsx`, unrelated and not touched in this increment.
- `M src/components/dashboard/ScoutIntelligenceCenter.tsx`, unrelated and not touched in this increment.
- `M src/components/dashboard/__tests__/HomelabScoutIntelligenceWidget.test.tsx`, unrelated and not touched in this increment.
- `M src/lib/scout-human-readable.ts`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-3-to-6-closeout-summary.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-6-component-ownership-agent-assignment.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-6-cross-project-status-board.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-6-cross-repo-dirty-tree-classifier.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-6-multi-project-closeout-dashboard.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-7-autopilot-boundary-contract.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-7-disabled-by-default-feature-flag.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-7-to-10-autopilot-plan.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-7-diagnostics-summary-copy.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-7-review-ergonomics-stop-point.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-8-closeout-summary.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-8-next-lane-decision-record.md`, unrelated and not touched in this increment.

Next increment title:

Phase 1.5: Add accessibility token requirements for contrast, focus, motion, and touch targets

## Phase 1.5 Accessibility Token Requirements Closeout

Status: complete

Date: 2026-05-20

Scope:

This increment defines accessibility requirements for future token work. It does not run accessibility tooling, install dependencies, change CSS, or alter UI behavior.

Accessibility token requirements:

| Requirement | Token impact | Future verification expectation |
| --- | --- | --- |
| Contrast | Semantic color tokens must record intended text, surface, border, divider, focus, success, warning, danger, and disabled roles. | Future token packs should record contrast targets and flag any pair that needs manual review. |
| Focus visibility | Focus tokens must define visible ring color, ring offset, ring width, and fallback behavior across light, dark, and hybrid themes. | Future component checks should confirm focus is visible on interactive controls. |
| Reduced motion | Motion tokens must define default duration, reduced-motion fallback, and whether motion is decorative, navigational, or state-critical. | Future visual or accessibility checks should confirm reduced-motion mode does not hide state. |
| Touch targets | Responsive and component tokens must define minimum hit area expectations for buttons, rails, tabs, menu items, composer controls, and mobile drawers. | Future mobile checks should confirm primary controls meet the minimum target size. |
| State visibility | State tokens must make hover, active, selected, disabled, loading, error, warning, success, and pending states distinguishable without relying only on color. | Future component pattern cards should list state indicators and non-color cues. |
| Text scale behavior | Typography and layout tokens must define readable minimums, line-height expectations, wrapping behavior, and overflow rules. | Future viewport checks should confirm labels and buttons do not overlap or clip at mobile sizes. |

Minimum future token metadata:

Every canonical token or token pack should eventually record:

- category
- source token or source file
- intended role
- approved use mode
- theme family coverage
- contrast notes where color is involved
- focus notes where interactivity is involved
- reduced-motion notes where animation is involved
- touch-target notes where layout or controls are involved
- state visibility notes where status is involved
- reviewer and review date

Accessibility stop rules:

- Do not promote a color token to canonical if its foreground and background role are unknown.
- Do not promote a focus token unless it remains visible on both light and dark surfaces.
- Do not promote a motion token without a reduced-motion fallback.
- Do not promote a layout or control token without a touch-target expectation.
- Do not mark a state token accessible if the state is communicated only by color.
- Do not treat Design Vault evidence as accessibility approval until reviewed.

First safe acceptance criteria:

- `--spirit-*` semantic tokens need role-pair notes before broad migration.
- `--demo-*` primitive colors need contrast review before becoming canonical.
- `--ddv4-*` and `--trinity-*` component tokens need state and focus review before reuse outside their current surfaces.
- `--design-vault-*` aliases remain evidence-only until accessibility notes are attached.

What changed:

- Added this docs-only accessibility token requirement closeout to the v0.2 plan.

What did not change:

- No CSS file changed.
- No theme file changed.
- No Design Vault artifact changed.
- No route or component changed.
- No accessibility tooling was installed.
- No package was installed.
- No implementation, commit, push, deletion, or apply was performed.

Commands run:

```bash
cd /home/source/SpiritOS
printf '\n== PHASE 1.5 ACCESSIBILITY TOKEN CHECK ==\n'
printf '\n== STATUS ==\n'
git status -sb
printf '\n== ACCESSIBILITY SOURCE CHECK ==\n'
grep -n "contrast\|focus\|reduced motion\|touch target\|state visibility\|text scale" data/design-vault/token-model-v0.1.md docs/design-system-overhaul-master-v0.2.md | head -180
printf '\n== ACCESSIBILITY CLOSEOUT CHECK ==\n'
grep -n "Phase 1.5 Accessibility Token Requirements Closeout\|Accessibility token requirements\|Minimum future token metadata\|Accessibility stop rules\|First safe acceptance criteria\|Phase 2.1: Audit current src/components/ui primitives" docs/design-system-overhaul-master-v0.2.md
printf '\n== EM DASH CHECK ==\n'
LC_ALL=C grep -n "$(printf '\342\200\224')" docs/design-system-overhaul-master-v0.2.md docs/plan-index.md 2>/dev/null || true
printf '\n== DIFF CHECK ==\n'
git --no-pager diff --check -- docs/design-system-overhaul-master-v0.2.md docs/plan-index.md
```

Expected output:

- Existing Design Vault accessibility concepts are found.
- The v0.2 plan contains accessibility token requirements, metadata, stop rules, and acceptance criteria.
- Em dash check prints no matches.
- Diff check prints no whitespace errors.

Actual output:

- Existing Design Vault accessibility concepts were found for contrast target, focus visibility, reduced motion, touch target size, state visibility, and text scale behavior.
- The v0.2 plan contains accessibility token requirements, minimum future token metadata, accessibility stop rules, and first safe acceptance criteria.
- Em dash check printed no matches.
- Diff check printed no whitespace errors.

Dirty files:

- `M docs/design-system-overhaul-master-v0.2.md`, intentional.
- `M docs/plan-index.md`, intentional earlier design-system index work plus unrelated Scout index entries already present in the worktree.
- `M scout/src/scout/packets/synthesis.py`, unrelated and not touched in this increment.
- `M scout/src/scout/tests/test_packet_synthesis_orchestrator.py`, unrelated and not touched in this increment.
- `M source_proxy/api/cartographer.py`, unrelated and not touched in this increment.
- `M source_proxy/cartographer/autopilot_config.py`, unrelated and not touched in this increment.
- `M source_proxy/cartographer/safety.py`, unrelated and not touched in this increment.
- `M source_proxy/cartographer/service.py`, unrelated and not touched in this increment.
- `M source_proxy/tests/test_cartographer_api.py`, unrelated and not touched in this increment.
- `M src/components/coding/CodingCockpitShell.tsx`, unrelated and not touched in this increment.
- `M src/components/coding/__tests__/coding-cockpit-shell.test.tsx`, unrelated and not touched in this increment.
- `M src/components/dashboard/HomelabScoutIntelligenceWidget.tsx`, unrelated and not touched in this increment.
- `M src/components/dashboard/ScoutIntelligenceCenter.tsx`, unrelated and not touched in this increment.
- `M src/components/dashboard/__tests__/HomelabScoutIntelligenceWidget.test.tsx`, unrelated and not touched in this increment.
- `M src/lib/scout-human-readable.ts`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-3-to-6-closeout-summary.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-6-component-ownership-agent-assignment.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-6-cross-project-status-board.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-6-cross-repo-dirty-tree-classifier.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-6-multi-project-closeout-dashboard.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-7-autopilot-boundary-contract.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-7-disabled-by-default-feature-flag.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-7-next-safe-action-recommendation-contract.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-7-to-10-autopilot-plan.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-7-diagnostics-summary-copy.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-7-review-ergonomics-stop-point.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-8-closeout-summary.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-8-next-lane-decision-record.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-9-next-phases-plan.md`, unrelated and not touched in this increment.

Next increment title:

Phase 2.1: Audit current src/components/ui primitives

## Phase 2.1 UI Primitive Audit Closeout

Status: complete

Date: 2026-05-20

Scope:

This increment audits the current reusable UI primitive layer. It does not edit components, exports, styles, tests, routes, or runtime behavior.

Current primitive files:

| File | Exported surface | Current role | Notes |
| --- | --- | --- | --- |
| `src/components/ui/GlassPanel.tsx` | `GlassPanel`, `glassPanelSurfaceClasses` | Basic glass/card panel wrapper with static Tailwind classes and `as` support for a small set of HTML elements. | Uses `--spirit-border` and the global `glass` utility. No variant API yet. |
| `src/components/ui/SectionLabel.tsx` | `SectionLabel`, `sectionLabelClasses` | Small uppercase mono label primitive. | Supports `p`, `span`, and `dt`. No tone, size, or truncation contract yet. |
| `src/components/ui/SpiritButton.tsx` | `SpiritButton`, `spiritPrimaryCtaClasses`, `SpiritButtonProps` | Primary pill-style button with min touch size, disabled styling, and static classes. | Only one visual variant. Link reuse happens through exported class string rather than an `as` or slot contract. |
| `src/components/ui/index.ts` | barrel exports | Public primitive export surface. | Exports all current primitive files. |

What exists:

- A very small reusable primitive spine.
- Static class strings that Tailwind can see.
- Basic `cn` composition support.
- A button with `min-h-[44px]` and `min-w-[44px]`, which is a useful accessibility starting point.
- Some token use through `--spirit-border`, `--spirit-accent`, and `--spirit-accent-strong`.

What is missing:

- No general text primitive.
- No generic surface or card variant system beyond `GlassPanel`.
- No field, input, textarea, select, checkbox, switch, radio, or slider primitive.
- No tabs, menu, dialog, popover, tooltip, or sheet primitive.
- No badge, status, alert, progress, skeleton, toast, or empty-state primitive.
- No toolbar, icon button, segmented control, rail, or navigation primitive.
- No density, tone, size, state, or motion variant contract.
- No component anatomy contract.
- No accessibility contract per primitive beyond the button touch size.
- No primitive-level tests in `src/components/ui/`.

Risk assessment:

- Feature components are likely carrying too much repeated UI behavior because the primitive layer is thin.
- `glassPanelSurfaceClasses`, `sectionLabelClasses`, and `spiritPrimaryCtaClasses` are useful, but exported class strings can become informal APIs if variants are not defined.
- Future generated UI would have too few safe building blocks and may overfit route-specific classes.
- Adding many primitives at once would create churn. The next safe step is to define the required primitive set before implementation.

Safe next primitive work:

- Define the required primitive set in Phase 2.2 before creating or editing components.
- Keep future primitives token-driven, accessible, and small.
- Require anatomy and variant contracts before implementation.
- Prefer incremental additions through Source Proxy gated implementation later.

What changed:

- Added this docs-only UI primitive audit closeout to the v0.2 plan.

What did not change:

- No component file changed.
- No export file changed.
- No CSS file changed.
- No route changed.
- No test changed.
- No package was installed.
- No implementation, commit, push, deletion, or apply was performed.

Commands run:

```bash
cd /home/source/SpiritOS
printf '\n== PHASE 2.1 UI PRIMITIVE AUDIT CHECK ==\n'
printf '\n== STATUS ==\n'
git status -sb
printf '\n== UI PRIMITIVES ==\n'
find src/components/ui -maxdepth 2 -type f | sort
printf '\n== UI EXPORTS ==\n'
sed -n '1,200p' src/components/ui/index.ts
printf '\n== PRIMITIVE CLOSEOUT CHECK ==\n'
grep -n "Phase 2.1 UI Primitive Audit Closeout\|Current primitive files\|What exists\|What is missing\|Risk assessment\|Safe next primitive work\|Phase 2.2: Define required primitive set" docs/design-system-overhaul-master-v0.2.md
printf '\n== EM DASH CHECK ==\n'
LC_ALL=C grep -n "$(printf '\342\200\224')" docs/design-system-overhaul-master-v0.2.md docs/plan-index.md 2>/dev/null || true
printf '\n== DIFF CHECK ==\n'
git --no-pager diff --check -- docs/design-system-overhaul-master-v0.2.md docs/plan-index.md
```

Expected output:

- The current UI primitive files are listed.
- The UI barrel exports the current primitives.
- The v0.2 plan contains the Phase 2.1 primitive audit closeout.
- Em dash check prints no matches.
- Diff check prints no whitespace errors.

Actual output:

- Current UI primitive files were listed: `GlassPanel.tsx`, `SectionLabel.tsx`, `SpiritButton.tsx`, and `index.ts`.
- The UI barrel exports `GlassPanel`, `glassPanelSurfaceClasses`, `SectionLabel`, `sectionLabelClasses`, `SpiritButton`, `spiritPrimaryCtaClasses`, and `SpiritButtonProps`.
- The v0.2 plan contains the Phase 2.1 primitive audit closeout.
- Em dash check printed no matches.
- Diff check printed no whitespace errors.

Dirty files:

- `M docs/design-system-overhaul-master-v0.2.md`, intentional.
- `M docs/plan-index.md`, intentional earlier design-system index work plus unrelated Scout index entries already present in the worktree.
- `M scout/src/scout/packets/synthesis.py`, unrelated and not touched in this increment.
- `M scout/src/scout/tests/test_packet_synthesis_orchestrator.py`, unrelated and not touched in this increment.
- `M source_proxy/api/cartographer.py`, unrelated and not touched in this increment.
- `M source_proxy/cartographer/autopilot_config.py`, unrelated and not touched in this increment.
- `M source_proxy/cartographer/safety.py`, unrelated and not touched in this increment.
- `M source_proxy/cartographer/service.py`, unrelated and not touched in this increment.
- `M source_proxy/tests/test_cartographer_api.py`, unrelated and not touched in this increment.
- `M src/components/coding/CodingCockpitShell.tsx`, unrelated and not touched in this increment.
- `M src/components/coding/__tests__/coding-cockpit-shell.test.tsx`, unrelated and not touched in this increment.
- `M src/components/dashboard/HomelabScoutIntelligenceWidget.tsx`, unrelated and not touched in this increment.
- `M src/components/dashboard/ScoutIntelligenceCenter.tsx`, unrelated and not touched in this increment.
- `M src/components/dashboard/__tests__/HomelabScoutIntelligenceWidget.test.tsx`, unrelated and not touched in this increment.
- `M src/lib/scout-human-readable.ts`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-3-to-6-closeout-summary.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-6-component-ownership-agent-assignment.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-6-cross-project-status-board.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-6-cross-repo-dirty-tree-classifier.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-6-multi-project-closeout-dashboard.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-7-autopilot-boundary-contract.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-7-disabled-by-default-feature-flag.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-7-dry-run-action-packet-builder.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-7-next-safe-action-recommendation-contract.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-7-to-10-autopilot-plan.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-7-diagnostics-summary-copy.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-7-review-ergonomics-stop-point.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-8-closeout-summary.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-8-next-lane-decision-record.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-9-dry-run-receipt-format.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-9-lane-contract-schema.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-9-next-phases-plan.md`, unrelated and not touched in this increment.

Next increment title:

Phase 2.2: Define required primitive set

## Phase 2.2 Required Primitive Set Closeout

Status: complete

Date: 2026-05-20

Scope:

This increment defines the required primitive set for future implementation planning. It does not create components, edit exports, move styles, or change production UI.

Primitive tiers:

| Tier | Primitive group | Required primitives | Why it matters |
| --- | --- | --- | --- |
| Tier 1 | Core surface and text | `Box`, `Stack`, `Inline`, `Surface`, `Panel`, `Card`, `Text`, `Heading`, `Label`, `Divider` | Gives generated UI predictable structure without route CSS leakage. |
| Tier 1 | Core actions | `Button`, `IconButton`, `ButtonGroup`, `LinkButton` | Replaces one-off action styling and supports touch targets, disabled states, and icons. |
| Tier 1 | Status and feedback | `Badge`, `StatusDot`, `Alert`, `Progress`, `Spinner`, `Skeleton`, `EmptyState` | Makes state visibility reusable instead of feature-local. |
| Tier 2 | Forms and controls | `Field`, `Input`, `Textarea`, `Select`, `Checkbox`, `Switch`, `RadioGroup`, `Slider`, `Stepper` | Needed before generated UI can safely ask for user input. |
| Tier 2 | Navigation and layout controls | `Tabs`, `SegmentedControl`, `Toolbar`, `Rail`, `Breadcrumb`, `Pagination` | Supports dashboard, chat, coding, and Oracle surfaces without inventing route-specific chrome. |
| Tier 2 | Overlays | `Dialog`, `Sheet`, `Popover`, `Menu`, `Tooltip`, `Toast` | Needed for bounded review flows, menus, mobile drawers, and explanatory UI. |
| Tier 3 | Data display | `Table`, `DescriptionList`, `CodeBlock`, `LogViewer`, `Metric`, `Timeline` | Supports operational UI, coding console output, and review evidence. |
| Tier 3 | Domain adapters | `CommandBar`, `DiffFrame`, `EvidenceCard`, `VoiceControlCluster` | Should wrap primitives and remain domain-specific, not become base primitives too early. |

Required primitive rules:

- Every primitive must be token-driven.
- Every interactive primitive must define focus, disabled, loading, hover, active, and keyboard behavior.
- Every clickable primitive must meet the touch-target requirement from Phase 1.5.
- Every primitive must have a small anatomy contract before implementation.
- Variants must be finite and named by role, not by route.
- Domain adapters must compose primitives rather than bypassing them.
- No primitive may import Design Vault preview CSS directly.

Implementation order recommendation:

1. Button family: evolve `SpiritButton` into a role-based button contract while preserving current behavior.
2. Surface family: evolve `GlassPanel` into `Surface`, `Panel`, and `Card` concepts after variant rules exist.
3. Text family: evolve `SectionLabel` into a broader text and label contract.
4. Status family: extract badge, status dot, alert, and progress patterns from dashboard and chat.
5. Form and overlay families: add only after anatomy and variant rules are approved.

What changed:

- Added this docs-only required primitive set to the v0.2 plan.

What did not change:

- No component file changed.
- No export file changed.
- No CSS file changed.
- No route changed.
- No test changed.
- No package was installed.
- No implementation, commit, push, deletion, or apply was performed.

Commands run:

```bash
cd /home/source/SpiritOS
printf '\n== PHASE 2.2 REQUIRED PRIMITIVE SET CHECK ==\n'
printf '\n== STATUS ==\n'
git status -sb
printf '\n== UI PRIMITIVES ==\n'
find src/components/ui -maxdepth 2 -type f | sort
printf '\n== FEATURE COMPONENT SAMPLE ==\n'
find src/components/dashboard src/components/chat src/components/coding src/components/oracle -maxdepth 1 -type f | sort | sed -n '1,180p'
printf '\n== REQUIRED SET CHECK ==\n'
grep -n "Phase 2.2 Required Primitive Set Closeout\|Primitive tiers\|Required primitive rules\|Implementation order recommendation\|Phase 2.3: Define component anatomy contracts" docs/design-system-overhaul-master-v0.2.md
printf '\n== EM DASH CHECK ==\n'
LC_ALL=C grep -n "$(printf '\342\200\224')" docs/design-system-overhaul-master-v0.2.md docs/plan-index.md 2>/dev/null || true
printf '\n== DIFF CHECK ==\n'
git --no-pager diff --check -- docs/design-system-overhaul-master-v0.2.md docs/plan-index.md
```

Expected output:

- Current UI primitive files remain unchanged.
- Feature component sample shows the larger surface area that future primitives should support.
- The v0.2 plan contains primitive tiers, required primitive rules, and implementation order recommendation.
- Em dash check prints no matches.
- Diff check prints no whitespace errors.

Actual output:

- Current UI primitive files remained unchanged: `GlassPanel.tsx`, `SectionLabel.tsx`, `SpiritButton.tsx`, and `index.ts`.
- Feature component sample showed the broader dashboard, chat, coding, and Oracle surface area that future primitives should support.
- The v0.2 plan contains primitive tiers, required primitive rules, and implementation order recommendation.
- Em dash check printed no matches.
- Diff check printed no whitespace errors.

Dirty files:

- `M docs/design-system-overhaul-master-v0.2.md`, intentional.
- `M docs/plan-index.md`, intentional earlier design-system index work plus unrelated Scout index entries already present in the worktree.
- `M scout/src/scout/packets/synthesis.py`, unrelated and not touched in this increment.
- `M scout/src/scout/tests/test_packet_synthesis_orchestrator.py`, unrelated and not touched in this increment.
- `M source_proxy/api/cartographer.py`, unrelated and not touched in this increment.
- `M source_proxy/cartographer/autopilot_config.py`, unrelated and not touched in this increment.
- `M source_proxy/cartographer/safety.py`, unrelated and not touched in this increment.
- `M source_proxy/cartographer/service.py`, unrelated and not touched in this increment.
- `M source_proxy/tests/test_cartographer_api.py`, unrelated and not touched in this increment.
- `M src/components/coding/CodingCockpitShell.tsx`, unrelated and not touched in this increment.
- `M src/components/coding/__tests__/coding-cockpit-shell.test.tsx`, unrelated and not touched in this increment.
- `M src/components/dashboard/HomelabScoutIntelligenceWidget.tsx`, unrelated and not touched in this increment.
- `M src/components/dashboard/ScoutIntelligenceCenter.tsx`, unrelated and not touched in this increment.
- `M src/components/dashboard/__tests__/HomelabScoutIntelligenceWidget.test.tsx`, unrelated and not touched in this increment.
- `M src/lib/scout-human-readable.ts`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-3-to-6-closeout-summary.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-6-component-ownership-agent-assignment.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-6-cross-project-status-board.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-6-cross-repo-dirty-tree-classifier.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-6-multi-project-closeout-dashboard.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-7-autopilot-boundary-contract.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-7-disabled-by-default-feature-flag.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-7-dry-run-action-packet-builder.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-7-exact-approval-handshake-contract.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-7-next-safe-action-recommendation-contract.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-7-to-10-autopilot-plan.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-7-diagnostics-summary-copy.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-7-review-ergonomics-stop-point.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-8-closeout-summary.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-8-next-lane-decision-record.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-9-dry-run-receipt-format.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-9-lane-contract-schema.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-9-next-phases-plan.md`, unrelated and not touched in this increment.

Next increment title:

Phase 2.3: Define component anatomy contracts

## Phase 2.3 Component Anatomy Contracts Closeout

Status: complete

Date: 2026-05-20

Scope:

This increment defines anatomy contracts for future primitives and patterns. It does not edit components, props, exports, styles, tests, or runtime behavior.

Base anatomy contract:

Every reusable primitive or pattern should define only the slots it needs from this shared vocabulary.

| Slot | Purpose | Applies to |
| --- | --- | --- |
| `root` | Outermost element, layout boundary, role, and data attributes. | All primitives and patterns. |
| `surface` | Visual background, border, elevation, blur, and tone treatment. | Panel, card, dialog, sheet, menu, popover. |
| `header` | Top content region for title, eyebrow, status, and actions. | Card, panel, dialog, sheet, table, evidence card. |
| `title` | Primary readable name for the component or section. | Card, panel, dialog, field, status surfaces. |
| `description` | Secondary explanatory text. | Field, alert, empty state, dialog, evidence card. |
| `label` | Compact label, field label, or metadata key. | Field, badge, metric, section label, description list. |
| `icon` | Decorative or semantic icon region. | Button, badge, alert, card, nav item, status. |
| `body` | Main content region. | Card, panel, dialog, sheet, table, log viewer. |
| `footer` | Bottom content region for summary, actions, or metadata. | Card, panel, dialog, sheet. |
| `actions` | Explicit command area. | Card, panel, dialog, toast, toolbar, field. |
| `control` | Interactive input or command element. | Button, input, switch, select, slider, tabs. |
| `helper` | Helper text or hint. | Field, form row, control group. |
| `error` | Error copy or invalid state explanation. | Field, form, alert, review surface. |
| `status` | State indicator with text and optional icon. | Badge, alert, status dot, cards, dashboard widgets. |
| `media` | Image, canvas, animation, orb, waveform, or preview surface. | Oracle, evidence, visual verification, rich cards. |
| `meta` | Low-priority metadata such as timestamp, source, count, or provenance. | Evidence cards, Source Proxy previews, logs. |

Primitive-specific anatomy:

| Primitive | Required slots | Optional slots | Notes |
| --- | --- | --- | --- |
| Button | `root`, `control` | `icon`, `label`, `status` | Must define icon-only accessible label rules. |
| IconButton | `root`, `control`, `icon` | `status` | Requires tooltip or accessible label guidance. |
| Surface | `root`, `surface`, `body` | `header`, `footer`, `actions` | Should not imply card semantics by default. |
| Card | `root`, `surface`, `header`, `body` | `icon`, `status`, `footer`, `actions`, `meta` | Repeated content unit, not a page section wrapper. |
| Field | `root`, `label`, `control` | `description`, `helper`, `error`, `status` | Must bind labels and errors accessibly. |
| Badge | `root`, `label`, `status` | `icon` | State must not rely only on color. |
| Tabs | `root`, `control`, `label` | `icon`, `status` | Must define keyboard and selected-state behavior. |
| Dialog | `root`, `surface`, `header`, `title`, `body`, `actions` | `description`, `footer`, `status` | Must define focus management before implementation. |
| Sheet | `root`, `surface`, `header`, `title`, `body` | `actions`, `footer`, `description` | Mobile behavior must be part of the contract. |
| LogViewer | `root`, `surface`, `header`, `body` | `actions`, `status`, `meta` | Needs overflow and copy behavior in later contracts. |

Contract rules:

- Anatomy slots describe structure and responsibility, not class names.
- A component may omit optional slots, but must not invent unnamed regions for repeated behavior.
- Slot names should be stable across variants.
- Slot props should support `className` only after the variant contract is defined.
- Interactive slots need keyboard and focus expectations before implementation.
- Error, helper, description, and status slots must have accessibility relationships where applicable.
- Generated UI must target anatomy slots instead of route-specific CSS selectors.

Current primitive mapping:

- `GlassPanel` currently maps to `root`, `surface`, and `body` through `children`.
- `SectionLabel` currently maps to `root` and `label`.
- `SpiritButton` currently maps to `root`, `control`, and `label` through `children`.
- Exported class strings are useful but should not replace anatomy contracts.

What changed:

- Added this docs-only component anatomy contract to the v0.2 plan.

What did not change:

- No component file changed.
- No export file changed.
- No CSS file changed.
- No route changed.
- No test changed.
- No package was installed.
- No implementation, commit, push, deletion, or apply was performed.

Commands run:

```bash
cd /home/source/SpiritOS
printf '\n== PHASE 2.3 ANATOMY CONTRACT CHECK ==\n'
printf '\n== STATUS ==\n'
git status -sb
printf '\n== ANATOMY SOURCE SAMPLE ==\n'
grep -RIn "children\|className\|as:\|header\|footer\|icon\|action\|label\|description\|status" src/components/ui src/components/dashboard src/components/chat src/components/coding src/components/oracle 2>/dev/null | sed -n '1,180p'
printf '\n== ANATOMY CLOSEOUT CHECK ==\n'
grep -n "Phase 2.3 Component Anatomy Contracts Closeout\|Base anatomy contract\|Primitive-specific anatomy\|Contract rules\|Current primitive mapping\|Phase 2.4: Define variant rules" docs/design-system-overhaul-master-v0.2.md
printf '\n== EM DASH CHECK ==\n'
LC_ALL=C grep -n "$(printf '\342\200\224')" docs/design-system-overhaul-master-v0.2.md docs/plan-index.md 2>/dev/null || true
printf '\n== DIFF CHECK ==\n'
git --no-pager diff --check -- docs/design-system-overhaul-master-v0.2.md docs/plan-index.md
```

Expected output:

- Anatomy source sample shows current slot-like patterns in UI and feature components.
- The v0.2 plan contains the Phase 2.3 anatomy contract closeout.
- Em dash check prints no matches.
- Diff check prints no whitespace errors.

Actual output:

- Anatomy source sample showed current slot-like patterns across UI and feature components, including `children`, `className`, `as`, labels, icons, actions, status, headers, and route-specific card regions.
- The v0.2 plan contains the Phase 2.3 anatomy contract closeout, base anatomy contract, primitive-specific anatomy, contract rules, and current primitive mapping.
- Em dash check printed no matches.
- Diff check printed no whitespace errors.

Dirty files:

- `M docs/design-system-overhaul-master-v0.2.md`, intentional.
- `M docs/plan-index.md`, intentional earlier design-system index work plus unrelated Scout index entries already present in the worktree.
- `M scout/src/scout/packets/synthesis.py`, unrelated and not touched in this increment.
- `M scout/src/scout/tests/test_packet_synthesis_orchestrator.py`, unrelated and not touched in this increment.
- `M source_proxy/api/cartographer.py`, unrelated and not touched in this increment.
- `M source_proxy/cartographer/autopilot_config.py`, unrelated and not touched in this increment.
- `M source_proxy/cartographer/safety.py`, unrelated and not touched in this increment.
- `M source_proxy/cartographer/service.py`, unrelated and not touched in this increment.
- `M source_proxy/tests/test_cartographer_api.py`, unrelated and not touched in this increment.
- `M src/components/coding/CodingCockpitShell.tsx`, unrelated and not touched in this increment.
- `M src/components/coding/__tests__/coding-cockpit-shell.test.tsx`, unrelated and not touched in this increment.
- `M src/components/dashboard/HomelabScoutIntelligenceWidget.tsx`, unrelated and not touched in this increment.
- `M src/components/dashboard/ScoutIntelligenceCenter.tsx`, unrelated and not touched in this increment.
- `M src/components/dashboard/__tests__/HomelabScoutIntelligenceWidget.test.tsx`, unrelated and not touched in this increment.
- `M src/lib/scout-human-readable.ts`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-3-to-6-closeout-summary.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-6-component-ownership-agent-assignment.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-6-cross-project-status-board.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-6-cross-repo-dirty-tree-classifier.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-6-multi-project-closeout-dashboard.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-7-autopilot-boundary-contract.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-7-disabled-by-default-feature-flag.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-7-dry-run-action-packet-builder.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-7-exact-approval-handshake-contract.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-7-next-safe-action-recommendation-contract.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-7-to-10-autopilot-plan.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-7-diagnostics-summary-copy.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-7-review-ergonomics-stop-point.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-8-closeout-summary.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-8-next-lane-decision-record.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-9-dry-run-receipt-format.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-9-lane-contract-schema.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-9-next-phases-plan.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-9-phase-0-3-closeout.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-9-review-decision-labels.md`, unrelated and not touched in this increment.

Next increment title:

Phase 2.4: Define variant rules

## Phase 2.4 Variant Rules Closeout

Status: complete

Date: 2026-05-20

Scope:

This increment defines variant rules for future primitives and patterns. It does not edit components, props, exports, styles, tests, routes, or runtime behavior.

Variant dimensions:

| Dimension | Allowed values | Purpose | Notes |
| --- | --- | --- | --- |
| `tone` | `neutral`, `accent`, `success`, `warning`, `danger`, `info`, `muted` | Maps visual role to semantic state. | Must not rely on color alone for state. |
| `intent` | `default`, `primary`, `secondary`, `destructive`, `ghost`, `link` | Describes command meaning. | Mainly for action primitives. |
| `size` | `xs`, `sm`, `md`, `lg`, `icon` | Controls height, padding, and text scale. | Interactive sizes must preserve touch targets when used on mobile. |
| `density` | `comfortable`, `compact`, `dense` | Controls spacing and information density. | Dense mode must remain readable and tappable where interactive. |
| `emphasis` | `solid`, `soft`, `outline`, `subtle`, `plain` | Controls visual weight. | Avoid route-specific names such as glass-pearl as canonical variants. |
| `state` | `default`, `hover`, `active`, `selected`, `disabled`, `loading`, `error`, `empty` | Defines UI state. | Runtime state props should map to stable state attributes later. |
| `motion` | `none`, `subtle`, `standard`, `expressive` | Controls transition intensity. | Must include reduced-motion behavior. |
| `shape` | `square`, `rounded`, `pill`, `circle` | Controls border radius intent. | Shape must not replace component anatomy. |

Variant contract rules:

- Variants must be finite and documented before implementation.
- Variant names must describe role, not route or visual source.
- Variants should compose across dimensions only when the combination has a clear use case.
- Every interactive variant must define disabled, focus, loading, and keyboard behavior.
- Every state variant must include non-color cues when the state is meaningful.
- Every density variant must define spacing and touch-target expectations.
- Every motion variant must define reduced-motion behavior.
- Visual source names such as `ddv4`, `trinity`, `glass-pearl`, and `liquid` may appear in Design Vault evidence, but should not become canonical variant names without mapping.

Primitive variant recommendations:

| Primitive | First variant dimensions | Wait until later |
| --- | --- | --- |
| `Button` | `intent`, `size`, `emphasis`, `state` | Motion variants beyond subtle hover. |
| `IconButton` | `intent`, `size`, `state`, `shape` | Complex badge/status composition. |
| `Surface` | `tone`, `emphasis`, `density` | Route-specific glass variants. |
| `Card` | `tone`, `emphasis`, `density`, `state` | Complex media layouts before pattern contracts. |
| `Badge` | `tone`, `emphasis`, `size`, `state` | Brand-specific color names. |
| `Field` | `size`, `state`, `density` | Rich validation behavior before form contract. |
| `Tabs` | `size`, `density`, `state` | Animated indicator variants before visual verification. |
| `Dialog` and `Sheet` | `size`, `density`, `motion`, `state` | Custom route-specific shells. |

Current observed variant sources:

- `ThemeStrip` already has a `variant` prop with `strip` and `bubble`.
- Dashboard and Scout components use state language such as loading, ready, error, active, disabled, selected, pending, live, offline, and unavailable.
- Current UI primitives do not yet expose a formal variant API.
- Route and demo CSS contain visual variant names that should be mapped before reuse.

Stop rules:

- Do not add a variant because one route needs a one-off style.
- Do not expose arbitrary class strings as the primary variant system.
- Do not add a visual variant without accessibility and state rules.
- Do not allow generated UI to invent variant names.
- Do not implement variants until allowed files and expected behavior are approved in a later Source Proxy gated increment.

What changed:

- Added this docs-only variant rules closeout to the v0.2 plan.

What did not change:

- No component file changed.
- No export file changed.
- No CSS file changed.
- No route changed.
- No test changed.
- No package was installed.
- No implementation, commit, push, deletion, or apply was performed.

Commands run:

```bash
cd /home/source/SpiritOS
printf '\n== PHASE 2.4 VARIANT RULES CHECK ==\n'
printf '\n== STATUS ==\n'
git status -sb
printf '\n== VARIANT SOURCE SAMPLE ==\n'
grep -RIn "variant\|size\|tone\|density\|disabled\|loading\|active\|selected\|hover\|rounded\|className" src/components/ui src/components/dashboard src/components/chat src/components/coding src/components/oracle 2>/dev/null | sed -n '1,200p'
printf '\n== VARIANT CLOSEOUT CHECK ==\n'
grep -n "Phase 2.4 Variant Rules Closeout\|Variant dimensions\|Variant contract rules\|Primitive variant recommendations\|Current observed variant sources\|Phase 2.5: Define no-route-specific-style leakage rule" docs/design-system-overhaul-master-v0.2.md
printf '\n== EM DASH CHECK ==\n'
LC_ALL=C grep -n "$(printf '\342\200\224')" docs/design-system-overhaul-master-v0.2.md docs/plan-index.md 2>/dev/null || true
printf '\n== DIFF CHECK ==\n'
git --no-pager diff --check -- docs/design-system-overhaul-master-v0.2.md docs/plan-index.md
```

Expected output:

- Variant source sample shows existing ad hoc variant and state language.
- The v0.2 plan contains variant dimensions, variant contract rules, primitive variant recommendations, and current observed variant sources.
- Em dash check prints no matches.
- Diff check prints no whitespace errors.

Actual output:

- Variant source sample showed current ad hoc variant and state language, including `variant`, `disabled`, `loading`, `active`, `hover`, `rounded`, and `className`.
- The v0.2 plan contains variant dimensions, variant contract rules, primitive variant recommendations, and current observed variant sources.
- Em dash check printed no matches for the plan and index docs.
- Diff check printed no whitespace errors.

Dirty files:

- `M docs/design-system-overhaul-master-v0.2.md`, intentional.
- `M docs/plan-index.md`, intentional earlier design-system index work plus unrelated Scout index entries already present in the worktree.
- `M scout/src/scout/packets/synthesis.py`, unrelated and not touched in this increment.
- `M scout/src/scout/tests/test_packet_synthesis_orchestrator.py`, unrelated and not touched in this increment.
- `M source_proxy/api/cartographer.py`, unrelated and not touched in this increment.
- `M source_proxy/cartographer/autopilot_config.py`, unrelated and not touched in this increment.
- `M source_proxy/cartographer/safety.py`, unrelated and not touched in this increment.
- `M source_proxy/cartographer/service.py`, unrelated and not touched in this increment.
- `M source_proxy/tests/test_cartographer_api.py`, unrelated and not touched in this increment.
- `M src/components/coding/CodingCockpitShell.tsx`, unrelated and not touched in this increment.
- `M src/components/coding/__tests__/coding-cockpit-shell.test.tsx`, unrelated and not touched in this increment.
- `M src/components/dashboard/HomelabScoutIntelligenceWidget.tsx`, unrelated and not touched in this increment.
- `M src/components/dashboard/ScoutIntelligenceCenter.tsx`, unrelated and not touched in this increment.
- `M src/components/dashboard/__tests__/HomelabScoutIntelligenceWidget.test.tsx`, unrelated and not touched in this increment.
- `M src/lib/scout-human-readable.ts`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-3-to-6-closeout-summary.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-6-component-ownership-agent-assignment.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-6-cross-project-status-board.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-6-cross-repo-dirty-tree-classifier.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-6-multi-project-closeout-dashboard.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-7-autopilot-boundary-contract.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-7-closeout-dashboard.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-7-disabled-by-default-feature-flag.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-7-dry-run-action-packet-builder.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-7-exact-approval-handshake-contract.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-7-next-safe-action-recommendation-contract.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-7-to-10-autopilot-plan.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-7-diagnostics-summary-copy.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-7-review-ergonomics-stop-point.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-8-closeout-summary.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-8-next-lane-decision-record.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-9-design-intake-plan.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-9-dry-run-receipt-format.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-9-lane-contract-schema.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-9-next-phases-plan.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-9-phase-0-3-closeout.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-9-review-decision-labels.md`, unrelated and not touched in this increment.

Next increment title:

Phase 2.5: Define no-route-specific-style leakage rule

## Phase 2.5 No Route-Specific Style Leakage Closeout

Status: complete

Date: 2026-05-20

Scope:

This increment defines the style leakage rule for future design-system work. It does not move CSS, rename classes, edit components, change routes, or alter runtime behavior.

Leakage rule:

Route-specific CSS may consume design-system tokens and compose approved primitives or patterns. It must not become the source of truth for reusable primitive behavior, canonical tokens, component anatomy, or variant names.

Allowed route-specific styling:

- Route layout constraints that are genuinely route-owned.
- Temporary migration aliases while a route is being refactored.
- Feature-specific composition of approved primitives.
- One-off visual treatments that are documented as local and not reused elsewhere.
- Route-scoped overrides that are tied to a clear ownership map.

Forbidden leakage:

- Defining reusable primitive behavior inside route CSS.
- Promoting route class names into generated UI prompts as if they were design-system APIs.
- Treating `.dashboard-demo-v4-*`, `.spirit-trinity-*`, `.scout-center-*`, or route-only classes as canonical primitives.
- Creating new canonical tokens inside route CSS without a migration map.
- Importing Design Vault preview CSS into production UI.
- Copying route-specific visual names into global variant names.
- Adding new generated UI that depends on unapproved route CSS selectors.

Current leakage risks observed:

| Area | Risk | Handling |
| --- | --- | --- |
| `src/styles/spirit-trinity-chat.css` | Large route-scoped visual system with `--trinity-*`, `--ddv4-*`, `--chat-*`, and scoped selectors. | Keep route-scoped until chat patterns are extracted and approved. |
| `src/styles/dashboard-demo-v4.css` | Internal demo and dashboard visual language uses many `.dashboard-demo-v4-*` classes and `--ddv4-*` tokens. | Treat as Design Vault evidence and pattern source, not primitive API. |
| `src/app/globals.css` | Contains global utilities, dashboard v2 shell classes, and default `--spirit-*` variables. | Audit before moving any reusable behavior into primitives. |
| `src/components/dashboard/*` | Many feature components carry local layout, status, card, and badge behavior. | Extract only after primitive anatomy and variant contracts are approved. |
| `src/components/chat/*` | Chat surface behavior mixes route shell, thread rail, composer, mobile drawer, and message states. | Extract as chat patterns later, not as base primitives immediately. |
| `src/components/oracle/*` | Voice and visualizer components are domain-specific. | Keep as Oracle patterns unless a base primitive need is proven. |
| `src/components/coding/*` | Approval, diff, and task surfaces are Source Proxy domain UI. | Keep Source Proxy gated and pattern-level until primitive needs are clear. |

Promotion path from route style to design-system primitive:

1. Identify repeated behavior in at least two places or one critical product workflow.
2. Record source files and route ownership.
3. Map tokens to canonical category and naming rules.
4. Define anatomy slots.
5. Define variant dimensions.
6. Define accessibility requirements.
7. Create a bounded Source Proxy gated implementation proposal with allowed files.
8. Verify visually and with relevant tests after apply.

Stop rules:

- Stop if the proposed reusable behavior only exists in one route and has no clear reuse need.
- Stop if the route style relies on unreviewed external design references.
- Stop if ownership of the route or component is unclear.
- Stop if the extraction would require broad CSS churn.
- Stop if no manual verification path exists.

What changed:

- Added this docs-only no-route-specific-style leakage rule to the v0.2 plan.

What did not change:

- No CSS file changed.
- No component file changed.
- No export file changed.
- No route changed.
- No test changed.
- No package was installed.
- No implementation, commit, push, deletion, or apply was performed.

Commands run:

```bash
cd /home/source/SpiritOS
printf '\n== PHASE 2.5 ROUTE STYLE LEAKAGE CHECK ==\n'
printf '\n== STATUS ==\n'
git status -sb
printf '\n== ROUTE STYLE FILES ==\n'
find src/styles src/app -maxdepth 4 -type f | sort | grep -Ei 'css|design|dashboard|chat|coding|oracle' | sed -n '1,220p'
printf '\n== ROUTE STYLE SAMPLE ==\n'
grep -RIn "dashboard-demo-v4\|spirit-trinity\|scout-center\|oracle\|coding\|--ddv4\|--trinity\|--chat" src/app src/styles src/components 2>/dev/null | sed -n '1,220p'
printf '\n== LEAKAGE CLOSEOUT CHECK ==\n'
grep -n "Phase 2.5 No Route-Specific Style Leakage Closeout\|Leakage rule\|Allowed route-specific styling\|Forbidden leakage\|Current leakage risks observed\|Promotion path from route style\|Phase 3.1: Define layout patterns" docs/design-system-overhaul-master-v0.2.md
printf '\n== EM DASH CHECK ==\n'
LC_ALL=C grep -n "$(printf '\342\200\224')" docs/design-system-overhaul-master-v0.2.md docs/plan-index.md 2>/dev/null || true
printf '\n== DIFF CHECK ==\n'
git --no-pager diff --check -- docs/design-system-overhaul-master-v0.2.md docs/plan-index.md
```

Expected output:

- Route style files and route-scoped styling samples are visible.
- The v0.2 plan contains the leakage rule, allowed and forbidden handling, risks, and promotion path.
- Em dash check prints no matches.
- Diff check prints no whitespace errors.

Actual output:

- Route style files and route-scoped styling samples were visible, including `dashboard-demo-v4`, `spirit-trinity`, `scout-center`, `--ddv4-*`, `--trinity-*`, and `--chat-*`.
- The v0.2 plan contains the leakage rule, allowed route-specific styling, forbidden leakage, current leakage risks, and promotion path.
- Em dash check printed no matches for the plan and index docs.
- Diff check printed no whitespace errors.

Dirty files:

- `M docs/design-system-overhaul-master-v0.2.md`, intentional.
- `M docs/plan-index.md`, intentional earlier design-system index work plus unrelated Scout index entries already present in the worktree.
- `M scout/src/scout/packets/synthesis.py`, unrelated and not touched in this increment.
- `M scout/src/scout/tests/test_packet_synthesis_orchestrator.py`, unrelated and not touched in this increment.
- `M source_proxy/api/cartographer.py`, unrelated and not touched in this increment.
- `M source_proxy/cartographer/autopilot_config.py`, unrelated and not touched in this increment.
- `M source_proxy/cartographer/safety.py`, unrelated and not touched in this increment.
- `M source_proxy/cartographer/service.py`, unrelated and not touched in this increment.
- `M source_proxy/tests/test_cartographer_api.py`, unrelated and not touched in this increment.
- `M src/components/coding/CodingCockpitShell.tsx`, unrelated and not touched in this increment.
- `M src/components/coding/__tests__/coding-cockpit-shell.test.tsx`, unrelated and not touched in this increment.
- `M src/components/dashboard/HomelabScoutIntelligenceWidget.tsx`, unrelated and not touched in this increment.
- `M src/components/dashboard/ScoutIntelligenceCenter.tsx`, unrelated and not touched in this increment.
- `M src/components/dashboard/__tests__/HomelabScoutIntelligenceWidget.test.tsx`, unrelated and not touched in this increment.
- `M src/lib/scout-human-readable.ts`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-3-to-6-closeout-summary.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-6-component-ownership-agent-assignment.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-6-cross-project-status-board.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-6-cross-repo-dirty-tree-classifier.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-6-multi-project-closeout-dashboard.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-7-autopilot-boundary-contract.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-7-closeout-dashboard.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-7-disabled-by-default-feature-flag.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-7-dry-run-action-packet-builder.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-7-exact-approval-handshake-contract.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-7-next-safe-action-recommendation-contract.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-7-to-10-autopilot-plan.md`, unrelated and not touched in this increment.
- `?? docs/cartographer-level-8-workflow-runner-boundary-contract.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-7-diagnostics-summary-copy.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-7-review-ergonomics-stop-point.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-8-closeout-summary.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-8-next-lane-decision-record.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-9-design-intake-plan.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-9-design-pattern-taxonomy.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-9-dry-run-receipt-format.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-9-lane-contract-schema.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-9-next-phases-plan.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-9-phase-0-3-closeout.md`, unrelated and not touched in this increment.
- `?? docs/scout-v0-9-review-decision-labels.md`, unrelated and not touched in this increment.

Next increment title:

Phase 3.1: Define layout patterns

## Phase 3.1 Layout Patterns Closeout

Status: complete

Date: 2026-05-20

Scope:

This increment defines reusable layout patterns for future design-system planning. It does not create routes, edit components, move CSS, alter layout behavior, or add preview surfaces.

Core layout patterns:

| Pattern | Purpose | Current evidence | Future handling |
| --- | --- | --- | --- |
| App shell | Owns whole-page frame, background, navigation region, and main content boundary. | `SpiritWorkspaceShell`, dashboard route group, `SpiritTrinityChatShell`. | Define as a high-level pattern, not a base primitive. |
| Workspace rail | Persistent navigation rail or dock across dashboard, chat, coding, and Oracle. | `WorkspacePrimarySidebar`, `DashboardInternalSidebar`, `TaskbarRail`, dashboard demo nav. | Extract only after route ownership and mobile behavior are mapped. |
| Split workspace | Two or three column working layout with rail, panel, and main content. | Chat thread rail plus conversation, coding cockpit surfaces, dashboard grids. | Pattern candidate for operational UI. |
| Dashboard grid | Responsive card grid for status, metrics, health, and action cards. | Dashboard home widgets and `dashboard-demo-v4` grid classes. | Pattern candidate after card rules are defined. |
| Content stack | Vertical flow for compact panels, forms, settings, and readouts. | Chat panels, dashboard widgets, Oracle controls. | Safe base layout pattern if spacing tokens are defined. |
| Command surface | Primary task or command area with input, actions, output, and status. | Chat composer, coding cockpit, Source Proxy review surfaces. | Domain pattern, Source Proxy gated for implementation. |
| Drawer or sheet | Mobile and overlay layout for thread lists, menus, profiles, and review panels. | `MobileSheet`, `MobileThreadDrawer`, profile sheet variants. | Needs overlay anatomy and focus rules before implementation. |
| Stage surface | Large focused mode surface inside a dashboard or workspace shell. | Dashboard stages, Oracle stage, Quarantine visual. | Pattern candidate, not a generic primitive. |
| Evidence layout | Reviewable evidence with source, status, details, checks, and actions. | Scout center, Cartographer widgets, Source Proxy style cards. | Required for future design apply lane and visual verification. |

Layout rules:

- Layout patterns compose primitives and domain components. They are not primitive replacements.
- Each layout pattern must define ownership, regions, responsive behavior, overflow behavior, and navigation behavior.
- Layout patterns may consume route CSS while they are local, but reusable layout rules must move into documented patterns before generated UI uses them.
- Mobile behavior must be part of the pattern, not a late patch.
- Fixed rails, sticky bars, drawers, and composer docks must define collision and safe-area behavior.
- Layout patterns must not introduce nested cards as section wrappers.
- No new preview route should be created from this pattern definition alone.

First layout pattern candidates:

- Workspace shell with persistent rail and main content.
- Dashboard card grid with responsive density rules.
- Chat shell with thread rail, conversation, composer dock, and mobile drawer.
- Coding console layout with task list, diff preview, approval gate, run output, and status area.
- Oracle voice surface with control cluster, transcript, status, and visualizer regions.
- Evidence review layout for Scout, Design Vault, visual verification, and Source Proxy proposals.

Stop rules:

- Stop if a layout pattern requires new route creation.
- Stop if it cannot identify route or component ownership.
- Stop if mobile overflow and keyboard behavior are unknown.
- Stop if it depends on unapproved route-specific CSS as canonical behavior.
- Stop if the pattern would add UI before token, primitive, anatomy, and variant contracts are stable.

What changed:

- Added this docs-only layout pattern definition to the v0.2 plan.

What did not change:

- No component file changed.
- No export file changed.
- No CSS file changed.
- No route changed.
- No test changed.
- No package was installed.
- No implementation, commit, push, deletion, or apply was performed.

Commands run:

```bash
cd /home/source/SpiritOS
printf '\n== PHASE 3.1 LAYOUT PATTERN CHECK ==\n'
printf '\n== STATUS ==\n'
git status -sb
printf '\n== LAYOUT COMPONENT SAMPLE ==\n'
find src/components/dashboard src/components/chat src/components/coding src/components/oracle -maxdepth 1 -type f | sort | grep -Ei 'Shell|Sidebar|TopBar|Rail|Drawer|Sheet|Panel|Surface|Workspace|Stage|Cockpit|Chat|Oracle' | sed -n '1,200p'
printf '\n== LAYOUT SOURCE SAMPLE ==\n'
grep -RIn "shell\|rail\|sidebar\|drawer\|sheet\|grid\|layout\|workspace\|panel\|stage\|split\|composer\|surface" src/components/dashboard src/components/chat src/components/coding src/components/oracle src/styles 2>/dev/null | sed -n '1,220p'
printf '\n== LAYOUT CLOSEOUT CHECK ==\n'
grep -n "Phase 3.1 Layout Patterns Closeout\|Core layout patterns\|Layout rules\|First layout pattern candidates\|Phase 3.2: Define dashboard card patterns" docs/design-system-overhaul-master-v0.2.md
printf '\n== EM DASH CHECK ==\n'
LC_ALL=C grep -n "$(printf '\342\200\224')" docs/design-system-overhaul-master-v0.2.md docs/plan-index.md 2>/dev/null || true
printf '\n== DIFF CHECK ==\n'
git --no-pager diff --check -- docs/design-system-overhaul-master-v0.2.md docs/plan-index.md
```

Expected output:

- Layout-related components and source samples are visible.
- The v0.2 plan contains the Phase 3.1 layout pattern closeout.
- Em dash check prints no matches.
- Diff check prints no whitespace errors.

Actual output:

- Layout-related components and source samples were visible across dashboard, chat, coding, Oracle, and route style files.
- Samples showed workspace shells, rails, drawers, sheets, dashboard grids, stage surfaces, composer docks, panels, and evidence layouts.
- The v0.2 plan contains the Phase 3.1 layout pattern closeout, core layout patterns, layout rules, first layout pattern candidates, and the Phase 3.2 next increment title.
- Em dash check printed no matches.
- Diff check printed no whitespace errors.

Dirty files:

- Intentional docs touched by this design-system lane: `docs/design-system-overhaul-master-v0.2.md`, `docs/plan-index.md`.
- Unrelated modified files were present in Scout, Source Proxy, coding cockpit, dashboard, and `src/lib/scout-human-readable.ts`; they were not touched by this increment.
- Unrelated untracked Cartographer and Scout docs were present; they were not touched by this increment.

Next increment title:

Phase 3.2: Define dashboard card patterns

## Phase 3.2 Dashboard Card Patterns Closeout

Status: complete

Date: 2026-05-20

Scope:

This increment defines reusable dashboard card patterns for future design-system work. It does not edit dashboard components, CSS, routes, tests, or demo surfaces.

Current dashboard card evidence:

| Pattern evidence | Files or systems found | Notes |
| --- | --- | --- |
| Dashboard widget wrapper | `DashboardWidgetCard.tsx` | Existing shallow glass panel wrapper for dashboard grids. |
| Health and status cards | `HomelabBackendHealthCard.tsx`, `HomelabSystemStatsCard.tsx`, `HomelabStorageCard.tsx`, `SpiritHealthIndicator.tsx`, `HomelabStatusBadge.tsx` | Strong evidence for reusable health, node, storage, and badge patterns. |
| Agent and workflow cards | `HomelabCartographerWidget.tsx`, `HomelabScoutIntelligenceWidget.tsx`, `ScoutIntelligenceCenter.tsx`, `HomelabBlueprintReviewWidget.tsx`, `HomelabTestRunnerWidget.tsx` | Evidence cards need explicit status, evidence, action, and manual-control contracts. |
| Stage cards and panels | `HubStageCards.tsx`, `OracleStagePanel.tsx`, `StageFallback.tsx`, `QuarantineStageVisual.tsx` | Stage surfaces behave more like focused panels than repeated metric cards. |
| Demo-v4 card language | `src/components/dashboard/demo-v4/` and `dashboard-demo-v4-*` classes | Useful reference, but not canonical until tokens and primitive rules are stable. |
| Metric clusters | Cartographer metrics, Scout metrics, system stats nodes, storage drive cards | Needs a shared metric anatomy before implementation. |

Dashboard card pattern types:

| Card type | Purpose | Required anatomy | Source of truth need |
| --- | --- | --- | --- |
| Status card | Show current service, agent, source, or lane state. | Header, status badge, primary state, detail, timestamp or freshness when applicable. | Status tone and badge variants must come from canonical tokens. |
| Metric card | Show one or more numeric or short text facts. | Label, value, unit or detail, optional trend, optional icon, overflow handling. | Metric density and typography rules must be documented. |
| Health card | Show node, storage, service, or system health. | Entity name, health badge, key measurements, degraded or offline reason, loading and error state. | Health states must map to approved semantic tokens. |
| Action card | Offer a bounded manual action or navigation. | Label, value or state, help text, icon, target, disabled reason when blocked. | Actions must remain manual and visible. |
| Evidence card | Present source, check, packet, or verification evidence. | Source label, trust or risk label, summary, details, related command or artifact, decision state. | Required for Scout, Design Vault, visual verification, and Source Proxy lanes. |
| Review card | Support approval, rejection, or defer decisions. | Request summary, scope, safety reason, diff or evidence link, approval state, manual check block. | Source Proxy owns apply authority. |
| Stage card | Represent a focused workspace or lane. | Title, stage state, affordance, destination or active region, fallback state. | Should stay route-owned until layout ownership is mapped. |

Dashboard card rules:

- Cards must be repeated items, modals, framed tools, or clear evidence packets, not wrappers around whole page sections.
- Every card must declare its role: status, metric, health, action, evidence, review, or stage.
- Every card must define loading, empty, error, offline, degraded, blocked, and ready states when those states can occur.
- Every action card must expose the action boundary and blocked reason before a user can act.
- Dashboard cards must not become route-specific style containers for unrelated content.
- Card density must be chosen by use case: compact for scan-heavy dashboards, roomy only for focused evidence or review work.
- Icons and badges must support meaning, not decoration alone.
- Text must fit within card bounds on mobile and desktop.
- Future implementation must avoid copying demo-v4 classes directly into the canonical system before token migration is complete.

First canonical dashboard card candidates:

- `DashboardWidgetCard` as an existing local wrapper candidate, pending token and anatomy review.
- Health card pattern from backend health, system stats, storage, and status badge evidence.
- Metric cluster pattern from Cartographer, Scout, system stats, and storage evidence.
- Evidence review card pattern for Scout, Design Vault, visual verification, and Source Proxy.
- Manual action card pattern for bounded dashboard commands and navigation-only action cards.
- Stage card pattern for hub, Oracle, quarantine, and coding workspace entry points.

Stop rules:

- Stop if a card pattern needs new dashboard behavior or route creation.
- Stop if the pattern cannot identify its state model.
- Stop if the pattern depends on local CSS classes as canonical tokens.
- Stop if an action card implies autonomous apply, commit, push, deletion, or unapproved promotion.
- Stop if a card pattern would hide safety, provenance, blocked reasons, or manual checks.

What changed:

- Added this docs-only dashboard card pattern definition to the v0.2 plan.

What did not change:

- No dashboard component changed.
- No CSS file changed.
- No route changed.
- No test changed.
- No package was installed.
- No implementation, commit, push, deletion, or apply was performed.

Commands run:

```bash
cd /home/source/SpiritOS
printf '\n== PHASE 3.2 DASHBOARD CARD PATTERN CHECK ==\n'
printf '\n== STATUS ==\n'
git status -sb
printf '\n== DASHBOARD FILES ==\n'
find src/components/dashboard -maxdepth 1 -type f | sort
printf '\n== DASHBOARD CARD SOURCE SAMPLE ==\n'
grep -RIn "card\|Card\|panel\|Panel\|widget\|Widget\|metric\|Metric\|status\|Status" src/components/dashboard src/app 2>/dev/null | sed -n '1,220p'
printf '\n== DASHBOARD CLOSEOUT CHECK ==\n'
grep -n "Phase 3.2 Dashboard Card Patterns Closeout\|Dashboard card pattern types\|Dashboard card rules\|First canonical dashboard card candidates\|Phase 3.3: Define chat surface patterns" docs/design-system-overhaul-master-v0.2.md
printf '\n== EM DASH CHECK ==\n'
LC_ALL=C grep -n "$(printf '\342\200\224')" docs/design-system-overhaul-master-v0.2.md docs/plan-index.md 2>/dev/null || true
printf '\n== DIFF CHECK ==\n'
git --no-pager diff --check -- docs/design-system-overhaul-master-v0.2.md docs/plan-index.md
```

Expected output:

- Dashboard files are listed.
- Dashboard card and status source samples are visible.
- The v0.2 plan contains the Phase 3.2 dashboard card pattern closeout.
- Em dash check prints no matches.
- Diff check prints no whitespace errors.

Actual output:

- Dashboard files were listed.
- Dashboard card and status source samples were visible across widget wrappers, health cards, storage and system stats cards, Cartographer, Scout, stage panels, and demo-v4 dashboard files.
- The v0.2 plan contains the Phase 3.2 dashboard card pattern closeout, dashboard card pattern types, dashboard card rules, first canonical dashboard card candidates, and the Phase 3.3 next increment title.
- Em dash check printed no matches for the written docs.
- Diff check printed no whitespace errors.

Dirty files:

- Intentional docs touched by this design-system lane: `docs/design-system-overhaul-master-v0.2.md`, `docs/plan-index.md`.
- Unrelated modified files were present in Scout, Source Proxy, coding cockpit, dashboard, and `src/lib/scout-human-readable.ts`; they were not touched by this increment.
- Unrelated untracked Cartographer and Scout docs were present; they were not touched by this increment.

Next increment title:

Phase 3.3: Define chat surface patterns

## Phase 3.3 Chat Surface Patterns Closeout

Status: complete

Date: 2026-05-20

Scope:

This increment defines reusable chat surface patterns for future design-system work. It does not edit chat components, CSS, routes, tests, model behavior, message behavior, voice behavior, or persistence.

Current chat surface evidence:

| Pattern evidence | Files or systems found | Notes |
| --- | --- | --- |
| Chat shell | `SpiritTrinityChatShell.tsx`, `SpiritChat.tsx`, `src/styles/spirit-trinity-chat.css` | Route shell, runtime chat, and route-specific styling are tightly coupled today. |
| Thread rail | `ChatThreadSidebar.tsx`, `ChatFolderSection.tsx`, `ChatThreadListItem.tsx`, `SortableChatThreadItem.tsx`, `ChatSidebarDndProvider.tsx` | Strong evidence for a reusable thread rail pattern, but not a base primitive. |
| Mobile drawer and sheet | `MobileSheet.tsx`, `MobileThreadDrawer.tsx`, `MobileChatTopBar.tsx` | Mobile behavior is first-class and must stay part of the pattern contract. |
| Message row | `SpiritMessage.tsx`, `MessageMarkdown.tsx`, `EditableUserMessage.tsx`, `StreamingCursor.tsx` | Message anatomy needs role, state, actions, streaming, and overflow contracts. |
| Message actions | `MessageActions.tsx` | Desktop hover rail and mobile sheet behavior need an explicit responsive contract. |
| Tool activity | `SpiritToolActivityCards.tsx`, `SpiritActivityPanel.tsx`, `SpiritWorkflowVisualizer.tsx` | Tool evidence belongs in a compact activity pattern, not loose ad hoc cards. |
| Model and voice controls | `ModelProfileSelector.tsx`, `ChatActiveModeBadge.tsx`, `VoiceControl.tsx`, `TTSControls.tsx`, `VoiceSettingsPanel.tsx` | Controls need shared status, disabled, selected, and disclosure rules. |
| Research and profile panels | `ResearchPlanPanel.tsx`, `SpiritUserProfilePanel.tsx` | Inline and sheet variants should be governed by overlay and panel rules. |

Chat surface pattern types:

| Surface type | Purpose | Required anatomy | Source of truth need |
| --- | --- | --- | --- |
| Chat shell | Own conversation workspace, rail slot, main conversation, composer area, mobile chrome, and overlay slots. | Shell frame, rail region, conversation region, composer dock, status region, mobile top bar. | Layout tokens and ownership rules must define rail width, safe areas, and overflow. |
| Thread rail | Show saved threads, folders, pinned threads, search, create action, row actions, and drag affordances. | Header, search, pinned section, recent section, folders, row, drag handle, actions, empty state. | Needs reusable rail density and interaction rules before extraction. |
| Thread row | Represent one chat thread in desktop rail or mobile drawer. | Title, timestamp, snippet, selected state, pinned state, folder state, drag handle, actions. | Must define truncation, hit area, focus, and mobile drag behavior. |
| Message row | Render assistant, user, system-like, streaming, edited, and tool-enriched messages. | Role shell, body, markdown, action access, streaming cursor, optional tool activity, status. | Message anatomy must stay independent from one route's CSS selectors. |
| Composer dock | Own text input, submit, attachment or tool controls, voice entry, model state, and disabled reasons. | Input area, send control, mode indicator, helper state, pending state, error state. | Composer tokens need spacing, focus, and safe-area rules. |
| Tool activity surface | Summarize tool calls, local activity, workflow state, and evidence. | Activity card, tool kind, status, label, detail, related message or run. | Should align with evidence card and visual verification patterns. |
| Model control surface | Select or display model, active mode, voice or TTS state, and profile options. | Current value, options, selected state, disabled state, explanation, disclosure. | Must use shared menu, badge, and control contracts. |
| Mobile action sheet | Move dense actions into a sheet below the desktop breakpoint. | Trigger, title, action list, destructive action handling, close, focus return. | Needs overlay primitive rules and mobile verification. |

Chat surface rules:

- Chat patterns are domain patterns, not base UI primitives.
- The chat shell must define desktop, tablet, and mobile behavior together.
- Thread rail and mobile drawer must share row anatomy while allowing different drag and scroll rules.
- Message actions must not create layout shift or appear as extra message content.
- Mobile sheets must lock background scroll only while open and must return focus after close.
- Composer dock must define collision rules with mobile keyboards, safe areas, and sticky bars.
- Tool activity must be reviewable evidence, not decorative telemetry.
- Model and voice controls must expose active state and disabled reasons.
- Route-specific `spirit-trinity-chat.css` can remain reference evidence, but future canonical rules must migrate through tokens, primitives, and documented patterns.

First canonical chat pattern candidates:

- Chat shell pattern with rail, conversation, composer dock, and mobile top bar.
- Thread rail pattern with folders, pinned threads, search, create action, row actions, and drag handles.
- Thread row pattern shared by desktop rail and mobile drawer.
- Message row pattern with markdown, streaming, editing, actions, and optional tool activity.
- Composer dock pattern with input, send, voice, mode, pending, and disabled states.
- Tool activity evidence pattern aligned with Source Proxy, Scout, and visual verification evidence cards.
- Mobile action sheet pattern for message actions, profile panels, research plans, and thread drawer controls.

Stop rules:

- Stop if a chat pattern requires changing message behavior.
- Stop if a pattern cannot describe mobile behavior and focus handling.
- Stop if it depends on route CSS as the canonical source of truth.
- Stop if a control hides active model, voice, tool, or disabled state.
- Stop if a pattern would create new chat routes, change persistence, or bypass manual Source Proxy gates.

What changed:

- Added this docs-only chat surface pattern definition to the v0.2 plan.

What did not change:

- No chat component changed.
- No CSS file changed.
- No route changed.
- No test changed.
- No package was installed.
- No implementation, commit, push, deletion, or apply was performed.

Commands run:

```bash
cd /home/source/SpiritOS
printf '\n== PHASE 3.3 CHAT SURFACE PATTERN CHECK ==\n'
printf '\n== STATUS ==\n'
git status -sb
printf '\n== CHAT FILES ==\n'
find src/components/chat -maxdepth 1 -type f | sort | head -120
printf '\n== CHAT STYLE FILES ==\n'
find src/styles -maxdepth 1 -type f | sort | grep -Ei 'chat|trinity|spirit' || true
printf '\n== CHAT SOURCE SAMPLE ==\n'
grep -RIn "thread rail\|thread\|message\|composer\|tool activity\|tool\|model\|drawer\|sheet\|mobile\|conversation\|Chat" src/components/chat src/styles/spirit-trinity-chat.css 2>/dev/null | sed -n '1,240p'
printf '\n== CHAT CLOSEOUT CHECK ==\n'
grep -n "Phase 3.3 Chat Surface Patterns Closeout\|Chat surface pattern types\|Chat surface rules\|First canonical chat pattern candidates\|Phase 3.4: Define coding console patterns" docs/design-system-overhaul-master-v0.2.md
printf '\n== EM DASH CHECK ==\n'
LC_ALL=C grep -n "$(printf '\342\200\224')" docs/design-system-overhaul-master-v0.2.md docs/plan-index.md 2>/dev/null || true
printf '\n== DIFF CHECK ==\n'
git --no-pager diff --check -- docs/design-system-overhaul-master-v0.2.md docs/plan-index.md
```

Expected output:

- Chat files and route-specific chat styles are listed.
- Chat source samples show thread rails, mobile drawers and sheets, message rows, composer references, tool activity, model controls, and mobile behavior.
- The v0.2 plan contains the Phase 3.3 chat surface pattern closeout.
- Em dash check prints no matches.
- Diff check prints no whitespace errors.

Actual output:

- Chat files and route-specific chat style files were listed.
- Chat source samples showed thread rails, mobile drawers and sheets, message rows, message actions, tool activity cards, model controls, voice controls, and mobile behavior.
- The v0.2 plan contains the Phase 3.3 chat surface pattern closeout, chat surface pattern types, chat surface rules, first canonical chat pattern candidates, and the Phase 3.4 next increment title.
- Em dash check printed no matches for the written docs.
- Diff check printed no whitespace errors.

Dirty files:

- Intentional docs touched by this design-system lane: `docs/design-system-overhaul-master-v0.2.md`, `docs/plan-index.md`.
- Unrelated modified files were present in Scout, Source Proxy, coding cockpit, dashboard, and `src/lib/scout-human-readable.ts`; they were not touched by this increment.
- Unrelated untracked Cartographer and Scout docs were present; they were not touched by this increment.

Next increment title:

Phase 3.4: Define coding console patterns

## Phase 3.4 Coding Console Patterns Closeout

Status: complete

Date: 2026-05-20

Scope:

This increment defines reusable coding console patterns for future design-system work. It does not edit coding components, Source Proxy behavior, API routes, tests, CSS, app routes, or apply logic.

Current coding console evidence:

| Pattern evidence | Files or systems found | Notes |
| --- | --- | --- |
| Coding cockpit route | `src/app/coding/page.tsx`, `CodingCockpitShell.tsx` | Live console surface already models draft, preview, approval, apply, and verify flow. |
| Design demo route | `src/app/coding/design-demo/page.tsx` | Existing route should remain a reference until preview route decisions are made later. |
| Task composer | `CodingCockpitShell.tsx` | Captures task, target file, allowed files, and expected checks. |
| Diff review | `CodingCockpitShell.tsx` | Displays proposed diff and preview status before approval. |
| Approval gate | `approval-gate-binding.ts`, `approval-gate-binding.test.ts`, `CodingCockpitShell.tsx` | Strong evidence that approval must bind to target file, allowed files, and preview gate state. |
| Safety checks | `proxy-safety-smoke.test.ts`, `client-fallback.test.ts`, `coding-workflow-step.test.ts` | Existing tests reinforce Source Proxy boundaries and fallback behavior. |
| Status strip | `CodingCockpitShell.tsx` | Draft, Preview, Approval, Apply, Verify stages are already visible in live code. |

Coding console pattern types:

| Surface type | Purpose | Required anatomy | Source of truth need |
| --- | --- | --- | --- |
| Task composer | Collect a bounded coding task before any preview. | Task text, target file, allowed files, expected checks, validation messages, preview trigger. | Must align with Source Proxy task spec fields. |
| Scope summary | Show the active task boundary. | Task title, target, allowed files, expected checks, current state, blocked reason. | Must be derived from the proposal state, not duplicate hidden state. |
| Workflow status strip | Show current progress through the manual lane. | Draft, Preview, Approval, Apply, Verify, active step, completed states, blocked states. | Must keep apply and verify separate. |
| Diff preview | Review proposed file changes before approval. | Diff text, changed files, preview status, reviewer summary, verifier summary, blocker, empty diff state. | Source Proxy owns preview generation and safety gates. |
| Approval gate | Record human approval only when preview gates pass. | Gate checklist, approval availability, target match, allowed files, no deletion, no commit, no push, approve action. | Must bind approval to the reviewed diff and scope. |
| Apply lock | Prevent application until approval is recorded. | Apply unavailable reason, approved state, apply action, apply summary, post-apply warning. | Source Proxy owns apply. Design and coding agents cannot apply directly. |
| Verification prompt | Tell the human what to check after apply. | Expected commands, verification required state, post-apply summary, residual risk. | Must connect to manual checks and future visual verification evidence. |
| Mobile review rail | Make review usable on narrow screens. | Sticky state, compact task summary, approval availability, primary next action. | Needs mobile viewport verification before implementation changes. |

Coding console rules:

- The coding console is a Source Proxy lane surface, not an autonomous coding agent surface.
- The console must keep proposal, preview, approval, apply, and verification visually distinct.
- Approval must never be available before preview gates pass.
- Apply must never be available before human approval is recorded.
- Diff preview must show changed files, blocker state, and reviewer or verifier summaries when available.
- Task composer controls must expose target file, allowed files, and expected checks before preview.
- Empty diff, already satisfied, blocked, timeout, and error states must be first-class states.
- Mobile review must preserve the same safety gates as desktop review.
- Design Coding Agent work must enter this lane as a bounded proposal, not as a direct file change.

First canonical coding console candidates:

- Source Proxy task composer pattern with task, target, allowed files, and expected checks.
- Diff preview pattern with changed files, blocker, reviewer evidence, verifier evidence, and empty state.
- Approval gate pattern shared by coding and future design apply lanes.
- Apply lock pattern that makes no-change, approved-not-applied, applied, and verification-required states explicit.
- Workflow status strip pattern for Draft, Preview, Approval, Apply, and Verify.
- Mobile review summary pattern for small-screen approval review.

Stop rules:

- Stop if a pattern implies autonomous apply.
- Stop if approval can be separated from the reviewed diff and allowed file scope.
- Stop if a console pattern hides changed files, blockers, or verification requirements.
- Stop if a pattern requires API or Source Proxy behavior changes.
- Stop if a design coding flow bypasses the Source Proxy gated lane.

What changed:

- Added this docs-only coding console pattern definition to the v0.2 plan.

What did not change:

- No coding component changed.
- No Source Proxy behavior changed.
- No app route changed.
- No CSS file changed.
- No test changed.
- No package was installed.
- No implementation, commit, push, deletion, or apply was performed.

Commands run:

```bash
cd /home/source/SpiritOS
printf '\n== PHASE 3.4 CODING CONSOLE PATTERN CHECK ==\n'
printf '\n== STATUS ==\n'
git status -sb
printf '\n== CODING FILES ==\n'
find src/components/coding src/app/coding -maxdepth 3 -type f | sort 2>/dev/null | sed -n '1,180p'
printf '\n== CODING SOURCE SAMPLE ==\n'
grep -RIn "console\|Console\|diff\|Diff\|approval\|Approval\|task\|Task\|run\|Run\|output\|Output\|status\|Status\|cockpit\|Cockpit" src/components/coding src/app/coding 2>/dev/null | sed -n '1,240p'
printf '\n== CODING CLOSEOUT CHECK ==\n'
grep -n "Phase 3.4 Coding Console Patterns Closeout\|Coding console pattern types\|Coding console rules\|First canonical coding console candidates\|Phase 3.5: Define Oracle voice surface patterns" docs/design-system-overhaul-master-v0.2.md
printf '\n== EM DASH CHECK ==\n'
LC_ALL=C grep -n "$(printf '\342\200\224')" docs/design-system-overhaul-master-v0.2.md docs/plan-index.md 2>/dev/null || true
printf '\n== DIFF CHECK ==\n'
git --no-pager diff --check -- docs/design-system-overhaul-master-v0.2.md docs/plan-index.md
```

Expected output:

- Coding files and app route files are listed.
- Coding source samples show task composer, diff preview, approval gate, safety states, apply lock, status strip, and verification states.
- The v0.2 plan contains the Phase 3.4 coding console pattern closeout.
- Em dash check prints no matches.
- Diff check prints no whitespace errors.

Actual output:

- Coding files and app route files were listed.
- Coding source samples showed task composer, diff preview, approval gate, safety states, apply lock, workflow status strip, empty diff handling, blocked states, and verification states.
- The v0.2 plan contains the Phase 3.4 coding console pattern closeout, coding console pattern types, coding console rules, first canonical coding console candidates, and the Phase 3.5 next increment title.
- Em dash check printed no matches for the written docs.
- Diff check printed no whitespace errors.

Dirty files:

- Intentional docs touched by this design-system lane: `docs/design-system-overhaul-master-v0.2.md`, `docs/plan-index.md`.
- Unrelated modified files were present in Scout, Source Proxy, coding cockpit, dashboard, and `src/lib/scout-human-readable.ts`; they were not touched by this increment.
- Unrelated untracked Cartographer and Scout docs were present; they were not touched by this increment.

Next increment title:

Phase 3.5: Define Oracle voice surface patterns

## Phase 3.5 Oracle Voice Surface Patterns Closeout

Status: complete

Date: 2026-05-20

Scope:

This increment defines reusable Oracle voice surface patterns for future design-system work. It does not edit Oracle components, voice runtime behavior, CSS, app routes, tests, dashboard widgets, audio logic, or memory behavior.

Current Oracle voice surface evidence:

| Pattern evidence | Files or systems found | Notes |
| --- | --- | --- |
| Oracle route | `src/app/oracle/page.tsx` | Existing full Oracle workspace route is live code, not a new design-system preview route. |
| Voice surface | `OracleVoiceSurface.tsx` | Main surface combines session loop, voice input, TTS, transcript, activity, status, and visual regions. |
| Voice controls | `OracleVoiceControls.tsx`, `VoiceControl.tsx` | Control cluster handles start, stop, finish, loop mode, VAD settings, TTS, catalog, and selected voice. |
| Status card | `OracleVoiceStatusCard.tsx` | Status evidence includes runtime label, latency, transcript, provider, selected voice, playback, and errors. |
| Transcript | `OracleSessionTranscript.tsx` | Transcript and mic pickup create a reviewable session record. |
| Visualizer and orb | `OracleVoiceVisualizer.tsx`, `OracleOrbSprite.tsx`, `oracle-visuals.css` | Domain-specific media pattern with listening, processing, speaking, and idle states. |
| Dashboard entry points | `HomelabOracleVoiceWidget.tsx`, `OracleStagePanel.tsx`, `DashboardDemoV4OracleHero.tsx` | Smaller Oracle surfaces should stay entry points, not duplicate the full workspace. |
| Tests | Oracle component tests and dashboard Oracle tests | Good evidence that the surface has separately testable parts. |

Oracle voice surface pattern types:

| Surface type | Purpose | Required anatomy | Source of truth need |
| --- | --- | --- | --- |
| Oracle voice workspace | Host the full hands-free session. | Header, status strip, visual stage, controls, transcript, activity, fallback input, diagnostic details. | Route ownership must stay explicit. |
| Voice control cluster | Manage session and audio settings. | Start, stop, finish, loop mode, TTS controls, voice picker, VAD settings, disabled reasons, secure-context warning. | Must align with shared control, disclosure, and disabled-state rules. |
| Voice status card | Explain the current voice runtime state. | Status, runtime label, transcript state, provider, selected voice, latency, playback, last error. | Must map states to semantic status tokens. |
| Transcript surface | Preserve what the system heard and what was sent. | Pickup list, message text, timestamp or sequence, empty state, overflow handling. | Must support privacy and review boundaries before sharing outside Oracle. |
| Voice visualizer | Show audio and session state without becoming the only status source. | Visual state, audio level, compact variant, aria label, reduced motion behavior. | Motion tokens and accessibility rules are required before reuse. |
| Oracle orb media | Provide branded Oracle visual state. | Variant, state, decorative SVG, accessible label, bounded sizing. | Keep domain-specific unless a generic media primitive is justified. |
| Oracle dashboard entry | Open or summarize Oracle from dashboard contexts. | Compact status, call to action, visual hint, unavailable state. | Must not duplicate full workspace controls. |

Oracle voice rules:

- Oracle voice patterns are domain patterns, not base primitives.
- The voice visualizer and orb must support state, reduced motion, and nonvisual status text.
- Visual state must not be the only way to understand whether Oracle is listening, processing, speaking, idle, blocked, or errored.
- Audio controls must expose disabled reasons and secure-context requirements.
- Transcript and pickup regions must define overflow, empty, pending, and error states.
- Dashboard Oracle widgets should summarize or route to Oracle, not recreate the full voice workspace.
- TTS, VAD, selected voice, provider, and latency data belong in status or diagnostic surfaces, not hidden state.
- Future design-system extraction must keep privacy, microphone permission, audio unlock, and manual control boundaries visible.

First canonical Oracle pattern candidates:

- Oracle voice workspace pattern with header, visual stage, controls, transcript, activity, and fallback input.
- Voice control cluster pattern for start, stop, finish, loop mode, TTS, voice picker, and VAD settings.
- Voice status card pattern for runtime state, provider, selected voice, latency, playback, transcript, and errors.
- Transcript surface pattern for mic pickup, submitted text, assistant response evidence, and empty states.
- Voice visualizer media pattern with state, audio level, compact variant, and reduced motion requirement.
- Oracle dashboard entry pattern for compact status and route handoff.

Stop rules:

- Stop if a pattern changes voice runtime behavior.
- Stop if a pattern hides microphone, secure-context, audio unlock, or disabled reasons.
- Stop if visual animation becomes the only status indicator.
- Stop if dashboard widgets duplicate the full Oracle workspace.
- Stop if a reusable media primitive is proposed before motion and accessibility tokens are stable.

What changed:

- Added this docs-only Oracle voice surface pattern definition to the v0.2 plan.

What did not change:

- No Oracle component changed.
- No chat voice control changed.
- No dashboard component changed.
- No CSS file changed.
- No app route changed.
- No test changed.
- No package was installed.
- No implementation, commit, push, deletion, or apply was performed.

Commands run:

```bash
cd /home/source/SpiritOS
printf '\n== PHASE 3.5 ORACLE VOICE SURFACE PATTERN CHECK ==\n'
printf '\n== STATUS ==\n'
git status -sb
printf '\n== ORACLE FILES ==\n'
find src/components/oracle src/app/oracle src/components/dashboard -maxdepth 3 -type f 2>/dev/null | sort | grep -Ei 'oracle|voice|tts|visual|stage|panel|orb|control|surface' | sed -n '1,180p'
printf '\n== ORACLE SOURCE SAMPLE ==\n'
grep -RIn "oracle\|Oracle\|voice\|Voice\|tts\|TTS\|transcript\|Transcript\|visualizer\|Visualizer\|orb\|Orb\|listening\|speaking\|stage\|Stage\|control\|Control" src/components/oracle src/app/oracle src/components/dashboard src/components/chat 2>/dev/null | sed -n '1,260p'
printf '\n== ORACLE CLOSEOUT CHECK ==\n'
grep -n "Phase 3.5 Oracle Voice Surface Patterns Closeout\|Oracle voice surface pattern types\|Oracle voice rules\|First canonical Oracle pattern candidates\|Phase 3.6: Decide whether a preview route is needed" docs/design-system-overhaul-master-v0.2.md
printf '\n== EM DASH CHECK ==\n'
LC_ALL=C grep -n "$(printf '\342\200\224')" docs/design-system-overhaul-master-v0.2.md docs/plan-index.md 2>/dev/null || true
printf '\n== DIFF CHECK ==\n'
git --no-pager diff --check -- docs/design-system-overhaul-master-v0.2.md docs/plan-index.md
```

Expected output:

- Oracle files and dashboard Oracle entry points are listed.
- Oracle source samples show voice surface, controls, transcript, status card, visualizer, orb, TTS, listening, speaking, and stage behavior.
- The v0.2 plan contains the Phase 3.5 Oracle voice surface pattern closeout.
- Em dash check prints no matches.
- Diff check prints no whitespace errors.

Actual output:

- Oracle files and dashboard Oracle entry points were listed.
- Oracle source samples showed the voice surface, controls, transcript, status card, visualizer, orb, TTS state, listening state, speaking state, and stage behavior.
- The v0.2 plan contains the Phase 3.5 Oracle voice surface pattern closeout, Oracle voice surface pattern types, Oracle voice rules, first canonical Oracle pattern candidates, and the Phase 3.6 next increment title.
- Em dash check printed no matches for the written docs.
- Diff check printed no whitespace errors.

Dirty files:

- Intentional docs touched by this design-system lane: `docs/design-system-overhaul-master-v0.2.md`, `docs/plan-index.md`.
- Unrelated modified files were present in Scout, Source Proxy, coding cockpit, dashboard, and `src/lib/scout-human-readable.ts`; they were not touched by this increment.
- Unrelated untracked Cartographer and Scout docs were present; they were not touched by this increment.

Next increment title:

Phase 3.6: Decide whether a preview route is needed

## Phase 3.6 Preview Route Decision Closeout

Status: complete

Date: 2026-05-20

Decision:

Do not create a new design-system preview route in v0.2 yet. Existing demo routes are enough reference material for planning. A new preview route should wait until token, primitive, layout, dashboard, chat, coding, Oracle, visual verification, and Source Proxy apply-lane contracts are stable enough to justify a bounded implementation increment.

Scope:

This increment decides whether a preview route is needed. It does not create a route, edit an existing route, move demo code, change Storybook or Playwright setup, install packages, or implement visual snapshots.

Existing route evidence:

| Route or system | Current state | Decision |
| --- | --- | --- |
| `src/app/design-demo/page.tsx` | Existing design demo route. | Keep as reference evidence. Do not promote to canonical design-system route yet. |
| `src/app/design-demo/coding/page.tsx` | Existing coding-related design demo route. | Keep as reference evidence. Do not expand in this increment. |
| `src/app/coding/design-demo/page.tsx` | Existing vibe test canvas with `GlassPanel`. | Keep as reference evidence. Do not modify. |
| `src/app/coding/page.tsx` | Live Source Proxy cockpit surface. | Treat as production lane surface, not a design-system preview route. |
| Dashboard, chat, and Oracle routes | Live feature routes. | Use as pattern evidence only. Do not turn them into preview surfaces. |
| Storybook or visual preview tooling | Not treated as active in this increment. | Reassess during visual verification and tooling increments. |

Preview route decision criteria:

| Criterion | Required before route creation | Current decision |
| --- | --- | --- |
| Token stability | Canonical token categories, naming rules, migration map, and accessibility requirements are approved. | Not ready yet. |
| Primitive stability | Required primitive set, anatomy, variant rules, and leakage rules are approved. | Not ready yet. |
| Pattern stability | Layout, dashboard, chat, coding, Oracle, and future pattern rules are documented. | In progress. |
| Visual verification | Screenshot targets, mobile viewports, and diff reporting are defined. | Not ready yet. |
| Source Proxy lane | Allowed files, bounded diff preview, approval gate, rollback, and post-apply checks are defined. | Not ready yet. |
| Route ownership | Owner, purpose, non-production status, and deletion policy are clear. | Not ready yet. |

Recommended future route shape, if approved later:

- Name it as a clearly non-production design-system preview route.
- Keep it behind a bounded Source Proxy task with explicit allowed files.
- Use only approved tokens, primitives, and pattern examples.
- Include static states for dashboard cards, chat rows, coding review, Oracle status, evidence cards, and visual verification targets.
- Avoid runtime side effects, API calls, microphone access, file apply, commits, pushes, or external scraping.
- Make it screenshot-friendly only after visual verification targets are defined.

Stop rules:

- Stop if anyone tries to create the route before Source Proxy approval.
- Stop if the preview route would become a new production surface.
- Stop if it depends on unstable route-specific CSS as canonical design-system behavior.
- Stop if it requires Storybook, Playwright, or package installation before the tooling increment approves that.
- Stop if it adds UI examples before tokens, primitives, and pattern contracts are stable.

What changed:

- Added this docs-only decision that no new design-system preview route should be created yet.

What did not change:

- No app route changed.
- No component changed.
- No CSS file changed.
- No test changed.
- No Storybook or Playwright setup changed.
- No package was installed.
- No implementation, commit, push, deletion, or apply was performed.

Commands run:

```bash
cd /home/source/SpiritOS
printf '\n== PHASE 3.6 PREVIEW ROUTE DECISION CHECK ==\n'
printf '\n== STATUS ==\n'
git status -sb
printf '\n== EXISTING DESIGN / PREVIEW ROUTE FILES ==\n'
find src/app -maxdepth 5 -type f | sort | grep -Ei 'design|preview|demo|coding|dashboard|chat|oracle' | sed -n '1,220p'
printf '\n== DESIGN DEMO ROUTE CHECK ==\n'
test -f src/app/coding/design-demo/page.tsx && sed -n '1,220p' src/app/coding/design-demo/page.tsx || true
printf '\n== PREVIEW ROUTE DECISION CLOSEOUT CHECK ==\n'
grep -n "Phase 3.6 Preview Route Decision Closeout\|Do not create a new design-system preview route\|Preview route decision criteria\|Recommended future route shape\|Phase 4.1: Audit Playwright readiness" docs/design-system-overhaul-master-v0.2.md
printf '\n== EM DASH CHECK ==\n'
LC_ALL=C grep -n "$(printf '\342\200\224')" docs/design-system-overhaul-master-v0.2.md docs/plan-index.md 2>/dev/null || true
printf '\n== DIFF CHECK ==\n'
git --no-pager diff --check -- docs/design-system-overhaul-master-v0.2.md docs/plan-index.md
```

Expected output:

- Existing design, demo, coding, dashboard, chat, Oracle, and preview-related route files are listed.
- The existing coding design demo route can be read as reference evidence.
- The v0.2 plan contains the Phase 3.6 preview route decision closeout.
- The closeout states that no new design-system preview route should be created yet.
- Em dash check prints no matches.
- Diff check prints no whitespace errors.

Actual output:

- Existing design, demo, coding, dashboard, chat, Oracle, and preview-related route files were listed.
- The existing coding design demo route was readable as reference evidence.
- The v0.2 plan contains the Phase 3.6 preview route decision closeout, decision criteria, recommended future route shape, and the Phase 4.1 next increment title.
- The closeout states that no new design-system preview route should be created yet.
- Em dash check printed no matches for the written docs.
- Diff check printed no whitespace errors.

Dirty files:

- Intentional docs touched by this design-system lane: `docs/design-system-overhaul-master-v0.2.md`, `docs/plan-index.md`.
- Unrelated modified files were present in Scout, Source Proxy, coding cockpit, dashboard, and `src/lib/scout-human-readable.ts`; they were not touched by this increment.
- Unrelated untracked Cartographer and Scout docs were present; they were not touched by this increment.

Next increment title:

Phase 4.1: Audit Playwright readiness

## Phase 4.1 Playwright Readiness Audit Closeout

Status: complete

Date: 2026-05-20

Readiness decision:

Playwright is present as configuration, but the visual verification lane is not ready for screenshot baselines or visual diff enforcement yet. Do not install dependencies, install browsers, generate screenshots, or add baseline artifacts in this increment.

Scope:

This increment audits visual tooling readiness only. It does not change Playwright config, Vitest config, package dependencies, tests, browser binaries, screenshots, snapshots, app routes, or UI code.

Current tooling evidence:

| Evidence | Current state | Decision |
| --- | --- | --- |
| `playwright.config.mjs` | Exists and imports `@playwright/test`. | Configuration evidence exists, but local dependency readiness must be confirmed before running Playwright. |
| `package.json` | Present. The audit did not find an `@playwright/test` dependency line. | Do not run or install Playwright as part of this increment. |
| `vitest.config.mjs` | Present. | Existing unit and component test setup can remain the near-term verification base. |
| Storybook | No active Storybook setup was confirmed by this audit. | Do not add Storybook in this increment. |
| Chromatic | No active Chromatic setup was confirmed by this audit. | Do not add Chromatic in this increment. |
| Screenshot baselines | No active baseline lane was confirmed by this audit. | Plan targets first, capture later. |
| Existing visual-style tests | Vitest/component tests reference visualizer, viewport, demo, and shallow visual-diff behavior. | Treat as current coverage evidence, not screenshot coverage. |

Visual readiness grades:

| Area | Grade | Reason |
| --- | --- | --- |
| Config presence | B | A Playwright config exists, so the repo has a starting point. |
| Dependency readiness | D | `@playwright/test` was not confirmed in `package.json`, so browser checks should not be assumed runnable. |
| Screenshot baseline readiness | D | No baseline capture lane or approved artifact path is active. |
| Existing component visual coverage | C | Several Vitest tests cover visual components, viewport helpers, Oracle visualizer, and demo links. |
| Storybook or Chromatic readiness | F | No active setup was confirmed. |
| Safe next planning readiness | B | The repo has enough evidence to define screenshot target lists and visual report contracts next. |

Required before visual capture:

- Confirm whether `@playwright/test` should be added, reused from an external environment, or kept optional.
- Define screenshot target list before any capture.
- Define viewport matrix before any capture.
- Define artifact paths, retention rules, and approval boundaries.
- Define how screenshots attach to Design Vault, Design Pack, Visual Verifier, and Source Proxy proposals.
- Keep every visual check advisory until Source Proxy gating and human review are defined.

Stop rules:

- Stop if the next action requires installing `@playwright/test` or browser binaries.
- Stop if screenshots would be generated without approved target and artifact paths.
- Stop if a visual diff would become an automatic apply gate.
- Stop if Storybook, Chromatic, axe, or screenshot tooling would be added without a separate approved increment.
- Stop if visual verification evidence would bypass Source Proxy approval or human review.

What changed:

- Added this docs-only Playwright readiness audit closeout to the v0.2 plan.

What did not change:

- No package changed.
- No Playwright config changed.
- No Vitest config changed.
- No tests changed.
- No screenshots were captured.
- No browser binaries were installed.
- No implementation, commit, push, deletion, route creation, or apply was performed.

Commands run:

```bash
cd /home/source/SpiritOS
printf '\n== PHASE 4.1 PLAYWRIGHT READINESS CHECK ==\n'
printf '\n== STATUS ==\n'
git status -sb
printf '\n== PLAYWRIGHT CONFIG FILES ==\n'
ls -la playwright.config.mjs playwright.config.ts package.json vitest.config.mjs 2>/dev/null || true
printf '\n== PACKAGE VISUAL TOOLING REFERENCES ==\n'
grep -n "playwright\|storybook\|chromatic\|axe\|toHaveScreenshot\|visual\|screenshot" package.json playwright.config.mjs playwright.config.ts vitest.config.mjs 2>/dev/null || true
printf '\n== TEST FILES WITH VISUAL / PLAYWRIGHT TERMS ==\n'
find src -type f | grep -Ei 'test|spec' | xargs grep -n "playwright\|toHaveScreenshot\|screenshot\|viewport\|visual\|axe" 2>/dev/null | sed -n '1,220p' || true
printf '\n== PLAYWRIGHT READINESS CLOSEOUT CHECK ==\n'
grep -n "Phase 4.1 Playwright Readiness Audit Closeout\|Playwright is present as configuration\|Visual readiness grades\|Required before visual capture\|Phase 4.2: Define screenshot target list" docs/design-system-overhaul-master-v0.2.md
printf '\n== EM DASH CHECK ==\n'
LC_ALL=C grep -n "$(printf '\342\200\224')" docs/design-system-overhaul-master-v0.2.md docs/plan-index.md 2>/dev/null || true
printf '\n== DIFF CHECK ==\n'
git --no-pager diff --check -- docs/design-system-overhaul-master-v0.2.md docs/plan-index.md
```

Expected output:

- Playwright config, package, and Vitest config files are listed when present.
- Tooling references show Playwright config and visual-related test/doc references.
- The v0.2 plan contains the Phase 4.1 Playwright readiness closeout.
- The closeout states that no dependency install, browser install, screenshot generation, or baseline lane is active yet.
- Em dash check prints no matches.
- Diff check prints no whitespace errors.

Actual output:

- Playwright config, package, and Vitest config files were listed.
- Tooling references showed `playwright.config.mjs` importing `@playwright/test`; the audit did not find a matching dependency line in `package.json`.
- Visual-related Vitest and component tests were visible for chat, design demo, Oracle, dashboard, viewport behavior, and coding visual-diff safeguards.
- The v0.2 plan contains the Phase 4.1 Playwright readiness closeout, visual readiness grades, required before visual capture, and the Phase 4.2 next increment title.
- The closeout states that no dependency install, browser install, screenshot generation, or baseline lane is active yet.
- Em dash check printed no matches for the written docs.
- Diff check printed no whitespace errors.

Dirty files:

- Intentional docs touched by this design-system lane: `docs/design-system-overhaul-master-v0.2.md`, `docs/plan-index.md`.
- Unrelated modified files were present in Scout, Source Proxy, coding cockpit, dashboard, and `src/lib/scout-human-readable.ts`; they were not touched by this increment.
- Unrelated untracked Cartographer and Scout docs were present; they were not touched by this increment.

Next increment title:

Phase 4.2: Define screenshot target list

## Phase 4.2 Screenshot Target List Closeout

Status: complete

Date: 2026-05-20

Scope:

This increment defines future screenshot targets for visual verification. It does not run Playwright, capture screenshots, create baselines, install tooling, edit routes, edit components, or add tests.

Target decision:

Screenshot targets should start with high-signal existing surfaces, not new preview routes. The first target list should cover production-like route surfaces, current demo references, and future evidence review surfaces. Capture is deferred until Playwright dependency readiness, viewport matrix, artifact paths, and Source Proxy attachment rules are approved.

Primary screenshot targets:

| Target | Route or component evidence | Why it matters | Capture status |
| --- | --- | --- | --- |
| Dashboard home | `src/app/(dashboard)/page.tsx`, `SpiritWorkspaceShell`, dashboard widgets | Main operational shell, card grid, rail, status widgets, and density rules. | Planned only. |
| Dashboard demo v4 | `src/components/dashboard/demo-v4/`, `src/app/design-demo/page.tsx` | Internal design reference for current SpiritOS visual language and Design Vault pack evidence. | Planned only. |
| Chat workspace | `src/app/chat/page.tsx`, `SpiritTrinityChatShell`, `SpiritChat` | Thread rail, conversation, composer, actions, mobile drawer, and route-specific styling. | Planned only. |
| Coding cockpit | `src/app/coding/page.tsx`, `CodingCockpitShell` | Source Proxy task composer, diff preview, approval gate, apply lock, and verification states. | Planned only. |
| Coding design demo | `src/app/coding/design-demo/page.tsx` | Existing small design demo surface that exercises `GlassPanel` and token treatment. | Planned only. |
| Oracle workspace | `src/app/oracle/page.tsx`, `OracleVoiceSurface` | Voice controls, transcript, status card, visualizer, orb, and diagnostic details. | Planned only. |
| Design demo route | `src/app/design-demo/page.tsx`, `SpiritDesignDemo` | Current visual preview and production-route link evidence. | Planned only. |
| Intelligence or Scout surface | `src/app/intelligence/page.tsx`, Scout dashboard components | Future Scout design intake and evidence review target. | Planned only. |
| Proxy/backend review surface | `src/app/proxy-backend/page.tsx`, Source Proxy review patterns | Future gated proposal and visual evidence review target. | Planned only. |

Required state targets:

| Surface | States to capture later | Notes |
| --- | --- | --- |
| Dashboard | Ready, loading, degraded or unavailable widget, dense card grid, mobile rail state. | Use stable fixtures where possible. |
| Chat | Empty thread, active conversation, streaming message, message actions, mobile drawer, composer focus. | Do not require real external model calls. |
| Coding cockpit | Empty draft, preview ready, approval available, approved not applied, blocked, applied verification required. | Must stay Source Proxy gated. |
| Oracle | Idle, listening, processing, speaking, error, secure-context warning if applicable. | Avoid real microphone dependency in baseline capture. |
| Design demo | Default demo, compact viewport, component preview links. | Keep demo references non-canonical until approved. |
| Evidence review | Source card, design pack, visual diff report, approval packet. | May wait until Design Vault and Source Proxy evidence schemas are stable. |

Viewport target list:

| Viewport | Purpose | Status |
| --- | --- | --- |
| Desktop wide | Primary working layout and dense operational dashboard review. | Planned only. |
| Desktop standard | Common laptop layout and card density review. | Planned only. |
| Tablet | Rail, split-pane, and touch behavior review. | Planned only. |
| Mobile narrow | Drawer, sheet, composer, approval, and safe-area behavior review. | Planned only. |
| Mobile tall | Keyboard, sticky bars, and long-content overflow review. | Planned only. |

Target rules:

- Use existing routes and surfaces before proposing any new preview route.
- Do not capture screenshots until dependency readiness and artifact paths are approved.
- Do not let screenshots become automatic apply approval.
- Every screenshot target must declare route, viewport, state, fixture or data source, expected evidence, and owner.
- Screenshot targets must include mobile behavior, not just desktop.
- Screenshots must attach to Design Vault, Design Pack, Visual Verifier, or Source Proxy proposals as evidence only.
- Any target that needs secrets, live microphone access, external model calls, or destructive apply actions must be replaced with a fixture state.

Stop rules:

- Stop if defining a target requires route creation.
- Stop if capture requires installing Playwright or browser binaries.
- Stop if a target depends on live external services without fixtures.
- Stop if a screenshot would expose secrets, private data, or protected paths.
- Stop if screenshot evidence is treated as approval instead of review evidence.

What changed:

- Added this docs-only screenshot target list to the v0.2 plan.

What did not change:

- No screenshots were captured.
- No baseline files were created.
- No app route changed.
- No component changed.
- No CSS file changed.
- No test changed.
- No package was installed.
- No implementation, commit, push, deletion, route creation, or apply was performed.

Commands run:

```bash
cd /home/source/SpiritOS
printf '\n== PHASE 4.2 SCREENSHOT TARGET LIST CHECK ==\n'
printf '\n== STATUS ==\n'
git status -sb
printf '\n== ROUTE FILES FOR TARGETS ==\n'
find src/app -maxdepth 5 -type f | sort | grep -Ei 'dashboard|chat|coding|oracle|design-demo|page\.tsx' | sed -n '1,220p'
printf '\n== SURFACE COMPONENTS FOR TARGETS ==\n'
find src/components/dashboard src/components/chat src/components/coding src/components/oracle src/components/design-demo -maxdepth 3 -type f 2>/dev/null | sort | grep -Ei 'Shell|Surface|Card|Widget|Panel|Demo|Chat|Oracle|Coding|Cockpit|Visualizer|Transcript|Controls|Status' | sed -n '1,260p'
printf '\n== SCREENSHOT TARGET CLOSEOUT CHECK ==\n'
grep -n "Phase 4.2 Screenshot Target List Closeout\|Primary screenshot targets\|Required state targets\|Viewport target list\|Phase 4.3: Add optional visual capture plan" docs/design-system-overhaul-master-v0.2.md
printf '\n== EM DASH CHECK ==\n'
LC_ALL=C grep -n "$(printf '\342\200\224')" docs/design-system-overhaul-master-v0.2.md docs/plan-index.md 2>/dev/null || true
printf '\n== DIFF CHECK ==\n'
git --no-pager diff --check -- docs/design-system-overhaul-master-v0.2.md docs/plan-index.md
```

Expected output:

- Route files for dashboard, chat, coding, Oracle, design demo, and related surfaces are listed.
- Surface components for dashboard, chat, coding, Oracle, and design demo are listed.
- The v0.2 plan contains the Phase 4.2 screenshot target closeout.
- The closeout defines primary targets, required states, and viewport targets without capture.
- Em dash check prints no matches.
- Diff check prints no whitespace errors.

Actual output:

- Route files for dashboard, chat, coding, Oracle, design demo, intelligence, proxy backend, and related coding API surfaces were listed.
- Surface components for dashboard, chat, coding, Oracle, and design demo were listed.
- The v0.2 plan contains the Phase 4.2 screenshot target closeout, primary screenshot targets, required state targets, viewport target list, and the Phase 4.3 next increment title.
- The closeout defines target, state, and viewport lists without screenshot capture.
- Em dash check printed no matches for the written docs.
- Diff check printed no whitespace errors.

Dirty files:

- Intentional docs touched by this design-system lane: `docs/design-system-overhaul-master-v0.2.md`, `docs/plan-index.md`.
- Unrelated modified files were present in Scout, Source Proxy, coding cockpit, dashboard, and `src/lib/scout-human-readable.ts`; they were not touched by this increment.
- Unrelated untracked Cartographer and Scout docs were present; they were not touched by this increment.

Next increment title:

Phase 4.3: Add optional visual capture plan

## Phase 4.3 Optional Visual Capture Plan Closeout

Status: complete

Date: 2026-05-20

Scope:

This increment defines an optional visual capture plan that can run only after tooling, targets, artifact paths, and human approval are confirmed. It does not install Playwright, install browsers, run Playwright, capture screenshots, create baselines, edit tests, or create artifacts.

Capture readiness decision:

Keep visual capture disabled by default. The current repository has `playwright.config.mjs`, but local `@playwright/test` was not confirmed as installed. Any future capture lane must use skip-safe detection, explicit approval, approved target lists, fixture rules, artifact paths, and Source Proxy evidence attachment rules before it can run.

Optional capture gate:

| Gate | Requirement | Current state |
| --- | --- | --- |
| Tooling | `playwright.config.*` exists and local `@playwright/test` resolves. | Config exists, local dependency was not confirmed. |
| Targets | Phase 4.2 target list exists and is approved. | Target list drafted, not yet approved for capture. |
| Viewports | Desktop, tablet, and mobile viewport matrix is approved. | Planned, not yet approved. |
| Artifacts | Reference and generated screenshot paths are approved. | Not yet approved. |
| Data fixtures | Target states avoid secrets, live microphone dependency, destructive apply, and external service dependence. | Not yet defined. |
| Human approval | Operator approves the capture run and expected output. | Required later. |
| Source Proxy handling | Capture evidence is attached as evidence only, never as automatic approval. | Planned only. |

Skip-safe command pattern:

```bash
cd /home/source/SpiritOS
if ls playwright.config.* >/dev/null 2>&1 && node -e "require.resolve('@playwright/test/package.json')" >/dev/null 2>&1; then
  echo "Playwright config and local @playwright/test found. Future approved increment may list or run visual capture."
else
  echo "Playwright visual capture skipped. Config or local @playwright/test is missing."
fi
```

Future capture packet shape:

| Field | Purpose |
| --- | --- |
| `capture_id` | Unique id for the proposed capture run. |
| `reason` | Why capture is needed. |
| `approved_targets` | Routes, states, and viewports approved for capture. |
| `command` | Exact command proposed for the capture run. |
| `server_command` | Exact local server command, if needed. |
| `artifact_root` | Approved output folder. |
| `reference_paths` | Existing approved screenshots or source references. |
| `generated_paths` | Candidate screenshots produced by the run. |
| `known_limits` | Missing fixtures, unstable data, browser gaps, or non-determinism. |
| `reviewer_notes` | Human review notes after capture. |

Artifact rules:

- Keep `reference/` and `generated/` screenshots separate.
- Store generated captures under an approved Design Vault, Design Pack, Visual Verifier, or Source Proxy evidence folder.
- Include route, viewport, state, theme, browser project, timestamp, and capture id in metadata.
- Do not write screenshots into production component folders.
- Do not commit screenshots unless a later increment explicitly asks for that.
- Do not overwrite approved reference screenshots without a separate approval.

Stop rules:

- Stop if local `@playwright/test` is missing.
- Stop if the run would install dependencies or browsers.
- Stop if target routes, viewports, states, and artifact paths are not approved.
- Stop if capture requires secrets, private data, microphone permission, external service calls, or apply actions.
- Stop if screenshots would be treated as automatic approval.

What changed:

- Added this docs-only optional visual capture plan to the v0.2 plan.

What did not change:

- No Playwright command was run.
- No screenshot was captured.
- No baseline was created.
- No package was installed.
- No browser binary was installed.
- No test changed.
- No artifact changed.
- No implementation, commit, push, deletion, route creation, or apply was performed.

Commands run:

```bash
cd /home/source/SpiritOS
printf '\n== PHASE 4.3 OPTIONAL VISUAL CAPTURE PLAN CHECK ==\n'
printf '\n== STATUS ==\n'
git status -sb
printf '\n== PLAYWRIGHT READINESS PROBE ==\n'
if ls playwright.config.* >/dev/null 2>&1 && node -e "require.resolve('@playwright/test/package.json')" >/dev/null 2>&1; then
  echo "Playwright config and local @playwright/test found. Capture could be listed in a future approved increment."
elif ls playwright.config.* >/dev/null 2>&1; then
  echo "Playwright config found, but @playwright/test is not installed locally. Skipping Playwright check for this increment."
else
  echo "Playwright config not found, skipping Playwright check for this increment."
fi
printf '\n== EXISTING VISUAL DOC REFERENCES ==\n'
grep -n "capture\|screenshot\|baseline\|viewport\|artifact\|visual diff\|Playwright" docs/design-visual-verification-v0.1.md docs/design-system-overhaul-master-v0.2.md 2>/dev/null | sed -n '1,260p'
printf '\n== VISUAL CAPTURE CLOSEOUT CHECK ==\n'
grep -n "Phase 4.3 Optional Visual Capture Plan Closeout\|Capture readiness decision\|Optional capture gate\|Future capture packet shape\|Phase 4.4: Add visual diff report plan" docs/design-system-overhaul-master-v0.2.md
printf '\n== EM DASH CHECK ==\n'
LC_ALL=C grep -n "$(printf '\342\200\224')" docs/design-system-overhaul-master-v0.2.md docs/plan-index.md 2>/dev/null || true
printf '\n== DIFF CHECK ==\n'
git --no-pager diff --check -- docs/design-system-overhaul-master-v0.2.md docs/plan-index.md
```

Expected output:

- The Playwright readiness probe skips safely when local `@playwright/test` is not installed.
- Existing visual verification docs and v0.2 capture references are visible.
- The v0.2 plan contains the Phase 4.3 optional visual capture plan closeout.
- The closeout states that capture is disabled by default and requires approval.
- Em dash check prints no matches.
- Diff check prints no whitespace errors.

Actual output:

- The Playwright readiness probe skipped safely because `playwright.config.mjs` exists but local `@playwright/test` was not installed.
- Existing visual verification docs and v0.2 capture references were visible.
- The v0.2 plan contains the Phase 4.3 optional visual capture plan closeout, capture readiness decision, optional capture gate, future capture packet shape, and the Phase 4.4 next increment title.
- The closeout states that capture is disabled by default and requires approval.
- Em dash check printed no matches for the written docs.
- Diff check printed no whitespace errors.

Dirty files:

- Intentional docs touched by this design-system lane: `docs/design-system-overhaul-master-v0.2.md`, `docs/plan-index.md`.
- Unrelated modified files were present in Scout, Source Proxy, coding cockpit, dashboard, and `src/lib/scout-human-readable.ts`; they were not touched by this increment.
- Unrelated untracked Cartographer and Scout docs were present; they were not touched by this increment.

Next increment title:

Phase 4.4: Add visual diff report plan

## Phase 4.4 Visual Diff Report Plan Closeout

Status: complete

Date: 2026-05-20

Scope:

This increment defines the shape of a future visual diff report. It does not run screenshot comparison, create thresholds in code, create baselines, update Design Vault artifacts, modify Source Proxy, or add tests.

Report decision:

Visual diff reports should be advisory evidence only. They can summarize baseline, candidate, viewport, threshold, status, deltas, and reviewer notes, but they cannot approve, apply, reject, commit, push, or promote design changes automatically.

Existing evidence:

| Evidence | Current state | Use in v0.2 |
| --- | --- | --- |
| `docs/design-visual-verification-v0.1.md` | Defines match reports, threshold policy, screenshot conventions, and safe Playwright detection. | Source document for report shape. |
| `docs/design-pack-authoring-v0.1.md` | Defines design packs as bundles with screenshots, generated outputs, and match reports. | Confirms reports are evidence, not authority. |
| `docs/source-proxy-design-apply-lane-v0.1.md` | Lists screenshots and match report evidence for future Source Proxy proposals. | Confirms Source Proxy can attach report evidence later. |
| `data/design-vault/packs/internal-dashboard-demo-v4/match-report.json` | Existing Design Vault match-report artifact. | Treat as reference evidence, not as a canonical schema yet. |

Visual diff report schema:

| Field | Required | Purpose |
| --- | --- | --- |
| `report_id` | Yes | Unique report id. |
| `pack_id` | Yes | Design pack or proposal id the report belongs to. |
| `source_card_ids` | Yes | Approved source cards connected to the report. |
| `target_route` | Yes | Route or surface captured. |
| `target_state` | Yes | UI state represented by the candidate screenshot. |
| `viewport` | Yes | Width, height, device scale factor, and browser project. |
| `theme` | Yes | Theme or palette state used during capture. |
| `baseline_path` | Optional | Approved reference screenshot path. |
| `candidate_path` | Optional | Generated or implementation screenshot path. |
| `threshold_policy` | Yes | Informational threshold label and reviewer expectation. |
| `delta_summary` | Yes | Human-readable summary of meaningful visual differences. |
| `known_deltas` | Optional | Expected or accepted differences. |
| `unexpected_deltas` | Optional | Differences needing review. |
| `status` | Yes | `not_run`, `needs_review`, `accepted`, `rejected`, or `superseded`. |
| `reviewer_notes` | Optional | Human review notes and rationale. |
| `source_proxy_task_id` | Optional | Source Proxy proposal or task id if attached to an apply lane. |
| `created_at` | Yes | Timestamp for the report. |

Status rules:

| Status | Meaning | Authority |
| --- | --- | --- |
| `not_run` | Report shape exists, but no comparison ran. | Evidence only. |
| `needs_review` | A report exists and needs human review. | Evidence only. |
| `accepted` | Human reviewer accepted the visual evidence. | Still does not apply changes. |
| `rejected` | Human reviewer rejected the visual evidence. | Blocks recommendation, not source control by itself. |
| `superseded` | A newer report replaces this one. | Historical evidence only. |

Threshold policy:

- Thresholds are informational at v0.2.
- Thresholds must not approve or reject changes automatically.
- Threshold labels should describe review strictness, such as `informational`, `strict-review`, or `manual-only`.
- Any future numeric threshold must list route, viewport, state, browser project, baseline path, and known unstable regions.
- A threshold cannot override Source Proxy approval or human review.

Attachment rules:

- Design Vault can store visual diff reports as approved evidence after human review.
- Design Packs can include visual diff reports as proposal evidence.
- Visual Verifier can produce report drafts only.
- Source Proxy can attach visual diff reports to bounded design proposals.
- Cartographer can document report existence and state after approval.
- No design agent can apply changes based on a visual diff report.

Stop rules:

- Stop if thresholds are treated as automatic approval.
- Stop if a report requires screenshot comparison implementation in this increment.
- Stop if report output would overwrite Design Vault artifacts without approval.
- Stop if a report hides baseline, candidate, viewport, state, or known deltas.
- Stop if a report can trigger Source Proxy apply without explicit human approval.

What changed:

- Added this docs-only visual diff report plan to the v0.2 plan.

What did not change:

- No screenshot comparison was run.
- No baseline file was created.
- No Design Vault artifact changed.
- No Source Proxy code changed.
- No test changed.
- No package was installed.
- No implementation, commit, push, deletion, route creation, or apply was performed.

Commands run:

```bash
cd /home/source/SpiritOS
printf '\n== PHASE 4.4 VISUAL DIFF REPORT PLAN CHECK ==\n'
printf '\n== STATUS ==\n'
git status -sb
printf '\n== VISUAL DIFF SOURCE DOC REFERENCES ==\n'
grep -n "visual diff\|baseline\|candidate\|threshold\|delta summary\|match report\|reviewer notes\|known deltas" docs/design-visual-verification-v0.1.md docs/source-proxy-design-apply-lane-v0.1.md docs/design-pack-authoring-v0.1.md docs/design-system-overhaul-master-v0.2.md 2>/dev/null | sed -n '1,260p'
printf '\n== DESIGN VAULT MATCH REPORT CHECK ==\n'
find data/design-vault -maxdepth 5 -type f 2>/dev/null | sort | grep -Ei 'match-report|tokens|README|source-card|theme|components-map' | sed -n '1,180p'
printf '\n== VISUAL DIFF CLOSEOUT CHECK ==\n'
grep -n "Phase 4.4 Visual Diff Report Plan Closeout\|Visual diff report schema\|Status rules\|Threshold policy\|Phase 4.5: Define mobile viewport checks" docs/design-system-overhaul-master-v0.2.md
printf '\n== EM DASH CHECK ==\n'
LC_ALL=C grep -n "$(printf '\342\200\224')" docs/design-system-overhaul-master-v0.2.md docs/plan-index.md 2>/dev/null || true
printf '\n== DIFF CHECK ==\n'
git --no-pager diff --check -- docs/design-system-overhaul-master-v0.2.md docs/plan-index.md
```

Expected output:

- Visual diff source docs and references are visible.
- Design Vault match-report-related files are listed.
- The v0.2 plan contains the Phase 4.4 visual diff report closeout.
- The closeout defines schema, status rules, threshold policy, and attachment rules.
- Em dash check prints no matches.
- Diff check prints no whitespace errors.

Actual output:

- Visual diff source docs and references were visible.
- Design Vault match-report-related files were listed, including the internal dashboard demo match report.
- The v0.2 plan contains the Phase 4.4 visual diff report closeout, visual diff report schema, status rules, threshold policy, attachment rules, and the Phase 4.5 next increment title.
- The closeout defines schema, status rules, threshold policy, and attachment rules.
- Em dash check printed no matches for the written docs.
- Diff check printed no whitespace errors.

Dirty files:

- Intentional docs touched by this design-system lane: `docs/design-system-overhaul-master-v0.2.md`, `docs/plan-index.md`.
- Unrelated modified files were present in Scout, Source Proxy, coding cockpit, dashboard, and `src/lib/scout-human-readable.ts`; they were not touched by this increment.
- Unrelated untracked Cartographer and Scout docs were present; they were not touched by this increment.

Next increment title:

Phase 4.5: Define mobile viewport checks

## Phase 4.5 Mobile Viewport Checks Closeout

Status: complete

Date: 2026-05-20

Scope:

This increment defines future mobile viewport checks for visual verification. It does not run Playwright, open a browser, capture screenshots, edit mobile UI, edit CSS, add tests, or install dependencies.

Mobile readiness decision:

Mobile checks should be mandatory for future design-system UI work, but they should remain docs-only until capture tooling and artifact paths are approved. The current repo already has mobile evidence in Playwright project names and live UI code, especially chat drawers, sheets, composer docks, touch controls, safe-area padding, and visual viewport handling.

Existing mobile evidence:

| Evidence | Current state | Use in v0.2 |
| --- | --- | --- |
| `playwright.config.mjs` | Defines `Mobile Safari`, `Pixel 5`, and `iPad` projects. | Use these names as future viewport references. |
| `MobileSheet.tsx` | Handles mobile overlays, scroll lock, safe-area padding, and touch controls. | Reference for drawer and sheet checks. |
| `MobileThreadDrawer.tsx` | Provides mobile thread drawer behavior. | Reference for drawer open, close, scroll, and drag checks. |
| `SpiritChat.tsx` | Contains mobile composer, drawer, safe-area, keyboard, and overflow behavior. | Primary mobile chat target. |
| `SpiritWorkspaceShell` tests | Existing visual viewport and scroll-policy tests exist. | Evidence for mobile viewport risk coverage. |
| Oracle controls and transcript | Voice surface has compact controls, transcript overflow, and visualizer states. | Include in future mobile checks. |
| Coding cockpit | Source Proxy review surface needs small-screen approval review. | Include before any mobile apply-lane polish. |

Mobile viewport check matrix:

| Viewport | Surface | Checks |
| --- | --- | --- |
| Mobile Safari | Chat workspace | Thread drawer, composer dock, message actions sheet, safe-area padding, keyboard scroll, readable messages. |
| Mobile Safari | Dashboard | Rail or mobile chrome, card stacking, status badges, widget overflow, touch targets. |
| Mobile Safari | Coding cockpit | Task composer, diff preview, approval gate, sticky summary, apply lock, no clipped controls. |
| Mobile Safari | Oracle | Voice controls, transcript scroll, visualizer, status card, fallback input, secure-context warning. |
| Pixel 5 | Chat workspace | Narrow-width labels, drawer width, action sheet horizontal overflow, composer chip wrapping. |
| Pixel 5 | Dashboard | Card density, long metric values, status badge wrapping, scroll containment. |
| Pixel 5 | Coding cockpit | Diff line wrapping, approval checklist, expected checks block, blocked state text. |
| iPad | Dashboard and chat | Split-pane behavior, rail persistence, drawer threshold, readable density. |
| iPad | Coding and Oracle | Review panels, stage surfaces, visualizer sizing, transcript and diff overflow. |

Required mobile checks:

| Check | Requirement |
| --- | --- |
| Overflow | No horizontal page overflow unless an intentional scroll region is present. |
| Touch target | Primary actions, close buttons, drawer triggers, composer controls, and approval buttons must meet mobile hit-area expectations. |
| Safe area | Fixed and sticky controls must respect bottom and top safe areas. |
| Keyboard | Composer and input surfaces must remain usable when the mobile keyboard is open. |
| Drawer or sheet | Overlays must lock background scroll, allow internal scroll, close predictably, and return focus where possible. |
| Text fit | Labels, badges, long values, and button text must not clip or overlap. |
| Fixed bars | Top bars, taskbars, composer docks, and sticky approval bars must not collide with content. |
| Motion | Motion-heavy surfaces must preserve state in reduced-motion mode. |
| Evidence | Each mobile check must report route, viewport, state, expected output, actual output, and known limits. |

Future manual mobile check block shape:

```bash
cd /home/source/SpiritOS
printf '\n== MOBILE VIEWPORT CHECK READINESS ==\n'
printf '\n== PLAYWRIGHT PROJECTS ==\n'
grep -n "Mobile Safari\|Pixel 5\|iPad" playwright.config.mjs 2>/dev/null || true
printf '\n== MOBILE SOURCE REFERENCES ==\n'
grep -RIn "safe-area\|drawer\|sheet\|touch-manipulation\|visual-viewport\|composer\|keyboard\|overflow" src/components src/styles src/app 2>/dev/null | sed -n '1,180p'
```

Stop rules:

- Stop if mobile checks require installing Playwright or browser binaries.
- Stop if checks depend on live microphone access, external model calls, secrets, or Source Proxy apply.
- Stop if only desktop screenshots are available for a design-system change.
- Stop if mobile text clips, controls overlap, or safe-area collisions are unresolved.
- Stop if mobile verification would become automatic approval.

What changed:

- Added this docs-only mobile viewport check plan to the v0.2 plan.

What did not change:

- No Playwright command was run.
- No screenshot was captured.
- No browser was opened.
- No package was installed.
- No component changed.
- No CSS changed.
- No test changed.
- No implementation, commit, push, deletion, route creation, or apply was performed.

Commands run:

```bash
cd /home/source/SpiritOS
printf '\n== PHASE 4.5 MOBILE VIEWPORT CHECK PLAN ==\n'
printf '\n== STATUS ==\n'
git status -sb
printf '\n== PLAYWRIGHT MOBILE PROJECTS ==\n'
sed -n '1,220p' playwright.config.mjs 2>/dev/null || true
printf '\n== MOBILE / VIEWPORT SOURCE REFERENCES ==\n'
grep -RIn "Mobile Safari\|Pixel\|iPad\|viewport\|visual-viewport\|safe-area\|drawer\|sheet\|touch target\|touch\|overflow\|keyboard\|composer\|sticky\|fixed" src/components src/styles src/app docs/design-system-overhaul-master-v0.2.md 2>/dev/null | sed -n '1,260p'
printf '\n== MOBILE VIEWPORT CLOSEOUT CHECK ==\n'
grep -n "Phase 4.5 Mobile Viewport Checks Closeout\|Mobile viewport check matrix\|Required mobile checks\|Future manual mobile check block shape\|Phase 4.6: Define accessibility smoke checks" docs/design-system-overhaul-master-v0.2.md
printf '\n== EM DASH CHECK ==\n'
LC_ALL=C grep -n "$(printf '\342\200\224')" docs/design-system-overhaul-master-v0.2.md docs/plan-index.md 2>/dev/null || true
printf '\n== DIFF CHECK ==\n'
git --no-pager diff --check -- docs/design-system-overhaul-master-v0.2.md docs/plan-index.md
```

Expected output:

- Playwright mobile projects are visible when config exists.
- Mobile and viewport source references are visible across chat, dashboard, coding, Oracle, style, and route files.
- The v0.2 plan contains the Phase 4.5 mobile viewport check closeout.
- The closeout defines mobile viewport matrix, required checks, and future manual check block shape.
- Em dash check prints no matches.
- Diff check prints no whitespace errors.

Actual output:

- Playwright mobile projects were visible in `playwright.config.mjs`, including `Mobile Safari`, `Pixel 5`, and `iPad`.
- Mobile and viewport source references were visible across chat, dashboard, coding, Oracle, style, and route files.
- Source references showed mobile drawers, sheets, safe-area padding, composer docks, touch controls, overflow handling, visual viewport behavior, and mobile tests.
- The v0.2 plan contains the Phase 4.5 mobile viewport check closeout, mobile viewport matrix, required mobile checks, future manual check block shape, and the Phase 4.6 next increment title.
- Em dash check printed no matches for the written docs.
- Diff check printed no whitespace errors.

Dirty files:

- Intentional docs touched by this design-system lane: `docs/design-system-overhaul-master-v0.2.md`, `docs/plan-index.md`.
- Unrelated modified files were present in Scout, Source Proxy, coding cockpit, dashboard, and `src/lib/scout-human-readable.ts`; they were not touched by this increment.
- Unrelated untracked Cartographer and Scout docs were present; they were not touched by this increment.

Next increment title:

Phase 4.6: Define accessibility smoke checks

## Phase 4.6 Accessibility Smoke Checks Closeout

Status: complete

Date: 2026-05-20

Scope:

This increment defines future accessibility smoke checks for design-system visual verification. It does not install axe, add tests, run browsers, edit components, change CSS, or implement automated accessibility tooling.

Accessibility decision:

Accessibility checks should be required evidence for future design-system implementation, but v0.2 should keep them manual and docs-first until tooling and allowed files are approved. The first smoke layer should check keyboard order, focus visibility, reduced motion, contrast intent, labels, roles, disabled states, touch targets, and non-color state cues.

Current evidence:

| Evidence | Current state | Use in v0.2 |
| --- | --- | --- |
| Design docs | Existing docs reference accessibility, contrast, focus visibility, reduced motion, and touch targets. | Use as policy source. |
| Source components | Source scan shows `aria-*`, `role`, `sr-only`, disabled states, touch classes, and focus-related behavior. | Use as implementation evidence, not as proof of complete coverage. |
| Oracle visuals | Oracle visual state and reduced-motion related tests exist. | Include motion and nonvisual status checks. |
| Chat mobile controls | Chat surfaces include drawers, sheets, touch controls, composer, and labels. | Include keyboard, focus, label, and touch checks. |
| Coding cockpit | Source Proxy review surface includes approval and apply states. | Include disabled, blocked, approval, and verification state checks. |
| Tooling | No axe install was performed in this increment. | Keep axe optional until approved later. |

Accessibility smoke check matrix:

| Check | Requirement | Evidence to collect later |
| --- | --- | --- |
| Keyboard order | Main navigation, drawers, dialogs, composer, approval gates, and action menus must be reachable in a logical order. | Manual notes or future browser trace. |
| Focus visibility | Interactive controls must show visible focus on dark, glass, and accent surfaces. | Screenshot or manual observation. |
| Labels and names | Icon buttons, menu triggers, sheets, drawers, voice controls, and approval actions need accessible names. | Source scan plus manual check. |
| Roles and landmarks | Major surfaces should use meaningful landmarks, headings, buttons, dialogs, status regions, and alerts where appropriate. | Source scan plus manual check. |
| Reduced motion | Motion-heavy surfaces must preserve status without relying on animation. | CSS or component evidence plus manual check. |
| Contrast intent | Text, badges, borders, focus rings, disabled text, and danger states need documented contrast expectations. | Token notes and manual review. |
| State visibility | Ready, blocked, error, warning, approved, applied, listening, speaking, and loading states must not rely on color alone. | Component review evidence. |
| Touch targets | Primary mobile controls must meet mobile hit-area expectations. | Mobile viewport evidence. |
| Text scaling | Long labels, code, diffs, badges, and buttons must wrap or scroll without overlap. | Mobile and desktop notes. |

Manual accessibility smoke block shape:

```bash
cd /home/source/SpiritOS
printf '\n== ACCESSIBILITY SMOKE SOURCE CHECK ==\n'
printf '\n== TOOLING REFERENCES ==\n'
grep -n "axe\|accessibility\|a11y\|aria\|contrast\|focus\|reduced motion\|touch target" package.json docs/*.md 2>/dev/null | sed -n '1,180p' || true
printf '\n== SOURCE ACCESSIBILITY SAMPLE ==\n'
grep -RIn "aria-\|role=\|sr-only\|focus-visible\|prefers-reduced-motion\|tabIndex\|disabled\|aria-disabled\|aria-label" src/components src/styles src/app 2>/dev/null | sed -n '1,220p'
```

Optional future axe boundary:

- Axe can be considered only in a later approved tooling increment.
- Do not add axe packages in this planning lane.
- Do not treat axe output as automatic approval.
- Axe findings must be attached as evidence with route, viewport, state, command, expected output, actual output, and reviewer notes.
- Manual review remains required for semantics, state clarity, visual focus, and workflow safety.

Stop rules:

- Stop if accessibility checks require package installation.
- Stop if a check needs browser automation before tooling is approved.
- Stop if visual or design agents can approve changes based on accessibility output.
- Stop if color-only state, hidden focus, unlabeled controls, or unsafe disabled-state ambiguity is found and unresolved.
- Stop if accessibility evidence is not tied to route, viewport, state, and reviewer notes.

What changed:

- Added this docs-only accessibility smoke check plan to the v0.2 plan.

What did not change:

- No axe package was installed.
- No browser was run.
- No test changed.
- No component changed.
- No CSS changed.
- No screenshot was captured.
- No implementation, commit, push, deletion, route creation, or apply was performed.

Commands run:

```bash
cd /home/source/SpiritOS
printf '\n== PHASE 4.6 ACCESSIBILITY SMOKE CHECK PLAN ==\n'
printf '\n== STATUS ==\n'
git status -sb
printf '\n== ACCESSIBILITY TOOLING REFERENCES ==\n'
grep -n "axe\|accessibility\|a11y\|aria\|role\|contrast\|focus\|reduced motion\|touch target" package.json playwright.config.mjs vitest.config.mjs docs/*.md 2>/dev/null | sed -n '1,260p' || true
printf '\n== ACCESSIBILITY SOURCE SAMPLE ==\n'
grep -RIn "aria-\|role=\|sr-only\|focus-visible\|prefers-reduced-motion\|reduced-motion\|tabIndex\|disabled\|aria-disabled\|aria-label\|touch-manipulation" src/components src/styles src/app 2>/dev/null | sed -n '1,260p'
printf '\n== ACCESSIBILITY CLOSEOUT CHECK ==\n'
grep -n "Phase 4.6 Accessibility Smoke Checks Closeout\|Accessibility smoke check matrix\|Manual accessibility smoke block shape\|Optional future axe boundary\|Phase 5.1: Define Design Source Card schema" docs/design-system-overhaul-master-v0.2.md
printf '\n== EM DASH CHECK ==\n'
LC_ALL=C grep -n "$(printf '\342\200\224')" docs/design-system-overhaul-master-v0.2.md docs/plan-index.md 2>/dev/null || true
printf '\n== DIFF CHECK ==\n'
git --no-pager diff --check -- docs/design-system-overhaul-master-v0.2.md docs/plan-index.md
```

Expected output:

- Accessibility tooling and doc references are visible where present.
- Source accessibility samples show labels, roles, sr-only text, focus, disabled states, reduced-motion references, and touch controls.
- The v0.2 plan contains the Phase 4.6 accessibility smoke checks closeout.
- The closeout defines smoke check matrix, manual check block shape, and optional future axe boundary.
- Em dash check prints no matches.
- Diff check prints no whitespace errors.

Actual output:

- Accessibility tooling and doc references were visible where present.
- Source accessibility samples showed labels, roles, sr-only text, focus-visible styling, disabled states, reduced-motion references, and touch controls.
- The v0.2 plan contains the Phase 4.6 accessibility smoke checks closeout, accessibility smoke check matrix, manual accessibility smoke block shape, optional future axe boundary, and the Phase 5.1 next increment title.
- The closeout defines smoke check matrix, manual check block shape, and optional future axe boundary.
- Em dash check printed no matches for the written docs.
- Diff check printed no whitespace errors.

Dirty files:

- Intentional docs touched by this design-system lane: `docs/design-system-overhaul-master-v0.2.md`, `docs/plan-index.md`.
- Unrelated modified files were present in Scout, Source Proxy, coding cockpit, dashboard, and `src/lib/scout-human-readable.ts`; they were not touched by this increment.
- Unrelated untracked Cartographer and Scout docs were present; they were not touched by this increment.

Next increment title:

Phase 5.1: Define Design Source Card schema

## Phase 5.1 Design Source Card Schema Closeout

Status: complete

Date: 2026-05-20

Scope:

This increment defines the v0.2 Design Source Card schema contract for future Design Vault work. It does not edit Design Vault JSON, source-card templates, source-card registry files, pack artifacts, Scout runtime, Reverse Designer runtime, Source Proxy, app routes, or components.

Current source card evidence:

| Evidence | Current state | v0.2 use |
| --- | --- | --- |
| `data/design-vault/source-cards/source-card.template.json` | Existing v0.1 source-card template. | Base schema evidence. |
| `data/design-vault/source-cards/internal-dashboard-demo-v4.json` | Approved internal source card. | Example approved source card. |
| `data/design-vault/source-cards/index.json` | Source-card registry exists. | Registry evidence, not runtime authority. |
| `data/design-vault/source-cards/approval-checklist.md` | Human approval checklist exists. | Approval evidence. |
| `docs/reverse-designer-approved-inputs-v0.1.md` | Requires approved source cards before analysis. | Reverse Designer boundary. |
| `docs/scout-design-intake-bridge-v0.1.md` | Keeps Scout candidate-only and manual-gated. | Scout boundary. |
| `docs/design-pack-authoring-v0.1.md` | Treats source-card metadata as pack evidence. | Design Pack boundary. |

v0.2 Design Source Card schema fields:

| Field | Required | Purpose |
| --- | --- | --- |
| `version` | Yes | Schema version. |
| `id` | Yes | Stable source-card id. |
| `title` | Yes | Human-readable title. |
| `source_type` | Yes | Source class such as `internal-demo`, `owned-reference`, `licensed-reference`, `client-approved-reference`, `open-source-reference`, `public-inspiration`, or `rejected`. |
| `source_uri` | Conditional | Approved URL or source reference, if any. |
| `local_path` | Conditional | Local repo path, if any. |
| `related_paths` | Optional | Local supporting files. |
| `owner` | Yes | Owner or rights holder. |
| `rights_basis` | Yes | Category, license, approval reference, and notes. |
| `approval` | Yes | Status, approved use mode, reviewer, reviewed date, and approval notes. |
| `permitted_use_modes` | Yes | Allowed use modes for this source. |
| `disallowed_assets` | Yes | Assets that must not be copied or analyzed. |
| `capture` | Yes | Screenshots, notes, token files, and future evidence links. |
| `safety` | Yes | Manual intake, human approval, crawler, coding context, and app UI write flags. |
| `risk_flags` | Recommended | Unclear rights, protected assets, brand likeness, privacy, accessibility, or crawler risk. |
| `history` | Recommended | Created, reviewed, superseded, and retired metadata. |

State model:

| State | Meaning | Can advance to |
| --- | --- | --- |
| `candidate` | Suggested intake candidate with no vault authority. | `draft`, `rejected` |
| `draft` | Human-created or human-promoted card under review. | `approved`, `rejected` |
| `approved` | Human-approved source card with reviewed date and reviewer. | `superseded`, `retired` |
| `rejected` | Source must not be used by design agents. | `draft` only with new evidence and human review |
| `superseded` | Replaced by a newer card. | `retired` |
| `retired` | No longer active. | None |

Allowed transitions:

- `candidate` to `draft` requires explicit human promotion.
- `draft` to `approved` requires reviewer, reviewed date, rights basis, approved use mode, and safety flags.
- `draft` to `rejected` is allowed when rights, quality, originality, privacy, or safety checks fail.
- `approved` to `superseded` requires a replacement reference.
- `approved` to `retired` requires a retirement note.
- `rejected` to `draft` requires new evidence and human review.
- No design system process may auto-promote a candidate or draft to `approved`.

Approval rules:

- No approved card is valid without `approval.reviewer` and `approval.reviewed_date`.
- `approval.approved_use_mode` must be listed in `permitted_use_modes`.
- Exact-use modes require owned, licensed, client-approved, or open-source permission.
- `inspired-language-only` permits analysis of broad design language only and must not permit copying layout, assets, brand identity, or distinctive trade dress.
- `rejected`, `retired`, and `superseded` cards are not active inputs for Reverse Designer, Design Blender, or Design Coding Agent work unless a human explicitly reopens them as `draft`.
- `safety.manual_intake_only` and `safety.human_approved` must remain true for approved cards.
- `safety.auto_promote_to_coding_context` and `safety.app_ui_write_allowed` must remain false unless a later Source Proxy design apply lane explicitly defines a stricter gated mechanism.

Reverse Designer and Scout boundaries:

- Scout may suggest candidate sources only.
- Scout must not create approved source cards.
- Scout must not promote candidate cards into the Design Vault without human review.
- Reverse Designer may read approved source cards only.
- Reverse Designer outputs notes, tokens, maps, and risks only.
- Design Blender may use approved source cards or approved design packs only.
- Source Proxy may attach source-card evidence to a bounded proposal, but a source card never grants apply authority.

Stop rules:

- Stop if the source card references unclear rights, protected assets, copied brand identity, private data, or unknown crawl permission.
- Stop if the card has no reviewer or reviewed date.
- Stop if exact-use permissions are implied but not recorded.
- Stop if a candidate source is being treated as approved evidence.
- Stop if any agent attempts to write app UI, commit, push, delete, or create routes from a source card.

What changed:

- Added the Phase 5.1 closeout to this master plan.
- Defined the v0.2 Design Source Card schema contract.
- Defined source-card state transitions and approval rules.
- Reaffirmed Scout, Reverse Designer, Design Blender, Design Coding Agent, and Source Proxy boundaries.

What did not change:

- No Design Vault JSON was changed.
- No source-card templates or registries were changed.
- No source-card artifacts were created.
- No app routes, UI components, tests, Scout runtime, Reverse Designer runtime, or Source Proxy runtime were changed.

Commands run:

```bash
cd /home/source/SpiritOS
printf '\n== PHASE 5.1 DESIGN SOURCE CARD SCHEMA CHECK ==\n'
printf '\n== STATUS ==\n'
git status -sb
printf '\n== DESIGN VAULT SOURCE CARD FILES ==\n'
find data/design-vault docs -maxdepth 4 -type f 2>/dev/null | sort | grep -Ei 'source-card|design-vault|design-pack|reverse-designer|scout-design|approved-inputs' | sed -n '1,220p'
printf '\n== SOURCE CARD TEMPLATE SAMPLE ==\n'
sed -n '1,240p' data/design-vault/source-cards/source-card.template.json 2>/dev/null || true
printf '\n== APPROVED SOURCE CARD SAMPLE ==\n'
sed -n '1,240p' data/design-vault/source-cards/internal-dashboard-demo-v4.json 2>/dev/null || true
printf '\n== SOURCE CARD CLOSEOUT CHECK ==\n'
grep -n "Phase 5.1 Design Source Card Schema Closeout\|v0.2 Design Source Card schema fields\|State model\|Approval rules\|Phase 5.2: Define Design Token Pack schema" docs/design-system-overhaul-master-v0.2.md
printf '\n== EM DASH CHECK ==\n'
LC_ALL=C grep -n "$(printf '\342\200\224')" docs/design-system-overhaul-master-v0.2.md docs/plan-index.md 2>/dev/null || true
printf '\n== DIFF CHECK ==\n'
git --no-pager diff --check -- docs/design-system-overhaul-master-v0.2.md docs/plan-index.md
```

Expected output:

- Source-card template and approved internal source card are readable.
- Closeout sections are found.
- Em dash check prints no matches.
- Diff check prints no whitespace errors.

Actual output:

- Design Vault source-card files were found, including the template, approved internal source card, index, approval checklist, token model, pack files, and relevant docs.
- The source-card template was readable and showed rights basis, approval, permitted use modes, disallowed assets, capture, and safety fields.
- The approved internal source card was readable and showed approved status, reviewer, reviewed date, related paths, capture notes, token files, and safety flags.
- The v0.2 plan contains the Phase 5.1 closeout, schema fields, state model, approval rules, and Phase 5.2 next increment title.
- Em dash check printed no matches for the written docs.
- Diff check printed no whitespace errors.

Dirty files:

- Intentional docs touched by this design-system lane: `docs/design-system-overhaul-master-v0.2.md`, `docs/plan-index.md`.
- Unrelated modified files were present in Scout, Source Proxy, coding cockpit, dashboard, and `src/lib/scout-human-readable.ts`; they were not touched by this increment.
- Unrelated untracked Cartographer and Scout docs were present; they were not touched by this increment.

Next increment title:

Phase 5.2: Define Design Token Pack schema

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
