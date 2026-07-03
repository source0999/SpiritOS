# Source Proxy Design Studio Real Integration Pivot — Master Plan

**Pivot folder:**
`docs/source-proxy-design-studio-real-integration-pivot-20260702/`

**Status:** `PLAN_WRITTEN_NOT_STARTED`
**Implementation performed:** `false`
**Runtime code modified:** `false`
**GO claimed:** `false`
**Owner:** Britton
**Date:** 2026-07-02
**Purpose:** Replace the fake Plan 14 preview-contract completion path with a real `/coding` Design Studio implementation ladder.

This pivot exists because the prior Design Studio implementation path produced planning artifacts, preview stubs, source-text tests, and status rollups without proving the actual product path Britton uses. The new pivot treats that work as historical preview scaffolding only.

No Graphify, engraph, LlamaIndex, Neo4j ingestion, memory graph, graph database, or new external infra is part of this pivot. Memory/graph tooling is deferred to a separate future experiment after this pivot reaches proven GO.

---

## 1. Problem Statement

The current Design Studio state is not a production product lane. The audited failures are:

- `src/app/v1/coding/design-studio/preview/route.ts` is a hardcoded advisory stub.
- `DesignStudioShell` renders static copy and does not call the preview route.
- `execute-approved` is unrelated to Design Studio.
- Design packets, DesignDNA, coder packets, and critic packets are hardcoded/advisory.
- No model/provider/subagent lane is invoked or consumed.
- No sandbox apply path exists for Design Studio.
- No desktop/mobile screenshot artifact is produced, hashed, or consumed.
- Anti-template/originality checks inspect caller-supplied text rather than rendered output.
- Design critic and bounded repair are advisory or missing.
- Approved Obsidian writeback has a helper but no production importer.
- The writeback test suite currently has an inherited red baseline: 8 pass / 2 fail.
- Old Plan 14 claims GO from docs/status/test existence rather than runtime invocation, downstream consumption, failure-changing verdicts, and acceptance gating.

The honest current status is:

`PREVIEW_CONTRACT_SCAFFOLD_EXISTS_RUNTIME_INTEGRATION_NOT_PERFORMED`

---

## 2. Supersession Note

The old pivot folder:

`docs/source-proxy-design-studio-implementation-pivot-20260701/`

is deprecated as current source of truth (see `DEPRECATED.md` there). It remains historical evidence only.

The active planning source is now:

`docs/source-proxy-design-studio-real-integration-pivot-20260702/`

The old Plan 14 GO claim must not be treated as active truth. Any future implementation must start from this pivot's execution protocol, not the old Plan 14 status.

---

## 3. Apply-Path Authority Map

There is exactly one canonical Design Studio apply path in this pivot:

`/coding Design Studio task -> design/coder packet -> Design Studio sandbox apply -> /coding/design-demo only`

`src/app/v1/actions/execute-approved/route.ts` is **out of scope** for this Design Studio pivot.

Rules:

- `execute-approved` must not be reused, wrapped, shadowed, or partially integrated for Design Studio unless Britton approves a separate future seam-decision plan.
- Design Studio output must not flow through both the new sandbox apply path and `execute-approved`.
- Any second apply path is `FAIL_PARALLEL_ROUTE_CONFUSION`.
- Any production route apply is forbidden.
- The only allowed design-output mutation target is `/coding/design-demo`.
- The sandbox apply path must be traceable, reversible, and scoped to files explicitly named by the plan increment.

---

## 4. BLOCKED_ENV Ceiling

If no provider/model lane is reachable in the current environment, the best honest terminal state of this pivot is:

`BLOCKED_ENV`

not:

`GO_FULLY_INTEGRATED`

Codex must not grind, invent, mock, hardcode, or route around provider absence to manufacture GO. Provider absence is a real blocker, not a prompt-engineering problem.

---

## 5. Execution Protocol

This is the non-negotiable workflow for future implementation.

Codex must work one increment at a time.

Codex must not start the next increment until the current increment has a green receipt.

Codex must not batch multiple increments and test later.

Any red check blocks forward progress.

Any missing artifact path blocks forward progress.

Any missing trace ID blocks forward progress.

Any backend-only proof blocks forward progress when the increment claims frontend behavior.

Any source-text-only test blocks forward progress when the increment claims runtime behavior.

Any "route exists" proof blocks forward progress when the increment claims integration.

Any "screenshot captured" proof blocks forward progress unless there is a screenshot file path, stable hash, trace ID, and consumer verdict reference.

Every increment must produce an increment receipt.

Every phase must produce a phase closeout regression.

Phase closeout regression must rerun all prior green checks relevant to the changed path.

Final closeout must run all-phases regression from `/coding`, not from curl-only backend calls.

Docs/status cannot move to GO until implementation, browser proof, artifact chain validation, and all regressions are green.

Stop only for a real blocker:

- missing environment
- unavailable provider
- protected path conflict
- permission boundary
- failing test that cannot be fixed inside scope
- unsafe `/coding` seam
- ambiguity requiring Britton decision

