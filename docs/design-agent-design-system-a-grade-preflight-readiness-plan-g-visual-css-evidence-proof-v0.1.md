# Design Agent + Design System A-Grade Preflight Readiness Plan G: Visual/CSS Evidence Proof v0.1

Status: docs-only Plan G complete

Date: 2026-05-25

Count: 7/10

Owner lane: Visual/CSS evidence lane

Prerequisite: Plan F GO for planning

Decision: GO for Plan H planning only after Britton accepts the Plan G closeout and manual checks.

## 1. Purpose

Plan G defines the Visual/CSS evidence proof model required before Source Proxy PR-8.3 alignment planning. It makes future visual/CSS evidence reviewable by defining screenshot targets, viewport coverage, accessibility smoke checks, token alignment proof, component relevance proof, CSS risk proof, route visual-readiness scoring, and not_started/unavailable honesty rules.

Plan G is docs-only. It does not run browsers, capture screenshots, compare pixels, write baselines, write visual evidence files, edit CSS, edit tokens, edit app routes, edit components, edit `/coding`, run Source Proxy proof, call providers/models, execute queues/workers, consume approval tokens, apply changes, mutate git state, or create hidden autonomy.

Plan G does not start Plan H.

Plan G does not claim visual/CSS proof ran.

Plan G does not claim screenshots were captured.

## 2. Grade And Lane

| Field | Value |
| --- | --- |
| Current grade | C+ visual readiness and C actual reusable design system |
| Target grade | A- visual/CSS evidence readiness |
| Owner lane | Visual/CSS evidence lane |
| Allowed next plan | Plan H only after Plan G closeout is accepted |
| Current visual execution status | NO-GO |
| Current CSS implementation status | NO-GO |
| Current evidence execution status | NO-GO |

## 3. Standing Forbidden Set

- No browser run.
- No screenshot capture.
- No Playwright install or execution.
- No pixel comparison.
- No baseline write.
- No visual evidence file write.
- No accessibility test run.
- No CSS edits.
- No token edits.
- No app route edits.
- No component edits.
- No `/coding` UI edits.
- No Source Proxy calls or proof.
- No provider/model calls.
- No queue or worker execution.
- No approval-token reads, writes, validation, creation, or consumption.
- No apply.
- No execute-approved.
- No package, config, env, auth, generated/cache, protected-path, test, or app UI edits.
- No commit, push, branch, worktree, stash, reset, clean, checkout, or git mutation.
- No self-approval or hidden autonomy.
- No claim that visual/CSS proof ran.
- No claim that preflight readiness passed.

## 4. Evidence Inputs

| Evidence source | Plan G handling |
| --- | --- |
| `docs/design-agent-design-system-a-grade-preflight-readiness-master-plan-of-plans-v0.1.md` | Supplies Plan G scope, phases, gates, and next authorized title. |
| `docs/design-agent-design-system-a-grade-preflight-readiness-plan-f-diagnostic-batch-harness-proof-v0.1.md` | Supplies visual evidence quality and CSS/component relevance scoring fields. |
| `docs/design-agent-design-system-a-grade-preflight-readiness-plan-f-closeout-v0.1.md` | Supplies Plan F closeout and Plan G authorization boundary. |
| `docs/design-agent-design-system-a-grade-preflight-readiness-plan-b-design-system-overhaul-readiness-v0.1.md` | Supplies token categories, component anatomy, states, accessibility, responsive, visual target, and CSS risk vocabulary. |
| `docs/design-agent-ecosystem-plan-17-visual-css-evidence-harness-readiness-v0.1.md` | Supplies visual/CSS evidence schema, responsive/mobile criteria, fake-proof traps, and not-run status rules. |
| `data/design-vault/packs/internal-dashboard-demo-v4/match-report.json` | Prior evidence says match report status is not-run. It is not visual proof. |
| `data/design-vault/packs/internal-dashboard-demo-v4/README.md` | Prior evidence says screenshot folders are placeholders. They are not captured proof. |

## 5. Phase G1: Screenshot Target List

### Increment G1.1: Screenshot Targets

Objective:

Define route, component, state, and packet screenshot targets.

Allowed files:

Plan G docs, Plan G closeout, and narrow `docs/plan-index.md` update.

Forbidden files/actions:

No screenshot capture, no browser run, no Playwright execution, no baseline write, no visual evidence file write, no CSS edits, and no route/component edits.

Expected output:

Screenshot target list.

Codex self-checks:

Confirm `screenshot target`, `route`, `component`, `state`, and `target-only` appear.

Britton manual verification check:

Confirm target list covers actual weak surfaces and does not claim screenshots exist.

Stop condition:

Stop if target list claims screenshots exist.

Rollback or recovery note:

Mark all targets as target-only and not_started.

