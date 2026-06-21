# Stage 4R6 Recovery Runner Check

`_stage4r_runner.py` already contains the required Stage 4R6 recovery capabilities:

- strict JSON / Ollama format-mode attempt if available: present in the packet call.
- JSON parse cleanup only: present through JSON-object extraction and validation; missing packet substance is not filled in by the runner.
- repair prompt loop: present with up to three live packet attempts.
- raw attempt files: present as `<prompt>.decision_packet.attempt<N>.raw.json`.
- raw repair files: present as `<prompt>.decision_packet.repair<N>.raw.json`.
- decision packet validator: present in `validate_decision_packet`.
- renderer only after packet validation: present; unvalidated packets produce NEEDS_FIX text for grading instead of renderer output.
- hardened grader still runs: present; `grade(...)` computes final status after work product generation.
- A2/A9 query variants: present via `A2_QUERY_VARIANTS`, `A9_QUERY_VARIANTS`, and `run_research_variants`.
- A5 Mac evidence bundle: present via Mac worker plus read-only capability probe and Mac evidence summary.

No runner patch was required before the recovery rerun.
