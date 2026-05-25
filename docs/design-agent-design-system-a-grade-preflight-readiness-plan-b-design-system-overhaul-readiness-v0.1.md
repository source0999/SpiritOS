# Design Agent + Design System A-Grade Preflight Readiness Plan B: Design System Overhaul Readiness v0.1

Status: docs-only Plan B complete

Owner: Britton

Date: 2026-05-24

Active master: `docs/design-agent-design-system-a-grade-preflight-readiness-master-plan-of-plans-v0.1.md`

Plan count: 2/10

Decision: GO for Plan C planning only after Britton accepts the Plan B closeout and manual checks.

## 1. Purpose

Plan B defines the design-system readiness spine required before Design Agent helpers can be upgraded to A-grade evidence. It turns the current C-grade reusable app-facing design system into a reviewable A- target model for later implementation and proof.

Plan B is docs-only. It does not edit tokens, CSS, app routes, components, Source Proxy runtime, providers, queues, workers, approval-token systems, apply systems, git state, branches, commits, pushes, stashes, resets, cleans, worktrees, or hidden autonomy.

Plan B does not start Plan C.

Plan B does not claim design-system implementation readiness.

Plan B does not claim visual/CSS proof was run.

## 2. Current Grade, Target Grade, And Owner

| Field | Value |
| --- | --- |
| Current grade | C actual reusable design system |
| Target grade | A- minimum before gauntlet |
| Owner lane | Design system lane |
| Prerequisite | Plan A accepted docs-only baseline, authority, and source-of-truth recovery |
| Allowed next plan | Plan C only after Plan B closeout is accepted |
| Current implementation status | NO-GO |

## 3. Standing Authority Boundary

Allowed files:

- `docs/design-agent-design-system-a-grade-preflight-readiness-plan-b-design-system-overhaul-readiness-v0.1.md`
- `docs/design-agent-design-system-a-grade-preflight-readiness-plan-b-closeout-v0.1.md`
- `docs/plan-index.md` only as a narrow active-plan index update.

Forbidden files and actions:

- No runtime code edits.
- No CSS edits.
- No app route edits.
- No component edits.
- No Source Proxy runtime edits.
- No provider/model calls.
- No queue or worker execution.
- No `/coding` UI edits.
- No approval-token changes.
- No apply.
- No execute-approved.
- No commit.
- No push.
- No branch.
- No worktree.
- No stash.
- No reset.
- No clean.
- No checkout.
- No hidden autonomy.
- No visual/browser/screenshot proof execution.
- No claim that preflight readiness passed.
- No claim that gauntlet ran.
- No claim that Source Proxy proof ran.
- No claim that design/CSS proof ran.

## 4. Evidence Inputs

| Evidence source | Plan B handling |
| --- | --- |
| `docs/design-system-overhaul-master-v0.2.md` | Active design-system planning spine. Supplies C grade, current assets, gaps, and authority model. |
| `data/design-vault/token-model-v0.1.md` | Draft Design Vault token model. Proposal evidence only. |
| `data/design-vault/packs/internal-dashboard-demo-v4/tokens.raw.json` | Manual raw token inventory for internal dashboard demo v4. |
| `data/design-vault/packs/internal-dashboard-demo-v4/tokens.json` | Normalized draft token model. Runtime import not allowed. |
| `data/design-vault/packs/internal-dashboard-demo-v4/theme.css` | Preview-only CSS aliases. Not production authority. |
| `data/design-vault/packs/internal-dashboard-demo-v4/components-map.json` | Conceptual component map. Advisory only. |
| `src/theme/spiritPalettes.ts` | Palette registry and semantic CSS key source. Read-only evidence. |
| `src/theme/useSpiritTheme.ts` | Theme application hook. Read-only evidence. |
| `src/app/globals.css` | Global CSS variables and shell tokens. Read-only evidence. |
| `src/styles/*.css` | Route/demo/style-specific CSS risk evidence. Read-only evidence. |
| `src/components/ui/` | Current reusable primitive source. Read-only evidence. |
| `src/components/dashboard/`, `src/components/chat/`, `src/components/coding/`, `src/components/oracle/`, `src/components/design-demo/` | Feature-local and route-surface component evidence. Read-only evidence. |

## 5. Phase B1: Token Inventory