| Screenshot target | Evidence path or surface | Required states | Current status |
| --- | --- | --- | --- |
| dashboard shell | `src/app/(dashboard)/page.tsx` | default, dense data, loading, empty, selected | target-only, not_started |
| chat route | `src/app/chat/page.tsx` and `src/styles/spirit-trinity-chat.css` | default, active input, empty, error, overflow | target-only, not_started |
| coding route | `src/app/coding/page.tsx` | read-only packet display candidate, blocked state, no action controls | target-only, not_started |
| oracle route | `src/app/oracle/page.tsx` and `src/components/oracle/oracle-visuals.css` | voice state, transcript, controls, visual layer | target-only, not_started |
| design-demo route | `src/app/design-demo/page.tsx` | demo tokens, demo components, responsive layout | target-only, not_started |
| reusable primitives | `GlassPanel`, `SectionLabel`, `SpiritButton` | default, hover, focus, disabled, loading | target-only, not_started |
| Design Vault pack | `data/design-vault/packs/internal-dashboard-demo-v4/` | token/component relevance and missing screenshots | target-only, not_started |
| token alignment surface | live CSS vars, palette registry, Design Vault tokens | mismatch, unavailable, accepted later | target-only, not_started |

Closeout gate:

GO. Targets are specific and target-only.

## 6. Phase G2: Viewport Matrix

### Increment G2.1: Viewport Matrix

Objective:

Define mobile, tablet, desktop, wide, reduced-motion, and touch viewport expectations.

Allowed files:

Plan G docs and closeout.

Forbidden files/actions:

No browser run, no screenshot capture, no viewport test execution, and no visual proof claim.

Expected output:

Viewport matrix.

Codex self-checks:

Confirm `mobile`, `tablet`, `desktop`, `wide`, `reduced-motion`, and `touch` appear.

Britton manual verification check:

Confirm mobile evidence is first-class and not optional.

Stop condition:

Stop if viewport coverage is optional without reason.

Rollback or recovery note:

Require Britton exception for omitted viewport.

| Viewport category | Target | Required checks | Current status |
| --- | --- | --- | --- |
| mobile narrow | 360px to 390px width | text fit, touch target, overflow, nav behavior, state visibility | not_started |
| mobile wide | 414px to 430px width | touch comfort, vertical density, input behavior | not_started |
| tablet | 768px width | layout transitions, side panels, card/list density | not_started |
| desktop | 1280px width | normal work surface, density, focus path | not_started |
| wide desktop | 1440px to 1728px width | max-width behavior, long-line control, route framing | not_started |
| height constrained | 720px height or lower | scroll behavior, sticky controls, hidden content risk | not_started |
| reduced-motion | prefers-reduced-motion | no motion-only meaning, persistent state cues | not_started |
| touch | coarse pointer | hover alternatives, 44px target expectation, no hover-only controls | not_started |

Closeout gate:

GO. Viewport coverage is sufficient and not_started.

## 7. Phase G3: Accessibility Smoke Checklist

### Increment G3.1: Accessibility Smoke Checklist

Objective:

Define visual accessibility checks for contrast, focus, keyboard path, touch targets, text scale, motion, and state visibility.

Allowed files:

Plan G docs and closeout.

Forbidden files/actions:

No accessibility test run, no browser run, no screenshot capture, no CSS edits, and no component edits.

Expected output:

Accessibility smoke checklist.

Codex self-checks:

Confirm `contrast`, `focus`, `keyboard path`, `touch target`, `text scale`, `motion`, and `state visibility` appear.

Britton manual verification check:

Confirm checklist is usable in manual review.

Stop condition:

Stop if accessibility proof is claimed before evidence.

Rollback or recovery note:

Mark evidence unavailable.

| Criterion | Future evidence needed | Current status |
| --- | --- | --- |
| contrast | Text, icon, border, focus, and state contrast review. | not_started |
| focus | Visible focus ring and no hidden outline behind glass/glow/overlays. | not_started |
| keyboard path | Tab order, escape/close behavior, no keyboard trap. | not_started |
| touch target | Primary mobile controls target 44px minimum unless exception exists. | not_started |
| text scale | Text fits containers and remains readable under scaling. | not_started |
| motion | Reduced-motion fallback preserves meaning. | not_started |
| state visibility | Error, loading, disabled, selected, active, and empty states are not color-only. | not_started |

Closeout gate:

GO. Checklist is reviewable and no proof is claimed.

## 8. Phase G4: Token Alignment Proof

### Increment G4.1: Token Alignment Proof Recipe

Objective:

Define how future visual evidence proves token alignment.

Allowed files:

Plan G docs and closeout.

Forbidden files/actions:

No token edit, no CSS edit, no production import, no Design Vault write, and no runtime style change.

