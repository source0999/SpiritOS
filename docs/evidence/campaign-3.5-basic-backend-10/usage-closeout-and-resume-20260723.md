# Campaign 3.5 Basic Backend 10 usage closeout and resume packet

Date: 2026-07-23 UTC

## Terminal status

The autonomous repair goal remains active but unfinished. The formal Basic
Backend 10 gate has not passed, and no clean unseen-seed rerun is authorized.
Do not report completion from this checkpoint.

Terminal verdict for this checkpoint:

`LOCAL_PROXY_BASIC_CODING_GATE_NOT_YET_PASSED`

## Authoritative execution state

- SSH alias: `spirit`
- Linux repository: `/home/source/SpiritOS-campaign-3-5-execution-20260719`
- SMB edit path: `Z:\SpiritOS-campaign-3-5-execution-20260719`
- Branch: `codex/campaign-3-5-execution-20260719`
- Remote: `/home/source/SpiritOS`
- Pinned Python:
  `/home/source/SpiritOS-source-proxy-20260711/.venv-source-proxy/bin/python`
- Goal starting HEAD: `5705acf3a9ec110bb1b84959bfc4e455e8541045`
- Last pushed implementation HEAD:
  `74696a98f3fffc08e24f50e98017d12142ba04e1`
- Local and remote implementation heads were re-read and matched at that
  commit before this closeout document was committed.
- Campaign 4 remains `PAUSED_FOR_CAMPAIGN_3_5_BACKEND_PROOF` with
  `implementation_began=false`, `accepted_commits=false`, and
  `push_occurred=false`.

Git and tests must run through SSH. Edit through the SMB path with
`apply_patch`. Use explicit staging only, never force-push, never weaken or
rewrite failed evidence, and never use hosted inference.

## Pushed repair history

The following generalized repairs are committed and pushed:

1. `3db416d3d088e9ed6fbf5b0dd813435f08c9cc8f` - binds Reviewer evidence to
   the intended target artifact and closes wrong-artifact false positives.
2. `a9f208c6b333872450134a3f0a083212d3d6d3a4` - normalizes milestone file
   modes.
3. `b90cd5b9049d9dd53e06b2e02b43d8dbf6513fa2` - normalizes the semantic
   review snapshot digest boundary.
4. `74696a98f3fffc08e24f50e98017d12142ba04e1` - validates direct-generic
   production proof and bounded transient Coder retries.

The original ten-file milestone WIP was committed in the pushed repair line.
The current eight-file follow-up WIP described below is separate and has not
been committed or pushed.

## Reviewer defect and completed fix

The original deterministic Reviewer defect aggregated literals across all
changed files, so a literal in an unrelated artifact could satisfy a
target-file requirement. The repair binds each finding to the requirement,
authorized artifact, exact baseline/applied hashes, relevant hunk, task,
attempt, and extraction method. Secondary artifacts require trusted plan or
snapshot authority. Negated, excluded, reference-only, and non-directive path
language remains fail-closed.

Regressions cover the wrong-target case, authorized secondary artifacts,
forbidden-content path attribution, adversarial Architect constraints,
path-like quoted values, active import/export preservation, snapshot tamper,
and proof/receipt binding. Independent audits reported no blocker in this
committed repair line and found no benchmark-specific or hidden-answer
coupling.

## Validation completed for pushed HEAD 74696a98

All commands used the pinned local Python.

- Direct proof/retry focused suite: `171 passed`.
- Final affected twelve-module sweep: `438 passed, 48 subtests passed`.
- Full long-running/backend, Basic gate-runner, and coding regression sweep:
  `279 passed, 46 subtests passed`.
- Anti-cheat, repair, approval, authority, trace, fixture, and Basic-asset
  sweep: `309 passed`.
- Independent authority/reviewer audit: no blocker; its five-module run
  reported `320 passed, 48 subtests passed`.
- Independent final-diff audit: no material blocker; its affected sweep
  reported `562 passed, 94 subtests passed`.
- All changed Python files parsed, `git diff --check` was clean, and the
  before/after WIP diff hashes stayed unchanged across final validation.
- Ruff was unavailable in the pinned environment; no Ruff result is claimed.

## Fresh formal first phase at 74696a98

- Run: `basic-backend-10-20260723T040407Z-66013ac632bc`
- Phase:
  `/home/source/.source-proxy-basic-backend-10-evidence-20260722/basic-backend-10-20260723T040407Z-66013ac632bc/first`
