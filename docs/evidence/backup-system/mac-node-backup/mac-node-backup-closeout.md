# Mac Node Backup Closeout

Date: 2026-05-29

Status: NO-GO

Gate stopped at:

- Phase 1 / Increment 1.1 Mac preflight.

What worked:

- Dell/source-server restic repo is readable.
- Mac SSH alias `spirit-mac-mini` works.
- Mac checkout path `/Users/spiritmac/spiritos-worker/SpiritOS` exists.

What blocked the gate:

- Mac-side `restic` is not currently available, or at least did not report through `command -v restic && restic version`.
- Mac cannot see the Dell path `/mnt/spirit-8tb/spiritos-backups/restic-repos/spirit-mac-mini`.

Required next operator decision:

- Approve installing restic on the Mac and define the transport to the Dell backup repo, such as an approved Mac-visible mount, SFTP/restic REST server path, or Dell-side staging/pull design.

Update after restic-install approval:

- Mac is reachable and running macOS 15.7.7.
- `restic` is still not installed.
- Homebrew and MacPorts were not found in PATH or common install locations.
- No install command was run because no approved package manager or standalone binary path exists yet.
- Next required decision: approve a specific Mac install mechanism, for example installing Homebrew first, using MacPorts if Britton installs it, or providing a specific pre-approved restic binary/package path.

Safety:

- No Mac backup ran.
- No Mac data was copied.
- No Mac restic repo was initialized.
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
