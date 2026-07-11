# SpiritOS Worktree Rules

Before working, identify the requested project and read `docs/dev-setup/worktree-manifest.md`. Run `git worktree list --porcelain`, confirm the worktree path, branch, HEAD, and scoped status, then work only in the project-owned worktree.

- Do not borrow, stage, reset, restore, stash, or format unknown dirty changes.
- Report task-scoped dirt separately from whole-worktree dirt. A task-level `commit_safe` result never makes a whole repository commit-safe.
- Keep Source Proxy, SpiritFlix, generated evidence, fixtures, media data, and runtime state separate. Never commit Source Proxy and SpiritFlix changes together without an explicit shared-file justification.
- Check the backend and frontend process CWD before runtime testing. A passing service from a different worktree is not proof for the edited worktree.
- Use the project-specific tests and harnesses; do not scan all SpiritOS projects unless the task requires it.
- Stage explicit paths only. `git add -A` is prohibited.
- Preserve unknown work. If the implementation target drifts from the requested repository-cleanup objective, stop that implementation path and return to cleanup scope.
