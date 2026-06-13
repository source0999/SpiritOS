# Verifier Lane Truth

`source_proxy/decision/verifier_lane.py` implements a verifier packet and output normalizer, but it is explicitly preview/advisory:

- `preview_only: True`
- `advisory_only: True`
- `model_calls_enabled: False`

The verifier preview guards against fake success by downgrading PASS without browser behavior evidence. That is good policy, but it is not a live Hermes/Gemma verifier call.

Recent Level 3/4 runs used deterministic browser behavior probes and evidence wrappers. They did not invoke Hermes/Gemma as verifier lanes. Level 4 per-prompt traces mark `gemma_hermes_invoked: false`.

Current status:

- Deterministic verifier/browser behavior evidence: LIVE.
- Model verifier lane: PREVIEW_ONLY / NOT_INVOKED.

Needed next:

- Keep deterministic browser evidence authoritative.
- Add verifier receipt packet creation for every artifact run.
- Only after receipts exist, optionally call Hermes or Gemma as advisory critic.
- Prevent advisory verifier from changing PASS without browser/retest proof.

Verifier proof should include:

- model/provider/alias
- prompt excerpt hash
- transcript path
- verifier packet path
- verifier output path
- browser evidence refs
- final verdict authority: deterministic/browser, not model self-report
