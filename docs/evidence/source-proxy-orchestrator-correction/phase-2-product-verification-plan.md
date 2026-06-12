# Source Proxy Orchestrator Correction Phase 2 Product Verification Plan

## Status

* Phase 2 planning only
* no runtime changes authorized
* no test changes authorized
* no provider/model calls authorized
* no benchmark execution authorized
* no real app mutation authorized
* implementation/execution requires Britton's later explicit approval

## Verification Goal

Phase 2 will prove that Product mode is now a generic Source Proxy orchestration path, not homepage-specific scaffolding and not raw Pure mode autonomy.

The verification must show that Source Proxy Product mode decides task shape, safety, context, workspace, and allowed scope, while the model still authors concrete target paths, file contents, and executable actions. Runtime must execute only validated model-authored actions. Receipts must separate proxy decisions from model-authored output clearly enough to audit success and failure without reading tea leaves.

This phase is about product truth, not benchmark inflation. Product success means useful orchestration with no-cheat proof. Pure success means diagnostic benchmark eligibility under intentionally reduced support. Those are separate labels.

## Verification Boundaries

Local/mocked verification:

* Uses existing local tests and deterministic mocked model outputs.
* Runs under the repo venv on `source-server`.
* May inspect generated receipts from mocked loop runs.
* May verify parser, executor, safety, Product/Pure receipts, and no-cheat fields.
* Does not call providers or local models.
* Does not mutate real app files from trial prompts.

Smoke verification:

* May run existing smoke scripts only if they support mocked or fixture-based model responses.
* Must use disposable workspaces only.
* Must preserve raw transcripts, parsed actions, receipts, diffs, and scores.
* Must not make live provider/model calls unless a later approval explicitly permits them.

Live provider/model verification:

* Not approved by this plan.
* Requires local/mocked verification to be GO first.
* Requires Britton's later explicit live-verification prompt.
* Must use disposable workspaces only and a tiny prompt set first.

Benchmark verification:

* Not approved by this plan.
* Must remain separate from Product verification.
* Must not treat Product orchestration support as benchmark-pure success.
* Requires a later explicit benchmark approval gate.

This plan approves planning only. Later prompts must separately approve each execution level.

## Product vs Pure Assertions

Product mode must:

* use proxy task-shape classification
* use a safe workspace decision
* provide constraints and the generic action contract
* provide allowed/protected boundaries
* optionally provide artifact class or extension boundaries
* require model-authored target path, content, and action before execution
* record route type, task shape, proxy decisions, workspace decision, allowed scope, and model target in receipts
* remain benchmark-ineligible when proxy support is used
* avoid backend-authored task files, deterministic scaffolds, and hidden content injection
* leave real app files untouched for disposable artifact prompts

Pure mode must:

* remain diagnostic
* allow model path choice
* not receive Product helper scaffolding
* not receive proxy-suggested exact Product targets
* be allowed to fail product usefulness without being treated as Product failure
* use separate benchmark eligibility fields and reasons
* preserve raw transcripts, parsed actions, and model-authored target proof

## Test Matrix

### 1. Original Messy Homepage Prompt

Prompt shape:

* A messy create prompt such as "init a repo and make homepage for agent lab expermients".

Expected Product behavior:

* Classifies as `disposable_single_file_artifact`.
* Uses `html_static_page` or equivalent HTML artifact class.
* Uses disposable workspace.
* Provides `.html` boundary or equivalent safe artifact boundary.
* Does not make homepage-specific hardcoding the product pattern.
* Requires the model to author the final path and full HTML content.

Expected Pure behavior if applicable:

* Uses empty exact target and empty allowed files.
* Allows model path choice.
* Benchmark eligibility depends on model-chosen useful HTML output and no Product help.

Expected files touched:

* Product: only model-authored disposable `.html` target.
* Pure: only model-chosen disposable target if the model produces one.

Expected blocked/clarification behavior if applicable:

