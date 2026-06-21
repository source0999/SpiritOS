# GLM Full-Repo Audit — Evidence Reconciliation

**Date:** 2026-06-21 · **Reconciler:** Spirit (Cursor agent) · **Authority:** Britton

## What this is

- This is an **evidence reconciliation**, not a new audit.
- Britton accepted the current committed on-disk shards as canonical.
- The XML shards were **not modified** in this task.
- The checksum, metadata, shard-index, and mobile-index records were updated to match committed shard bytes.
- The prior mismatch was detected by **GLM cleanup P0**.
- The mismatch was caused by **stale checksum/index metadata after shard regeneration**.
- **Source cleanup did not start.**
- Cleanup-owned source files were **not touched**.
- This commit exists only to make the frozen audit evidence self-consistent again.

## Canonical shard bytes (on-disk, unchanged)

| Shard | Bytes | SHA-256 |
|---|---|---|
| `glm-full-repo-freeze-20260621-shard-001.xml` | 1,769,550 | `d1e6f74e2059aaafbee537be5348c92082d1547fd0e7edd0145c41dae8f143fd` |
| `glm-full-repo-freeze-20260621-shard-002.xml` | 550,808 | `bff9c938755a69ec3f7290f1c506ef9854a08089bc98a5f73eadc12286b57d19` |
| `glm-full-repo-freeze-20260621-shard-003.xml` | 1,883,447 | `04c831ce91e7959a9cb62b54665d9e59ad2cce8bb8b67eb910119626cecc6130` |

## Stale records replaced

Prior checksum/index metadata recorded pre-regeneration shard hashes and sizes. The audit conclusions markdown, Headroom log, and non-shard evidence verified correctly; only the three XML shard entries in the evidence contract were out of sync with committed bytes.

## Files updated in this reconciliation

- `glm-full-repo-checksums.sha256` — shard hashes (+ dependent index/metadata checksum lines)
- `glm-full-repo-metadata.json` — `shards[]` bytes and SHA-256; `shard_totals.total_bytes`
- `glm-full-repo-freeze-20260621-shard-index.md` — shard table bytes and hashes
- `glm-full-repo-mobile-index.md` — shard size/hash entries only

## Not changed

- Audit verdict, Headroom diagnosis, cleanup recommendations, and audit conclusions markdown.
- Any XML shard content.
- Any source code (`source_proxy/`, `src/`, `scripts/`, etc.).
