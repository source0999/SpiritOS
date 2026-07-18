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
| `r1-portable-authority-checkpoint` | Python/TypeScript registered-root and campaign authority suites | pass | portable identity and isolated authority state only | checkpoint observation; terminal manifest pending |
| `r1-cartographer-authority-checkpoint` | full Cartographer API plus proposal-review authority suites | 263 + 7 pass | production proposal review authority and removed client-authority routes | checkpoint observation; terminal manifest pending |
| `r1-design-security-checkpoint` | focused Design authority/writeback suites | 50 pass | existing Design writeback security only | checkpoint observation; terminal manifest pending |
| `r1-spiritflix-authority-checkpoint` | broad SpiritFlix route/transaction suite plus Python authority | 419 + 4 pass | SpiritFlix administrative mutation authority only | checkpoint observation; terminal manifest pending |
| `r1-production-orchestrator-checkpoint` | production route/orchestrator/proof/participant/recovery/target/runtime suites | 120 pass; long-running 71 pass; coding regression 133 pass | production ownership and fail-closed proof semantics only | checkpoint observation; clean proving run and terminal manifest pending |
| `r1-decision-target-orchestrator-checkpoint` | real FastAPI task plus exact LumaCart decision route regression | pass | production importer, exact context/runtime consumption, and direct-bypass rejection only | checkpoint observation; real model/apply proof pending |
| `r1-backend-state-checkpoint` | Source Proxy route tests and Next projection policy tests | pass | single decision-bearing backend owner only | checkpoint observation; terminal manifest pending |
| `r1-immutable-evidence-implementation` | evidence generator/validator/test-profile/secret-scan regression suites | pass | fail-closed source-binding and provenance semantics only | checkpoint observation; terminal artifacts pending |
| `r1-approval-reconciliation-checkpoint` | injected authority-response, receipt-persistence, and local-commit failures | pass | exact idempotent approval finalization and resumable local commit only | checkpoint observation; clean proving run and terminal manifest pending |
| `r1-participant-ownership-checkpoint` | subprocess participant/output/acknowledgement and approval-evidence tamper suites | 42 pass | process-separated output ownership and downstream acknowledgement semantics only | checkpoint observation; clean proving run and terminal manifest pending |
| `r1-terminal-projection-checkpoint` | Source Proxy terminal-proof and Next canonical proof-hash projection suites | pass | backend-owned terminal truth and read-only projection only | checkpoint observation; terminal manifest pending |
| `r1-proving-harness-regression` | inner/outer harness adversarial suites | 16 + 22 pass | harness fail-closed semantics under the stated trusted-prehashed-code claim ceiling only | checkpoint observation; real HTTP proving receipts pending |
| `r1-terminal-crossbinding-regression` | receipt/manifest cross-binding adversarial suite | 13 pass | standalone inner/outer receipt provenance and immutable-manifest inclusion only | checkpoint observation; real terminal artifacts pending |

## Required terminal evidence

| ID | Required artifact | Status | SHA-256 | Claim ceiling |
| --- | --- | --- | --- | --- |
| `r1-authority-callgraph` | `profiles/authority-callgraph.artifact.json` | passed | `fe2b1b87d9330368958633d6be54113fd4f61faf0a8ea33df3761ff18b630992` | production import and authority boundaries |
| `r1-orchestrator-route` | `production-proving-receipt.json` | passed | `ade839b7cb2c7621f126bd4fd529d4dddbb7a9832db4fce0113ddab9dc7b8a2a` | live canonical owner and state machine |
| `r1-runtime-contracts` | `profiles/runtime-contracts.receipt.json` | passed | `bf2e625b67837b7dee4c0712117c649d0141dfdc13c5d11d7b823901abe52d44` | live version/schema/output/consumption enforcement |
| `r1-cartographer-transfer` | `production-proving-receipt.json` | passed | `ade839b7cb2c7621f126bd4fd529d4dddbb7a9832db4fce0113ddab9dc7b8a2a` | real proposal-only participation |
| `r1-independent-participants` | `production-proving-receipt.json` | passed | `ade839b7cb2c7621f126bd4fd529d4dddbb7a9832db4fce0113ddab9dc7b8a2a` | executor/reviewer/verifier/anti-cheat/evidence participation |
| `r1-target-adapters` | `profiles/target-adapters-1-10.receipt.json` | passed | `5513f45cc635510501909707d531289a447f6d1c408ab10159b047a2dd0b8462` | executable target-owned behavior only |
| `r1-controlled-recovery` | `production-proving-receipt.json` | passed | `ade839b7cb2c7621f126bd4fd529d4dddbb7a9832db4fce0113ddab9dc7b8a2a` | exact primary failure and declared fallback recovery |
| `r1-undo-reset-rerun` | `lifecycle-receipt.json` | passed | `ccda1a909a6d24aa42028d77e7b883cd0fb46f0d3c362ffb5bc754a2aed8d4d3` | reversible isolated fixture lifecycle and clean rerun |
| `r1-profile-matrix` | `foundation-remediation-r1-test-profiles.json` plus 44 manifest entries | passed | `aabadfbb7f507b98f8074fa66fd4fbd66141d3261b8bf1497404a6481aaf0317` | exact 22 registered claim ceilings only |
| `r1-terminal-receipt` | `foundation-remediation-r1-receipt.json` | passed | `52b4bef5395031774209e1a204bdfdeee4be740da8c94dbd42181d968a776e37` | tested source commit at `recovered_via_declared_fallback_only` |
| `r1-immutable-manifest` | `foundation-remediation-r1-immutable-manifest.json` | passed | `bbd94369379138059bbb5bc8fcbdf9d54fbc6599d1c36a56fdbfd7e77a6405f7` | content-addressed tracked evidence set |
| `r1-recovery-bundle` | verified bundle plus `.sha256` sidecar at the restoration path | passed after annotated-tag creation | external sidecar binds the final bundle bytes | local restoration only |

The terminal manifest evidence hash is
`ee9dfba49d0e5609dbec90bc3d0095e331abc56ef359d8909f73d8879c818084`.
The profile registry records the raw receipt hash and completion timestamp for every
mandatory profile; the immutable manifest independently binds all 44 profile files.
The recovery-bundle digest is intentionally external because the bundle contains the
commit that tracks this index. Its sidecar is created and verified only after the
annotated terminal tag resolves to that commit.