### Increment B1.1: Token Source Inventory

Objective:
Inventory token sources in Design Vault, theme files, global CSS variables, route CSS, and palette files.

Allowed files:
Plan B docs, Plan B closeout, and narrow `docs/plan-index.md` update.

Forbidden files/actions:
No token edits, no CSS edits, no app edits, no route edits, no Source Proxy execution, no provider/model calls, no queue/worker action, no approval-token action, no apply, and no git mutation.

Expected output:
Token source table with owner, status, drift risk, and evidence path.

Codex self-checks:
Confirm `Design Vault`, `globals.css`, `spiritPalettes`, `route-scoped`, and `drift` appear in this Plan B doc.

Britton manual verification check:
Confirm inventory is based on real repository paths and no token source was changed.

Stop condition:
Stop if source inspection suggests hidden runtime edits are needed now.

Rollback/recovery note:
Mark unknown token sources `unavailable` and keep implementation NO-GO.

| Token source | Evidence path | Owner/status | Drift risk | Plan B handling |
| --- | --- | --- | --- | --- |
| Design Vault token model | `data/design-vault/token-model-v0.1.md` | Draft model, proposal evidence only | Medium | Use for category vocabulary, not runtime authority. |
| Design Vault raw tokens | `data/design-vault/packs/internal-dashboard-demo-v4/tokens.raw.json` | Manual raw inventory | Medium | Use as source traceability evidence only. |
| Design Vault normalized tokens | `data/design-vault/packs/internal-dashboard-demo-v4/tokens.json` | Normalized draft, runtime import not allowed | Medium | Map to canonical categories; do not import. |
| Design Vault preview aliases | `data/design-vault/packs/internal-dashboard-demo-v4/theme.css` | Preview-only CSS aliases | High if imported directly | Keep out of production CSS until later approved plan. |
| Palette registry | `src/theme/spiritPalettes.ts` | Live theme registry and semantic key source | Medium | Treat as app-facing token evidence. |
| Theme hook | `src/theme/useSpiritTheme.ts` | Live theme application behavior | Medium | Treat as behavior evidence, not edit target. |
| Global CSS variables | `src/app/globals.css` | Live global and shell token definitions | Medium/high | Primary live CSS token evidence; no edits in Plan B. |
| Demo/style CSS | `src/styles/spirit-demo.tokens.css`, `src/styles/spirit-demo.components.css`, `src/styles/spirit-demo.layout.css`, `src/styles/dashboard-demo-v4.css`, `src/styles/spirit-trinity-chat.css` | Demo, route, and feature styling | High | Map as route-scoped or feature-local risk. |
| Component-local CSS | `src/components/oracle/oracle-visuals.css` | Feature-local visual styling | Medium/high | Map as component-specific risk. |

Closeout gate:
GO. Token sources and drift risks are visible enough for canonical categories.

## 6. Phase B2: Canonical Token Categories

### Increment B2.1: Canonical Token Category Contract

Objective:
Define color, type, spacing, radius, shadow, motion, z-index, layout, state, and semantic token categories.

Allowed files:
Plan B docs and closeout.

Forbidden files/actions:
No token implementation and no CSS edits.

Expected output:
Category contract with required fields and examples.

Codex self-checks:
Confirm all token category names appear: color, type, spacing, radius, shadow, motion, z-index, layout, state, semantic.

Britton manual verification check:
Confirm categories are complete enough for future UI proposals.

Stop condition:
Stop if category naming conflicts with active design-system source of truth.

Rollback/recovery note:
Defer contested category to Plan B blocked notes.