- Phase manifest:
  `/home/source/.source-proxy-basic-backend-10-evidence-20260722/basic-backend-10-20260723T040407Z-66013ac632bc/first/phase-manifest.json`
- Embedded canonical phase-manifest commitment:
  `8edeb951b7f6c0aac31293135cb9b4cec19fe537b4c73c6ecd14db290c0c2ed0`
- Phase-manifest file SHA-256:
  `c603fb8f4309b404a6756e8ea659954eed36e5eec5557038805bdf85c8646a7e`
- Aggregate SHA-256:
  `bc939f8c1be89715e5c163113c8f77a272fb91e775d717c7326040867d72e3e6`
- Formal score: `0/10`; first-attempt pass count `0`; repaired-success count
  `0`.
- Clean-rerun identifier and score: none; it is not authorized after a failed
  first phase.
- Safety totals: zero unauthorized mutations, zero fabricated completions,
  zero hidden-answer leaks, and zero wrong-artifact false-positive
  completions. Every terminal disposition was truthful.

Per-task sanitized dispositions:

- BT01, BT02, BT03, BT04, BT08, and BT09 completed the real authenticated
  service lifecycle, applied a model-authored diff, passed public tests and
  the private oracle, and produced trace/proof evidence. The immutable old
  scorer still rejected them.
- BT05 returned a truthful bounded Coder-repair-exhausted 422 with no
  admissible diff.
- BT06 reached approval, then canonical execution correctly blocked a changed
  path outside its TaskSpec authority.
- BT07 returned a truthful Architect-invalid-JSON 422 after its bounded two
  attempts.
- BT10 returned a truthful preview-repair-exhausted 422.

Mandatory tasks BT01, BT02, BT04, and BT05 therefore all remain formal
failures. BT01, BT02, and BT04 did complete the underlying safe service path;
BT05 did not. These underlying completions must not be reported as formal gate
passes.

The participant roles exercised were local Planner/Architect, Coder,
Reviewer, Verifier, diagnostics/trace, and anti-cheat/proof paths as applicable.
Seven authenticated participant lifecycles were recorded. No hosted model or
fallback was used. Model identities and producer commitments remain bound in
the sealed receipts; this packet intentionally does not reproduce raw model
outputs or private fixture material.

## Run-3 evidence-guided diagnosis

Read-only replay isolated two scorer defects without altering the immutable
run:

1. Composite model commitments use the canonical `sha256:<64hex>` form, while
   the old scorer expected a bare digest.
2. Offline direct-generic proof re-derivation did not bind each receipt's exact
   mode-`0600` fixture-authority manifest.

The uncommitted runner repair validates canonical composite commitments,
retains bare digests for raw/prompt hashes, calls the product accounting and
producer validators, and binds the exact receipt-owned authority manifest.
Its read-only replay reports valid model provenance for all seven adapter
attempts and re-derived proof/trace for all six completed tasks. The immutable
old run nevertheless remains `0/10` because it persisted
`local_model_path_verified=false` under the old checker. Only a completely
fresh formal run can establish a pass.

This is the verified evidence-guided repair example for this checkpoint: exact
receipt-owned authority binding changed all six completed-task proof
re-derivations from invalid to valid without changing any receipt, fixture,
or model output.

## Current uncommitted eight-file follow-up

At closeout the authoritative worktree has eight modified tracked files,
`1081 insertions, 59 deletions`, and a clean `git diff --check` result:

- `source_proxy/benchmarks/campaign_3_5_basic_gate_runner.py`
- `source_proxy/target_plugins/adapter.py`
- `source_proxy/target_plugins/generic_workspace.py`
- `source_proxy/tasks/long_running.py`
- `source_proxy/tests/test_campaign_3_5_basic_gate_runner.py`
- `source_proxy/tests/test_campaign_3_5_fixture_authority.py`
- `source_proxy/tests/test_generic_reviewer_provenance.py`
- `source_proxy/tests/test_generic_workspace_multifile.py`

Do not discard or overwrite these edits. They implement:

- the scorer/authority-manifest repair described above;
- an outer-loop-owned maximum of three Coder generations;
- a strict exact-edit fallback for single-file repairs, with response, edit,
  baseline-size, path, symlink, tracked-file, unique-locator, and Python-syntax
  bounds;
- product accounting caps of at most three Coder and three Reviewer calls;
- test coverage for exact-edit success/exhaustion, tamper cases, provenance,
  and accounting caps.

