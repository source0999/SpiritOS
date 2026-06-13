# Risk and Permission Rules

## Allowed by v0.2 after phase approval

- Read existing evidence and source files needed for the approved phase.
- Write approved docs or focused implementation files for that phase only.
- Run local tests or static checks needed to verify that approved phase.
- Use disposable generated artifact workspaces for local repair attempts, if Phase 5 is approved.
- Produce handoff packets when local work is failed, unsafe, or out of scope.

## Forbidden without separate Britton approval

- Production file repair.
- Source Proxy implementation before the relevant phase is approved.
- Provider/API usage.
- Codex live worker starts.
- Local-model worker starts outside an approved path.
- Obsidian writes.
- Git operations: branch, commit, push, stash, reset, checkout, clean, stage.
- Hidden background jobs.
- Automatic escalation to high usage.
- Broad `/coding` UI rebuild.
- Full multi-lane benchmark execution.
- Full repo-wide brain revamp.

## Disposable workspace rule

Local repair is allowed only in disposable generated artifact workspaces with explicit path guards. The repair loop must reject paths outside the allowed workspace and must record every changed file, diff, transcript, and attempt count.

## Provider and escalation rule

The local route cannot silently escalate to paid/API/Codex/high-usage execution. If local repair fails or needs a stronger route, v0.2 must produce a handoff packet that asks for approval.

## Truth rule

Final PASS requires verified behavior when behavior is required. Unverified or failed behavior cannot become PASS because a route returned GO, a preview opened, or files were created.
