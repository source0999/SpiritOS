# Coder Trial Recovery Mini-Plan

## Purpose

This mini-plan is a narrow recovery plan for the contaminated Coder trial harness results. It is only for:

1. Gate 1: contamination containment and fallback/scaffold ban in trial mode.
2. Gate 2: research comparison report and read-only Obsidian memory-context integration.

Prompt expectations, grading, individual dropdown runner work, controlled trial reruns, and broader hardening come later after the Gate 1 and Gate 2 reports are grounded in evidence.

The Coder 10 PASS result is invalid as model-ability evidence.

Diagnostic facts to preserve:

* suite_id: suite-mq4in5v9
* 10/10 PASS should not be trusted as true model ability.
* Proven model-generated rows: 0
* Proven known-scaffold rows: 5
* Contamination-risk rows: 5
* Known scaffold/fallback behavior existed for exact Coder 10 Agent Lab paths.
* provider_call_made=true does not prove the final diff came from the model.
* Successful rows did not preserve enough generation provenance.
* Trial runner must not count scaffold/fallback/backend-generated output as model ability.

## Non-negotiables

* No prompt expectations yet.
* No full hardening yet.
* No Coder 10 rerun yet.
* No Coder 25/50/100.
* No Designer trial revamp.
* No hidden fallback.
* No known scaffold.
* No deterministic stub.
* No backend-generated app page counted as PASS.
* No provider_call_made=true treated as proof of model ability.
* If the model fails, report honest NEEDS_FIX/INVALID with reason.
* Trial PASS requires proven model-authored output.
* Obsidian context must be read-only, optional, and disabled by default unless configured.

## Gate 1: Contamination containment and fallback ban

Goal: stop the trial runner from cheating. Identify every scaffold/fallback path and ban it from trial mode so future trial results are not trusted unless the model actually produced the code.

### Increment 1.1: Freeze repo state and contaminated-suite evidence

Checks:

* git status --short
* git diff --stat
* git branch --show-current
* Record suite-mq4in5v9 as invalid benchmark evidence.

Manual/self-check:

* Dirty tree listed.
* Existing unrelated work identified.
* No reset/stash/delete/clean.
* Contaminated suite facts recorded.

### Increment 1.2: Full fallback/scaffold ID map

Starting files to inspect:

* source_proxy/planning/bounded_create.py
* source_proxy/planning/architect.py
* source_proxy/tasks/long_running.py
* source_proxy/api/decision.py
* source_proxy/verification/diff.py
* src/lib/coding/reversible-trial-runner.ts
* src/components/coding/CodingCockpitShell.tsx
* durable run/store/types files
* tests touching coding regression, reversible runner, durable rows, UI diagnostics

Classify behavior:

* known scaffold
* generic scaffold
* deterministic stub
* parser repair
* model-output conversion
* backend-generated diff
* backend-generated page
* fallback after model failure

Manual/self-check:

* Every fallback has file, function, caller, and behavior.
* It says whether the path affects trial mode.
* It says whether the path affects normal task composer.
* It flags anything tailored to Coder 10 / Agent Lab.

### Increment 1.3: Ban fallback/scaffold in trial mode

Trial mode contract:

* allow_known_scaffold=false
* allow_generic_scaffold=false
* allow_deterministic_stub=false
* allow_backend_generated_page=false
* allow_fallback_to_pass=false
* require_model_authored_diff=true

Behavior:

* Do not delete useful future code unless clearly dead.
* Block fallback/scaffold from trial scoring/execution.
* If fallback would run in trial mode, the row becomes INVALID or NEEDS_FIX, not PASS.
* Suggested reasons:
  * INVALID: scaffold_blocked_in_trial_mode
  * NEEDS_FIX: model_failed_no_scaffold_allowed
  * NEEDS_FIX: model_malformed_output_no_backend_repair

Manual/self-check:

