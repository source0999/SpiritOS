# Source Proxy Orchestrator Correction Phase 1 Product Orchestration Plan

## Status

* Phase 1 planning only
* no runtime changes authorized by this document
* no tests changed by this document
* no provider/model calls authorized
* no benchmark execution authorized
* implementation requires Britton's later explicit approval

## Phase 1 Goal

Phase 1 should design the smallest safe implementation path for moving Product mode from a homepage-specific bridge to a generic Source Proxy product orchestration route.

The goal is not to prove raw Qwen can infer every task shape, workspace rule, path boundary, and output contract from a messy prompt with minimal support. The goal is to restore Source Proxy as the product orchestrator: it should classify intent and scope, choose safe workspace mode, assemble context, expose a generic action contract, set allowed/protected boundaries, validate model-authored actions, and produce honest receipts.

The model still authors the concrete changes. That means final target paths, file contents, file edits, and explicit tool actions must come from model output before runtime execution. Product orchestration is allowed to provide transparent structure and constraints; it is not allowed to create task files or pretend proxy-authored content is model output.

## Product vs Diagnostic Boundary

Product mode:

* Source Proxy orchestration for daily messy prompts.
* Intended for user-facing usefulness.
* May classify task shape, decide safe workspace mode, provide context, expose allowed/protected boundaries, and guide the model with a generic action contract.
* Must require model-authored target path, content, and action before execution.
* Must not be graded as benchmark-pure when the proxy provides scope help.

Pure mode:

* Diagnostic benchmark lane.
* Intentionally removes product support such as proxy-selected target files and helper scope.
* Tests whether the selected model can choose safe relative paths and author content with minimal orchestration.
* Must remain available for benchmark and regression truth.
* Must not become the default daily route.

Receipts should make the selected route type obvious. A future receipt should include route type, benchmark eligibility, whether the proxy supplied task-shape help, whether the proxy supplied allowed/protected boundaries, whether any exact target was proxy-suggested, and which target/content came from the model.

## Non-Cheating Architecture

Proxy decides task shape, safety, context, workspace, and allowed scope.
Model authors concrete changes.
Runtime executes only validated model-authored actions.
Receipt separates proxy decisions from model-authored content.

Target flow:

User prompt
-> TaskSpec intake
-> generic intent and scope classification
-> product route decision
-> context packet and action contract
-> selected model call
-> model-authored actions or path-bound content blocks
-> parser and validator
-> disposable workspace or bounded repo executor
-> checks
-> receipt with proxy/model separation

The proxy may say "this looks like a disposable single-file HTML artifact" or "this is an explicit docs edit against `docs/foo.md`" or "this real-repo implementation is too vague and needs clarification." The proxy may not silently write the file, inject the file contents, or transform vague freeform prose into a working file without model-authored path/content/action.

## Proposed Generic Resolver

The generic resolver should classify task shapes without hardcoding homepage as the only useful artifact type.

### Disposable Single-File Artifact

When it applies:

* The user asks to create a small standalone artifact.
* The prompt does not require mutation of the real app.
* The artifact can be represented as one file such as HTML, Markdown, JSON, TXT, CSS, JS demo, or another safe static file type.

What the proxy may decide:

* `task_shape = disposable_single_file_artifact`
* `workspace_mode = disposable_workspace`
* safe artifact class, such as `html_static_page`, `markdown_document`, `json_example`, or `text_artifact`
* allowed extension set or file class
* file count limit of 1 unless the model asks through an explicit multi-file action and the task shape permits it
* protected/forbidden path boundaries

What the model must author:

* final relative target path
* full file content
* explicit `WriteFile` action or accepted path-bound content block

Execution mode allowed:

* disposable workspace execution only
* no real app mutation
* no network by default
* checks only when policy allows

Receipt fields should show:

* route type: product
* task shape
* proxy artifact class
* allowed extension or class boundary
* model-authored target path
* model-authored content hash or byte equality proof
* files touched
* benchmark eligibility: false when proxy supplied product help

