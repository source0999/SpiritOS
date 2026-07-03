# GLM-4-9B Model-Lane Benchmark

## Verdict

Benchmark execution status: PASS. Local Ollama calls completed on the Dell host for GLM-4-9B Q5_K_M and comparison models; parsed/timed evidence is under the evidence folder below.

Routing status: NO CHANGE. This benchmark does not authorize any automatic route change or promotion. Any secondary or primary routing change requires Britton approval.

Evidence folder:

```text
docs/evidence/glm4-9b-model-lanes-20260702-202200/
```

Runtime: ~137 minutes for 87 model/task pairs (18 tasks × up to 5 models each).

## Models

| Key | Model ID |
| --- | --- |
| GLM (challenger) | `hf.co/bartowski/THUDM_GLM-4-9B-0414-GGUF:Q5_K_M` |
| Qwen 7B (primary coder) | `qwen2.5-coder:7b` |
| Qwen 14B (challenger) | `qwen2.5-coder:14b` |
| Hermes 4 | `hermes4:latest` |
| Gemma | `gemma3n:e4b` |
| Ornith | `hf.co/deepreinforce-ai/Ornith-1.0-9B-GGUF:Q4_K_M` |

Hermes-14B was in inventory but not wired into task model_keys for this run (optional comparison only).

## Role Results

| Role | Winner | GLM result |
| --- | --- | --- |
| Coder patch author | Qwen 7B | NEEDS_MORE_TESTS (180s timeout on strict JSON patch; avg 3.10 vs Qwen 4.24) |
| Workflow organizer | GLM | ADD_AS_SECONDARY (avg 4.43, beat Qwen 4.24; no hard blockers) |
| Intent/spec extraction | Gemma | NEEDS_MORE_TESTS (timeout on proxy-intent task; avg 3.19 vs Gemma 4.33) |
| Critique/risk verifier | Qwen 7B | ADD_AS_SECONDARY (avg 4.24, tied Hermes; zero blockers) |
| Research/query formulation | Qwen 7B | NEEDS_MORE_TESTS (timeout on repo-first task; avg 2.95) |
| Operator closeout | Qwen 7B | ADD_AS_SECONDARY (avg 4.38, solid but slower than Qwen) |
| Visual/media roles | Not applicable | DO_NOT_USE_FOR_ROLE |

## Routing Recommendation

- Do not replace Qwen 7B as primary coder. GLM timed out on `coder_strict_patch_edit` and scored below Qwen on all coder tasks.
- Do not replace Gemma for intent/spec. GLM timed out on `intent_proxy_implementation`.
- Do not replace Qwen/Hermes for research query packets. GLM timed out on `research_repo_first_no_web`.
- Consider GLM as a secondary challenger only for workflow organization, critique, and closeout drafting — pending Britton approval and parser checks.
- Do not use GLM for visual/media roles.
- GLM beats Ornith on workflow organizer (4.43 vs 1.95) and is more reliable on critique (zero blockers vs 7). Ornith still edges GLM slightly on coder avg score but both fail promotion gates.
- No production default routing was mutated.

## Key Evidence

- `summary.json` — aggregate role scores, latency, parser success, blocker counts.
- `scorecard.md` — compact role/model table.
- `recommendation-matrix.md` — no-change routing recommendation.
- `results.jsonl` and `samples/` — bounded per-call evidence.
- Install notes: `docs/local-models/glm-4-9b-install.md`

## Harness

```bash
python3 -m source_proxy.benchmarks.model_lane_benchmark --suite glm
```

Suite added on branch `bench/glm4-9b-model-lanes`; Ornith suite remains default for backward compatibility.
