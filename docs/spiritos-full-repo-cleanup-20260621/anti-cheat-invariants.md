# Anti-Cheat Invariants — Operationalized

This restates the non-cheating constitution as concrete, checkable invariants
that every stage's acceptance contract and the F10 tailoring scan enforce. It is
normative: if any invariant is violated, the stage is NEEDS_FIX regardless of
test pass count.

## A. No benchmark tailoring
- **Invariant:** runtime/production code contains no branch keyed on
  `A1–A10`, `A2`/`A5`/`A9`, `Set A`, `4R*` trial labels, exact benchmark prompt
  wording, known expected answers, audit verdict wording, or fixture names.
- **Allowed:** A2/A5/A9 in docs/tests as historical regression references only.
- **Check (F10):** ripgrep runtime paths for these tokens in conditional context;
  any production branch → automatic NEEDS_FIX.

## B. No canned substance
- **Invariant:** no hardcoded final work products, research conclusions, model
  decisions, role assignments, API-escalation conclusions, expected
  recommendation text, source lists presented as live research, renderer-created
  substance, or benchmark answers.
- **Allowed:** a renderer may format already-validated model-produced fields. It
  may not decide or fill substantive fields.

## C. No stamped success
- **Forbidden:** default PASS, hardcoded `fake_go_detected=false`, manual
  `final_status` edits, manual JSON flipping, summary-only GO, route-exists-only
  GO, status-only GO, preview/advisory GO, mock/fixture GO, consumer-event-only
  GO, test-count-only GO, docs-only GO.
- **Invariant:** every positive verdict is derived from actual behavior +
  contract checks + raw evidence + required tests.

## D. No handholding
- **Invariant:** expected answers are not encoded into model prompts, evidence
  digests, validators, repair prompts, renderer templates, unit-test fixtures,
  comments, or task-specific branches.
- **Allowed:** prompts may specify schema, safety boundaries, required fields,
  and the user's actual goal — never the conclusion to reach.

## E. No scaffolding credit
- **Not implementation completion:** TODO-only modules, placeholder functions,
  pass-through no-op adapters, mocked worker success, synthetic provider
  success, fake receipts, static fixtures labeled live, compatibility wrappers
  with no real downstream consumer, test-only orchestration as runtime integration.
- **Temporary adapters allowed only if:** preserve behavior, have parity tests,
  explicitly labeled, have a retirement/review condition, never counted as new
  capability.

## F. No silent fallback
- **Invariant:** every fallback records primary path, primary failure class,
  fallback path, `fallback_used=true`, effect on final verdict, evidence ref.
- **Cannot prove primary success:** tree-sitter (≠ Headroom), repo context
  (≠ internet research), Dell (≠ Mac-required work), mock (≠ live), API
  (≠ local-first when local-first is required).

## G. No self-acceptance
- **Invariant:** GLM stage verdicts are `INTERNAL_GO_PENDING_SECONDARY_REVIEW`.
  Final acceptance requires independent Codex review + Britton + repair + merge
  authority. Terminal state is `READY_FOR_SECONDARY_REVIEW`.

## H. No moving goalposts
- **Invariant:** after a stage's acceptance-contract + holdout-manifest are
  frozen (hashed into status.json), they are not weakened. Required invariants,
  mandatory tests, negative cases, compatibility expectations, failure
  conditions, protected paths, holdout checks are immutable for that stage.
- **If frozen contract is materially wrong:** stop `BLOCKED_HUMAN`. Do not edit
  the contract to pass.

## I. No skipped-test success
- **Forbidden:** reporting a required test as PASS if it did not run, timed out,
  was skipped/deselected, used an unavailable dependency, or relied on fallback.
- **Report honestly:** PARTIAL / BLOCKED_ENV / NEEDS_FIX.
- **Carry rule:** pre-existing unrelated failures may be carried only if they
  existed in the frozen baseline, the cleanup didn't touch their dependency path,
  the exact failing command + baseline output are recorded, and they don't test
  the stage's required contract.

## J. No evidence fabrication
- **Invariant:** every reported command has exact command, start time, exit code,
  decisive output excerpt, raw evidence location, SHA-256 of raw evidence (when
  retained), and a conclusion derived from the command.
- **Forbidden:** summarizing a command not run; claiming raw evidence exists
  when the path doesn't.

## How stages enforce these
- Each `acceptance-contract.json` names the invariants the stage is responsible for.
- Each `holdout-manifest.json` defines generic unseen checks (not known examples).
- F2 is the independent detector layer; F10 is the terminal scan.
- `status.json` records invariant-gate results per stage.
