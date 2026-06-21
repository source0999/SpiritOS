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
run uptime
run journalctl -b -1 -p warning..alert --no-pager
run journalctl -k -b -1 --no-pager
run last -x reboot shutdown
} >"$LOG" 2>&1
