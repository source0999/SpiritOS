#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/spirit-backup-common.sh
source "${SCRIPT_DIR}/lib/spirit-backup-common.sh"

for arg in "$@"; do
  case "${arg}" in
    --dry-run) SPIRIT_BACKUP_MODE=dry-run ;;
    *) fail "Unknown argument: ${arg}" ;;
  esac
done

cat <<'MANIFEST'
# SpiritOS Backup Candidate Manifest v0.1

[include/source]
/home/source/SpiritOS/src
/home/source/SpiritOS/scripts
/home/source/SpiritOS/backend
/home/source/SpiritOS/scout
/home/source/SpiritOS/docs
/home/source/SpiritOS/config
/home/source/SpiritOS/docker-compose*.yml

[include/runtime]
/home/source/SpiritOS/.spirit-backups
/home/source/SpiritOS/source_proxy/.spirit-backups
/home/source/SpiritOS/source_proxy/data
/home/source/SpiritOS/backend/searxng_data
/home/source/SpiritOS/backend/volumes
/home/source/SpiritOS/logs
/home/source/SpiritOS/receipts

[include/evidence]
/home/source/SpiritOS/docs/evidence

[include/docker]
source_postgres_data
ollama_data
whisper_cache
openedai_voices
searxng_data

[include/node-mac]
spirit-mac-mini:/Users/spiritmac/spiritos-worker/SpiritOS
spirit-mac-mini:/Users/spiritmac/spiritos-worker/pre-git-backups

[include/node-windows]
C:\\Projects
Known SpiritOS Windows agent/config paths only

[exclude/rebuildable]
node_modules
.next
dist
coverage
.turbo
.cache
repomix-output.*
*.tsbuildinfo

[exclude/unsafe-secret-content]
.env
.env.local
*.pem
*.key
*token*
*credential*
*password*
certificates

Mode: dry-run/read-only manifest; no backup is performed.
MANIFEST