* Scaffold/fallback cannot produce PASS.
* Provider call + backend scaffold cannot produce PASS.
* Trial mode failure is honest.
* Normal task composer is not accidentally broken.

### Increment 1.4: Add provenance fields everywhere trial rows are stored/displayed

Required fields:

* generation_source
* diff_source
* model_output_classification
* raw_response_length
* raw_response_excerpt_safe
* scaffold_used
* scaffold_kind
* fallback_used
* fallback_kind
* parser_repair_used
* bounded_create_used
* known_scaffold_used
* generic_scaffold_used
* model_raw_diff_used
* generated_diff_by_backend
* trial_result_trust_status

Manual/self-check:

* Durable run rows include these fields.
* Receipts include these fields.
* Copied diagnostics include these fields.
* UI row details include these fields.
* Missing provenance cannot silently PASS.

### Increment 1.5: Tests for "no scaffold PASS"

Required tests:

* known scaffold cannot PASS
* generic scaffold cannot PASS
* deterministic stub cannot PASS
* fallback after model failure cannot PASS
* provider_call_made=true does not prove model ability
* missing provenance cannot PASS
* valid model-authored diff can still PASS

Manual/self-check:

* Tests prove scaffold/fallback is blocked in trial mode.
* Tests prove valid model-authored output still works.
* Coder 10 is not rerun.
* Expectations are not written.

### Gate 1 closeout

Required closeout fields:

* Fallback/scaffold locations found:
* Trial-mode ban contract:
* Files changed:
* Tests added:
* Tests run:
* Whether scaffold can still count as PASS:
* Whether suite-mq4in5v9 is marked invalid:
* Current git status:
* Proceed/Stop:

## Gate 2: Research comparison report + Obsidian memory-context integration

Goal: before writing expectations, compare useful behavior patterns from other coder/designer agent systems and add Obsidian as a read-only optional memory/context source for Source Proxy.

### Increment 2.1: Research comparison packet

Compare:

* Odysseus
* Aider
* OpenHands
* OpenCode
* SWE-agent / mini-swe-agent
* Cursor-like debugger workflows
* any other relevant open-source coder/designer agent references

Research categories:

* repo context gathering
* repo-map / file-map behavior
* memory/context injection
* model routing
* model recommendation
* diff generation
* tool-use loop
* test/check loop
* failure reporting
* clarification behavior
* designer screenshot critique
* rollback/revert workflow

Manual/self-check:

* Every reference has source/link/license notes.
* Separate "use concept" from "copy code."
* No copied code without explicit approval.
* Map each useful pattern to SpiritOS needs.
* No hardening changes yet.

### Increment 2.2: Obsidian integration discovery

Questions to answer:

* Where is Britton's Obsidian vault?
* Is it local on Dell, Windows-mounted, synced, or not available yet?
* Should integration be read-only first?
* What file types are allowed? .md only?
* What folders should be included/excluded?
* How should secrets/private notes be protected?
* How should notes be chunked/summarized?
* How should note context be cited in diagnostics?

Manual/self-check:

* If vault path is unknown, add config placeholder and report missing path.
* Do not scan the whole filesystem.
* Do not ingest secrets blindly.
* Propose/read-only first.

### Increment 2.3: Add Obsidian as read-only memory context source

Minimal optional config:

