# Increment 1.1.1 Evidence Root

Date: 2026-05-29
Repo path: `/home/source/SpiritOS`
Branch: `main`
HEAD: `ac1c6ddf7cf2d71739801a13c46a3f1f3426ea26`

Dirty status before backup-system work: existing unrelated changes were present in `_reference/`, `docs/evidence/mac-worker-hardening/`, `docs/mac-worker-operator-contract.md`, `docs/plan-index.md`, `package*.json`, `playwright.config.mjs`, `scripts/mac-worker/`, `src/`, `.codex-smoke/`, `scripts/agent-trials/`, and related trial docs/tests.

Backup-system scope created:

- `docs/evidence/backup-system/plan-1/`

Runtime data was not altered.

Manual checks to rerun:

```bash
cd /home/source/SpiritOS
git status --branch --short --untracked-files=normal
git rev-parse HEAD
test -d docs/evidence/backup-system/plan-1 && echo EVIDENCE_ROOT_PRESENT
git diff --check
```

GO evidence target: evidence root exists, HEAD recorded, backup-system changes stay in allowed scope, diff check passes.
