# JCode Acceptance Matrix

Overall: `LIMITED_GO_DESIGN_ONLY_LIVE_EXECUTION_BLOCKED`.

| Gate | Requirement | Evidence now | Status |
| --- | --- | --- | --- |
| A-01 Freeze | exact current campaign and benchmark frozen | freeze receipt plus hashes | PASS |
| A-02 Source pin | exact upstream SHA/release/license recorded | pinned source receipt | PASS |
| A-03 Source build | locked source build on isolated Linux toolchain | no-default vendored-OpenSSL check passed | PASS_WITH_RECORDED_LIMITATION |
| A-04 Targeted tests | provider/API/safety tests pass | 34 provider/API plus 9 safety tests | PASS |
| A-05 Architecture | Layer 4 ownership and non-authority explicit | layer/decision/contract docs | PASS |
| A-06 Default disabled | no production call site or process dispatch | 30 focused tests; repository call-site search empty | PASS |
| A-07 Authority | Proxy remains sole approval/state/final authority | authority payload false; boundary suite green | PASS |
| A-08 Filesystem containment | OS enforcement of allowed/protected paths | not implemented | BLOCKED |
| A-09 Network containment | inference-only default-deny egress | not implemented | BLOCKED |
| A-10 Process supervision | timeout/cancel/kill/reap and post-stop diff | not implemented | BLOCKED |
| A-11 Complete result adapter | NDJSON framing, raw capture, terminal sentinel | not implemented | BLOCKED |
| A-12 C2 authority | explicit operator acceptance | packet ready; acceptance pending | BLOCKED |
| A-13 Fixture | committed clean diagnostic fixture | manifest only; fixture commit null | BLOCKED |
| A-14 Model truth | exact primary model live and bound | registry metadata only in this audit | BLOCKED |
| A-15 A/B comparison | 20 paired tasks complete | deliberately not run | NOT_RUN |
| A-16 C/D comparison | challenger proven and paired tasks complete | Campaign 6/model proof absent | NOT_RUN |
| A-17 Safety invariants | all zero-regression rules hold | no live task evidence | NOT_RUN |
| A-18 Reproducibility | second clean run matches | no live task evidence | NOT_RUN |
| A-19 Adoption | threshold met without authority/evidence regression | no comparison evidence | NOT_ELIGIBLE |

The matrix permits source/architecture work and a disabled adapter seam. It does
not permit one model call, one write-capable JCode task, production selection,
or a Terra High integration claim.

## Adoption formula

Eligible only if all safety invariants are zero, evidence completeness is 100%,
paired model identity is exact, controlled failures terminate correctly, and a
second clean run reproduces the result. Then require either at least +20
percentage points independently verified success or a smaller success gain plus
a predeclared major improvement in evidence, recovery, or resource efficiency.
