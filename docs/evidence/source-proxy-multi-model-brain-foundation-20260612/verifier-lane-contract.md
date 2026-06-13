# Verifier Lane Contract

The verifier-lane packet includes the original prompt, normalized intent, behavior contract, context summary, selected coder lane, changed files, generated preview path, test output, browser observation, receipt and retest refs, known failure modes, and any model claim.

Verifier output is advisory. It can return PASS, WARNING, NEEDS_FIX, HANDOFF, FAIL, or UNVERIFIED, but it cannot turn UNVERIFIED into PASS, trust Qwen self-explanation alone, override browser behavior proof, or act as a hidden benchmark hint provider.