* OBSIDIAN_CONTEXT_ENABLED=false by default
* OBSIDIAN_VAULT_PATH=
* OBSIDIAN_INCLUDE_GLOBS=*.md
* OBSIDIAN_EXCLUDE_GLOBS=.obsidian/**, private/**, secrets/**, archive/**
* OBSIDIAN_MAX_NOTES=
* OBSIDIAN_MAX_CHARS_PER_NOTE=

Behavior:

* Read-only.
* Disabled by default until configured.
* Only used when explicitly requested by agent context builder.
* Does not write to Obsidian.
* Does not modify notes.
* Does not upload notes externally.

Manual/self-check:

* Disabled-by-default confirmed.
* Read-only confirmed.
* Missing vault path fails safely.
* Excluded folders are respected.

### Increment 2.4: Add context query path for Obsidian

The proxy should be able to answer: "Given this task, retrieve a small relevant set of Obsidian notes as context."

Output should include:

* note title/path
* safe excerpt
* why it matched
* char/token estimate
* whether it was used in prompt context

Manual/self-check:

* Query returns only small relevant context.
* It does not include excluded/private folders.
* It shows why notes were selected.
* It can be turned off.

### Increment 2.5: Add diagnostics for memory context

Trial/task diagnostics should show:

* obsidian_context_enabled
* obsidian_context_used
* obsidian_notes_considered
* obsidian_notes_selected
* obsidian_context_chars
* obsidian_context_paths

Manual/self-check:

* Diagnostics show whether Obsidian was used.
* If not used, it says why.
* No note content is copied into public diagnostics unless safe excerpt rules allow it.

### Gate 2 closeout

Required closeout fields:

* Research comparison report:
* Useful patterns to steal conceptually:
* Patterns rejected:
* Obsidian integration status:
* Obsidian config fields:
* Read-only safety status:
* Memory-context diagnostics:
* Tests run:
* Current git status:
* Recommended next gate:
* Manual approval needed before hardening:

## Stop condition after Gate 2

After Gate 2, stop.

Do not write hardening plan yet.
Do not write expectations yet.
Do not add dropdown runner yet.
Do not add grading yet.
Do not rerun Coder 10.

The likely future order is:

* Gate 3: hardening plan based on research + Obsidian context
* Gate 4: first 10 Coder expectations only
* Gate 5: individual prompt dropdown runner
* Gate 6: grading system
* Gate 7: controlled single-prompt runs, then Coder 10

But do not lock those future gates yet.

## Required final terminal verification block after Gate 2

Codex executing the plan must provide one pasteable terminal block after Gate 2 that checks all completed work so far, including:

* repo status
* fallback/scaffold ban tests
* provenance tests
* Obsidian context tests
* typecheck
* diff check
* HTTPS LAN health
* source proxy health
* fallback/scaffold grep audit
* final criteria reminder

Pasteable terminal block template:

```bash
cd /home/source/SpiritOS
set -euo pipefail

echo "=== repo status ==="
git status --short
git diff --stat

echo "=== trial contamination / scaffold ban tests ==="
npm run test -- src/lib/coding/__tests__/reversible-trial-runner.test.ts src/lib/coding/__tests__/durable-run-store.test.ts src/components/coding/__tests__/coding-cockpit-shell.test.tsx

echo "=== source proxy scaffold/fallback tests ==="
.venv-source-proxy/bin/python -m unittest source_proxy.tests.test_coding_regression_pack source_proxy.tests.test_verification_contracts source_proxy.tests.test_diff_verification

echo "=== obsidian context tests ==="
# Codex fills exact test paths after implementation

echo "=== typecheck ==="
npm run typecheck -- --pretty false

echo "=== diff check ==="
git diff --check

echo "=== HTTPS LAN health ==="
curl -k -I --max-time 10 https://localhost:3000/coding
curl -k -s --max-time 10 https://localhost:3000/v1/coding/runs/active | jq .
curl -k -s --max-time 10 https://localhost:3000/v1/coding/agent-lab-baseline | jq .

echo "=== source proxy health ==="
curl -k -s --max-time 10 https://localhost:8787/v1/self/status | jq .

echo "=== fallback/scaffold audit ==="
grep -RIn "KNOWN_PAGE_SCAFFOLDS\\|bounded_create\\|deterministic scaffold\\|fallback" source_proxy src | head -n 200 || true

echo "=== final criteria ==="
echo "Trial PASS requires proven model-authored output."
echo "Scaffold/fallback/provenance-missing rows must be INVALID or NEEDS_FIX."
echo "Obsidian context must be read-only, optional, and disabled by default unless configured."
```
