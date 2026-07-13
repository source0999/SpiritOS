# Campaign 1 Ledger

CAMPAIGN: SpiritOS B+ Structural Foundation (Phases 0-3 only)
CAMPAIGN_BRANCH: codex/spiritos-campaign-1-foundation-20260712
CAMPAIGN_WORKTREE: /home/source/SpiritOS-campaign-1-20260712
BASE_HEAD: 49e58f2982521c46a1a4fc73ef66461a86643792
CURRENT_HEAD:8d17286d8673e698a19ec258f2b637a5d1db160d
APPROVED_SOURCE_PROXY_HEAD: 594d66ef8280953af767a273d7c91be765d1a6eb
APPROVED_SPIRITFLIX_HEAD: 5fde4ae064d471e1133e00d6bf25fb5aecb5d196
KNOWN_GOOD_LIVE_ARTIFACT: /home/source/SpiritOS-live-integration-20260712/.next BUILD_ID=1QbS3_KBLAULLONqVQRWn
CURRENT_PHASE: Phase 0
CURRENT_INCREMENT: 0A-0C baseline, provenance, and real-writeback location
ALLOWED_PATHS: docs/architecture/**; narrowly mapped authority/provenance/contracts/test-boundary paths only
FORBIDDEN_DETOURS: phases 4-7; god-file decomposition; final migration; runtime state migration; product-branch edits; push
COMPLETED_GATES: neutral campaign worktree; exact merge-parent proof; product branch cleanliness; live process CWD proof; AR-003 real route/location
NEXT_GATE: finish clean candidate build and temporary-port runtime/browser characterization
OPEN_BLOCKERS: Browser cannot trust Dell-local mkcert CA on live HTTPS; live browser proof is UNVERIFIED pending a trusted route. Candidate HTTP browser proof remains required.
SERVICE_TOPOLOGY: 8787=/home/source/SpiritOS-source-proxy-20260711; 3000 and 3002=/home/source/SpiritOS-live-integration-20260712; candidate 3003 reserved for Campaign 1 only
CONTRACT_VERSIONS: none yet
EVIDENCE_MANIFEST: docs/architecture/campaign-1-baseline/no-reversion-manifest.json
CANONICAL_CODING_SHELL: UNVERIFIED
TEST_PROFILE_REGISTRY: UNVERIFIED
ROLLBACK_POINT: current live integration artifact at 49e58f2982521c46a1a4fc73ef66461a86643792
LAST_VERIFIED_AT: 2026-07-12T04:34:40Z

Files read: worktree-manifest.md; context-map.md; project-entrypoints.md; test-registry.md; agent-scope-and-drift-policy.md; mapped SpiritFlix admin routes/actions; mapped Cartographer API; Design writeback route/runtime/writer.
2026-07-12 Phase 0 receipt:
- Candidate `npm run build` produced BUILD_ID `1vxzSBRA24QRgZI244mVW1` and served `http://127.0.0.1:3003/spiritflix` with HTTP 200 from this worktree.
- In-app Browser attempted live HTTPS and candidate HTTP; both are blocked by the browser security/policy surface (`ERR_CERT_AUTHORITY_INVALID` and HTTP-to-HTTPS policy followed by `ERR_SSL_PROTOCOL_ERROR`). No certificate warning was bypassed.
- Therefore real browser, console, network-request, loader, Latest Added, and mobile/Fold characterization is UNVERIFIED. This blocks any authority or deployment cutover that could regress current SpiritFlix.

2026-07-12 browser unblocking receipt:
- Candidate HTTPS 3004 certificate SHA-256 fingerprint and SPKI pin were checked before browser launch.
- Dell-native Playwright Chromium used only --ignore-certificate-errors-spki-list=<exact pin>; ignoreHTTPSErrors=false; no host trust store changed.
- Real rendered desktop and Fold-sized DOM, requests, console, and screenshots were captured for /spiritflix and /coding.
- Candidate rejects the stale SpiritFlix snapshot by exact approved merge-parent/source binding and candidate artifact provenance.
- Authenticated loader and Latest Added remain NOT_PROVEN: no dedicated private Jellyfin browser session or configured credential exists on the Dell lane. Mock fixtures were not accepted as proof.

2026-07-12 stop-state update:
- Genuine blocker under original condition 5: authenticated SpiritFlix loader/Latest Added proof requires a dedicated private Jellyfin session or credential. Dell service/config inspection found no configured non-secret test credential or session; credentials will not be extracted, reset, or invented.
- SpiritFlix product checkout now reports borrowed untracked _worktrees/spiritflix-player-repair-20260712/ created before this resume. It was not touched, staged, moved, or cleaned by Campaign 1.

2026-07-12 Phase B contract receipt:
- Commit f64ab7f4 adds an ignored server-side E2E secret contract, redacted preflight, exact opt-in opaque HTTP-only session broker, and proxy substitution path.
- Preflight result is dedicated_e2e_secret_not_configured; no configured dedicated credential or provisioning API key was found in approved Dell service/config locations.
- The broker and authenticated browser proof remain fail-closed until a dedicated non-admin Jellyfin identity is provided through the approved secret path or an approved provisioning credential is configured.

2026-07-12 Phase B policy gate:
- The installed dedicated identity authenticates, is non-admin, and has deletion/server-management permissions disabled.
- It is rejected because Jellyfin returns EnableAllFolders=false and EnabledFolders=[]; real authenticated loader and Latest Added proof cannot run without explicit library assignment.
- Broker and preflight now fail closed with dedicated_e2e_identity_no_library_access.

2026-07-12 authenticated browser receipt:
- Dedicated server-managed E2E identity now passes the redacted preflight: non-admin, deletion/server-management disabled, and eight enabled libraries. Browser receives only the opaque broker sentinel and HTTP-only application cookie; no raw Jellyfin credential was emitted to evidence.
- Candidate HEAD 6053b53fcefd56223477df1d9fa1a09c591cc4da was built as BUILD_ID sGCqWet3V2EeYFhS-QdQA; deterministic .next file-list SHA-256 is ce0e32838e7d3b49002919a54832dbea7b6005a6986fe1ca9a24a6d8a7e5252e.
- The served certificate SHA-256 is AAF476079332A4D3032FAE6989D1B6AD7CE0B744B2C44E3F29C93D73AD8A8CEE; SPKI SHA-256 is dMR8NZsnzNjABlxSAJwd/IyBvxr3kavIAwsr2pw0O9c=. Dell-native Playwright Chromium used only that per-process SPKI allowlist; ignoreHTTPSErrors=false and no host trust was modified.
- Real authenticated desktop and Fold DOM proved loader completion, Latest Added, accessible player entry, attached video, and /coding plus API bridge rendering. Required Jellyfin and coding bridge request families were observed; no page errors occurred.
- Strict browser zero-console acceptance remains OPEN: the approved SpiritFlix code intentionally requests unavailable mobile-optimized media and receives two /api/spiritflix/mobile-optimized 404 responses. They are classified and non-blocking to live media/player behavior, but count as console errors and were not masked or changed in this candidate.
- Evidence: docs/architecture/campaign-1-baseline/authenticated-browser-proof.json (sanitized; no cookies, tokens, headers, passwords, session IDs, or media paths).

2026-07-12 authenticated no-reversion gate PASS:
- The normal "no mobile-optimized derivative" state now returns 200 with {available:false}; the Jellyfin client already consumes this state and preserves direct-media fallback. Focused route/cache characterization passed 6/6.
- Rebuilt candidate BUILD_ID Qts75774IMdsWljly7uq5 with deterministic .next file-list SHA-256 f6761bc85e0b852cf91a82a0c2753313b7914eb621090cb6b289e6d1e937788a.
- Rerun on the same SPKI-only Dell Playwright Chromium lane passed authenticated desktop and Fold loader/Latest Added/player proof plus /coding/API bridge, with failed requests=0, console errors=0, page errors=0. Sanitized receipt replaced at docs/architecture/campaign-1-baseline/authenticated-browser-proof.json.
- Browser gate is complete; next incomplete increment is Phase 0E characterization and Phase 1 P0 authority enforcement.

2026-07-12 Phase 1 AR-002 duplicate-route increment:
- Removed the reduced shadow registrations for Cartographer GET/POST /safe-write and GET/POST /verification/run. The earlier canonical routes retain lane identity, approved file checks, and verification receipt summary.
- Added a production-router registration test requiring exactly one registration for each method/path. Focused command: /home/source/SpiritOS-source-proxy-20260711/.venv-source-proxy/bin/pytest -q source_proxy/tests/test_cartographer_api.py -k mutation_routes_are_registered_once (1 passed, 261 deselected).
- This removes a duplicate path only; it does not yet make caller-supplied approvals authoritative. The AR-002 server-owned approval transfer remains the next enforcement increment.

2026-07-12 approval-chain duplicate removal:
- Removed shadow Cartographer approval-token validation and consumption-preview registrations plus duplicated helper implementations. The production router now has one route per approval preview method/path.
- Expanded registration regression coverage to approval preview routes. Focused command passed 2 tests (261 deselected). This is duplicate authority removal only; canonical server-owned approval persistence and transfer enforcement remains incomplete.
