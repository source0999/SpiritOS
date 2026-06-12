# Source Proxy Tool Action Runtime v1 Plan 2 Closeout

Plan completed: Plan 2/8: Tool/Action Contract And Parser.

## Files Changed

- `source_proxy/decision/tool_actions.py`
- `source_proxy/tests/test_coding_regression_pack.py`
- `docs/evidence/source-proxy-tool-action-runtime-v1/plan-2/plan-2-evidence.md`
- `docs/evidence/source-proxy-tool-action-runtime-v1/plan-2/plan-2-closeout.md`

## Evidence Created

- `docs/evidence/source-proxy-tool-action-runtime-v1/plan-2/plan-2-evidence.md`
- `docs/evidence/source-proxy-tool-action-runtime-v1/plan-2/plan-2-closeout.md`

## Increment Results

- Increment 2.1.1 Action envelope: GO. `SourceProxyAction` is versioned and captures model/source metadata, adapter source, allowed-file snapshot, target, arguments, reason, approval requirement, authorship, and parser-only execution state.
- Increment 2.1.2 Result envelope: GO. `SourceProxyActionResult` captures status, blocked reason, files touched, diff summary, stdout/stderr, observation, receipt path, adapter source, schema version, and error code.
- Increment 2.1.3 Stable error codes: GO. Contract exposes stable parse, adapter, target-policy, and Plan 3 execution-boundary error codes.
- Increment 2.2.1 ReadFile: GO. Defined as a read action.
- Increment 2.2.2 ListFiles: GO. Defined as a read action.
- Increment 2.2.3 SearchRepo: GO. Defined as a read action.
- Increment 2.2.4 WriteFile: GO. Defined as a write action and blocked until Plan 3.
- Increment 2.2.5 EditFile: GO. Defined as a write action and blocked until Plan 3.
- Increment 2.2.6 MultiEdit: GO. Defined as a write action and blocked until Plan 3.
- Increment 2.2.7 RunCheck: GO. Defined as an execute action and blocked until Plan 3.
- Increment 2.2.8 AskClarification: GO. Defined as a respond action.
- Increment 2.2.9 ReturnFinal: GO. Defined as a respond action.
- Increment 2.3.1 Strict JSON parser: GO. Parses one action or an `actions` list.
- Increment 2.3.2 Line-delimited parser: GO. Parses multiple JSON action lines and normalizes Continue `Bash` string arguments only.
- Increment 2.3.3 Path/content block parser: GO. Parses explicit `<file path="...">...</file>` blocks only.
- Increment 2.3.4 Wrong-format rejection/repair prompt: GO. Free-floating code with no path/action is rejected with `free_floating_code_no_path_action`.
- Increment 2.3.5 Preserve raw transcript and parse decisions: GO. Parse result includes `raw_transcript` and per-parser decisions.
- Increment 2.4.1 Continue Bash adapter: GO. String arguments normalize only when the model-authored tool is `Bash`; plain `RunCheck` string arguments reject.
- Increment 2.4.2 Aider-like edit chunks: GO. Search/replace chunks parse only with an explicit model-authored repo path.
- Increment 2.4.3 Free-floating HTML/code rejection: GO. Code with no path/action is not upgraded into a file.
- Increment 2.4.4 Adapter source receipt lane: GO. `adapter_source` is recorded on parse results, actions, decisions, and Plan 2 blocked results.

## Checks Run

```powershell
ssh source@10.0.0.186 "cd /home/source/SpiritOS && .venv-source-proxy/bin/python -m pytest source_proxy/tests/test_coding_regression_pack.py -k 'task_spec_intake or tool_action'"
ssh source@10.0.0.186 "cd /home/source/SpiritOS && .venv-source-proxy/bin/python -m pytest source_proxy/tests/test_proxy_agent_routing.py source_proxy/tests/test_coding_regression_pack.py -k 'task_spec_intake or tool_action or prompt_packet_exposes_task_spec_intake'"
ssh source@10.0.0.186 "cd /home/source/SpiritOS && .venv-source-proxy/bin/python -m py_compile source_proxy/decision/tool_actions.py"
ssh source@10.0.0.186 "cd /home/source/SpiritOS && git diff --check"
git status --branch --short --untracked-files=normal
```

Outputs:

- Coding regression parser/intake slice: `13 passed, 63 deselected`.
- Combined routing/regression selected slice: `13 passed, 86 deselected`.
- `py_compile`: passed on Dell.
- `git diff --check`: clean.
- Status showed pre-existing dirty/untracked roadmap/evidence files plus Plan 1 and Plan 2 changes.

## Expected Output

- Model-authored JSON actions parse into generic Source Proxy action envelopes.
- Multiple model-authored JSON action lines parse into multiple action envelopes.
- Explicit path/content blocks parse only when the model provides a repo path.
- Continue `Bash` string arguments normalize into a blocked `RunCheck`; non-`Bash` string arguments reject.
- Aider-like edit chunks parse only when model-authored, path-bound, and inside the allowed snapshot when provided.
- Adapter source lane is preserved on the parse receipt.
- Free-floating code with no path/action is rejected rather than upgraded into a file.
- Backend-authored content is rejected before it can masquerade as model output.
- Write/edit/multiedit/run actions remain blocked until Plan 3 and produce no file mutations.

## Manual Verification

Copy-paste terminal verification block:

```powershell
ssh source@10.0.0.186 "cd /home/source/SpiritOS && .venv-source-proxy/bin/python -m pytest source_proxy/tests/test_coding_regression_pack.py -k 'task_spec_intake or tool_action'"
ssh source@10.0.0.186 "cd /home/source/SpiritOS && .venv-source-proxy/bin/python -m pytest source_proxy/tests/test_proxy_agent_routing.py source_proxy/tests/test_coding_regression_pack.py -k 'task_spec_intake or tool_action or prompt_packet_exposes_task_spec_intake'"
ssh source@10.0.0.186 "cd /home/source/SpiritOS && .venv-source-proxy/bin/python -m py_compile source_proxy/decision/tool_actions.py"
ssh source@10.0.0.186 "cd /home/source/SpiritOS && git diff --check"
git status --branch --short --untracked-files=normal
```

## Forbidden Scope Avoided

- No Plan 3 executor behavior.
- No provider/model calls.
- No benchmark or stress tests.
- No safe apply.
- No Cartographer mutation.
- No hidden workers.
- No branch, worktree, stash, reset, checkout, clean, commit, or push.

## Blockers

None for Plan 2.

Environment note: authoritative checks run over SSH on `/home/source/SpiritOS` with `.venv-source-proxy/bin/python`.

## Rollback Guidance

Rollback by reverting only the Plan 2 files listed above. Preserve unrelated dirty tree work, Plan 0/1 artifacts, and other pre-existing evidence/scripts.

## GO/NO-GO

GO for Plan 2 closeout.

NO-GO for Plan 3 start in this turn.

Next plan title only:

`Plan 3/8: Workspace-Only Action Executor`