On blocker, write:

- `BLOCKED_REAL_REASON`
- exact evidence
- next required permission

Never hide a blocker behind `PARTIAL_GO`, advisory success, or "future work."

---

## 6. Machine-Checkable Receipt Validator

Receipts are not valid just because Codex writes them. They must be machine-checkable.

Future proposed paths:

- `scripts/coding/validate-design-studio-receipts.mjs`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/schemas/increment-receipt.schema.json`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/schemas/artifact-chain.schema.json`

These are proposed implementation targets, not created by this plan unless Plan 00 is approved.

The validator must:

- validate receipt schema
- validate required fields for the increment type
- confirm referenced artifact paths exist
- recompute `sha256` hashes for artifacts
- verify same-trace chain links
- verify screenshot receipts reference `sandbox_apply_receipt_id`
- verify screenshot receipts reference `diff_hash`
- verify critic verdicts reference screenshot hashes
- verify repair retests reference prior critic verdict and new screenshot hashes
- verify acceptance references all required prior artifacts
- verify writeback receipt references acceptance ID, approval ID hash, and trace ID

Required artifact chain:

`original_user_prompt_hash -> request_id -> trace_id -> model_invocation_event_id -> design_packet_hash -> designdna_hash -> coder_packet_hash -> diff_hash -> sandbox_apply_receipt_id -> desktop_screenshot_hash -> mobile_screenshot_hash -> anti_template_verdict_id -> critic_verdict_id -> repair_id/retest_id if present -> acceptance_id -> writeback_receipt_id if present`

Validator gate (run in every phase closeout):

```bash
node scripts/coding/validate-design-studio-receipts.mjs --pivot docs/source-proxy-design-studio-real-integration-pivot-20260702 --through-plan <NN>
```

Bootstrap exemption:

Plan 00.4 is the only validator-bootstrap exception. Its own receipt cannot be validator-gated because the validator does not exist until that increment completes.

Plan 00.4 must still produce a bootstrap receipt with exact files created, schema paths, validator script path, commands run, `git diff --check`, JSON validation if schemas are created, manual artifact-path review, blockers, and final bootstrap verdict.

Every receipt after Plan 00.4 is not bootstrap-exempt. From Plan 00.5 onward, any receipt, phase closeout, or plan closeout that bypasses the validator is invalid and blocks forward progress.

---

## 7. Receipt Contract

Every future implementation increment must create a receipt:

`increment-<plan>-<phase>-<increment>-receipt-<YYYYMMDD-HHMMSS>.md`

Required receipt fields:

- `increment_id`
- `plan_id`
- `phase_id`
- `started_at`
- `completed_at`
- `head_before`
- `head_after`
- `branch`
- `dirty_tree_before`
- `dirty_tree_after`
- `exact_files_changed`
- `forbidden_files_checked`
- `original_user_prompt_hash`, if prompt involved
- `request_id`, if route involved
- `trace_id`, if runtime path involved
- `model_invocation_event_id`, if model/subagent call involved
- `provider_model_name`, if model/subagent call involved
- `input_hash`
- `output_hash`
- `design_packet_hash`, if generated
- `designdna_hash`, if generated
- `coder_packet_hash`, if generated
- `diff_hash`, if diff generated
- `sandbox_apply_receipt_id`, if apply happened
- `desktop_screenshot_path`, if visual output involved
- `desktop_screenshot_hash`, if visual output involved
- `mobile_screenshot_path`, if visual output involved
- `mobile_screenshot_hash`, if visual output involved
- `dom_snapshot_path`, if visual output involved
- `network_proof_path`, required for Plan 01, Plan 02, and Plan 10 frontend/backend claims
- `anti_template_verdict_id`, if anti-template involved
- `critic_verdict_id`, if critic involved
- `repair_attempt_ids`, if repair involved
- `retest_receipt_id`, if repair involved
- `acceptance_id`, if acceptance involved
- `commands_run`
- `browser_actions_run`
- `test_results`
- `what_failed_before_fix`
- `what_changed_to_fix_it`
- `blockers`
- `final_increment_verdict`

Allowed increment verdicts:

- `INCREMENT_GO_PROVEN`
- `INCREMENT_BLOCKED_ENV`
- `INCREMENT_BLOCKED_PERMISSION`
- `INCREMENT_BLOCKED_TEST_FAILURE`
- `INCREMENT_BLOCKED_SCOPE_CONFLICT`
- `INCREMENT_NO_GO_FAKE_PROOF`

Only `INCREMENT_GO_PROVEN` allows forward progress.

---

## 8. Frontend Browser Proof Contract

The tested entrypoint is the existing `/coding` frontend Britton actually uses.

A helper page may be used only as a sandbox output target, never as the tested product entrypoint.

Browser proof must include:

- navigate to `/coding`
- use the real composer or a real visible Design Studio control attached to the existing `/coding` UI
- submit a messy prompt
- observe visible pending/running state
- observe trace ID in UI or linked receipt
- observe visible result or blocked state
- inspect network proof that frontend invoked backend
- inspect final rendered sandbox target when apply is involved

