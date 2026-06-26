# GLM Plan 4 Integrity Audit - 2026-06-25

## Executive Verdict

Plan 4 ("Canonical `/coding` UI/API Consolidation") is reported at
`PLAN4_FINAL_CLOSEOUT_READY_FOR_BRITTON_REVIEW` and closes out through increment
`4.6.2`. This independent audit inspected the production code, tests, status
files, handoff, final closeout packet, and every browser/live-route/operator
proof artifact for hardcoding, prompt tailoring, fake apply/operator proof,
route laundering, hidden apply authority, fake GO wording, overclaiming, and
unsupported Plan 5 readiness.

The causal contract in `/v1/actions/execute-approved` is a genuine structural
guard: it fails closed (HTTP 502, `plan4_execute_approved_contract_missing`)
when a Source Proxy apply-like 2xx response omits any required causal field.
The `/coding` operator surface preserves the fail-closed reason code, route,
task/trace/consumer fields, output hash, productive truth, and control
authority, and never displays a hidden apply success. Dormant/advisory routes
are honestly marked and never masquerade as canonical. No proof-artifact prompt
IDs reach production code.

Findings are non-blocking. The caveats are: (1) the operator-surface tests are
mostly source-text string assertions rather than behavior-render assertions, so
they verify presence of labels/authority flags but not rendered output for every
field; (2) the Windows `Z:\` drive-root environment could not re-run vitest
locally (vitest module resolution fails as `Z:\@id\Z:\...` for all suites), so
this audit relies on the recorded `/home/source/SpiritOS` PASS results plus
source inspection rather than a fresh local green run; (3) browser proof relied
on Playwright route interception against the live Dell dev server, with DOM/JSON
kept authoritative over screenshots — this is real route/UI proof, not fake
success, but the screenshots themselves could not be visually re-verified by GLM
in this environment.

Verdict: `PLAN4_INTEGRITY_CONFIRMED_WITH_CAVEATS`. Grade 90/100 (A-).

## Audit Scope

Audit-only task. All 12 completed Plan 4 increments (`4.1.1`–`4.6.2`) plus the
final closeout packet, status files, and handoff. No fixes, no patches, no
source/test edits, no Plan 5/6 work. Only this report file may be produced.

## Methods / Commands Run

- `git log --oneline -15` and `git status` to confirm branch and clean tree.
- `git -C "Z:/" show --stat d74d80ab` to inspect the final closeout commit
  (docs/proof only: 10 files, +308/-9, no source).
- `git -C "Z:/" log --stat e11e940a^..d74d80ab` to enumerate every source file
  Plan 4 touched.
- `git -C "Z:/" log --name-only e11e940a^..d74d80ab | grep ...` for forbidden
  path touches (.env, secret, jellyfin, media, spiritflix, mac-optim, obsidian,
  package.json/-lock, .xml, repomix, plan-05, plan-06) — none found.
- `Read` of `src/app/v1/actions/execute-approved/route.ts` (full),
  `__tests__/route.test.ts` (full), `src/lib/coding/shell-registry.ts` (full),
  `src/lib/coding/__tests__/shell-registry.test.ts` (full),
  `src/app/v1/coding/codex/route.ts` (full) and its test (full).
- `Grep` of `CodingCockpitShell.tsx` (13k+ lines) for hardcoding/prompt IDs:
  `plan4|PLAN4|task-plan4|trace-plan4|proof|fake_go|forced_pass|hardcoded|bypass|fallback`.
- `Grep` of `src/` for proof-artifact IDs `task-plan4|trace_plan4|plan4_browser_intercept|plan4-412|plan4-461`
  — no matches in production source.
- `Read` of all status/handoff/closeout MD and key browser/live proof JSON.
- `npx vitest run ...` attempted locally — FAILED to run on the `Z:\` Windows
  drive root for ALL suites (vitest resolves modules as
  `Z:\@id\Z:\node_modules\...`), so local re-execution was not possible. This is
  an environment limitation, not a Plan 4 defect; recorded results were
  produced on `/home/source/SpiritOS`.

## Files And Commits Inspected

Key commits (all within `e11e940a^..d74d80ab`):
- `e11e940a` — Complete Plan 4 approved-action causal proof
- `6ec67d32` — Add Plan 4 operator ledger proof
- `35f47c9b` — Complete Plan 4 output-contract ledger proof
- `a5c5239c` — Add Plan 4 operator control ledger proof
- `646c4eef` — Complete Plan 4 operator control phase
- `5859a30a` — Complete Plan 4 truth ledger phase
- `a305ad14` — Add Plan 4 API consolidation ledger
- `02469f41` — Mark Plan 4 dormant coding routes
- `d74d80ab` — Add Plan 4 final closeout proof (docs/proof only)

Source files Plan 4 changed (scoped):
- `src/app/v1/actions/execute-approved/route.ts` (+45) and `__tests__/route.test.ts` (+110)
- `src/app/v1/coding/{codex,bounded-diff-preview,research-preview,helper-agents/preview}/route.ts` (+dormant headers) and their tests
- `src/lib/coding/shell-registry.ts` (+94) and `__tests__/shell-registry.test.ts` (+25)
- `src/components/coding/CodingCockpitShell.tsx` (+ledgers) and `__tests__/coding-cockpit-shell.test.tsx` (+assertions)

Docs/proof inspected: `status.md`, `status.json`, `next-plan-handoff.md`,
`plan4-final-closeout-packet-20260625.md`, `gate-manifest.template.json`,
`operator-check.sh`, all `increment-4-*.md/.json/.png`,
`phase-4-{2,3,4,5,6}-closeout-review-*.md`,
`increment-4-1-1-live-proof-20260625.md`,
`increment-4-5-2-live-route-proof-20260625.json`.

## Hardcoding / Prompt-Tailoring Findings

No prompt-specific branches or hardcoded exact proof IDs were found in
production code.

- The `plan4ExecuteApprovedContractCheck` function in
  `execute-approved/route.ts` is fully structural: it reads
  `execution`/`task.causal_trace` and checks for the presence of five named
  fields (`task_id`, `trace_id`, `invocation_event_id`, `consumer_event_id`,
  `consumer_subsystem`). There is no value match, no allowlist of specific task
  ids, and no special-cased trace ids.
- In `CodingCockpitShell.tsx`, identifiers `plan42*`/`plan43*`/`plan44*`/`plan45*`
  are UI ledger section builders (e.g. `plan42OutputContractItems`,
  `plan43ControlAuthorityItems`) that read live runner state. They are not
  branches keyed on prompt content.
- A repo-wide `Grep` of `src/` for proof-artifact ids
  (`task-plan4`, `trace_plan4`, `plan4_browser_intercept`, `plan4-412`,
  `plan4-461`) returned zero matches. Those ids exist only inside the proof
  JSON artifacts in `docs/.../plan-04/`, which is the correct location.
- The `apply_ack_no_disk_proof` reason code in `CodingCockpitShell.tsx`
  (lines ~1016, ~6842) is a pre-existing apply-truth guard that *downgrades* a
  PASS to NEEDS FIX when execute-approved returns 200 without disk/applied
  proof. This is the opposite of a forced pass; it is honest apply truth.
- No `fake_go`, `forced_pass`, `bypass`, or hardcoded-approval branches found.

Finding: none. No prompt tailoring reaches production behavior.

## Route Truth / Causal Contract Findings

Confirmed fail-closed in `execute-approved/route.ts`:

- After the proxy call, if `response.ok` and content-type is JSON, the route
  runs `plan4ExecuteApprovedContractCheck(responseText)`.
- If any of the five required causal fields is missing, it returns HTTP 502 with
  `error: "execute-approved returned success without the Plan 4 causal output contract."`,
  `reason_code: "plan4_execute_approved_contract_missing"`, the `missing_fields`
  list, and the `task_id`. It does NOT fall through to the success passthrough.
- The test `fails closed when Source Proxy success lacks the Plan 4 causal
  contract` asserts exactly this 502 response and that no trial row/patch side
  effects occur.
- The route cannot display a false apply success on `/coding` because a missing
  contract produces a 502 (not a 2xx passthrough); `/coding` renders the
  fail-closed reason/route/technical payload.

The contract check is the last gate before `recordTrialApplyProof` and the
final `new Response(responseText, ...)`. Ordering is correct: contract failure
short-circuits before any success recording. No path returns the raw proxy 2xx
without the contract passing.

## Operator Surface Truth Findings

`CodingCockpitShell.tsx` preserves, in visible ledgers derived from runner
state:

- Fail-closed reason code: `plan43ControlLedgerItems`/`plan44RepairProductiveTruthItems`
  carry `previewState.reasonCode` (e.g. `plan4_execute_approved_contract_missing`,
  `cancelled_no_apply_success`).
- Route called: `previewState.routeCalled` (e.g. `/v1/actions/execute-approved`).
- Task id, trace id, invocation event id, consumer event id, consumer subsystem:
  in `plan42OutputContractItems` from `previewState`.
- Output hash: `plan42OutputContractItems` `output_hash`.
- Status / productive truth: `codingVisibleResult.live_model_proof_status` and
  `causalStatusAfter`.
- Control state: `plan43ControlLedgerItems` (edit/approve/reject/apply/cancel/resume/stop_or_kill),
  `plan43ControlContractItems` (backend run id, control route/status, resume,
  sync, interruption source).
- Dormant/canonical route truth: `plan45CanonicalRouteItems`,
  `plan45SupportingRouteItems`, `plan45DormantRouteItems` from the registry.

Caveat: the corresponding tests are source-text assertions
(`readFileSync(...).toContain(...)`) that verify the string constants and
builder names exist in the source, plus explicit `.not.toContain("Plan 4.2 GO")`
guards against fake GO wording. They do not mount and render the component to
assert the field values appear in DOM. The browser proof JSON (e.g.
4-6-1-responsive) does capture rendered DOM excerpts containing these fields,
so the behavior is evidenced — but the unit test layer itself is text-shape,
not behavior-render.

## Browser / Operator Proof Findings

Browser proofs are real route-interception proofs, not fake success:

- Target URL is the live Dell Next dev server
  `https://10.0.0.186:3000/coding` in every browser proof JSON.
