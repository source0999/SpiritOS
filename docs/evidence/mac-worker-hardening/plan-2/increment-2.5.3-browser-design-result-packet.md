# Increment 2.5.3 Browser Design Result Packet

Date: 2026-05-28

## Scope

Allowed work for this increment:

- Normalize `browser_design_check` output.
- Return summary, URL, viewport, findings, severity, screenshot artifacts, limitations, recommended checks, and mutation confirmation.
- Do not apply CSS.
- Do not change design files.
- Do not pretend visual proof exists if no screenshot exists.
- Add or update tests.

## Files changed

- `scripts/mac-worker/spirit_mac_worker.py`
- `scripts/mac-worker/spirit-mac-worker.mjs`
- `src/lib/mac-worker/types.ts`
- `src/lib/mac-worker/__tests__/contract.test.ts`
- `docs/evidence/mac-worker-hardening/plan-2/increment-2.5.3-browser-design-result-packet.md`

The two approved worker entry files were refreshed on the Mac checkout after checks passed.

## Result shape

`browser_design_check` now returns:

- `summary`
- `url`
- `viewport`
- `check`
- `findings`
- `severity`
- `screenshot_artifacts`
- `limitations`
- `recommended_checks`
- `no_mutation_confirmed`

Because Mac browser automation is unavailable, the packet honestly reports:

- `severity:"blocked"`
- finding title `Screenshot proof unavailable`
- `screenshot_artifacts:[]`
- `No browser was launched.`
- `No screenshot was captured.`
- `No layout pixels were inspected.`

## Checks run

### Python syntax

Command:

```bash
python3 -m py_compile scripts/mac-worker/spirit_mac_worker.py
```

Result:

```text
passed with no output
```

### Node syntax

Command:

```bash
node --check scripts/mac-worker/spirit-mac-worker.mjs
```

Result:

```text
passed with no output
```

### Contract tests

Command:

```bash
npx --no-install vitest run src/lib/mac-worker/__tests__/contract.test.ts --reporter=dot
```

Result:

```text
Test Files  1 passed (1)
Tests  8 passed (8)
```

Added test coverage:

- blocked browser design packet fields without fake screenshot proof

### Whitespace diff check

Command:

```bash
git diff --check
```

Result:

```text
passed with no output
```

## API proof after hardening

Command:

```bash
curl -sk -X POST https://127.0.0.1:3000/api/coding/mac-worker \
  -H 'content-type: application/json' \
  --data '{"job_type":"browser_design_check","input":{"repo_path":"/Users/spiritmac/spiritos-worker/SpiritOS","url":"https://127.0.0.1:3000/coding","viewport":"mobile","check":"layout_readability_and_overlap"}}'
```

Result summary:

```json
{
  "ok": true,
  "result": {
    "job_type": "browser_design_check",
    "success": true,
    "node_id": "spirit-mac-mini",
    "result": {
      "summary": "Mac browser/design check packet prepared; screenshot proof unavailable from current worker dependencies.",
      "url": "https://127.0.0.1:3000/coding",
      "viewport": "mobile",
      "check": "layout_readability_and_overlap",
      "findings": [
        {
          "severity": "blocked",
          "title": "Screenshot proof unavailable"
        }
      ],
      "severity": "blocked",
      "screenshot_artifacts": [],
      "limitations": [
        "No browser was launched.",
        "No screenshot was captured.",
        "No layout pixels were inspected.",
        "This packet is advisory metadata only until browser tooling is approved and available."
      ],
      "recommended_checks": [
        "Install or expose approved Mac browser automation before claiming visual proof.",
        "Run Playwright screenshot proof when available.",
        "Use manual Safari screenshot only with saved artifact evidence."
      ],
      "no_mutation_confirmed": true
    },
    "artifacts": []
  }
}
```

## Safety confirmation

- No CSS was applied.
- No design files were changed.
- No screenshot proof was fabricated.
- No browser was launched.
- No screenshot was captured.
- No dependency was installed.
- No hidden worker, daemon, launch agent, or persistent browser process was started.
- No Cartographer data, Scout production data, provider routing, secrets, or protected files were changed.

## GO / NO-GO

GO for Increment 2.5.3 complete.

NO-GO for screenshot-backed Mac browser/design proof until approved browser automation or manual screenshot artifact capture exists on the Mac.

Next authorized increment: Phase 2.5 closeout.
