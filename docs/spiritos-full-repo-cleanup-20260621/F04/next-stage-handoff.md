# F04 -> F05 Handoff

**Status:** INTERNAL_GO_PENDING_SECONDARY_REVIEW

## F04 hands to F05
- `source_proxy/decision/packet_decomposition.py` provides generic local-only decomposition.
- `source_proxy/decision/packet_templates/` exposes a compatibility import surface for the F04 packet wording.
- `prompt_packet.py` attaches `local_decomposition` only when F3 dry-run recommendation is `LOCAL_DECOMPOSITION_RECOMMENDED`.
- Sub-packets validate independently and expose evidence requirements, validation focus, and F1 failure classes.

## F05 can begin once
- F04 commit is created and worktree is clean.
- F01-F04 statuses are `INTERNAL_GO_PENDING_SECONDARY_REVIEW`.

## Carry-forward for F05
- Keep `api/decision.py` behavior-preserving and avoid line-count-only refactors.
- Do not change receipt shape, FIP semantics, final status, trace/consumer behavior, or `fake_go_detected`.
- Broad `source_proxy/tests` timeout remains an F10 caveat, not a PASS.