Expected output:

Token alignment proof recipe.

Codex self-checks:

Confirm `token alignment`, `Design Vault`, `canonical`, `spiritPalettes`, and `globals.css` appear.

Britton manual verification check:

Confirm proof ties to Plan B token categories.

Stop condition:

Stop if proof requires live token change now.

Rollback or recovery note:

Defer to future implementation plan.

| Token proof area | Sources to compare | Required future result | Current status |
| --- | --- | --- | --- |
| canonical categories | Plan B color, type, spacing, radius, shadow, motion, z-index, layout, state, semantic | Category mapped or gap labeled. | planned |
| Design Vault tokens | `data/design-vault/packs/internal-dashboard-demo-v4/tokens.json` | Proposal token maps to canonical category. | not_started |
| palette registry | `src/theme/spiritPalettes.ts` | Semantic key source is identified. | not_started |
| global CSS variables | `src/app/globals.css` | Live variable source is identified. | not_started |
| route CSS | `src/styles/*.css` and component-local CSS | Route-scoped drift risk is labeled. | not_started |
| mismatch handling | Design Vault vs live CSS vs palette registry | mismatch, unavailable, partial, or accepted later. | not_started |

Closeout gate:

GO. Token proof is tied to canonical categories.

## 9. Phase G5: Component Relevance Proof

### Increment G5.1: Component Relevance Proof Recipe

Objective:

Define how future evidence proves proposals map to actual primitives, anatomy, variants, and states.

Allowed files:

Plan G docs and closeout.

Forbidden files/actions:

No component edit, no route edit, no CSS edit, and no implementation authority.

Expected output:

Component relevance proof recipe.

Codex self-checks:

Confirm `component relevance`, `anatomy`, `variant`, `state`, and `actual repo surfaces` appear.

Britton manual verification check:

Confirm proof rejects generic component advice.

Stop condition:

Stop if proof cannot map to actual repo surfaces.

Rollback or recovery note:

Return to Plan B component inventory recovery.

| Proof area | Actual repo surface | Required future evidence | Current status |
| --- | --- | --- | --- |
| primitive mapping | `GlassPanel`, `SectionLabel`, `SpiritButton` | Component anatomy and state coverage. | not_started |
| feature-local mapping | `src/components/dashboard/`, `src/components/chat/`, `src/components/coding/`, `src/components/oracle/` | Feature-local ownership and extraction risk. | not_started |
| missing primitives | field/input, modal, toast, badge, tabs, table/list, nav/rail, command surface | Missing primitive does not become fake implementation. | not_started |
| variants | default, dense, compact, destructive, selected, emphasized | Visual distinction and token linkage. | not_started |
| states | hover, active, focus, disabled, loading, error, empty, selected, responsive, reduced-motion | State evidence target or unavailable label. | not_started |
| generic advice rejection | no repo path, no anatomy, no state, no route risk | score blocked or generic only. | planned |

Closeout gate:

GO. Component relevance can be proven later against actual repo surfaces.

## 10. Phase G6: CSS Risk Proof

### Increment G6.1: CSS Risk Proof Recipe

Objective:

Define proof for route CSS risk, specificity risk, token drift, and responsive risk.

Allowed files:

Plan G docs and closeout.

Forbidden files/actions:

No CSS edits, no CSS cleanup, no route edits, no component edits, and no production token import.

Expected output:

CSS risk proof recipe.

Codex self-checks:

Confirm `CSS risk`, `specificity`, `token drift`, `responsive`, and `read-only` appear.

Britton manual verification check:

Confirm risk proof blocks unsafe polish.

Stop condition:

Stop if proof starts CSS cleanup.

Rollback or recovery note:

Keep risk proof read-only.

| Risk area | Evidence target | Future proof question | Current status |
| --- | --- | --- | --- |
| route-scoped CSS | `src/styles/spirit-trinity-chat.css`, `src/styles/dashboard-demo-v4.css` | Does route styling conflict with canonical tokens or mobile behavior? | not_started |
| demo CSS | `src/styles/spirit-demo.tokens.css`, `src/styles/spirit-demo.components.css`, `src/styles/spirit-demo.layout.css` | Is demo styling reusable or only reference material? | not_started |
| component-local CSS | `src/components/oracle/oracle-visuals.css` | Does component-local styling create route-specific visual risk? | not_started |
| specificity | global, route, component-local selectors | Does specificity block safe future polish? | not_started |
| token drift | Design Vault vs palette registry vs globals vs route CSS | Are duplicate token vocabularies drifting? | not_started |
| responsive | mobile, touch, height-constrained, wide desktop | Does CSS hold across viewport matrix? | not_started |

Closeout gate:

GO. CSS risk proof is non-mutating.

## 11. Phase G7: Route Visual-Readiness Scoring

