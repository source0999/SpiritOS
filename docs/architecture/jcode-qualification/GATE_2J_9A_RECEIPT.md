# Gate 2-J.9A Receipt — Authority Constants and Canonical Schemas

status: `GATE_2J_9A_COMPLETED_NO_MODEL`

schema: `source-proxy.gate-2j-9a-receipt/v1`
gate: 2-J.9A (Authority Constants and Canonical Schemas)
executor: Terra High (driven by GLM campaign authority architect)
no_model_restriction: respected — no JCode process spawned, no model request, no benchmark or daily-runtime change.

## Objective

Implement canonical schemas, sealed authority constants, deterministic canonical
serialization, SHA-256 hashing, fail-closed envelope validation, and sealed
configuration loaders for the Gate 2-J.9 dispatcher. No execution authority granted.

## Implemented artifacts

| Artifact | Path | Purpose |
|---|---|---|
| Sealed constants | `source_proxy/jcode/constants.py` | single source of truth for all sealed values |
| Canonical IO | `source_proxy/jcode/canonical_io.py` | deterministic canonical JSON + section/root hashing |
| Sealed envelope | `source_proxy/jcode/sealed_envelope.py` | schema, required sections, fail-closed validation |
| Config loaders | `source_proxy/jcode/config_loaders.py` | lane/context/provider/budget loaders with drift rejection |
| Tests | `source_proxy/tests/test_jcode_2j9a_sealed_authority.py` | 28 tests |

## Sealed decisions encoded

All five authority decisions are sealed and encoded (see
`GATE_2J_9_SEALED_AUTHORITY_DECISIONS.md` and the `gate_2j_9_*.json` artifacts):
1. lane + executor binding; 2. context-packet construction; 3. provider profile +
bridge (corrects the dead port-4000 slot); 4. budgets/limits; 5. real-model probe
deferred to 2-J.9H.

## Tests run

- Gate 2-J.9A suite: **28 passed**.
  Covers: canonical-JSON determinism + sorted keys; trailing-newline/UTF-8 bytes;
  hash rule parity with `preparation`; section hash binds name+payload; root hash
  tamper-evidence; empty-map rejection; sealed-constant parity; paired-lane model
  sharing; good-envelope validation with hashes; missing-field, tampered-identity,
  unknown-section, unsafe-command-policy, unsafe-fallback, jcode-terminal-authority
  rejection; envelope-hash tamper-evidence; sealed lane/context/provider/budget
  loading; drifted-digest rejection; unsafe-shell budget rejection; dead-endpoint
  rejection.
- Existing no-model suites: **47 passed** (no regression).

## Controlled failures demonstrated

tampered envelope -> rejection; missing required field -> rejection; unknown section ->
rejection; unsafe command policy -> rejection; unsafe fallback -> rejection; JCode
terminal authority -> rejection; drifted lane digest -> ConfigLoadError; unsafe shell
budget -> ConfigLoadError; dead 4000 endpoint as permitted -> ConfigLoadError.

## Integrity

- JCode task runs: 0. Model requests: 0. Diagnostic tasks: 0/20. Comparison runs: 0/80.
- Frozen benchmark changes: 0. Daily-runtime changes from this work: 0.
- No secret in changed files (scan: secrets not present in source_proxy/jcode new modules).

## Acceptance

Gate 2-J.9A acceptance criteria met: schemas versioned; sealed constants encoded;
deterministic canonical serialization + hashing; fail-closed validation; sealed config
loaders with drift rejection; static/unit tests green; receipt produced. No JCode or
model execution. Automatic advancement NOT permitted; stop here pending the next
authorization (`TERRA_HIGH_AUTHORIZED__GATE_2J_9B`).
