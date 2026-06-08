# Increment 1.4 - Provenance Fields

## Fields added/preserved

Implemented across source proxy diagnostics and frontend durable rows:

- `generation_source`
- `diff_source`
- `model_output_classification`
- `raw_response_length`
- `raw_response_excerpt_safe`
- `scaffold_used`
- `scaffold_kind`
- `fallback_used`
- `fallback_kind`
- `parser_repair_used`
- `bounded_create_used`
- `known_scaffold_used`
- `generic_scaffold_used`
- `model_raw_diff_used`
- `generated_diff_by_backend`
- `trial_result_trust_status`

## Storage and display surfaces

- `source_proxy/tasks/long_running.py` initializes and updates diagnostics.
- `src/lib/coding/durable-run-types.ts` defines durable provenance shape.
- `src/lib/coding/durable-run-store.ts` normalizes and persists provenance.
- `src/components/coding/CodingCockpitShell.tsx` carries provenance into reversible trial results and durable rows.

## Self-check

- PASS and NEEDS_FIX rows can carry provenance: yes.
- Safe raw excerpts are redacted/truncated: yes.
- Missing provenance defaults to `missing_provenance`: yes.
- Provider call alone is not treated as model proof: yes.
