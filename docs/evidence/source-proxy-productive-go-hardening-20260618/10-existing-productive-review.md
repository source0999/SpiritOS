# Existing Productive Review

## Existing Gate

`source_proxy/api/decision.py` computes receipt truth in `_structured_verdict_fields`.

Before this patch, `productive` was a single boolean requiring:

- `final_verdict` starts with `GO:`
- `coder_path == fip4_real`
- deterministic verifier passed
- browser or functional behavior verifier passed
- no protected-path block
- no degraded lanes

The browser verifier patch at `007ea217` made `verification_real.browser` consume structured browser truth, so legacy `status=used/passed=true` no longer counts as behavior proof.

## Gap

The receipt still lacked an explicit productive truth schema. A caller could see `productive=false`, but not whether the result was `PARTIAL_GO`, `NO_GO`, `BLOCKED`, `SKIPPED`, or `UNSUPPORTED`, nor which evidence dimensions were present.

## Patch Target

Keep `productive` as the compatibility boolean, but make it an alias of the stricter `productive_go` field. Add explicit fields:

- `productive_status`
- `productive_go`
- `productive_reasons`
- `productive_blockers`
- `productive_evidence`

Raw context: `raw/10-evidence-read.txt`, `raw/11-source-proxy-files.txt`, `raw/12-productive-rg.txt`.
