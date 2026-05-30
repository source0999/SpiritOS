# Realistic /coding Prompt Trial Remediation Closeout

Generated: 2026-05-28

## Before bug summary

The `/coding` Agent Trials sidebar labeled the operator/batch request as `Britton realistic prompt`. That visible preview showed text like `hey can you run the 25 agent trial...`, while the Playwright runner submitted a different generated prompt into the `/coding` composer. The artifact used `prompt_text` and `typed_through_ui`, but did not record `submitted_prompt`, selector proof, prompt preview match, meta-prompt leak status, or copy-paste diagnostics.

## After behavior summary

- The runner records `operator_command`, `operator_run_request`, `submitted_prompt`, `prompt_fixture_id`, `prompt_profile`, `submitted_through_ui`, `composer_selector_used`, `transcript_match`, `prompt_preview_matches_submitted_prompt`, and `meta_prompt_leak`.
- Britton-realistic coding fixtures now contain 12 messy task prompts submitted through `/coding`, plus separate clean-control prompts.
- Expected blocked, clarification, and failed-safe fixtures produce `copy_paste_block` diagnostics.
- Summary JSON/markdown report realistic intake and diagnostic coverage metrics.
- The Agent Trials UI now separates Generated command, Operator run request, Actual prompts to be submitted, Last submitted prompt, and Last diagnostics block.

## Files changed

- `scripts/agent-trials/run-ui-agent-trials.mjs`
- `tests/ui-agent-trials/fixtures/coding-agent-prompts.json`
- `tests/ui-agent-trials/trial-result-schema.ts`
- `tests/ui-agent-trials/trial-result-schema.test.ts`
- `tests/ui-agent-trials/realistic-prompt-remediation.test.ts`
- `src/lib/coding/agent-trials-ui.ts`
- `src/lib/coding/__tests__/agent-trials-ui.test.ts`
- `src/components/coding/CodingCommandCenterShell.tsx`
- `src/components/coding/__tests__/coding-command-center-shell.test.tsx`
- `docs/evidence/agent-runtime-trial-harness/realistic-prompt-remediation/baseline-audit.md`
- `docs/evidence/agent-runtime-trial-harness/realistic-prompt-remediation/contracts.md`
- `docs/evidence/agent-runtime-trial-harness/realistic-prompt-remediation/fixtures.md`
- `docs/evidence/agent-runtime-trial-harness/realistic-prompt-remediation/closeout.md`

## Commands run

| Increment | Command | Result |
| --- | --- | --- |
| 0.2 | `node scripts/agent-trials/run-ui-agent-trials.mjs --agent coding --viewport desktop --limit 1 --profile britton-realistic` | Baseline reproduced; old artifact lacked contract fields. |
| 1.1/1.2 | `npx --no-install vitest run tests/ui-agent-trials/trial-result-schema.test.ts` | PASS, 2 tests. |
| 2.1 | Fixture parse/id print with `node -e ...` | PASS, 12 fixture ids. |
| 2.2 | Clean-control separation check with `node - <<'NODE' ...` | PASS, 12 prompt pairs separate. |
| 3.1 | `node scripts/agent-trials/run-ui-agent-trials.mjs --agent coding --viewport desktop --limit 1 --profile britton-realistic` | PASS/GO; artifact had `submitted_prompt`, UI proof, and `meta_prompt_leak: false`. |
| 3.2 | `node scripts/agent-trials/run-ui-agent-trials.mjs --agent coding --viewport desktop --limit 1 --profile britton-realistic` after blocked status wiring | Expected blocked diagnostic produced. Old summary briefly returned NO-GO before 3.3 fixed expected-block accounting. |
| 3.3 | `node scripts/agent-trials/run-ui-agent-trials.mjs --agent coding --viewport desktop --limit 3 --profile britton-realistic` | PASS/GO; 3 blocked expected outcomes with copy diagnostics. |
| 4.1 | `grep -RIn "Britton realistic prompt\\|Copy prompt \\+ command\\|Operator run request\\|Generated command" ...` | PASS; misleading label removed from UI. |
| 4.2 | `npx --no-install vitest run src/lib/coding/__tests__/agent-trials-ui.test.ts` | PASS, 7 tests. |
| 4.2 | `npx --no-install vitest run src/components/coding/__tests__/coding-command-center-shell.test.tsx --testNamePattern "Agent Trials sidebar runner"` | PASS, 1 focused test. |
| 5.1 | `npx --no-install vitest run tests/ui-agent-trials/realistic-prompt-remediation.test.ts tests/ui-agent-trials/trial-result-schema.test.ts src/lib/coding/__tests__/agent-trials-ui.test.ts src/components/coding/__tests__/coding-command-center-shell.test.tsx --testNamePattern "realistic prompt remediation|trial result contracts|agent trials UI helpers|Agent Trials sidebar runner"` | PASS, 4 files, 16 active tests. |
| 5.2 | `node scripts/agent-trials/run-ui-agent-trials.mjs --agent coding --viewport desktop --limit 5 --profile britton-realistic` | PASS/GO; artifacts root `docs/evidence/agent-runtime-trial-harness/plan-5/artifacts/2026-05-28T04-02-07-889Z-coding-desktop-britton-realistic`. |
| 5.2 | `node scripts/agent-trials/run-ui-agent-trials.mjs --agent coding --viewport mobile --limit 3 --profile britton-realistic` | PASS/GO; artifacts root `docs/evidence/agent-runtime-trial-harness/plan-5/artifacts/2026-05-28T04-02-25-880Z-coding-mobile-britton-realistic`. |
| 5.2 | `node scripts/agent-trials/run-ui-agent-trials.mjs --agent combined --viewport desktop --limit 3 --profile britton-realistic` | PASS/GO; artifacts root `docs/evidence/agent-runtime-trial-harness/plan-5/artifacts/2026-05-28T04-02-51-202Z-combined-desktop-britton-realistic`. |
| 5.2 | `npx --no-install tsc --noEmit --pretty false` | PASS. |
| 5.2 | `git diff --check` | PASS. |
| 5.2 | `git status --branch --short --untracked-files=normal` | PASS for inspection; dirty worktree existed before this remediation and still contains unrelated pre-existing changes. |

