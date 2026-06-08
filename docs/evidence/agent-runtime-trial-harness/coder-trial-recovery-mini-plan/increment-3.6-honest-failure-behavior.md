# Increment 3.6 - Honest Failure Behavior

Status: passed for focused Gate 3 paths.

Added/verified diagnostics:
- `model_output_usable=false` on blocked Coder payloads.
- `scaffold_or_fallback_blocked=true` when scaffold/fallback contamination is blocked.
- `recommended_next_action` on blocked payloads.

Recommendations include:
- ask for clarification or regenerate Architect context
- retry with stricter output contract or stronger model
- regenerate with allowed files and protected-path block
- retry model-authored output only
- check model route or use configured stronger model
- provide more repo context or retry with validation feedback
- inspect file manually or retry with narrower context

Manual/self-check:
- Failures do not hide model weakness.
- `provider_call_made=true` is not treated as proof of model ability.
- Scaffold/fallback is not applied as PASS in live trial mode.
- Failed tasks are not called PASS.
