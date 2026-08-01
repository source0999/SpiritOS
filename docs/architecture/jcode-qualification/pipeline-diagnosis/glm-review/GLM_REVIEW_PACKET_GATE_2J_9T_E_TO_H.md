# GLM Review Packet - Gate 2-J.9T E-H

## Scorecard

- 2-J.9T-E Focused test/evaluator: PASS (`211b0a3b0`)
- 2-J.9T-F Qwen profiles: PASS for read-only (`5eb6c66a2`)
- 2-J.9T-G Baseline harness: PARTIAL (`550d40455`): both read lanes grounded; neither model qualified the immutable write lane.
- 2-J.9T-H JCode harness: FAIL/CONFIG-BLOCKED: the pinned JCode binary/source and required runtime capabilities are absent.

Batch 2 authorization predates implementation: `0a7f3a84b`. Authorized model ledger: 14 of 24 requests. Exact models/digests were verified: 7B `dae161e2...f4364`, 14B `9ec8897f...16849`, both Q4_K_M. No benchmark, daily runtime, or production-default changes; no direct JCode provider path; no fallback.

The corrected baseline proved tool-mediated read observation reinjection for both models. The isolated non-benchmark write lane preserved a 7B ambiguous textual multi-call/invalid patch and a 14B scoped but behaviorally failing patch. The fixture was restored and removed.

H cannot run without a trusted pinned JCode binary/source, enabled qualification runtime, and required containment contracts. Recommendation: HOLD Batch 2; independently review the model limitations and JCode configuration blocker before authorizing any remediation or Gate I.
