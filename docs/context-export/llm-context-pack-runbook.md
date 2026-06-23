# LLM Context Pack Runbook

This runbook is for handing SpiritOS context to ChatGPT or another outside LLM. External LLM sessions cannot see the repo directly, so upload focused XML packs instead of relying on memory or sending a raw full-repo dump.

## Which pack to send first

Start with `repo-map-context.xml` plus `source-proxy-context.xml` for most cleanup or Source Proxy review. Send `frontend-context.xml` only for frontend review. Send `spiritflix-media-code-context.xml` only for SpiritFlix/media code review. Send `docs-plans-context.xml` only for roadmap, breakpoint, old-plan, or archive-index review.

Never send `docs/evidence/**` unless the review is specifically auditing receipts or raw evidence. Evidence and media sludge can turn a context pack into a noisy 300MB artifact that hides the source-of-truth docs.

## Pack purposes

| Pack | Visible output | Purpose |
| --- | --- | --- |
| Repo map | `/home/source/SpiritOS/repo-map-context.xml` | README, package/config, repo-map docs, cleanup docs, and plan orientation. |
| Source Proxy / coding | `/home/source/SpiritOS/source-proxy-context.xml` | Source Proxy Python, coding UI, worker adapters, context scripts, and coding routes. |
| Source Proxy minimal | `/home/source/SpiritOS/source-proxy-min-context.xml` | Existing focused npm profile for Source Proxy/coding work. |
| Frontend | `/home/source/SpiritOS/frontend-context.xml` | Next app, components, lib helpers, and frontend config. |
| SpiritFlix/media code | `/home/source/SpiritOS/spiritflix-media-code-context.xml` | SpiritFlix and media code only; no media files. |
| Docs/plans | `/home/source/SpiritOS/docs-plans-context.xml` | Plans, breakpoints, audits, cleanup state, and roadmap docs. |

## Exclusions

All normal packs exclude `.git`, dependency folders, build outputs, Python venvs, caches, SQLite/database files, logs, generated `*context.xml` files, `repomix-output*.xml`, `docs/evidence/**`, `docs/handoff/**`, backend volumes, Jellyfin service data, media gallery JSON, and common binary/media archive extensions.

This keeps review focused on source and operator truth rather than receipts, runtime state, media files, or generated bundles.

## Verify Headroom is active

Headroom is active only when the generated XML metadata contains both:

```xml
compressed="true"
tokens_saved="1"
```

The exact `tokens_saved` value can be any positive integer. If `compressed="false"`, `tokens_saved="0"`, or the Headroom metadata is absent, the pack may still be useful Tree-sitter Repomix output, but it is not Headroom-compressed.

For the Source Proxy minimal pack, run:

```bash
cd /home/source/SpiritOS-cleanup-20260621

HEADROOM_PORT=8798 \
HEADROOM_BASE_URL=http://127.0.0.1:8798 \
HEADROOM_BIN=/home/source/SpiritOS/.venv-headroom/bin/headroom \
npm run context:source-proxy-min

HEADROOM_PORT=8798 \
HEADROOM_BASE_URL=http://127.0.0.1:8798 \
HEADROOM_BIN=/home/source/SpiritOS/.venv-headroom/bin/headroom \
npm run context:verify
```

## Generate one pack

Use the npm profiles for the maintained focused packs:

```bash
cd /home/source/SpiritOS-cleanup-20260621

npm run context:repo-map

HEADROOM_PORT=8798 \
HEADROOM_BASE_URL=http://127.0.0.1:8798 \
HEADROOM_BIN=/home/source/SpiritOS/.venv-headroom/bin/headroom \
npm run context:source-proxy-min
```

For ad hoc single packs, reuse the README `make_pack` function with one `make_pack` call and the same `COMMON_IGNORE` list. Do not remove the evidence/media exclusions just to make a pack look complete.

## Generate all packs

Use the all-packs command in `README.md` under `LLM Context Packs / Repomix + Headroom`. It writes these visible outputs into `/home/source/SpiritOS/`:

```text
/home/source/SpiritOS/repo-map-context.xml
/home/source/SpiritOS/source-proxy-context.xml
/home/source/SpiritOS/frontend-context.xml
/home/source/SpiritOS/spiritflix-media-code-context.xml
/home/source/SpiritOS/docs-plans-context.xml
```

Generated XMLs are upload artifacts and should remain untracked.
