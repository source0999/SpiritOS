# Source Proxy Orchestrator Correction Phase 0 Audit

## Status

* Phase 0 audit only
* docs-only
* no runtime code changes made by this audit
* no tests changed by this audit
* no provider/model calls run by this audit
* no benchmark prompts run by this audit
* no real app files mutated by this audit
* no git branch, worktree, stash, reset, checkout, clean, stage, commit, or push performed

## Files Inspected

* `docs/evidence/source-proxy-orchestrator-correction/refined-plan.md`
* `docs/evidence/source-proxy-tool-action-runtime-v1/human-messy-homepage-debug/root-cause.md`
* `docs/evidence/source-proxy-tool-action-runtime-v1/human-messy-homepage-debug/terminal-verification.md`
* `docs/evidence/source-proxy-tool-action-runtime-v1/human-messy-homepage-debug/pure-mode-phase-1/phase-1-report.md`
* `docs/source-proxy-tool-action-runtime-v1-master-plan.md`
* `docs/source-proxy-tool-action-runtime-v1-new-chat-handoff.txt`
* `source_proxy/decision/task_spec_intake.py`
* `source_proxy/decision/human_messy_homepage.py`
* `source_proxy/decision/tool_actions.py`
* `source_proxy/decision/tool_action_executor.py`
* `source_proxy/decision/tool_action_loop.py`
* `source_proxy/decision/tool_action_safety.py`
* `scripts/agent-trials/run-source-proxy-human-messy-homepage-smoke.py`
* `source_proxy/tests/test_coding_regression_pack.py`

## Findings

The current architecture has the right no-cheat foundation: generic model action parsing, path-contained disposable workspace execution, protected-path validation, bounded loop receipts, raw model transcripts, parsed actions, diff/check receipts, and explicit anti-cheat scoring fields.

The over-correction is not that Pure mode exists. Pure mode is useful as a diagnostic benchmark lane because it removes Product helper support and asks whether the model can choose a safe path and author content. The risk is treating Pure mode as the product default. That would make Source Proxy behave like a raw local-model relay and would push task intent, workspace selection, and high-level path decisions too far onto Qwen.

Product mode currently restores usefulness through a homepage-specific bridge. It identifies the messy homepage prompt as a disposable `index.html` create candidate, sets `allowed_files` to `index.html` and `styles.css`, adds `transparent_default_target`, and prompts the model for an `index.html` `WriteFile` action. That fixed the immediate runtime gap, but it is too specific to become the general product pattern.

The smallest correct direction is to preserve Pure mode as diagnostic, keep Product mode as the daily messy-prompt route, and replace the homepage-specific bridge with a generic disposable artifact/create resolver. The proxy may decide task shape, workspace mode, allowed/protected boundaries, and context. The model must still author concrete path/content/action before runtime execution.

## Product vs Pure Mode Inventory

Product mode:

* `run_human_messy_homepage(..., mode="product")` is the default.
* `build_task_spec_intake(..., allow_messy_homepage_helper=True)` can classify the prompt as `create_new_file`.
* Product mode sets `target` to `index.html` through TaskSpec intake.
* Product mode sets `allowed_files` to `index.html` and `styles.css`.
* Product mode sets `model_may_choose_paths=False`.
* Product mode context includes `transparent_default_target: index.html`.
* Product mode scoring allows GO for useful output but marks `benchmark_eligible=false`.
* Product mode receipts expose `product_helper_used`, `transparent_default_target_used`, `system_preselected_target`, and `file_equals_model_action_content`.

Pure mode:

* `run_human_messy_homepage(..., mode="pure")` is available through the smoke script.
* Pure mode calls TaskSpec intake with `allow_messy_homepage_helper=False`.
* Pure mode replaces the Product TaskSpec with `_pure_mode_task_spec`, which has empty `target` and empty `allowed_files`.
* Pure mode sets `model_may_choose_paths=True`.
* Pure mode context omits `transparent_default_target`.
* Pure mode scoring requires common GO plus no product helper, no transparent default target, no system-preselected target, and a model-chosen target.
* Pure mode is correctly diagnostic/benchmark-oriented, not product-oriented.

Evidence note:

* The Phase 1 report shows Product mode GO but not benchmark eligible.
* The Phase 1 report shows Pure mode NO-GO because the model chose `README.md`, proving model-chosen path/content but not an openable homepage.

## Homepage-Specific Logic Inventory

Homepage-specific pieces currently present:

