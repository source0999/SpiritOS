# Acceptance Criteria

## v0.2 success

- Final PASS requires behavior PASS when behavior is required.
- Runtime GO, preview existence, file creation, static DOM presence, or model self-report cannot become product PASS by themselves.
- Unverified behavior remains UNVERIFIED or FAIL according to scope; it cannot become PASS.
- Repair attempts are limited and counted.
- Repair only touches disposable generated artifact workspaces unless Britton separately approves production-file repair.
- Failed repair produces a handoff packet.
- Out-of-scope tasks produce a handoff packet instead of a fake local attempt.
- The local route cannot silently escalate to paid/API/Codex/high-usage execution.
- No Obsidian writes, git operations, hidden worker starts, or production source mutation occur without explicit approval.
- Known false positives remain at zero in final reporting.

## Required final verdict behavior

- PASS: required observable behavior was directly verified.
- FAIL: required behavior was tested or inspected and did not meet the contract.
- UNVERIFIED: the check was not run, unavailable, unsafe, or outside approved scope.
- NEEDS_FIX: route, worker, verifier, environment, or proof pipeline prevented judgment.
- BLOCKED: permission, dependency, or operator choice prevents progress.
- HANDOFF: local repair is exhausted, unsafe, out of scope, or needs stronger approved route.

## Target score goals

- Current baseline: about 4/11 useful PASS on the revamped diagnostic, unless stronger evidence later proves otherwise.
- v0.2 target: 7/11 or 8/11 useful PASS with a repair loop, without cheating.
- Stretch target: 9/11 if local repair works well.
- Required truth target: 0 known false positives.

## Anti-cheat rules

- Repair prompts may include observed failure and expected behavior.
- Repair prompts must not include a full hardcoded solution.
- Verification must use the same user prompt intent and behavior contract, not a benchmark answer key.
- The repaired artifact must pass the behavior probe after repair.