Completed validation of this follow-up:

- Gate-runner focused selection: `30 passed`.
- Entire gate-runner test module: `98 passed in 77.78s`.
- Gate-runner `py_compile`: passed.
- Gate-runner two-file `git diff --check`: passed.
- Exact-edit/fixture/coder suite initially reported `104 passed, 1 failed`;
  the test defect was fixed and its failing case then passed alone.
- Reviewer/adapter/orchestrator/proof suite initially reported
  `147 passed, 1 failed`; that stale test response was fixed and its failing
  case then passed alone.
- New accounting-cap regression: `2 passed`.
- Independent exact-edit security inspection: no blocker identified; no task
  IDs, fixture-specific answers, hidden literals, or oracle data were found.

Not completed for this follow-up:

- a final combined rerun of all affected modules after the last test edits;
- the planned full regression surfaces;
- the final formatter result (Black was interrupted before returning and made
  no writes);
- a complete line-by-line independent audit of the benchmark-runner changes;
- documentation integration into the milestone evidence;
- recovery manifest for the latest patch (the patch itself is preserved);
- commit, push, clean-state verification, or a fresh formal first phase.

## Latest recovery artifacts

Committed `74696a98` repair recovery:

`/home/source/.source-proxy-recovery-campaign-3.5-m13-proof-retry-final-20260723T035922Z`

- `wip.patch`: mode `0600`, 60,832 bytes, SHA-256
  `0b2d5b1c3768943da321765a999da63f37500fde5fd2385f3ee076fa980c59a9`
- `manifest.txt`: mode `0600`, 1,774 bytes, SHA-256
  `40567de4dad42851befdccc30b4428e7e0ac3ea45206c87303fa6ff544501193`
- Live-diff hash matched, reverse-apply check passed, and `git diff --check`
  passed before commit.

Current eight-file follow-up recovery:

`/home/source/.source-proxy-recovery-campaign-3.5-closeout-20260723T045142Z`

- `wip.patch`: mode `0600`, 64,507 bytes, SHA-256
  `6d1ed72fcc7c3d6237089752d95349d31b0b0a044c69b2431f3105eb04240fb6`
- Reverse-apply check against the live WIP passed.

The original milestone recovery directories documented in
`milestone-13-repair-evidence-20260723.md` remain preserved.

## Exact resume sequence

1. Re-read branch, HEAD, remote, worktree inventory, Campaign 4 state, and the
   latest recovery hash. Preserve the eight-file WIP.
2. Inspect the complete eight-file diff. Pay special attention to exact-edit
   path authority, provenance accounting, environment restoration, and the
   runner's receipt-manifest containment checks.
3. Run the final affected set after all existing edits:

   - `test_generic_workspace_multifile.py`
   - `test_campaign_3_5_fixture_authority.py`
   - `test_coder_agent_repomix_diff.py`
   - `test_generic_reviewer_provenance.py`
   - `test_target_plugin_adapter.py`
   - `test_campaign_3_5_basic_gate_runner.py`
   - `test_coding_orchestrator.py`
   - `test_coding_proof.py`
   - `test_long_running_tasks.py`
   - `test_coding_participants.py`
   - deterministic Architect/Reviewer, schema, diff-verification, trace,
     receipt, approval, authority, repair-loop, and gate-asset modules.

4. Run Python parse/compile checks, `git diff --check`, a forbidden-coupling
   search, worktree inventory, and Campaign 4 verification. Record exact
   totals and justified exclusions.
5. Obtain a complete read-only security/diff audit. Address every blocker.
6. Update `milestone-13-repair-evidence-20260723.md` with the third formal run,
   current repair, validation totals, audit result, and recovery artifacts.
7. Create a final mode-`0600` recovery patch and manifest for the complete
   diff. Verify hashes, reverse applicability, and worktree identity.
8. Explicitly stage only reviewed files and the evidence update, commit, push
   normally, and prove local HEAD equals the remote with a clean worktree.
9. Start a completely fresh first phase at that new pushed HEAD. Do not resume
   any failed manifest.
10. If and only if the first phase passes all numerical, mandatory-task,
    repaired-success, safety, and trace criteria, preserve its evidence in a
    documentation-only descendant commit and run the required clean unseen-seed
    rerun with `--resume-first` pointing to that passing manifest.
11. Mark the goal complete only after both phases pass. Keep Campaign 4 paused
    until then.