* Blocks if the model chooses a disallowed extension, protected path, or path escape.

Receipt assertions:

* `route_type = product` for Product.
* `task_shape = disposable_single_file_artifact`.
* proxy artifact class is recorded.
* `model_authored_targets` contains the model target.
* benchmark eligibility is false for Product.

No-cheat assertions:

* No backend-created content.
* File bytes match model action content.
* Real app untouched.

Checks to run:

* Focused regression pytest.
* Receipt inspection for Product and Pure runs.
* `git diff --check`.

### 2. Non-Homepage HTML Artifact Prompt

Prompt shape:

* "make a small static html demo" or "create a simple landing page".

Expected Product behavior:

* Uses generic artifact resolver.
* Classifies as HTML static artifact without requiring homepage wording.
* Requires model-authored target and content.

Expected Pure behavior if applicable:

* Same diagnostic path-choice rules as Pure homepage.

Expected files touched:

* Only model-authored `.html` files in disposable workspace.

Expected blocked/clarification behavior if applicable:

* Blocks wrong extension or protected path.

Receipt assertions:

* Generic resolver source is visible.
* Artifact class and model target are separate.

No-cheat assertions:

* No injected file content.
* No backend-created file counts as model output.

Checks to run:

* Mocked Product run.
* Receipt/provenance assertion.

### 3. Markdown Artifact Prompt

Prompt shape:

* "make a markdown checklist for release verification".

Expected Product behavior:

* Classifies as `markdown_document`.
* Allows `.md` artifact boundary in disposable workspace.
* Requires model-authored `.md` target and content.

Expected Pure behavior if applicable:

* Model chooses path and content without Product artifact-class help.

Expected files touched:

* Only model-authored `.md` target.

Expected blocked/clarification behavior if applicable:

* Blocks `.env`, path escapes, or wrong protected targets.

Receipt assertions:

* Proxy artifact class is `markdown_document`.
* Model target is recorded separately.
* Content equality/hash proof is available.

No-cheat assertions:

* No backend content.
* No real app mutation.

Checks to run:

* Focused mocked regression and receipt inspection.

### 4. JSON/Config Artifact Prompt

Prompt shape:

* "create a json config example for local settings".

Expected Product behavior:

* Classifies as `json_example` or safe disposable config artifact.
* Allows `.json` in disposable workspace.
* Requires model-authored `.json` target and content.

Expected Pure behavior if applicable:

* Diagnostic path choice only.

Expected files touched:

* Only model-authored `.json` target when accepted.

Expected blocked/clarification behavior if applicable:

* Blocks `.env`, key, pem, cert, path escape, and wrong extension attempts.

Receipt assertions:

* Protected boundary decision is present.
* Artifact class and model target are distinct.

No-cheat assertions:

* No secret-shaped file writes.
* No backend-created output.

Checks to run:

* Mocked accepted JSON artifact case.
* Wrong-extension trap.
* Protected-path trap.

### 5. Explicit Docs/Config Edit With Target Path

Prompt shape:

* User supplies a clear repo-relative target such as `Target file: docs/foo.md`.

Expected Product behavior:

* Uses explicit target path.
* Sets exact allowed file to the user-supplied target.
* Provides context and action contract.
* Requires model-authored edit/write action.

Expected Pure behavior if applicable:

* Not the default route for daily Product use.

Expected files touched:

* Only the explicit target in preview/disposable policy allowed by the current runtime.

Expected blocked/clarification behavior if applicable:

* Blocks wrong-file action outside exact allowed scope.

Receipt assertions:

* `target_source = user_explicit`.
* Allowed scope source is explicit target.
* Model-authored action target equals the allowed file.

No-cheat assertions:

* Backend-authored content is rejected.
* Wrong-file attempts are blocked.

Checks to run:

* Existing TaskSpec and tool-action regression tests.

### 6. Vague Real-Repo Implementation That Should Clarify Or Block

Prompt shape:

* "make the app better somewhere" or broad real-repo implementation without a target.

