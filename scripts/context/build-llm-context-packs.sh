#!/usr/bin/env bash
# Build split, uploadable Repomix XML packs for broad LLM review.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
OUT="${SPIRIT_CONTEXT_OUT:-$ROOT/repomixes}"

cd "$ROOT"
mkdir -p "$OUT"

export HEADROOM_PORT="${HEADROOM_PORT:-8798}"
export HEADROOM_BASE_URL="${HEADROOM_BASE_URL:-http://127.0.0.1:8798}"
export HEADROOM_BIN="${HEADROOM_BIN:-$ROOT/.venv-headroom/bin/headroom}"

REPOMIX="$ROOT/node_modules/repomix/bin/repomix.cjs"
if [[ ! -f "$REPOMIX" ]]; then
  echo "FAIL: missing local Repomix CLI at $REPOMIX"
  echo "Run npm install in $ROOT, then retry npm run context:all"
  exit 1
fi

CONFIG="$(mktemp /tmp/spiritos-repomix-focused.XXXXXX.json)"

cat > "$CONFIG" <<'JSON'
{
  "input": { "maxFileSize": 2000000 },
  "output": {
    "style": "xml",
    "parsableStyle": true,
    "compress": true,
    "fileSummary": true,
    "directoryStructure": true,
    "files": true,
    "truncateBase64": true,
    "topFilesLength": 15
  },
  "security": { "enableSecurityCheck": true },
  "tokenCount": { "encoding": "o200k_base" }
}
JSON

COMMON_IGNORE="node_modules/**,.git/**,.next/**,dist/**,out/**,build/**,coverage/**,**/.venv/**,**/venv/**,**/__pycache__/**,**/*.pyc,**/*.sqlite,**/*.db,**/*.log,repomix-output*.xml,*context.xml,docs/evidence/**,docs/handoff/**,backend/searxng_data/**,backend/volumes/**,services/jellyfin/**,scripts/media/*.json,scripts/media/model_gallery/**,**/*.{mp4,mkv,mov,m4v,ts,mp3,wav,flac,jpg,jpeg,png,webp,gif,heic,zip,tar,gz,7z}"

make_pack() {
  local name="$1"
  local include="$2"
  local final="$OUT/${name}.xml"

  echo ""
  echo "=== PACK: ${name} ==="
  rm -f "$final"
  node "$REPOMIX" . \
    --config "$CONFIG" \
    --compress \
    --include "$include" \
    --ignore "$COMMON_IGNORE" \
    --output "$final"
  ls -lh "$final"
}

make_pack "repo-map-context" "README.md,package.json,repomix*.config.json,.repomixignore,docs/**/*.md,docs/**/*.json,_blueprints/**"
make_pack "source-proxy-context" "source_proxy/**,scripts/context/**,scripts/source-proxy-*.mjs,scripts/source-proxy-*.sh,scripts/headroom-proxy-dev.sh,scripts/source-context-compress.mjs,scripts/repomix-llm.mjs,src/app/coding/**,src/components/coding/**,src/lib/coding/**,src/app/v1/**,src/app/api/coding/**,src/lib/mac-worker/**,scripts/mac-worker/**"
make_pack "frontend-context" "src/app/**,src/components/**,src/lib/**,package.json,tsconfig.json,next.config.*"
make_pack "spiritflix-media-code-context" "src/app/spiritflix/**,src/components/spiritflix/**,src/app/api/spiritflix/**,src/lib/spiritflix/**,src/lib/media/**,scripts/media/**/*.py,scripts/media/**/*.mjs,scripts/media/**/*.sh,services/jellyfin/**/*.md,services/jellyfin/**/*.yml,services/jellyfin/**/*.yaml"
make_pack "docs-plans-context" "docs/**/*.md,docs/**/*.json,_blueprints/**"

echo ""
echo "=== DONE: uploadable context packs in ${OUT} ==="
ls -lh "$OUT"/repo-map-context.xml \
       "$OUT"/source-proxy-context.xml \
       "$OUT"/frontend-context.xml \
       "$OUT"/spiritflix-media-code-context.xml \
       "$OUT"/docs-plans-context.xml
