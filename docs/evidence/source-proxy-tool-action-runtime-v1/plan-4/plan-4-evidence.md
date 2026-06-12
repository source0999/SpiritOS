# Source Proxy Tool Action Runtime v1 Plan 4 Evidence

Plan: Plan 4/8: Bounded Agent Loop And Verification Receipts.

Status: implemented and verified.

## Phase 4.1 Loop Controller

Implemented:

- `source_proxy/decision/tool_action_loop.py`
  - Adds `BoundedAgentLoopRequest` for TaskSpec, context packet, workspace contract, model identity, adapter lane, recommended checks, verification policy, and retry caps.
  - Adds `run_bounded_agent_loop(...)` with an injected model-call function so Plan 4 tests prove loop behavior without provider/model routing.
  - Sends each model call a visible packet containing TaskSpec, context packet, tool contract, workspace contract, observations, and loop policy.
  - Executes parsed actions through the Plan 3 disposable workspace executor.
  - Stops on `ReturnFinal`, blocked state, failed format cap, failed verification cap, or partial completion with skipped checks.

Evidence:

- Bounded loop test asserts the model packet includes `tool_contract`.
- Successful write action executes through the Plan 3 executor and produces a diff.
- Loop stops after one model call when verification policy skips checks.

GO/NO-GO: GO.

## Phase 4.2 Retry Policy

Implemented:

- Format retry cap defaults to one retry.
- Verification repair cap defaults to one repair.
- Authority/protected-path parser rejects and executor blocks are not retried.
- Partial completion is explicit when productive work exists but policy skips checks.

Evidence:

- Bad free-floating code followed by invalid text makes exactly two calls and ends `failed_format`.
- `.env.local` write attempt ends `blocked`, with one model call and no execution attempt.
- Failing recommended check retries once, then ends `failed_verification`.

GO/NO-GO: GO.

## Phase 4.3 Receipts

Implemented:

- `BoundedAgentLoopReceipt` records raw model transcripts, model packets, parse results, parsed actions, execution receipts, skipped checks, final state, diagnostics packet, and optional receipt path.
- Receipt writer persists JSON when a path is supplied.
- Diagnostics packet includes model id, adapter source, final state, model call count, retries used, parsed action count, execution count, blocked reasons, files touched, and skipped checks.

Evidence:

- Receipt test asserts raw transcript preservation.
- Receipt test asserts parsed `WriteFile` action is recorded.
- Receipt test asserts diff output includes the Plan 4 write.
- Saved JSON receipt includes touched files in the diagnostics packet.

GO/NO-GO: GO.

## Phase 4.4 Verification Policy

Implemented:

- Recommended checks run only when `run_recommended_checks=True`.
- Skipped checks record command and reason.
- Recommended checks execute through the Plan 3 RunCheck allowlist.
- Failed verification feeds observations back into the next bounded model call until the repair cap is exhausted.

Evidence:

- Skipped check receipt records `manual_policy`.
- Allowlisted verification commands are routed through `RunCheck`.
- Failed verification command `python -m py_compile missing.py` produces `run_check_failed` and ends honestly after the repair cap.

GO/NO-GO: GO.

## Checks

Executed from `Z:\` PowerShell against `/home/source/SpiritOS`:

```powershell
ssh source@10.0.0.186 "cd /home/source/SpiritOS && .venv-source-proxy/bin/python -m pytest source_proxy/tests/test_coding_regression_pack.py -k 'bounded_agent_loop'"
ssh source@10.0.0.186 "cd /home/source/SpiritOS && .venv-source-proxy/bin/python -m py_compile source_proxy/decision/tool_action_loop.py"
```

Results:

- Plan 4 bounded loop slice: `4 passed, 81 deselected`.
- `py_compile`: passed on Dell.

Final combined checks are recorded in the Plan 4 closeout.

## Forbidden Scope Avoided

- No Plan 5 Mac/subagent broker.
- No provider/model calls; model behavior is injected in tests.
- No benchmark or stress tests.
- No safe apply to the real repo.
- No Cartographer mutation.
- No hidden workers.
- No branch, worktree, stash, reset, checkout, clean, commit, or push.
