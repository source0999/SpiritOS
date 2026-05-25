# Design Agent Ecosystem Plan 17 of 21: Visual/CSS Evidence Harness Readiness v0.1

Status: Proposed docs-only visual/CSS evidence harness readiness plan complete

Date: 2026-05-24

Lane: Design Agent Ecosystem diagnostics

## 1. Purpose

This Plan 17 document defines visual/CSS evidence harness readiness fields, responsive and mobile criteria, accessibility criteria, token-alignment criteria, evidence honesty rules, and future execution prerequisites before any approved browser run, screenshot capture, Playwright install, pixel comparison, baseline write, visual evidence file write, app UI edit, route edit, component edit, CSS edit, token edit, Source Proxy proof, provider/model call, queue/worker execution, approval-token action, apply, execute-approved, git action, or hidden autonomy exists in this lane.

This plan follows Design Agent Ecosystem Plan 16 of 21, which planned a 100-prompt Design And Proxy Integration Diagnostic but did not run prompts, obtain Source Proxy owner-confirmed execution, call providers/models, execute queues/workers, run Source Proxy proof, edit `/coding`, or produce visual/CSS results.

This is docs-only readiness planning. It does not run browsers, install Playwright, capture screenshots, compare pixels, write baselines, write visual evidence files, create routes, set up Storybook, edit app UI, edit components, edit styles, edit CSS, edit tokens, edit Source Proxy, edit `/coding`, fetch URLs, crawl, call Figma APIs, process images, call providers or models, run queues or workers, consume approval tokens, apply changes, execute approved changes, commit, push, create branches or worktrees, stash, reset, clean, checkout, self-approve, or create hidden autonomy.

Plan 17 grants no runtime authority.

Plan 17 grants no visual execution authority.

Plan 17 grants no screenshot capture authority.

Plan 17 grants no browser automation or Playwright install authority.

Plan 17 grants no pixel diff, baseline write, or visual evidence file write authority.

Plan 17 grants no CSS edits.

Plan 17 grants no token edits.

Plan 17 grants no Source Proxy integration implementation or Source Proxy proof authority.

Plan 17 grants no `/coding`, app UI, route, component, style, package, config, auth, env, or protected-path edit authority.

Plan 17 grants no provider/model, queue, worker, approval-token, apply, execute-approved, commit, push, branch/worktree, stash, reset, clean, checkout, self-approval, or background autonomy authority.

## 2. Evidence Reviewed

- `docs/design-agent-ecosystem-integration-diagnostic-master-plan-v0.1.md`: defines Plan 17 as Visual/CSS Evidence Harness Readiness with separate approval required for any visual execution plan.
- `docs/design-agent-ecosystem-plan-8-visual-verification-diagnostic-v0.1.md`: defines visual evidence honesty, fake-proof traps, viewport criteria, accessibility criteria, and no-execution boundaries.
- `docs/design-agent-ecosystem-plan-16-100-prompt-design-and-proxy-integration-diagnostic-v0.1.md`: records visual_evidence_quality and css_component_relevance as not_started until a separately approved evidence method exists.
- `docs/design-agent-ecosystem-plan-16-closeout-v0.1.md`: records GO only for this docs-only Visual/CSS Evidence Harness Readiness plan.
- `data/design-vault/packs/internal-dashboard-demo-v4/README.md`: records screenshot folders as placeholders and visual match report as not run.
- `data/design-vault/packs/internal-dashboard-demo-v4/match-report.json`: records `status` as `not-run`, no reference screenshots, no generated screenshots, no compared pairs, and no blocking visual threshold.

## 3. Current Boundary Facts

- Visual evidence remains scaffold-only.
- Screenshots are not captured.
- Browser automation is not_started.
- Playwright install and execution are not_started.
- Pixel comparison and baseline generation are not_started.
- Accessibility measurement is not_started.
- CSS/component relevance proof is not_started.
- Token alignment proof is docs-only criteria, not token editing.
- Current `match-report.json` is not-run and cannot be treated as visual proof.
- Any future visual execution requires separate Britton approval for exact files/actions, forbidden files/actions, commands, evidence paths, stop conditions, and GO/NO-GO gate.

## 4. Evidence Schema Readiness

Required future evidence fields:

| Field | Required meaning | Current status |
| --- | --- | --- |
| `pack_id` | Binds evidence to a Design Vault pack. | planned |
| `source_card_id` | Binds evidence to approved provenance. | planned |
| `target_surface` | Names exact route, component, or preview surface under later approval. | not_started |
| `viewport_set` | Lists mobile, tablet, desktop, wide desktop, and height-constrained targets. | planned |
| `state_set` | Lists loading, empty, error, default, active, hover, focus, disabled, and dense-data states. | planned |
| `reference_screenshots` | Lists approved reference screenshot paths after capture. | unavailable |
| `generated_screenshots` | Lists generated screenshot paths after capture. | unavailable |
| `compared_pairs` | Lists reference/generated comparisons after approved run. | not_started |
| `visual_evidence_quality` | Grades completeness and trustworthiness of visual evidence. | not_started |
| `css_component_relevance` | Scores whether visual evidence supports CSS/component decisions. | not_started |
| `accessibility_evidence` | Records contrast, focus, keyboard, touch, motion, and text-scale checks. | not_started |
| `token_alignment_evidence` | Records token usage and mismatch notes without token edits. | planned |
| `proof_status` | Distinguishes planned, unavailable, not_started, captured, compared, pass, fail, and blocked. | planned |

Expected evidence-schema counts:

| Count | Expected |
| --- | --- |
| planned_count | 6 |
| unavailable_count | 2 |
| not_started_count | 5 |
| blocked_count | 0 |
| unsafe_count | 0 |

## 5. Responsive And Mobile Criteria

Future visual/CSS readiness requires coverage for:

- mobile narrow viewport.
- mobile touch target and text-fit states.
- tablet viewport.
- desktop viewport.
- wide desktop viewport.
- height-constrained viewport.
- dense data state.
- loading, empty, error, active, focus, disabled, and overflow states.

Readiness rules:

- A viewport checklist is planning evidence only until screenshots are captured in a separately approved visual run.
- Desktop-only evidence cannot support daily-use CSS readiness.
- Hover-only evidence cannot support touch or keyboard readiness.
- Text fit, clipping, overlap, fixed-format UI dimensions, and state visibility must be verified with actual evidence before any visual pass claim.
- Missing route, component, pack, source-card, viewport, or state binding blocks visual readiness claims.

## 6. Accessibility And Token Criteria

Future visual/CSS readiness requires criteria for:

- contrast evidence.
- focus visibility.
- keyboard path.
- touch target size.
- reduced motion behavior.
- text scale behavior.
- semantic status/state visibility.
- token-to-surface alignment.
- token mismatch notes.
- component-state coverage.

Readiness rules:

- Token names alone are not contrast proof.
- Theme aliases are not CSS polish approval.
- Token alignment evidence is advisory until measured or reviewed under a later approved method.
- Any token edit, CSS edit, or production import remains blocked in this plan.
- Accessibility and token criteria can identify missing evidence, but cannot claim pass without approved measurement or review evidence.

## 7. Fake-Proof And Stop Condition Matrix

| Scenario | Expected status | Required handling |
| --- | --- | --- |
| Placeholder screenshot folder is treated as captured evidence. | `blocked` | Block fake screenshot evidence. |
| Empty screenshot arrays are treated as visual pass. | `blocked` | Block visual pass claim. |
| Not-run match report is treated as proof. | `blocked` | Label visual proof not_started. |
| Token names are treated as contrast evidence. | `blocked` | Require measured or approved review evidence. |
| Viewport checklist is treated as screenshot proof. | `blocked` | Preserve planning-only label. |
| User asks to run Playwright now. | `blocked` | Require separate visual execution approval. |
| User asks to edit CSS based on planned criteria. | `blocked` | Preserve no CSS edits. |
| User asks to write baselines or update match-report files. | `blocked` | Preserve no baseline or visual evidence writes. |
| User asks for daily-use readiness from scaffold evidence. | `blocked` | Block readiness escalation. |
| Report keeps all missing evidence and not_started fields visible. | `ready` | Accept as docs-only readiness evidence. |

Expected fake-proof counts:

| Count | Expected |
| --- | --- |
| ready_count | 1 |
| blocked_count | 9 |
| unsafe_count | 0 |
| unavailable_count | 0 |
| not_started_count | 0 |

## 8. Current Docs/Evidence Grade

This report grades visual/CSS evidence harness readiness planning, not visual execution.

| Area | Evidence field clarity | Responsive criteria | Accessibility criteria | Token criteria | Evidence honesty | Final grade | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Visual/CSS evidence harness readiness | B | B | B | B | A | B | GO for Plan 18 docs-only Controlled Design-Code Preview Lane planning only |

Grade notes:

- Visual/CSS evidence harness readiness earns B because evidence fields, responsive/mobile criteria, accessibility criteria, token-alignment criteria, fake-proof traps, and execution prerequisites are explicit.
- It does not earn A because no browser run, screenshot capture, Playwright install, baseline write, pixel comparison, accessibility measurement, CSS/component proof, token proof, app implementation, or CSS implementation has been approved or run.
- Evidence honesty is A because screenshots, compared pairs, visual pass, accessibility proof, CSS/component relevance, and token alignment proof remain unavailable or not_started where evidence is absent.

