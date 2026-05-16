#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCOUT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
REPO_DIR="$(cd "${SCOUT_DIR}/.." && pwd)"
STAMP="$(date -u +%Y%m%d%H%M)"
MANIFEST="${SCOUT_DIR}/data/MIGRATION_MANIFEST.txt"
TARBALL="${REPO_DIR}/scout-migration-${STAMP}.tar.gz"

cd "${REPO_DIR}"
docker compose --profile cpu -f scout/docker-compose.scout.yml stop || true

mkdir -p "${SCOUT_DIR}/data"
(
  cd "${SCOUT_DIR}"
  find data -type f -print0 | sort -z | xargs -0 sha256sum > "${MANIFEST}"
)

tar -czf "${TARBALL}" -C "${SCOUT_DIR}" data config

echo "Manifest: ${MANIFEST}"
echo "Tarball: ${TARBALL}"
