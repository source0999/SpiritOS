# Review And Gate Contract

Future GLM implementation owns edits. Future Codex review is independent and must not silently fix GLM changes.

Codex Quick Gate checks scope, focused checks, live invocation, downstream consumption, forbidden-state scan, and causal identifiers. Required identifiers: `task_id`, `trace_id`, `invocation_event_id`, `consumer_event_id`, `consumer_subsystem`, and task-state fields changed.

Deep review is mandatory at every plan boundary, first Obsidian write, first Mac write, every authority expansion, route migration, checkpoint/recovery, repair execution, failed Quick Gate, and each plan closeout. Allowed review verdicts are `GO`, `NEEDS_FIX`, `BLOCKED_HUMAN`, and `BLOCKED_ENV`; `PARTIAL_GO` is forbidden.
