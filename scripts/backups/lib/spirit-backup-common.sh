#!/usr/bin/env bash
set -euo pipefail

SPIRIT_BACKUP_MODE="${SPIRIT_BACKUP_MODE:-dry-run}"
SPIRIT_BACKUP_I_UNDERSTAND_REAL_WRITES="${SPIRIT_BACKUP_I_UNDERSTAND_REAL_WRITES:-false}"

log() {
  printf '[spirit-backup] %s\n' "$*"
}

warn() {
  printf '[spirit-backup][WARN] %s\n' "$*" >&2
}

fail() {
  printf '[spirit-backup][FAIL] %s\n' "$*" >&2
  exit 1
}

is_dry_run() {
  [[ "${SPIRIT_BACKUP_MODE}" != "real" ]]
}

require_real_write_approval() {
  local action="${1:-protected action}"
  if [[ "${SPIRIT_BACKUP_MODE}" != "real" || "${SPIRIT_BACKUP_I_UNDERSTAND_REAL_WRITES}" != "true" ]]; then
    fail "Refusing ${action}: set SPIRIT_BACKUP_MODE=real and SPIRIT_BACKUP_I_UNDERSTAND_REAL_WRITES=true only after Britton approval."
  fi
}

require_path_under() {
  local path="$1"
  local parent="$2"
  local resolved_path
  local resolved_parent
  resolved_path="$(realpath -m -- "$path")"
  resolved_parent="$(realpath -m -- "$parent")"
  case "${resolved_path}" in
    "${resolved_parent}"|"${resolved_parent}"/*) return 0 ;;
    *) fail "Path ${resolved_path} is not under required parent ${resolved_parent}" ;;
  esac
}

redact_path_if_secret_shaped() {
  local path="$1"
  case "${path}" in
    *.env|*.env.*|*"/.env"|*"/.env.local"|*"key"*|*"token"*|*"credential"*|*"cert"*|*"secret"*|*"password"*)
      printf '%s\n' '[REDACTED_SECRET_SHAPED_PATH]'
      ;;
    *)
      printf '%s\n' "${path}"
      ;;
  esac
}

print_command() {
  if is_dry_run; then
    printf '[DRY-RUN] '
    printf '%q ' "$@"
    printf '\n'
  else
    require_real_write_approval "executing command: $*"
    "$@"
  fi
}

command_exists() {
  command -v "$1" >/dev/null 2>&1
}