### Disposable Small File Bundle

When it applies:

* The user asks for a tiny static project, demo, or artifact bundle.
* The task is disposable and does not imply editing the real app.
* Multiple files are natural, such as `index.html` plus `styles.css`, a Markdown checklist plus JSON example, or a static demo bundle.

What the proxy may decide:

* `task_shape = disposable_small_file_bundle`
* disposable workspace mode
* max file count
* allowed artifact classes or extension set
* forbidden/protected boundaries
* optional transparent generic default directory such as `artifact/` if needed

What the model must author:

* each final relative target path
* full content for every file
* explicit actions or path-bound blocks for every file

Execution mode allowed:

* disposable workspace execution
* bounded file count
* no real app mutation

Receipt fields should show:

* proxy task shape and file count limit
* model-authored target paths
* byte equality proof for each changed file
* files touched
* blocked reasons if any file exceeds scope

### Docs/Config Edit With Explicit Path

When it applies:

* The user provides a clear repo-relative path.
* The requested file is docs/config-like and not protected.
* The request is bounded enough for preview or disposable execution policy.

What the proxy may decide:

* `task_shape = explicit_docs_or_config_edit`
* target path from user prompt
* allowed file equals the explicit target
* protected path and path escape validation
* workspace mode based on existing policy

What the model must author:

* explicit edit action against the target
* replacement content or path-bound edit
* reason for the action

Execution mode allowed:

* bounded repo preview or approved disposable copy path, depending on current runtime authority
* no safe apply unless a later approval grants it

Receipt fields should show:

* user-supplied target path
* proxy allowed boundary
* model-authored edit
* check result or skipped-check reason

### Bounded Existing-Repo Edit With Clear Target

When it applies:

* The user gives a clear existing file or route/component target.
* The requested change is bounded.
* The target is not protected and does not escape the workspace.

What the proxy may decide:

* `task_shape = bounded_existing_repo_edit`
* target path and allowed files based on explicit user target or safe resolver result
* real repo preview or disposable copy mode according to current authority
* context packet from the target file and repo map

What the model must author:

* explicit edit action
* content/edit fragments
* no broad file changes beyond allowed scope

Execution mode allowed:

* bounded preview or disposable workspace, not real app apply unless separately approved

Receipt fields should show:

* target source, such as `user_explicit` or `safe_resolver`
* allowed files
* protected path check
* model-authored action
* diff and checks

### Clarification-Required Real-Repo Implementation

When it applies:

* The prompt asks for real app implementation but lacks a clear target.
* The task could touch many files or product areas.
* The proxy cannot safely infer scope.

What the proxy may decide:

* `task_shape = clarification_required_real_repo_implementation`
* `workspace_mode = none`
* no write scope
* clarification prompt

What the model must author:

* no file action should be executed before clarification
* optional `AskClarification` or final explanation only

Execution mode allowed:

* no write execution

Receipt fields should show:

* clarification required
* no files touched
* blocked reason or clarification question

### Blocked/Protected-Path Request

When it applies:

* The target is secret-shaped, protected, outside workspace, forbidden, or otherwise unsafe.

What the proxy may decide:

* `task_shape = blocked_protected_or_unsafe_path`
* `workspace_mode = none`
* no allowed write scope
* explicit protected/path-escape reason

What the model must author:

* no executable write action
* optional safe explanation or clarification

Execution mode allowed:

* none

Receipt fields should show:

* protected path or path escape reason
* no files touched
* benchmark eligibility false

## Artifact/Create Intent Rules

Product mode should detect disposable artifact/create prompts generically. Examples:

* "create a homepage"
* "make a simple landing page"
* "create a small html demo"
* "make a markdown checklist"
* "make a json config example"
* "build a tiny static page"

Desired behavior:

