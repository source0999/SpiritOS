# Draft Review

## Inputs

Missing required prior files: none

Reviewed draft folder: `/home/source/SpiritOS/docs/evidence/repo-cleanup-manifest-watchers-20260617/drafts`.
Reviewed installed script folder already present in repo: `/home/source/SpiritOS/scripts/spiritos-health`.

## Safety Confirmation

- no restart command in installed watcher scripts
- no kill command in installed watcher scripts
- no delete/move/archive command in installed watcher scripts
- no media mutation in installed watcher scripts
- no git mutation in installed watcher scripts; repo-bloat watcher reads `git status` and `git count-objects` only
- no env/printenv dump in installed watcher scripts; model guard explicitly avoids dumping environment
- no secret dump behavior found
- writes logs only to `/mnt/spirit-8tb/spiritos-health/`
- Source Proxy liveness uses `https://127.0.0.1:8787/docs` and `https://127.0.0.1:8787/openapi.json`, not `/health`
- Next liveness uses `https://127.0.0.1:3000/spiritflix/admin`

## Installed Script Hashes Before Chmod

| script | exists | sha256 |
|---|---:|---|
| `spiritos-host-health-snapshot.sh` | True | `a0d57ac8c59a039f53b9e1b364747aa719632e0feda4dce53fbfa6e0705eb649` |
| `spiritos-service-health-snapshot.sh` | True | `0a7747826b25718ef043badf5a35228ffae1dff0be78f73981a8d61d81efc1d8` |
| `spiritos-boot-postmortem.sh` | True | `e38c253bca5dcd8b17e2626587d426326b160873d15dd3248b0cf76d39dda432` |
| `spiritos-model-storage-guard.sh` | True | `7c0dd577a9c5cde3b1b1e82ba7f713d62f4f961bb4f6480e2dfea4470a8d8071` |
| `spiritos-repo-bloat-report.sh` | True | `c31b932a5921c90cc6c10976219b4afa35b9d237fc8595b26db8d7e4ec3cfa11` |
| `spiritos-health-lib.sh` | True | `543fb109487ecceacebb8b24f0ba4a56d8d5ab5b0fb7910addc53a6a807a7a3f` |

## Notes

The original draft `spiritos-model-storage-guard.sh` included `systemctl show ollama -p Environment`; the installed script does not include that environment dump and is therefore safer for this approved install.