| Category | Required fields | Evidence examples | A- readiness rule |
| --- | --- | --- | --- |
| color | primitive value, semantic role, contrast target, state use, source path | `--spirit-bg`, `--spirit-accent`, `primitive.color`, `semantic.background` | Must map from source to semantic use and flag contrast proof as future Plan G. |
| type | family, scale, weight, line-height, usage, source path | `--font-sans`, `--text-h1`, `typography.body` | Must avoid viewport-scaled ambiguity in compact UI contracts. |
| spacing | scale name, value, density role, responsive behavior | `--spirit-space-page-gutter`, `--demo-space-md` | Must separate page, panel, control, compact, and touch spacing. |
| radius | scale name, value, component role | `--spirit-radius-card`, `--radius-card` | Must map shell, panel, card, control, pill. |
| shadow | elevation role, token, contrast risk, motion relationship | `--spirit-shadow-elevated`, `--spirit-panel-glow` | Must not hide focus, state, or content readability. |
| motion | duration, easing, reduced-motion fallback, trigger | Design Vault motion tokens | Must include reduced-motion fallback before visual proof. |
| z-index | layer name, value, owner, collision risk | `--shell-z-nav`, `--shell-z-modal`, `--shell-z-toast` | Must prevent nav, composer, modal, toast overlap ambiguity. |
| layout | container, grid, rail, mobile nav, safe area, density | shell dimension variables | Must define viewport and touch behavior before implementation. |
| state | hover, active, focus, disabled, loading, error, empty, selected | semantic state tokens and component states | Must require visible state proof later. |
| semantic | intent, primitive source, accessible usage, owner | `SPIRIT_SEMANTIC_CSS_KEYS` | Must be the bridge from raw tokens to component contracts. |

Closeout gate:
GO. Canonical categories are complete enough to guide future implementation planning.

## 7. Phase B3: Design Vault Alignment

### Increment B3.1: Vault Alignment Matrix

Objective:
Map Design Vault token and pack artifacts to canonical token categories and proposal evidence rules.

Allowed files:
Plan B docs and closeout.

Forbidden files/actions:
No Design Vault writes and no runtime CSS import.

Expected output:
Design Vault alignment matrix with gaps and future migration notes.

Codex self-checks:
Confirm `tokens.raw.json`, `tokens.json`, `theme.css`, `components-map.json`, and `proposal evidence` appear.

Britton manual verification check:
Confirm vault remains evidence, not runtime authority.

Stop condition:
Stop if alignment implies production CSS import.

Rollback/recovery note:
Keep vault alignment advisory and block implementation sequencing.

| Vault artifact | Alignment | Gap | Proposal evidence rule |
| --- | --- | --- | --- |
| `tokens.raw.json` | Raw observed token inventory | Needs canonical mapping review before implementation | Cite as source evidence only. |
| `tokens.json` | Normalized draft maps primitive, semantic, component, motion, responsive, accessibility ideas | Screenshots not captured; runtime import false | Use for Plan C packet vocabulary and Plan G proof targets. |
| `theme.css` | Preview-only aliases | High risk if imported to production | Never import without separate Source Proxy plan. |
| `components-map.json` | Conceptual map from demo components to design roles | Does not prove reusable primitives exist | Use for anatomy planning and component relevance scoring. |
| `match-report.json` | Visual verification scaffold | Not run | Keep not_started until Plan G proof. |
| `reference/`, `generated/` | Screenshot folders | Placeholder only | Do not claim screenshot evidence. |

Closeout gate:
GO. Design Vault evidence maps to canonical categories without apply authority.

## 8. Phase B4: Primitive/Component Inventory

### Increment B4.1: Reusable Primitive Inventory

Objective:
Inventory existing primitives, feature components, route components, and missing primitives.

Allowed files:
Plan B docs and closeout.

Forbidden files/actions:
No component edits.

Expected output:
Primitive/component table with reuse status and ownership.

Codex self-checks:
Confirm `GlassPanel`, `SectionLabel`, `SpiritButton`, `feature-local`, and `missing primitive` appear.

Britton manual verification check:
Confirm inventory distinguishes reusable system parts from route-specific styling.

Stop condition:
Stop if no stable source can identify component ownership.

Rollback/recovery note:
Mark ownership questions and block anatomy contracts.