* If the user clearly asks for a disposable artifact, proxy may choose disposable workspace mode.
* If the artifact type implies safe file patterns, proxy may provide allowed artifact classes or file extension patterns.
* The proxy should avoid silently preselecting an exact file unless the user gave one or the task shape has a transparent generic default that is recorded.
* The model must author the final path and content.
* Product receipts must distinguish proxy-suggested artifact class from model-authored target path.
* Homepage should become one example of generic artifact/create intent, not a special product architecture.

Artifact class examples:

* `html_static_page`: allowed extensions `.html`, `.css`, `.js` when bundle mode is allowed; single-file mode should prefer `.html`.
* `markdown_document`: allowed extension `.md`.
* `json_example`: allowed extension `.json`; validation should reject protected filenames and path escapes.
* `text_artifact`: allowed extensions `.txt` or `.md`, depending on prompt.
* `static_demo_bundle`: allowed extensions `.html`, `.css`, `.js`, `.json`, `.md` with a small file count cap.

Exact file defaults should be transparent and limited. For example, a single-file HTML artifact may allow a recorded generic default suggestion of `index.html`, but the receipt must mark it as proxy-suggested and not benchmark-pure. The preferred product direction is to let the model author the final target path inside the permitted artifact class.

## TaskSpec Intake Changes To Plan

Smallest safe planned changes in `source_proxy/decision/task_spec_intake.py`:

* Generalize `_is_messy_homepage_disposable_prompt` into a resolver for disposable artifact/create intent.
* Replace a homepage-only branch with a task-shape classifier that can return artifact class, workspace mode, allowed extension/class boundary, max file count, and clarification state.
* Keep explicit bounded proposal handling ahead of generic inference.
* Keep protected path and path escape checks ahead of any artifact/create inference.
* Keep existing explicit-target behavior for docs/config and existing-repo edits.
* Avoid making `index.html` and `styles.css` the default product pattern.
* Carry task shape, workspace mode, allowed/protected boundaries, artifact class, and source of target decision in TaskSpec.
* Preserve Pure mode behavior: empty target, empty allowed files, `model_may_choose_paths=True`, and benchmark eligibility checks.
* Reframe fields so legitimate proxy orchestration is not labeled as cheating by default.

Field naming/reframing to plan:

* Replace or supplement `product_helper_used` with `proxy_orchestration_used`.
* Split homepage-specific preselection into `proxy_exact_target_suggested` and `proxy_artifact_class_suggested`.
* Keep `system_preselected_target` for benchmark truth.
* Add `target_source` values such as `user_explicit`, `model_authored`, `proxy_generic_default`, and `legacy_homepage_helper`.
* Add `task_shape_source` values such as `generic_artifact_resolver`, `explicit_task_spec`, `protected_path_gate`, and `pure_diagnostic`.

## Prompt Packet and Model Contract Changes To Plan

The Source Proxy packet should tell the model:

* inferred task shape
* workspace mode
* allowed/protected boundaries
* file count limits
* allowed artifact class or extensions
* action contract
* requirement to author explicit path/content/action
* clarification/blocking expectations

The packet should not inject file contents.

The packet should not pretend proxy-authored paths/content are model-authored.

The packet may provide transparent guidance and constraints.

Planned packet shape:

* `route_type`: `product` or `pure_diagnostic`
* `task_shape`
* `workspace_mode`
* `artifact_class`
* `allowed_extensions` or `allowed_file_patterns`
* `max_file_count`
* `protected_paths`
* `forbidden_files`
* `model_requirements`: explicit path, full content, supported action JSON or path-bound block
* `clarification_policy`: ask when target is unsafe, broad, or real-repo ambiguous
* `benchmark_eligible`: false for Product when proxy help is provided

The model contract should remain generic: `WriteFile`, `EditFile`, `MultiEdit`, `ReadFile`, `ListFiles`, `SearchRepo`, `RunCheck`, `AskClarification`, and `ReturnFinal` as already defined by the tool action contract. Product prompts should show schema expectations, not task-specific answer content.

