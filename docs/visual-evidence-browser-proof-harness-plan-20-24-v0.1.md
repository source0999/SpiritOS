# Visual Evidence And Browser Proof Harness Plan 20/24

Status: closed proof-harness contract with visual readiness NO-GO
Plan: Plan 20/24, Visual Evidence And Browser Proof Harness
Mode: NON-CART ONLY UNTIL CART CLEARS

## Scope

Plan 19/24 closed with GO for authority design packet, while keeping token consumption, approved writes, execution, apply, execute-approved, commit, push, branch, worktree, queue/worker execution, provider/model calls, runtime mutation, protected path mutation, and Plan 20 start as NO-GO without explicit operator approval.

The operator then requested the next plan if all good. Plan 19 manual verification passed before this packet started.

This packet records Plan 20 only. It does not start Plan 21/24.

Allowed:
- Route inventory.
- Screenshot contract.
- Responsive proof contract.
- Accessibility, token, and component relevance scoring contract.
- Visual readiness scoring.
- Read-only evidence inspection.

Forbidden:
- Live `/map` work unless Cart clears.
- Browser automation that touches live Cart.
- Hidden browser automation.
- Runtime start.
- Screenshot capture without explicit proof-run approval.
- Final CSS edits.
- App UI, route, component, token, package, config, env, source, runtime, test, generated, cache, protected-path, Source Proxy, Scout, Cartographer, approval-token, queue, worker, provider/model, apply, execute-approved, commit, push, branch, worktree, stash, reset, clean, checkout, or staging mutation.

## Phase 20.1 Route Inventory

### 20.1.1 `/coding`

Allowed work:
- Inventory `/coding` as a non-Cart visual proof candidate.
- Do not edit or run `/coding`.

Evidence:
- `src/app/coding/page.tsx` exists as the `/coding` route.
- `src/components/coding/CodingCommandCenterShell.tsx` contains explicit no-authority copy, including no apply, commit, push, provider, queue, worker, shell, approval-token, or mutation authority.
- Plan 10/24 recorded `/coding` active-task cockpit clarity as GO and no apply/provider/queue/worker/source mutation as NO-GO.

Route inventory:

| Route | Status | Visual proof status | Notes |
| --- | --- | --- | --- |
| `/coding` | `proof_candidate_non_cart` | `not_started` | Needs approved screenshot, responsive, accessibility, and component relevance proof before CSS polish. |

GO / NO-GO:
- GO for `/coding` route inventory.
- NO-GO for `/coding` implementation, browser proof claim, or CSS polish.

Next authorized increment: 20.1.2 dashboard.

### 20.1.2 Dashboard

Allowed work:
- Inventory dashboard as a non-Cart visual proof candidate with Cart widgets excluded.
- Do not edit or run dashboard.

Evidence:
- `src/app/(dashboard)/page.tsx` imports `SpiritDashboardHome`.
- Plan 16/24 records Dashboard as a mixed support hub, eligible only for non-Cart display/support proof.
- Plan 16/24 records Dashboard Cartographer widget action paths as blocked by Cart gate.

Route inventory:

| Route | Status | Visual proof status | Notes |
| --- | --- | --- | --- |
| `/` dashboard | `proof_candidate_non_cart_partial` | `not_started` | Non-Cart dashboard surfaces eligible with proof; Cart widgets and action paths excluded. |

GO / NO-GO:
- GO for dashboard route inventory.
- NO-GO for Cart dashboard controls, dashboard implementation, browser proof claim, or CSS polish.

Next authorized increment: 20.1.3 chat/oracle.

### 20.1.3 Chat/Oracle

Allowed work:
- Inventory `/chat` and `/oracle` as non-Cart visual proof candidates.
- Do not call providers, voice backends, or storage.

Evidence:
- `src/app/chat/page.tsx` identifies `/chat` as Trinity chat workspace.
- `src/app/oracle/page.tsx` identifies `runtimeSurface=oracle`.
- Plan 16/24 records Chat and Oracle as eligible later only with provider/storage or provider/voice/storage proof.

Route inventory:

| Route | Status | Visual proof status | Notes |
| --- | --- | --- | --- |
| `/chat` | `proof_candidate_non_cart` | `not_started` | Needs screenshot and responsive proof; provider/storage behavior remains outside this plan. |
| `/oracle` | `proof_candidate_non_cart` | `not_started` | Needs screenshot and responsive proof; provider/voice/backend behavior remains outside this plan. |

