# Increment 1.1 Mac Preflight

Date: 2026-05-29

Scope:

- Mac node backup gate only.
- No Mac install, copy, backup, or repo initialization was run.

Checks run:

- `git diff --check`: PASS
- `git status --branch --short --untracked-files=normal`: PASS, existing dirty worktree recorded
- `restic snapshots`: PASS on Dell/source-server repo
- SSH reachability and Mac path check: PASS
- Mac restic availability check: NO-GO, no `restic` path/version printed
- Mac visibility of Dell Mac repo path: NO-GO

Observed Dell restic snapshots:

- `12865b16`: source-server file-level backup
- `cb127b36`: DB dump backup
- `8e09ed34`: Docker volume export backup

Observed Mac SSH:

```text
spirit-mac-mini.local
spiritmac
MAC_SPIRITOS_PATH_PRESENT
MAC_CANNOT_SEE_DELL_MAC_REPO_PATH
```

Result: NO-GO.

Reasons:

- Mac-side `restic` did not report as installed.
- Mac cannot see `/mnt/spirit-8tb/spiritos-backups/restic-repos/spirit-mac-mini`, so the existing Mac backup wrapper's planned repository path is not usable from the Mac.

Safety:

- No Mac backup ran.
- No Mac data was copied.
- No restic repo was initialized for Mac.
- No packages were installed.
- No DB dumps ran.
- No Docker volume exports ran.
- No Windows backup ran.
- No containers were stopped or restarted.
- No timers were installed.
- No cloud sync ran.
- No pruning/deletion ran.
- No commit/push ran.
- No secrets were printed.
