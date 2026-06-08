# Increment 1.3 - Trial Mode Ban

## Ban contract implemented

`source_proxy/tasks/long_running.py` defines:

```text
allow_known_scaffold=false
allow_generic_scaffold=false
allow_deterministic_stub=false
allow_backend_generated_page=false
allow_fallback_to_pass=false
require_model_authored_diff=true
```

## Runtime behavior

- In live trial mode, if deterministic scaffold/fallback provenance appears, `propose_coder_agent_diff_payload_from_plan` returns a blocked payload.
- The blocked reason code is `scaffold_blocked_in_trial_mode`.
- The trial trust status becomes `invalid_scaffold_blocked`.
- Malformed or validation-failed model output does not fall back to deterministic scaffold in live trial mode.
- Normal non-trial bounded-create helper content remains available for future use, but it is not valid model-ability evidence.

## Self-check

- Scaffold/fallback cannot produce trial PASS: yes.
- Provider call plus backend scaffold cannot produce PASS: yes.
- Trial failure is honest: yes, blocked/needs-fix payload with reason code.
- Normal future fallback code preserved: yes.
