# Gate 2-J.9H Read-Only Real-Model Smoke

## Verdict

PASS

## Identity And Authorization

- Authorization: `TERRA_HIGH_AUTHORIZED__GATE_2J_9H_READ_ONLY`
- Binary SHA-256: `2c59d30eeebc6d21e0a8a9a3b90af0022e4b92a7f3e6075db082cd256b3f8ef6`
- Model: `qwen2.5-coder:7b`
- Registry digest: `dae161e27b0e90dd1856c8bb3209201fd6736d8eb66298e75ed87571486f4364`
- Quantization: `Q4_K_M`
- Registry observation: Proxy-side `GET /api/tags` before execution.

JCode had no direct host access. Its only provider path was contained loopback,
the relay sibling, an inherited socketpair, and the Proxy-controlled
compatibility bridge. The bridge made the one authorized host-side
`POST /api/generate` request with the exact model, `temperature: 0`, and
`seed: 7`; Ollama reported the same model and `done: true`.

## Accepted Task

`GATE_2J_9H_READ_ONLY_SMOKE_TASK.json` was created and hashed before execution.
Prompt hash: `95d13b4ce81bcd6a7a5ecac57fca1126515594a3d5ad2a0b89a0548377917b3c`.

The fresh contained JCode run exited `0`, made one bridge request, emitted its
normal NDJSON terminal sequence, and returned exactly `READ_ONLY_SMOKE_OK`.
The independent evaluator accepted that exact response. The root was read-only
and the independent source-worktree Git diff was empty.

## Deviations Preserved

Two earlier, separately hashed source-reading task attempts completed with the
same exact model and zero diff, but were independently rejected because their
answers invented loader names rather than using the supplied files. They are
recorded as failed answer-evaluation attempts, not accepted results. They used
two additional authorized real requests; neither mutated the repository or
opened a direct provider path.

## Counters And Cleanup

- Real model requests: 3 total in Gate 2-J.9H, including two rejected attempts
  and one accepted minimal smoke.
- Accepted task real model requests: 1.
- Fake requests: 0 in Gate 2-J.9H.
- Direct Ollama requests from JCode: 0.
- Cloud or paid-provider requests: 0.
- Repository writes by JCode: 0.
- Frozen benchmark changes: 0.
- Daily-runtime changes: 0.
- Process cleanup: all bounded contained runs exited and disposable roots were
  removed.

Gate 2-J.9I was not started.