For Plan 10 full `/coding` gauntlet, network proof is required.

Acceptable network proof:

- HAR file
- browser network log JSON
- Playwright request log
- Codex browser/tool event log with request URL, method, status, request ID, trace ID, and response status

Required Plan 10 field:

`network_proof_path`

Plan 10 cannot pass without `network_proof_path`.

For Plan 01 and Plan 02, `network_proof_path` is also mandatory because those plans claim frontend/backend connection.

Backend curl may supplement browser proof but cannot replace it.

A source-text test does not prove browser behavior.

A route unit test does not prove frontend behavior.

A screenshot alone does not prove behavior unless tied to trace and consumed downstream.

---

## 9. Anti-Fake-GO Contract

The following substitutions are forbidden:

- route exists = integration
- component renders = product works
- source text contains string = UI works
- preview route returns stub = runtime works
- hardcoded packet = generated packet
- installed model = invoked model
- model field present = model consumed
- provider configured = provider consumed
- screenshot path supplied by caller = screenshot captured
- screenshot captured = screenshot verified
- screenshot verified = critic consumed it
- advisory critic = acceptance gate
- docs status says GO = GO
- unit tests pass = frontend works
- backend curl passes = frontend works
- manual "looks good" = visual verification
- clean modern UI = original design
- generic purple/blue glass cards = acceptable design
- Obsidian helper function exists = writeback wired
- approval ID string exists = valid human approval
- same filename = same trace
- no failure surfaced = success

Fail labels:

- `FAIL_ROUTE_EXISTS_NOT_INTEGRATED`
- `FAIL_FRONTEND_NOT_TESTED`
- `FAIL_BACKEND_ONLY_PROOF`
- `FAIL_PACKET_HARDCODED`
- `FAIL_MODEL_NOT_INVOKED`
- `FAIL_MODEL_NOT_CONSUMED`
- `FAIL_SCREENSHOT_THEATER`
- `FAIL_CRITIC_ADVISORY_ONLY`
- `FAIL_GENERIC_AI_STUDIO_ONE_LOOK`
- `FAIL_WRITEBACK_DORMANT`
- `FAIL_STATUS_DOC_GO`
- `FAIL_NO_PHASE_REGRESSION`
- `FAIL_INCREMENT_BATCHING`
- `FAIL_PARALLEL_ROUTE_CONFUSION`

---

# Phase and Plan Map

## Phase 0 — Truth Reset and Fake-GO Baseline

### Plan 00 — Truth Reset and Baseline

**Folder:**
`plan-00-truth-reset-and-baseline/`

**Status:** `PLAN_WRITTEN_NOT_STARTED`
**Implementation performed:** `false`

**Goal:** Reset the source of truth, baseline inherited red tests, fix only the inherited writeback path separator defect, bootstrap receipt validation, and prevent Plan 01 from starting on a known-red baseline.

#### Increment 00.1 — Current audit and baseline readback

Required future work:

- inspect the hardline audit
- inspect current Design Studio files
- record current fake-GO findings
- record old Plan 14 status contradiction
- record that this pivot has not implemented anything yet

Required checks:

```bash
git status --short
git diff --check
rg "COMPLETE_GO|Plan 14|design-studio|writeback" docs/source-proxy-design-studio-implementation-pivot-20260701 docs/source-proxy-design-studio-real-integration-pivot-20260702
```

Receipt must include:

- old Plan 14 fake-GO summary
- current chain break summary
- no runtime files touched

#### Increment 00.2 — Inherited red-test baseline

Required future work:

Record the inherited failing test exactly:

`src/lib/coding/__tests__/design-studio-obsidian-writeback.test.ts`

Required baseline facts:

- current result: 8 pass / 2 fail
- failing cases:
  - `creates a valid design memory note payload`
  - `does not overwrite an existing note`
- root cause:
  - `approvedDesignMemoryDestination` uses `path.startsWith(`${allowedRoot}/`)`
  - this fails with Windows backslashes on win32
- blocker label:
  - `INHERITED_RED_WRITEBACK_PATH_SEPARATOR`

Required future command:

```bash
CI=1 npx vitest run src/lib/coding/__tests__/design-studio-obsidian-writeback.test.ts --reporter=verbose --testTimeout=15000 --hookTimeout=15000 --no-file-parallelism
```

The receipt must mark the failure as inherited, not introduced by Plan 00.

#### Increment 00.3 — Baseline-only writeback path normalization fix

Authorization: This increment is implementation-authorized ONLY when Britton explicitly starts Plan 00. It is the first runtime mutation in the pivot and inherits the pivot's `requires_britton_permission_to_implement: true`.

Scope:

Fix only the path separator normalization defect in:

`src/lib/coding/design-studio-obsidian-writeback.ts`

No other Design Studio runtime wiring is allowed.

Required future result:

