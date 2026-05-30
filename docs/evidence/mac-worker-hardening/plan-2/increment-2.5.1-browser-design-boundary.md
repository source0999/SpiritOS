# Increment 2.5.1 Browser Design Boundary

Date: 2026-05-28

## Scope

Allowed work for this increment:

- Inspect how `browser_design_check` is implemented.
- Determine whether it needs Playwright, Chromium, screenshots, local app URL, or browser permissions on Mac.
- Do not install anything.
- Do not start persistent browsers.

No implementation files were changed.

## Implementation inspection

`browser_design_check` is currently implemented in:

- `scripts/mac-worker/spirit_mac_worker.py`
- `scripts/mac-worker/spirit-mac-worker.mjs`

Current behavior:

- returns a metadata/manual-check packet
- includes the requested URL
- recommends Safari manual check and Playwright screenshot check when available
- does not launch a browser
- does not capture a screenshot
- does not mutate design files

Current result shape is too weak for A+ browser/design proof because it lacks:

- `viewport`
- `findings`
- `severity`
- `screenshot_artifacts`
- `limitations`
- `recommended_checks`
- `no_mutation_confirmed`

## Dependency inspection

Command:

```bash
grep -RIn "browser_design_check\|playwright\|chromium\|screenshot\|layout_readability\|overlap" scripts src tests package.json playwright.config.mjs docs 2>/dev/null | head -160
```

Result summary:

- Existing Playwright usage is on the Linux repo side in:
  - `scripts/agent-trials/run-ui-agent-trials.mjs`
  - `tests/ui-agent-trials/*.spec.ts`
  - `tests/e2e/coding-ui.spec.mjs`
- Mac worker `browser_design_check` is only a stub/manual packet.
- UI text already warns that screenshot proof is pending until screenshot evidence exists.

Command:

```bash
find node_modules -maxdepth 3 \( -path '*/playwright' -o -path '*/@playwright/test' \) -type d -print 2>/dev/null | head -20
```

Result:

```text
node_modules/@playwright/test
node_modules/playwright
```

Interpretation: Playwright is installed in the Linux repo.

Command:

```bash
ssh -o BatchMode=yes spirit-mac-mini 'cd /Users/spiritmac/spiritos-worker/SpiritOS && python3 - <<PY
import shutil, subprocess
for cmd in ["node", "npm", "npx", "python3"]:
    path=shutil.which(cmd)
    print(cmd, path or "missing")
try:
    p=subprocess.run(["npx", "--no-install", "playwright", "--version"], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=10)
    print("playwright", p.returncode, (p.stdout or p.stderr).strip())
except Exception as e:
    print("playwright_error", type(e).__name__, e)
PY'
```

Result:

```text
node missing
npm missing
npx missing
python3 /usr/bin/python3
playwright_error FileNotFoundError [Errno 2] No such file or directory: 'npx'
```

Interpretation: the Mac worker cannot currently run Node/Playwright from PATH. No install was attempted.

## Dependency boundary

`browser_design_check` would need at least one of these to produce real screenshot proof:

- working Playwright/Chromium on the Mac
- an approved browser automation path on the Mac
- a manual Safari screenshot workflow with artifact capture
- a Linux-hosted browser proof lane explicitly marked as not Mac-backed

Current Mac-backed browser proof does not have automated screenshot capability.

## Local target

The local app target for the next smoke is available through the explicit temporary HTTPS dev server on port 3000:

- `https://127.0.0.1:3000/coding`

The Mac may not be able to use `127.0.0.1` for the Linux-hosted app. For the required API call, the Mac worker only records metadata and does not fetch the URL yet.

## Safety confirmation

- No implementation files were changed.
- No browser was launched.
- No screenshot was captured.
- No dependency was installed.
- No design files were mutated.
- No hidden worker, daemon, launch agent, or persistent browser process was started.
- No Cartographer data, Scout production data, provider routing, secrets, or protected files were changed.

## GO / NO-GO

GO for Increment 2.5.1 complete.

Next authorized increment: Increment 2.5.2, run `browser_design_check` against a safe local target.