## 9. Inert Report Fixture

```yaml
report_id: design-agent-plan-17-visual-css-evidence-harness-readiness-v0.1
plan_position: "Plan 17 of 21 listed plans"
scope: docs-only visual/CSS evidence harness readiness
authority:
  statement: >
    This report grants no runtime authority, no visual execution authority, no
    screenshot capture authority, no browser automation, no Playwright install,
    no pixel diff, no baseline writes, no visual evidence file writes, no CSS
    edits, no token edits, no Source Proxy integration implementation, no
    Source Proxy proof, no /coding edits, no app UI edits, no route edits, no
    component edits, no provider/model calls, no queue/worker execution, no
    approval-token action, no apply, no execute-approved, no commit, no push,
    no branch/worktree, no stash, no reset, no clean, no checkout, no
    self-approval, and no hidden autonomy.
current_evidence:
  match_report_status: not-run
  reference_screenshots: 0
  generated_screenshots: 0
  compared_pairs: 0
  visual_evidence_quality: not_started
  css_component_relevance: not_started
  accessibility_evidence: not_started
  token_alignment_evidence: planned
readiness_counts:
  planned_count: 6
  unavailable_count: 2
  not_started_count: 5
  blocked_count: 9
  unsafe_count: 0
decision:
  value: GO
  reason: GO only for Plan 18 docs-only Controlled Design-Code Preview Lane planning.
```

## 10. Failure Caps

Any of these caps forces NO-GO:

- Placeholder folders, empty screenshot arrays, not-run match reports, token names, notes, checklists, or planned fields are treated as visual proof.
- Any screenshot, browser result, contrast result, accessibility result, match score, baseline, pixel comparison, CSS/component relevance proof, or production readiness claim is fabricated.
- Any browser automation, screenshot capture, Playwright install, pixel diff, baseline write, visual evidence file write, app UI write, route write, component write, CSS edit, token edit, Source Proxy action, `/coding` action, provider/model call, queue/worker execution, approval-token action, apply, execute-approved, commit, push, branch/worktree, stash, reset, clean, checkout, self-approval, or hidden autonomy is suggested or approved.
- Missing screenshots, missing compared pairs, missing viewport coverage, missing responsive evidence, missing accessibility evidence, missing token alignment evidence, missing source-card binding, or not_started visual verification is hidden.

## 11. Handoff To Plan 18

Plan 18 should use these findings:

- Visual/CSS evidence harness requirements are planned but not executed.
- Current screenshot evidence is unavailable.
- Current match report is not-run.
- Visual_evidence_quality and css_component_relevance remain not_started.
- Accessibility and token-alignment criteria are planned but not measured.
- Any controlled preview lane must preserve approval separation and cannot treat preview planning as apply authority.
- Plan 18 must preserve no production CSS polish, no apply, no execute-approved, no approval-token consumption, no provider/model calls, no queue/worker execution, no git mutation, and no hidden autonomy.

## 12. Self-Check Commands

```bash
git diff --check -- \
  docs/design-agent-ecosystem-plan-17-visual-css-evidence-harness-readiness-v0.1.md \
  docs/design-agent-ecosystem-plan-17-closeout-v0.1.md \
  docs/plan-index.md

grep -nE "Plan 17 of 21|Visual/CSS Evidence Harness Readiness|evidence schema|responsive|mobile|accessibility|token alignment|screenshot|viewport|match report|not-run|not_started|unavailable|visual_evidence_quality|css_component_relevance|Playwright|baseline|blocked_count|unsafe_count|Final grade|no runtime authority|no visual execution authority|no screenshots|no CSS edits|GO/NO-GO|NO-GO" \
  docs/design-agent-ecosystem-plan-17-visual-css-evidence-harness-readiness-v0.1.md \
  docs/design-agent-ecosystem-plan-17-closeout-v0.1.md

LC_ALL=C grep -n "$(printf '\342\200\224')" \
  docs/design-agent-ecosystem-plan-17-visual-css-evidence-harness-readiness-v0.1.md \
  docs/design-agent-ecosystem-plan-17-closeout-v0.1.md \
  docs/plan-index.md 2>/dev/null || true

git status --branch --short --untracked-files=normal -- \
  docs/design-agent-ecosystem-plan-17-visual-css-evidence-harness-readiness-v0.1.md \
  docs/design-agent-ecosystem-plan-17-closeout-v0.1.md \
  docs/plan-index.md
```

Expected:

- `git diff --check` prints no whitespace errors.
- Required plan title, evidence schema, responsive/mobile, accessibility, token alignment, screenshot, viewport, match report, not-run, not_started, unavailable, visual_evidence_quality, css_component_relevance, Playwright, baseline, counts, grade, GO/NO-GO, and boundary phrases are present.
- Em dash grep prints no lines.
- Focused status shows only the Plan 17 docs and `docs/plan-index.md` as created or changed for this increment.

## 13. Manual Check Block For Britton

```bash
cd /home/source/SpiritOS

git diff --check -- \
  docs/design-agent-ecosystem-plan-17-visual-css-evidence-harness-readiness-v0.1.md \
  docs/design-agent-ecosystem-plan-17-closeout-v0.1.md \
  docs/plan-index.md

grep -nE "Plan 17 of 21|Visual/CSS Evidence Harness Readiness|evidence schema|responsive|mobile|accessibility|token alignment|screenshot|viewport|match report|not-run|not_started|unavailable|visual_evidence_quality|css_component_relevance|Playwright|baseline|blocked_count|unsafe_count|Final grade|no runtime authority|no visual execution authority|no screenshots|no CSS edits|GO/NO-GO|NO-GO" \
  docs/design-agent-ecosystem-plan-17-visual-css-evidence-harness-readiness-v0.1.md \
  docs/design-agent-ecosystem-plan-17-closeout-v0.1.md

LC_ALL=C grep -n "$(printf '\342\200\224')" \
  docs/design-agent-ecosystem-plan-17-visual-css-evidence-harness-readiness-v0.1.md \
  docs/design-agent-ecosystem-plan-17-closeout-v0.1.md \
  docs/plan-index.md 2>/dev/null || true

git status --branch --short --untracked-files=normal -- \
  docs/design-agent-ecosystem-plan-17-visual-css-evidence-harness-readiness-v0.1.md \
  docs/design-agent-ecosystem-plan-17-closeout-v0.1.md \
  docs/plan-index.md
```

## 14. Expected Output

- `git diff --check` prints no whitespace errors.
- Grep prints matching lines for Plan 17 of 21, Visual/CSS Evidence Harness Readiness, evidence schema, responsive, mobile, accessibility, token alignment, screenshot, viewport, match report, not-run, not_started, unavailable, visual_evidence_quality, css_component_relevance, Playwright, baseline, blocked_count, unsafe_count, Final grade, no runtime authority, no visual execution authority, no screenshots, no CSS edits, GO/NO-GO, and NO-GO.
- Em dash grep prints no lines.
- Focused status shows:
  - `?? docs/design-agent-ecosystem-plan-17-visual-css-evidence-harness-readiness-v0.1.md`
  - `?? docs/design-agent-ecosystem-plan-17-closeout-v0.1.md`
  - `M docs/plan-index.md`

## 15. GO/NO-GO Exit Gate

GO if:

- Visual/CSS evidence harness readiness earns at least B for current docs/evidence readiness.
- Evidence schema, responsive/mobile criteria, accessibility criteria, token-alignment criteria, fake-proof traps, and not_started execution prerequisites are explicit.
- Current screenshot and match-report limitations are visible.
- No wording grants visual execution, screenshot capture, browser automation, Playwright install, baseline writes, CSS edits, token edits, Source Proxy proof, provider/model, queue/worker, `/coding`, app UI, route, component, approval-token, apply, execute-approved, commit, push, branch/worktree, stash, reset, clean, checkout, self-approval, or hidden autonomy authority.

NO-GO if:

- Any unavailable, not-run, scaffold-only, planned, or checklist evidence is treated as visual proof.
- Any visual result, accessibility result, CSS/component relevance result, token proof, or production readiness claim is fabricated.
- Any screenshot capture, browser automation, Playwright install, baseline write, visual evidence write, CSS edit, token edit, Source Proxy action, `/coding` action, provider/model call, queue/worker execution, approval-token action, apply, execute-approved, commit, push, branch/worktree, stash, reset, clean, checkout, self-approval, or hidden autonomy is suggested or approved.

Exit decision:

- GO for Design Agent Ecosystem Plan 18 of 21: Controlled Design-Code Preview Lane.
- NO-GO for implementation.
- NO-GO for visual execution.
- NO-GO for screenshot capture, browser automation, Playwright install, pixel diff, baseline write, visual evidence file write, app UI edit, route edit, component edit, CSS edit, token edit, Source Proxy proof, provider/model call, queue/worker execution, approval-token action, apply, execute-approved, commit, push, branch/worktree, stash, reset, clean, checkout, self-approval, or hidden autonomy.

## 16. Next Plan Title

Design Agent Ecosystem Plan 18 of 21: Controlled Design-Code Preview Lane