Expected Product behavior:

* Does not infer broad real app mutation.
* Returns clarification-required or blocked state.
* Provides no write scope.

Expected Pure behavior if applicable:

* Not used as Product default.

Expected files touched:

* None.

Expected blocked/clarification behavior if applicable:

* Clarification required with no execution.

Receipt assertions:

* Clarification reason is recorded.
* Files touched is empty.

No-cheat assertions:

* No hidden backend fallback.
* No real app mutation.

Checks to run:

* TaskSpec intake clarification test.
* Prompt-packet block-before-coder test if included in focused suite.

### 7. Wrong Extension/File Trap

Prompt shape:

* JSON artifact prompt where model tries `config.txt`, or explicit docs target where model writes another file.

Expected Product behavior:

* Blocks outside artifact extension boundary or exact allowed file.

Expected Pure behavior if applicable:

* Pure may allow model path choice only inside disposable workspace, but protected/path escape still blocks.

Expected files touched:

* None for blocked traps.

Expected blocked/clarification behavior if applicable:

* `target_not_allowed` or equivalent executor/parser block.

Receipt assertions:

* Blocked result visible.
* Files touched empty.

No-cheat assertions:

* Wrong file is not created.
* No retry hides the authority failure.

Checks to run:

* Tool action executor wrong-file tests.
* Product wrong-extension mocked test.

### 8. Protected Path Trap

Prompt shape:

* Any model action or user target involving `.env`, `.env.local`, pem/key/cert, or path escape.

Expected Product behavior:

* Blocks before execution when possible.
* Blocks at parser/executor if model attempts protected target.

Expected Pure behavior if applicable:

* Same protected/path escape safety remains active.

Expected files touched:

* None.

Expected blocked/clarification behavior if applicable:

* `protected_path`, `path_escape`, or equivalent authority error.

Receipt assertions:

* Protected/path reason is recorded.
* No verification repair retry treats it as format repair.

No-cheat assertions:

* Protected file is not read or written.
* No hidden mutation.

Checks to run:

* Existing protected path intake, parser, executor, and loop tests.

### 9. Fake Apply Claim Trap

Prompt shape:

* Model returns prose like "I applied the change" without executable action.

Expected Product behavior:

* Does not count prose as execution.
* Requires parsed action and executor result.

Expected Pure behavior if applicable:

* Same parser/action requirement.

Expected files touched:

* None.

Expected blocked/clarification behavior if applicable:

* Honest failed-format, blocked, or safety failure classification depending on scorer.

Receipt assertions:

* Raw transcript preserved.
* Parsed actions empty or non-mutating.
* Files touched empty.

No-cheat assertions:

* Fake apply is not promoted to diff or success.

Checks to run:

* Existing fake apply safety scoring tests.

### 10. Pure Diagnostic Model Path-Selection Test

Prompt shape:

* Messy create prompt run explicitly in Pure mode.

Expected Product behavior:

* Not applicable as Product proof.

Expected Pure behavior if applicable:

* No Product helper scaffolding.
* Empty exact allowed files.
* Model may choose target path.
* Benchmark eligibility requires useful model-chosen artifact and no Product help.

Expected files touched:

* Model-chosen disposable path only.

Expected blocked/clarification behavior if applicable:

* Protected/path escape still blocks.

Receipt assertions:

* `route_type = pure_diagnostic`.
* `model_may_choose_paths = true`.
* No transparent default target.
* Benchmark eligibility and reason are recorded.

No-cheat assertions:

* No Product helper fields used in Pure.

Checks to run:

* Pure mocked regression test.

### 11. Receipt/Provenance Field Assertion

Prompt shape:

* Product accepted artifact and Product blocked trap.

Expected Product behavior:

* Receipts expose proxy/model separation.

Expected Pure behavior if applicable:

* Receipts expose diagnostic route and benchmark fields.

Expected files touched:

* Accepted case touches only model-authored disposable file.
* Blocked case touches none.

