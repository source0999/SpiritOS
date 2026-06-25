# Generic Model Contract Stability Rerun - 2026-06-25

## Recovery Summary

This recovery resumed the interrupted generic model contract implementation for
`MODEL_PROMPT_CONTRACT_REDESIGN_NEEDED`. It did not restart the original prompt and
did not wipe the worktree. A fresh host-side recovery snapshot was saved before
edits:

- `/tmp/spiritos-codex-recovery/recovery-current.diff`
- `/tmp/spiritos-codex-recovery/recovery-current.diffstat`
- `/tmp/spiritos-codex-recovery/recovery-current.status`

The interrupted run had partially applied the intended runner/test changes and had
also overwritten tracked Set A evidence. The implementation diff was preserved. The
accidental evidence churn was restored by exact path, excluding `_stage4r_runner.py`.

## Implementation Summary

Runner changes now present:

- maintained general `DECISION_VERB_VOCABULARY`
- `decision_line_is_vague` guard for non-decisions and vague bodies
- `select_work_product_lane` based on task shape, not prompt id
- generic stabilized research lane metadata with local Ollama provider, low
  temperature, larger `num_predict`, timeout, and selection basis
- `repair_vague_decision_lines` repair path that does not silently PASS when no
  rewrite is available
- `classification_for_stability` and `run_stability_check`
- append-only per-run-id receipt copies under `runs/<run_id>/`

Tests now cover:

- accepted concrete planning verbs: Investigate, Adopt, Integrate, Build, Recommend,
  Validate, Assess, Test, Leverage, Determine, Prototype, and related verbs
- rejected vague lines: Think about it, Maybe consider stuff, do things, look into it,
  consider it, and similar non-decisions
- no prompt-id branch in new helper paths
- A2/A5/A9 structured packet lane remains intact
- fake GO and model-owned source URLs still fail

## Evidence Churn Restored

The following class of accidental churn was restored:

- tracked Set A rerun receipts and Markdown summaries (`A3.json`, `A3.md`,
  `summary.json`, `summary.md`, `4r*.md`, preflight files, verdict/test-result docs,
  and `failure-buckets.md`)

The following were preserved and not staged by this recovery:

- unrelated SpiritFlix/media changes
- deleted plan-02 evidence under `home/source/spiritos-evidence`
- untracked `nul`

## Tests Run

- `python3 -m py_compile docs/.../set-a-rerun/_stage4r_runner.py` - PASS
- `.venv/bin/python -m pytest source_proxy/tests/test_plan3_stage4r_packet_runner.py -q` - PASS (`37 passed`)
- requested backend regression slice - PASS (`133 passed` after rerunning one
  transient browser-verifier timeout)

## Live Stability Proof

Live model availability was checked at `http://127.0.0.1:11434/api/tags`.

At recovery time, the local Ollama service was reachable and reported available
models including `gemma3n:e4b`. Because the task required no Set B/C and no Plan 4,
the eligible live proof was limited to A3 and then full Set A only if A3 was stable.

Live proof result:

- Initial A3 stability runs before the prompt-contract tightening were unstable:
  - `run-20260625T035628Z`: `PASS`
  - `run-20260625T040050Z`: `NEEDS_FIX`
    (`research_materially_changed_output`, `garbled_or_fabricated_tokens_detected`,
    `research_change_source_not_from_raw_sources`)
  - `run-20260625T040556Z`: `NEEDS_FIX`
    (`research_materially_changed_output`, `research_change_source_not_from_raw_sources`)
- After tightening the generic research prompt to require exact four-line
  `Finding` / `Source` / `Decision changed` / `Why this changes the recommendation`
  blocks and to reject prose-only `Evidence Used` substitutes, A3 was rerun three
  times:
  - `run-20260625T041716Z`: `PASS`
  - `run-20260625T042249Z`: `BLOCKED_ENV`
    (`live research provider returned no sources`; failed gates also recorded
    `live_search_sources`, `research_materially_changed_output`,
    `research_change_source_not_from_raw_sources`)
  - `run-20260625T042819Z`: `PASS`
- Full Set A stability runs: not run, because A3 did not produce stable PASS across
  all three reruns.
- Set B/C: not run.
- Plan 4: not started.

No tracked latest receipts were intentionally staged as stability evidence. The
implementation preserves per-run receipt support so future live reruns can keep
append-only copies under `runs/<run_id>/`.

## Remaining Blockers

- The code and focused tests are coherent.
- Live stability proof remains blocked by environment/provider instability: the
  tightened prompt eliminated the observed fabrication/provenance failures in the
  final completed model runs, but one A3 run had no live research sources and was
  correctly classified `BLOCKED_ENV`.
- If a future live run mutates tracked latest receipts, keep the per-run receipts and
  restore latest receipt churn by exact path before staging implementation changes.
