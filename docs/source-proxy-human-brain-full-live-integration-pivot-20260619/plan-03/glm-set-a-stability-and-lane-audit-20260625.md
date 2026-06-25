# GLM Plan 3 Set A Stability + Source Proxy Lane Functionality Audit (2026-06-25)

Independent hardline audit. Audit-only. No source edits, no stage, no commit, no
push, no Set B/C, no Plan 4, no SpiritFlix/media/Jellyfin mutation. This report is
the only artifact added by this audit and is left uncommitted.

This audit supersedes neither the earlier `glm-set-a-stability-hardline-audit-20260625.md`
nor the `codex-set-a-stability-audit-20260625.md`; it independently re-verifies the
latest Set A stability claim against the live HEAD and the append-only receipts, and
adds a Source Proxy lane/context/packet/cheat audit that the prior reports did not
cover in equal depth.

## Executive verdict

`SET_A_CONFIRMED_READY_FOR_HUMAN_APPROVAL`

Plan 3 Set A is genuinely stable at HEAD `9be0ec89`. The claimed
`PLAN3_SET_A_STABLE_GO_READY_FOR_HUMAN_DECISION` is supported by real append-only
receipts: A3 passed 3x (PASS/6 sources/SOURCES_AVAILABLE/no failed gates), and full
Set A passed 2x (10/10 PASS, 0 failed, 0 blocked) with all 10 records carrying the
fresh run_id in both full runs. The anti-cheat layer is real (computed
`fake_go_detected`, anti-branch `inspect.getsource` tests, internet-required + zero
sources → BLOCKED_ENV, model provenance stripped from the code-owned packet shell).
The prior GLM hardline audit's root-cause fixes were actually landed (widened
`DECISION_VERB_VOCABULARY`, generic stabilized lane with `temperature=0.03` /
`num_predict=6000`, per-run-id append-only receipts).

This is **not** a rubber stamp. Two honest caveats do not block Set A approval:

1. `MISSING_EPHEMERAL_TMP_PROVIDER_EVIDENCE` — the direct SearXNG 10x file is under
   `/tmp` and was not present on this audit host. The durable provider proof survives
   inside every receipt's `research_provider_debug` (real SearXNG attempts, latencies,
   result counts), so this does not weaken the Set A claim, but durable provider proof
   should be moved into the docs tree before Set B research-heavy prompts.
2. A3-only run `summary.json` aggregate counts are inflated by carry-forward
   (`pass_count=10`, `verdict=GO` for what was an A3-only execution; non-A3 records
   carry `run_id=None`). This is receipt-hygiene noise, not a cheat: the A3.json
   receipts themselves are standalone-valid and honestly PASS, and the per-record
   `run_id` tagging distinguishes fresh from carried records. The two full Set A
   summaries are clean (all 10 records fresh).

Set B/C were not run. Plan 4 was not started. No source files were edited.

## Evidence reviewed

Docs:
- `final-set-a-stability-readback-20260625.md`
- `final-set-a-stability-rerun-20260625.md`
- `codex-set-a-stability-audit-20260625.md`
- `research-provider-stability-rerun-20260625.md`
- `generic-model-contract-stability-rerun-20260625.md`
- `glm-set-a-stability-hardline-audit-20260625.md` (prior, earlier-state)
- `debugger-diagnostic-standard-20260623.md`
- `backend/searxng.yml`
- `continuation-3x10-dryrun/battery-v4.1.md` + `stage-plan.md`

Receipts (append-only per-run-id):
- `runs/run-20260625T121016Z/` (A3)
- `runs/run-20260625T121558Z/` (A3)
- `runs/run-20260625T121858Z/` (A3)
- `runs/run-20260625T122144Z/` (full Set A)
- `runs/run-20260625T124450Z/` (full Set A)

Runner source:
- `continuation-3x10-dryrun/set-a-rerun/_stage4r_runner.py`
- `source_proxy/tests/test_plan3_stage4r_packet_runner.py`
- production `source_proxy/decision/expectation_scoring.py`,
  `source_proxy/tasks/long_running.py`