### Increment G7.1: Route Scoring Rules

Objective:

Define route visual-readiness scoring and evidence thresholds.

Allowed files:

Plan G docs and closeout.

Forbidden files/actions:

No route edits, no browser run, no screenshot capture, no CSS edits, and no score assignment without evidence.

Expected output:

Route scoring table.

Codex self-checks:

Confirm `route visual-readiness`, `score`, `threshold`, and `NO-GO` appear.

Britton manual verification check:

Confirm weak routes stay blocked.

Stop condition:

Stop if route scores are assigned without evidence.

Rollback or recovery note:

Leave scores `not_started`.

| Score | Threshold | Readiness effect |
| --- | --- | --- |
| `not_started` | No captured evidence or approved review. | NO-GO for readiness claim. |
| `blocked` | Fake proof, missing critical viewport, unsafe CSS risk, or inaccessible state. | NO-GO. |
| `partial` | Some evidence exists but gaps remain visible. | Planning only. |
| `reviewable` | Required targets captured and issues labeled, but acceptance pending. | Manual review required. |
| `accepted` | Required evidence is captured, reviewed, and blockers resolved under later approval. | Can support later gate. |

Route targets:

| Route/surface | Initial score | Reason |
| --- | --- | --- |
| dashboard shell | not_started | No Plan G screenshot capture. |
| chat route | not_started | No Plan G screenshot capture. |
| coding route | not_started | No Plan G screenshot capture and no `/coding` edits. |
| oracle route | not_started | No Plan G screenshot capture. |
| design-demo route | not_started | No Plan G screenshot capture. |

Closeout gate:

GO. Scoring is evidence-based and all current route scores are not_started.

## 12. Phase G8: Not Started/Unavailable Honesty Rules

### Increment G8.1: Honesty Rules

Objective:

Define `not_started`, `unavailable`, `blocked`, `partial`, and `accepted` statuses for visual/CSS proof.

Allowed files:

Plan G docs and closeout.

Forbidden files/actions:

No evidence fabrication, no screenshot claim, no browser claim, no visual pass claim, no CSS proof claim, and no readiness escalation.

Expected output:

Honesty status rules.

Codex self-checks:

Confirm `not_started`, `unavailable`, `blocked`, `partial`, and `accepted` appear.

Britton manual verification check:

Confirm unavailable evidence cannot pass as accepted.

Stop condition:

Stop if missing proof is softened into readiness.

Rollback or recovery note:

Force NO-GO for missing proof.

| Status | Meaning | Passing? |
| --- | --- | --- |
| `not_started` | The proof target exists, but no approved capture/review happened. | No |
| `unavailable` | Evidence cannot be inspected or does not exist. | No |
| `blocked` | Fake proof, unsafe claim, critical gap, or authority drift. | No |
| `partial` | Evidence exists but required coverage is incomplete. | No final pass |
| `accepted` | Evidence exists, is reviewed, and satisfies the threshold under later approval. | Yes for that criterion only |

Fake-proof blocks:

- Placeholder screenshot folders are not screenshots.
- Empty screenshot arrays are not visual pass.
- Not-run match reports are not visual proof.
- Token names are not contrast proof.
- Viewport lists are not screenshot proof.
- Route target lists are not route visual-readiness proof.
- CSS risk maps are not CSS polish approval.

Closeout gate:

GO. Honesty rules are strict.

## 13. Phase G9: Plan G Closeout

### Increment G9.1: Visual/CSS Evidence Decision

Objective:

Decide GO/NO-GO for Plan H.

Allowed files:

Plan G closeout and optional `docs/plan-index.md` note.

Forbidden files/actions:

Standing forbidden set.

Expected output:

Visual/CSS evidence proof readiness decision and next authorized title only.

Codex self-checks:

Run docs diff check, Visual/CSS grep, forbidden-claim grep, focused status, and em dash grep.

Britton manual verification check:

Confirm no CSS edits occurred and no screenshots were fabricated.

Stop condition:

Stop if visual/CSS proof remains target-only when Plan H needs accepted evidence.

Rollback or recovery note:

Request Plan G recovery or separate visual execution approval.

Plan G GO/NO-GO decision gate:

GO for Plan H planning only. Plan G defines screenshot targets, viewport matrix, accessibility smoke checklist, token alignment proof, component relevance proof, CSS risk proof, route visual-readiness scoring, and honesty rules. NO-GO remains for visual proof execution, screenshot capture, browser work, CSS edits, app edits, Source Proxy proof, `/coding` edits, provider/model calls, queues/workers, approval-token actions, apply, git mutation, and final readiness.

Next authorized title only:

8/10: Design Agent + Design System A-Grade Preflight Readiness Plan H: Source Proxy PR-8.3 Alignment