GO / NO-GO:
- GO for chat/oracle route inventory.
- NO-GO for provider calls, voice backend calls, storage mutation, browser proof claim, or CSS polish.

Next authorized increment: 20.1.4 exclude `/map` unless allowed.

### 20.1.4 Exclude `/map` Unless Allowed

Allowed work:
- Exclude `/map` and `/map/raw` from non-Cart visual proof and CSS/preflight.

Evidence:
- Plan 17/24 records `/map`, `/map/raw`, `src/app/map/`, and `/v1/cartographer/*` as `cart_only_excluded_from_non_cart`.
- Plan 17/24 records map is excluded from non-Cart UI polish, broad CSS/preflight, and visual proof unless a later Cart gate explicitly approves exact scope.
- Plan 7/24 records Cart state `blocked`, isolation `isolated`, and activation NO-GO.

Exclusion:

| Route | Status | Visual proof status | Rule |
| --- | --- | --- | --- |
| `/map` | `excluded_cart_only` | `blocked_by_cart_gate` | Excluded from Plan 20 visual proof. |
| `/map/raw` | `excluded_cart_only` | `blocked_by_cart_gate` | Excluded from Plan 20 visual proof. |

GO / NO-GO:
- GO for `/map` exclusion.
- NO-GO for live map proof, Cart visual proof, Cart UI work, or broad CSS/preflight including `/map`.

## Phase 20.1 Review

Completed increments:
- 20.1.1 GO for `/coding` inventory; NO-GO for `/coding` implementation or proof claim.
- 20.1.2 GO for dashboard inventory; NO-GO for Cart dashboard controls or proof claim.
- 20.1.3 GO for chat/oracle inventory; NO-GO for provider/voice/storage work or proof claim.
- 20.1.4 GO for `/map` exclusion; NO-GO for Cart visual proof.

Evidence exists:
- Route files were inventoried read-only.
- Plan 16 ownership constraints are recorded.
- Plan 17 `/map` exclusion evidence is recorded.
- Plan 7 Cart blocked/isolated evidence is recorded.

Forbidden scope avoided:
- No browser automation, screenshot capture, route edit, UI edit, CSS edit, runtime start, provider call, storage write, Cart work, or git mutation occurred.

Checks:
- Read-only route inventory and grep checks returned expected route, Cart exclusion, visual proof, not_started, and NO-GO evidence.

Phase result: GO to Phase 20.2; NO-GO for screenshot proof execution.

Next authorized increment: 20.2.1 Screenshot evidence.

## Phase 20.2 Visual Proof Contract

### 20.2.1 Screenshot Evidence

Allowed work:
- Define screenshot evidence contract.
- Do not capture screenshots in Plan 20.

Evidence:
- Roadmap Plan 20 requires screenshot evidence before final CSS polish.
- Existing Design Agent Plan 20 evidence records Visual/CSS evidence proof as unavailable or not_started.
- This Plan 20 did not start a runtime or browser and did not capture screenshots.

Screenshot evidence contract:

| Field | Required | Meaning |
| --- | --- | --- |
| `route` | yes | Exact route. |
| `viewport` | yes | Exact viewport size. |
| `theme_state` | yes | Light/dark/system or fixed theme. |
| `auth_state` | yes | Auth/demo state used. |
| `screenshot_path` | yes | Evidence file path if captured. |
| `captured_at` | yes | Timestamp if captured. |
| `capture_command` | yes | Command used, if approved. |
| `cart_excluded` | yes | Must be true for non-Cart proof runs. |
| `overlap_check` | yes | Text and UI overlap result. |
| `blank_screen_check` | yes | Nonblank route result. |
| `proof_status` | yes | `not_started`, `captured`, `blocked`, or `failed`. |

Plan 20 screenshot status:

| Route | Screenshot proof |
| --- | --- |
| `/coding` | `not_started` |
| `/` dashboard non-Cart | `not_started` |
| `/chat` | `not_started` |
| `/oracle` | `not_started` |
| `/map` | `blocked_by_cart_gate` |
| `/map/raw` | `blocked_by_cart_gate` |

GO / NO-GO:
- GO for screenshot evidence contract.
- NO-GO for claiming screenshot proof exists.

Next authorized increment: 20.2.2 Responsive evidence.

### 20.2.2 Responsive Evidence

Allowed work:
- Define responsive evidence contract.
- Do not run browser or device proof.