## Current HEAD / baseline

- repo path discovered: `Z:\` (task assumed `/home/source/SpiritOS`; that Linux path
  does not exist on this win32 host — repo is the working directory, as the prior GLM
  audit also found)
- branch: `integration/cleanup-plan3-debug-20260623` ✓
- HEAD: `9be0ec8911b9d94f487b6b9e4aaea917240ebbac` ✓ (matches required)
- staged files: none ✓
- dirty tracked source files: none (`source_proxy`, `backend` clean) ✓
- untracked: the audit docs + 7 run dirs under the audited evidence root only; no
  unexpected dirty Source Proxy source files ✓

## Direct SearXNG proof

`MISSING_EPHEMERAL_TMP_PROVIDER_EVIDENCE`

- `/tmp/spiritos-final-set-a-stability/direct-searxng-10x.jsonl`: **not present** on
  this audit host (checked `/tmp`, `$TEMP`, `$LOCALAPPDATA/Temp`). The Codex audit
  itself flagged this file as ephemeral under `/tmp`.
- Per Phase 3 rule, this is **not** an auto-fail. Durable provider proof survives
  inside the receipts: every research prompt's `research_provider_debug` records real
  SearXNG attempts (`searxng: used`, `searxng_result_count=6`, `searxng_latency_ms`
  in the ~1.4s range, `searxng_provider_url_used=http://127.0.0.1:8080`,
  `failure_classification=SOURCES_AVAILABLE`, `retry_count=0`).
- Recommendation: before Set B research-heavy prompts, capture a durable direct
  SearXNG proof into the docs tree so provider stability is not relying on `/tmp`.

## A3 3x proof

All three A3-only append-only runs contain `A3.json` + `summary.json`. A3 receipts
verified independently:

| Run | final_status | source_count | retry | classification | failed_gates | local_fallback | fake_go |
| --- | --- | ---: | ---: | --- | --- | --- | --- |
| `run-20260625T121016Z` | PASS | 6 | 0 | SOURCES_AVAILABLE | [] | False | False |
| `run-20260625T121558Z` | PASS | 6 | 0 | SOURCES_AVAILABLE | [] | False | False |
| `run-20260625T121858Z` | PASS | 6 | 0 | SOURCES_AVAILABLE | [] | False | False |

A3 stable PASS/PASS/PASS: **confirmed**. A3 rides the generic stabilized lane
(`selected_work_lane=generic_stabilized_research`,
`selection_basis=task_shape_internet_required_not_prompt_id`,
`temperature=0.03`, `num_predict=6000`) — the exact fixes the prior GLM hardline
audit recommended (drop temperature, raise num_predict, widen verb vocabulary).

## Full Set A 2x proof

Both full Set A runs contain `A1.json`–`A10.json` + `summary.json`. **All 10 records
carry the run's run_id in both runs** (no stale carry-forward in the full runs).

| Run | pass | failed | blocked | Set B | Set C | Plan 4 | all records fresh |
| --- | ---: | ---: | ---: | --- | --- | --- | --- |
| `run-20260625T122144Z` | 10 | 0 | 0 | not run | not run | not started | yes (10/10) |
| `run-20260625T124450Z` | 10 | 0 | 0 | not run | not run | not started | yes (10/10) |

Per-prompt (identical in both runs): A1–A6 PASS / 6 sources / SOURCES_AVAILABLE;
A7,A8,A10 PASS / 0 sources / UNKNOWN_NEEDS_HUMAN (internet_required=false — see
A7/A8/A10 analysis); A9 PASS / 6 sources / SOURCES_AVAILABLE. No failed gates on any
prompt. No local fallback. No fake_go.

Summary flags (both full runs):
- `final_status_derived_by_grader: true`
- `fake_go_detected_computed: true`
- `hardcoded_sources_used: false`
- `hardcoded_plans_used: false`
- `old_generator_disqualified: true`
- `no_set_b_run / no_set_c_run / no_plan4_work: true`

## Append-only receipt proof

