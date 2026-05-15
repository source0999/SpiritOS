#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <scout-migration.tar.gz> [cpu|nvidia|amd]" >&2
  exit 2
fi

TARBALL="$1"
PROFILE="${2:-cpu}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCOUT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_DIR="$(cd "${SCOUT_DIR}/.." && pwd)"

case "${PROFILE}" in
  cpu|nvidia|amd) ;;
  *)
    echo "Profile must be one of: cpu, nvidia, amd" >&2
    exit 2
    ;;
esac

tar -xzf "${TARBALL}" -C "${SCOUT_DIR}"

if [[ ! -f "${SCOUT_DIR}/data/MIGRATION_MANIFEST.txt" ]]; then
  echo "Missing data/MIGRATION_MANIFEST.txt after restore" >&2
  exit 1
fi

(
  cd "${SCOUT_DIR}"
  sha256sum -c data/MIGRATION_MANIFEST.txt
)

cd "${REPO_DIR}"
docker compose --profile "${PROFILE}" -f scout/docker-compose.scout.yml up -d --build
echo "Scout restore complete with profile: ${PROFILE}"
