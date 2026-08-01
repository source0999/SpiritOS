# Compact Handoff Packet

## Verdict

`PIPELINE_DIAGNOSIS_COMPLETE__MULTI_FACTOR_FAILURE__AMENDMENT_READY`

Current campaign decision: `PIPELINE_NOT_READY_FOR_COMPARISON`.

## Identity

- Canonical campaign worktree:
  `/home/source/SpiritOS-source-proxy-jcode-qualification-20260726`
- Canonical branch/HEAD:
  `codex/source-proxy-jcode-qualification-20260726` at
  `07151b44cb886ac4d8c3668e947e81825d01bd50`
- Audit worktree:
  `/home/source/SpiritOS-source-proxy-jcode-pipeline-diagnosis-20260731`
- Audit branch:
  `codex/source-proxy-jcode-pipeline-diagnosis-20260731`
- Root-cause report HEAD:
  `abf6b61c4576ab423d11aa0ff9c62f8ca74f0c61`
- Authorization ID:
  `OPERATOR_AUTHORIZATION__C2J_PIPELINE_DIAGNOSIS_20260731_V1`
- Operator prompt SHA-256:
  `f45bde0f3fd1c4c225f4a896577a0778408d449ebee41b3dc4f57c0171ab7afb`

## What Is Proven

- 24 immutable diagnostic runs used 24/36 requests and one turn each.
- Both exact Qwen digests pass direct Task R grounding.
- 7B passes direct Task W; 14B returns semantically correct W code that the AST
  evaluator rejects.
- Both models use assistant-text JSON for reads instead of native tool calls.
- The baseline loop executes a read and exits before result reinjection.
- The legacy JCode bridge drops roles/tools; the corrected diagnostic bridge
  preserves them in 4/4 confirmations.
- Corrected JCode still records zero tool events because text calls are not
  parsed. JCode also lacks Task W's focused-test tool.
- Full Proxy packets reduce relevant-context ratio below two percent and both
  baseline full-packet calls time out.
- One exact request body (`s1-r-e-7b`) and the prior 9I raw response are
  explicitly incomplete. Nothing was reconstructed or retried.

## Campaign State

Retain: 2-J.9B through 2-J.9E Batch 1, runtime 2-J.9G-D through
2-J.9H technical acceptance, and 2-J.9I containment/safety evidence. Refine
9I's model-quality attribution: it is not model-incapability evidence.

Block: new Gate 2-J.9T, 2-J.9J, 2-J.9K, sealed 20-task diagnostics, 80-run
comparison, and Campaign 4.

## Canonical Artifacts

- `HUMAN_TO_CODER_RUNTIME_TRACE.md/json`
- `CONTEXT_PACKET_QUALITY_AUDIT.md`
- `TOOL_PROTOCOL_COMPATIBILITY_AUDIT.md`
- `JCODE_PROMPT_AND_SESSION_AUDIT.md`
- `BRIDGE_TRANSFORMATION_AUDIT.md`
- `DIAGNOSTIC_MATRIX_RESULTS.md/json`
- `MODEL_CAPABILITY_VS_SYSTEM_FAILURE_MATRIX.md`
- `ROOT_CAUSE_TREE.md/json`
- `GLOBAL_CORRECTION_CONFIRMATION.md`
- `CAMPAIGN_2J_PACKET_TOOL_COMPATIBILITY_AMENDMENT.md/json`
- `SOL_ULTRA_FINAL_PIPELINE_DIAGNOSIS.md/json`
- `EVIDENCE_VALIDATION_RECEIPT.json`
- 24 run directories plus the immutable manifest, preflight, request ledger,
  request journal, authorization, freeze, packet schema, and remediation receipt.

## Commit Chain

- `c42d62f189542e69112e600c5e0bdef05e2705ac` authorization/freeze
- `f94f43450ea0f7bec8b9272204d736ac15e5a49b` instrumentation
- `75b53b2187fce9b64b8a2775ddd9e46dc82a4888` socketpair relay
- `2901640068db890b2af21a78b128ea88f92de98c` preflight/manifest
- `09b215935c127cf094993540bb491de7a780d2c8` mountpoint diff fix
- `6a0065b72c06e1f468133cdb974e10850acf1fc2` request journaling
- `e49282debf926ae26a6d680bfff35484c2754bc4` read matrix
- `a28365a5bbe9cf3b7d8d13eed23ec6b571ee3e0a` write matrix
- `eb92504e408a2338fa44b7fc1a3943f8a9976e4a` correction authorization
- `0f11057216fd6465061780d4ea9e866ebbea33aa` confirmation evidence
- `abf6b61c4576ab423d11aa0ff9c62f8ca74f0c61` root-cause report
- final amendment/handoff commit: resolve from audit branch HEAD after commit

