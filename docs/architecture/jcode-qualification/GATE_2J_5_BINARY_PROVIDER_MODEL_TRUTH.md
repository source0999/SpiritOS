# Gate 2-J.5 Binary, Provider, and Model Truth

status: `GREEN_BINARY_ATTESTED_MODEL_RECONCILIATION_FAIL_CLOSED`

The initial fresh registry cache contained a malformed `rustls 0.23.37` source
despite the locked version. The audited Cargo cache contains the correctly
spelled, checksummed source. A fully offline locked build using that audited
cache completed without touching the audit checkout or daily runtime.

| Field | Evidence |
|---|---|
| Pinned source | `2444e7b6bc80d421ae3ee404081bdb41150a1830`, audit checkout clean |
| Build mode | `CARGO_BUILD_JOBS=1`, `--locked --no-default-features --features linux-compat-vendored-openssl --bin jcode`, offline audited cache |
| Binary SHA-256 | `d7598ca48bb4fc8ff9c37d122fde5dd47314cd36fc2516ce6156795b71a545cc` |
| Binary version | `jcode v0.58.51-dev (2444e7b6)` |
| Identity code | `source_proxy/jcode/identity.py`, focused tests pass |

The reconciliation contract accepts an executor receipt only when the requested
provider profile and requested model exactly equal observed provider profile and
actual model. Missing actual identity blocks. No provider, model, or task was
called at this gate, so no live model identity is claimed; that observation is a
mandatory input to the controlled comparison gate.

Gate 2-J.5 is complete as binary attestation and fail-closed reconciliation
logic. Gate 2-J.6 evidence mapping may begin.
