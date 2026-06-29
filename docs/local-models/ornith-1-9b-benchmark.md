# Ornith 1.0 9B Model-Lane Benchmark

## Verdict

Benchmark execution status: PASS. Local Ollama calls completed on the Dell host for the configured local candidates and produced parsed/timed evidence.

Routing status: NO CHANGE. This benchmark does not authorize any automatic route change or promotion. Any secondary or primary routing change requires Britton approval.

Evidence folder:

```text
docs/evidence/ornith-model-lane-benchmark-20260628-223123/
```

The evidence was generated from live local Ollama calls and then rescored from bounded raw samples without rerunning model calls after tightening the blocker detector for negated cloud-fallback language.

## Models

| Key | Model ID |
| --- | --- |
| Qwen | `qwen2.5-coder:7b` |
| Ornith | `hf.co/deepreinforce-ai/Ornith-1.0-9B-GGUF:Q4_K_M` |
| Hermes | `hermes4:latest` |
| Gemma | `gemma3n:e4b` |

## Role Results

| Role | Winner | Ornith result |
| --- | --- | --- |
| Coder patch author | Qwen | NEEDS_MORE_TESTS |
| Workflow organizer | Qwen | NEEDS_MORE_TESTS |
| Intent/spec extraction | Gemma | ADD_AS_SECONDARY candidate only |
| Critique/risk verifier | Qwen | NEEDS_MORE_TESTS |
| Research/query formulation | Qwen | ADD_AS_SECONDARY candidate only |
| Operator closeout | Qwen | ADD_AS_SECONDARY candidate only |
| Visual/media roles | Not applicable | DO_NOT_USE_FOR_ROLE |

## Routing Recommendation

- Do not replace Qwen as coder.
- Do not make Ornith the primary workflow organizer.
- Do not replace Hermes or Gemma with Ornith.
- Do not use Ornith for visual/media roles; no multimodal Ornith route was found.
- Keep Ornith challenger-only by default.
- Consider a secondary, explicitly approved Ornith lane only for intent/spec, research-query packet drafting, or closeout drafting, and only with parser checks and human review.

## Key Evidence

- `summary.json` has aggregate role scores, latency, parser success, and blocker counts.
- `scorecard.md` has the compact role/model table.
- `recommendation-matrix.md` records the no-change routing recommendation.
- `results.jsonl` and `samples/` preserve bounded per-call evidence.