Evidence:
- Roadmap Plan 20 requires responsive proof before final CSS polish.
- No viewport screenshot or browser proof was executed in this plan.

Responsive evidence contract:

| Field | Required | Meaning |
| --- | --- | --- |
| `route` | yes | Exact route. |
| `viewport_set` | yes | Required set: mobile, tablet, desktop. |
| `mobile_result` | yes | Pass/fail/not_started. |
| `tablet_result` | yes | Pass/fail/not_started. |
| `desktop_result` | yes | Pass/fail/not_started. |
| `horizontal_overflow` | yes | Pass/fail/not_started. |
| `text_overlap` | yes | Pass/fail/not_started. |
| `control_reachability` | yes | Pass/fail/not_started. |
| `proof_status` | yes | `not_started`, `captured`, `blocked`, or `failed`. |

Plan 20 responsive status:

| Route | Responsive proof |
| --- | --- |
| `/coding` | `not_started` |
| `/` dashboard non-Cart | `not_started` |
| `/chat` | `not_started` |
| `/oracle` | `not_started` |
| `/map` | `blocked_by_cart_gate` |
| `/map/raw` | `blocked_by_cart_gate` |

GO / NO-GO:
- GO for responsive evidence contract.
- NO-GO for claiming responsive proof exists.

Next authorized increment: 20.2.3 Accessibility/token/component relevance.

### 20.2.3 Accessibility/Token/Component Relevance

Allowed work:
- Define accessibility, token, and component relevance scoring contract.
- Do not edit CSS, tokens, or components.

Evidence:
- Design Agent ecosystem evidence records Visual/CSS evidence proof as unavailable or not_started.
- Plan 12 records visual proof and Source Proxy receive/display/score proof as required before final readiness.
- Plan 13 records Visual/CSS proof as `not_started`.

Relevance scoring contract:

| Field | Required | Meaning |
| --- | --- | --- |
| `route` | yes | Exact route. |
| `accessibility_status` | yes | `not_started`, `pass`, `fail`, or `blocked`. |
| `keyboard_status` | yes | `not_started`, `pass`, `fail`, or `blocked`. |
| `contrast_status` | yes | `not_started`, `pass`, `fail`, or `blocked`. |
| `token_relevance` | yes | Token/CSS relevance notes without edits. |
| `component_relevance` | yes | Component relevance notes without edits. |
| `css_scope_risk` | yes | Whether future CSS scope is route-specific or broad. |
| `cart_exclusion_confirmed` | yes | Must be true for non-Cart proof. |

GO / NO-GO:
- GO for accessibility/token/component relevance contract.
- NO-GO for CSS edits, token edits, component edits, or relevance-as-proof claims.

## Phase 20.2 Review

Completed increments:
- 20.2.1 GO for screenshot evidence contract; NO-GO for screenshot proof claim.
- 20.2.2 GO for responsive evidence contract; NO-GO for responsive proof claim.
- 20.2.3 GO for accessibility/token/component relevance contract; NO-GO for CSS/token/component edits.

Evidence exists:
- Screenshot proof requirements are recorded.
- Responsive proof requirements are recorded.
- Accessibility/token/component relevance requirements are recorded.
- Existing Visual/CSS `not_started` blockers are recorded.

Forbidden scope avoided:
- No browser, screenshot, runtime, CSS, token, component, route, source, provider, queue, worker, approval-token, apply, git, or Cart action occurred.

Checks:
- Read-only grep checks returned expected screenshot, responsive, accessibility, token, component relevance, Visual/CSS not_started, and NO-GO evidence.

Phase result: GO to Phase 20.3; NO-GO for visual readiness claim.

Next authorized increment: 20.3.1 Route score.

## Phase 20.3 Readiness Scoring

### 20.3.1 Route Score

Allowed work:
- Score route visual readiness honestly from existing evidence.

Route score:

| Route | Inventory | Screenshot | Responsive | Accessibility/token/component | Score | Result |
| --- | --- | --- | --- | --- | --- | --- |
| `/coding` | present | `not_started` | `not_started` | `not_started` | 1/4 | `not_ready_visual_proof_missing` |
| `/` dashboard non-Cart | present | `not_started` | `not_started` | `not_started` | 1/4 | `not_ready_visual_proof_missing` |
| `/chat` | present | `not_started` | `not_started` | `not_started` | 1/4 | `not_ready_visual_proof_missing` |
| `/oracle` | present | `not_started` | `not_started` | `not_started` | 1/4 | `not_ready_visual_proof_missing` |
| `/map` | excluded | `blocked_by_cart_gate` | `blocked_by_cart_gate` | `blocked_by_cart_gate` | 0/4 | `excluded_cart_only` |
| `/map/raw` | excluded | `blocked_by_cart_gate` | `blocked_by_cart_gate` | `blocked_by_cart_gate` | 0/4 | `excluded_cart_only` |

