# Increment 3.3 - Context Packet Hardening

Status: passed.

Added safe coder context packet summary in `source_proxy/tasks/long_running.py`.

Summary fields:
- user prompt excerpt
- selected target candidates
- selected target
- allowed files
- forbidden files
- protected paths
- repo snippet summaries with path/kind/chars/sha256/line range
- Obsidian context diagnostics summary
- model/provider/runtime route
- trial mode flags
- scaffold/fallback ban flags
- expected output format
- checks that will run
- rollback/reversal availability
- secrets policy

Prompt-packet endpoint now exposes these fields in `context_metadata` without dumping full file contents or raw Obsidian notes.

Live proof:
- `/v1/decisions/prompt-packet` after source-proxy restart returned `has_context_packet_summary=true`.
- `context_metadata` included `allowed_files`, `checks_that_will_run`, `expected_output_format`, `obsidian_context_summary`, `protected_paths`, `rollback_reversal_available`, `scaffold_fallback_ban_flags`, `selected_target`, and `trial_mode_flags`.

Manual/self-check:
- Context packet can be summarized safely.
- Full source snippets are not dumped into `relevant_context`.
- Secret-shaped paths remain omitted/blocked by existing packet and path policy.
- The model is told to produce strict JSON replacement content; backend generates diffs.
