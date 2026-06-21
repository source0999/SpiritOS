# GLM Full-Repo Freeze — Shard Index

**Date:** 2026-06-21 · **HEAD:** `927055e4` · **Branch:** `master`
A single full-repo XML was 38 MB / 6,630 files (unusable on mobile). Per the task's shard provision, GLM delivered **3 focused shards**, each a clean repomix run scoped to one area, each under 2 MB. Together they cover all code + architecture docs (binary/media/build/runtime/secrets/evidence-raw excluded).

| Shard | Scope | Bytes | Files | SHA-256 |
|---|---|---|---|---|
| `glm-full-repo-freeze-20260621-shard-001.xml` | **Core OS code** — `source_proxy/**/*.py` + `src/**` (Coding UI, SpiritFlix code, media code, spirit, dashboard, chat) | 1,769,609 | 816 | `fbe676b55f4a4ceb550cea3f0f73567d605ace25c06f1a18cd5c1cf4efc8b82b` |
| `glm-full-repo-freeze-20260621-shard-002.xml` | **Tooling** — `scout/**` + `scripts/**` (ops, mac-worker, context, media tooling code) + root configs | 550,807 | 189 | `4666eb61e8a396130011af03f5ab70325299395dd04765c38c7a8e063adff530` |
| `glm-full-repo-freeze-20260621-shard-003.xml` | **Architecture docs** — `_blueprints/**` + top-level `*.md` plan docs + source-proxy-human-brain pivot + context-export + cartographer-live-receipts docs | 1,883,468 | 431 | `2f18e3b1d51f3f177684b162263f812ef750e51e89bd22f073f5a8c2a33db34e` |
| **Total** | | **4,203,884** | **1,436** | (per-file hashes above) |

## How the shards were made
- Tool: `node node_modules/repomix/bin/repomix.cjs --config <shard-config>.json -o <shard>.xml .`
- Compression: tree-sitter (`--compress`). **Headroom pass skipped** (proxy BLOCKED_ENV — Cursor on 8797, Linux venv; see `glm-headroom-repair-log.md`).
- Shard configs kept alongside (audit-local, not part of the repo's canonical repomix configs): `glm-shard-001-config.json`, `glm-shard-002-config.json`, `glm-shard-003-config.json`, plus the broader `glm-full-repo-repomix.config.json`.
- Repomix security auto-excluded: `source_proxy/tests/test_bubblewrap_sandbox.py` (2 issues) and `docs/evidence/.../increment-2.1-local-default-patch.md` (1 issue) — no secrets in included files.

## Which shard to use when
- **Source Proxy / Coding loop questions** → shard-001.
- **Scout / Mac worker / scripts / ops / context tooling questions** → shard-002.
- **Blueprint / Cartographer / intent / plan / contract questions** → shard-003.
- **Whole-OS architecture** → read the audit Markdown (`glm-full-repo-audit-20260621.md`); use shards to drill in.

## Caveat
This is a shard freeze, not a byte-exact full-tree dump. Binary/media/build/runtime/secrets/evidence-raw were excluded per the task's bloat rules. For byte-exact full-tree, regenerate with `repomix.config.json` (warned at 321 MB pre-ignore).
