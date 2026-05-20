# SpiritOS Design Systems Master Plan v0.1

Status: manual-first, planning complete, Phase 2.1 manual intake docs complete, runtime implementation not started

Status date: 2026-05-19

## Executive Summary

SpiritOS should build this as a Design Intelligence Stack, not as one mega-agent. The first version is Design Scout Lite plus Design Vault v0.1: a manual-fed, approval-gated store for design references, source cards, notes, screenshots, token files, and generated design packs.

The system should start from owned and internal references. The first extraction target should be the existing `src/components/dashboard/demo-v4/` demo and `src/styles/dashboard-demo-v4.css`, with `src/styles/spirit-demo.tokens.css` and `src/theme/spiritPalettes.ts` as related token and palette references. Public websites, random inspiration links, and later Scout discoveries should not enter coding context automatically.

The v0.1 goal is to define the lanes, metadata, safety rules, and small implementation increments. It does not add crawler behavior, autonomous discovery, app UI writes, Scout runtime behavior, Source Proxy behavior, or Cartographer authority. After approval, Phase 1.1 added only the local Design Vault documentation and empty registry scaffold. Phase 2.1 added only the manual source-card template and approval checklist.

## Current Repo Fit

Observed repo structure:

- Docs registry exists at `docs/plan-index.md`.
- Scout docs exist under `scout/docs/`, including `scout/docs/V0_4_SCOUT_POLISH_CLOSEOUT.md`.
- Cartographer and Blueprinter docs exist under `docs/` and `_blueprints/`, including `docs/cartographer-level-1-autonomy-plan.md`, `docs/cartographer-level-2-autonomy-plan.md`, `_blueprints/components/cartographer_agent.md`, and `_blueprints/_schema/blueprint-frontmatter.schema.md`.
- Source Proxy planning and runbooks exist under `docs/`, including `docs/source-proxy-production-hardening-plan.md`, `docs/source-proxy-daily-use-runbook.md`, and `docs/source-proxy-regression-matrix.md`.
- Dashboard demo v4 exists at `src/components/dashboard/demo-v4/` with styling at `src/styles/dashboard-demo-v4.css`.
- Token and palette references exist at `src/styles/spirit-demo.tokens.css`, `src/styles/spirit-demo.components.css`, `src/styles/spirit-demo.layout.css`, `src/styles/spirit-demo.animations.css`, `src/styles/spirit-demo.effects.css`, and `src/theme/spiritPalettes.ts`.
- Playwright config exists at `playwright.config.mjs`, with e2e tests under `tests/e2e/`.
- No Storybook setup was found in the inspected top-level paths. Storybook remains a proposed future preview option only.

Later connections:

- Scout should act as a reference intake and research lane only after manual gates are mature. In v0.1, Scout must not crawl or auto-promote design packets into coding context.
- Cartographer and Blueprinter should document, audit, and plan design intelligence work. They should not gain new write authority from this plan.
- Source Proxy and the coding approval gate should remain the only implementation lane for app changes. Design packs may become proposal evidence, not direct edits.
- Playwright should be used for visual capture and regression checks when a phase needs screenshots or comparison evidence. It must be detected before use and skipped cleanly when unavailable.
- Dashboard demo v4 should be the first safe extraction source because it is internal, already present, and isolated from the production UI.

## System Components

- Design Vault / Design Scout Lite: Manual-first local store for approved references, screenshots, extracted tokens, generated variants, notes, and match reports.
- Source Card Registry: Metadata for each source, including owner, license or approval basis, source type, approved use mode, date added, reviewer, and legal notes.
- Design Token Store: Structured tokens extracted from internal demos and approved references.
- Reverse Designer: Reads approved source cards, screenshots, and notes to infer design language, interaction patterns, and reusable tokens.
- Token Normalizer: Converts raw extracted values into stable primitive, semantic, component, motion, responsive, and accessibility tokens.
- Component Synthesizer: Produces reusable component guidance or prototypes from approved tokens and design language, but does not write app UI directly.
- Visual Verifier: Uses screenshots, Playwright captures, and comparison reports to check whether generated UI matches the approved target or intended style.
- Design Blender / Style Alchemist: Combines approved concepts into new original design directions without copying protected brand assets, copy, images, or logos.
- Design Pack Librarian: Catalogs packs, versions, provenance, status, and recommended use cases.
- Integration lane through Source Proxy approval: Converts approved design packs into bounded implementation proposals only after human approval.

## Safety And Legality Rules

