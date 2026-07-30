# Gate 2-J.9A Authorization Correction

status: `CORRECTION_PLAN_PROSPECTIVE_REVALIDATION_AUTHORIZATION_ISSUED`

schema: `source-proxy.gate-2j-9a-authorization-correction/v1`

This note records the corrective plan triggered by `GATE_2J_9A_AUTHORIZATION_SEQUENCE_AUDIT.md`.

## What was wrong

The original Gate 2-J.9A authorization (`TERRA_HIGH_AUTHORIZED__GATE_2J_9A`,
content_sha256 `defad82047ade26d...`) was bound and hashed AFTER the implementation it
authorized was committed. It is `RETROACTIVE_AUTHORIZATION_BINDING`, not prospective.

## What is preserved

- Original implementation commits (`e8bebd9fc` and its receipts). No rewrite, squash, amend,
  or force-push.
- The original authorization artifact is marked SUPERSEDED (not deleted) and linked to its
  replacement.

## Corrective sequence (prospective)

```text
1. Audit + correction note + prospective revalidation authorization + manifest  (this set)
2. Canonicalize and hash the revalidation authorization (excluding hash + artifact_commit fields)
3. Commit the authorization set to the qualification branch  (Commit 1)
4. Push Commit 1 to origin  (authorization exists remotely BEFORE revalidation)
5. Create a clean isolated worktree from the authorization commit
6. Verify authorization hash + base; verify clean status
7. ONLY THEN run the revalidation suite
8. Produce the revalidation receipt (Commit 2), which descends from Commit 1
```

The revalidation authorization commit MUST be an ancestor of the revalidation receipt commit.
No revalidation command runs before the authorization commit exists.

## Scope of revalidation

Revalidation inspects and tests the EXISTING implementation; it does not execute JCode, call a
model, modify the benchmark or daily runtime, or implement Gate 2-J.9B. Policy corrections
(context policy: one canonical context for all four lanes; budget policy: split into
gate-specific profiles) are explicit allowed scope of this authorization because they are
documentation/policy corrections, not JCode execution and not Gate 2-J.9B.

## Outcome handling

- If all checks pass: `GATE_2J_9A_REVALIDATION_PASS`.
- If a substantive implementation fix is required: `GATE_2J_9A_REVALIDATION_BLOCKED_IMPLEMENTATION_FIX_REQUIRED`,
  stop, propose the smallest amendment, do not modify implementation under this authorization.
