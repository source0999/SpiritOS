# GLM Plan 3 Set A — Hardline Stability Audit (2026-06-25)

Independent diagnostic audit. Audit-only. No source edits, no stage, no commit, no
push, no Set B/C, no Plan 4, no media/Jellyfin mutation. This report diagnoses why
Set A keeps returning NEEDS_FIX after many bounded patches and whether that is
cheating, overfitting, brittle harness logic, nondeterminism, or flawed contract
design.

## Executive verdict

There is **no cheating and no prompt-ID hack for A3**. The anti-cheat layer is real
and the 25-test suite (including explicit anti-branch guards) is green. The A3
flicker (isolated PASS, full-set NEEDS_FIX) is **not** a shared-state leak and **not**
a grader-mode difference. The grader is **fully deterministic** — proven by replaying
the exact captured A3 work product through `grade()` in isolation and reproducing the
identical `research_change_no_specific_decision` failure.

The real root cause is a **brittle decision-verb gate fed by a nondeterministic,
token-capped, under-prompted model lane**. A3 is routed to the *generic* path
(`ollama()`, `temperature=0.2`, `num_predict=3000`, no structured packet, no repair
loop for decision verbs), unlike A2/A5/A9 which get the hardened structured-packet
lane (`num_predict=9000`, JSON validation, repair prompts). On any given run the
model emits a different set of decision verbs; the verb regex only accepts ~5 of ~20
common decision verbs, so a single block whose verb is `Investigate`/`Leverage`/
`Adopt`/`Integrate`/… fails the whole prompt. Combined with a `num_predict=3000` cap
that truncates the work product mid-sentence on some runs, A3 is statistically
unstable by construction.

Codex is **patching brittle layers, not cheating**. But it is also **solving the
wrong layer**: it keeps tightening source provenance while the actual variance is in
(a) the narrow verb allow-list and (b) the cheap model lane assigned to A3. This will
not generalize to Set B/C.

Verdict: **MODEL_PROMPT_CONTRACT_REDESIGN_NEEDED** (harshest accurate option short
of a redesign-of-everything; the harness itself is salvageable, the model contract is
not).

## Baseline

