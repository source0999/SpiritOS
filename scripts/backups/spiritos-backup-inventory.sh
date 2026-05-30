#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=lib/spirit-backup-common.sh
source "${SCRIPT_DIR}/lib/spirit-backup-common.sh"

WRITE_EVIDENCE=false
for arg in "$@"; do
  case "${arg}" in
    --dry-run) SPIRIT_BACKUP_MODE=dry-run ;;
    --write-evidence) WRITE_EVIDENCE=true ;;
    *) fail "Unknown argument: ${arg}" ;;
  esac
done

collect_inventory() {
  echo "# SpiritOS Backup Inventory"
  echo
  echo "Date: $(date -Is)"
  echo "Host: $(hostname 2>/dev/null || echo unknown)"
  echo "User: $(whoami 2>/dev/null || echo unknown)"
  echo "Repo: $(pwd)"
  echo
  echo "## Dell Mount"
  findmnt /mnt/spirit-8tb 2>&1 || true
  df -h /mnt/spirit-8tb 2>&1 || true
  echo
  echo "## Git"
  git status --branch --short --untracked-files=normal 2>&1 || true
  git rev-parse HEAD 2>&1 || true
  echo
  echo "## Docker"
  if command_exists docker; then
    docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Image}}' 2>&1 || true
    docker volume ls 2>&1 || true
  else
    echo "docker command not found"
  fi
  echo
  echo "## Runtime Path Presence"
  for path in .spirit-backups source_proxy/.spirit-backups source_proxy/data backend/searxng_data backend/volumes scout docs/evidence logs receipts; do
    if [[ -e "${path}" ]]; then
      printf '%s\t' "${path}"
      du -sh "${path}" 2>/dev/null || echo "size unavailable"
    else
      echo "${path} MISSING"
    fi
  done
  echo
  echo "## Mac Reachability"
  ssh -o BatchMode=yes -o ConnectTimeout=5 spirit-mac-mini 'hostname; whoami; test -d /Users/spiritmac/spiritos-worker/SpiritOS && echo MAC_SPIRITOS_PATH_PRESENT || echo MAC_SPIRITOS_PATH_MISSING' 2>&1 || echo "spirit-mac-mini unreachable or alias unavailable"
  echo
  echo "## Windows Config Notes"
  grep -R "SPIRITDESKTOP_TELEMETRY_URL\|SPIRIT_WINDOWS_FS_ALLOWLIST\|C:\\\\Projects" -n .env.local.example docs scripts src 2>/dev/null | head -80 || true
}

if [[ "${WRITE_EVIDENCE}" == "true" ]]; then
  out_dir="docs/evidence/backup-system/manual-inventory"
  require_path_under "${out_dir}" "docs/evidence/backup-system"
  mkdir -p "${out_dir}"
  collect_inventory >"${out_dir}/inventory-$(date +%Y%m%d-%H%M%S).md"
else
  collect_inventory
fi
