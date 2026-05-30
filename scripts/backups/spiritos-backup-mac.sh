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

MAC_HOST="${SPIRIT_MAC_HOST:-spirit-mac-mini}"
MAC_REPO_PATH="${SPIRIT_MAC_REPO_PATH:-/Users/spiritmac/spiritos-worker/SpiritOS}"
MAC_RESTIC_REPOSITORY="${SPIRIT_MAC_RESTIC_REPOSITORY:-/mnt/spirit-8tb/spiritos-backups/restic-repos/spirit-mac-mini}"

log "Mac backup planner mode=${SPIRIT_BACKUP_MODE}"
log "Testing SSH reachability for ${MAC_HOST}"
ssh -o BatchMode=yes -o ConnectTimeout=5 "${MAC_HOST}" "hostname; whoami; test -d '${MAC_REPO_PATH}' && echo MAC_SPIRITOS_PATH_PRESENT || echo MAC_SPIRITOS_PATH_MISSING; find /Users/spiritmac/spiritos-worker -maxdepth 2 -type d \\( -name '*backup*' -o -name '*overlay*' \\) -print 2>/dev/null | head -40" 2>&1 || warn "Mac unavailable or SSH alias missing"

log "Planned Mac candidates: ${MAC_HOST}:${MAC_REPO_PATH}, worker overlays, preserved pre-git backups if present."
log "No restic install, no data copy, and no Mac secret reads are performed."
print_command ssh "${MAC_HOST}" restic -r "${MAC_RESTIC_REPOSITORY}" backup --exclude node_modules --exclude .next --exclude dist "${MAC_REPO_PATH}"