- Repo path discovered: `Z:\` (task assumed `/home/source/SpiritOS`; that Linux path
  does not exist on this host — win32). Repo is at the working directory.
- branch: `integration/cleanup-plan3-debug-20260623` ✓ (matches required)
- HEAD: `3f6e38c0 docs: preserve cleanup explainability reviews` — newer than the
  stated `d9a01476`, but `d9a01476` ("Fix Plan 3 A3 source linkage") IS in history
  (one commit below HEAD). HEAD includes the A3 source-linkage patch. ✓
- dirty/staged state: **nothing staged**. Tracked modifications present are
  **pre-existing SpiritFlix/media changes** (commit `a4851c93`), not produced by this
  audit and not staged. One untracked 0-byte temp artifact `NDH6SA~M` (Windows 8.3
  name, present at session start) — not a source edit, not deleted per rules.
- No unexpected dirty *source* edits attributable to the audit.
- report: `docs/.../plan-03/glm-set-a-stability-hardline-audit-20260625.md` (this file)

## Commands run

```
git status --branch --short --untracked-files=normal
git rev-parse HEAD ; git log --oneline -24
git diff --cached --name-status   (nothing staged)
curl http://127.0.0.1:11434/api/tags                (ollama up; models listed)
curl http://127.0.0.1:11434/api/show  gemma3n:e4b    (NOT FOUND)
curl http://127.0.0.1:8080/search?q=android...      (search provider UP, real results)
PLAN3_STAGE4R_ONLY=A3 python3 .../_stage4r_runner.py            (default model)
PLAN3_STAGE4R_ONLY=A3 PLAN3_STAGE4R_MODEL=phi4-mini ...runner   (override attempt)
python3 -m pytest source_proxy/tests/test_plan3_stage4r_packet_runner.py -q   (25 passed)
# deterministic grader repro (see A3 isolated/full-run results)
git checkout -- docs/.../set-a-rerun/   (restored tracked evidence my runs overwrote; NOT staged)
```

Targeted scans (ripgrep) for `prompt_id ==`, `pid == "A.."`, `hardcoded`,
`fake.*source`, `fallback.*pass`, `mark.*PASS`, the two gate names — run over
`docs/.../plan-03` and `source_proxy`.

## Environment divergence (important caveat)

- Task assumed a Linux runtime at `/home/source/SpiritOS` with `.venv/bin/python` and
  a live `gemma3n:e4b`. On this audit host:
  - `/home/source/SpiritOS` does not exist; repo is `Z:\`.
  - `.venv` is a **Linux venv copied to win32** (`pyvenv.cfg home=/usr/bin`,
    `bin/python` missing). Not executable here. System `python3` (3.13) used instead;
    it imports the runner and all deps (`litellm`, `jsonschema`, `httpx`) fine.
  - **`gemma3n:e4b` is NOT installed** in local ollama → `model not found`. Available
    models: phi4-mini, qwen2.5-coder:14b/7b, dolphin-mistral, Spirit, dolphin-llama3,
    gpt-4o-mini, gpt-4o, llama3.1.
  - Even an override to `phi4-mini` returned **HTTP 500** on the full Plan 3 prompt
    (large prompt; local ollama cannot serve it reliably here).
- Therefore the model-generated work product **could not be reproduced live** on this
  host. The recorded evidence (A3.json/A3.md) was produced on the Linux box where
  `gemma3n:e4b` exists. To still answer the core audit question (is the isolated-vs-
  full difference a harness/grader artifact?), the **grader was replayed
  deterministically** on the exact captured work product (see below). This is stronger
  evidence than a live rerun because it removes the model as a variable.

## A3 isolated run results

Live A3-only runs on this host were **environment-blocked** (model missing → empty
output → `EMPTY_OUTPUT` / `work_product_too_short`), which is a *different* failure
mode than the Linux `research_change_no_specific_decision` and is **not** evidence
about the real flicker. Recorded here honestly, not used as the verdict basis:

- A3 isolated run 1 (default `gemma3n:e4b`): NEEDS_FIX, EMPTY_OUTPUT, model `not found`
- A3 isolated run 2 (`phi4-mini` override): NEEDS_FIX, EMPTY_OUTPUT, model HTTP 500
- A3 isolated run 3: not separately run; env-block is deterministic (model layer dead)

**Deterministic grader repro (the real isolated test).** Replayed the exact A3 work
product captured in `A3.md` (Work Product section) through `repair_research_change_fields`
+ `grade()` in isolation — no other prompts, no shared state, one process, one call:

- `final_status = NEEDS_FIX`
- `failed_gates = ['research_change_no_specific_decision']`
- 5 of 6 research-change blocks are GOOD; exactly ONE block fails — the block whose
  `Decision changed:` starts with **"Investigate"**, which is not in the allowed
  decision-verb regex.
- Grader run 5× on identical input → **identical result every time** (deterministic).

This **reproduces the full-set A3 failure in isolation**, proving the failure is not
caused by full-set execution, shared state, or run mode.

## Full Set A run results

Full Set A live runs were not reproducible on this host (same model env-block). The
latest committed full-set summary (`summary.json`, generated `2026-06-25T00:20:04Z`)
shows the real Linux result:

- full Set A run 1 (committed evidence): pass_count=9, failed_count=1, A3 NEEDS_FIX
  `research_change_no_specific_decision`. A1,A2,A4–A10 PASS.
- full Set A run 2: not re-run on this host (env-blocked); prior docs record the same
  A3 NEEDS_FIX with the source-linkage fix already applied.

## Isolated vs full-run diff

- isolated vs full difference: **NONE at the grader/harness level.** The deterministic
  isolated replay reproduces the full-set failure exactly. The *only* thing that
  differs between an A3-only PASS and a full-set A3 FAIL is the **model's emitted
  text** on that particular run.
- selected lane/model/provider: `ollama_default` / `gemma3n:e4b` / `ollama` — identical
  in isolated and full runs (A3 is always the generic `ollama()` lane; never the
  structured-packet lane).
- raw source count: 6, stable (research layer is deterministic and works; search
  provider returns the same Android sources).
- model body stability: **UNSTABLE** — `temperature=0.2` on the A3 lane means the
  decision verbs and prose differ run-to-run. The A3-only PASS run emitted only
  allowed verbs; the full-set run emitted an "Investigate" block.
- code-owned shell stability: the `repair_research_change_fields` pass is deterministic
  and stable; it canonicalizes sources but does **not** repair decision verbs.
- grader stability: **fully deterministic** (proven). No mode dependence.
- suspected root cause: **MODEL_NONDETERMINISM** (primary) +
  **PROMPT_TEMPLATE_TOO_WEAK / brittle verb gate** (the gate that makes the
  nondeterminism fatal) + **MODEL_BODY_TOO_THIN** (`num_predict=3000` truncation).

## Cheating / overfit scan

Classification of every suspicious pattern found:

- `prompt_specific_failed_gates` has `if pid == "A2"` / `elif pid == "A5"` /
  `elif pid == "A9"` (runner lines 612/624/637); `grade()` has
  `required_material_blocks = 3 if pid in {"A2","A5","A9"} else 2` (1965);
  `POLICY_REQUIRED = {"A2","A6"}` (66); `prompt_specific_guidance` branches A2/A5/A9
  (1898+); `RESEARCH_QUERIES`/`REPO_SURFACES` keyed by pid; `PACKET_CONTRACTS` for
  A2/A5/A9 only; main loop routes only A2/A5/A9 to the structured-packet lane.
  → **Classification: EXPECTED_RUNNER_SELECTION / LIKELY_OVERFIT (deliberate).** These
  are real, declared benchmark-specific gates, not hidden. They are **not** tested as
  cheating by the suite. They are defensible as "per-prompt rubric" but they are
  benchmark-tailored by construction and will not transfer verbatim to Set B/C.
- **A3 has NONE of these branches.** A3 has no prompt-specific gate, no guidance, no
  contract, no structured packet, no query variant. A3 rides the generic lane. This is
  the core design gap.
- `test_research_change_repair_has_no_prompt_specific_branches` asserts
  `'pid == "A3"' not in source` and `'"A3"' not in source` for
  `repair_research_change_fields`; `test_packet_assembler_has_no_prompt_specific_branches`
  asserts no A2/A5/A9 branch in `assemble_code_owned_decision_packet`.
  → **Classification: BENIGN_TEST_FIXTURE / anti-cheat guard (good).** These actively
  prevent A3-specific hacks in the two code-owned functions. Real defense, not theater.
- Production `source_proxy` scan: `allow_fallback_to_pass: False`, trial-mode blocks
  deterministic scaffolds, anti-cheat detectors present.
  → **Classification: BENIGN / anti-cheat.** No hardcoded PASS/GO, no fake URLs, no
  silent fallbacks, no swallowed-exception→GO in production paths.
- No `if prompt_id == "A3"`, no hardcoded PASS, no fake source URLs, no model-authored
  refs copied into provenance, no "best effort"→PASS anywhere in the A3 path.

- prompt-ID branches: present for A2/A5/A9/A6 only (declared rubric); **absent for A3**.
- fake fallback/pass behavior: none found.
- benchmark tailoring: present and declared (A2/A5/A9 rubrics, query variants,
  contracts). Not hidden. Not applied to A3.
- hidden acceptance weakening: none — `fake_go_detected` is computed and the grader
  remains strict after every repair pass.
- **verdict: NO_CHEAT.** No A3 hack, no hidden PASS, no fabricated provenance. The
  work is honest but the A3 lane is under-engineered relative to A2/A5/A9.

## Harness quality assessment

- Is this a real harness? **Mostly yes.** It does live research, real repo reads,
  real model calls, real consumer/trace recording, and a real deterministic grader
  with anti-cheat. It is not a mock. The 25-test suite passes.
- Is the grader stable? **Yes, deterministic** (proven 5× identical). But
  *deterministic ≠ correct*: the decision-verb allow-list is too narrow to be a fair
  contract (see Missing gaps).
- per-prompt state isolation: **GOOD.** Each prompt gets its own `task_id`, `trace_id`,
  research bundle, repo read, and grader call inside the loop. No accumulator leaks
  across prompts. Variables (`work`, `grd`, `research`, `repo`, `mac`) are reset per
  iteration. The flicker is NOT a state leak.
- source registry isolation: **GOOD.** `source_facts` is derived per-call from the
  per-prompt `research` bundle; not a shared global.
- receipt freshness: **GOOD per-prompt**, but the runner **overwrites tracked
  receipts in place** (`A3.json`, `summary.json`, preflight `.md`). On this audit,
  live runs overwrote the real A3 evidence with env-fail output; restored via
  `git checkout` (not staged). In-place overwrite of canonical evidence is a
  fragility: there is no per-run timestamped receipt, so a failed rerun silently
  destroys the prior evidence.
- grader consistency: **GOOD** (deterministic, mode-independent).
- Set B/C generalization risk: **HIGH.** The A2/A5/A9 rubrics, query variants, and
  contracts are hand-written for those exact prompts. A3 (and any new prompt) get the
  generic lane, which is statistically unstable. Set B/C prompts would each need their
  own rubric or they will flicker like A3.

## Missing gaps Codex is not seeing

1. **The decision-verb allow-list is the actual gate, and it is far too narrow.**
   `specific_decision_verb_present` matches only
   `add|avoid|choose|consider|defer|design|evaluate|examine|explore|focus|implement|
   include|limit|narrow|narrowed|prefer|prioritize|reject|route|select|split|use|utilize`.
   Of 20 common decision verbs a planner emits, only ~5 pass
   (`use/utilize/consider/implement/explore`). `Investigate, Leverage, Adopt, Build,
   Recommend, Deploy, Integrate, Define, Test, Validate, Review, Assess, Plan,
   Determine` all FAIL. A single failing block fails the whole prompt. This is the
   direct, proven cause of the A3 NEEDS_FIX and the isolated/full flicker. Codex has
   been patching *source provenance*; the variance is in *decision-verb vocabulary*.

2. **A3 is on the wrong lane.** A2/A5/A9 get the structured decision-packet path
   (JSON, `num_predict=9000`, validation + repair loop, deterministic renderer).
   A3 (and A1/A4/A6/A7/A8/A10) get the raw `ollama()` path with
   `temperature=0.2`, `num_predict=3000`, and no decision-verb repair. The 3000-token
   cap is tight for Recommendation + 6 four-line research blocks + Plan/Limits/Handoff;
   the recorded `work_product_summary` is **truncated mid-sentence**
   ("...Research-to-decision changes: Finding:"), evidence of truncation. A3 is
   structurally set up to flicker.

3. **No nondeterminism budget / no deterministic receipt.** The runner uses nonzero
   temperature and overwrites the single canonical receipt in place. There is no
   mechanism to detect "same prompt, different verdict across runs" as a harness
   signal, and no timestamped per-run artifact. So a flaky A3 looks like "needs another
   bounded fix" instead of "this gate is unstable by construction." Codex is chasing a
   moving target it cannot see stabilize.

(Bonus) In-place overwrite of tracked evidence means any rerun silently destroys prior
evidence; the audit had to `git checkout` the real A3.json back. Receipts should be
append-only / per-run-id.

## Is Codex cheating or patching brittle layers?

**Patching brittle layers, not cheating.** Honest intent throughout: real research,
real model calls, real grader, computed `fake_go_detected`, declared rubrics, and
active anti-branch tests for the code-owned functions. But it is **patching the wrong
layer**: it keeps tightening source-linkage while the actual A3 variance lives in (a)
a too-narrow verb allow-list and (b) an under-provisioned model lane. It is also
overfitting effort onto A2/A5/A9 (structured packet, contracts, query variants) while
A3 — the failing prompt — gets none of that machinery.

## Root cause classification

Primary: **MODEL_NONDETERMINISM** (`temperature=0.2` on the A3 lane → different
decision verbs per run).
Secondary: **PROMPT_TEMPLATE_TOO_WEAK** (the verb allow-list accepts only ~5 of ~20
common decision verbs; one miss fails the prompt).
Tertiary: **MODEL_BODY_TOO_THIN** (`num_predict=3000` truncates the work product).
Design: A3 is routed to the generic lane and lacks the structured-packet + repair
machinery that stabilizes A2/A5/A9.
Explicitly NOT the cause: RUNNER_SHARED_STATE_LEAK, RECEIPT_STALENESS,
SOURCE_REGISTRY_ORDER_DEPENDENCE, PARSER_CONTEXT_ORDER_DEPENDENCE,
GRADER_MODE_DIFFERENCE, CHEATING_DETECTED (all disproven).

## Recommended next action

- exact action: **Do not patch source provenance again.** Redesign the A3 (generic)
  model contract: (1) widen `specific_decision_verb_present` to a real decision-verb
  vocabulary (or replace the allow-list with a "is this a concrete actionable
  decision" check that does not hinge on an exact verb), and (2) move A3 onto the same
  structured-packet + repair lane as A2/A5/A9 (or raise `num_predict`, drop
  temperature toward 0, and add a decision-verb repair pass). Add a nondeterminism
  budget: run each prompt N times and require a stable verdict, and make receipts
  per-run-id / append-only so reruns stop destroying evidence.
- patch allowed (after human approval): the decision-verb vocabulary and A3 lane
  assignment are general-contract fixes, not A3-specific hacks. They must be validated
  by the existing anti-branch tests (no `pid == "A3"` etc.) and by a stability re-run,
  not by a single A3-only PASS.
- patch forbidden: any `if pid == "A3"` branch; widening the verb list *only* enough to
  pass the current captured output; lowering the materiality bar; silently flipping
  NEEDS_FIX→PASS; deleting/overwriting prior receipts.
- human decision needed: confirm whether the verb allow-list should be a vocabulary
  list (and owned/maintained) or replaced by a semantic "concrete decision" check;
  confirm Set B/C will each get a declared rubric or share a general contract.

## Do not patch yet

This was audit-only. No source was edited, nothing staged, nothing committed. Tracked
evidence overwritten by env-blocked live runs was restored via `git checkout`. Await
human direction before any contract change.