## Validation

Run from the audit worktree with the qualified Source Proxy interpreter:

```text
/home/source/SpiritOS-source-proxy-jcode-qualification-20260726/.venv-source-proxy/bin/python -m pytest -q source_proxy/tests/test_jcode*.py
/home/source/SpiritOS-source-proxy-jcode-qualification-20260726/.venv-source-proxy/bin/python scripts/coding/run-jcode-pipeline-diagnosis.py verify-evidence
find docs/architecture/jcode-qualification/pipeline-diagnosis -name '*.json' -print0 | xargs -0 -n1 jq empty
git diff --check
```

Expected: 203 tests pass; evidence reports 24 runs, 24 requests, six timeouts,
one accepted capture gap, and no errors; JSON and diff checks pass.

## Exact Next Action

Review and adopt Gate 2-J.9T. Under a new bounded diagnostic authorization,
implement a concise packet, native-plus-Qwen-text tool parser, productive-read
observation reinjection, one sealed focused-test tool, and behaviorally aligned
evaluator. Rerun only the minimal qualification cells. Do not merge this branch
or start 2-J.9J/9K, 20-task, 80-run, production, deployment, or Campaign 4 work.

---

## GLM Independent Review (2026-08-01)

Verdict: `SOL_AUDIT_ACCEPTED_WITH_CORRECTIONS__PACKET_AMENDMENT_READY`.

The independent GLM review re-verified operator prompt hash, starting/final
HEAD, both model digests (live `ollama list`), the JCode binary hash+version
(live), reproduced the executable evidence verifier at HEAD (`passed: true`,
24 runs/24 requests/6 timeouts/1 declared gap), and re-inspected raw evidence
for all load-bearing lanes. The 14B `re.sub` solution was run against the actual
`focused_check.py` — both assertions PASS — confirming `VERIFIER_EXPECTATION_MISMATCH`.

One correction: adopt canonical amendment ID
`CAMPAIGN_2J_PACKET_TOOL_LOOP_COMPATIBILITY_AMENDMENT_V1` and gate
`Gate 2-J.9T — Model-Ready Packet, Tool Protocol, and Agent-Loop Qualification`
(operator-specified naming; agent-loop dimension made explicit in the title).
All Sol thresholds retained with explicit justification.

Canonical controlling spec + supporting artifacts:
`docs/architecture/jcode-qualification/pipeline-diagnosis/glm-review/PACKET_AMENDMENT.md`
and 13 supporting files in the same `glm-review/` directory. Sols precursor

---

## GLM Independent Review (2026-08-01)

Verdict: SOL_AUDIT_ACCEPTED_WITH_CORRECTIONS__PACKET_AMENDMENT_READY.

The independent GLM review re-verified operator prompt hash, starting/final
HEAD, both model digests (live ollama list), the JCode binary hash+version
(live), reproduced the executable evidence verifier at HEAD (passed: true,
24 runs/24 requests/6 timeouts/1 declared gap), and re-inspected raw evidence
for all load-bearing lanes. The 14B re.sub solution was run against the actual
focused_check.py — both assertions PASS — confirming VERIFIER_EXPECTATION_MISMATCH.

One correction: adopt canonical amendment ID
CAMPAIGN_2J_PACKET_TOOL_LOOP_COMPATIBILITY_AMENDMENT_V1 and gate
Gate 2-J.9T — Model-Ready Packet, Tool Protocol, and Agent-Loop Qualification
(operator-specified naming; agent-loop dimension made explicit in the title).
All Sol thresholds retained with explicit justification.

Canonical controlling spec + supporting artifacts:
docs/architecture/jcode-qualification/pipeline-diagnosis/glm-review/PACKET_AMENDMENT.md
and 13 supporting files in the same glm-review/ directory. Sol's precursor
draft (CAMPAIGN_2J_PACKET_TOOL_COMPATIBILITY_AMENDMENT.md) is retained as
audit evidence.

Next authorized action unchanged:
Operator review and adoption of PACKET_AMENDMENT.md, followed by a prospective
Terra High authorization for Gate 2-J.9T-A through Gate 2-J.9T-D only.
