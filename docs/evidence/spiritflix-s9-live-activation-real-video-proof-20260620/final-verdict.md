# Final Verdict

VERDICT: GO

Root cause: stale sidecars masked the new S9 path for already-current rows, and the naming heuristic preserved source-spam filenames even when visual tags existed. There was also an initial proof-probe mismatch because the live Next app on port 3000 is HTTPS-only.

Fixes:

- Added explicit `visualAnalysis`, `pendingSmartTags`, and `pendingDisplayName` sidecar/API fields.
- Updated source-spam naming so visual/content tags can drive model-based recommended names.
- Proved the live HTTPS batch API and UI row projection now return visual Smart Tags and the corrected recommended name.

Real media proof:

- Video: `/mnt/spirit-8tb/media/yes/models/aaliyah-yasan/Visit onlyshare.io for MORE 130.mkv`
- Frame samples: 6 cached JPEG frames under `/mnt/spirit-8tb/media/.spiritflix-admin/analysis-cache/frames`
- Local model: `gemma3n:e4b`
- Visual analysis: complete, 4/4 VLM frames analyzed
- Tags proposed: `solo`, `indoor`
- Display name proposed: `Aaliyah Yasan - solo indoor 01`
- Confirmed metadata: `displayTitle`, `displayNameOverride`, `smartDisplayName`, `customTags`, `smartTagIds`, and `smartApproved`

Safety:

- Physical rename: no
- Physical move: no
- Physical delete: no
- Jellyfin mutation: no
- Source Proxy touched: no
- Cloud/paid API: no
- Git push: no

Verification:

- `npm run typecheck`: pass
- Smart/admin Vitest: pass, 27 files / 194 tests
- Home/player Vitest: pass, 4 files / 23 tests
- Scoped diff check: pass
- Focused secret scan: pass