Expected blocked/clarification behavior if applicable:

* Blocked reason present.

Receipt assertions:

* Route type, task shape, workspace mode, proxy decisions, artifact class/extensions, model target, executor result, files touched, blocked/clarification reason, benchmark eligibility, and no-cheat flags are inspectable.

No-cheat assertions:

* Model-authored content equality/hash proof matches changed files.

Checks to run:

* Receipt sample inspection and focused pytest assertions.

### 12. Disposable Workspace No-Real-App-Mutation Assertion

Prompt shape:

* Product disposable artifact prompt with successful model action.

Expected Product behavior:

* Writes only in disposable workspace.

Expected Pure behavior if applicable:

* Same disposable workspace boundary.

Expected files touched:

* Disposable workspace files only.

Expected blocked/clarification behavior if applicable:

* Any `src/`, `app/`, `pages/`, `source_proxy/`, or `scripts/` mutation from a disposable prompt is a NO-GO.

Receipt assertions:

* `real_app_touched = false`.
* Files touched list has no real app paths.

No-cheat assertions:

* No backend fallback writes.
* No hidden mutation.

Checks to run:

* Mocked Product runtime and score assertions.
* `git status` before/after if an execution prompt later approves smoke runs.

## Receipt Assertions

Phase 2 execution should inspect these receipt fields or field classes:

* route type
* task shape
* workspace mode
* proxy decisions
* allowed/protected boundaries
* artifact class/extensions
* model-authored target path
* model-authored content equality/hash proof
* files touched
* executor result
* checks run
* blocked reason
* clarification reason
* benchmark eligibility
* Product helper/generic orchestration distinction
* backend-created content flag
* real app mutation flag

Expected concrete fields include:

* `route_type`
* `task_shape`
* `task_shape_source`
* `workspace_decision_source`
* `allowed_scope_source`
* `proxy_artifact_class_suggested`
* `proxy_exact_target_suggested`
* `model_authored_targets`
* `model_authored_content_hashes`
* `content_byte_match_by_target`
* `files_touched`
* `blocked_reasons`
* `clarification_or_block_reason`
* `benchmark_eligible`
* `benchmark_eligibility_reason`
* `product_helper_used`
* `proxy_orchestration_used`
* `backend_created_content`
* `real_app_touched`
* raw transcript, parse result, parsed actions, execution receipt, and skipped check arrays

## Evidence Files To Produce Later

Later execution prompts should produce:

* `docs/evidence/source-proxy-orchestrator-correction/phase-2-product-verification-summary.md`
* `docs/evidence/source-proxy-orchestrator-correction/phase-2-product-vs-pure-comparison.md`
* `docs/evidence/source-proxy-orchestrator-correction/phase-2-receipt-samples/`
* `docs/evidence/source-proxy-orchestrator-correction/phase-2-blocked-case-receipts/`
* `docs/evidence/source-proxy-orchestrator-correction/phase-2-no-cheat-assertion-summary.md`
* `docs/evidence/source-proxy-orchestrator-correction/phase-2-closeout.md`

Do not create those files in this task. This task creates only this Phase 2 plan.

## Required Local Verification Commands For Later Execution

Plan but do not run during future execution planning:

```bash
source .venv/bin/activate
python -m pytest source_proxy/tests/test_coding_regression_pack.py -k "task_spec_intake or tool_action or human_messy_homepage or messy_homepage or pure or artifact or protected or fake"
git diff --check
git status --branch --short --untracked-files=normal
```

Additional local mocked verification commands to consider in later execution, based on existing tests/scripts:

```bash
source .venv/bin/activate
python -m pytest source_proxy/tests/test_coding_regression_pack.py -k "human_messy_homepage or pure or artifact or protected or fake"
python -m pytest source_proxy/tests/test_coding_regression_pack.py -k "tool_action_executor or bounded_agent_loop or plan7"
python scripts/agent-trials/run-source-proxy-human-messy-homepage-smoke.py --help
```

