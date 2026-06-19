# Design

## Productive GO Meaning

`productive_go=true` now means a real FIP4 coder action produced file/action evidence and a real verifier proved behavior. Structural evidence alone is not productive.

## Productive Evidence

The receipt emits `productive_evidence` booleans for:

- `file_written`
- `action_applied`
- `browser_behavior_verified`
- `real_browser_used`
- `interactive_behavior_checked`
- `functional_behavior_verified`
- `deterministic_verified`
- `verification_real`
- `protected_path_clear`
- `degraded_lanes_clear`

`action_applied` means the FIP4 action output was accepted into the receipt truth path with changed files, not that this live repository was mutated.

## Status Mapping

- `GO`: all productive requirements pass.
- `NO_GO`: final verdict is non-GO, protected path is blocked, browser truth says `NO_GO`, or deterministic verification failed.
- `BLOCKED`: required lane degradation or browser truth says `BLOCKED`.
- `UNSUPPORTED`: browser truth says `UNSUPPORTED` and no functional verifier supplies real behavior.
- `SKIPPED`: browser truth says `SKIPPED` and no functional verifier supplies real behavior.
- `PARTIAL_GO`: structural/file/action evidence exists, but real behavior verification is missing or partial.

Functional verifier truth can still satisfy behavior proof for non-browser targets. Browser verifier proof requires the structured browser truth object from the previous patch.

## Scope Avoidance

No browser verifier implementation changes are made here. This patch only consumes existing browser verifier fields in the receipt productive truth gate.
