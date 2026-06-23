#!/usr/bin/env bash
# ── Repomix context export verifier ─────────────────────────────────
# Fails if the LLM handoff bundle is bloated or Headroom was claimed falsely.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PROFILE="${1:-source-proxy-min}"
OUTPUT="${ROOT}/repomix-output.${PROFILE}.xml"
TARGET_BYTES=$((2 * 1024 * 1024))   # 2 MB soft target
HARD_FAIL_BYTES=$((5 * 1024 * 1024)) # 5 MB hard fail

if [[ ! -f "$OUTPUT" ]]; then
  echo "FAIL: missing output ${OUTPUT}"
  echo "Run: npm run context:${PROFILE}"
  exit 1
fi

BYTES=$(stat -c%s "$OUTPUT" 2>/dev/null || stat -f%z "$OUTPUT")
HUMAN=$(ls -lh "$OUTPUT" | awk '{print $5}')

echo "=== Repomix context verify (${PROFILE}) ==="
echo "output: ${OUTPUT}"
echo "size: ${HUMAN} (${BYTES} bytes)"

# Headroom / compression metadata
COMPRESSION=$(grep -oP 'compression="\K[^"]+' "$OUTPUT" | head -1 || true)
HEADROOM_COMPRESSED=$(grep -oP '<headroom compressed="\K[^"]+' "$OUTPUT" | head -1 || true)
TOKENS_BEFORE=$(grep -oP 'tokens_before="\K[^"]+' "$OUTPUT" | head -1 || true)
TOKENS_AFTER=$(grep -oP 'tokens_after="\K[^"]+' "$OUTPUT" | head -1 || true)
TOKENS_SAVED=$(grep -oP 'tokens_saved="\K[^"]+' "$OUTPUT" | head -1 || true)
PROXY=$(grep -oP 'proxy="\K[^"]+' "$OUTPUT" | head -1 || true)

if [[ -z "${TOKENS_SAVED}" && "${TOKENS_BEFORE}" =~ ^[0-9]+$ && "${TOKENS_AFTER}" =~ ^[0-9]+$ ]]; then
  TOKENS_SAVED=$((TOKENS_BEFORE - TOKENS_AFTER))
fi

echo "bundle compression: ${COMPRESSION:-unknown}"
echo "headroom compressed: ${HEADROOM_COMPRESSED:-unknown}"
echo "tokens: ${TOKENS_BEFORE:-->} → ${TOKENS_AFTER:-->}"
echo "headroom proxy: ${PROXY:-unknown}"

FILE_COUNT=$(grep -c '<file path=' "$OUTPUT" 2>/dev/null || echo 0)
echo "included files (approx): ${FILE_COUNT}"

echo ""
echo "Largest included paths:"
grep -oP '<file path="\K[^"]+' "$OUTPUT" 2>/dev/null | while read -r path; do
  if [[ -f "${ROOT}/${path}" ]]; then
  stat -c "%s %n" "${ROOT}/${path}" 2>/dev/null || stat -f "%z %N" "${ROOT}/${path}"
  fi
done | sort -rn | head -8 | awk '{printf "  %8s  %s\n", $1, $2}'

FAIL=0
warn() { echo "WARN: $*"; }
fail() { echo "FAIL: $*"; FAIL=1; }

# Bloat checks — paths must not appear as included file entries
BLOAT_PATTERNS=(
  'node_modules/'
  '.next/'
  '/dist/'
  'scripts/media/'
  'docs/evidence/'
  'repomix-output'
  'spiritflix-only-repomix'
)

echo ""
echo "Bloat exclusion checks:"
INCLUDED_PATHS=$(grep -oP '<file path="\K[^"]+' "$OUTPUT" 2>/dev/null || true)
for pattern in "${BLOAT_PATTERNS[@]}"; do
  if echo "$INCLUDED_PATHS" | grep -q "${pattern}"; then
    fail "output includes bloated path matching ${pattern}"
  else
    echo "  OK  excluded ${pattern}"
  fi
done

if (( BYTES > HARD_FAIL_BYTES )); then
  fail "output ${BYTES} bytes exceeds hard limit ${HARD_FAIL_BYTES} (5 MB)"
elif (( BYTES > TARGET_BYTES )); then
  warn "output ${BYTES} bytes exceeds soft target ${TARGET_BYTES} (2 MB) but under hard limit"
else
  echo "  OK  size under 2 MB target"
fi

# Headroom honesty: if proxy URL is set and compressed=true, tokens should differ
if [[ "${HEADROOM_COMPRESSED}" == "true" ]]; then
  if [[ ! "${TOKENS_SAVED:-}" =~ ^[0-9]+$ || "${TOKENS_SAVED}" -le 0 ]]; then
    fail "headroom claims compressed=true but tokens_saved is not positive"
  else
    echo "  OK  headroom token savings verified (${TOKENS_SAVED} saved)"
  fi
elif [[ "${COMPRESSION}" == "tree-sitter+headroom" ]]; then
  fail "bundle claims tree-sitter+headroom but headroom compressed=false"
else
  echo "  OK  honest fallback tree-sitter profile (headroom inactive or unavailable)"
fi

echo ""
if (( FAIL )); then
  echo "RESULT: FAIL"
  exit 1
fi
echo "RESULT: PASS"
exit 0