- Exact replica mode is allowed only for owned, licensed, client-approved, or open-source permitted designs.
- Public websites and random references default to inspired design-language extraction, not copying.
- Do not copy logos, proprietary copy, brand assets, paid assets, protected images, or distinctive trade dress from unapproved sources.
- Do not add automated web crawling in v0.1.
- All external sources require source-card metadata and human approval before use.
- Scout must not auto-promote design packets into coding context.
- No writes to app UI without the Source Proxy approval gate.
- Screenshots and reference images must stay tied to source cards.
- Generated packs must record whether they are exact, inspired, blended, or internal-derived.
- If source rights are unclear, use the reference only for high-level notes or reject it.

## Proposed Design Pack Schema

The following path is proposed. The repo does not currently contain a better design-vault convention.

```text
data/design-vault/packs/<pack-id>/
  source-card.json
  tokens.json
  theme.css
  components-map.json
  reference/
  generated/
  match-report.json
  notes.md
```

Proposed file roles:

- `source-card.json`: provenance, approval status, usage mode, license notes, reviewer, and source type.
- `tokens.json`: normalized token payload.
- `theme.css`: optional generated CSS variables for preview or proposal evidence.
- `components-map.json`: mapping from source patterns to SpiritOS component concepts.
- `reference/`: approved screenshots, thumbnails, or internal capture artifacts.
- `generated/`: generated preview screenshots, variant captures, and design pack outputs.
- `match-report.json`: visual comparison summary and known deviations.
- `notes.md`: human review notes, design language summary, and constraints.

## Token Model

- Primitive tokens: raw colors, spacing, typography scales, radii, shadows, borders, opacity, blur, and z-index values.
- Semantic tokens: role-based aliases such as background, surface, text, accent, success, warning, danger, focus, disabled, and divider.
- Component tokens: component-specific variables for cards, navigation, buttons, badges, inputs, panels, charts, rails, dialogs, and shells.
- Motion tokens: durations, easing, stagger rules, hover transitions, entrance transitions, reduced-motion fallbacks, and animation intent.
- Responsive tokens: breakpoints, density modes, layout constraints, aspect ratios, minimum touch targets, and container behavior.
- Accessibility tokens: contrast expectations, focus indicators, reduced-motion behavior, hit areas, text scale limits, and state visibility.

## Phases And Increments

### Phase 0: Repo Audit And Safety Lock

#### Increment 0.1: Record Repo Fit And Safety Boundary

Goal: Capture the current repo fit and lock the manual-first boundary before any implementation starts.

Files likely touched:

- `docs/design-systems-master-v0.1.md`
- `docs/plan-index.md`

Exact actions:

- Inspect existing docs, Scout, Cartographer, Source Proxy, dashboard demo, token, theme, and Playwright structure.
- Record real paths only when observed.
- Mark uncreated design-vault paths as proposed.
- State that implementation has not started.
- Add the plan to the existing docs index.

Manual checks:

```bash
cd /home/source/SpiritOS
git status --short
test -f docs/design-systems-master-v0.1.md && echo "plan doc exists"
grep -n "SpiritOS Design Systems Master Plan v0.1" docs/design-systems-master-v0.1.md
grep -n "manual-first, planning complete, implementation not started" docs/design-systems-master-v0.1.md
grep -n "No writes to app UI without the Source Proxy approval gate" docs/design-systems-master-v0.1.md
grep -n "docs/design-systems-master-v0.1.md" docs/plan-index.md
git diff --check
```

Expected output:

- `git status` shows only the intended plan doc and plan index changes for this increment, apart from any unrelated pre-existing dirty files.
- The plan doc exists.
- Grep finds the title, status, safety rule, and index entry.
- `git diff --check` passes.

Next increment:
Phase 1.1: Create Design Vault schema docs and empty local registry scaffold

Rollback notes:

- Revert only `docs/design-systems-master-v0.1.md` and the plan-index entry.
- Do not modify Scout, Source Proxy, Cartographer, production UI, or demo code.

### Phase 1: Design Vault Schema

#### Increment 1.1: Create Design Vault Schema Docs And Empty Local Registry Scaffold

Goal: Define the local schema and create an empty approved-reference registry without adding runtime behavior.

Files likely touched:

- Proposed: `data/design-vault/README.md`
- Proposed: `data/design-vault/source-cards/index.json`
- Proposed: `data/design-vault/packs/.gitkeep`
- Proposed: `docs/design-systems-master-v0.1.md` only if the plan needs a status note

