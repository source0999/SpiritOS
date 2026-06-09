# Source Proxy Context-Orchestrated Coding Acceptance Contract

Status: master-plan contract only. This file does not approve Plan 0 execution.

## Non-Negotiable Acceptance Rules

- No preview-only acceptance.
- No route-exists acceptance.
- No docs-only acceptance for integration.
- No silent source skipping.
- No Repomix-only full-context claim.
- No hidden worker execution.
- No hidden apply, commit, push, queue continuation, or background autonomy.
- No Coder 50 or Coder 100 until the basic A+ gauntlet passes.
- No 14B default switch until 14B passes the same output-contract tests as the 7B route.
- Every integrated context source must report `used`, `skipped`, or `blocked`.
- Every plan ends with GO/NO-GO and stops for Britton approval before the next plan.

## Readiness States

Preview means a route, UI, packet draft, demo, or local-only fixture exists but has not proven real execution-path integration.

Advisory means a subsystem can produce reviewable guidance, critique, proposed context, test findings, or handoff packets, but it does not mutate the repo and does not have authority to apply work.

Integrated means Source Proxy invokes the subsystem through the real `/coding` hot path, receives a task-specific packet or explicit skipped/blocked diagnostic, includes that status in the final coder packet, and writes a durable run receipt.

Production-ready means the integrated path is covered by tests, durable diagnostics, negative cases, operator-visible receipts, and no-hidden-mutation proof across the approved gauntlet.

## Coder Packet Required Fields

Every coder run must expose and receipt:

- original Britton prompt
- normalized task
- task intent
- selected target files
- allowed files
- forbidden files
- repo map/context source used
- dirty-tree status
- Cartographer packet status
- Obsidian packet status
- Scout/research packet status
- Design packet status
- helper/subagent packet status
- model route truth
- output contract version
- final compact coder prompt payload
- used/skipped/blocked diagnostics for each source

## Output Contract Required Behavior

The coder output parser must reject:

- markdown fence found
- unclosed file tag
- no file block
- malformed file block
- empty diff
- unsafe path
- out-of-scope file

Only one formatting repair pass is allowed. If the repaired output still fails, the run is NO-GO and no mutation may occur.

## Evidence Contract

Each increment must produce an evidence file containing:

- increment id and title
- command/check performed, or explicit reason no command was safe
- files inspected or changed
- result
- GO/NO-GO decision
- next permitted increment

Each phase must produce a phase closeout. Each plan must produce a plan closeout with a clear stop-for-Britton-approval gate.
