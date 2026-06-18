# Browser Smoke

Smoke target: `https://127.0.0.1:3000/spiritflix/admin`.

The live lane is HTTPS-only: HTTP on `:3000` returned an empty response, while HTTPS returned `200 OK`. No server was restarted. A temporary dev server attempt on `:3002` was blocked by the existing Next dev lock and then stopped; no existing process was killed.

Browser smoke used Playwright with intercepted fixture responses for `/api/spiritflix/admin/fs`, `/api/spiritflix/admin/jellyfin-index`, image endpoints, and `/api/spiritflix/admin/smart/analysis`. It did not call real user media, real export, real preview, Jellyfin, or filesystem mutation.

## Checks

| Check | Result |
|---|---|
| Smart tags panel opens | PASS |
| Approved metadata section appears when reviewed analysis exists | PASS |
| Export approved metadata button appears | PASS |
| Prepare rename preview button appears | PASS |
| No Apply rename button | PASS |
| No Apply move button | PASS |
| No Confirm execute button | PASS |
| Rename preview shows current/suggested/target/warnings | PASS |
| Grid remains mounted | PASS |
| No console errors | PASS |

## Raw Result

```json
{
  "url": "https://127.0.0.1:3000/spiritflix/admin",
  "smartPanelOpened": true,
  "approvedMetadataVisible": true,
  "exportButtonVisible": true,
  "prepareRenameButtonVisible": true,
  "forbiddenButtons": [],
  "renamePreviewVisible": true,
  "gridMounted": true,
  "consoleErrors": [],
  "pageErrors": [],
  "exportRequests": 0,
  "executeRequests": 0,
  "note": "API responses were intercepted with fixture data; export button was not clicked; prepare preview was intercepted and did not touch real media."
}
```

Artifacts:

- `raw/browser/browser-smoke-result.json`
- `raw/browser/spiritflix-admin-s6-smoke.png`
- `raw/browser/s6-smoke.cjs`
- `raw/browser/existing-3000-probe.txt`
- `raw/browser/dev-server-3002.log` records the blocked temporary dev-server attempt.

Browser smoke exit code: `0`.
