# Increment 0.6.2: Define Evidence Packet Naming Convention

PLAN: Plan 0, Isolated Proxy Lane Baseline

PHASE: Phase 0.6, Test Sandbox And Evidence Directory Definition

INCREMENT: Increment 0.6.2, Define Evidence Packet Naming Convention

Objective:
Define a consistent evidence packet naming convention for the isolated proxy lane.

Isolated proxy lane scope:
unified-proxy-coding-design-plan-0

Allowed files or file zones:
- Evidence files inside /home/source/SpiritOS/docs/evidence/unified-proxy-coding-design-plan-0/
- Read-only inspection only when needed.

Forbidden files, paths, systems, and actions:
- Production source files.
- Source Proxy runtime files.
- Cartographer runtime files.
- Cartographer soak logs.
- Scout soak logs.
- Cartographer live evidence.
- Map state.
- Git mutations, including branch, worktree, stash, reset, clean, checkout, stage, commit, and push.
- Provider/model calls.
- Apply or execute-approved routes.
- Background worker or queue mutation.

Exact work performed:
- Defined a packet naming convention for increment evidence, phase closeouts, and plan closeout.
- Did not rename existing evidence files.
- Did not write outside the evidence root.

Required tests or inspections:
- Manual review of existing evidence filenames in the evidence root.

Evidence packet naming convention:
- Increment packet: `increment-<phase>.<increment>-<kebab-title>.md`
- Phase closeout packet: `phase-<phase>-closeout.md`
- Plan closeout packet: `plan-0-closeout.md`
- Verification notes, if needed: `verification-<scope>-<kebab-title>.md`

Applied Plan 0 examples:
- `increment-0.6.2-evidence-packet-naming-convention.md`
- `phase-0.6-closeout.md`
- `plan-0-closeout.md`

Naming constraints:
- Use lowercase kebab-case after the numeric increment identifier.
- Keep the numeric plan/phase/increment in the filename.
- Keep all evidence files inside /home/source/SpiritOS/docs/evidence/unified-proxy-coding-design-plan-0/
- Do not rename or move files without explicit authorization.

Required manual validation:
- Convention is specific.
- Convention keeps evidence isolated inside the lane root.
- Convention does not authorize edits outside the evidence root.

Required evidence artifact:
This file.

Stop conditions:
- Any need to rename, move, or delete existing files.
- Any evidence path outside the authorized root.
- Any ambiguity in naming that could collide with runtime/shared state.

Rollback or recovery note:
No rollback action is authorized. If a naming conflict appears, create a new clearly named evidence file inside the evidence root only.

GO / NO-GO exit rule:
GO only if naming convention is explicit and all evidence remains inside the isolated evidence root.

GO / NO-GO:
GO for Increment 0.6.2.

Next authorized increment only:
Plan 0, Phase 0.7, Increment 0.7.1: Define Rollback Without Stash/Reset/Clean/Checkout.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.
