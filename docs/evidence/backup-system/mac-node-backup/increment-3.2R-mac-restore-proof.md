# Increment 3.2R Mac Restore Proof

Date: 2026-05-29

Checks run:

- isolated restore target creation under `/mnt/spirit-8tb/spiritos-backups/restore-drills/`: PASS
- Mac snapshot lookup by tag `spiritos-mac-node`: PASS
- `restic restore "$mac_snapshot" --target "$target" --include "/mnt/spirit-8tb/spiritos-backups/staging/spirit-mac-mini/SpiritOS/**"`: PASS
- restored file listing by path only: PASS
- restored file count check: PASS
- restored secret-shaped filename count check: PASS
- `git diff --check`: PASS

Observed:

```text
MAC_SNAPSHOT=b9761b0c
Target=/mnt/spirit-8tb/spiritos-backups/restore-drills/mac-node-20260529T193726Z
Summary: Restored 1862 / 1857 files/dirs (32.620 MiB / 32.620 MiB) in 0:00
RESTORED_FILE_COUNT=1534
RESTORED_SECRET_SHAPED_FILE_COUNT=0
```

Result: GO. Mac backup restored into an isolated restore-drill path, restored file count is greater than zero, and no secret-shaped excluded files were restored.

Safety:

- Nothing was restored over live Mac or Dell repo paths.
- No file contents were printed.
- No secrets were printed.
