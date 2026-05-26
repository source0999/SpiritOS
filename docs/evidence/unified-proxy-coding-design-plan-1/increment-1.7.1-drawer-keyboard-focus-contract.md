# Increment 1.7.1: Define Keyboard/Focus Behavior For Drawers

PLAN:
Plan 1, Unified Coding + Design Foundation Architecture.

PHASE:
Phase 1.7, Accessibility and responsive baseline.

INCREMENT:
Increment 1.7.1, Define keyboard/focus behavior for drawers.

Objective:
Define WAI-ARIA-style drawer behavior without code changes.

Isolated proxy lane scope:
Accessibility contract evidence only.

Allowed files or file zones:
Plan 1 evidence files only.

Forbidden files, paths, systems, and actions:
Code changes, CSS changes, provider calls, apply, execute-approved, Cartographer writes, queues, hidden workers, and git mutation.

Exact work performed:
- Defined drawer behavior: labelled dialog/drawer, focus moves into drawer on open, Tab/Shift+Tab stay inside while modal, Escape closes, close button is always reachable, focus returns to trigger, scroll lock is explicit, reduced motion honored.
- Defined future checks: keyboard open/close, focus restore, screen-reader label, no hidden authority buttons.

Required tests/checks:
Future manual/test checklist review.

Manual validation performed by Codex:
Behavior is testable and does not require implementation in Plan 1.

Evidence artifact:
This file.

Stop conditions checked:
Behavior vague: no.

Rollback or recovery note:
Refine contract before implementation if drawer mode changes.

GO/NO-GO exit:
GO for Increment 1.7.1.

Next authorized increment only:
Plan 1, Phase 1.7, Increment 1.7.2.

Cartographer soak dependency status:
NOT DEPENDENT ON SOAK.