| Surface | Evidence path | Reuse status | Ownership note | Plan B grade impact |
| --- | --- | --- | --- | --- |
| GlassPanel | `src/components/ui/GlassPanel.tsx` | reusable primitive | app-facing UI primitive | Useful, but too small alone for A-. |
| SectionLabel | `src/components/ui/SectionLabel.tsx` | reusable primitive | app-facing UI primitive | Useful for headings/sections. |
| SpiritButton | `src/components/ui/SpiritButton.tsx` | reusable primitive | app-facing UI primitive | Useful control primitive. |
| UI index | `src/components/ui/index.ts` | primitive export map | app-facing primitive boundary | Current primitive set is narrow. |
| Dashboard components | `src/components/dashboard/` | feature-local with some reusable candidates | dashboard lane | Needs mapping before extraction. |
| Chat components | `src/components/chat/` | feature-local | chat lane | Not a canonical design system yet. |
| Coding components | `src/components/coding/` | feature-local operational UI | Source Proxy/coding lane | Must not be edited by Plan B. |
| Oracle components | `src/components/oracle/` | feature-local with local CSS | oracle lane | Visual surface needs CSS risk proof later. |
| Design demo components | `src/components/design-demo/` | demo/reference surface | design-demo lane | Useful reference, not production authority. |
| Missing primitive | field/input, card, modal, toast, badge, tabs, table/list, nav/rail, command surface | missing primitive | future implementation only | Blocks A- until contracts and later implementation exist. |

Closeout gate:
GO. Reusable versus feature-local parts are separated for planning.

## 9. Phase B5: Component Anatomy Contracts

### Increment B5.1: Anatomy Contract Plan

Objective:
Define anatomy fields for button, card, panel, field, nav, rail, table/list, modal, toast, badge, tabs, and command surface components.

Allowed files:
Plan B docs and closeout.

Forbidden files/actions:
No component code and no Storybook setup.

Expected output:
Anatomy contract template with slots, density, state, accessibility, and evidence expectations.

Codex self-checks:
Confirm every component family and `slots` appear.

Britton manual verification check:
Confirm contracts are specific enough for future Design Coding Proposal packets.

Stop condition:
Stop if anatomy contract hides route-specific CSS risk.

Rollback/recovery note:
Mark missing families as gaps before Plan C.

Anatomy template:

| Field | Required content |
| --- | --- |
| Component family | button, card, panel, field, nav, rail, table/list, modal, toast, badge, tabs, or command surface |
| Slots | root, label/title, description, icon/media, content/body, actions, metadata, status, error/help, close/dismiss when relevant |
| Density | compact, regular, spacious, mobile constraints |
| Token links | color, type, spacing, radius, shadow, motion, z-index, layout, state, semantic |
| States | default, hover, active, focus, disabled, loading, error, empty, selected, responsive, reduced-motion |
| Accessibility | role, name, keyboard path, focus visibility, contrast target, touch target |
| Evidence | source path, screenshot target later, test/check target later, unavailable proof rule |
| Risk | route CSS dependency, feature-local styling dependency, missing primitive, owner |

Closeout gate:
GO. Component anatomy can be reviewed without code.

## 10. Phase B6: Variant/State Contracts

### Increment B6.1: Variant And State Matrix

Objective:
Define variant, hover, active, focus, disabled, loading, error, empty, selected, responsive, and reduced-motion states.

Allowed files:
Plan B docs and closeout.

Forbidden files/actions:
No CSS or tests.

Expected output:
State matrix with required visual evidence later.

Codex self-checks:
Confirm every state name and `reduced-motion` appear.

Britton manual verification check:
Confirm no state is waived without reason.

Stop condition:
Stop if state expectations require unapproved screenshot capture now.

Rollback/recovery note:
Mark visual proof as future Plan G dependency.

| State | Required contract | Later proof owner |
| --- | --- | --- |
| variant | intent, visual difference, token source, component family | Plan G and later implementation plan |
| hover | pointer behavior and non-hover fallback | Plan G |
| active | pressed/current behavior | Plan G |
| focus | visible focus ring, keyboard path, no hidden outline | Plan G |
| disabled | noninteractive semantics and visible disabled state | Plan G |
| loading | progress indication and blocked duplicate action | Plan G/Plan F |
| error | visible error text, semantics, recovery action | Plan G/Plan D |
| empty | empty-state copy, action, layout stability | Plan G |
| selected | aria/current selection and visual state | Plan G |
| responsive | mobile/tablet/desktop/wide behavior | Plan G |
| reduced-motion | no essential information in motion only | Plan G |

Closeout gate:
GO. Required states are explicit and not waived.

## 11. Phase B7: Route-Scoped CSS Risk Map

### Increment B7.1: CSS Risk Map

Objective:
Map route-scoped CSS, feature-local styling, token drift, specificity risk, and mobile risk.

Allowed files:
Plan B docs and closeout.

Forbidden files/actions:
No CSS edits or CSS cleanup.

