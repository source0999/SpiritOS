# FIP-6 Mini Context Pack

Status: GO

Scope: FIP-6 only. Operator-visible prompt transaction trace was added as a projection of durable FIP-0/FIP-5 receipts. No model decision semantics were changed.

Approved surfaces added:

- Backend latest trace: `/v1/decisions/fip0-receipts/latest/trace`
- Backend by-run trace: `/v1/decisions/fip0-receipts/{run_id}/trace`
- App-origin latest trace proxy: `/v1/decisions/fip0-receipts/latest/trace`
- App-origin by-run trace proxy: `/v1/decisions/fip0-receipts/{run_id}/trace`
- `/coding` visible `Trace` link beside the receipt link

Trace source of truth:

- Every trace field is projected from the durable receipt JSON or from trace metadata about missing receipt fields.
- Trace authority label is `operational_receipt_projection_no_private_reasoning`.
- Hidden/private reasoning is not displayed.
- Missing receipt fields are listed in `missing_fields` and represented as `status=unknown`, `reason=receipt_field_missing`.

Accepted runtime proof receipts:

- Clean PASS trace proof: `/home/source/SpiritOS/docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-c7e5a81bb99be214.json`
- Repair trace proof: `/home/source/SpiritOS/docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-988b78ba25538cea.json`
- Max-repair NO-GO trace proof: `/home/source/SpiritOS/docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-ea5af7def160c78c.json`
- Browser-authority NO-GO trace proof: `/home/source/SpiritOS/docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-98cae88a9ca55a17.json`
- Protected/skipped-lane proof: `/home/source/SpiritOS/docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-122176b0aa824276.json`
- FIP-6 protected-path smoke POST proof: `/home/source/SpiritOS/docs/evidence/source-proxy-full-integration-pivot/fip-0-receipts/fip0-449e7937a5eda8ac.json`

Runtime proof summary:

- Clean PASS `fip0-c7e5a81bb99be214`: trace final verdict matched durable receipt, Qwen packet hash matched, deterministic verifier passed, Hermes verifier role was `post_code_verifier`, repair count was 0, TinyFish remained skipped, xersearch remained skipped.
- Repair PASS `fip0-988b78ba25538cea`: trace final verdict matched durable receipt, repair loop was used, repair attempt count was 1, one repair packet was visible, Qwen repair output was visible, Hermes verifier passed.
- Max-repair NO-GO `fip0-ea5af7def160c78c`: trace final verdict matched durable receipt, deterministic verifier stayed failed, Hermes verifier verdict was `NEEDS_FIX`, repair attempt count was 2, two repair packets were visible.
- Browser-authority NO-GO `fip0-98cae88a9ca55a17`: trace final verdict matched durable receipt, browser behavior status stayed failed, Hermes verifier verdict was `FAIL`, browser failure was not softened.
- Protected/skipped proof `fip0-122176b0aa824276`: trace showed Qwen skipped, coder hash missing by skip, TinyFish deferred, xersearch missing, and missing verifier fields were called out honestly.
- FIP-6 smoke POST `fip0-449e7937a5eda8ac`: direct runtime POST returned `NO-GO`, Qwen skipped, coder hash empty, and trace retrieval succeeded.

Checks:

- PASS: `python -m pytest source_proxy/tests/test_prompt_packet_context_metadata.py -q` (`43 passed`)
- PASS: focused backend FIP-6 trace aggregation tests in `source_proxy/tests/test_prompt_packet_context_metadata.py`
- PASS: focused app-origin trace route tests on Linux (`4 passed`)
- PASS: focused tests proving selected trace fields equal durable receipt fields
- PASS: focused tests proving skipped/blocked/failed lanes are displayed
- PASS: focused tests proving hidden/private reasoning fields are not emitted
- PASS: `npm run typecheck -- --pretty false`
- PASS with line-ending warnings only: `git diff --check`
- PASS: restarted Linux runtime checkout with `npm run proxy:https:lan`
- PASS: direct runtime POST/GET on `https://127.0.0.1:8787`
- PASS: by-run receipt and by-run trace retrieval for accepted FIP-6 proof receipts

Manual Britton checks:

- Authenticated app-origin browser proof was not available in-tool. Britton can open `/coding`, click `Trace`, and confirm it loads `/v1/decisions/fip0-receipts/latest/trace` from the authenticated app origin.

Hard stops honored:

- Did not start FIP-7.
- Did not resume Level 3/4/5.
- Did not add TinyFish.
- Did not create xersearch.
- Did not commit or push.

Next stop gate: Stop after FIP-6. FIP-7 requires Britton approval.
