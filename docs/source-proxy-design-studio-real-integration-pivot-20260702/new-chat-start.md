# New Chat Start — Design Studio Real Integration Pivot

**Handoff target:** a fresh Codex/Claude chat that will execute the pivot.
**Active plan source:** `docs/source-proxy-design-studio-real-integration-pivot-20260702/`
**Deprecated prior:** `docs/source-proxy-design-studio-implementation-pivot-20260701/` (see its `DEPRECATED.md` — historical only, do not treat its Plan 14 GO as truth).

## What failed in prior Plan 14

A hardline audit found the prior Design Studio "implementation" was an advisory preview stub, not an integrated product lane:

- `src/app/v1/coding/design-studio/preview/route.ts` is hardcoded, `advisory_only:true`, `model_call_made:false`, `provider_call_made:false`, `sandbox_apply_authority:false`.
- `DesignStudioShell` makes zero network calls.
- `execute-approved` is unrelated to Design Studio.
- Design/DesignDNA/coder/critic packets are hardcoded literals.
- No screenshot artifact is produced, hashed, or consumed.
- Anti-template detection inspects caller-supplied text, not rendered output.
- Writeback helper has no production importer.
- Writeback test suite is red 2/10 (Windows path-sep).
- Plan 14 GO was built on docs/status/test existence, not runtime invocation or downstream consumption.

Verdict that triggered this pivot: `NO_GO_FAKE_GO_RISK`.

## What this new pivot is

A 12-plan real-implementation ladder (Plans 00–11) with a machine-checkable receipt validator, an artifact chain, browser-proof-from-`/coding` requirements, an anti-fake-GO contract, and status gated behind green. Full detail in `master-plan.md`.

Current status: **plan written only. No implementation performed.**

## Next action

**Ask Britton for permission before starting Plan 00 implementation.** Do not auto-start.

## Required execution protocol reminders (non-negotiable)

- Work exactly one increment at a time. No batching.
- Do not start the next increment until the current increment has a green receipt (`INCREMENT_GO_PROVEN`).
- Any red check, missing artifact path, or missing trace ID blocks forward progress.
- Source-text-only tests are not runtime proof. Route unit tests are not frontend proof. Backend curl is not browser proof.
- Every increment produces a receipt; every phase runs the receipt validator.
- The receipt validator (`scripts/coding/validate-design-studio-receipts.mjs`) is bootstrap-created in Plan 00.4 and mandatory from Plan 00.5 onward.
- Real `/coding` browser proof is required (Plan 01, 02, 10). A helper page is a sandbox target only, never the entrypoint.
- `execute-approved` is out of scope for Design Studio. One canonical sandbox-apply path to `/coding/design-demo` only.
- No Graphify / memory graph / new external dependency. Deferred to a separate future experiment.
- BLOCKED_ENV is an honest terminal state. Do not manufacture a provider lane to fake GO.

## Where to start when approved

1. Read `master-plan.md` end to end.
2. Start Plan 00.1 (current audit and baseline readback).
3. Plan 00.2 records the inherited red writeback test (`INHERITED_RED_WRITEBACK_PATH_SEPARATOR`).
4. Plan 00.3 fixes ONLY the path-separator normalization in `design-studio-obsidian-writeback.ts` (must go 8/10 → 10/10).
5. Plan 00.4 bootstraps the receipt validator + schemas + negative tests.
6. Plan 00.5 phase closeout regression.
7. Then Plan 01 seam discovery (highest-risk step).

Do not skip ahead. Each plan gates the next.
