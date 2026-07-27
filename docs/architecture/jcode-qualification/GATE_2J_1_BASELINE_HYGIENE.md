# Gate 2-J.1 Baseline Hygiene

status: `CHARACTERIZED_NOT_GREEN`

## Reproduction environment

| Field | Value |
|---|---|
| Worktree | `/home/source/SpiritOS-source-proxy-jcode-qualification-20260726` |
| Branch/base before 2-J.0 commit | `codex/source-proxy-jcode-qualification-20260726` / `1641ddb1` |
| Interpreter | `/home/source/SpiritOS-source-proxy-20260711/.venv-source-proxy/bin/python` |
| Python | `3.12.3` |
| Full-pack command | `python -m pytest -q source_proxy/tests/test_coding_regression_pack.py` |

The qualification worktree deliberately has no borrowed `.venv-campaign1`
link. The absolute Source Proxy venv is the reproducible interpreter for this
baseline command.

## Result

The full coding regression pack produced `136 passed`, `3 failed`, and `46`
subtests passed. The failing expectations are:

1. `test_bounded_proposal_diff_preview_ignores_json_envelope_requirements`
2. `test_prompt_packet_live_trial_creates_hidden_allowed_agent_lab_target`
3. `test_prompt_packet_live_trial_reuses_hidden_allowed_existing_agent_lab_target`

These tests exercise existing preview and agent-lab replacement validation
behavior, not `source_proxy.jcode`. The JCode seam has no production import and
its own focused suite passed separately.

The historically order-sensitive approval test
`test_approved_apply_moves_to_post_verification_state_only_after_approval`
passed in isolation (`1 passed`). This is recorded as an order-pollution
observation, not as a reason to call the complete pack green.

## Gate disposition

Gate 2-J.1 is complete as baseline characterization. No production behavior was
changed, no existing test was relaxed, and no JCode execution is authorized.
The exact command above is the deterministic reproduction command for later
gates. Gate 2-J.2 may now address filesystem containment independently.
