# Campaign 1 Ledger

CAMPAIGN: SpiritOS B+ Structural Foundation (Phases 0-3 only)
CAMPAIGN_BRANCH: codex/spiritos-campaign-1-foundation-20260712
CAMPAIGN_WORKTREE: /home/source/SpiritOS-campaign-1-20260712
BASE_HEAD: 49e58f2982521c46a1a4fc73ef66461a86643792
CURRENT_HEAD: 49e58f2982521c46a1a4fc73ef66461a86643792
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
