# Gate 2-J.5 Binary, Provider, and Model Truth

status: `GREEN_BINARY_ATTESTED_MODEL_RECONCILIATION_FAIL_CLOSED`

The initial fresh registry cache contained a malformed `rustls 0.23.37` source
despite the locked version. The audited Cargo cache contains the correctly
spelled, checksummed source. A fully offline locked build using that audited
cache completed without touching the audit checkout or daily runtime.

| Field | Evidence |
|---|---|
| Pinned source | `2444e7b6bc80d421ae3ee404081bdb41150a1830`, audit checkout clean |
| Build mode | `--locked --no-default-features --features linux-compat-vendored-openssl --bin jcode`, offline audited cache |
| Binary SHA-256 | `6f0b9aca0017075d614481ebbc2f39baa27380a6421aa01bfc42ca4c65f5c3ab` |
| Binary version | `jcode v0.58.51-dev (2444e7b6)` |
| Identity code | `source_proxy/jcode/identity.py`, focused tests pass |

The reconciliation contract accepts an executor receipt only when the requested
provider profile and requested model exactly equal observed provider profile and
actual model. Missing actual identity blocks. No provider, model, or task was
called at this gate, so no live model identity is claimed; that observation is a
mandatory input to the controlled comparison gate.

Gate 2-J.5 is complete as binary attestation and fail-closed reconciliation
logic. Gate 2-J.6 evidence mapping may begin.
