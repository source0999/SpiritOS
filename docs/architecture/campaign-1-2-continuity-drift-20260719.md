# Campaign 1/2 external SpiritFlix continuity-drift report — 2026-07-19

## Result

`BLOCKED_HISTORICAL_CONTINUITY_DIVERGENCE`

No validator was changed. The exact-equality failures are not benign forward
drift: the observed external `master` is an ancestor of the historical
SpiritFlix baseline, rather than a descendant. The external object database
also fails strict `git fsck` because of a pack checksum/CRC failure. The dirty
external checkout was read only.

## Shared SpiritFlix evidence

- Repository identity: `/home/source/SpiritOS/.git` (read through `--git-dir`,
  never through the dirty worktree).
- Historical protected commit: `5fde4ae064d471e1133e00d6bf25fb5aecb5d196`.
  It resolves as a commit; its tree `2ef5f8f3bb7f0a4b6e105ffbf86cca68104c0ec8`
  and parent `2656fb91782bf088363aabf4309f811794e8af2a` are readable.
- Immutable retention: `refs/heads/codex/spiritflix-smart-scan-identity-fix`
  and multiple campaign tags still contain the historical commit.
- Observed live ref: `refs/heads/master` at
  `85dee8b59cce39afe1fbe7d674c066ccca1e6f13`.
- Relation: `master` **is** an ancestor of the protected commit; the protected
  commit is **not** an ancestor of `master`. There are 168 commits from master
  to the historical protected baseline. This is a backwards/divergent live
  relation, not permissible forward movement.
- Tree comparison from live master to historical baseline: 1,107 additions,
  238 modifications, and 11 deletions across 1,356 paths (principally `docs`,
  `src`, `scripts`, and `source_proxy`). The original campaign records a broad
  protected-head constraint, not a narrower protected-path allowlist; no
  path-level waiver can establish continuity after the ancestry failure.
- Strict external `git fsck --no-reflogs --full --strict` failed with a pack
  checksum mismatch and index CRC/inflate error. Empty `master` reflog leaves
  the precise rewrite event unproven, but does not cure the failed relation.

## Campaign 1

- Validator: `scripts/validate-campaign-1-continuity.py`.
- Native command: `python3 scripts/validate-campaign-1-continuity.py` from
  `/home/source/SpiritOS-campaign-1-20260712`.
- Machine-readable expectation:
  `docs/architecture/campaign-1-state.json` → `protected_heads.spiritflix`.
- Existing rule: exact equality between that historical protected commit and
  the current `HEAD` of `/home/source/SpiritOS`.
- Original purpose: preserve the accepted SpiritFlix source-head binding and
  borrowed-worktree/product immutability baseline before campaign closeout.
- Failure: `protected_head_mismatch:spiritflix`; a valid historical snapshot
  cannot be treated as an exact equality constraint for a live branch, but the
  evidence above also prevents a safe conversion to a descendant relation.

## Campaign 2

- Validator: `scripts/validate-campaign-2-continuity.py`.
- Native command: `python3 scripts/validate-campaign-2-continuity.py` from
  `/home/source/SpiritOS-campaign-2-20260716`.
- Machine-readable expectation:
  `docs/architecture/campaign-2-state.json` → `protected_heads.spiritflix`.
- Existing rule: exact equality between that historical protected commit and
  the current `HEAD` of `/home/source/SpiritOS`.
- Original purpose: revalidate the Campaign 1 entry-condition protected heads
  before accepting Campaign 2's core coding-OS closeout.
- Failure: `protected_head_mismatch:spiritflix` for the same non-descendant
  live `master` and failed external integrity condition.

## Required human decision

Restore or identify an authoritative, integrity-verified SpiritFlix reference
that is a permitted descendant of `5fde4ae…`, then document the relation and
any protected-path policy in its owning repository. Do not update Campaign 1/2
validator semantics until that evidence exists. The Campaign 3.5 planning
transaction remains preserved but uncommitted.