Exact actions:

- Create a Design Vault README that repeats the manual-first boundary.
- Add an empty registry file with no approved sources.
- Add empty folder placeholders only if needed by git.
- Do not add importers, crawlers, background jobs, or app routes.

Manual checks:

```bash
cd /home/source/SpiritOS
git status --short
test -f data/design-vault/README.md && echo "vault readme exists"
test -f data/design-vault/source-cards/index.json && echo "source card index exists"
grep -n "manual-first" data/design-vault/README.md
grep -n "crawler\\|crawl\\|autonomous" data/design-vault/README.md || true
git diff --check
```

Expected output:

- `git status` shows only Design Vault docs/scaffold files and any intended plan status note.
- The README and empty registry exist.
- Grep finds the manual-first boundary.
- Any crawler/autonomous references are prohibitions, not implementation.
- `git diff --check` passes.

Next increment:
Phase 2.1: Add manual source card template and approval checklist

Rollback notes:

- Remove only the proposed `data/design-vault/` scaffold files from this increment.
- No app behavior should need rollback because no runtime code is touched.

### Phase 2: Manual Intake Source Cards

#### Increment 2.1: Add Manual Source Card Template And Approval Checklist

Goal: Make every reference explicit, reviewable, and tied to an approved usage mode.

Files likely touched:

- Proposed: `data/design-vault/source-cards/source-card.template.json`
- Proposed: `data/design-vault/source-cards/approval-checklist.md`
- Proposed: `data/design-vault/README.md`

Exact actions:

- Define required source card fields: id, title, source type, source URI or local path, owner, license basis, approval status, approved use mode, reviewer, reviewed date, notes, and disallowed assets.
- Define use modes: internal-exact, licensed-exact, client-approved-exact, open-source-permitted, inspired-language-only, rejected.
- Add a checklist requiring human approval before extraction.
- Keep the registry empty unless a human supplies an approved source.

Manual checks:

```bash
cd /home/source/SpiritOS
git status --short
test -f data/design-vault/source-cards/source-card.template.json && echo "template exists"
test -f data/design-vault/source-cards/approval-checklist.md && echo "checklist exists"
grep -n "approved use mode\\|inspired-language-only\\|rejected" data/design-vault/source-cards/approval-checklist.md
grep -n "license" data/design-vault/source-cards/source-card.template.json
git diff --check
```

Expected output:

- `git status` shows only source-card template, checklist, and related docs changes.
- Grep finds approved use modes and license metadata.
- The registry remains empty unless a source was manually approved.
- `git diff --check` passes.

Next increment:
Phase 3.1: Extract dashboard demo v4 source card and token inventory manually

Rollback notes:

- Revert the template and checklist files.
- Do not remove any later approved source cards unless they were created in the same increment.

### Phase 3: Internal Demo Extraction, Starting With Dashboard Demo v4 If Present

#### Increment 3.1: Extract Dashboard Demo v4 Source Card And Token Inventory Manually

Goal: Create the first internal source card and a manual token inventory from the existing dashboard demo v4 files.

Files likely touched:

- Existing source references only: `src/components/dashboard/demo-v4/`
- Existing source references only: `src/styles/dashboard-demo-v4.css`
- Existing source references only: `src/styles/spirit-demo.tokens.css`
- Existing source references only: `src/theme/spiritPalettes.ts`
- Proposed: `data/design-vault/source-cards/internal-dashboard-demo-v4.json`
- Proposed: `data/design-vault/packs/internal-dashboard-demo-v4/notes.md`
- Proposed: `data/design-vault/packs/internal-dashboard-demo-v4/tokens.raw.json`

Exact actions:

- Confirm dashboard demo v4 exists.
- Create an internal source card marked owned/internal.
- Manually inventory token families from the demo CSS and palette files.
- Store raw token observations without normalizing them yet.
- Do not modify dashboard demo v4 or production UI.

Manual checks:

```bash
cd /home/source/SpiritOS
git status --short
test -d src/components/dashboard/demo-v4 && echo "dashboard demo v4 exists"
test -f src/styles/dashboard-demo-v4.css && echo "dashboard demo v4 css exists"
test -f data/design-vault/source-cards/internal-dashboard-demo-v4.json && echo "internal source card exists"
test -f data/design-vault/packs/internal-dashboard-demo-v4/tokens.raw.json && echo "raw token inventory exists"
grep -n "owned\\|internal" data/design-vault/source-cards/internal-dashboard-demo-v4.json
git diff -- src/components/dashboard/demo-v4 src/styles/dashboard-demo-v4.css src/styles/spirit-demo.tokens.css src/theme/spiritPalettes.ts
git diff --check
```