The smoke script should only be run later if the approved prompt confirms a mocked/local mode that avoids provider/model calls.

## Provider/Model Call Gate

No provider/model calls are allowed until local/mocked Product verification is GO and Britton explicitly approves a live verification prompt.

Live verification must:

* use disposable workspaces only
* run a tiny prompt set first
* compare Product and Pure route receipts
* preserve raw transcripts
* preserve parsed actions
* preserve diff/check receipts
* avoid real app mutation
* stop on first provenance/no-cheat failure

Live verification must not:

* run benchmark prompts
* mutate real app files
* count backend-created files as model output
* hide provider/model failure as Product GO
* overwrite local mocked evidence
* continue after protected-path, wrong-file, backend-authorship, fake-apply, or receipt-provenance failure

## Phase 2 Execution Increments

### Increment 2.1: Local/Mocked Verification Run And Receipt Audit

Purpose:

* Re-run the focused local mocked regression slice on `source-server`.
* Audit representative Product, Pure, accepted, and blocked receipts.

Files likely touched:

* `docs/evidence/source-proxy-orchestrator-correction/phase-2-product-verification-summary.md`
* `docs/evidence/source-proxy-orchestrator-correction/phase-2-receipt-samples/`

Commands to run:

```bash
source .venv/bin/activate
python -m pytest source_proxy/tests/test_coding_regression_pack.py -k "task_spec_intake or tool_action or human_messy_homepage or messy_homepage or pure or artifact or protected or fake"
git diff --check
git status --branch --short --untracked-files=normal
```

Evidence to create:

* Test output summary.
* Python path used.
* Receipt field audit.

Allowed actions:

* Read files.
* Run local mocked tests.
* Create evidence docs.

Forbidden actions:

* Runtime changes.
* Test changes.
* Provider/model calls.
* Benchmark prompts.
* Real app mutation from trial prompts.

Stop condition:

* Stop if tests fail or receipts cannot prove proxy/model separation.

### Increment 2.2: Product/Pure Comparison Evidence

Purpose:

* Compare Product and Pure behavior for the original messy homepage prompt and at least one non-homepage artifact prompt using mocked/local fixtures.

Files likely touched:

* `docs/evidence/source-proxy-orchestrator-correction/phase-2-product-vs-pure-comparison.md`
* receipt samples directory

Commands to run:

* Focused local mocked tests for Product/Pure.
* No provider/model commands.

Evidence to create:

* Comparison table showing route type, task shape, allowed scope, model target, benchmark eligibility, files touched, and GO/NO-GO.

Allowed actions:

* Read receipts.
* Run mocked/local verification.
* Write docs evidence.

Forbidden actions:

* Treat Pure mode as Product default.
* Run live model calls.
* Run benchmark prompts.

Stop condition:

* Stop if Product/Pure distinction is ambiguous in receipts.

### Increment 2.3: No-Cheat And Protected-Path Verification

Purpose:

* Prove backend-authorship rejection, wrong-file blocking, protected-path blocking, fake-apply classification, and no real app mutation still hold.

Files likely touched:

* `docs/evidence/source-proxy-orchestrator-correction/phase-2-no-cheat-assertion-summary.md`
* blocked case receipts directory

Commands to run:

```bash
source .venv/bin/activate
python -m pytest source_proxy/tests/test_coding_regression_pack.py -k "protected or fake or wrong_file or backend_authored or tool_action"
git diff --check
```

Evidence to create:

* No-cheat assertion summary.
* Blocked-case receipt snippets.

Allowed actions:

* Run mocked/local tests.
* Write evidence docs.

Forbidden actions:

* Weakening anti-cheat.
* Fixing failures through runtime/test changes unless a later prompt explicitly authorizes repair.

Stop condition:

* Stop if backend-created content, wrong files, protected paths, fake apply, or hidden mutation can pass.

### Increment 2.4: Disposable Artifact Smoke Without Provider/Model Calls, If Script Supports Mocked Mode