## Receipt and Provenance Changes To Plan

Receipt fields should clearly separate:

* route type: product vs pure diagnostic
* proxy task shape decision
* proxy workspace decision
* proxy allowed/protected boundary decision
* proxy suggested artifact class
* model-authored target path
* model-authored content hash or byte equality proof
* executor result
* checks run
* files touched
* blocked/clarification reasons
* benchmark eligibility

Preserve existing anti-cheat fields:

* backend-created content detection
* fallback used
* deterministic scaffold used
* dummy fixture used
* real app touched
* file equals model action content
* product/helper or proxy-orchestration trace
* transparent default target trace
* system-preselected target trace
* model chose target trace

Planned new or reframed receipt fields:

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
* `benchmark_eligibility_reason`
* `clarification_or_block_reason`

The receipt should be honest even when the product route succeeds. Product GO should mean useful product behavior with no-cheat proof. Benchmark GO should require Pure diagnostic criteria.

## Homepage Bridge Reduction Plan

Options evaluated:

1. Keep as legacy regression only.
2. Convert into a generic artifact/create resolver case.
3. Park behind a diagnostic/compatibility flag.
4. Remove only after generic resolver proves equivalent Product behavior.

Safest recommended option:

Convert the homepage bridge into a generic artifact/create resolver case, keep the current homepage smoke as a legacy regression during the transition, and remove or park the hardcoded bridge only after generic resolver Product behavior proves equivalent.

Why:

* The homepage bridge fixed a real runtime gap and should not be deleted blindly.
* Pure mode depends on preserving the diagnostic contrast.
* Product mode needs a generic path that handles homepage as one artifact class, not as the architecture.
* Keeping the legacy regression temporarily prevents losing the original human messy prompt proof.
* Parking/removal should happen only after the generic resolver proves the same Product outcome without backend-authored content or hidden scaffolding.

Do not delete anything in this task.

## Test Plan For Later Implementation

Do not edit tests in this planning task.

### Original Messy Homepage Prompt

Expected Product behavior:

* Classifies as disposable artifact/create, likely `html_static_page`.
* Uses disposable workspace.
* Provides artifact class and safe boundaries.
* Model authors path/content/action.
* Produces openable HTML if model output is good.

Expected Pure behavior:

* Keeps empty target/allowed behavior.
* Model must choose path and content.
* Benchmark eligibility only if model-chosen path/content produce a valid openable artifact.

No-cheat assertions:

* No backend-created content.
* File bytes equal model action content.
* Real app untouched.

Receipt assertions:

* Product route says benchmark-ineligible because proxy help was used.
* Pure route shows no product help.
* Model-authored target path is explicit.

### Non-Homepage Disposable Artifact Prompt

Expected Product behavior:

* Classifies as disposable single-file artifact or bundle.
* Does not require homepage words.
* Model authors target/content.

Expected Pure behavior:

* May be evaluated only as diagnostic if requested.
* Model carries path and content without product support.

No-cheat assertions:

* No exact file content injected by proxy.
* No backend-authored file.

Receipt assertions:

* Artifact class and model-authored target are separate.

### Markdown Artifact Prompt

Expected Product behavior:

* Classifies as `markdown_document`.
* Allows `.md` artifact class in disposable workspace.
* Model authors a `.md` path and content.

No-cheat assertions:

* Reject protected or escaped paths.
* Reject free-floating content without path/action if parser cannot bind it.

Receipt assertions:

* `proxy_artifact_class_suggested = markdown_document`.
* `model_authored_targets` contains the model path.

### JSON/Config Artifact Prompt

Expected Product behavior:

* Classifies as `json_example` or config artifact if disposable.
* Allows `.json` in disposable workspace.
* Model authors valid target/content.

No-cheat assertions:

* `.env`, key, pem, cert, and path escape requests remain blocked.

Receipt assertions:

* Protected boundary decision recorded.
* Model-authored content hash or byte match recorded.