Expected output:

- Existing dashboard demo v4 files are present.
- The internal source card and raw token inventory exist.
- Grep confirms the source is owned/internal.
- `git diff` for existing demo, token, and theme files is empty.
- `git diff --check` passes.

Next increment:
Phase 4.1: Normalize raw internal tokens into token model v0.1

Rollback notes:

- Remove only the internal source card and generated design-vault pack files.
- Existing dashboard demo v4 files must remain unchanged.

### Phase 4: Token Normalizer

#### Increment 4.1: Normalize Raw Internal Tokens Into Token Model v0.1

Goal: Convert raw internal observations into a stable token model that can support previews and later synthesis.

Files likely touched:

- Proposed: `data/design-vault/packs/internal-dashboard-demo-v4/tokens.json`
- Proposed: `data/design-vault/packs/internal-dashboard-demo-v4/theme.css`
- Proposed: `data/design-vault/token-model-v0.1.md`

Exact actions:

- Map raw values into primitive, semantic, component, motion, responsive, and accessibility token groups.
- Preserve source references back to the raw inventory.
- Generate a draft `theme.css` for preview evidence only.
- Do not import generated CSS into production UI.

Manual checks:

```bash
cd /home/source/SpiritOS
git status --short
test -f data/design-vault/packs/internal-dashboard-demo-v4/tokens.json && echo "normalized tokens exist"
test -f data/design-vault/packs/internal-dashboard-demo-v4/theme.css && echo "theme css exists"
grep -n "primitive\\|semantic\\|component\\|motion\\|responsive\\|accessibility" data/design-vault/token-model-v0.1.md
grep -n "dashboard-demo-v4" data/design-vault/packs/internal-dashboard-demo-v4/tokens.json
git diff -- src/app src/components src/styles src/theme
git diff --check
```

Expected output:

- Normalized tokens and preview-only theme CSS exist in Design Vault.
- Grep finds every required token group.
- Existing app, component, style, and theme files are unchanged.
- `git diff --check` passes.

Next increment:
Phase 5.1: Add Playwright visual capture plan and optional smoke check

Rollback notes:

- Remove the normalized token files and token-model doc from this increment.
- No production CSS imports should exist.

### Phase 5: Playwright Visual Capture And Verification

#### Increment 5.1: Add Playwright Visual Capture Plan And Optional Smoke Check

Goal: Define how visual capture and comparison will work, then verify Playwright availability without assuming it is installed.

Files likely touched:

- Proposed: `data/design-vault/packs/internal-dashboard-demo-v4/reference/`
- Proposed: `data/design-vault/packs/internal-dashboard-demo-v4/generated/`
- Proposed: `data/design-vault/packs/internal-dashboard-demo-v4/match-report.json`
- Proposed: `docs/design-visual-verification-v0.1.md`
- Optional proposed later: `tests/e2e/design-vault-capture.spec.mjs`

Exact actions:

- Document capture targets, viewports, screenshot naming, and comparison thresholds.
- Use Playwright only when a config exists.
- Start with capture/listing behavior before adding strict regression gates.
- Do not add fragile visual tests against unapproved references.

Manual checks:

```bash
cd /home/source/SpiritOS
git status --short
test -f docs/design-visual-verification-v0.1.md && echo "visual verification doc exists"
grep -n "Playwright\\|screenshot\\|match-report" docs/design-visual-verification-v0.1.md
if ls playwright.config.* >/dev/null 2>&1; then
  npx playwright test --list
else
  echo "Playwright config not found, skipping Playwright check for this increment."
fi
git diff --check
```

Expected output:

- Visual verification docs exist.
- Grep finds Playwright, screenshot, and match-report guidance.
- Playwright check is skipped if no config exists, or lists configured tests if Playwright is available.
- `git diff --check` passes.

Next increment:
Phase 6.1: Create design pack preview documentation

Rollback notes:

- Remove the visual verification doc and any proposed capture test from this increment.
- Remove generated screenshots only if they were produced by this increment.

### Phase 6: Design Pack Preview And Documentation

#### Increment 6.1: Create Design Pack Preview Documentation

Goal: Make a design pack understandable without wiring it into production UI.

Files likely touched:

- Proposed: `data/design-vault/packs/internal-dashboard-demo-v4/README.md`
- Proposed: `data/design-vault/packs/internal-dashboard-demo-v4/components-map.json`
- Proposed: `docs/design-pack-authoring-v0.1.md`

Exact actions:

- Document what the pack contains, what it may be used for, and what is out of scope.
- Add a component map that describes design concepts without importing app components.
- Include preview instructions that are documentation-only unless a later approved implementation creates a preview route.
- Keep Storybook as proposed only because no Storybook setup was found.

Manual checks:

```bash
cd /home/source/SpiritOS
git status --short
test -f data/design-vault/packs/internal-dashboard-demo-v4/README.md && echo "pack readme exists"
test -f data/design-vault/packs/internal-dashboard-demo-v4/components-map.json && echo "components map exists"
test -f docs/design-pack-authoring-v0.1.md && echo "authoring doc exists"
grep -n "documentation-only\\|preview\\|Source Proxy" docs/design-pack-authoring-v0.1.md
git diff -- src/app src/components
git diff --check
```

Expected output:

- Pack README, component map, and authoring doc exist.
- Grep confirms preview and Source Proxy boundaries.
- Existing app routes and components are unchanged.
- `git diff --check` passes.

Next increment:
Phase 7.1: Define Reverse Designer approved-input contract

Rollback notes:

- Remove only the pack README, component map, and authoring doc from this increment.
- No app preview route should need rollback.

### Phase 7: Reverse Designer For Approved URLs, Images, Figma Later

#### Increment 7.1: Define Reverse Designer Approved-Input Contract

Goal: Specify how the Reverse Designer may analyze approved URLs, images, or Figma references later without enabling crawler behavior.

Files likely touched:

- Proposed: `docs/reverse-designer-approved-inputs-v0.1.md`
- Proposed: `data/design-vault/source-cards/approval-checklist.md`

Exact actions:

- Define accepted input types: internal route, local image, approved URL, approved Figma export, licensed asset bundle, and client-approved reference.
- Require source card approval before analysis.
- Define exact mode versus inspired-language mode.
- State that URL support means human-approved single references, not crawling.
- Defer Figma API wiring until later approval.

Manual checks:

```bash
cd /home/source/SpiritOS
git status --short
test -f docs/reverse-designer-approved-inputs-v0.1.md && echo "reverse designer contract exists"
grep -n "approved URL\\|Figma\\|single references\\|not crawling" docs/reverse-designer-approved-inputs-v0.1.md
grep -n "source card" docs/reverse-designer-approved-inputs-v0.1.md
git diff -- scout source_proxy src
git diff --check
```

Expected output:

- Reverse Designer contract exists.
- Grep confirms approved input types, single-reference boundary, and source-card requirement.
- Scout, Source Proxy, and app source files are unchanged.
- `git diff --check` passes.

Next increment:
Phase 8.1: Define Design Blender originality and attribution rules

Rollback notes:

- Revert the Reverse Designer contract and checklist edits.
- No runtime integration should exist.

### Phase 8: Design Blender / Style Alchemist

#### Increment 8.1: Define Design Blender Originality And Attribution Rules

Goal: Define how SpiritOS can blend approved design concepts into new original styles.

Files likely touched:

- Proposed: `docs/design-blender-style-alchemist-v0.1.md`
- Proposed: `data/design-vault/packs/<pack-id>/notes.md` for future packs

Exact actions:

- Define blend inputs as approved design packs, internal demos, owned references, or inspiration-only language notes.
- Require output to avoid protected copy, logos, brand assets, paid assets, and distinctive replicas unless exact mode is approved.
- Record influence notes without presenting generated output as another brand's work.
- Define review criteria for originality, usability, accessibility, and SpiritOS fit.

Manual checks:

```bash
cd /home/source/SpiritOS
git status --short
test -f docs/design-blender-style-alchemist-v0.1.md && echo "style alchemist doc exists"
grep -n "original\\|logos\\|brand assets\\|influence notes" docs/design-blender-style-alchemist-v0.1.md
grep -n "accessibility\\|SpiritOS fit" docs/design-blender-style-alchemist-v0.1.md
git diff -- src scout source_proxy
git diff --check
```

Expected output:

- Style Alchemist doc exists.
- Grep confirms originality, protected asset, influence, accessibility, and SpiritOS fit rules.
- Runtime source folders are unchanged.
- `git diff --check` passes.

Next increment:
Phase 9.1: Add Scout manual-gated design intake bridge plan

