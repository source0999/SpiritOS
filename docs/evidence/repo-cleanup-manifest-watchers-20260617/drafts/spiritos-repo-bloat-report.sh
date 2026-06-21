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
REPO="${SPIRITOS_REPO:-/home/source/SpiritOS}"
if [ -d "$REPO/.git" ]; then
  cd "$REPO" || exit 0
  run git status --short --untracked-files=normal
  run git count-objects -vH
  echo; echo "Top-level file counts:"
  find . -path ./.git -prune -o -type f -printf '%h
' | sort | uniq -c | sort -nr | head -80 || true
else
  echo "Repo not found: $REPO"
fi
} >"$LOG" 2>&1
