# Campaign 2 Acceptance Matrix

status: `IMPLEMENTATION_AND_NEGATIVE_PROOF_COMPLETE_OPERATOR_ACCEPTANCE_PENDING`

| Requirement | Result | Evidence or disposition |
|---|---|---|
| C1 dependency | GREEN | Accepted source `aa06361c` and publication `4e577218`; C2 was created from the publication commit. |
| Isolated C2 source | GREEN | Branch `codex/source-proxy-campaign-2-full-pipeline-benchmark-authority-20260726`, initial HEAD `4e577218`, rollback point recorded in the authority matrix. |
| C2-FR-001 frozen contract | GREEN | `C2-FPA-001` is generated from clean source `2ecbb56d`; task manifest and contract digests are rederived. |
| C2-FR-002/003 canonical path and identity | GREEN | The receipt schema requires authenticated canonical entry, producer-owned terminal truth, clean source/runtime CWD, commit/tree, and remote identity equality. |
| C2-FR-004/005 causal and applicability proof | GREEN | The scorer requires pre-outcome applicability and every six causal boundaries for each applicable capability. |
| C2-FR-006 oracle isolation | GREEN | Isolated verifier, digest-only oracle reference, forbidden-import flag, and actor access audit hard-fail exposure. |
| C2-FR-008/009/010 ten-task coverage | GREEN | Immutable controlled/unfamiliar ten-task manifest includes baseline, multi-file, discovery, expansion, review, verifier repair, strategy, escalation/refusal, restart, and negative controls. Later capability slices remain requirements, not claimed integrations. |
| C2-FR-011 clean rerun | GREEN | Campaign scoring requires distinct first/clean namespaces and fresh-state IDs; reuse blocks the terminal token. |
| C2-FR-012/013 strict scorer | GREEN | Missing receipts, identity drift, leaks, causal gaps, or one missing task reject the literal `10/10` result; declared scores are not trusted. |
| C2-FR-014 Basic Backend 10 boundary | GREEN | Its token is structurally rejected as full-pipeline authority; the historical runner is preserved unchanged. |
| C2-FR-015 native-equivalence ledger | PENDING LATER CAMPAIGNS | The add-only contract reserves capability slices; no unsupported equivalence claim was made. |
| C2-FR-016 immutable terminal output | GREEN | Gate code only reads/rederives receipts and writes new immutable receipt files; it has no product mutation path. |
| C2-FI-002 non-consumed layer | GREEN | `C2-RCPT-001-negative-control` rejected `repository_discovery` after `consumed` and consumer acknowledgement were removed. |
| C2-UT-001 through C2-UT-010 | GREEN | `source_proxy/tests/test_full_pipeline_authority.py`: `9 passed` (the mocked and sidecar variants share one parametrized test). |
| C2-LP-002 baseline disposition | GREEN | The source-bound negative receipt is deliberately non-green and explains the exact causal gap; it makes no product-success claim. |
| C2-LP-003 disconnected/non-influential proof | GREEN | The required non-consumption failure was injected and rejected by the rederived scorer. |
| C2-LP-004/005 additional live failure proofs | PENDING OPERATOR-RUN PACKET | The validator supports oracle leakage, cross-run identity, and clean-state rejection; no private-oracle leak was intentionally exercised against a production participant. |
| C2-LP-006 Basic Backend boundary | GREEN | Unit coverage rejects Basic Backend 10 as a full-pipeline token source. |
| C1 terminal regressions | GREEN WITH RECORDED FULL-SUITE EVIDENCE | This run: orchestrator `44 passed`, proof `56 passed`; accepted C1 packet records the `81`-test long-running suite. A combined re-run exceeded the command cap; its final eight cases passed individually. |
| Coding regression | GREEN | `npm run test:coding-regression`: `139 passed, 46 subtests passed`. |
| Frontend/typecheck/build | INCOMPLETE | Combined command exceeded the execution cap before a reliable result was emitted; no green claim is made. |
| Operator acceptance | PENDING | The threat model, hidden-oracle boundary, resource policy, contract, and clean-rerun policy require an explicit operator decision. |

The matrix deliberately does not mark the full proxy green. It also does not
authorize Campaign 3, a daily-runtime change, deployment, or merge to a
primary branch.
