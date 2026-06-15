# FIP-5 Mini Context Pack

Status: GO

Scope: FIP-5 only. Required verification and bounded repair were wired after the accepted FIP-4 Qwen coding-only output. FIP-6 operator transaction trace was not started.

Accepted runtime receipts:

- Clean verifier PASS: `/home/source/SpiritOS/docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-c7e5a81bb99be214.json`
- Verifier-triggered repair PASS: `/home/source/SpiritOS/docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-988b78ba25538cea.json`
- Max-repair NO-GO: `/home/source/SpiritOS/docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-ea5af7def160c78c.json`
- Browser-authority NO-GO: `/home/source/SpiritOS/docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-98cae88a9ca55a17.json`
- Protected-path regression: `/home/source/SpiritOS/docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-122176b0aa824276.json`

Runtime model configuration:

- Gemma advisory lane: `gemma3n:e4b`
- Hermes critic lane: `hermes3:8b-abliterated`
- Hermes verifier lane: `hermes3:8b-abliterated`
- Qwen coder lane: `qwen2.5-coder:7b`

Proof summary:

- Clean PASS run `fip0-c7e5a81bb99be214`: Qwen coder was `used`, deterministic verifier passed with no failures, browser behavior was skipped as not relevant for the text target, Hermes verifier was a distinct `post_code_verifier` invocation with schema-valid `PASS`, and repair was skipped.
- Repair PASS run `fip0-988b78ba25538cea`: initial deterministic verifier required repair, one repair packet was sent to Qwen as `qwen_repair_as_coder_only`, the repair attempt was receipted, deterministic verifier passed after repair, Hermes verifier returned schema-valid `PASS`, and final verdict was GO.
- Max-repair run `fip0-ea5af7def160c78c`: deterministic failure persisted, two repair packets were sent to Qwen, the loop stopped at the max attempt count of 2, Hermes verifier returned `NEEDS_FIX`, and final verdict stayed hard NO-GO with operator intervention required.
- Browser-authority run `fip0-98cae88a9ca55a17`: deterministic verifier passed, but the HTML target required browser behavior evidence and no passing browser evidence existed. Browser behavior stayed authoritative, Hermes verifier returned `FAIL`, and final verdict stayed NO-GO.
- Protected-path regression `fip0-122176b0aa824276`: `.env` was blocked before Qwen, Qwen remained skipped, `coder_received_packet_hash` stayed empty, and changed files stayed empty.

Receipt semantics preserved:

- Deterministic verifier fields are present on FIP-5 receipts.
- Hermes verifier fields are distinct from Hermes critic fields: model, role, prompt hash, output hash, schema validity, verdict, and repair instructions are recorded separately.
- Hermes verifier cannot turn unverified output into PASS.
- Hermes verifier cannot override browser behavior failure.
- Repair attempts are bounded by `repair_max_attempts=2` by default.
- Repair packets go to Qwen as coder-only and do not grant Qwen verification authority.
- No hidden apply, commit, push, FIP-6 trace, TinyFish, or xersearch was added.

Checks:

- PASS: `python -m pytest source_proxy/tests/test_prompt_packet_context_metadata.py -q` (`40 passed`)
- PASS: `npm run typecheck -- --pretty false`
- PASS with line-ending warnings only: `git diff --check`
- PASS: restarted Linux `source-server` runtime checkout with `npm run proxy:https:lan`
- PASS: direct runtime POST/GET on `https://127.0.0.1:8787`
- PASS: by-run retrieval for all accepted FIP-5 proof receipts listed above

Next stop gate: Stop after FIP-5. FIP-6 requires Britton approval. Do not wire operator transaction trace, resume Level 3/4/5, add TinyFish, create xersearch, commit, or push from this pack.