- writeback suite goes from 8/10 to 10/10
- no unrelated writeback behavior changes
- no design-studio route wiring
- no shell wiring
- no model wiring
- no screenshot work
- no docs GO claim

Required future command:

```bash
CI=1 npx vitest run src/lib/coding/__tests__/design-studio-obsidian-writeback.test.ts --reporter=verbose --testTimeout=15000 --hookTimeout=15000 --no-file-parallelism
```

Plan 01 cannot start until this suite is green.

#### Increment 00.4 — Receipt validator bootstrap contract

Scope:

Create the machine-checkable receipt validator and schemas as future implementation targets:

- `scripts/coding/validate-design-studio-receipts.mjs`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/schemas/increment-receipt.schema.json`
- `docs/source-proxy-design-studio-real-integration-pivot-20260702/schemas/artifact-chain.schema.json`

This increment is the only validator bootstrap exception.

Negative test requirement (R6): The validator must ship with negative tests proving it REJECTS each of the following bad receipts. A validator that returns "valid" on any of these fails 00.4:

- a receipt with a forged/incorrect artifact hash
- a receipt with a broken trace-link chain (a referenced prior artifact hash that does not match the actual prior receipt)
- a screenshot receipt missing `sandbox_apply_receipt_id`
- a screenshot receipt missing `diff_hash`
- a critic verdict that does not reference any screenshot hash
- a writeback receipt missing `approval_id` hash or with a trace mismatch
- a receipt missing a required field for its increment type
- a receipt referencing an artifact path that does not exist on disk

Each negative case must be a concrete fixture under `scripts/coding/__tests__/fixtures/` (PROPOSED ONLY path) and the validator test suite must assert each is rejected. These negative tests are part of the 00.4 deliverable, not deferred.

Required bootstrap receipt:

- exact validator files
- exact schema files
- exact negative-test fixture files and the cases they cover
- `git diff --check`
- JSON validation if schemas are created
- manual artifact-path review
- blocker list
- final bootstrap verdict

After this increment, validator bypass is forbidden.

#### Increment 00.5 — Phase closeout regression

Required checks:

```bash
git diff --check
CI=1 npx vitest run src/lib/coding/__tests__/design-studio-obsidian-writeback.test.ts --reporter=verbose --testTimeout=15000 --hookTimeout=15000 --no-file-parallelism
node scripts/coding/validate-design-studio-receipts.mjs --pivot docs/source-proxy-design-studio-real-integration-pivot-20260702 --through-plan 00
```

Closeout required:

- inherited red test fixed
- receipt validator exists and its negative tests pass
- all Plan 00 receipts validated except the bootstrap-exempt 00.4 receipt
- no runtime integration beyond the path-normalization fix
- no GO claim

---

## Phase 1 — Real `/coding` Frontend Entrypoint

### Plan 01 — Real `/coding` Composer Entrypoint

**Folder:**
`plan-01-real-coding-composer-entrypoint/`

**Status:** `PLAN_WRITTEN_NOT_STARTED`
**Implementation performed:** `false`

**Goal:** Attach Design Studio to the exact `/coding` UI Britton uses, not a parallel test page.

### Highest-Risk Seam

The `/coding` composer/control seam is the highest-risk integration point. If Codex builds a separate Design Studio UI instead of wiring the UI Britton actually clicks, the pivot fails.

Plan 01.1 must produce a seam decision receipt before any Plan 01.2 UI implementation.

Required seam decision fields:

- exact current composer/control component
- exact state/store/hook/event path
- exact route payload path
- where Design Studio mode can attach
- where task status/result can display
- how selected-prompt clearing/failure state is preserved
- whether the seam is safe
- whether adding Design Studio mode would break existing `/coding` behavior
- required Britton decision if unsafe

Fallback:

If no clean seam exists, Plan 01 stops with:

`BLOCKED_SEAM_DECISION_REQUIRED`

Plans 02–10 cannot proceed until Britton approves a seam decision.

All later plans inherit the Plan 01 approved seam. If the seam changes, return to Plan 01 and rerun Plan 01 closeout before continuing.

#### Increment 01.1 — Seam discovery and decision

Required proof:

- browser opens `/coding`
- actual composer/control identified
- DOM snapshot saved
- current event path mapped
- no code changes yet unless needed for instrumentation and approved
- seam verdict recorded

#### Increment 01.2 — Add Design Studio mode/control to existing `/coding`

Required proof:

- user-like browser action selects or invokes Design Studio mode
- prompt submitted through existing UI
- visible pending/running state appears
- `network_proof_path` exists
- request ID and trace ID visible or linked

#### Increment 01.3 — Existing `/coding` regression

Required proof:

- ordinary coding prompt path still submits
- selected prompt clearing still works
- failure state is visible
- no unrelated coding UI regression

#### Plan 01 closeout

Required:

```bash
node scripts/coding/validate-design-studio-receipts.mjs --pivot docs/source-proxy-design-studio-real-integration-pivot-20260702 --through-plan 01
```

---

## Phase 2 — Real Packet, Model, and Coder Pipeline

### Plan 02 — Real Design Studio Network Path

**Folder:**
`plan-02-real-design-studio-network-path/`

**Status:** `PLAN_WRITTEN_NOT_STARTED`
**Implementation performed:** `false`

**Goal:** `DesignStudioShell` must call the real backend and render live response data.

#### Increment 02.1 — Wire shell to backend route

Required proof:

- source inspection confirms real route call
- browser network proof confirms call
- backend receives original prompt/body
- UI changes based on live response

Required field:

`network_proof_path`

#### Increment 02.2 — Remove hardcoded success as product proof

Required proof:

- two prompt submissions produce different request IDs
- blocked backend response surfaces as blocked UI
- route failure changes UI verdict
- no hardcoded success accepted

#### Increment 02.3 — Phase regression

Required:

- Plan 01 browser proof still passes
- network call still starts from `/coding`
- validator passes through Plan 02

---

### Plan 03 — Real Packet Generation

**Folder:**
`plan-03-real-packet-generation/`

**Status:** `PLAN_WRITTEN_NOT_STARTED`
**Implementation performed:** `false`

**Goal:** Replace hardcoded packet literals with prompt-derived generated packets.

#### Increment 03.1 — Prompt hash and request identity

Required proof:

- `original_user_prompt_hash`
- `request_id`
- `trace_id`
- same prompt produces same prompt hash
- different prompt produces different prompt hash

#### Increment 03.2 — Generated design packet

Required proof:

Two different messy prompts produce different `design_packet_hash` values.

Packet must include prompt-derived structured fields:

- intent
- audience
- page/app target
- constraints
- reference inputs
- visual direction
- accessibility notes
- risk flags

Derivation rule (R3): packet fields must be genuinely derived/structured from the prompt, not the raw prompt re-serialized. A packet that is just `{ raw_prompt, prompt_hash }` with no structured fields is a degenerate derivation and fails this increment.

Fail if packet equals a fixed default.

Fail if two different prompts produce the same packet hash.

#### Increment 03.3 — DesignDNA normalization

Required proof:

DesignDNA includes:

- spatial system
- product/domain motif
- typography
- rhythm
- interaction model
- visual hierarchy

Generic fallback must be marked weak and cannot pass.

#### Increment 03.4 — Phase regression

Required:

- Plans 01–02 still pass
- packet hashes visible in receipt
- validator passes through Plan 03

---

### Plan 04 — Model and Subagent Consumption

**Folder:**
`plan-04-model-and-subagent-consumption/`

**Status:** `PLAN_WRITTEN_NOT_STARTED`
**Implementation performed:** `false`

**Goal:** Wire real model/subagent lanes where available and fail honestly where unavailable.

### BLOCKED_ENV ceiling

If no provider/model lane is reachable, Plan 04 stops as `BLOCKED_ENV`. It must not manufacture a provider.

### Expected Lane Baseline

The following are expected `BLOCKED_ENV` or likely missing/dormant until proven otherwise:

- Mac worker for Design Studio lane
- Mac web search/SearXNG for Design Studio lane
- Scout/current research for Design Studio lane
- Cartographer for Design Studio lane

These lanes are not assumed available. The implementer must not burn cycles proving the same negative repeatedly. The first Plan 04.1 inventory may mark them:

`EXPECTED_BLOCKED_ENV_OR_DORMANT`

with evidence.

They become implementation targets only if approved Plan 04 scope explicitly wires them. Absence blocks GO only when final acceptance criteria require them; otherwise they are honestly represented as blocked/deferred.

Reachability matrix required fields:

- `lane`
- `claimed_role`
- `expected_status`
- `observed_status`
- `reachable_from_coding`
- `reachable_from_sandbox_apply`
- `evidence`
- `required_for_go`
- `future_decision_needed`

#### Increment 04.1 — Runtime provider inventory

Required proof:

- actual available local/provider models discovered from runtime/config
- model/provider names recorded
- unavailable providers marked `BLOCKED_ENV`
- no assumed availability

#### Increment 04.2 — At least one live model/subagent invocation

Required proof:

- `model_invocation_event_id`
- provider/model name
- input hash
- output hash
- token count or byte count when available
- short non-sensitive output excerpt
- output materially changes design packet

Material-change rule (R4): "materially changes the design packet" is defined as — `design_packet_hash` produced with the live model invocation differs from `design_packet_hash` produced by the no-model fallback path on the same prompt. Both hashes must be recorded in the receipt. If they are equal, the model did not materially change the packet and the increment fails.

#### Increment 04.3 — Subagent reachability matrix

Required proof:

- all target lanes classified
- no "exists" counted as live
- missing/dormant lanes honestly labeled

#### Increment 04.4 — Failure behavior

Required proof:

- unavailable model -> `BLOCKED_ENV`
- timeout -> retry-limited fail or `BLOCKED_ENV`
- missing source -> `BLOCKED_ENV`
- no fake fallback success

#### Increment 04.5 — Phase regression

Required:

- Plans 01–03 still pass
- model invocation linked to same trace
- validator passes through Plan 04

---

## Phase 3 — Real Sandbox Apply and Browser-Visible Output

### Plan 05 — Coder Packet to Sandbox Apply

**Folder:**
`plan-05-coder-packet-to-sandbox-apply/`

**Status:** `PLAN_WRITTEN_NOT_STARTED`
**Implementation performed:** `false`

**Goal:** Generated design packet produces a coder packet and applies only to `/coding/design-demo`.

Canonical path:

`/coding Design Studio task -> generated design_packet -> generated coder_packet -> scoped sandbox apply -> /coding/design-demo`

`execute-approved` is not part of this plan.

#### Increment 05.1 — Generate coder packet

Required proof:

- `coder_packet_hash`
- references `design_packet_hash`
- target limited to design demo sandbox
- no production route apply

#### Increment 05.2 — Apply sandbox diff

Required proof:

- actual file diff generated
- changed files under allowed sandbox only
- `diff_hash`
- protected paths blocked
- production app files blocked

#### Increment 05.3 — Browser-visible sandbox output

Required proof:

- browser opens `/coding/design-demo`
- visible content/layout changes after apply
- DOM snapshot saved
- screenshot saved
- UI links result to trace

#### Increment 05.4 — Phase regression

Required:

- Plans 01–04 still pass
- unrelated `/coding` paths still pass
- no forbidden files touched
- validator passes through Plan 05

---

## Phase 4 — Visual Verification, Originality, Critic, and Repair

### Plan 06 — Desktop and Mobile Screenshot Proof

**Folder:**
`plan-06-desktop-mobile-screenshot-proof/`

**Status:** `PLAN_WRITTEN_NOT_STARTED`
**Implementation performed:** `false`

**Goal:** Capture real screenshots after sandbox apply, tie them structurally to the same-trace apply receipt, and make them consumable by critic/acceptance.

Screenshot provenance cannot rely on timestamps alone.

Each screenshot receipt must include:

- `sandbox_apply_receipt_id`
- `diff_hash`
- `trace_id`
- `rendered_route`
- `viewport`
- `screenshot_path`
- `screenshot_hash`
- `captured_after_apply:true`

Validator rule:

The receipt validator must confirm each screenshot references the same-trace `sandbox_apply_receipt_id` and `diff_hash` from Plan 05.

A screenshot without `sandbox_apply_receipt_id` is invalid even if the file exists and the hash matches.

No screenshot can be consumed by critic or acceptance unless structurally linked back to sandbox apply.

#### Increment 06.1 — Desktop screenshot

Required proof:

- desktop screenshot path
- sha256 hash
- trace ID
- `sandbox_apply_receipt_id`
- `diff_hash`
- file non-empty

#### Increment 06.2 — Mobile screenshot

Required proof:

- mobile screenshot path
- sha256 hash
- trace ID
- `sandbox_apply_receipt_id`
- `diff_hash`
- no measurable horizontal overflow if available

#### Increment 06.3 — Screenshot consumption preparation

Required proof:

- screenshot hashes included in verifier/critic packet
- hashes cannot be caller-supplied only
- missing screenshot blocks acceptance

#### Increment 06.4 — Phase regression

Required:

- Plans 01–05 still pass
- validator passes through Plan 06
- no "looked good" proof accepted

---

### Plan 07 — Anti-Template Rendered Output Verifier

**Folder:**
`plan-07-anti-template-rendered-output-verifier/`

**Status:** `PLAN_WRITTEN_NOT_STARTED`
**Implementation performed:** `false`

**Goal:** Detect generic Google AI Studio / v0 / Claude artifact / modern SaaS slop from rendered output, not prompt text.

### Rendered-Output Anti-Template Signal Contract

Detector must inspect rendered DOM/output and screenshot-derived metadata. It must never inspect only caller-supplied prompt text or packet text.

Required signal set:

1. Centered hero block as dominant first viewport structure.
2. Purple/blue gradient hero or page background.
3. Generic glassmorphism cards used on more than 50% of visible cards.
4. Three-card feature grid with generic headings.
5. Pricing tiers or pricing-card structure.
6. Bland footer with generic links and no product-specific behavior.
7. Decorative blobs/auras with no project-specific reason.
8. Hero-left/cards-right default SaaS composition.
9. Glass sidebar + main canvas + floating action button default app-shell composition.
10. "Modern dashboard" layout with interchangeable stat cards and no domain-specific hierarchy.
11. Repeated rounded-xl card stacks with uniform spacing and no content-specific layout change.
12. Generic CTA labels such as "Get Started," "Learn More," or "Explore Features" when not grounded in the prompt/product.

Threshold rule:

- `GENERIC_TEMPLATE_REJECT` if 4 or more template signals are present.
- `GENERIC_TEMPLATE_REJECT` if 3 template signals are present and no rendered product/domain motif is found.
- `GENERIC_TEMPLATE_REPAIR_REQUIRED` if 2 template signals are present and the layout lacks project-specific spatial hierarchy.
- May pass only when fewer than 2 template signals remain, or when critic records a project-specific justification referencing rendered DOM/output and screenshot hashes.

### Project-Specific Motif Requirement

Accepted rendered output must include visible, rendered evidence of project/domain-specific design direction. This is verified against rendered DOM/output text, ARIA labels, structural roles, navigational labels, panel names, or screenshot-associated DOM snapshots. Packet fields alone do not count.

Motif evidence must be user-facing and product/domain-facing. It must not require internal pipeline jargon.

Acceptable rendered motif anchors:

- SpiritOS
- Source Proxy
- coding cockpit
- design studio
- design workbench
- design sandbox
- coding agent
- project workspace
- prompt-to-design
- visual review
- design demo
- design trace, only if shown as a user-facing run/debug affordance
- screenshot review, only if shown as a user-facing review affordance
- repair review, only if shown as a user-facing review affordance

Forbidden motif anchors as required user-facing copy:

- artifact chain
- anti-template verdict
- acceptance harness
- approval-gated memory writeback
- writeback receipt
- model_invocation_event_id
- packet_hash
- diff_hash
- receipt validator
- same-trace hash-link
- BLOCKED_ENV
- fake-GO
- consumer_event_id

Those terms may appear only in developer/debug receipts or operator evidence panels, not as the core visual motif of a user-facing design-demo page.

A pass requires:

- at least two rendered, visible product/domain-specific motif anchors, or
- one strong domain-specific layout structure described in critic verdict and tied to screenshot hashes.

Strong domain-specific layout structures include:

- composer + live task trace + design preview + sandbox result
- coding cockpit panels organized around prompt, packet, diff, and preview
- design workbench organized around brief, constraints, visual direction, and review
- side-by-side before/after design review tied to real sandbox output
- run-state layout that makes pending, blocked, repair, and accepted states visible to the operator

Automatic rejects:

- clean purple-blue SaaS hero + cards
- generic glass sidebar + canvas + floating button
- centered hero + three features + footer
- pricing/cards/footer composition
- "looks polished" approval without rendered motif evidence
- satisfying motif rules only by dumping internal pipeline jargon into visible copy

Receipt fields:

- `rendered_dom_snapshot_path`
- `desktop_screenshot_hash`
- `mobile_screenshot_hash`
- `template_signal_matches`
- `template_signal_count`
- `project_motif_rendered_evidence`
- `anti_template_verdict_id`
- `anti_template_verdict`
- `reject_or_repair_reason`

#### Increment 07.1 — Rendered output detector

Required proof:

- detector inspects DOM/layout/screenshot metadata
- text-only prompt detector rejected
- generic AI Studio one-look flagged

#### Increment 07.2 — DesignDNA non-default check

Required proof:

- accepted DesignDNA includes product-specific motif
- accepted output includes non-default spatial rhythm
- generic clean UI cannot pass

#### Increment 07.3 — Hostile rejection test

Required proof:

- generic purple/blue glass SaaS prompt rejected or sent to heavy repair
- receipt includes signals
- acceptance blocked until repaired

#### Increment 07.4 — Phase regression

Required:

- Plans 01–06 still pass
- anti-template verdict references screenshot/DOM artifacts
- validator passes through Plan 07

---

### Plan 08 — Design Critic and Bounded Repair

**Folder:**
`plan-08-design-critic-bounded-repair/`

**Status:** `PLAN_WRITTEN_NOT_STARTED`
**Implementation performed:** `false`

**Goal:** Critic consumes screenshot hashes and anti-template verdict, then approves, rejects, or repairs inside bounded attempts.

#### Increment 08.1 — Critic consumes screenshots

Required proof:

- `critic_verdict_id`
- critic input includes desktop screenshot hash
- critic input includes mobile screenshot hash
- critic input includes anti-template verdict ID
- verdict references those hashes

#### Increment 08.2 — Bounded repair loop

Required proof:

- max repair attempts defined
- repair attempt IDs recorded
- repair changes sandbox diff
- repair cannot touch forbidden paths
- repair output is retested

#### Increment 08.3 — Retest after repair

Required proof:

- new screenshot hashes after repair
- anti-template reruns
- critic reruns
- acceptance sees repaired artifacts

#### Increment 08.4 — Phase regression

Required:

- Plans 01–07 still pass
- no advisory-only critic accepted
- no unbounded repair accepted
- validator passes through Plan 08

---

## Phase 5 — Approved Writeback and Full Gauntlet

### Plan 09 — Approved Obsidian Writeback Runtime

**Folder:**
`plan-09-approved-obsidian-writeback-runtime/`

**Status:** `PLAN_WRITTEN_NOT_STARTED`
**Implementation performed:** `false`

**Goal:** Wire approved writeback into the real accepted-run path, locked behind explicit approval and same-trace acceptance.

#### Increment 09.1 — Production importer

Required proof:

- writeback helper has production importer/call site
- call site reachable only after accepted run
- preview cannot write memory

#### Increment 09.2 — Approval gate

Required proof:

- missing approval ID fails closed
- invalid approval ID fails closed
- trace mismatch fails closed
- missing acceptance fails closed
- model cannot self-promote approval

#### Increment 09.3 — Writeback receipt

Required proof:

- approval ID hash
- trace ID
- design packet hash
- screenshot hashes
- critic verdict
- anti-template verdict
- acceptance ID
- no raw prompt leakage if sensitive
- no writeback before acceptance

#### Increment 09.4 — Phase regression

Required:

- Plans 01–08 still pass
- preview write blocked
- approved path only works with real approval
- validator passes through Plan 09

---

### Plan 10 — Full `/coding` Gauntlet

**Folder:**
`plan-10-full-coding-gauntlet/`

**Status:** `PLAN_WRITTEN_NOT_STARTED`
**Implementation performed:** `false`

**Goal:** Prove the entire chain from the real `/coding` UI.

#### Increment 10.1 — Happy path gauntlet

Required proof:

- browser opens `/coding`
- messy design prompt submitted through actual UI
- `network_proof_path`
- request ID
- trace ID
- model invocation event or honest `BLOCKED_ENV`
- design packet hash
- DesignDNA hash
- coder packet hash
- sandbox diff hash
- sandbox apply receipt ID
- desktop screenshot hash
- mobile screenshot hash
- anti-template verdict ID
- critic verdict ID
- repair/retest ID if needed
- acceptance ID
- UI displays final status

#### Increment 10.2 — Hostile generic slop gauntlet

Required proof:

- generic AI Studio/v0 prompt submitted through `/coding`
- rendered output rejected or repaired heavily
- cannot accept clean generic output
- verdict references rendered artifacts

#### Increment 10.3 — Failure path gauntlet

Required proof:

- unavailable provider safely triggered or simulated
- UI shows `BLOCKED_ENV`
- no fake GO
- trace records failure reason

Simulation rule (R5): If a provider failure is simulated rather than triggered on a live provider, the simulation must be environmental — e.g., point the route at an unreachable endpoint/port, or remove/empty the provider config for the run. A code-path mock that returns a `BLOCKED_ENV` response is forbidden; that is the same fake-GO shape this pivot exists to prevent. The receipt must record how the unavailability was induced.

#### Increment 10.4 — All prior phase regression

Required proof:

- all prior checks rerun
- no previous green proof broken
- no unrelated `/coding` regression
- no forbidden files touched
- validator passes through Plan 10

---

## Phase 6 — Docs and Status Closeout Only After Green

### Plan 11 — Docs Status Closeout Only After Green

**Folder:**
`plan-11-docs-status-closeout-only-after-green/`

**Status:** `PLAN_WRITTEN_NOT_STARTED`
**Implementation performed:** `false`

**Goal:** Update docs/status only after Plan 10 proves the full product chain.

#### Increment 11.1 — Evidence reconciliation

Required proof:

- every GO claim links to trace ID and artifact paths
- every screenshot claim links to hash
- every model claim links to invocation event
- every critic claim links to screenshot hash
- every writeback claim links to approval and trace
- old Plan 14 not treated as current truth

#### Increment 11.2 — Status update

Required proof:

- status JSON validates
- no GO without Plan 10 acceptance ID
- no contradiction with master plan
- old pivot has deprecation marker
- new pivot is canonical

#### Increment 11.3 — Final all-phases closeout

Required checks:

```bash
git diff --check
npx tsc --noEmit --pretty false --incremental false
CI=1 npx vitest run src/lib/coding/__tests__/design-studio-obsidian-writeback.test.ts --reporter=verbose --testTimeout=15000 --hookTimeout=15000 --no-file-parallelism
node scripts/coding/validate-design-studio-receipts.mjs --pivot docs/source-proxy-design-studio-real-integration-pivot-20260702 --through-plan 11
```

Required browser proof:

- full `/coding` gauntlet
- screenshot artifacts
- receipt validation
- forbidden fake-GO grep
- exact changed files only

---

## Root Status JSON

See `status.json` in this folder. Every plan status JSON conforms to the per-plan schema in this section:

```json
{
  "status": "PLAN_WRITTEN_NOT_STARTED",
  "implementation_performed": false,
  "runtime_code_modified": false,
  "go_claimed": false,
  "requires_britton_permission_to_implement": true,
  "phase_closeout_required": true,
  "browser_proof_required": true,
  "artifact_chain_required": true,
  "machine_receipt_validation_required": true
}
```

---

## Scope Confirmation

- Runtime files touched by this plan: false
- Source Proxy runtime files touched by this plan: false
- Obsidian modified by this plan: false
- External dependency added by this plan: false
- Graph/memory tooling added by this plan: false
- Plan count changed: false
- GO claimed: false

---

## Permission Gate

This plan is written but not implemented. No increment may begin without Britton's explicit permission to start Plan 00.
