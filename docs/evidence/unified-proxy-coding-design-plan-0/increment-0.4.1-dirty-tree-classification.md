# Increment 0.4.1: Classify Dirty Files As Owned/Unowned/Unknown Without Edits

PLAN: Plan 0, Isolated Proxy Lane Baseline

PHASE: Phase 0.4, Dirty-Tree Classification Without Cleanup

INCREMENT: Increment 0.4.1, Classify Dirty Files As Owned/Unowned/Unknown Without Edits

Objective:
Classify the current dirty tree without editing, cleaning, stashing, resetting, checking out, staging, committing, or pushing.

Isolated proxy lane scope:
unified-proxy-coding-design-plan-0

Allowed files or file zones:
- Read-only git status and diff inspection.
- Evidence files inside /home/source/SpiritOS/docs/evidence/unified-proxy-coding-design-plan-0/

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
- Captured read-only status and diff output.
- Classified dirty files by ownership category.

Required tests or inspections:
```text
$ git -C /home/source/SpiritOS status --short
?? docs/evidence/
?? docs/spirit-os-unified-proxy-coding-design-system-master-plan-of-plans-v0.1.md

$ git -C /home/source/SpiritOS diff --name-only
<no output>

$ git -C /home/source/SpiritOS ls-files --others --exclude-standard docs/evidence/unified-proxy-coding-design-plan-0
docs/evidence/unified-proxy-coding-design-plan-0/increment-0.1.2-main-repo-and-forbidden-shared-state-paths.md
docs/evidence/unified-proxy-coding-design-plan-0/increment-0.2.1-read-only-git-status-snapshot.md
docs/evidence/unified-proxy-coding-design-plan-0/increment-0.2.2-diff-summary.md
docs/evidence/unified-proxy-coding-design-plan-0/increment-0.3.1-active-cartographer-soak-locations.md
docs/evidence/unified-proxy-coding-design-plan-0/increment-0.3.2-cartographer-soak-forbidden-declaration.md
```

Dirty-tree classification:
- Owned: /home/source/SpiritOS/docs/evidence/unified-proxy-coding-design-plan-0/
- Unowned/preserved: /home/source/SpiritOS/docs/spirit-os-unified-proxy-coding-design-system-master-plan-of-plans-v0.1.md
- Unknown: none observed.
- Tracked production diffs: none observed.

Required manual validation:
- Dirty entries are limited to authorized evidence artifacts plus the untracked source-of-truth plan file.
- The source-of-truth plan file is explicitly allowed for read-only reference and was not edited.
- No cleanup was performed.
- No unowned dirty file was mutated.

Required evidence artifact:
This file.

Stop conditions:
- Any unowned or unknown file requires edits.
- Any production tracked diff appears and cannot be classified.
- Any cleanup operation would be needed.

Rollback or recovery note:
No rollback action is authorized. If an unexpected dirty file appears, classify it without cleanup and stop if ownership is unclear.

GO / NO-GO exit rule:
GO only if dirty files are classified without cleanup and no forbidden paths were touched.

GO / NO-GO:
GO for Increment 0.4.1.

Next authorized increment only:
Plan 0, Phase 0.5, Increment 0.5.1: Produce Allowed Path Matrix For Proxy/Design/Coding Work.

Cartographer soak dependency status:
SAFE WHILE SOAK RUNS.