## Pass/fail table

| Check | Status | Evidence |
| --- | --- | --- |
| No meta prompt leak | PASS | Latest proof summaries show `meta_prompt_leak_failures: 0`; trial artifacts include `meta_prompt_leak: false`. |
| Actual submitted prompts visible | PASS | Artifacts include `submitted_prompt`; UI shows Actual prompts to be submitted. |
| Submitted through UI | PASS | Latest summaries show `prompts_submitted_through_ui` equals total trials. |
| Blocked/failed diagnostics | PASS | Blocked desktop proof shows `blocked_with_copy_diagnostics: 3`; artifacts include `copy_paste_block`. |
| Protected path and hidden mutation traps safe | PASS | `hidden_mutation_failures: 0`; protected path attempts are counted without mutation. |
| No forbidden authority | PASS | Safety fields remain false for apply, commit, push, provider, Cartographer, and hidden workers. |
| Summary clarity | PASS | Summary JSON includes all required realistic intake metrics. |
| TypeScript | PASS | `npx --no-install tsc --noEmit --pretty false`. |
| Whitespace diff check | PASS | `git diff --check`. |

## Screenshots and artifacts

- Baseline artifact: `docs/evidence/agent-runtime-trial-harness/plan-5/artifacts/2026-05-28T03-51-09-143Z-coding-desktop-britton-realistic`
- Desktop proof batch: `docs/evidence/agent-runtime-trial-harness/plan-5/artifacts/2026-05-28T04-02-07-889Z-coding-desktop-britton-realistic`
- Mobile proof batch: `docs/evidence/agent-runtime-trial-harness/plan-5/artifacts/2026-05-28T04-02-25-880Z-coding-mobile-britton-realistic`
- Combined proof batch: `docs/evidence/agent-runtime-trial-harness/plan-5/artifacts/2026-05-28T04-02-51-202Z-combined-desktop-britton-realistic`
- Latest summary: `docs/evidence/agent-runtime-trial-harness/plan-5/summary.json`
- Combined report: `docs/evidence/agent-runtime-trial-harness/plan-6/combined-report.json`

## Remaining limitations

- The UI diagnostics block is a labeled copy location and points to the latest artifact JSON; it does not live-read the newest filesystem artifact into the browser.
- The runner proves UI intake through composer value after submit and screenshot/trace artifacts. It does not currently capture a backend request payload because this preview-only harness does not activate provider/model execution.
- Several unrelated files were already dirty before this remediation; they were not reverted.

## Phase reviews

- Phase 0: GO. Baseline bug was located and reproduced; evidence exists.
- Phase 1: GO. Prompt and diagnostics contracts were defined and tested.
- Phase 2: GO. Messy Britton fixtures and clean controls are separate and validated.
- Phase 3: GO. Runner artifacts, diagnostics, and summary metrics now prove realistic prompt intake.
- Phase 4: GO. UI labels and actual prompt preview now distinguish operator request from submitted prompts.
- Phase 5: GO. Targeted tests and requested proof batches passed.
- Phase 6: GO. Closeout evidence exists.

## Britton readiness

Britton can now start proper realistic testing. The realistic prompt trial is no longer a clean lab fixture pass or a preview of the batch-run prompt. It records the actual prompt submitted through `/coding`, whether the preview matched it, whether a meta prompt leaked, and the copy-paste diagnostics for expected blocks/failures.

UI simplification and Codex-like feature polish are unblocked from this harness perspective.

GO / NO-GO:

- GO for moving on to UI simplification and Codex-like feature polish.