- A3-only runs: `A3.json` (the actual A3 evidence) is standalone-valid and honest.
  `summary.json` carries all 10 prompt records but only the A3 record has the fresh
  `run_id`; A1,A2,A4–A10 records carry `run_id=None` (carry-forward from prior runs).
  → This inflates A3-only summary aggregates to `pass_count=10` / `verdict=GO`, which
  is **misleading for A3-only summaries** but does not touch the A3 receipts. Receipt
  hygiene caveat, not a cheat; flagged NEEDS_HUMAN_REVIEW.
- Full Set A runs: clean. All 10 records fresh, real run_ids, real trace_ids.

## Lane functionality table

| Lane | Required for | Evidence | Status | Honest skip? | Concern |
| --- | --- | --- | --- | --- | --- |
| route_decision | all | lanes_invoked on every receipt | real | n/a | none |
| task_spec | all | lanes_invoked; task_id per prompt | real | n/a | none |
| plan3_durable_task | all | lanes_invoked; latest_consumer_event_id | real | n/a | none |
| live_model | all | model_call_attempted=true; gemma3n:e4b via ollama | real | n/a | model served on Linux box; not live-reproducible on this win32 host |
| current_research (SearXNG) | A1–A6,A9 (internet_required) | research_provider_debug, 6 sources, real domains | real | A7/A8/A10 honestly skip (internet_required=false) | provider proof ephemeral in /tmp |
| repo_context | A2–A10 | repo_files_read real paths | real | A1 honestly skips (pure research) | none |
| structured decision packet | A2/A5/A9 (declared) | code_owned_packet_shell_status.assembled, raw_source_registry 6 real URLs | real | others ride generic lane by task shape | declared benchmark rubric, not hidden |
| generic_stabilized_research | A1,A3,A4,A6 + future Set B/C | generic_lane_sampling_contract, task_shape basis | real | n/a | none — generalizes |
| verifier / browser | none in Set A | verification_result=not_required | honest skip | yes (research/planning prompts need no functional verifier) | Set B patch prompts WILL require this lane — untested at Set A |
| repair / recovery | none in Set A | lanes_not_required lists them | honest skip | yes | Set B/C may exercise; untested at Set A |
| policy_gate | A2,A6 (POLICY_REQUIRED) | policy_event_present=true | real | others honestly skip | none |
| mac_worker | A5 only | mac evidence signals | real | others honest skip (mac_required=false) | none |
| anti-cheat / fake-go | all | computed per receipt; anti-branch tests | real | n/a | none |
| packet assembly | A2/A5/A9 | assemble_code_owned_decision_packet builds from model body + code-owned evidence | real (code-owned) | n/a | model_provenance_stripped confirmed |

## Context / relevance table

| Prompt | Research relevant? | Repo context relevant? | Packet real? | Concern |
| --- | --- | --- | --- | --- |
| A1 | yes (reddit/pkhex markers) | not required (pure research) | n/a (generic lane) | none |
| A2 | yes (chrome MV3/native messaging) | yes (long_running tasks/route.ts) | yes — 6 real URLs, model provenance stripped | none |
| A3 | yes (android/compose/kotlin) | yes (long_running/route/CodingShell) | n/a (generic lane) | none |
| A4 | yes (github/obsidian/youtube) | yes (obsidian modules) | n/a (generic lane) | none |
| A5 | yes (local LLM tools) | yes (repo routing) | yes — structured packet | none |
| A6 | yes (tinymediamanager/jellyfin) | yes (SpiritFlix/jellyfin-client) | n/a (generic lane) | none — media research only, no media mutation |
| A7 | n/a (internet_required=false) | yes (durable_execution/long_running) | n/a | none — REAL_CONTEXT_USED |
| A8 | n/a | yes (long_running/CodingShell) | n/a | none — REAL_CONTEXT_USED |
| A9 | yes (local LLM tools) | yes (repo routing) | yes — structured packet | none |
| A10 | n/a | yes (durable_execution/current_research) | n/a | none — REAL_CONTEXT_USED |

