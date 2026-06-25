# Generic Model Contract Redesign Plan - 2026-06-25

## Scope

- Branch: `integration/cleanup-plan3-debug-20260623`
- Starting HEAD: `3f6e38c01a09f67f3ce41d084fe3962ab10619ff`
- This is a **general contract fix** for research/planning prompts in the Plan 3
  Stage 4R Set A dry-run runner. It is **not an A3-only fix**.
- No Set B/C, no Plan 4, no push, no API/frontier calls, no RouteLLM.

## What GLM proved (hardline audit)

The GLM hardline audit (`glm-set-a-stability-hardline-audit-20260625.md`) proved,
deterministically, that:

1. The A3 isolated-PASS / full-set-NEEDS_FIX flicker is **not** a shared-state leak
   and **not** a grader-mode difference. Replaying the exact captured A3 work product
   through `grade()` in isolation reproduced the identical
   `research_change_no_specific_decision` failure. The grader is deterministic.
2. The actual failing gate is `specific_decision_verb_present`, whose regex accepts
   only ~5 of ~20 common concrete planning verbs. One block whose decision began with
   `Investigate` failed the whole prompt. Other common verbs that fail the current
   regex: `Leverage, Adopt, Build, Recommend, Deploy, Integrate, Define, Test,
   Validate, Review, Assess, Plan, Determine`.
3. A3 rides the weak generic `ollama()` lane (`temperature=0.2`, `num_predict=3000`,
   no structured packet, no decision-verb repair), unlike A2/A5/A9 which get the
   structured decision-packet lane (`num_predict=9000`, JSON validation, repair loop).
4. The work product is truncated mid-sentence on some runs (`num_predict=3000` is
   tight for Recommendation + N research-to-decision blocks + Plan/Limits/Handoff).
5. There is no nondeterminism budget and receipts are overwritten in place, so a flaky
   prompt looks like "needs another bounded fix" instead of "this contract is unstable."

## What Codex had been patching incorrectly

Codex kept tightening **source provenance** (canonicalizing source refs, dropping
non-raw-source blocks) across `836d8707`, `d1edd343`, `0296415d`, `d9a01476`. That work
was honest and real, but it addressed the `research_change_source_not_from_raw_sources`
gate, **not** the `research_change_no_specific_decision` gate that is now the actual
blocker. The variance lives in (a) the narrow verb allow-list and (b) the cheap model
lane assigned to research/planning prompts that are not A2/A5/A9.

## Why A3 flickers

- `temperature=0.2` on the A3 lane => the model emits a different set of decision
  verbs on each run.
- The verb allow-list rejects most concrete decision verbs, so whether A3 passes
  depends on whether the sampled verbs happen to be in the tiny allow-list.
- `num_predict=3000` can truncate the required sections, producing thin/empty output
  on some runs.
- A3 has no decision-verb repair pass (only source-ref canonicalization).

## What general layer will be fixed

Four general, prompt-shape-routed components. **None route by `pid == "A3"` or any
prompt id.**

### 1. Decision-verb contract (general)

Replace the brittle regex with a **maintained vocabulary** of concrete planning verbs
PLUS a **semantic vagueness guard**. A decision line passes only if it contains a
concrete decision verb AND is not a vague restatement.

- Vocabulary (Option A, expanded, maintained): `use, utilize, implement, build, adopt,
  integrate, select, choose, route, prefer, prioritize, avoid, reject, defer,
  investigate, evaluate, assess, validate, test, review, recommend, define, design,
  explore, examine, split, narrow, limit, include, focus, determine, compare,
  prototype, start, continue, stop, add, leverage, deploy`.
- Vagueness guard (Option B layer): reject lines whose substantive content is only
  vague phrases such as `think about`, `maybe`, `stuff`, `do things`, `look into`,
  `consider it`, `various`, `etc`, or that merely restate the finding without a
  decision.
- **Still strict:** a vague/non-decision block still fails. This is not a PASS
  rubber-stamp. The bar is "concrete actionable decision tied to a source," not "any
  verb."

### 2. Generic stabilized lane for research/planning prompts (general)

Route by **task shape**, not prompt id: any prompt with `internet_likely_required`
(research needed) that is **not** already on the A2/A5/A9 structured decision-packet
lane will use a **stabilized generic generation lane** with:

- near-deterministic sampling for dry-run validation (low temperature),
- a `num_predict` large enough to avoid truncating required sections,
- a **general decision-verb repair pass** that, on a `research_change_no_specific_decision`
  grade, asks the model to rewrite vague decision lines with concrete verbs (mirrors
  the existing source-ref repair, but for decision verbs),
- local-first: still local ollama only, no API/frontier call, no RouteLLM.

This is keyed on `item["internet_likely_required"]`, so Set B/C research prompts get
the same stabilization automatically.

### 3. Nondeterminism budget (general)

A stability runner that runs a prompt N times (default 3 for a flaky prompt, 2 for a
full set) and records every verdict. If verdicts differ, it classifies the prompt as
`MODEL_NONDETERMINISM` / `UNSTABLE_MODEL_CONTRACT` and surfaces it — it does **not**
flip a NEEDS_FIX to PASS. A single PASS after a prior flicker is not sufficient.

### 4. Append-only / per-run-id receipts (general)

Diagnostic/stability runs write per-run-id evidence under
`docs/.../set-a-rerun/runs/<run_id>/`. The canonical latest receipts may be refreshed
but only with a per-run copy preserved. This stops reruns from silently destroying
prior evidence (the audit had to `git checkout` the real A3.json back after a live
run overwrote it).

## How this avoids A3-specific hacking

- No `if pid == "A3"`, no `elif pid == ...` for the new logic.
- The verb vocabulary is a general planning vocabulary, not tuned to A3's current
  output (it also accepts verbs A3 never used).
- The stabilized lane is selected by `internet_likely_required` (task shape), so A1,
  A4, A6, A9 and any future research prompt benefit identically.
- The existing anti-branch tests (`test_research_change_repair_has_no_prompt_specific_branches`,
  `test_packet_assembler_has_no_prompt_specific_branches`) remain green, and new tests
  assert the new functions also contain no prompt-id branches.

## What tests will prove generalization

- Decision verbs accepted: `investigate, adopt, integrate, build, recommend, validate,
  assess, test, leverage, deploy, determine` (verbs that previously failed).
- Vague non-decisions still fail: `think about it`, `maybe consider`, `do things`,
  `stuff`, empty restatement.
- The verb check and the new lane selector contain **no** `pid ==` / `"A3"` branches
  (anti-overfit assertion via `inspect.getsource`).
- A research/planning task **shape** (internet_required) selects the stabilized lane;
  a non-research shape does not.
- `num_predict`/temperature contract is surfaced in lane metadata.
- Per-run receipts include `run_id`; a rerun does not destroy the only prior copy.
- Nondeterminism classification is produced and surfaced when verdicts differ.
- Fake GO still fails; fake/model-owned source URLs still fail/stripped (existing
  anti-cheat tests stay green and are extended).

## Out of scope

- No source-provenance weakening. The strict `research_change_source_not_from_raw_sources`
  gate stays.
- No materiality bar lowering. `required_material_blocks` stays at 2/3.
- No Set B/C execution.
- No Plan 4.
- No push/merge.