Expected output:
Route CSS risk table and future sequencing recommendation.

Codex self-checks:
Confirm `route-scoped CSS`, `specificity`, `mobile`, and `risk` appear.

Britton manual verification check:
Confirm risk language does not start CSS polish.

Stop condition:
Stop if any CSS file must be touched to complete the map.

Rollback/recovery note:
Leave risk item as `unknown` and continue only if nonblocking.

| Risk area | Evidence path | Risk | Future handling |
| --- | --- | --- | --- |
| Global token/root variables | `src/app/globals.css` | Medium/high token drift risk | Future token consolidation plan only. |
| Demo token CSS | `src/styles/spirit-demo.tokens.css` | Medium/high duplicate token vocabulary | Map before reuse. |
| Demo component CSS | `src/styles/spirit-demo.components.css` | Medium route/demo coupling | Treat as reference until extracted. |
| Demo layout/effects/animation CSS | `src/styles/spirit-demo.layout.css`, `src/styles/spirit-demo.effects.css`, `src/styles/spirit-demo.animations.css` | Medium/high visual dependency risk | Plan G target, no polish now. |
| Dashboard demo CSS | `src/styles/dashboard-demo-v4.css` | High pack-to-runtime drift risk | Keep Design Vault alignment advisory. |
| Chat route styling | `src/styles/spirit-trinity-chat.css` | Medium/high feature-local risk | Requires visual and mobile proof later. |
| Oracle visual CSS | `src/components/oracle/oracle-visuals.css` | Medium component-local risk | Needs component relevance proof later. |
| Route/app surfaces | `src/app/chat/page.tsx`, `src/app/coding/page.tsx`, `src/app/oracle/page.tsx`, `src/app/design-demo/page.tsx`, `src/app/(dashboard)/page.tsx` | Medium route coupling risk | Do not edit until later approved implementation. |

Closeout gate:
GO. CSS risks are known enough to block unsafe proposals.

## 12. Phase B8: Accessibility Baseline

### Increment B8.1: Accessibility Criteria

Objective:
Define contrast, focus, keyboard, touch target, motion, semantics, text scale, and state visibility baseline.

Allowed files:
Plan B docs and closeout.

Forbidden files/actions:
No accessibility implementation or test edits.

Expected output:
Accessibility checklist for future proposals and visual evidence.

Codex self-checks:
Confirm all baseline criteria appear.

Britton manual verification check:
Confirm accessibility is a grade cap.

Stop condition:
Stop if accessibility evidence is claimed without a run.

Rollback/recovery note:
Mark unavailable evidence and require Plan G proof.

| Criterion | A- baseline |
| --- | --- |
| contrast | Text, icon, border, focus, and state contrast must be checked later before A claim. |
| focus | Keyboard focus must be visible and not hidden by glass, glow, or overlays. |
| keyboard | Interactive flows need tab order, escape/close behavior, and no keyboard traps. |
| touch target | Primary mobile controls target 44px minimum unless an accepted exception exists. |
| motion | Reduced-motion fallback must preserve meaning. |
| semantics | Buttons, links, tabs, nav, modal, toast, fields, tables/lists need roles/names. |
| text scale | Text must fit containers and remain readable under scaling. |
| state visibility | Error, loading, disabled, selected, active, and empty states cannot be color-only. |

Closeout gate:
GO. Accessibility baseline is reviewable and remains a grade cap.

## 13. Phase B9: Responsive/Mobile Baseline

### Increment B9.1: Responsive Criteria

Objective:
Define mobile, tablet, desktop, wide, reduced-motion, and touch review expectations.

Allowed files:
Plan B docs and closeout.

Forbidden files/actions:
No browser run and no screenshot capture.

Expected output:
Viewport matrix and responsive acceptance criteria.

Codex self-checks:
Confirm `mobile`, `tablet`, `desktop`, `wide`, and `touch` appear.

Britton manual verification check:
Confirm criteria match actual SpiritOS review needs.

Stop condition:
Stop if viewport proof is claimed before capture.

Rollback/recovery note:
Mark viewports as target list only.