* `DEFAULT_HUMAN_MESSY_HOMEPAGE_PROMPT` in `source_proxy/decision/human_messy_homepage.py`.
* `DEFAULT_ALLOWED_FILES = ("index.html", "styles.css")`.
* `_is_messy_homepage_disposable_prompt()` in `task_spec_intake.py`, matching create-ish words plus homepage-ish words.
* The TaskSpec branch that sets `target = "index.html"`, `target_paths = ["index.html"]`, `task_kind = "create_new_file"`, `workspace_mode = "disposable_workspace"`, and `allowed = ["index.html", "styles.css"]`.
* Product context `transparent_default_target = "index.html"`.
* Product prompt text instructing the model to create the requested homepage and gives an example `WriteFile` with `target: "index.html"`.
* Score logic that checks for an openable HTML document in changed files.
* Smoke script name, evidence path, and report names all centered on `human-messy-homepage`.

Useful pieces to preserve:

* The disposable workspace execution path.
* The receipt fields separating Product helper use from model-authored content.
* The check that file bytes equal model action content.
* The anti-cheat fields for backend-created content, fallback use, dummy fixtures, real app mutation, product helper use, transparent default target, and system preselection.
* The ability to score Product and Pure differently.

Pieces to reduce or generalize:

* Homepage phrase detection should become a generic disposable artifact/create intent resolver.
* `index.html` and `styles.css` should not be the general allowed-file pattern.
* `transparent_default_target` should become a generic proxy decision field such as task shape or suggested artifact class, not a hardcoded homepage target.
* Product prompt examples should not hardcode only homepage JSON; they should present the generic action contract plus any proxy-decided boundaries.
* Smoke script serve/latest behavior should be made mode-aware later. It now writes `latest-product-run.json` and `latest-pure-run.json`, while `_read_latest()` still reads the older `latest-run.json`.

## Proxy-Orchestration Gaps

1. Generic artifact/create intent is incomplete. Current TaskSpec intake supports explicit bounded proposal tasks and the homepage helper, but non-homepage artifact prompts without explicit targets still tend toward `target_unresolved`.

2. Product mode is too prompt-specific. The proxy can make the homepage prompt useful, but the implementation path currently demonstrates a homepage bridge more than a reusable orchestration layer.

3. Pure mode bypasses too much orchestration for product use. Empty target and empty allowed files prove model autonomy, but that is a benchmark condition, not daily-driver UX.

4. Task shape and path responsibility are not separated enough. The proxy should be able to say "this is a disposable single-page artifact task" or "this is a docs edit with explicit path" without forcing the model to infer every high-level boundary from a messy prompt.

5. Receipts have useful anti-cheat fields, but the product/diagnostic distinction should become a first-class receipt concept rather than only homepage smoke score fields.

6. The smoke script's `--serve` path still reads the legacy `latest-run.json`, even though `--run --mode product|pure` now writes mode-specific latest files. This is evidence plumbing drift, not a Phase 0 implementation blocker.

## No-Cheat Protections To Preserve

* `parse_model_actions(..., author="backend")` rejects backend-authored content with `backend_authorship_rejected`.
* Free-floating code without a path/action rejects with `free_floating_code_no_path_action`.
* Write/edit actions require explicit model-authored target and content.
* Allowed-file validation blocks wrong files when `model_may_choose_paths` is false.
* Path traversal, symlink escape, protected paths, and forbidden files are blocked.
* RunCheck is allowlisted, bounded, and network-blocked by default.
* Bounded loop receipts include raw model transcripts, model call packets, parse results, parsed actions, executions, skipped checks, diagnostics, blocked reasons, and files touched.
* Authority/protected-path failures are not retried as repair opportunities.
* Score fields detect backend-created content, fallback use, deterministic scaffold use, dummy fixture use, real app mutation, helper use, transparent default target use, and system-preselected target use.
* Mac workers and subagents remain advisory-only and cannot write, apply, bypass Source Proxy authority, or start hidden execution.
* Benchmark/stress testing remains paused until the return gate is explicitly satisfied.

## Tests That Must Not Be Weakened

* TaskSpec protected-path blocking.
* Tool contract tool set and stable error codes.
* Parser raw transcript preservation and Plan 2 execution blocking.
* Multiple model-action parsing.
* Aider/path-bound parsing only when path-bound.
* Wrong file and path traversal blocking.
* Protected path and symlink escape blocking.
* Unsafe command, hidden background command, and network command blocking.
* Bounded loop raw transcript, parsed action, diagnostics, file touch, retry, and no-retry behavior.
* Fake apply claim trap and wrong-file trap.
* Product/Pure anti-cheat assertions for helper use, benchmark eligibility, model-chosen target, and model-authored bytes.

