# FIP-4 Mini Context Pack

Status: GO

Scope: FIP-4 only. Final coder packet assembly and Qwen coding-only execution were wired after the accepted FIP-1 context lanes, FIP-2 research lanes, and FIP-3 Gemma/Hermes pre-coder lanes. FIP-5 verifier authority and repair loop remain skipped.

Duplicate-work check:

- One active Linux runtime session was present: `source-proxy-lan`.
- Earlier nearby receipts were sequential proof attempts, not concurrent active work from another Codex thread.
- Receipts where FIP-5 activated or Gemma failed schema validation are not accepted for this pack.

Accepted runtime receipts:

- No-search coding proof: `/home/source/SpiritOS/docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-36deb32ba4fdb2a0.json`
- Search-needed honesty proof: `/home/source/SpiritOS/docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-52e787f2903ff57e.json`
- Protected-path enforcement proof: `/home/source/SpiritOS/docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-8a633b11eb895d6e.json`

Runtime model configuration:

- Gemma advisory lane: `gemma3n:e4b`
- Hermes critic lane: `hermes3:8b-abliterated`
- Qwen coder lane: `qwen2.5-coder:7b`
- Hermes verifier lane: skipped/reserved for FIP-5

Accepted proof summary:

- No-search run `fip0-36deb32ba4fdb2a0`: `final_verdict=GO: fip4_qwen_coding_only_execution_complete`, `search_needed=false`, `searxng_status=skipped`, `scout_status=skipped`, `gemma_status=used`, `hermes_critic_status=used`, `hermes_verifier_status=skipped`, `repair_loop_status=skipped`, `qwen_coder_status=used`, changed file `docs/fip4-runtime-target.txt`, and `coder_received_packet_hash` matched `final_coder_packet_hash` (`cef2e9e42f022a01fa2c6240acefa412c8822b3c11f0bf9fe47afa32d05dfafc`).
- Search-needed run `fip0-52e787f2903ff57e`: `final_verdict=GO: fip4_qwen_coding_only_execution_complete`, `search_needed=true`, research packet hash `3620e0435b7689a0bca759040d52387eed83a253badac281d8d2e3bfe18e6c0e` was included in context, Qwen received the exact final coder packet, and `coder_received_packet_hash` matched `final_coder_packet_hash` (`7f5fc879350c24e7b7e087b130fb4452c28fa3120b5fbf7ec2febbd130970d92`). SearXNG was honestly `blocked` because the provider returned no usable http/https results for the query; Scout was honestly `blocked` on timeout.
- Protected-path run `fip0-8a633b11eb895d6e`: `.env` was blocked before Qwen, Qwen remained skipped, `coder_received_packet_hash` stayed empty, and changed files stayed empty.
- Parser proof: focused test `test_fip4_malformed_qwen_output_is_rejected` proves malformed/non-action Qwen output is rejected; `test_fip4_gemma_acceptance_criteria_parser_accepts_model_variants` proves recoverable Gemma criteria variants do not cause false schema failure.

Receipt semantics preserved:

- `final_coder_packet_hash` is present on accepted FIP-4 coding receipts.
- `coder_received_packet_hash` is present and non-empty only when Qwen actually received the final coder packet.
- Accepted FIP-4 coding receipts prove Qwen received the exact final coder packet by matching `coder_received_packet_hash == final_coder_packet_hash`.
- Malformed or non-action Qwen output is rejected and does not claim successful coding.
- Protected or forbidden paths are blocked before Qwen and do not receive a coder hash.
- Hermes verifier remains skipped/reserved for FIP-5.
- Repair loop remains skipped.
- TinyFish remains deferred.
- xersearch remains missing and was not created.

Checks:

- PASS: Linux runtime checkout full test file: `.venv-source-proxy/bin/python -m pytest source_proxy/tests/test_prompt_packet_context_metadata.py -q` (`49 passed`)
- PASS: focused FIP-2/FIP-4 tests in `source_proxy/tests/test_prompt_packet_context_metadata.py` (`10 passed`)
- PASS: `npm run typecheck -- --pretty false`
- PASS with line-ending warnings only: `git diff --check`
- PASS: restarted Linux `source-server` runtime checkout with `npm run proxy:https:lan`
- PASS: direct runtime POST/GET on `https://127.0.0.1:8787`
- PASS: by-run retrieval for `fip0-36deb32ba4fdb2a0`
- PASS: by-run retrieval for `fip0-52e787f2903ff57e`
- PASS: by-run retrieval for `fip0-8a633b11eb895d6e`
- NOTE: full `python -m pytest source_proxy/tests/test_prompt_packet_context_metadata.py -q` timed out twice on the Windows SMB checkout, but the required Linux runtime checkout run passed.

Next stop gate: Stop after FIP-4. FIP-5 requires Britton approval. Do not activate Hermes verifier authority, repair loop, operator transaction trace, TinyFish, xersearch, or Level 3/4/5 continuation from this pack.
