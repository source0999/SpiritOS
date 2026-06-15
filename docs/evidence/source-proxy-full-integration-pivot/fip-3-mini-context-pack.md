# FIP-3 Mini Context Pack

Status: GO

Scope: FIP-3 only. Local non-coding model lanes were wired after FIP-1 context and FIP-2 research into the real `/coding` / `/v1/decisions/prompt-packet` truth receipt path.

Accepted runtime receipts:

- Search-needed proof: `/home/source/SpiritOS/docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-5c52b7eee31f37ff.json`
- No-search proof: `/home/source/SpiritOS/docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-da05ed097be14470.json`
- Failed-model honesty proof: `/home/source/SpiritOS/docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-2ea314bbf5a63785.json`

Runtime model configuration:

- Gemma advisory lane: `gemma3n:e4b`
- Hermes critic lane: `hermes3:8b-abliterated`
- Hermes verifier lane: reserved only, future FIP-5, non-authoritative
- Qwen coder lane: skipped

Inventory notes:

- `gemma3n:e4b` present.
- `hermes3:8b-abliterated` present and returned valid JSON.
- `hermes4:latest` present but returned empty output during direct and receipt-path probes, so it was not used for the accepted FIP-3 GO receipts.
- `qwen2.5-coder:7b` present but not used for pre-coder reasoning or coding.

Receipt semantics preserved:

- FIP-0 truth receipt path remains the source of record.
- FIP-1 context lanes emit `used`, `skipped`, `blocked`, or `failed`.
- FIP-2 search lanes remain separate: repo/router research is not live SearXNG.
- SearXNG is only `used` when a live local provider query executes.
- Scout emits an honest status; accepted proofs recorded `skipped` with attributable reason.
- TinyFish remains `deferred_cloud_requires_britton_approval`.
- xersearch remains `missing_alias_do_not_create`.
- `coder_received_packet_hash` remains empty only while `qwen_coder_status=skipped`.

Accepted proof summary:

- Search-needed run `fip0-5c52b7eee31f37ff`: `search_needed=true`, `searxng_status=used`, `searxng_result_count=1`, `gemma_status=used`, `hermes_critic_status=used`, `qwen_coder_status=skipped`.
- No-search run `fip0-da05ed097be14470`: `search_needed=false`, `searxng_status=skipped`, `gemma_status=used`, `hermes_critic_status=used`, `qwen_coder_status=skipped`.
- Failed-model run `fip0-2ea314bbf5a63785`: Hermes-4 alias produced invalid/empty output and receipt recorded `hermes_critic_status=failed`, final verdict `NO-GO: fip3_local_model_lane_failed`.

Next stop gate: FIP-4 only after Britton approval. Do not activate Qwen coder, Hermes verifier authority, repair loop, operator trace, TinyFish, or xersearch from this pack.