No `GENERIC_NO_CONTEXT`, no `IRRELEVANT_CONTEXT`, no `MODEL_HALLUCINATED_CONTEXT`,
no `MODEL_OWNED_PROVENANCE`. A2 `raw_source_registry` confirmed: 6 distinct real
external URLs, `source_urls_from_code=true`, `model_provenance_stripped=['manifest.json','route.ts']`.
Model-owned fields (`decision_summary`, `reasoning_summary`, `risk_notes`) are
explicitly listed as model-owned and bounded separately from code-owned source URLs.

## Cheat / overfit scan

Targeted ripgrep over `plan-03` docs + runner + `source_proxy`:

- prompt-specific branches (`pid == "A3"` etc.): all hits are receipts/reports/fixtures.
  The one runner source hit (`_stage4r_runner.py:806`) is a **comment forbidding**
  `pid == "A3"` branches. → `BENIGN` / anti-cheat guard.
- `pid == "A2"/"A5"/"A9"` branches: present in `select_work_product_lane`,
  `prompt_specific_failed_gates`, `PACKET_CONTRACTS`, `decision_packet_prompt`,
  `positive_synthetic_packet` (selftest scaffold only). → `DECLARED_RUBRIC`
  (benchmark-tailored, not hidden, not applied to A3).
- anti-branch tests: `test_packet_assembler_has_no_prompt_specific_branches` asserts
  no `pid == "A2"/"A5"/"A9"` in production `assemble_code_owned_decision_packet`;
  `test_research_change_repair_has_no_prompt_specific_branches`,
  `test_decision_line_vague_guard_has_no_prompt_specific_branches`,
  `test_run_stability_check_has_no_prompt_specific_branches`,
  `test_research_change_no_specific_decision_uses_general_vocabulary_not_a3_tuning`
  all assert no `pid == "A3"` and use of general `DECISION_VERB_VOCABULARY`.
  → `EXPECTED_TEST_GUARD` (real defense via `inspect.getsource`).
- fake GO / fallback PASS: only hit is the self-check assertion at runner:2522 that
  FAILS if internet-required PASS carries local fallback. `local_fallback_used`
  hardcoded `False` in receipts is the honest default. → `BENIGN_TEST_GUARD`.
- production `source_proxy` PASS returns: `expectation_scoring.py:293` is the terminal
  branch of a real multi-gate scorer (all dimensions > thresholds, behavior verified);
  `long_running.py:5783` is `allow_fallback_to_pass: False` in `TRIAL_MODE_BAN_CONTRACT`
  (anti-cheat). → `REAL_LOGIC` / anti-cheat.
- hand-authored A2/A5/A9 recommendation strings: live in `positive_synthetic_packet`
  (selftest scaffold), NOT production `assemble_code_owned_decision_packet`.
  → `BENIGN_TEST_FIXTURE` — no scaffold pretending to be runtime.
- zero-source PASS: only A7/A8/A10, all `internet_required=false` (see below).
- hardcoded_sources_used / hardcoded_plans_used / old_generator_disqualified: all
  `false`/`true` in summaries. → no cheat.

**Cheat verdict: NO_CHEAT.** No hardcoded PASS/GO, no A3-specific hack, no fake-source
acceptance, no model-owned provenance, no silent fallback→PASS, no swallowed
exception→GO, no scaffold masquerading as runtime.

## A7/A8/A10 zero-source PASS analysis

