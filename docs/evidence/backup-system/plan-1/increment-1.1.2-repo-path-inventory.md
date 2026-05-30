# Increment 1.1.2 Repo Path Inventory

Date: 2026-05-29
Repo path: `/home/source/SpiritOS`

Backup-relevant tracked source candidates:

- `src/`
- `scripts/`
- `backend/`
- `scout/`
- `docs/`
- `config/`
- compose files such as `docker-compose*.yml`
- package and tool config files at repo root

Evidence and operational docs candidates:

- `docs/evidence/`
- `docs/runbooks/`
- `docs/backup-system/`

Runtime backup candidates that GitHub/Repomix alone do not protect:

- `.spirit-backups`
- `source_proxy/.spirit-backups`
- `source_proxy/data`
- root runtime data when present and explicitly reviewed
- Scout runtime data
- Docker named volumes
- `backend/searxng_data`
- evidence, receipts, logs, compose files, and config examples

Generated or rebuildable exclusions:

- `.git/`
- `node_modules/`
- `.next/`
- `dist/`
- caches
- Repomix output files
- build artifacts

Secret handling:

- Secret-shaped paths such as `.env`, `.env.local`, private keys, tokens, credentials, certificates, and password files are candidates by path/presence only.
- Secret file contents must not be printed, copied, or backed up without a separate Britton approval gate.

Manual checks to rerun are the exact increment checks from the PIVOT request. No secret contents are required or expected.
