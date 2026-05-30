# Increment 2.1R Mac Pull Dry-run

Date: 2026-05-29

Command:

- `rsync -avzn --delete` from `spirit-mac-mini:/Users/spiritmac/spiritos-worker/SpiritOS/`
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

- rsync dry-run: PASS
- `head -120 /tmp/spiritos-mac-rsync-dry-run.txt`: PASS
- `git diff --check`: PASS

Observed:

- Dry-run listed expected repo files such as `README.md`, `package.json`, `backend/docker-compose.yml`, `docs/`, `src/`, and related source/docs paths.
- Dry-run summary reported total size around `34,204,171` bytes.

Result: GO. Dry-run showed expected Mac files, excluded secret-bearing patterns, and did not copy data.

Safety:

- No actual copy occurred.
- No file contents were printed.
- No secret contents were printed.