Purpose:

* Confirm smoke tooling can produce disposable artifact evidence without provider/model calls.

Files likely touched:

* `docs/evidence/source-proxy-orchestrator-correction/phase-2-product-verification-summary.md`
* smoke receipt samples only if mocked mode is confirmed

Commands to run:

```bash
source .venv/bin/activate
python scripts/agent-trials/run-source-proxy-human-messy-homepage-smoke.py --help
```

Only run a smoke command if the script exposes a mocked/local mode in help or docs.

Evidence to create:

* Smoke capability note.
* Mocked smoke output if approved and supported.

Allowed actions:

* Inspect script help.
* Run mocked/local smoke only if explicitly safe.

Forbidden actions:

* Provider/model calls.
* Live smoke against a model.
* Real app mutation.

Stop condition:

* Stop if mocked mode is unavailable or unclear.

### Increment 2.5: Live Provider/Model Verification Approval Packet Only

Purpose:

* Prepare a later approval packet for live verification without running it.

Files likely touched:

* `docs/evidence/source-proxy-orchestrator-correction/phase-2-live-verification-approval-packet.md`

Commands to run:

* None required beyond status/diff checks.

Evidence to create:

* Tiny prompt set.
* Disposable workspace paths.
* Stop conditions.
* Raw transcript and receipt preservation plan.

Allowed actions:

* Write approval packet.

Forbidden actions:

* Provider/model calls.
* Benchmark prompts.
* Runtime changes.

Stop condition:

* Stop if local/mocked verification is not GO.

### Increment 2.6: Phase 2 Closeout

Purpose:

* Close Phase 2 verification with exact evidence, checks, blockers, and GO/NO-GO.

Files likely touched:

* `docs/evidence/source-proxy-orchestrator-correction/phase-2-closeout.md`

Commands to run:

```bash
source .venv/bin/activate
python -m pytest source_proxy/tests/test_coding_regression_pack.py -k "task_spec_intake or tool_action or human_messy_homepage or messy_homepage or pure or artifact or protected or fake"
git diff --check
git status --branch --short --untracked-files=normal
```

Evidence to create:

* Final closeout.
* Files changed.
* Commands run.
* Exact outputs.
* Blockers.
* GO/NO-GO.
* Next title only.

Allowed actions:

* Run approved verification.
* Write closeout docs.

Forbidden actions:

* Starting Phase 3.
* Provider/model calls unless explicitly approved in a separate prompt.
* Benchmark prompts.
* Git mutation beyond normal file writes.

Stop condition:

* Stop if verification evidence is incomplete or contradictory.

## Stop Conditions

Stop and report NO-GO if the plan would:

* treat Pure mode as product default
* make homepage-specific behavior the product pattern
* remove model-authored path/content/action requirements
* weaken anti-cheat/provenance
* allow backend-created files as model output
* run provider/model calls
* run live benchmark prompts
* mutate real app files
* require runtime/test changes during this docs-only task

## Manual Verification Block

Commands run at the end of this docs-only planning task:

```bash
source .venv/bin/activate
python -m pytest source_proxy/tests/test_coding_regression_pack.py -k "task_spec_intake or tool_action or human_messy_homepage or messy_homepage or pure or artifact or protected or fake"
git diff --check
git status --branch --short --untracked-files=normal
```

Expected result:

* The focused pytest command runs under `/home/source/SpiritOS/.venv/bin/python`.
* Focused pytest passes.
* `git diff --check` exits 0.
* `git status --branch --short --untracked-files=normal` shows this plan doc plus existing Phase 1 dirty/untracked files.

## Current Decision

GO for Phase 2 execution planning review.

NO-GO for executing Phase 2 verification, provider/model calls, benchmark prompts, runtime changes, test changes, or real app mutation until Britton approves a separate execution prompt.

## Next Title Only

Source Proxy Orchestrator Correction Phase 2 Local Mocked Verification Approval
