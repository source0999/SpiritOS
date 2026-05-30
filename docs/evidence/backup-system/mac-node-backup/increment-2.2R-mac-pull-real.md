# Increment 2.2R Mac Pull Real

Date: 2026-05-29

Command:

- `rsync -avz --delete` from `spirit-mac-mini:/Users/spiritmac/spiritos-worker/SpiritOS/`
- Destination: `/mnt/spirit-8tb/spiritos-backups/staging/spirit-mac-mini/SpiritOS/`

Exclusions:

- `.git/`
- `node_modules/`
- `.next/`
- `dist/`
- `.env`
- `.env.*`
- `*.pem`
- `*.key`
- `id_rsa`
- `id_ed25519`

Checks run:

- real rsync pull into Dell staging: PASS
- `find ... -maxdepth 3 -type f | sort | head -120`: PASS
- secret-shaped filename count check: PASS
- staged file count check: PASS
- `git diff --check`: PASS

Observed:

```text
sent 35,831 bytes  received 18,352,239 bytes
total size is 34,204,171
SECRET_SHAPED_FILE_COUNT=0
MAC_STAGING_FILE_COUNT=1534
```

Result: GO. Mac checkout files were copied into Dell staging. No secret-bearing files matching the excluded patterns were copied. No live Mac files were modified.