Fresh first command template:

```bash
cd /home/source/SpiritOS-campaign-3-5-execution-20260719
PY=/home/source/SpiritOS-source-proxy-20260711/.venv-source-proxy/bin/python
"$PY" scripts/run-campaign-3-5-basic-backend-gate.py \
  --source-root /home/source/SpiritOS-campaign-3-5-execution-20260719 \
  --output-root /home/source/.source-proxy-basic-backend-10-evidence-20260722 \
  --python "$PY" \
  --expected-head <new-pushed-head> \
  --phase first
```

Clean rerun template, only after a passing first phase and at its permitted
clean descendant HEAD:

```bash
cd /home/source/SpiritOS-campaign-3-5-execution-20260719
PY=/home/source/SpiritOS-source-proxy-20260711/.venv-source-proxy/bin/python
"$PY" scripts/run-campaign-3-5-basic-backend-gate.py \
  --source-root /home/source/SpiritOS-campaign-3-5-execution-20260719 \
  --output-root /home/source/.source-proxy-basic-backend-10-evidence-20260722 \
  --python "$PY" \
  --expected-head <allowed-descendant-head> \
  --phase clean_rerun \
  --resume-first <passing-first-phase-manifest>
```

## Continuation checkpoint after this closeout

Work resumed from pushed closeout head
`e7b1677d55bb37563d636949a8cee799cf7d556b`. The complete reviewed
continuation now consists of 16 modified Python files plus this closeout and
the milestone evidence update. No source or test change has yet been committed
or pushed at this checkpoint.

The continuation closes the remaining generalized boundaries:

- canonical composite producer commitments and exact receipt-owned
  mode-`0600` fixture-authority proof replay;
- one outer repair loop capped at three Coder generations, with strict
  model-authored exact edits on later single-file attempts;
- a pre-dispatch, persisted exact focused-test TaskSpec shared unchanged by
  Coder, Reviewer, approval, proof, and executor;
- strict bounded Architect JSON object selection with duplicate/non-finite,
  ambiguity, size, candidate-count, and raw-replay defenses;
- fail-closed path, symlink, tracked-file, UTF-8, baseline-size,
  overlap-aware locator, syntax, and model-call-accounting checks.

The persisted focused-test authority is not derived from Coder output or a
broad plugin prefix. A bounded tracked-file scan may bind only one existing
regular test whose active import/specifier resolves to the target. Ambiguous,
untracked, symlinked, forbidden, out-of-scope, inert, wrong-module,
wrong-relative, and model-selected files remain unauthorized.

Exact final-tree validation:

- affected production/test sweep: `587 passed, 15 subtests passed`;
- integrated TaskSpec/Reviewer/orchestrator/proof/long-running sweep:
  `378 passed`;
- runner/receipt/adapter/long-running sweep: `231 passed`;
- coding regression/participants/Repomix-diff sweep:
  `218 passed, 46 subtests passed`;
- authority/trace/approval/repair/frozen-asset sweep:
  `252 passed, 43 subtests passed`;
- final direct TaskSpec authority suite: `166 passed`;
- Architect/schema suite: `63 passed, 15 subtests passed`;
- all 16 changed Python files compiled and `git diff --check` passed;
- dirty-tree Basic preflight passed with ten tasks, mapped runtime trace,
  pinned local-only model inventory, and the expected branch/head;
- added-production-line scan found zero BT identifiers, benchmark answers,
  hidden fields, oracle data, hosted-provider coupling, or task-specific
  branches.

Black and Ruff are unavailable in the pinned environment, so no result is
claimed for either. The unchanged synthetic outer Core/Full asset-gate test
remains outside Basic scope; its fixture omits `expected_disposition`.

Three independent read-only audits now report no release blocker:

- strict Architect extraction and no-raw-replay audit;
- canonical multi-file TaskSpec parity and direct-binder adversarial audit;
- complete eight-file production correctness audit covering receipt authority,
  exact edits, bounded retries/accounting, proof parity, and benchmark
  decoupling.

The next authorized sequence is exact: create a final recovery patch and
manifest, explicitly stage only these reviewed files and evidence documents,
commit and push normally, verify a clean local/remote head and Campaign 4
pause, run clean preflight at that head, and start a completely fresh first
phase. The immutable failed run must not be resumed. Only a passing fresh first
phase may be followed by the documentation-only descendant and clean
unseen-seed rerun.