| Viewport target | Purpose | Status |
| --- | --- | --- |
| mobile narrow | Single-column, touch, safe-area, nav/composer overlap | target only |
| mobile large | Dense mobile review and touch spacing | target only |
| tablet | Rail/content split and grid density | target only |
| desktop | Primary operator workflow | target only |
| wide desktop | Dense dashboard/coding surfaces and next-section visibility where relevant | target only |
| reduced-motion | Motion fallback and visual state persistence | target only |

Closeout gate:
GO. Responsive targets are explicit and not claimed as captured.

## 14. Phase B10: Visual Evidence Target Matrix

### Increment B10.1: Visual Evidence Matrix

Objective:
Define screenshots, viewport coverage, component examples, route examples, token checks, and unavailable-proof rules.

Allowed files:
Plan B docs and closeout.

Forbidden files/actions:
No screenshot capture in this phase.

Expected output:
Visual target matrix for Plan G.

Codex self-checks:
Confirm `screenshot target`, `viewport`, `token alignment`, and `unavailable` appear.

Britton manual verification check:
Confirm matrix is realistic and does not claim evidence exists.

Stop condition:
Stop if matrix depends on unapproved tool installation.

Rollback/recovery note:
Defer tool choice to Plan G.

| Screenshot target | Evidence target | Status |
| --- | --- | --- |
| dashboard home | shell, cards, nav, state, responsive grid | not_started |
| chat surface | thread list, composer, message states, mobile drawer | not_started |
| coding surface | command center, status/progress, approval/apply separation | not_started |
| oracle surface | voice state, transcript, controls, visual layer | not_started |
| design demo | reference patterns and component examples | not_started |
| reusable primitives | GlassPanel, SectionLabel, SpiritButton | not_started |
| Design Vault pack | internal-dashboard-demo-v4 token/component relevance | not_started |
| token alignment | live CSS vars vs palette registry vs Design Vault | not_started |
| unavailable evidence | explicit not_started/unavailable labels and no fake proof | required |

Closeout gate:
GO. Plan G can consume the visual target matrix.

## 15. Phase B11: Future Implementation Sequencing

### Increment B11.1: Implementation Sequence Plan

Objective:
Sequence future implementation after docs readiness: tokens, primitives, contracts, route risk reduction, visual proof.

Allowed files:
Plan B docs and closeout.

Forbidden files/actions:
No implementation now.

Expected output:
Future plan titles with prerequisites and stop conditions.

Codex self-checks:
Confirm `future implementation`, `separate approval`, and `NO-GO` appear.

Britton manual verification check:
Confirm sequence does not jump to CSS polish.

Stop condition:
Stop if future implementation plan grants authority now.

Rollback/recovery note:
Convert overbroad step to title-only.

Future implementation sequencing, title-only and not authorized now:

1. Design System Implementation Step 1: Canonical Token Contract Patch Plan.
2. Design System Implementation Step 2: Primitive Expansion Patch Plan.
3. Design System Implementation Step 3: Component Anatomy Implementation Plan.
4. Design System Implementation Step 4: Route CSS Risk Reduction Plan.
5. Design System Implementation Step 5: Visual Evidence Execution Plan.
6. Design System Implementation Step 6: A- Design-System Evidence Closeout.

Each future implementation step requires separate approval, exact files, checks, rollback, and stop conditions. Plan B grants no implementation authority.

Closeout gate:
GO. Future sequencing is separate and gated.

## 16. Phase B12: Plan B Closeout

### Increment B12.1: Plan B Decision

Objective:
Decide GO/NO-GO for Plan C.

Allowed files:
Plan B closeout and optional `docs/plan-index.md` note.

Forbidden files/actions:
Standing forbidden set.

Expected output:
Design-system readiness grade, gap list, and next authorized title only.

Codex self-checks:
Run docs diff check, required grep, forbidden-claim grep, and em dash grep.

Britton manual verification check:
Confirm actual reusable design system can support subagent diagnostics.

Stop condition:
Stop if actual design system remains too ambiguous for subagent packet grading.

Rollback/recovery note:
Request additional Plan B recovery increment.

Plan B GO/NO-GO decision gate:
GO for Plan C planning only. Plan B defines a clear design-system target model, A- path, evidence matrix, and risk map. NO-GO for implementation, CSS edits, visual proof execution, and final readiness.

Next authorized title only:
`3/10: Design Agent + Design System A-Grade Preflight Readiness Plan C: Subagent A-Grade Evidence Upgrade`
