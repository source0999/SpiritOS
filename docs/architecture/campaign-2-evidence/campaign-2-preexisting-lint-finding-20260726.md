# Campaign 2 Pre-existing Lint Finding

status: `DEFERRED_BY_OPERATOR_DECISION_NOT_A_CAMPAIGN_2_REGRESSION`

## Finding

`npm run lint` exited `1` on 2026-07-26 with `78` errors and `109` warnings.
The output is retained at `/tmp/c2-lint.log` on Dell for this validation run.
This finding is outside the authorized Campaign 2 evidence-only scope and was
not fixed by Campaign 2.

## C2 diff proof

The complete committed Campaign 2 diff from `4e577218` through `c3f59492`
contains exactly these eight files:

1. `docs/architecture/campaign-2-evidence/c2-fpa-001-contract-2ecbb56d.json`
2. `docs/architecture/campaign-2-evidence/c2-rcpt-001-negative-nonconsumed-layer-20260726.json`
3. `docs/architecture/campaign-2-evidence/campaign-2-acceptance-matrix-20260726.md`
4. `docs/architecture/campaign-2-evidence/campaign-2-benchmark-authority-matrix-20260726.md`
5. `docs/architecture/campaign-2-evidence/campaign-2-operator-review-packet-20260726.md`
6. `scripts/run-campaign-2-full-pipeline-negative.py`
7. `source_proxy/benchmarks/full_pipeline_authority.py`
8. `source_proxy/tests/test_full_pipeline_authority.py`

None of the lint-failing files appears in this diff. The reported debt is in
the `docs/handoff/spiritflix-llm-pack/stage/` SpiritFlix handoff material,
`src/components/spiritflix/`, and the pre-existing coding files
`src/lib/coding/agent-trials-ui.ts` and
`src/lib/coding/spiritflix-admin-approval-binding.ts`. It is pre-existing on
the `4e577218` Campaign 1 acceptance base, is not a Campaign 2 regression, and
is escalated to the owning file areas.

## Build disposition

The installed Next `16.2.4` no longer supports `eslint.ignoreDuringBuilds` and
does not invoke ESLint from `next build`. A temporary attempt to use that
removed configuration was immediately reverted and was never committed. The
successful static build therefore used the unchanged `next.config.ts` while
this lint finding remained separately recorded and operator-deferred.

This documentation does not accept Campaign 2, does not alter the frozen
contract or negative receipt, and does not authorize Campaign 3.
