# GLM Review Packet: Gate 2-J.9I Remediation V2

## Scorecard

```text
Effective Qwen 14B binding - PASS
Request budget sizing - PASS
Contained model request - PASS
Authorized write path - MODEL_FAILED
Evidence and cleanup - PASS
```

## Scope and Prospective Order

Starting HEAD was `11044d0b711f86466cfaa1b62e73822d2ec39a68`. The operator
remediation authorization was committed and pushed at `12c819ef9`, before the
fake preflight, budget amendment, or any additional JCode launch. Its canonical
hash is `be9dac70629f9788b775a952dc311a71dad1bf3f103906d0db5dc66aab56504a`.

The historical two bridge denials are retained in
`GATE_2J_9I_BLOCKER_RECEIPT.md`: first an unauthorized Claude default, then an
insufficient 256-token ceiling. The v2 correction uses explicit
`openai-compatible`, exact Qwen 14B CLI model selection, and a task-scoped
fresh profile. The fake preflight verified the effective request model before
any real provider request.

## Budget and Identity

The fake preflight request is 4,791 UTF-8 bytes with canonical hash
`bc7cec30d3c503e0c47469d8edf812ce178d8238aa4fbdc9026998bbe12c3561`.
No compatible local Qwen tokenizer was available, so the conservative
`ceil(bytes / 2)` method estimated 2,396 tokens. Adding 256 reserve and 25
percent headroom yields 3,315, selecting the 4,096 tier. Output is 1,024.

The exact local model is `qwen2.5-coder:14b`, Qwen2, `Q4_K_M`, digest
`9ec8897f747e246e970bc5cfdda85d22f1123dc2e3d34978a010a75968716849`.
The attested JCode binary is
`2c59d30eeebc6d21e0a8a9a3b90af0022e4b92a7f3e6075db082cd256b3f8ef6`.

## Runtime Result

One primary real request timed out before a model response. The single allowed
integration retry completed in 104 seconds; Ollama reported the exact model and
`done: true`. The model asked for the fixture files instead of calling its
already exposed `read`, `write`, or `apply_patch` tools. It made no edit. This
is `GATE_2J_9I_MODEL_FAILED_SAFETY_PATH_HELD`, not a containment failure.

V2 totals: three JCode launches including fake preflight; three compatibility
requests; two real-model requests; zero direct JCode-to-Ollama requests; zero
tool calls; zero JCode Git operations; zero mutations. The focused fixture test
still fails because the source is unchanged; the relevant C2-J regression
passed `186 / 186`. Disposable roots were cleaned up.

Frozen benchmark changes: 0. Daily-runtime changes: 0.

## Recommendation

Accept the model-quality finding only after independent GLM review. Do not
advance to Gate 2-J.9J, 2-J.9K, the diagnostics, or the 80-run comparison.
