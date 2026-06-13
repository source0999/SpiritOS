# Step 2 Failure Analysis

- Weather baseline was a true artifact failure: static labels without plausible populated values.
- Habit baseline was a verifier false negative risk: checkbox state changed even when body text did not. The generic browser verifier now records checked before/after state.
- Repair/report hardening was generic: behavior proof now carries expected, actual, and passed fields; tracker verification inspects checkbox state.
