# Increment 3.1 - Runtime Freshness

Status: passed with focused source-proxy restart.

Git state captured:
- Branch: `lane/coding-human-trial-runner-polish-20260530-112512`, ahead 14.
- Dirty work existed before Gate 3 and was preserved. No reset, stash, clean, or unrelated overwrite was done.

Runtime checks:
- `/coding`: `200`, length `48285`.
- `/v1/coding/runs/active`: `200`, `{"run":null}`.
- `/v1/coding/agent-lab-baseline`: `200`, `baseline_clean_for_fresh_suite=true`.
- `/v1/self/status`: `200`, manifest `2.7A-1`.
- `/healthcheck`: `200`.

Freshness finding:
- Initial restart helper left the old source-proxy PID running.
- Recreated `source-proxy-lan` tmux session manually with the same uvicorn command.
- Fresh source proxy PID after restart: `2110971`.

Live field proof after restart:
- Prompt packet POST returned `has_context_packet_summary=true`.
- `model_output_classification=model_markdown_code_block`.
- `generation_source=model`.
- `diff_source=backend_diff_from_model_authored_replacement`.
- `trial_result_trust_status=model_authored_diff_proven`.
- `context_metadata` includes Obsidian, allowed files, forbidden files, protected paths, checks, expected output format, trial flags, scaffold/fallback ban flags, selected target, and rollback availability.

Self-check:
- No unrelated route was intentionally changed.
- Frontend and source proxy are live on the LAN.