GO / NO-GO:
- GO for route scoring.
- NO-GO for treating any route as visually ready.

Next authorized increment: 20.3.2 Blocker score.

### 20.3.2 Blocker Score

Allowed work:
- Score blockers for final CSS polish readiness.

Blocker score:

| Blocker | Status | Impact |
| --- | --- | --- |
| Screenshot proof | `not_started` | Blocks final CSS polish. |
| Responsive proof | `not_started` | Blocks final CSS polish. |
| Accessibility/token/component relevance | `not_started` | Blocks final CSS polish. |
| `/map` Cart gate | `blocked_by_cart_gate` | Excludes map from non-Cart work. |
| Browser proof run | `not_started` | Blocks visual readiness. |
| CSS scope approval | `not_approved` | Blocks Plan 21 patching. |
| Final visual readiness | `NO-GO` | No route has proof. |

GO / NO-GO:
- GO for blocker scoring.
- NO-GO for CSS polish, broad visual readiness, or Plan 21 implementation.

Next authorized increment: 20.3.3 Final visual GO/NO-GO.

### 20.3.3 Final Visual GO/NO-GO

Allowed work:
- Record final visual readiness decision.
- Name next roadmap plan only.

Decision:
- Visual proof harness contract: `GO`
- Route inventory: `GO`
- `/map` exclusion: `GO`
- Screenshot proof execution: `NO-GO`
- Responsive proof execution: `NO-GO`
- Accessibility/token/component proof execution: `NO-GO`
- Any route visually ready: `NO-GO`
- Final CSS polish readiness: `NO-GO`
- Plan 21 start: `NO-GO without explicit operator approval`

Next roadmap plan:

`Plan 21/24: Final CSS Polish Gate`

GO / NO-GO:
- GO for visual proof harness contract and readiness scoring.
- NO-GO for final visual readiness, CSS polish, or starting Plan 21 without explicit operator approval.

Next authorized increment: Plan 20/24 closeout.

## Phase 20.3 Review

Completed increments:
- 20.3.1 GO for route scoring; NO-GO for visually ready route claim.
- 20.3.2 GO for blocker scoring; NO-GO for CSS polish readiness.
- 20.3.3 GO for final visual GO/NO-GO; NO-GO for Plan 21 start.

Evidence exists:
- Route inventory and exclusion evidence is recorded.
- Screenshot, responsive, accessibility/token/component contracts are recorded.
- Visual readiness and blocker scores are recorded.

Forbidden scope avoided:
- No screenshots, browser proof, CSS edits, UI edits, route edits, runtime starts, provider/model calls, queue/worker execution, approval-token actions, apply, execute-approved, commit, push, branch, worktree, protected-path mutation, or Cart work occurred.

Checks:
- Read-only grep checks returned expected route score, blocker score, excluded map status, not_started proof fields, NO-GO readiness, and Plan 21 title.

Phase result: GO to Plan 20 closeout; NO-GO for Plan 21 start.

Next authorized increment: Plan 20/24 closeout.

## Plan 20/24 Closeout

Phase review:
- Phase 20.1 Route Inventory: GO for `/coding`, dashboard, chat/oracle inventory and `/map` exclusion; NO-GO for proof execution.
- Phase 20.2 Visual Proof Contract: GO for screenshot, responsive, accessibility/token/component contracts; NO-GO for claiming proof exists.
- Phase 20.3 Readiness Scoring: GO for route and blocker scoring; NO-GO for visual readiness or CSS polish.

Increment evidence:
- 20.1.1 `/coding`: inventory recorded; proof `not_started`.
- 20.1.2 dashboard: inventory recorded; proof `not_started`; Cart widgets excluded.
- 20.1.3 chat/oracle: inventory recorded; proof `not_started`.
- 20.1.4 `/map`: excluded as Cart-only and blocked by Cart gate.
- 20.2.1 screenshot contract: recorded; execution `not_started`.
- 20.2.2 responsive contract: recorded; execution `not_started`.
- 20.2.3 accessibility/token/component relevance contract: recorded; execution `not_started`.
- 20.3.1 route score: no route visually ready.
- 20.3.2 blocker score: final CSS polish blocked.
- 20.3.3 final visual GO/NO-GO: contract GO; readiness NO-GO.

