# Source Proxy Orchestrator Correction Refined Plan

## Status

* docs-only plan
* no runtime changes authorized by this document
* no revert authorized by this document
* Phase 0 audit only is approved to start after Britton reviews this plan
* implementation requires later explicit approval

## Problem Statement

The recent "Pure mode" push improved benchmark honesty on paper by proving whether the local model can choose its own target path without product helper scaffolding. That diagnostic is useful, but it risks shifting too much intent understanding, scope selection, safe workspace selection, and path responsibility onto Qwen or another local model. Source Proxy is not supposed to be a thin raw-prompt relay. It is the product system under test.

The homepage repair also fixed a real runtime gap: a messy create prompt was previously advisory-only because no explicit target path reached the tool-action runtime. The fix proved that a disposable workspace can execute only model-authored content and avoid real app mutation. However, the current homepage-specific bridge may be too narrow if it becomes the general product pattern. The correction should restore Source Proxy as the orchestrator while preserving the no-cheat boundary that the model must author concrete paths, content, and actions before runtime execution.

## What Must Be Preserved

* generic model action contract
* model-authored paths/content/actions
* disposable workspace execution
* safety boundaries
* protected path validation
* provenance and receipts
* anti-cheat fields
* clear separation of proxy decisions vs model-authored output
* Mac/subagent advisory-only boundary
* benchmark pause/return gate discipline

## What Must Change

* Pure mode should be benchmark/diagnostic, not the default product behavior.
* Product route should use Source Proxy orchestration.
* TaskSpec intake should support generic artifact/create intent better.
* Homepage-specific special casing should be audited and reduced or generalized.
* Proxy should provide intent/scoping help without writing task content for the model.
* Product tests should ask whether the proxy system produces useful results on messy input, not whether Qwen succeeds with no help.

## Non-Cheating Target Architecture

Proxy decides task shape, safety, context, workspace, and allowed scope.
Model authors concrete changes.
Runtime executes only validated model-authored actions.
Receipt separates proxy decisions from model-authored content.

Target flow:

User prompt
-> TaskSpec intake
-> intent and scope classification
-> context packet and generic action contract
-> selected model call
-> model-authored actions or path-bound content blocks
-> parser and validator
-> disposable workspace executor
-> checks
-> receipt with proxy/model separation

The proxy may classify a prompt as likely disposable artifact creation, choose disposable workspace mode, expose a generic action contract, set allowed/protected boundaries, and provide relevant context. The proxy must not silently create the requested file, inject file contents, or convert vague freeform prose into working files without an explicit model-authored path/content/action. Receipts must show which decisions came from Source Proxy and which concrete changes came from model output.

## Phase 0: Audit Only

Purpose:
Map exactly what changed and decide what should be reverted, reduced, renamed, or generalized.

Allowed:

* read files
* grep files
* inspect diffs if available
* create Phase 0 audit doc
* update this refined plan only if the audit finds missing constraints

Forbidden:

* runtime code changes
* deleting Pure mode
* deleting provenance
* deleting anti-cheat fields
* changing tests
* rerunning live model/provider prompts
* creating new homepage helper logic
* real app mutation
* git mutation beyond normal file writes for docs

Audit questions:

1. What code/docs/tests were added specifically for Pure mode or model autonomy?
2. What code/docs/tests were added specifically for Product mode?
3. Where does homepage detection currently preselect or constrain files?
4. Which pieces are product-useful and should stay?
5. Which pieces are benchmark-only and should move behind diagnostic mode?
6. Which pieces are too homepage-specific and should be generalized?
7. Which pieces accidentally force the model to carry high-level intent/path responsibility?
8. Which current tests protect no-cheat behavior and must not be weakened?
9. Which tests incorrectly reward product usability through narrow prompt-specific scaffolding?
10. What is the smallest safe Phase 1 change set?

Phase 0 deliverable:
`docs/evidence/source-proxy-orchestrator-correction/phase-0-audit.md`

The audit doc must include:

* files inspected
* findings
* Product vs Pure mode inventory
* homepage-specific logic inventory
* proxy-orchestration gaps
* no-cheat protections to preserve
* proposed minimal reverts/reductions
* proposed generic replacement direction
* explicit GO/NO-GO for Phase 1
* next plan title only

## Phase 1: Restore Product Orchestration

Do not implement Phase 1 yet. Plan only.

Expected direction:

