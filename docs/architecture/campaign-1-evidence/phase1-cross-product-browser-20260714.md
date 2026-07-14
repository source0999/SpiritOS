# Campaign 1 authenticated cross-product browser receipt

- Recorded: `2026-07-14T01:57:20Z` on an isolated production start from the committed Campaign 1 build. The protected Source Proxy, SpiritFlix, and architecture worktrees remained read-only at their pinned heads.
- Certificate policy: Playwright Chromium used only the known development-certificate SPKI allowance. `ignoreHTTPSErrors` remained `false`; host trust was not changed.
- Authentication: the server-managed dedicated E2E identity passed preflight as non-admin, without deletion or server-management privilege, and with library access. The browser received only an HTTP-only session cookie and the opaque `e2e-broker` sentinel; no raw Jellyfin credential, token, cookie value, user identifier, or media path is recorded.

## SpiritFlix rendering and player entry

1. Desktop and Fold viewports each established the broker session, loaded the authenticated SpiritFlix shell, rendered `Latest Added`, and exposed eight play controls.
2. The one uniquely named feature play control opened an attached video in both viewports. No page errors were observed.
3. The existing protected HTTPS lane was identity-checked first. Its served artifact returns `404` for the Campaign E2E session route, so it cannot provide authenticated Campaign proof without mutating a protected service. The isolated Campaign production lane was used instead; this is a scope boundary, not a protected-product modification.

## Coding shell regression

1. The isolated production `/coding` route returned `200`, rendered the `Coding` heading, the canonical cockpit shell, and the selected-prompt control. No page errors occurred.
2. Four framework prefetches for `/intelligence` and `/map` were observed as `net::ERR_ABORTED`; direct requests to both routes returned `200`. They are documented background navigation cancellations, not route failures or authority execution. No approval, apply, commit, or push action was invoked.

This receipt is redacted and records a completed browser-regression slice only. Campaign 1 final acceptance remains open.