## Tests That May Reward Narrow Scaffolding

The current Product homepage tests are useful as regression tests for the discovered gap, but they can reward a narrow Product helper if treated as product architecture proof. Specifically:

* The messy homepage Product path expects `index.html` and `styles.css`.
* The Product prompt asks for exactly one `WriteFile` to `index.html`.
* Product GO does not require the model to choose the path.
* The Product fixture proves useful output and no-cheat content bytes, but not generic artifact/create orchestration.

These tests should remain, but Phase 1 should add non-homepage disposable artifact/create tests so Product success does not depend on homepage-specific scaffolding.

## Proposed Minimal Reverts/Reductions

Do not delete Pure mode.

Do not delete provenance, receipts, anti-cheat fields, or Product/Pure score fields.

Do not revert the generic tool action parser, executor, or bounded loop.

Minimal reductions for Phase 1 planning:

* Move homepage-specific Product helper behavior behind a named diagnostic or legacy compatibility surface once generic artifact/create resolution exists.
* Reduce direct use of `transparent_default_target = "index.html"` in product prompting.
* Rename or reframe `product_helper_used` so generic proxy orchestration is not treated as cheating by default. Homepage-specific target preselection should be marked separately from legitimate generic proxy classification.
* Fix mode-aware latest/serve evidence plumbing after a plan approves implementation.
* Keep Product homepage smoke as a regression case, but stop treating it as sufficient proof of Product orchestration.

## Proposed Generic Replacement Direction

Phase 1 should plan a generic resolver with these boundaries:

* Detect disposable artifact/create intent without hardcoding homepage as the only useful create class.
* Classify task shape, such as single-page artifact, small file bundle, docs/config edit, or clarification-required real-repo implementation.
* Choose safe workspace mode.
* Set allowed scope generically: exact path when user supplies one, safe artifact class or bounded workspace pattern when disposable create is clear, and no write scope when real-repo target is vague.
* Provide context and constraints to the model, including protected paths, workspace mode, file count limits, allowed/protected boundary, and action contract.
* Require the model to author explicit path/content/action.
* Validate and execute only model-authored actions.
* Record receipt fields that separate proxy decisions from model-authored content.

The generic resolver should not write task content, silently create files, preselect exact files only to satisfy a benchmark, or upgrade vague prose into files without model-authored path/content/action.

## Audit Questions Answered

1. Pure/model-autonomy additions: `mode="pure"`, `_pure_mode_task_spec`, empty target/allowed files, `model_may_choose_paths=True`, Pure prompt text, benchmark eligibility fields, Pure evidence path, and Pure tests.
2. Product additions: homepage helper toggle, Product mode default, `index.html` target, `styles.css` allowed file, transparent default target, Product score fields, Product evidence report.
3. Homepage preselection happens in `task_spec_intake.py` and `human_messy_homepage.py` Product context/prompt.
4. Product-useful pieces: disposable workspace, generic action contract, bounded loop, receipts, anti-cheat fields, model-authored byte equality, and visible Product/Pure scoring.
5. Benchmark-only pieces: Pure empty-target/empty-allowed mode and benchmark eligibility gate.
6. Too homepage-specific pieces: prompt detection, allowed files, target, prompt text, smoke naming, and openable-homepage scoring as sole success.
7. Model overburdening risk: treating Pure as default forces local models to infer high-level task shape and path responsibility from messy prompts without Source Proxy orchestration.
8. No-cheat protections: backend-authorship rejection, free-floating code rejection, allowed/protected validation, receipt completeness, no retry on authority failures, and anti-cheat score fields.
9. Narrow scaffolding risk: Product homepage tests prove one useful bridge, not generic Product orchestration.
10. Smallest Phase 1 set: plan generic artifact/create resolver, keep Pure diagnostic, keep Product default, preserve no-cheat fields, add non-homepage product tests, and defer implementation until explicit approval.

## Explicit GO/NO-GO For Phase 1

GO for a Phase 1 planning document titled below.

NO-GO for runtime implementation, test edits, provider/model calls, benchmark execution, or real app mutation until Britton explicitly approves the Phase 1 implementation scope.

GO conditions for the next plan:

* It preserves Pure mode as diagnostic/benchmark behavior.
* It restores Product mode as Source Proxy orchestration, not raw local-model autonomy.
* It generalizes homepage-specific helper behavior into artifact/create task shape classification.
* It preserves model-authored path/content/action execution.
* It preserves protected path validation, anti-cheat/provenance, receipts, and Mac/subagent advisory-only boundaries.

