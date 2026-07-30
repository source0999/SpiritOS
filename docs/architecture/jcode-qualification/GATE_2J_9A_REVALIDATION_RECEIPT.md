# Gate 2-J.9A Revalidation Receipt

status: `GATE_2J_9A_REVALIDATION_PASS`

schema: `source-proxy.gate-2j-9a-revalidation-receipt/v1`
authorization: `TERRA_HIGH_AUTHORIZED__GATE_2J_9A_REVALIDATION_V1`
authorization_content_sha256: `c299a8fcc30aadfd05031f4cd0730fd766c274d14368230c2acaf24447a09db1`
authorization_base_commit: `e77e3e62146fcb9b8f4cd499b48dccc6be05c95c`
authorization_artifact_commit: `591d18e34a7416999f391209c7f88f5f1b088f82`
revalidation_worktree: `/home/source/SpiritOS-jcode-2j9a-revalidation-20260729`
revalidation_branch: `codex/source-proxy-jcode-2j9a-revalidation-20260729`
revalidation_started_after_commit: `be93b23f3b4b9eff193f03db33438d5c55920f93` (authorization pushed BEFORE revalidation)
no_model_restriction: respected.

## Prospective order proof

1. Audit + prospective authorization written and hashed.
2. Authorization committed (`591d18e34`) and PUSHED (`be93b23f3`) to origin.
3. Clean revalidation worktree created FROM the authorization commit.
4. Authorization hash + base verified in the worktree.
5. Implementation identity verified against `GATE_2J_9A_REVALIDATION_MANIFEST.json`.
6. ONLY THEN revalidation tests ran.
7. This receipt is produced by a commit that DESCENDS from the authorization commit.

`591d18e34` IS an ancestor of the revalidation worktree HEAD. Authorization existed (locally and
on origin) before any revalidation command ran.

## Implementation identity verification

All 10 expected source/config/test files match the manifest's git blob hashes exactly
(4 source modules, 1 test module, 5 config JSON). No drift. The existing Gate 2-J.9A
implementation required NO substantive change; it validated as-is.

## Test results (actual, discovered, not hardcoded)

- Gate 2-J.9A suite: **32 passed** (28 original + 4 policy-correction tests).
- Existing no-model suites: **47 passed** (no regression).
- Total: **79 passed, 0 failed**.

## Canonicalization and hashing (verified)

- Deterministic JSON serialization (sorted keys, separators, ensure_ascii, trailing newline).
- Identical input -> identical bytes -> identical SHA-256.
- Dictionary insertion order cannot change canonical output.
- Section hash binds name+payload; root envelope hash is tamper-evident.
- Authorization self-hash derivation is reproducible (excludes content_sha256 + artifact_commit).

## Envelope/config validation (rejection verified)

missing required fields; unknown top-level section; tampered JCode binary hash; tampered model
digest; unsafe command policy; unsafe fallback; attempted JCode terminal authority; drifted lane
digest; dead/unauthorized endpoint; mismatched config schema versions. All rejected (fail-closed).

## Policy corrections applied (explicit revalidation scope)

- Context policy -> v2 `ONE_TASK_ONE_CANONICAL_CONTEXT_PACKET_ALL_LANES` (A==B==C==D by default;
  model-specific variation only as a declared operator-accepted exception).
- Budget policy -> v2 gate-specific profiles (9a..2j_10) over a `shared_base`. Schema-only gate
  keeps shell=0/deletes=0; later coding gates (2j_10) allow structured repo test/read commands
  and bounded writes to the disposable overlay while denying commit/push/merge/deploy/raw shell.
  No profile authorizes execution of a later gate in this correction.
- Lane bindings -> all four lanes reference one shared context policy/packet identity.

## Integrity

- Frozen benchmark changes: 0. Daily-runtime changes: 0.
- JCode task runs: 0. Model requests: 0. Diagnostic tasks: 0/20. Comparison runs: 0/80.
- No secret in changed files. All JSON validates. Campaign 4 remains paused.

## Verdict

`GATE_2J_9A_REVALIDATION_PASS`. No substantive implementation fix was needed. The corrected
sequence is prospective. The original retroactive-authorization defect is preserved in history
and superseded, not erased.

## Next permitted action

Operator review of this revalidation receipt, then creation of a SEPARATE prospective
Gate 2-J.9B authorization. Gate 2-J.9B is NOT started by this correction.
