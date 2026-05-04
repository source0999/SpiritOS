#!/usr/bin/env bash
# ── Generate LAN/Tailscale-friendly TLS certs for Next dev (mkcert) ────────────────
# > Default `npm run dev:https` certs often include localhost only; remote browsers
# > hitting https://10.x need SANs on the cert (warnings OK after mkcert -install).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
mkdir -p certificates

EXTRA_RAW="${SPIRIT_TLS_EXTRA_HOSTS:-}"
EXTRA_PARTS=()
if [[ -n "$EXTRA_RAW" ]]; then
  IFS=',' read -ra EXTRA_PARTS <<< "${EXTRA_RAW// /}"
fi

HOSTS=(localhost 127.0.0.1 ::1)
for part in "${EXTRA_PARTS[@]}"; do
  t="$(echo "$part" | xargs)"
  if [[ -n "$t" ]]; then
    HOSTS+=("$t")
  fi
done

if ! command -v mkcert >/dev/null 2>&1; then
  echo "mkcert not found. Install: https://github.com/FiloSottile/mkcert#installation" >&2
  exit 1
fi

mkcert -key-file certificates/spirit-dev-key.pem -cert-file certificates/spirit-dev.pem "${HOSTS[@]}"
echo "OK: certificates/spirit-dev.pem — SANs: ${HOSTS[*]}"
echo "Next: npm run dev:https:lan   (or export SPIRIT_TLS_EXTRA_HOSTS and re-run to add hosts)"