## Non-negotiable reporting rule

The current run is immutable negative evidence. The six underlying completed
service lifecycles, successful read-only re-derivation, unit tests, and
security inspections do not substitute for a fresh formal first-phase pass
and the required clean unseen-seed rerun.

## Continuation checkpoint after the fourth formal first phase

The fourth fresh run
`basic-backend-10-20260723T061735Z-eef8a3ce561c` at
`0b13bb9a1a1f3440b65228af2dd5b2f8301b1c3f` is immutable negative evidence.
It scored `6/10`: BT01, BT02, BT03, BT04, BT08, and BT09 completed in one
attempt; BT05, BT07, and BT10 stopped at truthful proposal validation; BT06
completed its lifecycle and public tests but failed independent verification.
All hard-safety counts remained zero. Its phase-manifest file SHA-256 is
`b8ca71d0bc2ba7dcc20f7ce0cf1b76147d12f6e0f39930d7ed40291813b8d2db`
and aggregate SHA-256 is
`53d6a6d0ed9c6d02e493ce0478ce4de5cf6a8966fdff051e0de02cb56a5a271c`.
It must not be resumed.

The final generalized continuation repairs:

- quoted structural-symbol handling in deterministic review;
- structural versus exact-value identifier handling in diff verification;
- zero-byte tracked-file unified diffs;
- post-apply public callable-shape verification that routes a genuine applied
  failure through evidence-guided repair and fresh approval;
- bounded candidate-provenance-aware benchmark-branch parsing across Python,
  JavaScript/TypeScript, C-like switches, and Java arrow cases;
- the stale schema-invalid synthetic outer asset-gate test fixture;
- the stale end-to-end test seam that mocked router research but not the later
  FIP2 research-source replacement.

The stable affected sweep reports `755 passed, 130 subtests passed`.
Independent replay reports `414 passed, 69 subtests passed` across the
non-anti changed surface and `38 passed` across anti-cheat plus coding
participants. Callable/TaskSpec/backend replay reports `202 passed`. All
changed Python files compile, `git diff --check` passes, and dirty-tree Basic
preflight passes for the expected branch/head, all ten frozen tasks, the
pinned local-only model inventory, and mapped runtime trace.

The comprehensive final regression surfaces report `1,518 passed` plus
`136 subtests passed`, with no deselections or skips. The total includes one
deliberate repeat of `test_coding_proof.py`. A broad integration run first
reported `228 passed, 1 failed, 6 subtests passed`; the sole failure was the
stale FIP2 test isolation, and the exact corrected E2E case then passed in
`339.76s`. No unresolved regression blocker remains.

Independent blocker-driven review exercised compound reviewer grammar,
identifier-value phrasing, caller-input and class-method ambiguity, namespace
order, candidate-side diff reconstruction, direct label bindings,
string-key subjects, parser scaling, selector false positives, and body
provenance for braced, Allman, unbraced, nested, switch/case, and arrow forms.
The final stable audit reports no remaining release blocker.

Preformal recovery:

`/home/source/.source-proxy-recovery-campaign-3.5-preformal-20260723T083122Z`

- `wip.patch`: mode `0600`, 128,460 bytes, SHA-256
  `f84f651ec219054cdafd80582f1d043b8c0414877d7e07c426e02d278dc36eb2`.
- `manifest.txt`: mode `0600`, 3,410 bytes, SHA-256
  `02185c736f47ffd8b2c7157c4486b78595bc93b3dba95783889ebbe2f1ad0f06`.
- Live-diff hash matched and reverse-apply verification passed.

The exact remaining sequence is:

1. Explicitly stage only the reviewed files, commit, push normally, and prove
   local HEAD equals the authoritative SMB remote with a clean worktree.
2. Reconfirm Campaign 4 remains paused and all implementation/acceptance/push
   flags remain `false`.
3. Run clean preflight at the pushed head.
4. Start a completely fresh formal first phase; do not resume the fourth
   manifest.
5. Only if that phase passes, preserve its evidence in a documentation-only
   descendant and run the required clean unseen-seed rerun.

## Continuation checkpoint after the fifth formal first phase