- Route interception is explained per proof (e.g. 4-1-2:
  "Playwright page.route fulfilled /v1/actions/execute-approved with HTTP 502
  fail-closed payload"; 4-3-2: `active_run_route`/`patch_run_route` injection
  with explicit call counts `active_run_calls:1, get_run_calls:1,
  patch_run_calls:1`).
- Visible assertions are recorded as boolean fields:
  `noApplySuccessVisible`, `reasonCodeVisible`, `failedVisible`,
  `noCommitAuthorityVisible`, `noPushAuthorityVisible`,
  `noProcessKillAuthorityVisible`, etc.
- JSON/DOM proof is preserved and is the authoritative medium (DOM excerpts in
  `domExcerpt`/`desktop_excerpt`; full assertion JSON in each artifact). The
  4-6-1 note explicitly states DOM/JSON is authoritative if PNGs render too
  dark.
- The 4-1-2 DOM excerpt visibly shows `plan4_execute_approved_contract_missing`,
  the route, task id, and "0/100 LIVE APPLY PROOF" — i.e. a fail-closed state,
  not apply success.
- 4-3-2 captures before/after stop/resume control-contract transitions with
  `interruption_source: user_stop` and `apply_success` never displayed.
- No black/blank screenshot was used as the *sole* proof — each PNG is paired
  with a JSON/DOM artifact. (Screenshots themselves could not be visually
  re-verified by GLM in this Windows environment; this is a caveat, not a
  defect.)

