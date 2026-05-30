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

log "Docker volume export planner mode=${SPIRIT_BACKUP_MODE}"

declare -A CLASS=(
  [source_postgres_data]="critical database state"
  [ollama_data]="large runtime/model state"
  [whisper_cache]="rebuildable cache unless operator marks critical"
  [openedai_voices]="runtime voice assets"
  [searxng_data]="search runtime state"
)

if command_exists docker; then
  docker volume ls 2>&1 || true
else
  warn "docker command not found; expected volumes are still listed."
fi

for volume in source_postgres_data ollama_data whisper_cache openedai_voices searxng_data; do
  log "${volume}: ${CLASS[${volume}]}"
  print_command docker run --rm -v "${volume}:/volume:ro" -v /mnt/spirit-8tb/spiritos-backups/docker-volumes:/backup alpine tar -C /volume -cf "/backup/${volume}.tar" .
done

log "No Docker volume export occurs without approval."
