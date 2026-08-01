# JCODE_COMPATIBILITY_PROFILE.md

Profile for qualifying the pinned JCode binary for Gate 2-J.9T section K. JCode
readiness is defined INDEPENDENTLY from model readiness. JCode is NOT the only
permitted harness; the baseline harness is an independent qualification lane.

## Binary identity (proven)

- Path: `/home/source/.codex-audits/jcode-dell-remediation-20260727/approved-binary/jcode`
- SHA-256: `2c59d30eeebc6d21e0a8a9a3b90af0022e4b92a7f3e6075db082cd256b3f8ef6`
  (independently re-hashed in this review)
- Version: `jcode v0.58.51-dev (2444e7b6)`

## Required changes/wraps

1. **Conflicting system instructions.** Seal a project system prompt that
   removes commit/self-development/unavailable-tool/generic-workflow defaults.
   The default 2,004-char prompt says self-modify + commit by default while the
   sealed task forbids both.
2. **Project instruction loading.** Disable generic AGENTS/project instruction
   ingestion for sealed tasks.
3. **Default model contamination.** Carry exact model/digest binding through
   the request (no default-model substitution).
4. **Native-only parser.** Add the textual-tool adapter (section G).
5. **Textual-tool adapter.** Required — Qwen emits assistant-text JSON, not
   native `tool_calls`.
6. **Tool-result role mapping.** Map tool results to the role/name JCode
   expects.
7. **Session/memory disabling.** Already proven by fresh HOME/`JCODE_HOME`/
   overlay/session per run.
8. **Focused-test tool registration.** Section J (Task W cannot complete
   without it; JCode policy is `no command tool`).
9. **Task-finalization behavior.** Require a valid final answer (R) or scoped
   diff + passing focused test (W).

## Suitability decision

- Identity/containment suitable: YES.
- Model-profile suitable for Qwen 7B/14B: NO.
- Current outcome: `JCODE_TOOL_COMPATIBILITY_READY=false`,
  `PIPELINE_NOT_READY_FOR_COMPARISON`.
- Unblocked only when sub-gate 2-J.9T-H passes (corrected bridge + parser +
  loop + focused-test tool + sealed prompt) for both minimal and corrected
  packets, for both Qwen models where meaningful.