## API Consolidation / Dormant Route Findings

Honest and accurate:

- `shell-registry.ts` defines three canonical routes
  (`prompt-packet`, `diff-preview`, `execute-approved`), one supporting
  (`durable-runs`), and four dormant (`codex-adapter`, `bounded-diff-preview`,
  `research-preview`, `helper-agents-preview`). Each dormant route has a
  non-empty `dormantReason` and `operatorSurface` (test asserts
  `dormantReason.length > 20`).
- Dormant routes emit `x-spiritos-plan4-route-status: dormant` and
  `x-spiritos-plan4-canonical-replacement` headers; advisory bodies include
  `plan4_route_status: dormant`. Confirmed in `codex/route.ts` and the 4-5-2
  live route proof JSON for all four dormant routes.
- Canonical replacement pointers are accurate (they point back to the canonical
  sequence `/v1/decisions/prompt-packet -> /v1/verification/diff-preview ->
  /v1/actions/execute-approved`, or the relevant prefix).
- No parallel state engine or backend substitute was introduced. Plan 4 added
  UI ledgers + a route registry + dormant headers; it did not add a new worker,
  provider, or backend execution path.
- The 4-5-2 live proof shows dormant routes still expose
  `apply_authority:false`, `commit_authority:false`, `push_authority:false`,
  `hidden_execution_started:false` — they do not launder into apply authority.

