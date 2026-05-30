# Increment 2.3R Restic Init

Date: 2026-05-29

Environment used:

- `RESTIC_REPOSITORY=/mnt/spirit-8tb/spiritos-backups/restic-repos/source-server`
- `RESTIC_PASSWORD_FILE=/home/source/.config/spiritos-backup/restic-source-server.pass`

Checks run:

- `restic snapshots`: PASS command executed, repository was not initialized
- `restic init`: PASS
- `restic snapshots`: PASS after initialization
- `git diff --check`: PASS

Observed:

```text
Fatal: unable to open config file: stat /mnt/spirit-8tb/spiritos-backups/restic-repos/source-server/config: no such file or directory
Is there a repository at the following location?
/mnt/spirit-8tb/spiritos-backups/restic-repos/source-server
created restic repository 7226724f4b at /mnt/spirit-8tb/spiritos-backups/restic-repos/source-server
```

Post-init `restic snapshots` exited successfully and printed no snapshots, which is expected before the first backup.

Result: GO. Restic repo was initialized locally on the Dell 8TB drive. No cloud remote was configured.

Password contents were not printed.