Evidence exists:
- `src/app/coding/page.tsx`
- `src/components/coding/CodingCommandCenterShell.tsx`
- `src/app/(dashboard)/page.tsx`
- `src/app/chat/page.tsx`
- `src/app/oracle/page.tsx`
- `docs/surface-ownership-chat-oracle-dashboard-plan-16-24-v0.1.md`
- `docs/map-cartographer-ui-integration-gate-plan-17-24-v0.1.md`
- `docs/design-agent-ecosystem-plan-20-closeout-v0.1.md`
- `docs/design-agent-ecosystem-plan-20-full-design-agent-ecosystem-production-daily-use-preflight-css-polish-readiness-gate-v0.1.md`

Forbidden actions review:
- No `/map` proof or live Cart work occurred.
- No browser automation was run.
- No screenshot was captured.
- No runtime was started.
- No CSS, token, component, UI, route, source, package, config, env, generated, cache, or protected path was edited.
- No provider/model call, queue/worker execution, approval-token action, apply, execute-approved, commit, push, branch, worktree, stash, reset, clean, checkout, or staging occurred.
- No Plan 21 work started.

Visual readiness score:

| Category | Score | Result |
| --- | --- | --- |
| Route inventory | 4/4 non-Cart candidates inventoried | `GO` |
| `/map` exclusion | 2/2 Cart routes excluded | `GO` |
| Screenshot proof | 0/4 non-Cart candidates captured | `NO-GO` |
| Responsive proof | 0/4 non-Cart candidates proven | `NO-GO` |
| Accessibility/token/component relevance | 0/4 non-Cart candidates proven | `NO-GO` |
| Final visual readiness | 0/4 non-Cart candidates ready | `NO-GO` |

Final Plan 20/24 result: GO for visual proof harness contract, route inventory, `/map` exclusion, and honest readiness scoring; NO-GO for screenshot proof, responsive proof, accessibility/token/component proof, final visual readiness, CSS polish, or Plan 21 start without explicit operator approval.

Next roadmap plan only: `Plan 21/24: Final CSS Polish Gate`.

## Manual Verification

Copy-paste verification:

```bash
cd /home/source/SpiritOS && git status --branch --short --untracked-files=normal && grep -nE "Plan 20/24|/coding|dashboard|chat/oracle|exclude /map|Screenshot evidence|Responsive evidence|Accessibility/token/component|Route score|Blocker score|Visual readiness score|not_started|blocked_by_cart_gate|NO-GO|Plan 21/24" docs/visual-evidence-browser-proof-harness-plan-20-24-v0.1.md && grep -nE "Trinity chat workspace|runtimeSurface=oracle|SpiritDashboardHome|cart_only_excluded_from_non_cart|Visual/CSS evidence proof is unavailable or not_started|Source Proxy receive/display/score proof is not_started|NO-GO|No browser proof|No screenshot" src/app/chat/page.tsx src/app/oracle/page.tsx 'src/app/(dashboard)/page.tsx' docs/map-cartographer-ui-integration-gate-plan-17-24-v0.1.md docs/design-agent-ecosystem-plan-20-closeout-v0.1.md docs/design-agent-ecosystem-plan-20-full-design-agent-ecosystem-production-daily-use-preflight-css-polish-readiness-gate-v0.1.md docs/design-agent-design-system-a-grade-preflight-readiness-plan-e-source-proxy-read-only-integration-proof-v0.1.md && git diff --check -- docs/visual-evidence-browser-proof-harness-plan-20-24-v0.1.md
```

Expected output:
- Git status shows the existing untracked plan docs, including this Plan 20 packet.
- Plan 20 grep prints route inventory, `/map` exclusion, screenshot/responsive/accessibility contracts, route and blocker scores, not_started proof fields, NO-GO readiness, and Plan 21 title.
- Evidence grep prints chat, oracle, dashboard, Cart `/map` exclusion, Visual/CSS not_started blockers, Source Proxy receive/display/score not_started blocker, and no-browser/no-screenshot proof boundaries.
- `git diff --check` prints no output.
