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
RESTORE_SOURCE="${SPIRIT_RESTORE_SOURCE:-/home/source/SpiritOS/docs/runbooks/spiritos-backup-runbook.md}"
RESTORE_SNAPSHOT="${SPIRIT_RESTORE_SNAPSHOT:-latest}"
DRILL_ROOT="${SPIRIT_RESTORE_DRILL_ROOT:-/mnt/spirit-8tb/spiritos-backups/restore-drills/$(date +%F)/$(date -u +%H%M%SZ)}"
RESTORE_TARGET="${DRILL_ROOT}/source-server"

resolved_target="$(realpath -m -- "${RESTORE_TARGET}")"
case "${resolved_target}" in
  /home/source/SpiritOS|/home/source/SpiritOS/*) fail "refuse restore over /home/source/SpiritOS" ;;
esac
require_path_under "${resolved_target}" "/mnt/spirit-8tb/spiritos-backups/restore-drills"

if [[ -e "${RESTORE_TARGET}" ]]; then
  fail "refuse overwrite: restore target already exists: ${RESTORE_TARGET}"
fi

log "Restore drill planner mode=${SPIRIT_BACKUP_MODE}"
log "Target isolated restore-drills path: ${RESTORE_TARGET}"
log "Snapshot source path: ${RESTORE_SOURCE}"
log "Snapshot selector: ${RESTORE_SNAPSHOT}"
log "Refuse overwrite is active."

if is_dry_run; then
  print_command restic -r "${RESTIC_REPOSITORY}" restore "${RESTORE_SNAPSHOT}" --target "${RESTORE_TARGET}" --include "${RESTORE_SOURCE}"
  exit 0
fi

require_real_write_approval "running restore drill"
restic -r "${RESTIC_REPOSITORY}" restore "${RESTORE_SNAPSHOT}" --target "${RESTORE_TARGET}" --include "${RESTORE_SOURCE}"

restored_count="$(find "${RESTORE_TARGET}" -type f | wc -l | tr -d '[:space:]')"
if [[ "${restored_count}" == "0" ]]; then
  fail "restore drill restored zero files; refusing GO"
fi

log "Restored file count: ${restored_count}"
find "${RESTORE_TARGET}" -type f | sort