NO-GO conditions for the next plan:

* It makes backend-created files acceptable.
* It makes homepage-specific helpers the product pattern.
* It removes Pure mode instead of parking it as diagnostic.
* It weakens model-authored action requirements.
* It runs provider/model calls or benchmarks before implementation approval.

## Manual Verification Block

Commands run for this audit:

```powershell
rg -n "Source Proxy Orchestrator|Pure mode|Product mode|human_messy_homepage|homepage helper|TaskSpec|tool action" C:\Users\smith\.codex\memories\MEMORY.md
git status --branch --short --untracked-files=normal
Get-Content -LiteralPath 'docs\evidence\source-proxy-orchestrator-correction\refined-plan.md'
git diff -- source_proxy/decision/task_spec_intake.py source_proxy/decision/human_messy_homepage.py scripts/agent-trials/run-source-proxy-human-messy-homepage-smoke.py source_proxy/tests/test_coding_regression_pack.py docs/evidence/source-proxy-tool-action-runtime-v1/human-messy-homepage-debug/root-cause.md docs/evidence/source-proxy-tool-action-runtime-v1/human-messy-homepage-debug/terminal-verification.md
Get-Content -LiteralPath 'source_proxy\decision\task_spec_intake.py'
Get-Content -LiteralPath 'source_proxy\decision\human_messy_homepage.py'
Get-Content -LiteralPath 'scripts\agent-trials\run-source-proxy-human-messy-homepage-smoke.py'
Get-Content -LiteralPath 'source_proxy\decision\tool_action_executor.py'
Get-Content -LiteralPath 'source_proxy\decision\tool_action_loop.py'
Get-Content -LiteralPath 'source_proxy\decision\tool_actions.py'
Select-String -Path 'source_proxy\tests\test_coding_regression_pack.py' -Pattern 'messy_homepage|human_messy_homepage|pure|product|backend_created_content|model-authored|protected|fake|wrong-file|tool_action|model_may_choose_paths' -CaseSensitive:$false -Context 2,3
Get-Content -LiteralPath 'docs\source-proxy-tool-action-runtime-v1-master-plan.md'
Get-Content -LiteralPath 'docs\source-proxy-tool-action-runtime-v1-new-chat-handoff.txt'
rg -n "benchmark pause|Benchmark return gate|return gate|no-cheat|backend-created|model-authored|Mac worker|Mac subagents|advisory/check|advisory-only|Stop if backend-created|execute only model-authored|vague/freeform" docs\source-proxy-tool-action-runtime-v1-master-plan.md docs\source-proxy-tool-action-runtime-v1-new-chat-handoff.txt docs -g "*.md" -g "*.txt"
Get-Content -LiteralPath 'docs\evidence\source-proxy-tool-action-runtime-v1\human-messy-homepage-debug\pure-mode-phase-1\phase-1-report.md'
rg -n "allow_messy_homepage_helper|_is_messy_homepage_disposable_prompt|transparent_default_target|DEFAULT_ALLOWED_FILES|model_may_choose_paths|pure_mode|benchmark_eligible|product_helper_used|system_preselected_target|latest-.*run|LATEST_PATH|_read_latest|latest-run" source_proxy scripts docs\evidence\source-proxy-tool-action-runtime-v1\human-messy-homepage-debug -g "*.py" -g "*.md" -g "*.json" -g "*.txt"
rg -n "backend_authorship_rejected|free_floating_code_no_path_action|target_not_allowed|path_escape|protected_path|model_may_choose_paths|RunCheck|network_blocked|AskClarification|ReturnFinal|raw_model_transcripts|parsed_actions|diagnostics_packet|files_touched" source_proxy\decision source_proxy\tests\test_coding_regression_pack.py
git diff --check
git status --branch --short --untracked-files=normal
```

Expected output:

* Targeted greps show Product/Pure fields, homepage-specific helper logic, model-authored action protections, receipt fields, protected path protections, and benchmark/advisory boundaries.
* `git diff --check` passes with no whitespace errors. Existing LF-to-CRLF warnings may print for already-dirty files.
* `git status --branch --short --untracked-files=normal` shows this audit doc plus the previously dirty/untracked Source Proxy evidence/code files.

## Blockers

None for Phase 1 planning.

Implementation remains blocked until later explicit approval.

## Next Plan Title Only

Source Proxy Orchestrator Correction Phase 1 Product Orchestration Plan
