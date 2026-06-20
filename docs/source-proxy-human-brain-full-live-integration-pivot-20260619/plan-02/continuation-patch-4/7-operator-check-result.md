# Operator Check Result

Operator was hardened to inspect lane-level proof.

It now fails if:

- Qwen lane is missing
- Qwen is not activated
- Qwen lacks live invocation
- Qwen lacks downstream consumption
- Qwen lacks consumer_event_id
- Qwen is metadata-only
- Verifier lane is missing
- Verifier result is not VERIFIED
- Verifier is advisory-only
- Verifier is preview-only
- Verifier is unverified
- Verifier lacks downstream consumption
- Verifier lacks consumer_event_id
- Task A is not PASS
- Patch 4 artifacts are missing
- Plan 3 artifacts exist

Result after artifacts and tests were present:

PASS Plan 2/6 operator check
