This file is a merged representation of a subset of the codebase, containing specifically included files and files not matching ignore patterns, combined into a single document by Repomix.
The content has been processed where content has been formatted for parsing in markdown style, content has been compressed (code blocks are separated by ⋮---- delimiter), security check has been disabled.

# File Summary

## Purpose
This file contains a packed representation of a subset of the repository's contents that is considered the most important context.
It is designed to be easily consumable by AI systems for analysis, code review,
or other automated processes.

## File Format
The content is organized as follows:
1. This summary section
2. Repository information
3. Directory structure
4. Repository files (if enabled)
5. Multiple file entries, each consisting of:
  a. A header with the file path (## File: path/to/file)
  b. The full contents of the file in a code block

## Usage Guidelines
- This file should be treated as read-only. Any changes should be made to the
  original repository files, not this packed version.
- When processing this file, use the file path to distinguish
  between different files in the repository.
- Be aware that this file may contain sensitive information. Handle it with
  the same level of security as you would the original repository.

## Notes
- Some files may have been excluded based on .gitignore rules and Repomix's configuration
- Binary files are not included in this packed representation. Please refer to the Repository Structure section for a complete list of file paths, including binary files
- Only files matching these patterns are included: **/*
- Files matching these patterns are excluded: repomix.config.json
- Files matching default ignore patterns are excluded
- Content has been formatted for parsing in markdown style
- Content has been compressed - code blocks are separated by ⋮---- delimiter
- Long base64 data strings (e.g., data:image/png;base64,...) have been truncated to reduce token count
- Security check has been disabled - content may contain sensitive information

# Directory Structure
```
allowed-dev-origins.ts
docs/media-server/jellyfin-access.md
docs/media-server/jellyfin-operations.md
docs/media/spiritflix-anime-importer.md
middleware.ts
next.config.ts
PACK_INSTRUCTIONS.md
package.json
postcss.config.mjs
scripts/media/spiritflix_anime_import.py
scripts/media/spiritflix_continue_diag.py
src/app/api/spiritflix/face-metadata/route.ts
src/app/api/spiritflix/gallery/image/route.ts
src/app/api/spiritflix/gallery/route.ts
src/app/api/spiritflix/jellyfin-image/route.ts
src/app/api/spiritflix/jellyfin/route.ts
src/app/api/spiritflix/stream/route.ts
src/app/spiritflix/page.tsx
src/components/spiritflix/__tests__/SpiritFlixHome.test.tsx
src/components/spiritflix/__tests__/SpiritFlixPlayer.test.tsx
src/components/spiritflix/SpiritFlixApp.tsx
src/components/spiritflix/SpiritFlixCard.tsx
src/components/spiritflix/SpiritFlixDetailsModal.tsx
src/components/spiritflix/SpiritFlixHome.tsx
src/components/spiritflix/SpiritFlixImage.tsx
src/components/spiritflix/SpiritFlixLogin.tsx
src/components/spiritflix/SpiritFlixPlayer.tsx
src/components/spiritflix/SpiritFlixRail.tsx
src/lib/spiritflix-jellyfin-client.ts
src/lib/spiritflix-resume.ts
src/lib/spiritflix-types.ts
src/lib/spiritflix/jellyfin-client.ts
src/lib/spiritflix/resume.ts
src/lib/spiritflix/types.ts
src/styles/spiritflix.css
tsconfig.json
vitest.config.mjs
```

# Files

## File: allowed-dev-origins.ts
````typescript
// ── buildAllowedDevOrigins - Tailscale/LAN HMR allowlist (Prompt 9J) ───────────────
// > Lives next to next.config.ts so Next can import without @ path drama.
// > Hostnames only - no protocol, no port. Wildcard: `*.ts.net` per Next docs.
⋮----
/**
 * Merge baked-in homelab defaults with `NEXT_ALLOWED_DEV_ORIGINS` (comma-separated).
 */
export function buildAllowedDevOrigins(
  env: Record<string, string | undefined> = process.env,
): string[]
````

## File: docs/media-server/jellyfin-access.md
````markdown
# Jellyfin Access

Primary private route:

```text
http://spirit.tailb69ea6.ts.net:8096
```

Fallback private route:

```text
http://100.111.32.31:8096
```

Short-name route on the Dell:

```text
http://spirit:8096
```

The short `spirit` route may not work from every device because local DNS can resolve that name differently. Use the MagicDNS FQDN above when in doubt.

This service is private Tailscale/LAN access only. Do not configure public router forwarding, Tailscale Funnel, or public DNS for this Jellyfin lane.
````

## File: docs/media-server/jellyfin-operations.md
````markdown
# Jellyfin Operations

Compose file:

```bash
cd /home/source/SpiritOS
docker compose -f services/jellyfin/docker-compose.yml ps
docker compose -f services/jellyfin/docker-compose.yml logs --tail 120 jellyfin
docker compose -f services/jellyfin/docker-compose.yml restart jellyfin
docker compose -f services/jellyfin/docker-compose.yml pull jellyfin
docker compose -f services/jellyfin/docker-compose.yml up -d
docker compose -f services/jellyfin/docker-compose.yml down
```

Local health:

```bash
curl -I http://127.0.0.1:8096
docker inspect spirit-jellyfin --format '{{.State.Status}} {{if .State.Health}}{{.State.Health.Status}}{{end}}'
```

Rollback:

```bash
cd /home/source/SpiritOS
docker compose -f services/jellyfin/docker-compose.yml down
```

Do not delete `/mnt/spirit-8tb/services/jellyfin/config` unless the user explicitly approves losing Jellyfin setup state.
````

## File: docs/media/spiritflix-anime-importer.md
````markdown
# SpiritFlix Anime Importer

Use `scripts/media/spiritflix_anime_import.py` to place authorized anime episodes into the Jellyfin-backed SpiritFlix anime folder.

This importer is for media you own, created, or have written permission/license to download and process. It refuses known unauthorized streaming mirror hosts and does not bypass DRM, site protections, or copyright restrictions.

## Folder Decision

The live Jellyfin compose file mounts:

- Host: `/mnt/spirit-8tb/media/anime`
- Jellyfin: `/media/anime`

The existing Rurouni Kenshin layout on the host is:

```text
/mnt/spirit-8tb/media/anime/Rurouni Kenshin (1996)/
  Season 01/
  Season 02/
```

So this importer uses that existing pattern instead of creating a parallel `/Caasca/SpiritFlix/...` tree:

```text
/mnt/spirit-8tb/media/anime/<Series Name>/Season NN/
```

For Rurouni Kenshin, keep using:

```text
/mnt/spirit-8tb/media/anime/Rurouni Kenshin (1996)/Season 01/
```

## One-Episode Test

Run this on the Dell host. It tests episode 1 and stops. Because `S01E01` already exists, the command should skip the existing file and write a receipt rather than duplicate it.

```bash
cd /home/source/SpiritOS
python3 scripts/media/spiritflix_anime_import.py \
  --series "Rurouni Kenshin (1996)" \
  --season 1 \
  --episode 1 \
  --stop-after 1 \
  --audio dub \
  --source-file "/mnt/spirit-8tb/media/anime/Rurouni Kenshin (1996)/Season 01/Rurouni Kenshin (1996) - S01E01.mkv" \
  --affirm-authorized \
  --authorization-note "One-episode SpiritFlix placement smoke test."
```

Receipt log:

```text
/mnt/spirit-8tb/media/anime/.spiritos-import-receipts/YYYYMMDD.jsonl
```

## Import From an Authorized URL

Install `yt-dlp` on the host first if needed. Then use a direct or supported URL that you are allowed to download:

```bash
cd /home/source/SpiritOS
python3 scripts/media/spiritflix_anime_import.py \
  --series "Example Anime (2026)" \
  --season 1 \
  --episode 1 \
  --stop-after 1 \
  --audio dub \
  --source-url "https://example.com/authorized-episode-1" \
  --affirm-authorized \
  --authorization-note "Licensed or owned test episode."
```

## Batch / Season Import

For any series, create a CSV manifest with one row per episode. The downloader/importer uses the row metadata to place files into the right series and season folder.

```csv
series,season,episode,audio,source_url,source_file,episode_title
Rurouni Kenshin (1996),1,1,dub,,/mnt/spirit-8tb/media-originals/keep-for-30-days/anime/mi-mpzx6l69-9a89a8d2/Rurouni Kenshin (1996) - S01E01.mkv,
Example Anime (2026),1,1,dub,https://example.com/authorized-episode-1,,
Example Anime (2026),1,2,dub,https://example.com/authorized-episode-2,,
```

Run the whole manifest:

```bash
cd /home/source/SpiritOS
python3 scripts/media/spiritflix_anime_import.py \
  --manifest /mnt/spirit-8tb/media-processing/my-anime-manifest.csv \
  --affirm-authorized \
  --authorization-note "Authorized anime batch import."
```

Test only the first row and stop:

```bash
cd /home/source/SpiritOS
python3 scripts/media/spiritflix_anime_import.py \
  --manifest /mnt/spirit-8tb/media-processing/my-anime-manifest.csv \
  --stop-after 1 \
  --affirm-authorized \
  --authorization-note "One-episode manifest smoke test."
```

The script is safe to re-run. Existing target files are skipped unless `--force` is provided.
By default, filenames match the existing SpiritFlix convention and do not include a quality tag. Add `--include-detected-quality` or `--quality 1080p` only when you intentionally want names like `[1080p]`.

## Send Downloads Through The Converter

Use `--send-to-converter` when the source file still needs SpiritOS conversion. This writes to the watched inbox:

```text
/mnt/spirit-8tb/media-inbox/anime/<Series Name>/Season NN/
```

The `media-ingest-worker` then converts it and moves the accepted output to:

```text
/mnt/spirit-8tb/media/anime/<Series Name>/Season NN/
```

Example one-episode handoff:

```bash
cd /home/source/SpiritOS
python3 scripts/media/spiritflix_anime_import.py \
  --series "Rurouni Kenshin (1996)" \
  --season 1 \
  --episode 2 \
  --audio dub \
  --source-file "/path/to/authorized/source-episode-2.mkv" \
  --send-to-converter \
  --affirm-authorized \
  --authorization-note "Authorized dub import for converter."
```

For downloader workflows, prefer `--send-to-converter`; otherwise the importer writes directly to the final Jellyfin library and bypasses conversion.

## Auto-Optimize The Yes Library

The media ingest worker also watches the existing SpiritFlix yes library:

```text
/mnt/spirit-8tb/media/yes
```

Files copied or uploaded directly into that folder are treated as library-source jobs. After the worker sees a stable file, it moves the file into active processing, creates the smaller MKV output under the same `media/yes` tree, writes a `.media-ingest.json` receipt beside the accepted output, and deletes the original large upload only after `ffprobe` verifies the converted output and the final move succeeds.

The default watch root can be changed with `MEDIA_INGEST_LIBRARY_WATCH_ROOTS`. Use the platform path separator to watch more than one root.

```bash
cd /home/source/SpiritOS
MEDIA_INGEST_ENCODER=mac-videotoolbox-hevc \
MEDIA_INGEST_LIBRARY_WATCH_ROOTS=/mnt/spirit-8tb/media/yes \
node ./scripts/media-ingest-worker.mjs
```

Set `MEDIA_INGEST_DELETE_LIBRARY_ORIGINALS=0` for a dry/holding run where library originals should not be deleted after successful conversion.

Manifest columns:

- `series`: Jellyfin series folder name, such as `Rurouni Kenshin (1996)`.
- `season`: Season number.
- `episode`: Episode number.
- `audio`: `dub`, `sub`, or `original`.
- `source_url`: Authorized URL to fetch with `yt-dlp`.
- `source_file`: Authorized local file to copy into the library.
- `episode_title`: Optional title to append to the filename.

## Safety Rules

- Default write root is `/mnt/spirit-8tb/media/anime`.
- Custom roots require `--allow-custom-root`.
- `--affirm-authorized` is required.
- Known unauthorized mirror hosts are refused.
- Existing files are not overwritten unless `--force` is provided.
- JSONL receipts include source, target, status, quality, audio lane, detected audio languages, and SHA-256 when available.
````

## File: middleware.ts
````typescript
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";
⋮----
export function middleware(_request: NextRequest)
⋮----
// Passthrough for now - auth, rate limiting, homelab headers go here later
````

## File: next.config.ts
````typescript
import type { NextConfig } from "next";
import { realpathSync } from "node:fs";
⋮----
import { buildAllowedDevOrigins } from "./allowed-dev-origins";
⋮----
/* ── Homelab dev - HMR allowlist + webpack watch ignore (big artifacts) ────────────
 * Next parses `Origin` to hostname only - no `http://` entries.
 * Tailscale / LAN: set `NEXT_ALLOWED_DEV_ORIGINS` (comma-separated hostnames), restart dev.
 */
⋮----
async headers()
````

## File: PACK_INSTRUCTIONS.md
````markdown
This pack contains only the SpiritFlix/Jellyfin-facing code from SpiritOS needed for LLM review or debugging.
Focus areas:
- SpiritFlix UI route, app shell, cards, rails, details modal, player, login, image handling.
- Jellyfin client wrappers and resume/playback helpers.
- SpiritFlix API proxy routes for Jellyfin, images, gallery, face metadata, and stream fallback.
- SpiritFlix-specific CSS and focused tests.
- Minimal Next/Vitest/package config so imports and runtime assumptions are understandable.
Do not infer unrelated SpiritOS modules are present unless imported by these files.
Recent operational context: the :3001 sidecar should stream directly to Jellyfin :8096 where possible instead of proxying video through /api/spiritflix/stream.
````

## File: package.json
````json
{
  "name": "spirit-os",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev -H 0.0.0.0 --webpack",
    "dev:https": "next dev -H 0.0.0.0 --webpack --experimental-https -p 3000",
    "dev:https:lan": "next dev -H 0.0.0.0 --webpack -p 3000 --experimental-https --experimental-https-key ./certificates/spirit-dev-key.pem --experimental-https-cert ./certificates/spirit-dev.pem",
    "dev:https:lan:watch": "bash ./scripts/spiritos-lan-watchdog.sh",
    "dev:turbo": "next dev -H 0.0.0.0",
    "dev:backend": "cd backend && docker compose up -d",
    "dev:all": "npm run dev:backend && npm run dev",
    "dev:all:https": "npm run dev:backend && npm run dev:https",
    "dev:all:https:lan": "npm run dev:backend && npm run dev:https:lan",
    "gate:status": "node ./scripts/gate-status",
    "gate:approve": "node ./scripts/gate-approve",
    "gate:start": "node ./scripts/gate-start",
    "gate:complete": "node ./scripts/gate-complete",
    "gate:block": "node ./scripts/gate-block",
    "proxy:bootstrap": "node ./scripts/source-proxy-bootstrap.mjs",
    "proxy:bootstrap:linux": "bash ./scripts/source-proxy-bootstrap.sh",
    "proxy:bootstrap:windows": "powershell -ExecutionPolicy Bypass -File ./scripts/source-proxy-bootstrap.ps1",
    "proxy:dev": "node ./scripts/source-proxy-dev.mjs",
    "proxy:https": "node ./scripts/source-proxy-dev.mjs --https",
    "proxy:https:lan": "node ./scripts/source-proxy-dev.mjs --https --lan",
    "context:pack": "repomix --config repomix.config.json .",
    "context:compress": "node ./scripts/source-context-compress.mjs",
    "context:headroom": "node ./scripts/source-context-compress.mjs --headroom-only",
    "validate:blueprints": "node ./scripts/validate-blueprints.mjs",
    "next:mcp:ws": "node ./scripts/next-mcp-ws-bridge.mjs",
    "next:mcp:ws:probe": "node ./scripts/next-mcp-ws-probe.mjs",
    "next:mcp:ws:smoke": "node ./scripts/next-mcp-ws-smoke.mjs",
    "build": "next build --webpack",
    "start": "next start",
    "lint": "eslint .",
    "typecheck": "tsc --noEmit",
    "check": "npm run lint && npm run typecheck && npm run build",
    "test": "vitest",
    "test:coding-regression": "python -m pytest -q source_proxy/tests/test_coding_regression_pack.py",
    "test:coding-frontend-regression": "vitest run src/app/coding/__tests__/page.test.tsx src/components/coding/__tests__/coding-command-center-shell.test.tsx src/lib/coding/__tests__/model-provider-status.test.ts src/lib/coding/__tests__/unified-diff-paths.test.ts src/components/coding/__tests__/approval-gate-binding.test.ts src/lib/coding/__tests__/proxy-route-payload.test.ts src/app/v1/actions/execute-approved/__tests__/route.test.ts src/components/coding/__tests__/coding-workflow-step.test.ts src/components/coding/__tests__/client-fallback.test.ts src/components/coding/__tests__/proxy-safety-smoke.test.ts src/app/v1/coding/self-tests/run/__tests__/route.test.ts",
    "test:ui": "vitest --ui",
    "ytmclone:stats:smoke": "node ./scripts/ytmclone-stats-smoke.mjs",
    "ytmclone:android:build": "cd apps/ytmclone-android && ./gradlew assembleDebug"
  },
  "dependencies": {
    "@ai-sdk/openai": "^3.0.58",
    "@ai-sdk/react": "^3.0.176",
    "@dnd-kit/core": "^6.3.1",
    "@dnd-kit/sortable": "^10.0.0",
    "@dnd-kit/utilities": "^3.2.2",
    "ai": "^6.0.174",
    "clsx": "^2.1.1",
    "dexie": "^4.4.2",
    "dexie-react-hooks": "^4.4.0",
    "framer-motion": "^12.38.0",
    "headroom-ai": "^0.22.4",
    "hls.js": "^1.6.16",
    "lucide-react": "^1.8.0",
    "next": "16.2.4",
    "react": "19.2.4",
    "react-dom": "19.2.4",
    "react-markdown": "^10.1.0",
    "remark-gfm": "^4.0.1",
    "server-only": "^0.0.1",
    "swr": "^2.4.1",
    "tailwind-merge": "^3.5.0"
  },
  "devDependencies": {
    "@modelcontextprotocol/sdk": "^1.24.3",
    "@playwright/test": "^1.60.0",
    "@tailwindcss/postcss": "^4",
    "@testing-library/jest-dom": "^6.9.1",
    "@testing-library/react": "^16.3.2",
    "@types/node": "^20",
    "@types/react": "^19",
    "@types/react-dom": "^19",
    "@vitejs/plugin-react": "^6.0.1",
    "@vitest/ui": "^4.1.5",
    "eslint": "^9",
    "eslint-config-next": "16.2.4",
    "jsdom": "^24.1.3",
    "next-devtools-mcp": "^0.3.10",
    "repomix": "^1.14.0",
    "tailwindcss": "^4",
    "typescript": "^5",
    "vitest": "^4.1.5",
    "ws": "^8.20.0"
  }
}
````