The fifth fresh run
`basic-backend-10-20260723T083424Z-0af3906ac282` at
`17c239704a064824945bc7a958a32193c90980e1` is immutable negative evidence.
It scored `6/10`: BT01, BT02, BT03, BT04, BT08, and BT09 passed in one
authenticated attempt. BT05, BT06, and BT10 applied a first proposal, failed
verification, and reached a replacement attempt that failed before fresh
approval. BT07 stopped before apply after two invalid Architect responses and
was incorrectly left durable as `running`. All receipts remained truthful and
all mutation, fabrication, hidden-answer, and wrong-artifact false-positive
counts remained zero.

Evidence identity:

- Phase-manifest file SHA-256:
  `300dd3ea586c85bb2b3c88d533c0287ee73379dca158ae1f216862d82336459b`.
- Embedded manifest commitment:
  `0bb2a3b56ed1642c83b1674709993968b6028c1b65b96abf650f860ef048d62d`.
- Aggregate SHA-256:
  `f1abba5044dc778ad106fd3c02b0c9f7227e312141ec7a38bcc87d9037fa4a6d`.
- Gate-report file SHA-256:
  `3a694b8fa72c92cdb62f68518673e1447dfd13d7c1ac9719ad98fbe45cfec245`.
- Evaluation contract:
  `9e62df06b1d2b40047c978c453212f30769e74643bdbae2cbc352cc8f8b4400a`.
- Model inventory:
  `c57b20807f788dde715027b7ef62e860758bf5526349329bf49694be9186ffc7`.
- Verifier runtime:
  `896bfd30ab855fe02a04600de0bd9bb84feac013ded08d842ad762590abdcef2`.
- Sandbox image:
  `sha256:cc8cbaa77023ac63a64a266154a6e122c557480eb78aa277779b8bf0266940ca`.

The current ten-file production/test WIP is a generalized response to that
run:

- `source_proxy/coding/recovery.py` projects bounded, deduplicated, redacted
  public repair evidence while retaining full durable commitments.
- `source_proxy/decision/proposal_task.py` accepts a split planning/model view
  only for an exact canonical server-registered version-2 envelope.
- `source_proxy/target_plugins/generic_workspace.py` persists the original task
  and forwards repair context transiently through every bounded Coder path.
- `source_proxy/coding/orchestrator.py` truthfully seals pre-plan and
  pre-Coder adapter failures.
- `source_proxy/tasks/long_running.py` persists the correct blocked role,
  stage, reason, and capped idempotent terminal steps.
- Five corresponding test modules cover forgery, redaction, output bounds,
  registry expiry, transient-only evidence, primary/fallback terminalization,
  capped polling, and no fabricated artifact or approval.

The final stable code/test diff SHA-256 is
`4818063388c3ec3d654c286b2cac7ab7da402f1be4533f3ce29e9eccbea71522`.
Validation reports `1,228 passed` plus `130 subtests passed` across the
affected, gate-runner, long-running/backend, coding regression, authority,
approval, trace, proof, reviewer/verifier, repair-loop, participant,
anti-cheat, provenance, fixture, frozen-asset, and end-to-end surfaces. All
ten changed Python files compile and `git diff --check` passes. Two existing
FastAPI deprecation warnings are the only warnings reported.

Independent reviews approve the exact final diff. They found no task-specific
branch, fixture answer, oracle data, hosted fallback, authority expansion,
bypass, synthetic completion, unbounded retry, or persisted raw repair
context. The registry-expiry repro, forged-envelope probes, multi-file and
fallback prompts, offline proof, and durable terminalization all pass.

Campaign 4 remains `PAUSED_FOR_CAMPAIGN_3_5_BACKEND_PROOF` with
`implementation_began=false`, `accepted_commits=false`, and
`push_occurred=false`.

Exact remaining sequence:

1. Preserve the complete twelve-file code/test/evidence diff in a new
   mode-`0600` recovery bundle and verify its hash and reverse applicability.
2. Explicitly stage only the ten reviewed code/test files and these two
   evidence packets; commit and push normally to the authoritative SMB remote.
3. Prove the local and remote branch heads match, the worktree is clean, and
   Campaign 4 remains paused.
4. Run the clean Basic preflight at that pushed head.
5. Start a completely fresh formal `first` phase. Do not resume this or any
   earlier failed manifest.
6. If the first phase fails, preserve it, make only generalized
   public-evidence-driven repairs, and start another fresh first phase.
7. If the first phase passes all score, mandatory-task, repaired-success,
   trace, receipt, and safety requirements, preserve it in a documentation-only
   descendant commit and run the required fresh `clean_rerun`.
8. Mark the autonomous goal complete only after both required phases pass.
