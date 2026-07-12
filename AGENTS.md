# SpiritOS Bootstrap Rules

Before editing, restate the requested objective and identify its product scope: Source Proxy, SpiritFlix, a named shared area, or read-only cross-repository architecture.

1. Read `docs/dev-setup/worktree-manifest.md`, then the selected section of `docs/dev-setup/context-map.md`.
2. Verify the named worktree, branch, HEAD, and scoped status. Use SSH alias `spirit` for `/home/source/**`, Linux processes, archives, native tests, and service identity; `Z:\` is only the SMB view of SpiritFlix.
3. Do not silently switch projects or borrow dirty work. Report scoped status separately from whole-worktree status; task-level `commit_safe` never means the repository is safe to commit.
4. Keep Git hygiene, repository architecture, and product behavior as distinct objectives. A read-only architecture audit does not edit architecture.
5. Start from the project's **Minimal context** in `docs/dev-setup/project-entrypoints.md`; justify any expansion. Do not scan all branches, products, evidence, media, or history by default.
6. Use only the selected project's test and harness entries in `docs/dev-setup/test-registry.md`. Verify process CWD, branch, and HEAD before accepting runtime results.
7. Maintain the concise scope ledger in `docs/dev-setup/agent-scope-and-drift-policy.md`; reload it after compaction rather than replaying discovery.
8. Block objective, project, host, runtime, discovery, compaction, and easier-task-substitution drift as defined in that policy.
9. Never claim a Dell path or service is unavailable until configured access has been checked. Never replace the requested objective with an easier harness.
10. Do not stage, reset, restore, stash, format, or clean unknown work. Use explicit paths only; `git add -A` is prohibited.
11. Generated media, fixtures, browser evidence, runtime databases, caches, backups, and queues are runtime/archive state unless a named receipt says otherwise.
12. Finish with the required focused validation, scoped status, explicit handoff, and a local commit only when authorized.

Operational detail lives in `docs/dev-setup/`; those Markdown files are intentionally manual references, not extra Codex configuration formats.