* keep Pure mode as diagnostic/benchmark mode
* make Product mode the default for daily messy prompts
* create or improve a generic artifact/create intent resolver
* avoid hardcoding homepage file names as the general pattern
* allow proxy to propose task shape and safe scope
* require model-authored path/content/action before execution
* keep receipts showing which decisions came from proxy and which came from model

Phase 1 must avoid collapsing the system into task-specific helpers. The expected product path is a generic orchestration improvement: classify disposable artifact/create intent, decide safe workspace mode, assemble context and constraints, then require the selected model to author the actual file path and content or an explicit action accepted by the action contract. If a prompt is too vague for safe product execution, the route should block or ask for clarification honestly.

## Phase 2: Tests

Do not implement Phase 2 yet. Plan only.

Test categories:

* original messy homepage prompt
* non-homepage disposable artifact prompt
* docs/config edit with explicit path
* vague real-repo implementation prompt requiring clarification
* wrong-file trap
* protected path trap
* fake apply claim trap

Success criteria:

* useful product behavior on messy input
* no backend-authored task files pretending to be model output
* no real app mutation from disposable prompt
* no hidden helper scaffolding
* clear receipt separation
* Pure mode remains available only as diagnostic benchmark behavior

The tests should preserve the distinction between product usefulness and benchmark autonomy. Product tests may expect Source Proxy to provide task shape, scope, context, and safe workspace boundaries. Diagnostic benchmark tests may intentionally remove those supports, but they must not redefine the default product route.

## Phase 3: Product Verification

Do not implement Phase 3 yet. Plan only.

Verification should compare:

* Product route behavior
* Pure diagnostic route behavior
* model-authored actions seen
* proxy decisions made
* files touched
* checks run
* receipt quality
* blocked/clarification states

The verification report should make the product/diagnostic split visible. It should record whether Source Proxy made the right orchestration decisions, whether the model authored explicit path/content/action data, whether the runtime executed only validated model-authored actions, whether protected paths and real app files stayed untouched, and whether receipts honestly separate proxy decisions from model-authored content.

## Stop Conditions

Stop and report NO-GO if:

* any runtime implementation seems required during this docs-only task
* source-of-truth docs conflict
* the plan would weaken anti-cheat/provenance
* the plan would make backend-created files acceptable
* the plan would make homepage-specific helper behavior the product pattern
* any provider/model call is needed
* any benchmark execution is attempted
* any real app file mutation is attempted

## Manual Verification Block

Commands to run at the end of this docs-only task:

```powershell
Get-Content -LiteralPath 'docs\evidence\source-proxy-tool-action-runtime-v1\human-messy-homepage-debug\root-cause.md'
Get-Content -LiteralPath 'docs\evidence\source-proxy-tool-action-runtime-v1\human-messy-homepage-debug\terminal-verification.md'
rg -n "Pure mode|Product mode|Product vs Pure|diagnostic|anti-cheat|provenance|no-cheat|benchmark pause|return gate|Mac|subagent|homepage|TaskSpec|tool action|receipt|protected" docs source_proxy scripts -g "*.md" -g "*.py"
Select-String -Path 'source_proxy\decision\task_spec_intake.py','source_proxy\decision\human_messy_homepage.py','scripts\agent-trials\run-source-proxy-human-messy-homepage-smoke.py','source_proxy\tests\test_coding_regression_pack.py' -Pattern 'pure|product|homepage|allowed|protected|model|authored|receipt|diagnostic|preselect|TaskSpec|target|messy' -CaseSensitive:$false | Select-Object -First 220
rg -n "no-cheat|anti-cheat|provenance|backend_created_content|model-authored|model authored|benchmark pause|return gate|advisory-only|Mac/subagent|Mac advisory|subagent" docs source_proxy scripts -g "*.md" -g "*.py"
rg --files docs source_proxy scripts | rg "source-proxy|tool-action|homepage|runtime|trial|benchmark|mac-subagent|hardening|coding-regression"
git diff --check
git status --branch --short --untracked-files=normal
```

Expected deliverables for this task:

1. `docs/evidence/source-proxy-orchestrator-correction/refined-plan.md`
2. no other file unless a tiny docs index pointer already exists and is clearly appropriate
3. final response with files changed, evidence, checks, blockers, GO/NO-GO, and next plan title only

Current plan result: GO for Britton review of this refined plan. NO-GO for implementation until later explicit approval.

Next plan title only: Source Proxy Orchestrator Correction Phase 0 Audit
