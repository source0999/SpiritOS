#!/usr/bin/env bash
set -euo pipefail

ROOT="${SPIRITOS_ROOT:-$HOME/SpiritOS}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=runtime-port-guard.sh
source "$SCRIPT_DIR/runtime-port-guard.sh"

printf '== SpiritOS runtime lane audit ==\n'
date -Is
printf '\n'

printf '== tmux ==\n'
tmux ls 2>&1 || true
printf '\n'

printf '== ports ==\n'
ss -ltnp 2>/dev/null | grep -E ':3000|:3001|:8787|:3020|:3030' || printf '(no lane listeners found)\n'
printf '\n'

printf '== memory / swap ==\n'
free -h || true
printf '\n'

printf '== top RSS node/next ==\n'
ps -eo pid,ppid,stat,pcpu,pmem,rss,etime,cmd --sort=-rss 2>/dev/null | grep -E 'next-server|next dev|uvicorn source_proxy|spiritos-lan-watchdog|spiritflix-stable' | grep -v grep | head -12 || true
printf '\n'

printf '== health probes ==\n'
curl -k -sS -o /dev/null -w '  :3000 root -> %{http_code} in %{time_total}s\n' --max-time 20 https://127.0.0.1:3000/ || printf '  :3000 root -> FAIL\n'
curl -k -sS -o /dev/null -w '  :3000 coding -> %{http_code} in %{time_total}s\n' --max-time 20 https://127.0.0.1:3000/coding || printf '  :3000 coding -> FAIL\n'
curl -k -sS -o /dev/null -w '  :8787 health -> %{http_code} in %{time_total}s\n' --max-time 25 https://127.0.0.1:8787/healthcheck || printf '  :8787 health -> FAIL\n'
curl -sS -o /dev/null -w '  :3001 spiritflix -> %{http_code} in %{time_total}s\n' --max-time 20 http://127.0.0.1:3001/spiritflix || printf '  :3001 spiritflix -> FAIL\n'
printf '\n'

printf '== recent watchdog churn ==\n'
if [[ -f "$HOME/spiritos-dev-lan-watchdog.log" ]]; then
  rg -c 'frontend health check failed|frontend is hung|frontend exited' "$HOME/spiritos-dev-lan-watchdog.log" 2>/dev/null | head -1 || true
  tail -5 "$HOME/spiritos-dev-lan-watchdog.log" 2>/dev/null || true
else
  printf '  (no spiritos watchdog log)\n'
fi
printf '\n'

orphans="$(ps -eo pid,args --sort=-rss 2>/dev/null | grep -E 'next dev -H.*--port (3020|3027|3030)|next dev.*-p (3027)' | grep -v grep || true)"
if [[ -n "$orphans" ]]; then
  printf '== orphan next dev listeners (should be cleaned) ==\n'
  printf '%s\n' "$orphans"
  printf '\n'
fi

printf 'audit complete\n'