### Docs/Config Edit With Explicit Path

Expected Product behavior:

* Uses explicit path.
* Sets allowed files to that path.
* Provides context and action contract.

Expected Pure behavior:

* Not the default route.

No-cheat assertions:

* Wrong-file model action is blocked.
* Backend-authored content is rejected.

Receipt assertions:

* `target_source = user_explicit`.
* Files touched match allowed path.

### Vague Real-Repo Implementation That Should Clarify Or Block

Expected Product behavior:

* Does not infer broad real app mutation.
* Returns clarification-required or blocked state.

No-cheat assertions:

* No files touched.
* No trial mutation.

Receipt assertions:

* Clarification prompt or blocked reason recorded.

### Wrong-File Trap

Expected Product behavior:

* Blocks model action outside allowed scope.

No-cheat assertions:

* `target_not_allowed` visible.
* No files touched outside scope.

Receipt assertions:

* Execution result blocked.
* Files touched empty or limited to safe scope.

### Protected Path Trap

Expected Product behavior:

* Blocks before model execution when possible.
* Blocks at executor if a model action attempts a protected target.

No-cheat assertions:

* Protected file is not read or written.
* Authority/protected failure is not retried as repair.

Receipt assertions:

* `protected_path` or `path_escape` recorded.

### Fake Apply Claim Trap

Expected Product behavior:

* Does not treat model prose claiming "applied" as execution.
* Requires real parsed action and executor result.

No-cheat assertions:

* No files touched from prose alone.
* Fake apply claim is classified honestly.

Receipt assertions:

* Raw transcript preserved.
* Parsed actions and files touched show truth.

### Pure Diagnostic Path-Selection Test

Expected Product behavior:

* Not applicable as Product benchmark proof.

Expected Pure behavior:

* No proxy target or allowed-file helper.
* Model chooses target.
* Benchmark eligibility requires successful useful artifact and no helper fields.

No-cheat assertions:

* `product_helper_used` or successor field false.
* `system_preselected_target` false.

Receipt assertions:

* `route_type = pure_diagnostic`.
* `benchmark_eligible` and reason recorded.

## Minimal Implementation Increments

### Increment 1.1: Route Boundary And Naming Cleanup Plan

Purpose:

* Define Product vs Pure route names and receipt fields before behavior changes.

Files likely touched:

* `source_proxy/decision/human_messy_homepage.py`
* `source_proxy/decision/task_spec_intake.py`
* `source_proxy/tests/test_coding_regression_pack.py`
* future evidence docs under `docs/evidence/source-proxy-orchestrator-correction/`

Allowed changes:

* Add route type constants or fields.
* Reframe helper/proxy field names while preserving old fields during transition.
* Update receipts to expose route type and benchmark eligibility reason.

Forbidden changes:

* Removing Pure mode.
* Weakening anti-cheat fields.
* Runtime behavior changes beyond explicit naming/receipt scope.

Tests/checks to run:

* Focused Product/Pure receipt tests.
* `git diff --check`.

Evidence to write:

* Increment evidence showing route fields and no behavior expansion.

Stop condition:

* Stop if naming cleanup weakens benchmark truth or hides product helper use.

### Increment 1.2: Generic Artifact/Create Resolver Implementation Plan

Purpose:

* Replace homepage-only create detection with a generic disposable artifact/create resolver.

Files likely touched:

* `source_proxy/decision/task_spec_intake.py`
* possible new helper under `source_proxy/decision/`
* `source_proxy/tests/test_coding_regression_pack.py`

Allowed changes:

* Add task shape classification.
* Add artifact class and allowed extension/class boundary.
* Preserve explicit target and protected-path precedence.

Forbidden changes:

* Backend-created file content.
* Exact benchmark-answer scaffolds.
* Real app mutation from disposable prompts.

Tests/checks to run:

* Homepage, landing page, HTML demo, Markdown checklist, JSON example, vague real-repo prompt, protected path.
* `git diff --check`.