Acceptable. A7 ("next highest leverage thing from source proxy context"), A8 ("plan
for a dashboard showing a proxy run"), A10 ("review this repo context and plan what
an outside ai should work on") are **repo-context prompts**, not internet-research
prompts. Receipts confirm `internet_required=false`, `live_search_used=false`, and
the grader enforces `internet_likely_required and not sources → BLOCKED_ENV` — so a
zero-source internet-required prompt cannot be PASS. A7/A8/A10 invoked `repo_context`
and read real repo files (`durable_execution.py`, `long_running.py`,
`CodingCommandCenterShell.tsx`), and their recommendations reference those files.
Zero live sources here is correct, not suspicious.

## Set B readiness / generalization risk

Set B readiness: **NEEDS_READBACK** (not READY, not NOT_READY).
Generalization risk: **MEDIUM** (down from the prior audit's HIGH for A3 specifically;
MEDIUM overall because Set B is a different task class).

- Set B prompts (B1–B10) are safe build/patch/implementation asks ("make a tiny safe
  patch", "add a validator", "make a cli"). They are a **different task class** than
  Set A research/planning and will require lanes Set A mostly did not exercise:
  real source patches, `created_modified_files`, `verifier`, `protected_path_block`,
  `repair`/`recovery`. Set A receipts show `verifier_required=false` throughout, so
  the verifier/patch lane is **untested at Set A**.
- No declared Set B/C rubrics exist (no `PACKET_CONTRACTS` for B*, no hand-authored
  recommendations). Set B prompts route by task shape — fine in principle, but each
  patch prompt's pass criteria (did it produce a real, verified, safe diff?) must be
  defined before running, or the grader has no honest contract for them.
- Gates are in place: stage-plan mandates human stop after each stage, no Set B until
  Set A reviewed, max 3 auto-fix attempts, Stage 9 "No fake GO", append-only receipts.
- Provider stability should be rechecked before any research-heavy Set B prompt (B8/B9
  lean research-ish); move durable SearXNG proof into docs first.

Required next gate before Set B: (1) Britton approves Set A closeout; (2) declare a
Set B per-prompt rubric for the patch/verifier lanes (what counts as a real, verified,
safe patch); (3) capture durable provider proof into docs.

## Validation results

- `git diff --check`: PASS (clean)
- `test_plan3_stage4r_packet_runner.py -q`: PASS, 39 passed
- `test_research_preview.py -q`: PASS, 10 passed
- `test_scout_research_bridge.py -q`: PASS, 8 passed
- backend slice (8 modules: status_codes, anticheat_registry, brain_switch_contract,
  packet_decomposition, prompt_packet_context_metadata, model_lane_observability,
  model_lanes, verifier_lane): PASS, 133 passed

Counts match the claimed evidence exactly. No skipped check was called PASS.
Environment note (consistent with prior GLM audit): `.venv/bin/python` is a Linux
venv not executable on this win32 host; system `python3` (3.13) used — all deps
import cleanly.

## Blockers

None for Set A approval.

## Caveats

1. `MISSING_EPHEMERAL_TMP_PROVIDER_EVIDENCE` — direct SearXNG 10x file is in `/tmp`,
   not durable. Receipts carry durable provider proof; recommend moving a captured
   provider proof into docs before Set B.
2. A3-only `summary.json` aggregates are inflated by carry-forward
   (`pass_count=10`/`verdict=GO` for A3-only runs); A3.json receipts are clean.
   Receipt-hygiene noise, not a cheat.
3. Model lane live-reproducibility: `gemma3n:e4b` is served on the Linux box; not
   live-reproducible on this win32 audit host. Receipts are the evidence.
4. This audit confirms Set A stability only. It does not prove Set B/C generalization;
   the patch/verifier lane is untested at Set A.
5. Codex's `SET_A_STABILITY_CONFIRMED_FOR_HUMAN_REVIEW` is accurate for the current
   HEAD/receipts and supersedes the earlier (pre-fix) GLM hardline verdict for Set A
   readiness.

## Final recommendation

`SET_A_CONFIRMED_READY_FOR_HUMAN_APPROVAL`. Set A is real, stable, and honest. The
prior GLM hardline root-cause fixes were genuinely landed and validated by 2x full
Set A + 3x A3 append-only receipts, a real anti-cheat layer, and a passing 190-test
focused+backend slice.

Exact next step: hand Set A to Britton for human approval. Do not start Set B until
(a) Britton approves Set A closeout, (b) a Set B per-prompt patch/verifier rubric is
declared, and (c) durable SearXNG provider proof is captured into the docs tree.

## Safety

- source edited: no
- committed: no
- pushed: no
- Set B/C run: no
- Plan 4 started: no
- SpiritFlix/media/Jellyfin touched: no
