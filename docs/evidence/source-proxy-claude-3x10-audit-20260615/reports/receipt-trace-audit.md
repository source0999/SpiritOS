# Receipt & Trace Audit (evidence-based)

Date: 2026-06-16 (UTC). Basis: 30-row battery receipts + traces + source inspection.

## Durability & consistency (STRONG)

- 30/30 posted rows produced a durable FIP-0 receipt at
  `docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/<run_id>.json`.
- 30/30 produced an FIP-6 trace; 30/30 `verdict_trace.final_verdict == receipt.final_verdict`.
- trace_version `fip6.operator_trace.v1`; trace_authority
  `operational_receipt_projection_no_private_reasoning`; `no_hidden_thinking_displayed=true` 30/30.
- Hash discipline: `final_coder_packet_hash == coder_received_packet_hash` on all 22 productive
  rows. `_packet_hash_match_status` in the trace reflects this.
- Copies preserved under `../receipts/` and `../traces/` for independent review.

## Source-of-truth model (CORRECT)

- Durable FIP-0 receipt is authoritative; FIP-6 trace is a projection. Verdict precedence in
  `_attach_fip0_truth_receipt` is fip5 > fip4 > fip3 > fip1 > fip2 > base. All 22 GOs are
  `GO: fip5_...` (real integrated), 0 foundation/preview GOs slipped through.

## LEAKAGE FINDING (MEDIUM)

`operator_trace.coder_trace.qwen.parser_result` includes `raw_output_excerpt` — the RAW Qwen
model output (verified: 824 chars of `{"action":"replace_file", "content_lines":[...]}` in the
`s1-04-todo` trace). So the FIP-6 operator_trace, which advertises
"operational_receipt_projection_no_private_reasoning", still surfaces raw coder model output.
Additionally the co-served full `receipt` (returned by both `/fip0-receipts/{id}` and
`/fip0-receipts/{id}/trace`) carries `raw_prompt` and, for FIP-5 rows, Hermes verifier
`raw_output_excerpt` and `input_summary.raw_prompt`. These endpoints are unauthenticated and
linked from `/coding`.

Note: a naive keyword scan also flagged `thinking`/`hidden`, but those are false positives from
the `no_hidden_thinking_displayed` field name. The genuine leak is `raw_output_excerpt`.

## Stale-latest / overwrite risk (source, not hit here)

- `run_id = fip0-<sha256(timestamp_to_second, task, target, route)[:16]>`. Identical prompt in
  the same second collides/overwrites. The battery used distinct prompts/targets so no collision
  occurred, but the risk is real.
- `latest` is `max(timestamp_string, mtime)`; a stale duplicate with a high timestamp can shadow.
  The canonical receipt dir already holds 190+ receipts including superseded duplicates.

## missing_fields behavior

- `_fip6_operator_trace_from_receipt` computes `missing_fields`; battery traces had complete
  field sets for the integrated rows.

## Recommendations

1. Remove `raw_output_excerpt` (and any raw model text) from the operator_trace projection;
   keep only hashes + status + bounded structured summaries.
2. Strip `raw_prompt`/raw excerpts from the served receipt body, or auth-gate the endpoints.
3. Replace the constant `no_hidden_thinking_displayed=true` with a real content scanner that
   sets the flag based on inspection.
4. Make `run_id` collision-proof (uuid/monotonic seq) and move superseded receipts to an archive
   subdir so `latest` cannot select a stale duplicate.