## Control Authority Findings

`/coding` does not expose or imply hidden authority:

- `plan43ControlAuthorityItems` hardcodes
  `apply_without_approval=false`, `commit=false`, `push=false`,
  `os_process_kill=false`. These are honest "no authority" constants, not
  dynamic flags that could flip to true.
- `stop_or_kill` control resolves to `no_process_kill_exposed` when idle and
  `available_as_reviewable_stop` when a durable suite is running — it routes
  through `/v1/coding/runs/[runId]`, not an OS kill.
- Dormant route bodies explicitly carry `approval_authority:false`,
  `apply_authority:false`, `commit_authority:false`, `push_authority:false`,
  `write_authority:false` (4-5-2 proof).
- No commit/push/package/env/secrets/protected-path access is exposed by the
  Plan 4 changes. `isProtectedApplyPath` in execute-approved additionally
  blocks `.env*`, `.pem`, `.key`, `source_proxy/data/`, `backend/volumes/`,
  `backend/searxng_data/`, `.spirit-backups/`.

## Verification Realism Findings

Mixed but honest:

- Tests are focused per increment and match the changed behavior at the
  string-contract level (presence of ledger builders, authority constants,
  fail-closed reason codes; explicit `not.toContain` fake-GO guards).
- The execute-approved fail-closed test is behavior-level (constructs a 200
  response missing fields and asserts the 502 body) — strong.
- The shell-registry and cockpit tests are source-text assertions; they prove
  the contract strings exist but would not catch a logic regression that
  rendered the wrong value while keeping the constant. This is a realism gap,
  partly compensated by browser DOM excerpts.
