# JCode Qualification Manifest and Acceptance Matrix

Current qualification status: BINARY_RESEALED_RUNNER_PREFLIGHT_BLOCKED.
Binary provenance is green through the Dell two-build attestation. The runner,
complete result adapter, live comparison, and adoption remain not run.

status: `MANIFEST_SEALED_NOT_EXECUTED`

The sealed diagnostic manifest contains 20 tasks: five read-only investigation,
five constrained single-file repairs, five multi-file implementations, three
test-failure/retry tasks, and two ambiguity/escalation tasks. Its SHA-256 is
`149e2cdc7407f19cb4b0a431edb246affaaaeebabaa0694a22af57dcb6cadbb6`.

It is not the frozen benchmark, contains no frozen task text, has not been
shown to an executor, and must not run during Gate 2-J.0. Fixture creation and
commit are future prerequisites, not evidence available now.

| Acceptance group | Current disposition |
|---|---|
| Freeze, source pin, targeted source tests, Layer 4 design, default disabled, Proxy authority | Design evidence recorded |
| Filesystem, network, supervision, complete result adapter, fixture, model truth | BLOCKED |
| A/B and challenger comparisons, live safety, clean reproduction | NOT_RUN |
| Adoption | NOT_ELIGIBLE |

No result in this matrix upgrades JCode from `SPECIFIED_NOT_RUNTIME_PROVEN`.