Rollback notes:

- Revert the Style Alchemist doc.
- Leave existing design packs untouched unless this increment created them.

### Phase 9: Scout Integration, Still Manual-Gated

#### Increment 9.1: Add Scout Manual-Gated Design Intake Bridge Plan

Goal: Plan a future Scout bridge where Scout can suggest design references but cannot approve, extract, or promote them automatically.

Files likely touched:

- Proposed: `docs/scout-design-intake-bridge-v0.1.md`
- Existing reference only: `scout/docs/V0_4_SCOUT_POLISH_CLOSEOUT.md`

Exact actions:

- Document Scout as a candidate suggestion lane.
- Keep approval in the Source Card Registry.
- Forbid auto-promotion into coding context.
- Forbid crawler behavior for v0.1.
- Require explicit human action to move a Scout suggestion into Design Vault.

Manual checks:

```bash
cd /home/source/SpiritOS
git status --short
test -f docs/scout-design-intake-bridge-v0.1.md && echo "Scout design bridge plan exists"
grep -n "candidate suggestion\\|manual\\|auto-promote\\|coding context" docs/scout-design-intake-bridge-v0.1.md
grep -n "auto-approve\\|write to coding context" scout/docs/V0_4_SCOUT_POLISH_CLOSEOUT.md
git diff -- scout/src source_proxy src
git diff --check
```

Expected output:

- Scout bridge plan exists.
- Grep confirms Scout remains candidate-only, manual-gated, and blocked from auto-promoting into coding context.
- Existing Scout runtime, Source Proxy, and app source files are unchanged.
- `git diff --check` passes.

Next increment:
Phase 10.1: Define Source Proxy design apply approval lane

Rollback notes:

- Revert the Scout design bridge plan.
- No Scout runtime files should need rollback.

### Phase 10: Source Proxy Apply Lane, Approval Only

#### Increment 10.1: Define Source Proxy Design Apply Approval Lane

Goal: Define how an approved design pack can later become a bounded implementation proposal without bypassing Source Proxy approval.

Files likely touched:

- Proposed: `docs/source-proxy-design-apply-lane-v0.1.md`
- Existing reference only: `docs/source-proxy-production-hardening-plan.md`
- Existing reference only: `docs/source-proxy-daily-use-runbook.md`

Exact actions:

- Define design packs as proposal evidence, not direct write authority.
- Require target files, allowed files, diff preview, approval ID, post-apply verification, and separate commit/push approvals if those ever apply.
- Require no writes to app UI before Source Proxy approval.
- Keep Cartographer authority unchanged.
- Keep Source Proxy behavior unchanged until a later approved implementation increment.

Manual checks:

```bash
cd /home/source/SpiritOS
git status --short
test -f docs/source-proxy-design-apply-lane-v0.1.md && echo "design apply lane doc exists"
grep -n "proposal evidence\\|approval ID\\|diff preview\\|post-apply verification" docs/source-proxy-design-apply-lane-v0.1.md
grep -n "Cartographer authority unchanged\\|Source Proxy behavior unchanged" docs/source-proxy-design-apply-lane-v0.1.md
git diff -- source_proxy src scout
git diff --check
```

Expected output:

- Source Proxy design apply lane doc exists.
- Grep confirms proposal evidence, approval binding, verification, and unchanged authority.
- Source Proxy, app source, and Scout runtime files are unchanged.
- `git diff --check` passes.

Next increment:
Phase 1.1: Create Design Vault schema docs and empty local registry scaffold

Rollback notes:

- Revert the design apply lane doc.
- No Source Proxy behavior should need rollback.

## v0.1 Acceptance Criteria

- Plan doc exists at `docs/design-systems-master-v0.1.md`.
- Phase 1.1 scaffold exists under proposed `data/design-vault/` paths after approval.
- Phase 2.1 source-card template and approval checklist exist after approval.
- All required phases are present.
- All phases have increments.
- Every increment has a manual check block.
- Every increment has expected output.
- Every increment has a next increment title.
- No implementation beyond docs is included in this planning increment.
- No crawler or autonomous behavior is added.
- No app UI is changed.
- No Source Proxy behavior is changed.
- No Scout runtime behavior is changed.
- No Cartographer authority is changed.
- Proposed Design Vault paths are clearly marked proposed until implemented later.

## Recommended Next Implementation Increment After Phase 2.1

Phase 3.1: Extract dashboard demo v4 source card and token inventory manually

Implementation permission is required before starting that increment.
