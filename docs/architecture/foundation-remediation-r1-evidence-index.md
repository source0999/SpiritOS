# Foundation Remediation R1 Evidence Index

Schema: `spiritos-foundation-remediation-r1-evidence-index/v1`

## Acceptance policy

An entry is accepted only when its command ran from the named Dell worktree/HEAD,
the result is stored at a stable path, its SHA-256 is recorded, and the claim does not
exceed the profile ceiling. Terminal evidence additionally requires the v1 receipt,
tracked immutable manifest, annotated tag, verified recovery bundle, and SHA sidecar.

Ignored runtime output, mutable database state, callback labels, test-only imports,
and self-declared `GO` fields are not accepted terminal evidence.

## Baseline evidence

| ID | Source | Result | Claim ceiling | Accepted |
| --- | --- | --- | --- | --- |
| `r1-baseline-git-integrity` | Dell `git fsck --full --strict --no-progress --no-dangling` | pass | object integrity at branch creation | diagnostic; terminal rerun required |
| `r1-baseline-protected-heads` | exact six commit resolutions | pass | ref identity at branch creation | diagnostic; terminal rerun required |
| `r1-baseline-c1-validators` | inherited C1 validator commands | mixed/fail | demonstrates no inherited R1 acceptance | diagnostic only |
| `r1-baseline-c2-authority` | inherited C2 authority validator | pass despite production bypass | falsification example only | diagnostic only |
| `r1-baseline-c2-completion-regression` | inherited suite | 6 pass / 1 fail | contradiction proof only | diagnostic only |
| `r1-control-completion-regression` | `scripts/test-foundation-remediation-r1-completion.py` | 6/6 pass | fail-closed evaluator semantics only | checkpoint observation; terminal manifest pending |
| `r1-control-test-profile-validator` | `scripts/validate-foundation-remediation-r1-test-profiles.py` | pass | registry coherence only | checkpoint observation; terminal manifest pending |
| `r1-runtime-contract-boundary` | focused runtime boundary/contracts/orchestrator/Cartographer/observability suites | 25 pass | immutable library boundary only; no live-call claim | checkpoint observation; live proof and terminal manifest pending |

## Required terminal evidence

| ID | Required artifact | Status | SHA-256 | Claim ceiling |
| --- | --- | --- | --- | --- |
| `r1-authority-callgraph` | validator output/manifest entry | pending | pending | production import and authority boundaries |
| `r1-orchestrator-route` | HTTP task lineage | pending | pending | live canonical owner and state machine |
| `r1-runtime-contracts` | producer/consumer events | pending | pending | live version/schema/output/consumption enforcement |
| `r1-cartographer-transfer` | proposal/selection/transfer lineage | pending | pending | real proposal-only participation |
| `r1-independent-participants` | five distinct invocation/output records | pending | pending | executor/reviewer/verifier/anti-cheat/evidence participation |
| `r1-target-adapters` | prompts 1-10 focused matrix | pending | pending | executable target-owned behavior only |
| `r1-controlled-recovery` | one run/resume lineage | pending | pending | exact failure/retry/fallback/claim-ceiling recovery |
| `r1-undo-reset-rerun` | undo, reset, and clean rerun receipts | pending | pending | reversible isolated fixture lifecycle |
| `r1-terminal-receipt` | `foundation-remediation-r1-receipt.json` | pending | pending | tested source commit at stated claim ceiling |
| `r1-immutable-manifest` | tracked closeout manifest | pending | pending | content-address and recovery reachability |
| `r1-recovery-bundle` | verified Git bundle + SHA sidecar | pending | pending | local restoration only |

The index is updated in every checkpoint that accepts new evidence. “Pending” may not
be converted to “passed” without an actual artifact path and verified hash.