Evidence to write:

* Resolver inventory and focused test output.

Stop condition:

* Stop if generic resolver preselects exact files broadly or lets protected paths pass.

### Increment 1.3: Product Prompt Packet/Action Contract Update Plan

Purpose:

* Update Product packets so the model receives task shape, artifact class, boundaries, and action contract without task-specific answer injection.

Files likely touched:

* `source_proxy/decision/human_messy_homepage.py`
* eventual general product route packet builder if present or added by approved implementation
* tests

Allowed changes:

* Add task shape, artifact class, allowed extensions, file count, protected/forbidden boundaries, and model requirements.
* Remove hardcoded homepage-only prompt wording from the generic Product path.

Forbidden changes:

* Injecting file contents.
* Pretending proxy-suggested exact paths are model-authored.
* Hiding allowed/protected constraints.

Tests/checks to run:

* Packet snapshot tests.
* Parser/action contract tests.
* Product homepage and non-homepage artifact tests.

Evidence to write:

* Packet examples with no content injection.

Stop condition:

* Stop if prompt packet tells the model exactly what content to write or hides model-authorship requirements.

### Increment 1.4: Receipt/Provenance Field Update Plan

Purpose:

* Make proxy/model separation first-class in receipts.

Files likely touched:

* `source_proxy/decision/tool_action_loop.py`
* `source_proxy/decision/human_messy_homepage.py`
* `source_proxy/decision/tool_action_safety.py`
* tests

Allowed changes:

* Add route type, task shape, proxy decision fields, model-authored target fields, content hash/byte match fields, and benchmark eligibility reason.
* Preserve existing anti-cheat fields.

Forbidden changes:

* Removing raw transcripts.
* Removing parsed actions.
* Collapsing proxy decisions into model-authored output.

Tests/checks to run:

* Receipt snapshot/focused tests.
* Fake apply claim trap.
* Backend-authorship rejection.

Evidence to write:

* Receipt field matrix.

Stop condition:

* Stop if receipts cannot distinguish proxy-suggested artifact class from model target.

### Increment 1.5: Homepage Bridge Reduction Or Conversion Plan

Purpose:

* Convert homepage bridge into a generic artifact/create resolver case while preserving legacy regression evidence.

Files likely touched:

* `source_proxy/decision/task_spec_intake.py`
* `source_proxy/decision/human_messy_homepage.py`
* `scripts/agent-trials/run-source-proxy-human-messy-homepage-smoke.py`
* tests

Allowed changes:

* Route homepage prompts through generic artifact resolver.
* Keep legacy smoke names temporarily.
* Make `--serve` latest handling mode-aware if implementation approval includes evidence plumbing.

Forbidden changes:

* Deleting homepage proof before generic equivalence exists.
* Making homepage helper the generic product pattern.
* Running live model/provider prompts unless separately approved.

Tests/checks to run:

* Mocked model Product/Pure tests.
* Homepage prompt regression.
* Non-homepage artifact regression.

Evidence to write:

* Before/after Product route comparison without provider/model calls unless approved.

Stop condition:

* Stop if homepage behavior only works through hardcoded `index.html` scaffolding.

### Increment 1.6: Product/Pure Test Update Plan

Purpose:

* Add tests that prove Product orchestration and Pure diagnostics are distinct.

Files likely touched:

* `source_proxy/tests/test_coding_regression_pack.py`
* possible fixtures under existing test fixture paths

Allowed changes:

* Add mocked tests for generic artifact prompts.
* Add receipt assertions.
* Add trap assertions for wrong-file/protected/fake apply.

Forbidden changes:

* Weakening existing safety tests.
* Removing Pure diagnostic test.
* Marking no-diff or no-action output as PASS.

Tests/checks to run:

* Focused pytest for TaskSpec, tool action, Product/Pure, and safety traps.
* `git diff --check`.

Evidence to write:

* Focused test result summary.

