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

log "Database dump planner mode=${SPIRIT_BACKUP_MODE}"
log "PostgreSQL plan: discover a running postgres container, then run pg_dump inside it after approval."
print_command docker exec source-postgres pg_dump -U REPLACE_ME_DB_USER -d REPLACE_ME_DB_NAME --format=custom --file=/approved/export/path/source-postgres.dump

log "SQLite plan: find known SQLite files by path only, then use sqlite3 .backup for online-safe copy after approval."
for candidate in source_proxy/data backend scout; do
  [[ -e "${candidate}" ]] && find "${candidate}" -maxdepth 4 -type f \( -name '*.sqlite' -o -name '*.sqlite3' -o -name '*.db' \) -print 2>/dev/null || true
done | sed 's#^#SQLite candidate path: #'

print_command sqlite3 /path/to/source.db ".backup '/approved/export/path/source.db.backup'"
log "No live DB dump is executed in dry-run."
