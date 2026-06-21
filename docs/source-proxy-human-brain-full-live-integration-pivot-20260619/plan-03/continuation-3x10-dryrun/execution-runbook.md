# Plan 3 3x10 Dry-Run Execution Runbook

## Global Rules

1. Each future stage is one Codex run.
2. Codex stops after each stage for human review.
3. Maximum 3 auto-fix/rerun attempts per prompt.
4. If still failing after 3 attempts, mark NEEDS_FIX and continue only if the next prompt is independent; otherwise stop.
5. No new dry-run harness may bypass real Source Proxy routing.
6. Prefer existing canonical workflow/task harness.
7. If no real harness exists, write NEEDS_FIX and stop before creating a parallel engine.
8. If media/Jellyfin/SpiritFlix files are touched, stop and report safety violation.
9. If broad tests time out, document the exact command and whether focused truth-critical tests passed.
10. No stage may claim GO using top-level booleans only.

## Stage 3 Harness Rule

Use existing canonical Source Proxy workflow/task harness paths only.

Do not create a new dry-run engine.

Do not create a parallel test orchestration layer.

Do not add new `source_proxy/tests` files or directories in Stage 3 unless Britton explicitly approves after reviewing Stage 0-1.

If the existing workflow cannot run the 3x10 prompts, write NEEDS_FIX and stop for human review.

Codex must provide evidence that the selected harness uses real Source Proxy routing/task paths. No Set A prompt may run until Britton approves that evidence.

## Prompt Execution Rules

- Run one prompt at a time.
- Preserve the exact user prompt from `battery-v4.1.md`.
- Use `battery-v4.1.json` only for grading expectations, not as user-facing prompt text.
- Record task ID, trace ID, lanes invoked, required lanes, downstream consumer event, and final work product.
- Mark BLOCKED_ENV when live search, Mac, Qwen, verifier, or another required environment is unavailable and no honest substitute exists.
- Do not count local repo fallback as internet.
- Do not count unconsumed output as PASS.
- Do not count preview/advisory/status/route-exists/metadata-only output as PASS.
- Do not count Mac-required work as done by Dell unless the work was not actually Mac-required.
- Do not count code work as verified unless Qwen/verifier requirements are satisfied or honestly marked failed/blocked.

## Closeout Rules

- PASS requires the user goal to be reached and the required hidden expectations to be satisfied.
- NEEDS_FIX is the default for useful but acceptance-incomplete output.
- Failure buckets must identify root cause and exact next patch target.
- Battery closeout is 30/30 PASS or honest NEEDS_FIX/BLOCKED. No partial GO.