Stop condition:

* Stop if tests reward hidden scaffolding or backend-created output.

### Increment 1.7: Verification And Closeout Plan

Purpose:

* Verify the implementation with docs evidence and explicit GO/NO-GO.

Files likely touched:

* `docs/evidence/source-proxy-orchestrator-correction/phase-1-implementation-closeout.md`
* generated evidence only if approved

Allowed changes:

* Record evidence from approved tests/checks.
* Record remaining blockers.

Forbidden changes:

* Provider/model calls or benchmark prompts unless separately approved.
* Commit/stage/push/branch/worktree mutation.

Tests/checks to run:

* Focused pytest.
* `git diff --check`.
* `git status --branch --short --untracked-files=normal`.

Evidence to write:

* Closeout with files changed, tests run, artifacts, blockers, GO/NO-GO, next title.

Stop condition:

* Stop if implementation cannot prove model-authored content and proxy/model separation.

## Explicit Implementation Approval Gate

This Phase 1 plan does not approve implementation.

Implementation starts only after Britton approves a separate implementation prompt.

That later prompt must name the authorized implementation scope, allowed files, tests/checks, evidence output, and stop boundary. Until then, runtime code, tests, provider/model calls, benchmark prompts, and real app mutation remain NO-GO.

## Stop Conditions

Stop and report NO-GO if the plan would:

* remove Pure mode instead of keeping it diagnostic
* weaken anti-cheat/provenance
* allow backend-created files to count as model output
* make homepage-specific helpers the product pattern
* remove model-authored path/content/action requirements
* run provider/model calls
* run benchmarks
* mutate real app files
* require runtime changes during this docs-only task

## Manual Verification Block

Commands run for this docs-only plan:

```powershell
Get-Content -LiteralPath 'C:\Users\smith\.codex\attachments\779b52ee-73e5-414c-acba-b810dce3bad1\pasted-text.txt'
git status --branch --short --untracked-files=normal
Get-Content -LiteralPath 'docs\evidence\source-proxy-orchestrator-correction\refined-plan.md'
Get-Content -LiteralPath 'docs\evidence\source-proxy-orchestrator-correction\phase-0-audit.md'
rg -n "allow_messy_homepage_helper|_is_messy_homepage_disposable_prompt|transparent_default_target|DEFAULT_ALLOWED_FILES|model_may_choose_paths|pure_mode|benchmark_eligible|product_helper_used|system_preselected_target|latest-.*run|LATEST_PATH|_read_latest|latest-run" source_proxy scripts docs\evidence\source-proxy-tool-action-runtime-v1\human-messy-homepage-debug -g "*.py" -g "*.md" -g "*.json" -g "*.txt"
rg -n "backend_authorship_rejected|free_floating_code_no_path_action|target_not_allowed|path_escape|protected_path|model_may_choose_paths|RunCheck|raw_model_transcripts|parsed_actions|diagnostics_packet|files_touched" source_proxy\decision source_proxy\tests\test_coding_regression_pack.py
git diff --check
git status --branch --short --untracked-files=normal
```

Expected output:

* The refined plan and Phase 0 audit are readable.
* The targeted greps show Product/Pure boundary fields, homepage-specific helper logic, Pure diagnostic fields, no-cheat parser/executor protections, receipt fields, and protected path checks.
* `git diff --check` passes with no whitespace errors. Existing LF-to-CRLF warnings may print for already-dirty files.
* `git status --branch --short --untracked-files=normal` shows this new docs plan plus previously dirty/untracked Source Proxy files.

## Deliverables

1. `docs/evidence/source-proxy-orchestrator-correction/phase-1-product-orchestration-plan.md`
2. no runtime code changes
3. no test changes

## Current Decision

GO for implementation planning review.

NO-GO for implementation until Britton approves a separate implementation prompt.

## Next Implementation Prompt Title Only

Source Proxy Orchestrator Correction Phase 1 Implementation Approval
