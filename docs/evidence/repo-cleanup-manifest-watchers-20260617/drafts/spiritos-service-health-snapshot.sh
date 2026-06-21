#!/usr/bin/env bash
set -u
OUT_DIR="${SPIRITOS_HEALTH_DIR:-/mnt/spirit-8tb/spiritos-health}"
LOCK_DIR="${OUT_DIR}/locks"
RUN_ID="$(date -Is | tr ":" "-")"
mkdir -p "$OUT_DIR" "$LOCK_DIR" 2>/dev/null || exit 0
exec 9>"$LOCK_DIR/${0##*/}.lock"
if ! flock -n 9; then echo "already running"; exit 0; fi
LOG="$OUT_DIR/${0##*/}.${RUN_ID}.log"
run(){ echo; echo "## $*"; "$@" 2>&1 || true; }
{
echo "spiritos health snapshot: ${0##*/}"
date -Is
hostname
run ss -ltnp
run systemctl status ollama docker --no-pager
run docker ps --format 'table {{.Names}	{{.Status}}	{{.Ports}}'
run tmux ls
echo; echo "Source Proxy health (no restart):"; curl -sk https://127.0.0.1:8787/health || true
echo; echo "Next root (no restart):"; curl -s http://127.0.0.1:3000 || true
echo; echo "Ollama tags:"; curl -s http://127.0.0.1:11434/api/tags || true
} >"$LOG" 2>&1
