# Probe Capability Audit

Status: complete before run.

## Existing Probe Capability

The existing Gate B runner uses `docs/evidence/source-proxy-simple-blunt-diagnostics-after-multi-model-foundation-20260612/anti_tailoring_behavior_probe.mjs`.

It can fairly test many Level 3 behaviors: preview opening, one visible state change, numeric result updates, theme computed state change, basic password feedback, basic player control, and canvas pixel mutation.

It cannot by itself fairly score all Level 4 prompts because several probes stop after one behavior observation. Examples: calculator verifies a numeric update but not reset; player verifies one control change but not next episode; weather verifies weather-like text/control change but not both city and F/C; notes/checklist verify text persistence more strongly than edit/delete or packed-count changes.

## Per-Prompt Fairness

- `level4-clean-01`: partly fair with existing timer probe; existing probe starts and touches pause/stop, but does not require reset or finished-load history.
- `level4-clean-02`: existing probe can test calculation, but not reset.
- `level4-clean-03`: existing probe can test theme/palette only, not text size.
- `level4-clean-04`: existing probe can test add/list text, but not reliably check toggle plus packed count.
- `level4-clean-05`: existing probe can test weather-like content/control change, but not city switch plus unit toggle.
- `level4-clean-06`: existing probe can test play/pause state change, but not next episode.
- `level4-clean-07`: existing probe can test a click state change, but not add set plus reps/total.
- `level4-clean-08`: existing probe can test memo add/text persistence, but not edit/delete plus saved count.
- `level4-clean-09`: existing probe can test strength feedback, but not show/hide.
- `level4-clean-10`: existing probe can test drawing pixels, but not color/brush or clear.

## Evidence-Only Wrapper Decision

A Level 4 evidence-only wrapper is needed and allowed.

Wrapper path: `docs/evidence/source-proxy-level-4-first-hard-artifact-proof-20260613/level4_behavior_probe.mjs`

The wrapper is created under the evidence folder before the run. It only opens disposable preview files, performs predefined browser interactions for the locked prompt families, and writes JSON/HTML/trace evidence. It does not patch Source Proxy runtime, does not patch generated artifacts, does not change the runner, does not change repair behavior, does not change prompt strings, and does not activate cloud fallback.

The wrapper defines Level 4 behavior scoring before the run. Applying it after generation does not change scoring rules after seeing results.

## False-Pass Risk

Without the Level 4 wrapper there is a material risk of false PASS because the existing probe can mark a run PASS after only one interaction when Level 4 requires at least two meaningful behavior observations where possible.
