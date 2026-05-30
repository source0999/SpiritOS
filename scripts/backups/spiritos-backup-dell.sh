#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/spirit-backup-common.sh
source "${SCRIPT_DIR}/lib/spirit-backup-common.sh"

for arg in "$@"; do
  case "${arg}" in
    --dry-run) SPIRIT_BACKUP_MODE=dry-run ;;
    --real) SPIRIT_BACKUP_MODE=real ;;
    *) fail "Unknown argument: ${arg}" ;;
  esac
done

RESTIC_REPOSITORY="${RESTIC_REPOSITORY:-/mnt/spirit-8tb/spiritos-backups/restic-repos/source-server}"
REPO_ROOT="${REPO_ROOT:-/home/source/SpiritOS}"

log "Dell/source-server backup planner mode=${SPIRIT_BACKUP_MODE}"
if ! command_exists restic; then
  warn "restic not found; install requires APPROVAL REQUIRED before any real backup."
fi
findmnt /mnt/spirit-8tb >/dev/null 2>&1 || warn "/mnt/spirit-8tb is not mounted or not visible"

EXCLUDES=(
  --exclude node_modules
  --exclude .next
  --exclude dist
  --exclude coverage
  --exclude .turbo
  --exclude .cache
  --exclude 'repomix-output.*'
  --exclude '*.tsbuildinfo'
)

INCLUDES=(
  "${REPO_ROOT}/src"
  "${REPO_ROOT}/scripts"
  "${REPO_ROOT}/backend"
  "${REPO_ROOT}/scout"
  "${REPO_ROOT}/docs"
  "${REPO_ROOT}/config"
  "${REPO_ROOT}/source_proxy/data"
  "${REPO_ROOT}/source_proxy/.spirit-backups"
  "${REPO_ROOT}/.spirit-backups"
  "${REPO_ROOT}/backend/searxng_data"
  "${REPO_ROOT}/backend/volumes"
)

log "RESTIC_REPOSITORY=${RESTIC_REPOSITORY}"
log "Planned includes are path names only; secret contents are not read."
print_command restic -r "${RESTIC_REPOSITORY}" backup "${EXCLUDES[@]}" "${INCLUDES[@]}"
print_command restic -r "${RESTIC_REPOSITORY}" snapshots
