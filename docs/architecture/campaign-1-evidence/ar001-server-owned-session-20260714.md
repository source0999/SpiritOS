# AR-001 server-owned ordinary SpiritFlix session receipt

- Schema: `spiritos-campaign-1-evidence/v1`
- Campaign / run: `spiritos-campaign-1` / `phase1-ar001-session-20260714`
- Mutable source head before commit: `6c4ebff4553330abb3818095b72d0f8cb8d2d846`
- Protected heads: Source Proxy `594d66ef`; SpiritFlix `5fde4ae0`; architecture audit `05612d2a`
- Scope: ordinary browser login, BFF media reads/playback, logout/revocation, and admin-library read containment.

## Result

PASS for the ordinary session migration only; this is not final AR-001 acceptance. The browser receives an opaque HTTP-only application session and a CSRF value. Jellyfin authorization, actual Jellyfin user identity, and server selection are retained only by the server-side session map. The ordinary browser client uses the canonical BFF for reads, images, streams, and HLS.

Rejected production-path inputs include browser-supplied authorization/server/token parameters, private-route access without the opaque session, credential-bearing admin-library requests, untrusted mutation origin, and ordinary BFF mutations without the matching CSRF value. Logout revokes the opaque session; subsequent BFF session lookup is rejected. Session expiry is enforced by the server-side TTL lookup.

## Verification

- 10 focused Vitest files, 64 tests passed.
- `npm run typecheck`: passed.
- `npm run campaign-1:validate-authority`: passed.
- `npm run campaign-1:validate-continuity`: passed.
- `git diff --check`: passed.

No password, token, API key, authorization value, opaque cookie, approval identifier, or private media path is recorded in this receipt.

## Claim ceiling

AR-001 administrative mutation authority remains unresolved. The next gate inventories and migrates or fail-closes all administrative mutation entry points behind distinct durable operator approval; ordinary media sessions are not administrative authority.