## File: postcss.config.mjs
````javascript

````

## File: scripts/media/spiritflix_anime_import.py
````python
#!/usr/bin/env python3
"""Authorized anime episode importer for SpiritFlix/Jellyfin.

This tool is intentionally a placement/import wrapper. It does not bypass DRM,
site protections, or copyright restrictions. Use it only with files or URLs you
own, created, or have permission/license to download and process.
"""
⋮----
DEFAULT_ANIME_ROOT = Path(os.environ.get("SPIRITFLIX_ANIME_ROOT", "/mnt/spirit-8tb/media/anime"))
DEFAULT_ANIME_INBOX_ROOT = Path(
DEFAULT_RECEIPT_DIR = ".spiritos-import-receipts"
BLOCKED_SOURCE_HOSTS = {
VIDEO_EXTENSIONS = {".mkv", ".mp4", ".webm", ".mov", ".m4v"}
⋮----
def utc_now() -> str
⋮----
def sanitize_segment(value: str, fallback: str = "untitled") -> str
⋮----
cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "", value.strip())
cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
⋮----
def ensure_under_root(root: Path, target: Path) -> Path
⋮----
resolved_root = root.resolve()
resolved_target = target.resolve()
⋮----
def parse_episode_range(value: str | None, fallback_episode: int | None) -> list[int]
⋮----
episodes: list[int] = []
⋮----
part = part.strip()
⋮----
start = int(start_raw)
end = int(end_raw)
⋮----
def reject_blocked_url(source_url: str) -> None
⋮----
host = urlparse(source_url).hostname or ""
host = host.lower().removeprefix("www.")
⋮----
def command_exists(name: str) -> bool
⋮----
def sha256_file(path: Path) -> str
⋮----
digest = hashlib.sha256()
⋮----
def ffprobe(path: Path) -> dict[str, Any]
⋮----
result = subprocess.run(
⋮----
def video_height(probe: dict[str, Any]) -> int | None
⋮----
def audio_languages(probe: dict[str, Any]) -> list[str]
⋮----
languages: list[str] = []
⋮----
tags = stream.get("tags") or {}
language = str(tags.get("language") or "und").lower()
⋮----
stem = f"{sanitize_segment(series)} - S{season:02d}E{episode:02d}"
⋮----
def find_existing_episode(season_dir: Path, series: str, season: int, episode: int) -> Path | None
⋮----
safe_series = re.escape(sanitize_segment(series))
pattern = re.compile(rf"^{safe_series} - S{season:02d}E{episode:02d}(?:\b|[ ._-]).*", re.IGNORECASE)
matches = sorted(
⋮----
def write_receipt(receipt_dir: Path, payload: dict[str, Any]) -> Path
⋮----
receipt_path = receipt_dir / f"{dt.datetime.now(dt.UTC).strftime('%Y%m%d')}.jsonl"
⋮----
def download_with_ytdlp(source_url: str, staging_dir: Path) -> Path
⋮----
output_template = str(staging_dir / "%(title).120B.%(ext)s")
⋮----
candidates = sorted(
⋮----
def load_manifest(manifest_path: Path) -> list[dict[str, Any]]
⋮----
data = json.loads(manifest_path.read_text(encoding="utf-8"))
⋮----
rows: list[dict[str, Any]] = []
⋮----
stripped = line.strip()
⋮----
parsed = json.loads(stripped)
⋮----
def row_value(row: dict[str, Any], *keys: str) -> str | None
⋮----
value = row.get(key)
⋮----
text = str(value).strip()
⋮----
def args_for_manifest_row(base_args: argparse.Namespace, row: dict[str, Any], row_number: int) -> argparse.Namespace
⋮----
row_args = argparse.Namespace(**vars(base_args))
⋮----
season = row_value(row, "season", "season_number") or (str(base_args.season) if base_args.season else None)
episode = row_value(row, "episode", "episode_number", "ep")
⋮----
def import_episode(args: argparse.Namespace, episode: int) -> dict[str, Any]
⋮----
anime_root = DEFAULT_ANIME_INBOX_ROOT if args.send_to_converter else Path(args.target_root)
allowed_roots = {str(DEFAULT_ANIME_ROOT)}
⋮----
series_dir = ensure_under_root(anime_root, anime_root / sanitize_segment(args.series))
season_dir = ensure_under_root(series_dir, series_dir / f"Season {args.season:02d}")
receipt_dir = ensure_under_root(anime_root, anime_root / DEFAULT_RECEIPT_DIR)
⋮----
source_path: Path | None = None
staging_parent: tempfile.TemporaryDirectory[str] | None = None
source_kind = "source-file" if args.source_file else "source-url"
⋮----
source_path = Path(args.source_file)
⋮----
staging_parent = tempfile.TemporaryDirectory(prefix="spiritflix-anime-import-")
source_path = download_with_ytdlp(args.source_url, Path(staging_parent.name))
⋮----
probe = ffprobe(source_path)
height = video_height(probe)
quality = args.quality or (f"{height}p" if args.include_detected_quality and height else None)
target_name = make_file_name(
target_path = ensure_under_root(season_dir, season_dir / target_name)
⋮----
existing_episode_path = find_existing_episode(season_dir, args.series, args.season, episode)
status = "planned"
⋮----
target_path = existing_episode_path
status = "skipped_existing"
⋮----
status = "dry_run"
⋮----
temp_path = target_path.with_suffix(target_path.suffix + ".part")
⋮----
status = "imported"
⋮----
receipt = {
⋮----
def build_parser() -> argparse.ArgumentParser
⋮----
parser = argparse.ArgumentParser(description="Import authorized anime episodes into SpiritFlix/Jellyfin anime folders.")
⋮----
def main() -> int
⋮----
parser = build_parser()
args = parser.parse_args()
⋮----
rows = load_manifest(Path(args.manifest))
⋮----
rows = rows[: max(args.stop_after, 0)]
receipts = [
⋮----
episodes = parse_episode_range(args.episodes, args.episode)
⋮----
episodes = episodes[: max(args.stop_after, 0)]
⋮----
receipts = [import_episode(args, episode) for episode in episodes]
````

## File: scripts/media/spiritflix_continue_diag.py
````python
#!/usr/bin/env python3
"""Secret-safe SpiritFlix/Jellyfin continue-watching diagnostics for agents."""
⋮----
DEFAULT_DB = "/mnt/spirit-8tb/services/jellyfin/config/data/jellyfin.db"
DEFAULT_SERVER = "http://127.0.0.1:8096"
⋮----
def open_db(path: str) -> sqlite3.Connection
⋮----
connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
⋮----
def rows_to_dicts(rows: list[sqlite3.Row]) -> list[dict[str, Any]]
⋮----
def seconds_from_ticks(ticks: int | None) -> int
⋮----
def format_seconds(seconds: int) -> str
⋮----
def get_server_latency(server_url: str, timeout: float) -> dict[str, Any]
⋮----
url = server_url.rstrip("/") + "/System/Info/Public"
started = time.perf_counter()
⋮----
body = response.read(4096)
⋮----
def get_container_status(container: str) -> dict[str, Any]
⋮----
output = subprocess.check_output(
⋮----
def collect(connection: sqlite3.Connection, limit: int, server_url: str, timeout: float, container: str) -> dict[str, Any]
⋮----
recent_devices = rows_to_dicts(
⋮----
resume_rows = rows_to_dicts(
⋮----
favorite_rows = rows_to_dicts(
⋮----
detached_resume_count = connection.execute(
⋮----
duplicate_resume_rows = rows_to_dicts(
⋮----
resume_by_library = Counter(row.get("TopParentName") or "(detached/no library)" for row in resume_rows)
resume_by_path_root = Counter((row.get("Path") or "(no path)").split("/")[2] if (row.get("Path") or "").startswith("/media/") else "(non-media/no path)" for row in resume_rows)
⋮----
def print_report(data: dict[str, Any]) -> None
⋮----
server = data["server"]
⋮----
summary = data["resumeSummary"]
⋮----
title = row["SeriesName"] or row["Name"] or row["ItemId"]
position = format_seconds(seconds_from_ticks(row["PlaybackPositionTicks"]))
library = row["TopParentName"] or "(detached/no library)"
⋮----
def main() -> int
⋮----
parser = argparse.ArgumentParser(description="Inspect SpiritFlix/Jellyfin resume, favorite, device, and latency state.")
⋮----
args = parser.parse_args()
⋮----
connection = open_db(args.db)
⋮----
data = collect(connection, args.limit, args.server, args.timeout, args.container)
````

## File: src/app/api/spiritflix/face-metadata/route.ts
````typescript
import { readdir, readFile } from "node:fs/promises";
import path from "node:path";
import { NextRequest, NextResponse } from "next/server";
import type {
  FaceOrganizerMetadataResponse,
  FaceOrganizerPerformer,
  FaceOrganizerStatus,
  FaceOrganizerVideoMatch,
} from "@/lib/spiritflix-types";
⋮----
interface FaceMetadataRequestItem {
  id?: string;
  name?: string;
  path?: string;
}
⋮----
interface FaceMetadataRequest {
  items?: FaceMetadataRequestItem[];
}
⋮----
interface SidecarPerformer {
  id?: string;
  name?: string;
  confidence?: number;
  similarity?: number;
  status?: string;
  verification_needed?: boolean;
}
⋮----
interface FaceMatchDecision {
  decision?: string;
  performer_name?: string;
  performer_id?: string;
  visual_confirmed?: boolean;
}
⋮----
interface FaceSidecar {
  video_path?: string;
  generated_at?: string;
  verification_needed?: boolean;
  performers?: SidecarPerformer[];
  faces_detected?: number;
  face_match_decisions?: FaceMatchDecision[];
}
⋮----
function normalizeNameKey(value?: string): string
⋮----
function normalizePathKey(value?: string): string
⋮----
function basenameKey(value?: string): string
⋮----
function stemPathKey(value?: string): string
⋮----
function basenameStemKey(value?: string): string
⋮----
function performerKeys(name?: string, id?: string): Set<string>
⋮----
function latestDecisionForPerformer(sidecar: FaceSidecar | undefined, performer: FaceOrganizerPerformer | undefined): FaceMatchDecision | undefined
⋮----
function toStatus(
  performers: FaceOrganizerPerformer[],
  verificationNeeded: boolean,
  sidecarFound: boolean,
  acceptedByUser: boolean,
): FaceOrganizerStatus
⋮----
async function readKnownPerformers(): Promise<FaceOrganizerPerformer[]>
⋮----
async function readEnrolledSources(): Promise<NonNullable<FaceOrganizerMetadataResponse["enrolledSources"]>>
⋮----
// The enrolled page JSON is generated by the review server; SpiritFlix can still use the model index if it is absent.
⋮----
// Keep face metadata usable even if the organizer model index has not been generated.
⋮----
async function findSidecars(root: string): Promise<string[]>
⋮----
async function loadSidecarIndex(): Promise<Map<string,
⋮----
// Ignore malformed sidecars; the organizer can regenerate them.
⋮----
function toVideoMatch(item: FaceMetadataRequestItem, sidecar:
⋮----
export async function POST(request: NextRequest)
````

## File: src/app/api/spiritflix/gallery/image/route.ts
````typescript
import { readFile, stat } from "node:fs/promises";
import path from "node:path";
import { NextRequest, NextResponse } from "next/server";
⋮----
function galleryRootCandidates(): string[]
⋮----
async function exists(target: string): Promise<boolean>
⋮----
async function findGalleryRoot(): Promise<string>
⋮----
function contentTypeFor(fileName: string): string
⋮----
function isSafeModelSlug(value: string): boolean
⋮----
export async function GET(request: NextRequest)
````

## File: src/app/api/spiritflix/gallery/route.ts
````typescript
import { readdir, readFile, stat } from "node:fs/promises";
import path from "node:path";
import { NextResponse } from "next/server";
import type { SpiritFlixGalleryItem, SpiritFlixGalleryResponse } from "@/lib/spiritflix-types";
⋮----
interface EnrolledGroup {
  name?: string;
  slug?: string;
  model_slug?: string;
}
⋮----
interface EnrolledPayload {
  groups?: EnrolledGroup[];
}
⋮----
interface GallerySidecar {
  model_name?: string;
  model_key?: string;
  model_slug?: string;
  collection?: string;
  uploaded_at?: string;
  content_type?: string;
  size_bytes?: number;
}
⋮----
function normalizeNameKey(value = ""): string
⋮----
function slugToName(slug: string): string
⋮----
function galleryRootCandidates(): string[]
⋮----
async function exists(target: string): Promise<boolean>
⋮----
async function findGalleryRoot(): Promise<string>
⋮----
async function readJson<T>(target: string, fallback: T): Promise<T>
⋮----
async function readModelNames(galleryRoot: string): Promise<Map<string, string>>
⋮----
async function readGallerySidecar(imagePath: string): Promise<GallerySidecar>
⋮----
function contentTypeFor(fileName: string, sidecar: GallerySidecar): string
⋮----
async function scanGallery(): Promise<SpiritFlixGalleryResponse>
⋮----
export async function GET()
````

## File: src/app/api/spiritflix/jellyfin-image/route.ts
````typescript
import { NextRequest, NextResponse } from "next/server";
import { normalizeJellyfinServerUrl } from "@/lib/spiritflix-jellyfin-client";
⋮----
function isAllowedServer(serverUrl: string): boolean
⋮----
export async function POST(request: NextRequest)
````

## File: src/app/api/spiritflix/jellyfin/route.ts
````typescript
import { NextRequest, NextResponse } from "next/server";
import { normalizeJellyfinServerUrl } from "@/lib/spiritflix-jellyfin-client";
⋮----
interface ProxyBody {
  serverUrl?: string;
  path?: string;
  method?: string;
  body?: unknown;
  authorization?: string;
}
⋮----
function isAllowedServer(serverUrl: string): boolean
⋮----
export async function POST(request: NextRequest)
````

## File: src/app/api/spiritflix/stream/route.ts
````typescript
import { NextRequest, NextResponse } from "next/server";
import { normalizeJellyfinServerUrl } from "@/lib/spiritflix-jellyfin-client";
⋮----
function isAllowedServer(serverUrl: string): boolean
⋮----
export async function GET(request: NextRequest)
````

## File: src/app/spiritflix/page.tsx
````typescript
import { SpiritFlixApp } from "@/components/spiritflix/SpiritFlixApp";
⋮----
export default function SpiritFlixPage()
````

## File: src/components/spiritflix/__tests__/SpiritFlixHome.test.tsx
````typescript
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { SpiritFlixHome } from "../SpiritFlixHome";
import type { JellyfinClient } from "@/lib/spiritflix-jellyfin-client";
import type { JellyfinItem, SpiritFlixGalleryResponse, SpiritFlixHomeData } from "@/lib/spiritflix-types";
⋮----
function createClient(gallery: SpiritFlixGalleryResponse = emptyGallery): JellyfinClient
⋮----
function createData(overrides: Partial<SpiritFlixHomeData> =
⋮----
client=
⋮----
onLogout=
onRefresh=
⋮----
onSelectHome=
onSelectLibrary=
onOpenDetails=
````

## File: src/components/spiritflix/__tests__/SpiritFlixPlayer.test.tsx
````typescript
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { SpiritFlixPlayer } from "../SpiritFlixPlayer";
import type { JellyfinClient } from "@/lib/spiritflix-jellyfin-client";
import type { JellyfinItem } from "@/lib/spiritflix-types";
⋮----
function createClient(): JellyfinClient
⋮----
client=
⋮----
onPlaybackProgress=
onToggleFavorite=
onSelectItem=
⋮----
return Object.assign([...touches], {
    item: (index: number) => touches[index] ?? null,
  });
⋮----
observe()
unobserve()
disconnect()
````

## File: src/components/spiritflix/SpiritFlixApp.tsx
````typescript
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  clearStoredSession,
  getStoredSession,
  JellyfinClient,
  isPlayableItem,
  normalizeJellyfinServerUrl,
  SPIRITFLIX_DEFAULT_SERVER,
  storeSession,
} from "@/lib/spiritflix-jellyfin-client";
import type {
  JellyfinItem,
  SpiritFlixHomeData,
  SpiritFlixServerInfo,
  SpiritFlixSession,
} from "@/lib/spiritflix-types";
import { hasResumeProgress } from "@/lib/spiritflix-resume";
import { SpiritFlixHome } from "./SpiritFlixHome";
import { SpiritFlixLogin } from "./SpiritFlixLogin";
import { SpiritFlixDetailsModal } from "./SpiritFlixDetailsModal";
import { SpiritFlixPlayer } from "./SpiritFlixPlayer";
⋮----
export interface SpiritFlixPlaybackQueue {
  items: JellyfinItem[];
  currentIndex: number;
  sourceTitle: string;
  startPositionTicks?: number;
}
⋮----
export interface SpiritFlixPlaybackProgress {
  itemId: string;
  item?: JellyfinItem;
  positionTicks: number;
  isEnded?: boolean;
}
⋮----
function isMediaLibrary(library:
⋮----
function uniqueItems(items: JellyfinItem[]): JellyfinItem[]
⋮----
function getLastPlayedMs(item: JellyfinItem): number
⋮----
function sortByLastPlayed(items: JellyfinItem[]): JellyfinItem[]
⋮----
function hasWatchActivity(item: JellyfinItem): boolean
⋮----
function isKenshinItem(item: JellyfinItem): boolean
⋮----
function byEpisodeOrder(left: JellyfinItem, right: JellyfinItem): number
⋮----
function applyPlaybackProgress(item: JellyfinItem, progress: SpiritFlixPlaybackProgress): JellyfinItem
⋮----
function upsertPlaybackItem(items: JellyfinItem[], item: JellyfinItem): JellyfinItem[]
⋮----
function upsertWatchHistoryItem(items: JellyfinItem[], item: JellyfinItem): JellyfinItem[]
⋮----
function applyFavoriteState(item: JellyfinItem, itemId: string, isFavorite: boolean): JellyfinItem
⋮----
function upsertFavoriteItem(items: JellyfinItem[], item: JellyfinItem): JellyfinItem[]
⋮----
const refreshPlaybackState = () =>
const handleVisibilityChange = () =>
⋮----
const handleLogin = async (username: string, password: string, targetServerUrl: string) =>
⋮----
const handleLogout = () =>
⋮----
const buildQueue = (
    item: JellyfinItem,
    items: JellyfinItem[] = [item],
    sourceTitle = "Direct play",
    startPositionTicks?: number,
) =>
⋮----
const handlePlay = (item: JellyfinItem, queueItems?: JellyfinItem[], sourceTitle?: string, startPositionTicks?: number) =>
⋮----
const handleQueueSelect = (item: JellyfinItem) =>
⋮----
const handleOpenDetails = (item: JellyfinItem) =>
⋮----
const handleSearch = (term: string) =>
⋮----
onSelectLibrary=
⋮----
onPlay=
````

## File: src/components/spiritflix/SpiritFlixCard.tsx
````typescript
import { Info, Play } from "lucide-react";
import { isPlayableItem, type JellyfinClient } from "@/lib/spiritflix-jellyfin-client";
import { getResumeProgressPercent, getResumeSlotLabel, hasResumeProgress } from "@/lib/spiritflix-resume";
import type { FaceOrganizerVideoMatch, JellyfinItem } from "@/lib/spiritflix-types";
import { SpiritFlixImage } from "./SpiritFlixImage";
⋮----
interface SpiritFlixCardProps {
  client: JellyfinClient;
  item: JellyfinItem;
  variant?: "poster" | "landscape";
  showResume?: boolean;
  faceMatch?: FaceOrganizerVideoMatch;
  modelName?: string;
  playOnPrimaryTap?: boolean;
  onOpenDetails: (item: JellyfinItem) => void;
  onPlay: (item: JellyfinItem, startPositionTicks?: number) => void;
}
````

## File: src/components/spiritflix/SpiritFlixDetailsModal.tsx
````typescript
import { Calendar, Clock, Heart, Play, RotateCcw, X } from "lucide-react";
import { formatRuntime, isPlayableItem, type JellyfinClient } from "@/lib/spiritflix-jellyfin-client";
import { getResumeSlotLabel, hasResumeProgress } from "@/lib/spiritflix-resume";
import type { JellyfinItem } from "@/lib/spiritflix-types";
import { SpiritFlixImage } from "./SpiritFlixImage";
⋮----
interface SpiritFlixDetailsModalProps {
  client: JellyfinClient;
  item: JellyfinItem;
  onClose: () => void;
  onPlay: (item: JellyfinItem) => void;
}
````

## File: src/components/spiritflix/SpiritFlixHome.tsx
````typescript
// Isolated Continue Watching v1 - Dedicated gooner user lane - Z Fold optimized
⋮----
// Face Organizer integration v1 - Model sorting from sidecars + known_performers - Z Fold optimized
// Layout v2 - Model-centric + Grid/List toggle - Z Fold optimized - Codex executed 2026-06-04
⋮----
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion } from "framer-motion";
import {
  ChevronLeft,
  ChevronRight,
  Clock3,
  Grid2X2,
  Images,
  List,
  LogOut,
  Maximize2,
  Pause,
  Play,
  RefreshCw,
  RotateCcw,
  Search,
  Server,
  Settings,
  SlidersHorizontal,
  Shuffle,
  Sparkles,
  Timer,
  X,
} from "lucide-react";
import { formatRuntime, isPlayableItem, type JellyfinClient } from "@/lib/spiritflix-jellyfin-client";
import {
  getResumePositionTicks,
  getResumeProgressPercent,
  getResumeSlotLabel,
  getTimeLeftLabel,
  hasResumeProgress,
} from "@/lib/spiritflix-resume";
import type {
  FaceOrganizerMetadataResponse,
  FaceOrganizerStatus,
  FaceOrganizerVideoMatch,
  JellyfinItem,
  SpiritFlixGalleryItem,
  SpiritFlixGalleryResponse,
  SpiritFlixHomeData,
  SpiritFlixServerInfo,
  SpiritFlixSession,
} from "@/lib/spiritflix-types";
import { SpiritFlixRail } from "./SpiritFlixRail";
import { SpiritFlixImage } from "./SpiritFlixImage";
⋮----
interface SpiritFlixHomeProps {
  client: JellyfinClient;
  data: SpiritFlixHomeData;
  loading: boolean;
  error: string;
  session: SpiritFlixSession;
  searchTerm: string;
  serverInfo: SpiritFlixServerInfo | null;
  onLogout: () => void;
  onRefresh: () => void;
  onSearch: (term: string) => void;
  onSelectHome: () => void;
  onSelectLibrary: (libraryId: string) => void;
  onOpenDetails: (item: JellyfinItem) => void;
  onPlay: (item: JellyfinItem, queueItems?: JellyfinItem[], sourceTitle?: string, startPositionTicks?: number) => void;
}
⋮----
type LibraryViewMode = "grid" | "list" | "history" | "gallery";
type LibrarySortMode = "model" | "title" | "dateAdded" | "duration";
type LibrarySortDirection = "asc" | "desc";
⋮----
interface ModelGroup {
  name: string;
  count: number;
  indexedCount: number;
  liveSourceCount?: number;
  items: JellyfinItem[];
  representative: JellyfinItem;
  source: "face-organizer" | "jellyfin";
  status: FaceOrganizerStatus;
  confidence?: number;
}
⋮----
function displayLibraryName(name?: string): string
⋮----
function getModelAliasKey(name: string): string
⋮----
function normalizeModelName(name: string): string
⋮----
function getOrganizerModelName(name: string, faceMetadata: FaceOrganizerMetadataResponse | null): string | undefined
⋮----
function getCanonicalModelName(name: string, faceMetadata: FaceOrganizerMetadataResponse | null): string
⋮----
function getLiveSourceCount(name: string, faceMetadata: FaceOrganizerMetadataResponse | null): number | undefined
⋮----
function isNonModelFolderName(name?: string): boolean
⋮----
function getModelName(item: JellyfinItem): string
⋮----
function getFaceMatch(item: JellyfinItem, faceMetadata: FaceOrganizerMetadataResponse | null): FaceOrganizerVideoMatch | undefined
⋮----
function hasIdentifiedFace(match?: FaceOrganizerVideoMatch): boolean
⋮----
function getDisplayModelName(item: JellyfinItem, faceMetadata: FaceOrganizerMetadataResponse | null): string
⋮----
function getStatusRank(status?: FaceOrganizerStatus): number
⋮----
function buildModelGroups(items: JellyfinItem[], faceMetadata: FaceOrganizerMetadataResponse | null): ModelGroup[]
⋮----
function shuffleItems(items: JellyfinItem[]): JellyfinItem[]
⋮----
function getNewThisWeekCount(items: JellyfinItem[]): number
⋮----
function getDateCreatedMs(item: JellyfinItem): number
⋮----
function getLastPlayedMs(item: JellyfinItem): number
⋮----
function getLastPlayedLabel(item: JellyfinItem): string
⋮----
function getModelSlug(name: string): string
⋮----
function galleryItemMatchesModel(item: SpiritFlixGalleryItem, modelName: string): boolean
⋮----
function getGalleryDateLabel(item: SpiritFlixGalleryItem): string
⋮----
function getDurationTicks(item: JellyfinItem): number
⋮----
function compareOptionalNumber(left: number, right: number, direction: LibrarySortDirection): number
⋮----
function getSortModeLabel(sortMode: LibrarySortMode): string
⋮----
function getSortDirectionLabel(sortDirection: LibrarySortDirection): string
⋮----
interface LibraryFeedCardProps {
  client: JellyfinClient;
  item: JellyfinItem;
  playOnPrimaryTap: boolean;
  onOpenDetails: (item: JellyfinItem) => void;
  onPlay: (item: JellyfinItem, startPositionTicks?: number) => void;
}
⋮----
const handleKeyDown = (event: KeyboardEvent) =>
⋮----
const toggleFullscreen = async () =>
⋮----
const handleRefresh = () =>
⋮----
const updateMode = ()
⋮----
const playShuffle = (scope: "library" | "model") =>
⋮----
const clearLongPressTimer = () =>
⋮----
const startShuffleLongPress = () =>
⋮----
const handleShuffleClick = () =>
⋮----
const scrollRow = (ref:
⋮----
onClick=
⋮----
onPlay(selectedItem, visibleLibraryItems, selectedModelGroup?.name ?? libraryTitle, startPositionTicks)
````

## File: src/components/spiritflix/SpiritFlixImage.tsx
````typescript
import Image from "next/image";
import { useEffect, useState } from "react";
import type { JellyfinClient } from "@/lib/spiritflix-jellyfin-client";
import type { JellyfinItem } from "@/lib/spiritflix-types";
⋮----
interface SpiritFlixImageProps {
  client: JellyfinClient;
  item: JellyfinItem;
  type?: "Primary" | "Backdrop" | "Thumb";
  width?: number;
  alt?: string;
  className?: string;
}
⋮----
function imageFallbackOrder(type: "Primary" | "Backdrop" | "Thumb"): Array<"Primary" | "Backdrop" | "Thumb">
⋮----
export function SpiritFlixImage({
  client,
  item,
  type = "Primary",
  width = 500,
  alt = "",
  className,
}: SpiritFlixImageProps)
⋮----
async function loadImage()
⋮----
// Try the next Jellyfin image type before falling back to the letter tile.
⋮----
height=
````

## File: src/components/spiritflix/SpiritFlixLogin.tsx
````typescript
import { FormEvent, useState } from "react";
import { Eye, EyeOff, LogIn, RefreshCw, Server, ShieldCheck } from "lucide-react";
import { SPIRITFLIX_FALLBACK_SERVER } from "@/lib/spiritflix-jellyfin-client";
import type { SpiritFlixServerInfo } from "@/lib/spiritflix-types";
⋮----
interface SpiritFlixLoginProps {
  serverUrl: string;
  serverInfo: SpiritFlixServerInfo | null;
  serverError: string;
  onServerUrlChange: (serverUrl: string) => void;
  onRetry: () => void;
  onLogin: (username: string, password: string, serverUrl: string) => Promise<void>;
}
⋮----
export function SpiritFlixLogin({
  serverUrl,
  serverInfo,
  serverError,
  onServerUrlChange,
  onRetry,
  onLogin,
}: SpiritFlixLoginProps)
⋮----
const handleSubmit = async (event: FormEvent) =>
⋮----
onChange=
````

## File: src/components/spiritflix/SpiritFlixPlayer.tsx
````typescript
import { useCallback, useEffect, useMemo, useRef, useState, type CSSProperties } from "react";
import {
  Activity,
  ChevronsDown,
  Heart,
  Maximize,
  Minimize,
  Pause,
  Play,
  RefreshCw,
  Repeat,
  Repeat1,
  SkipBack,
  SkipForward,
  Volume2,
  VolumeX,
  X,
} from "lucide-react";
import { ticksToSeconds, type JellyfinClient } from "@/lib/spiritflix-jellyfin-client";
import type { JellyfinItem } from "@/lib/spiritflix-types";
import type { SpiritFlixPlaybackProgress, SpiritFlixPlaybackQueue } from "./SpiritFlixApp";
⋮----
interface SpiritFlixPlayerProps {
  client: JellyfinClient;
  item: JellyfinItem;
  queue: SpiritFlixPlaybackQueue | null;
  startPositionTicks?: number;
  onPlaybackProgress: (progress: SpiritFlixPlaybackProgress) => void;
  onToggleFavorite: (item: JellyfinItem, isFavorite: boolean) => void;
  onSelectItem: (item: JellyfinItem) => void;
  onClose: () => void;
}
⋮----
type FitMode = "fit" | "fill";
type RepeatMode = "off" | "queue" | "one";
⋮----
interface PlaybackDiagnostics {
  bufferedAheadSeconds: number;
  droppedFrames: number;
  decodedFrames: number;
  networkState: number;
  readyState: number;
  playbackRate: number;
  stallCount: number;
  totalStallMs: number;
  serverDelayMs: number | null;
  streamMode: "direct" | "hls";
}
⋮----
function secondsToTicks(seconds: number): number
⋮----
function formatTime(seconds: number): string
⋮----
function getStoredFitMode(): FitMode
⋮----
function isRepeatMode(value: string | null): value is RepeatMode
⋮----
function getStoredRepeatMode(): RepeatMode
⋮----
function getStoredVolume(): number
⋮----
function getStoredMuted(): boolean
⋮----
function isInteractiveTarget(target: EventTarget | null): boolean
⋮----
function getTouchAt(
  touches: { length: number; item?: (index: number) => { clientX: number; clientY: number } | null; [index: number]: { clientX: number; clientY: number } | undefined },
  index: number,
):
⋮----
function getBufferedAheadSeconds(video: HTMLVideoElement): number
⋮----
function getFrameStats(video: HTMLVideoElement):
⋮----
const cycleRepeatMode = () =>
⋮----
const selectNextItem = () =>
⋮----
const setup = async () =>
⋮----
const handleDirectError = async () =>
⋮----
const flushForMobileSuspend = () =>
const handleVisibilityChange = () =>
⋮----
const handleFullscreenChange = () =>
⋮----
const updateShellSize = () =>
⋮----
const handleKeyDown = (event: KeyboardEvent) =>
⋮----
const handlePointerDown = (event: React.PointerEvent<HTMLElement>) =>
⋮----
const handlePointerUp = (event: React.PointerEvent<HTMLElement>) =>
⋮----
const touchDistance = (touches:
⋮----
setIsLoading(true);
⋮----
onTimeUpdate=
⋮----
onChange=
⋮----
setIsVolumeOpen(true);
revealControls(true);
````

## File: src/components/spiritflix/SpiritFlixRail.tsx
````typescript
import { useRef } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import type { JellyfinClient } from "@/lib/spiritflix-jellyfin-client";
import type { JellyfinItem } from "@/lib/spiritflix-types";
import { SpiritFlixCard } from "./SpiritFlixCard";
⋮----
interface SpiritFlixRailProps {
  title: string;
  variant?: "poster" | "landscape";
  client: JellyfinClient;
  items: JellyfinItem[];
  emptyText: string;
  playOnPrimaryTap?: boolean;
  onOpenDetails: (item: JellyfinItem) => void;
  onPlay: (item: JellyfinItem, queueItems?: JellyfinItem[], sourceTitle?: string, startPositionTicks?: number) => void;
}
⋮----
const scroll = (direction: "left" | "right") =>
⋮----
onPlay=
````

## File: src/lib/spiritflix-jellyfin-client.ts
````typescript
import type {
  JellyfinAuthResponse,
  JellyfinItem,
  JellyfinItemsResponse,
  JellyfinLibrary,
  FaceOrganizerMetadataResponse,
  SpiritFlixGalleryResponse,
  SpiritFlixServerInfo,
  SpiritFlixSession,
} from "./spiritflix-types";
⋮----
export function getStoredSession(): SpiritFlixSession | null
⋮----
export function storeSession(session: SpiritFlixSession): void
⋮----
export function clearStoredSession(): void
⋮----
function getDeviceId(): string
⋮----
function authHeader(token?: string): string
⋮----
export function normalizeJellyfinServerUrl(serverUrl: string): string
⋮----
function toQuery(params: Record<string, string | number | boolean | undefined>): string
⋮----
export class JellyfinClient
⋮----
constructor(serverUrl: string, token?: string, userId?: string)
⋮----
withSession(session: SpiritFlixSession): JellyfinClient
⋮----
private async request<T>(path: string, init: RequestInit =
⋮----
async checkPublicInfo(): Promise<SpiritFlixServerInfo>
⋮----
async login(username: string, password: string): Promise<SpiritFlixSession>
⋮----
async getLibraries(): Promise<JellyfinLibrary[]>
⋮----
async getLibraryItems(parentId: string, searchTerm = "", limit?: number): Promise<JellyfinItem[]>
⋮----
async getPlaylistItems(playlistId: string): Promise<JellyfinItem[]>
⋮----
async getPlaylists(): Promise<JellyfinItem[]>
⋮----
async getContinueWatching(parentId?: string): Promise<JellyfinItem[]>
⋮----
async getLibraryResumeItems(parentId: string): Promise<JellyfinItem[]>
⋮----
async getWatchHistory(parentId?: string): Promise<JellyfinItem[]>
⋮----
async getLatestAdded(): Promise<JellyfinItem[]>
⋮----
async getFavorites(): Promise<JellyfinItem[]>
⋮----
async getLibraryFavoriteItems(parentId: string): Promise<JellyfinItem[]>
⋮----
async setFavorite(itemId: string, isFavorite: boolean): Promise<void>
⋮----
async getFaceOrganizerMetadata(items: JellyfinItem[]): Promise<FaceOrganizerMetadataResponse>
⋮----
async getGallery(): Promise<SpiritFlixGalleryResponse>
⋮----
private async getItemsByQuery(extra: Record<string, string | number>): Promise<JellyfinItem[]>
⋮----
getImageUrl(item: JellyfinItem, type: "Primary" | "Backdrop" | "Thumb" = "Primary", width = 500): string
⋮----
async getImageObjectUrl(item: JellyfinItem, type: "Primary" | "Backdrop" | "Thumb" = "Primary", width = 500): Promise<string>
⋮----
getStreamUrl(itemId: string): string
⋮----
getHlsUrl(itemId: string): string
⋮----
async reportPlayback(
    itemId: string,
    event: "Start" | "Progress" | "Stopped",
    positionTicks: number,
    isPaused = false,
    options: { keepalive?: boolean } = {},
): Promise<void>
⋮----
export function isPlayableItem(item: JellyfinItem): boolean
⋮----
export function isPlaylistItem(item: JellyfinItem): boolean
⋮----
export function ticksToSeconds(ticks?: number): number
⋮----
export function formatRuntime(ticks?: number): string
````

## File: src/lib/spiritflix-resume.ts
````typescript
import type { JellyfinItem } from "./spiritflix-types";
import { ticksToSeconds } from "./spiritflix-jellyfin-client";
⋮----
export function formatResumeTime(seconds: number): string
⋮----
export function getResumePositionTicks(item: JellyfinItem): number
⋮----
export function getResumeProgressPercent(item: JellyfinItem): number
⋮----
export function hasResumeProgress(item: JellyfinItem): boolean
⋮----
export function getResumeSlotLabel(item: JellyfinItem): string
⋮----
export function getTimeLeftLabel(item: JellyfinItem): string
````

## File: src/lib/spiritflix-types.ts
````typescript
export interface SpiritFlixSession {
  serverUrl: string;
  accessToken: string;
  userId: string;
  username: string;
}
⋮----
export interface SpiritFlixServerInfo {
  LocalAddress?: string;
  ServerName?: string;
  Version?: string;
  ProductName?: string;
  OperatingSystem?: string;
}
⋮----
export interface JellyfinAuthResponse {
  AccessToken: string;
  User: {
    Id: string;
    Name: string;
  };
}
⋮----
export interface JellyfinItem {
  Id: string;
  Name: string;
  Type: string;
  ChildCount?: number;
  MediaType?: string;
  Path?: string;
  SeriesName?: string;
  Overview?: string;
  ProductionYear?: number;
  DateCreated?: string;
  IndexNumber?: number;
  ParentIndexNumber?: number;
  RunTimeTicks?: number;
  Genres?: string[];
  People?: {
    Id?: string;
    Name: string;
    Type?: string;
    Role?: string;
  }[];
  ImageTags?: {
    Primary?: string;
    Thumb?: string;
    Logo?: string;
  };
  BackdropImageTags?: string[];
  UserData?: {
    PlaybackPositionTicks?: number;
    IsFavorite?: boolean;
    Played?: boolean;
    PlayedPercentage?: number;
    PlayCount?: number;
    LastPlayedDate?: string;
  };
  MediaSources?: {
    Id?: string;
    Path?: string;
    RunTimeTicks?: number;
    Size?: number;
  }[];
}
⋮----
export type FaceOrganizerStatus = "confirmed" | "needs_review" | "unknown" | "unscanned";
⋮----
export interface FaceOrganizerPerformer {
  id?: string;
  name: string;
  aliases?: string[];
  confidence?: number;
  similarity?: number;
  status?: string;
  verificationNeeded?: boolean;
  source?: "known_performers" | "sidecar" | "jellyfin";
}
⋮----
export interface FaceOrganizerVideoMatch {
  itemId: string;
  itemPath?: string;
  sidecarPath?: string;
  videoPath?: string;
  primaryPerformer?: FaceOrganizerPerformer;
  performers: FaceOrganizerPerformer[];
  status: FaceOrganizerStatus;
  label: string;
  confidence?: number;
  verificationNeeded: boolean;
  facesDetected?: number;
  generatedAt?: string;
}
⋮----
export interface FaceOrganizerMetadataResponse {
  knownPerformers: FaceOrganizerPerformer[];
  enrolledSources?: Record<
    string,
    {
      name: string;
      slug?: string;
      candidateVideos: number;
      enrolledScreens?: number;
      recommendationSourceVideos?: string[];
      refreshedAt?: string;
      source?: "enrolled" | "model_index";
    }
  >;
  videos: Record<string, FaceOrganizerVideoMatch>;
  scannedCount: number;
  generatedAt: string;
}
⋮----
export interface SpiritFlixGalleryItem {
  id: string;
  modelName: string;
  modelKey: string;
  modelSlug: string;
  fileName: string;
  src: string;
  thumbnailSrc?: string;
  collection?: string;
  uploadedAt?: string;
  sizeBytes?: number;
  contentType?: string;
}
⋮----
export interface SpiritFlixGalleryGroup {
  name: string;
  modelKey: string;
  modelSlug: string;
  itemCount: number;
}
⋮----
export interface SpiritFlixGalleryResponse {
  schema: "spiritflix-model-gallery/v1";
  generatedAt: string;
  items: SpiritFlixGalleryItem[];
  groups: SpiritFlixGalleryGroup[];
  summary: {
    galleryItems: number;
    modelsWithGallery: number;
  };
}
⋮----
export interface JellyfinLibrary {
  Id: string;
  Name: string;
  Type?: string;
  CollectionType?: string;
}
⋮----
export interface JellyfinItemsResponse<T> {
  Items?: T[];
  TotalRecordCount?: number;
}
⋮----
export interface SpiritFlixHomeData {
  libraries: JellyfinLibrary[];
  playlists: JellyfinItem[];
  selectedLibraryId: string | null;
  featuredItems: JellyfinItem[];
  libraryItems: JellyfinItem[];
  continueWatching: JellyfinItem[];
  watchHistory: JellyfinItem[];
  latestAdded: JellyfinItem[];
  favorites: JellyfinItem[];
}
````

## File: src/lib/spiritflix/jellyfin-client.ts
````typescript
import type {
  JellyfinAuthResponse,
  JellyfinItem,
  JellyfinItemsResponse,
  JellyfinLibrary,
  SpiritFlixServerInfo,
  SpiritFlixSession,
} from "./types";
⋮----
export function getStoredSession(): SpiritFlixSession | null
⋮----
export function storeSession(session: SpiritFlixSession): void
⋮----
export function clearStoredSession(): void
⋮----
function getDeviceId(): string
⋮----
function authHeader(token?: string): string
⋮----
export function normalizeJellyfinServerUrl(serverUrl: string): string
⋮----
function toQuery(params: Record<string, string | number | boolean | undefined>): string
⋮----
export class JellyfinClient
⋮----
constructor(serverUrl: string, token?: string, userId?: string)
⋮----
withSession(session: SpiritFlixSession): JellyfinClient
⋮----
private async request<T>(path: string, init: RequestInit =
⋮----
async checkPublicInfo(): Promise<SpiritFlixServerInfo>
⋮----
async login(username: string, password: string): Promise<SpiritFlixSession>
⋮----
async getLibraries(): Promise<JellyfinLibrary[]>
⋮----
async getLibraryItems(parentId: string, searchTerm = "", limit = 80): Promise<JellyfinItem[]>
⋮----
async getPlaylistItems(playlistId: string): Promise<JellyfinItem[]>
⋮----
async getPlaylists(): Promise<JellyfinItem[]>
⋮----
async getContinueWatching(parentId?: string): Promise<JellyfinItem[]>
⋮----
async getLatestAdded(): Promise<JellyfinItem[]>
⋮----
async getFavorites(): Promise<JellyfinItem[]>
⋮----
private async getItemsByQuery(extra: Record<string, string | number>): Promise<JellyfinItem[]>
⋮----
getImageUrl(item: JellyfinItem, type: "Primary" | "Backdrop" | "Thumb" = "Primary", width = 500): string
⋮----
async getImageObjectUrl(item: JellyfinItem, type: "Primary" | "Backdrop" | "Thumb" = "Primary", width = 500): Promise<string>
⋮----
getStreamUrl(itemId: string): string
⋮----
getHlsUrl(itemId: string): string
⋮----
async reportPlayback(itemId: string, event: "Start" | "Progress" | "Stopped", positionTicks: number, isPaused = false): Promise<void>
⋮----
export function isPlayableItem(item: JellyfinItem): boolean
⋮----
export function isPlaylistItem(item: JellyfinItem): boolean
⋮----
export function ticksToSeconds(ticks?: number): number
⋮----
export function formatRuntime(ticks?: number): string
````

## File: src/lib/spiritflix/resume.ts
````typescript
import type { JellyfinItem } from "./types";
import { ticksToSeconds } from "./jellyfin-client";
⋮----
export function formatResumeTime(seconds: number): string
⋮----
export function getResumePositionTicks(item: JellyfinItem): number
⋮----
export function getResumeProgressPercent(item: JellyfinItem): number
⋮----
export function hasResumeProgress(item: JellyfinItem): boolean
⋮----
export function getResumeSlotLabel(item: JellyfinItem): string
⋮----
export function getTimeLeftLabel(item: JellyfinItem): string
````

## File: src/lib/spiritflix/types.ts
````typescript
export interface SpiritFlixSession {
  serverUrl: string;
  accessToken: string;
  userId: string;
  username: string;
}
⋮----
export interface SpiritFlixServerInfo {
  LocalAddress?: string;
  ServerName?: string;
  Version?: string;
  ProductName?: string;
  OperatingSystem?: string;
}
⋮----
export interface JellyfinAuthResponse {
  AccessToken: string;
  User: {
    Id: string;
    Name: string;
  };
}
⋮----
export interface JellyfinItem {
  Id: string;
  Name: string;
  Type: string;
  ChildCount?: number;
  MediaType?: string;
  Path?: string;
  SeriesName?: string;
  Overview?: string;
  ProductionYear?: number;
  DateCreated?: string;
  IndexNumber?: number;
  ParentIndexNumber?: number;
  RunTimeTicks?: number;
  Genres?: string[];
  People?: {
    Id?: string;
    Name: string;
    Type?: string;
    Role?: string;
  }[];
  ImageTags?: {
    Primary?: string;
    Thumb?: string;
    Logo?: string;
  };
  BackdropImageTags?: string[];
  UserData?: {
    PlaybackPositionTicks?: number;
    IsFavorite?: boolean;
    Played?: boolean;
    PlayedPercentage?: number;
    PlayCount?: number;
    LastPlayedDate?: string;
  };
}
⋮----
export interface JellyfinLibrary {
  Id: string;
  Name: string;
  Type?: string;
  CollectionType?: string;
}
⋮----
export interface JellyfinItemsResponse<T> {
  Items?: T[];
  TotalRecordCount?: number;
}
⋮----
export interface SpiritFlixHomeData {
  libraries: JellyfinLibrary[];
  playlists: JellyfinItem[];
  selectedLibraryId: string | null;
  featuredItems: JellyfinItem[];
  libraryItems: JellyfinItem[];
  continueWatching: JellyfinItem[];
  latestAdded: JellyfinItem[];
  favorites: JellyfinItem[];
}
````

## File: src/styles/spiritflix.css
````css
.spiritflix-shell {
⋮----
.spiritflix-shell *,
⋮----
.spiritflix-shell button,
⋮----
.spiritflix-shell button {
⋮----
.spiritflix-shell button:hover {
⋮----
.spiritflix-brand {
⋮----
.spiritflix-brand__sigil {
⋮----
.spiritflix-login {
⋮----
.spiritflix-login__backdrop {
⋮----
.spiritflix-login__panel {
⋮----
.spiritflix-login__panel::before,
⋮----
.spiritflix-login h1 {
⋮----
.spiritflix-login__copy,
⋮----
.spiritflix-health,
⋮----
.spiritflix-health {
⋮----
.spiritflix-health.is-ok {
⋮----
.spiritflix-health button,
⋮----
.spiritflix-health button:hover,
⋮----
.spiritflix-login__form {
⋮----
.spiritflix-login label {
⋮----
.spiritflix-login input,
⋮----
.spiritflix-password-field {
⋮----
.spiritflix-password-field input {
⋮----
.spiritflix-password-field button {
⋮----
.spiritflix-login input {
⋮----
.spiritflix-primary-button,
⋮----
.spiritflix-primary-button {
⋮----
.spiritflix-primary-button:hover {
⋮----
.spiritflix-secondary-button,
⋮----
.spiritflix-link-button {
⋮----
.spiritflix-error {
⋮----
.spiritflix-home {
⋮----
.spiritflix-restore {
⋮----
.spiritflix-topbar {
⋮----
.spiritflix-topbar__links,
⋮----
.spiritflix-topbar__links {
⋮----
.spiritflix-topbar__links::-webkit-scrollbar {
⋮----
.spiritflix-topbar__links button {
⋮----
.spiritflix-topbar__links button:first-child,
⋮----
.spiritflix-topbar__links button.is-active {
⋮----
.spiritflix-search {
⋮----
.spiritflix-search:focus-within {
⋮----
.spiritflix-search input {
⋮----
.spiritflix-source-pill,
⋮----
.spiritflix-source-pill span,
⋮----
.spiritflix-hero {
⋮----
.spiritflix-hero--empty {
⋮----
.spiritflix-hero__ambient,
⋮----
.spiritflix-hero__ambient {
⋮----
.spiritflix-hero__image {
⋮----
.spiritflix-hero__shade {
⋮----
.spiritflix-hero__content {
⋮----
.spiritflix-kicker {
⋮----
.spiritflix-hero h1 {
⋮----
.spiritflix-hero__meta {
⋮----
.spiritflix-hero p {
⋮----
.spiritflix-hero__actions {
⋮----
.spiritflix-rail__track::-webkit-scrollbar {
⋮----
.spiritflix-rows {
⋮----
.spiritflix-rail {
⋮----
.spiritflix-rail__header {
⋮----
.spiritflix-rail h2 {
⋮----
.spiritflix-rail__controls {
⋮----
.spiritflix-rail__controls button {
⋮----
.spiritflix-rail__track {
⋮----
.spiritflix-rail--poster .spiritflix-rail__track {
⋮----
.spiritflix-rail--landscape .spiritflix-rail__track {
⋮----
.spiritflix-card {
⋮----
.spiritflix-card__poster {
⋮----
.spiritflix-card--poster .spiritflix-card__poster {
⋮----
.spiritflix-card--landscape .spiritflix-card__poster {
⋮----
.spiritflix-card__poster:hover {
⋮----
.spiritflix-card__poster img,
⋮----
.spiritflix-card__poster img {
⋮----
.spiritflix-card:hover .spiritflix-card__poster img {
⋮----
.spiritflix-card__veil {
⋮----
.spiritflix-image-fallback {
⋮----
.spiritflix-card__progress {
⋮----
.spiritflix-card__progress span,
⋮----
.spiritflix-card__resume-badge {
⋮----
.spiritflix-card__face-badge {
⋮----
.spiritflix-card__meta h3 {
⋮----
.spiritflix-card__meta p {
⋮----
.spiritflix-card__actions {
⋮----
.spiritflix-card__actions button {
⋮----
.spiritflix-library-v2 {
⋮----
.spiritflix-library-v2__header {
⋮----
.spiritflix-library-v2__header h2 {
⋮----
.spiritflix-view-toggle {
⋮----
.spiritflix-view-toggle button {
⋮----
.spiritflix-view-toggle button.is-active,
⋮----
.spiritflix-library-stats {
⋮----
.spiritflix-library-stat {
⋮----
.spiritflix-library-stat strong,
⋮----
.spiritflix-library-modebar {
⋮----
.spiritflix-library-modebar::-webkit-scrollbar {
⋮----
.spiritflix-library-modebar button {
⋮----
.spiritflix-library-modebar button.is-active {
⋮----
.spiritflix-filter-trigger {
⋮----
.spiritflix-filter-trigger span {
⋮----
.spiritflix-model-tabs {
⋮----
.spiritflix-model-tabs button {
⋮----
.spiritflix-model-tabs button.is-active {
⋮----
.spiritflix-filter-popout {
⋮----
.spiritflix-filter-popout__section {
⋮----
.spiritflix-filter-popout__section > span {
⋮----
.spiritflix-filter-options {
⋮----
.spiritflix-filter-options button {
⋮----
.spiritflix-filter-options button.is-active {
⋮----
.spiritflix-face-note {
⋮----
.spiritflix-face-badge,
⋮----
.spiritflix-face-badge {
⋮----
.spiritflix-face-dot {
⋮----
.spiritflix-face-badge.is-confirmed,
⋮----
.spiritflix-face-badge.is-needs_review,
⋮----
.spiritflix-face-badge.is-unknown,
⋮----
.spiritflix-library-stat strong {
⋮----
.spiritflix-library-stat span {
⋮----
.spiritflix-resume-section {
⋮----
.spiritflix-resume-section__header {
⋮----
.spiritflix-resume-section__header > div:first-child {
⋮----
.spiritflix-resume-section__header h3 {
⋮----
.spiritflix-resume-section__header span {
⋮----
.spiritflix-resume-track {
⋮----
.spiritflix-row-controls {
⋮----
.spiritflix-row-controls button {
⋮----
.spiritflix-row-controls button:hover {
⋮----
.spiritflix-resume-track::-webkit-scrollbar {
⋮----
.spiritflix-resume-card {
⋮----
.spiritflix-resume-card__thumb {
⋮----
.spiritflix-resume-card__thumb img,
⋮----
.spiritflix-resume-card__copy {
⋮----
.spiritflix-resume-card__copy strong,
⋮----
.spiritflix-resume-card__copy strong {
⋮----
.spiritflix-resume-card__copy small {
⋮----
.spiritflix-resume-card__copy span,
⋮----
.spiritflix-resume-card__progress {
⋮----
.spiritflix-resume-card__progress span {
⋮----
.spiritflix-model-section {
⋮----
.spiritflix-model-section__header {
⋮----
.spiritflix-model-section__header > span {
⋮----
.spiritflix-model-strip {
⋮----
.spiritflix-model-strip::-webkit-scrollbar {
⋮----
.spiritflix-model-pill,
⋮----
.spiritflix-model-pill {
⋮----
.spiritflix-model-card {
⋮----
.spiritflix-model-card img,
⋮----
.spiritflix-model-card > span,
⋮----
.spiritflix-model-card strong,
⋮----
.spiritflix-model-card strong {
⋮----
.spiritflix-model-card small {
⋮----
.spiritflix-library-grid {
⋮----
.spiritflix-gallery-grid {
⋮----
.spiritflix-gallery-card {
⋮----
.spiritflix-gallery-card:nth-child(5n + 2),
⋮----
.spiritflix-gallery-card img {
⋮----
.spiritflix-gallery-card:hover img,
⋮----
.spiritflix-gallery-card__shade {
⋮----
.spiritflix-gallery-card__meta {
⋮----
.spiritflix-gallery-card__meta strong,
⋮----
.spiritflix-gallery-card__meta strong {
⋮----
.spiritflix-gallery-card__meta small {
⋮----
.spiritflix-feed-card {
⋮----
.spiritflix-feed-card__media {
⋮----
.spiritflix-feed-card:nth-child(4n + 2) .spiritflix-feed-card__media,
⋮----
.spiritflix-feed-card__media img,
⋮----
.spiritflix-feed-card:hover .spiritflix-feed-card__media img,
⋮----
.spiritflix-feed-card__shade {
⋮----
.spiritflix-feed-card:hover .spiritflix-feed-card__shade,
⋮----
.spiritflix-feed-card__progress {
⋮----
.spiritflix-feed-card__progress span {
⋮----
.spiritflix-feed-card__play {
⋮----
.spiritflix-feed-card:hover .spiritflix-feed-card__play,
⋮----
.spiritflix-feed-card__play:hover {
⋮----
.spiritflix-library-list {
⋮----
.spiritflix-library-row {
⋮----
.spiritflix-library-row__thumb {
⋮----
.spiritflix-library-row__thumb img,
⋮----
.spiritflix-library-row__copy {
⋮----
.spiritflix-library-row__copy strong,
⋮----
.spiritflix-library-row__copy strong {
⋮----
.spiritflix-library-row__copy small {
⋮----
.spiritflix-library-row__copy em {
⋮----
.spiritflix-library-row__copy span {
⋮----
.spiritflix-library-row__play {
⋮----
.spiritflix-shuffle-fab {
⋮----
.spiritflix-shuffle-fab strong,
⋮----
.spiritflix-shuffle-fab strong {
⋮----
.spiritflix-shuffle-fab small {
⋮----
.spiritflix-shuffle-fab:disabled {
⋮----
.spiritflix-empty {
⋮----
.spiritflix-loading,
⋮----
.spiritflix-loading {
⋮----
.spiritflix-gallery-viewer {
⋮----
.spiritflix-gallery-viewer__stage {
⋮----
.spiritflix-gallery-viewer__stage img {
⋮----
.spiritflix-gallery-viewer__top,
⋮----
.spiritflix-gallery-viewer__top {
⋮----
.spiritflix-gallery-viewer__controls {
⋮----
.spiritflix-gallery-viewer button {
⋮----
.spiritflix-gallery-viewer button:disabled {
⋮----
.spiritflix-gallery-viewer__title {
⋮----
.spiritflix-gallery-viewer__title strong,
⋮----
.spiritflix-gallery-viewer__title strong {
⋮----
.spiritflix-gallery-viewer__title span {
⋮----
.spiritflix-gallery-viewer__timer {
⋮----
.spiritflix-gallery-viewer__timer input {
⋮----
.spiritflix-modal,
⋮----
.spiritflix-modal__scrim {
⋮----
.spiritflix-modal__panel {
⋮----
.spiritflix-modal__media {
⋮----
.spiritflix-modal__backdrop {
⋮----
.spiritflix-modal__fade {
⋮----
.spiritflix-modal__content {
⋮----
.spiritflix-modal__layout {
⋮----
.spiritflix-modal__poster {
⋮----
.spiritflix-modal__poster img,
⋮----
.spiritflix-modal__copy {
⋮----
.spiritflix-modal__type {
⋮----
.spiritflix-modal__content h2 {
⋮----
.spiritflix-modal__facts,
⋮----
.spiritflix-modal__facts span,
⋮----
.spiritflix-favorite {
⋮----
.spiritflix-modal__progress {
⋮----
.spiritflix-modal__progress div {
⋮----
.spiritflix-modal__progress > span {
⋮----
.spiritflix-modal__copy p {
⋮----
.spiritflix-modal__actions {
⋮----
.spiritflix-modal__close {
⋮----
.spiritflix-player {
⋮----
.spiritflix-player__stage {
⋮----
.spiritflix-player video {
⋮----
.spiritflix-player.is-fit-fit video {
⋮----
.spiritflix-player.is-fit-fill video {
⋮----
.spiritflix-player__top,
⋮----
.spiritflix-player.is-awake .spiritflix-player__top,
⋮----
.spiritflix-player__top {
⋮----
.spiritflix-player__title {
⋮----
.spiritflix-player__title strong {
⋮----
.spiritflix-player__title span,
⋮----
.spiritflix-player__controls {
⋮----
.spiritflix-player.is-awake .spiritflix-player__controls,
⋮----
.spiritflix-player.is-controls-hidden .spiritflix-player__top,
⋮----
.spiritflix-player.is-controls-hidden .spiritflix-player__controls,
⋮----
.spiritflix-player__diagnostics {
⋮----
.spiritflix-player__diagnostics > div:first-child {
⋮----
.spiritflix-player__diagnostics strong {
⋮----
.spiritflix-player__diagnostics > div:first-child button {
⋮----
.spiritflix-player__diagnostics dl {
⋮----
.spiritflix-player__diagnostics dl div {
⋮----
.spiritflix-player__diagnostics dt,
⋮----
.spiritflix-player__diagnostics dt {
⋮----
.spiritflix-player__diagnostics dd {
⋮----
.spiritflix-player__scrub-row,
⋮----
.spiritflix-player__scrub-row {
⋮----
.spiritflix-player__button-row {
⋮----
.spiritflix-player__transport,
⋮----
.spiritflix-player__transport {
⋮----
.spiritflix-player__tools {
⋮----
.spiritflix-player__button-row button {
⋮----
.spiritflix-player button.is-active {
⋮----
.spiritflix-player__play {
⋮----
.spiritflix-player__scrub,
⋮----
.spiritflix-player__scrub {
⋮----
.spiritflix-player__volume {
⋮----
.spiritflix-player__volume input {
⋮----
.spiritflix-player button:disabled {
⋮----
.spiritflix-player button span {
⋮----
.spiritflix-player__time {
⋮----
.spiritflix-player__up-next {
⋮----
.spiritflix-player__up-next strong {
⋮----
.spiritflix-player__loading,
⋮----
.spiritflix-player__tap-feedback {
⋮----
.spiritflix-player__loading {
⋮----
.spiritflix-player__loading span {
⋮----
.spiritflix-player__error,
⋮----
.spiritflix-player__error p {
⋮----
.spiritflix-player__error div,
⋮----
.spiritflix-player__ended {
⋮----
.spiritflix-brand--compact span:last-child {
⋮----
.spiritflix-topbar__controls {
⋮----
.spiritflix-icon-button,
⋮----
.spiritflix-view-toggle,
⋮----
.spiritflix-view-toggle::-webkit-scrollbar,
⋮----
.spiritflix-player__button-row button,
⋮----
.spiritflix-player__volume.is-expanded {
⋮----
.spiritflix-player__volume.is-expanded input,
⋮----
.spiritflix-player__button-row button span {
⋮----
.spiritflix-source-pill {
⋮----
.spiritflix-view-toggle span {
⋮----
.spiritflix-filter-options--two {
⋮----
.spiritflix-feed-card__media,
````

## File: tsconfig.json
````json
{
  "compilerOptions": {
    "baseUrl": ".",
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "react-jsx",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": [
    "next-env.d.ts",
    "**/*.ts",
    "**/*.tsx",
    ".next/types/**/*.ts",
    ".next/dev/types/**/*.ts",
    "**/*.mts"
  ],
  "exclude": [
    "node_modules",
    ".next",
    "models",
    "backend",
    ".spirit-backups",
    ".cursor",
    "repomix-output*.xml",
    "oldSpiritOS.xml",
    "_reference"
  ]
}
````

## File: vitest.config.mjs
````javascript

````