- status.json records each focused check with `cwd: /home/source/SpiritOS` and a
  `PASS_*` result. These are honest records; GLM could not re-run them on the
  Windows `Z:\` drive (vitest module-resolution failure for every suite), so
  fresh local confirmation was not possible in this environment.
- Final phase 4.6 is docs/proof-only; the operator check (`operator-check.sh`)
  validates JSON well-formedness, presence of required planning files, absence
  of forbidden completion flags, and no empty planning dirs. Reasonable.

## Handoff / Status Laundering Findings

No laundering or overclaiming found:

- `status.md`, `status.json`, `next-plan-handoff.md`, and the final closeout
  packet consistently state `PLAN4_FINAL_CLOSEOUT_READY_FOR_BRITTON_REVIEW` and
  `next_plan_authorized: false`. Each explicitly says "Do not start Plan 5/6"
  and "Plan 5/6 requires Britton approval before any implementation begins."
- No document claims Plan 5 or Plan 6 started or was approved.
- The final verdict does NOT claim full production daily-driver readiness. It
  scopes itself to "browser, live-route, operator, responsive, accessibility,
  and closeout proof" for the `/coding` UI/API consolidation. It does not assert
  end-to-end autonomous coding or binary whole-brain acceptance (that is Plan
  5/6).
- `gate-manifest.template.json` lists `fake_productive_go` and
  `preview_only_completion`/`advisory_only_completion` as forbidden states; the
  operator check enforces their absence in `status.md`.
- One minor inconsistency (INFO): `status.json`'s
  `increment_4_4_2_browser_proof` points at the 4-4-1 browser proof path (a
  reuse), but 4.4.2 itself is documented as a productive-truth *contract*
  increment whose packet is the MD contract, so this is a pointer reuse, not a
  false claim.

## Protected-Scope Findings

No protected scope was touched by Plan 4:

- The forbidden-path scan over `e11e940a^..d74d80ab` returned zero hits for
  `.env`, secret, Jellyfin, media, SpiritFlix, Mac optimizer, Obsidian,
  `package.json`, `package-lock`, `.xml`, `repomix`, `plan-05`, or `plan-06`.
- Plan 4 source changes are confined to `src/app/v1/actions/execute-approved`,
  `src/app/v1/coding/*` (dormant headers), `src/lib/coding/shell-registry*`,
  and `src/components/coding/CodingCockpitShell*` plus their tests. The final
  closeout commit added only docs/JSON/PNG under `docs/.../plan-04/`.
- No package/env/generated XML/repomix files were staged.

## Findings Table

| ID | Severity | Area | Evidence | Impact | Recommendation |
|----|----------|------|----------|--------|----------------|
| F-1 | MEDIUM | Verification realism | Cockpit tests use `readFileSync().toContain(...)` source-text assertions (e.g. test lines 1107-1187) rather than rendered DOM assertions for ledger field values. | A logic regression rendering wrong values while keeping string constants would pass these tests. | For Plan 5, add render-level assertions (mount component, assert DOM text for at least task_id/trace_id/reason_code/authority flags). Not a Plan 4 blocker. |
| F-2 | MEDIUM | Verification environment | `npx vitest run` fails on the `Z:\` Windows drive root for ALL suites (`Cannot find module 'Z:\@id\Z:\node_modules\vitest\dist\index.js'`). GLM could not re-run tests locally. | Fresh local PASS confirmation unavailable in this environment; audit relies on recorded `/home/source/SpiritOS` results + source inspection. | Re-run the full Plan 4 focused suite on `/home/source/SpiritOS` (or a non-drive-root path) during Britton review to refresh green. |
| F-3 | LOW | Browser proof medium | Screenshots could not be visually re-verified by GLM in this environment; DOM/JSON is authoritative per the artifact notes. | Minor: screenshot readability asserted but not independently re-checked. | Already mitigated by DOM/JSON authoritative policy; no action required for Plan 4. |
| F-4 | LOW | Status pointer reuse | `status.json` `increment_4_4_2_browser_proof` points to the 4-4-1 browser proof path. | Cosmetic pointer reuse; 4.4.2 is a contract increment with its own MD packet. | Optionally clarify the pointer or mark 4.4.2 as contract-only. No integrity impact. |
| F-5 | INFO | Test naming | Increment prompt text in proof artifacts embeds the increment id (e.g. "Plan 4.6.1 responsive proof comment"). | None on production (IDs are confined to proof JSON, never `src/`). | Acceptable for proof traceability. |

No BLOCKER or HIGH findings.

## Final Grade

**90 / 100 — A-**

Deductions: -6 for source-text (non-render) operator tests (F-1), -4 for
inability to re-run vitest locally on `Z:\` (F-2). No integrity, authority, or
overclaiming deductions.

## Final Verdict

`PLAN4_INTEGRITY_CONFIRMED_WITH_CAVEATS`

Plan 4's causal contract, fail-closed behavior, operator surface truth, dormant
route honesty, and control authority are genuine and accurately reported. The
caveats are test-method realism (source-text vs render) and an environment
limitation preventing local test re-execution on `Z:\`, not defects in Plan 4
itself. Plan 5/6 was not started. Forbidden paths were not touched.

GLM_PLAN4_INTEGRITY_AUDIT_READY_FOR_BRITTON_REVIEW
