# Full Set A Remaining Fix Rerun - 2026-06-24

## Command

`PLAN3_STAGE4R_ONLY=A1,A3,A4,A6,A7,A8,A10 .venv/bin/python docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/_stage4r_runner.py`

## Fix Applied

- Root cause groups: `RESEARCH_SOURCE_LINKAGE`, `RESEARCH_MATERIALITY`, `VERIFIER_EXPECTATION_MISMATCH`, `PROMPT_TEMPLATE_UNCLEAR`
- Shared source/parser fixes:
  - raw source matching now accepts exact host, exact URL, exact normalized title, or strong raw-title token overlap
  - fake source lines still fail because they do not match raw source objects
  - repo-only prompts no longer receive research materiality/source-linkage failures when research was not required and no sources exist
  - concrete planning verbs such as prioritize, implement, evaluate, examine, focus, and narrow are recognized as specific decisions
  - retry prompt clarifies source-line and decision-verb requirements

## First Slice Result

- A1: `PASS`
- A3: `NEEDS_FIX` with `research_change_no_specific_decision`, `research_change_source_not_from_raw_sources`
- A4: `PASS`
- A6: `PASS`
- A7: `PASS`
- A8: `PASS`
- A10: `PASS`

One tiny loop was allowed because A3 still had the same shared source-linkage/materiality root. The loop added raw-title token matching and `evaluate` / `explore` as concrete planning verbs.

## Second Slice Result

- A1: `NEEDS_FIX` with `research_materially_changed_output`, `research_change_fields_too_thin`
- A3: `PASS`
- A4: `PASS`
- A6: `PASS`
- A7: `PASS`
- A8: `PASS`
- A10: `PASS`

## Prompt Details

| Prompt | Before failure | Root cause group | New selected lane/model/provider | Validation result | Receipt path | Trace path | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A1 | `research_materially_changed_output`, `research_change_no_specific_decision` | `RESEARCH_MATERIALITY`, then `DECISION_BODY_TOO_THIN` | `ollama_default` / `gemma3n:e4b` / `ollama` | no packet validation used | `docs/source-proxy-human-brain-full-live-integration-pivot-20260619/plan-03/continuation-3x10-dryrun/set-a-rerun/A1.json` | `/home/source/spiritos-evidence/plan-03-3x10-dryrun/set-a-rerun/A1.task.final.raw.json` | `NEEDS_FIX` |
| A3 | `research_materially_changed_output`, `repo_context_used`, `limitations_stated`, `handoff_created`, `research_change_no_specific_decision`, `research_change_source_not_from_raw_sources` | `RESEARCH_SOURCE_LINKAGE`, `RESEARCH_MATERIALITY` | `ollama_default` / `gemma3n:e4b` / `ollama` | no packet validation used | `.../set-a-rerun/A3.json` | `/home/source/spiritos-evidence/plan-03-3x10-dryrun/set-a-rerun/A3.task.final.raw.json` | `PASS` |
| A4 | `research_materially_changed_output`, `research_change_no_specific_decision` | `RESEARCH_MATERIALITY` | `ollama_default` / `gemma3n:e4b` / `ollama` | no packet validation used | `.../set-a-rerun/A4.json` | `/home/source/spiritos-evidence/plan-03-3x10-dryrun/set-a-rerun/A4.task.final.raw.json` | `PASS` |
| A6 | `research_materially_changed_output`, `research_change_no_specific_decision` | `RESEARCH_MATERIALITY` | `ollama_default` / `gemma3n:e4b` / `ollama` | no packet validation used | `.../set-a-rerun/A6.json` | `/home/source/spiritos-evidence/plan-03-3x10-dryrun/set-a-rerun/A6.task.final.raw.json` | `PASS` |
| A7 | `research_change_source_not_from_raw_sources` | `VERIFIER_EXPECTATION_MISMATCH` | `ollama_default` / `gemma3n:e4b` / `ollama` | no packet validation used | `.../set-a-rerun/A7.json` | `/home/source/spiritos-evidence/plan-03-3x10-dryrun/set-a-rerun/A7.task.final.raw.json` | `PASS` |
| A8 | `research_change_source_not_from_raw_sources` | `VERIFIER_EXPECTATION_MISMATCH` | `ollama_default` / `gemma3n:e4b` / `ollama` | no packet validation used | `.../set-a-rerun/A8.json` | `/home/source/spiritos-evidence/plan-03-3x10-dryrun/set-a-rerun/A8.task.final.raw.json` | `PASS` |
| A10 | `research_change_source_not_from_raw_sources` | `VERIFIER_EXPECTATION_MISMATCH` | `ollama_default` / `gemma3n:e4b` / `ollama` | no packet validation used | `.../set-a-rerun/A10.json` | `/home/source/spiritos-evidence/plan-03-3x10-dryrun/set-a-rerun/A10.task.final.raw.json` | `PASS` |

## Stop Reason

The maximum one additional fix loop was used. The remaining A1 failure is now `research_change_fields_too_thin`, which is a model-output thinness issue rather than the original shared source-linkage/materiality parser bug. Full Set A was not rerun because the remaining slice did not reach GO.
