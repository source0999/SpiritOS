# A2/A5/A9 Packet Failure Analysis - 2026-06-23

## Summary

Current Set A blockers are all structured decision packet failures. The validator is rejecting malformed or unsupported packets from `ollama_hermes4_latest`; the raw attempts show non-JSON wrapping, fuzzy or misspelled keys, fabricated hosts/URLs, missing required fields, and decisions that do not cite allowed evidence IDs.

Most likely root cause: `LANE_SELECTION_WRONG`.

Hermes is useful as a critique/advisory lane, but the current runner makes it the first structured packet author even though the repo already defines `qwen_local_coder` as the primary local coder lane and `qwen2.5-coder:7b` is installed locally. Structured packet generation needs a structured-output-capable author lane before using Hermes as sidecar/advisory.

## Evidence Table

| Prompt | Selected lane/model | Validation errors | Root cause candidate | Proposed fix |
| --- | --- | --- | --- | --- |
| A2 | `ollama_hermes4_latest` / `hermes4:latest` | `missing_contract_term:local api`, `non_json_wrapping_text`, invalid source URLs, missing/actionless decision fields | `LANE_SELECTION_WRONG` | Prefer installed `qwen2.5-coder:7b` for structured packet authorship; leave Hermes available as advisory/fallback after qwen. |
| A5 | `ollama_hermes4_latest` / `hermes4:latest` | missing no-new-hardware/privacy terms, fabricated `ollama.ai`/Apple source data, insufficient source refs, invalid evidence refs, non-JSON wrapping | `LANE_SELECTION_WRONG` | Prefer installed `qwen2.5-coder:7b` for structured packet authorship; keep validator unchanged so fabricated evidence still fails. |
| A9 | `ollama_hermes4_latest` / `hermes4:latest` | missing `use now` / `test later` / `skip`, non-JSON wrapping, garbled/fabricated token detection, invalid evidence | `LANE_SELECTION_WRONG` | Prefer installed `qwen2.5-coder:7b` for structured packet authorship; keep Hermes as later lane only if qwen fails. |

## Why This Is Not Contract Weakening

- The validator is catching real defects: malformed JSON wrapping, invented evidence, missing truth fields, and missing required prompt gates.
- Required truth fields remain required.
- Invalid packets must still fail.
- The fix changes lane ordering for structured packet authoring, not acceptance criteria.
- API/frontier escalation remains gated and is not added.

## Fix Strategy

Use a deterministic local-first lane-selection rule:

1. Honor `PLAN3_STAGE4R_PACKET_MODEL` if explicitly set.
2. Prefer the configured local qwen coder model for structured packet authoring when installed.
3. Keep Hermes available after qwen for critique/advisory or fallback evidence.
4. Keep Gemma/current default available after Hermes.
5. Keep API/provider lanes gated by existing environment credentials.

No prompt-ID branch, no hardcoded A2/A5/A9 answers, and no validation downgrade.
