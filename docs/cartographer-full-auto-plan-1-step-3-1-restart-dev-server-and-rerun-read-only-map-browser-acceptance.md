# Cartographer Full Auto Plan 1 Step 3.1: Restart Dev Server And Rerun Read-Only /map Browser Acceptance

status: acceptance-closeout

Status date: 2026-05-22

Current HEAD: `40141f34d27d915503f265efba119673a412354a`

## Result

Plan 1 Step 3.1 restored the local Next dev server and reran `/map` acceptance checks.

The stale Next server process on port `3000` was stopped and a fresh server was started on port `3000`. After restart, `/map` returned `200 OK`, `/v1/cartographer/status` returned `200`, and rendered HTML contained the expected read-only `/map` display content.

This closeout does not add endpoints, edit backend routes, edit tests, edit `/coding`, edit dashboard files, edit Source Proxy files, add durable storage, add approval-token runtime, add execution controls, grant limited unattended operation, or grant full auto.

Full auto is not granted. Limited unattended operation is not granted.

## Restart And Acceptance Evidence

Observed before restart:

- A `next-server (v16.2.4)` process was listening on port `3000`.
- `curl -v --max-time 5 http://localhost:3000/map` returned `curl: (52) Empty reply from server`.
- A second dev server on `3001` was blocked because Next detected the existing repo server.

Actions taken after operator approval:

- Stopped the existing Next dev server process.
- Started `npx next dev -H 0.0.0.0 --webpack -p 3000`.
- Confirmed Next reported ready on `http://localhost:3000`.

Acceptance evidence after restart:

- `curl http://localhost:3000/map` returned `HTTP/1.1 200 OK`.
- `curl http://localhost:3000/v1/cartographer/status` returned HTTP code `200`.
- Rendered `/map` HTML contained:
  - `Cartographer Manual Control Center`
  - `Display-only GET allowlist`
  - `Fallback proof`
  - `full auto is not granted`
  - `limited unattended operation is not granted`
  - `No authority increase`
  - `Data wiring remains display-only`
- Rendered `<button>` elements are limited to the shared SpiritOS theme picker from the imported floating nav.

## Remaining Operator Visual Check

The HTTP render check passed. The operator should still visually open `http://localhost:3000/map` and confirm:

- The page renders.
- Display-only GET state or fallback state is visible.
- Fallback proof is visible.
- Authority denials are visible.
- No active approval, apply, execute, commit, push, branch, queue, command, self-approval, or write controls exist.
- Full auto is not granted.
- Limited unattended operation is not granted.

## Manual Checks

```bash
cd /home/source/SpiritOS

git diff --check

npx eslint src/app/map/page.tsx src/app/map/read-only-map-data.ts

curl -sS -D /tmp/cartographer-map-3-1.headers -o /tmp/cartographer-map-3-1.html http://localhost:3000/map
sed -n '1,20p' /tmp/cartographer-map-3-1.headers

curl -sS -o /tmp/cartographer-status-3-1.json -w '%{http_code}\n' http://localhost:3000/v1/cartographer/status

grep -nE "Cartographer Manual Control Center|Display-only GET allowlist|Fallback proof|full auto is not granted|limited unattended operation is not granted|No authority increase|Data wiring remains display-only" \
  /tmp/cartographer-map-3-1.html

grep -o '<button[^>]*>' /tmp/cartographer-map-3-1.html || true

grep -nE "approve|apply|execute|commit|push|branch|queue execution|command controls|self-approval|write control" \
  /tmp/cartographer-map-3-1.html || true

grep -nE "Result|Restart And Acceptance Evidence|HTTP/1.1 200 OK|Full auto is not granted|Limited unattended operation is not granted|Next Recommended Increment Title" \
  docs/cartographer-full-auto-plan-1-step-3-1-restart-dev-server-and-rerun-read-only-map-browser-acceptance.md

git status --short -- \
  src/app/map/page.tsx \
  src/app/map/read-only-map-data.ts \
  docs/cartographer-full-auto-plan-1-implementation-decision-read-only-map-wiring.md \
  docs/cartographer-full-auto-plan-1-read-only-map-wiring-implementation-closeout.md \
  docs/cartographer-full-auto-plan-1-operator-review-read-only-map-wiring-acceptance-and-step-2-permission-gate.md \
  docs/cartographer-full-auto-plan-1-step-2-read-only-map-packet-shape-hardening-and-fallback-proof.md \
  docs/cartographer-full-auto-plan-1-step-3-read-only-map-manual-browser-acceptance-and-phase-closeout-gate.md \
  docs/cartographer-full-auto-plan-1-step-3-1-restart-dev-server-and-rerun-read-only-map-browser-acceptance.md \
  docs/plan-index.md

git status --branch --short

git diff --stat
```

## Expected Output

```text
git diff --check prints nothing.

Focused ESLint prints nothing.

The /map curl header includes HTTP/1.1 200 OK.

The status endpoint curl prints 200.

The rendered HTML grep shows Cartographer Manual Control Center, Display-only GET allowlist, Fallback proof, full-auto denial, limited-unattended denial, No authority increase, and Data wiring remains display-only.

The button grep may show exactly the shared SpiritOS theme-picker buttons from the floating nav:

<button type="button" class="dashboard-demo-v4-theme-picker dashboard-demo-v4-desktop-theme-picker" ...>
<button type="button" class="dashboard-demo-v4-theme-picker" ...>

The action-control grep may show inert blocked copy only. It must not show executable Cartographer approval, apply, execute, commit, push, branch, queue execution, command controls, self-approval, or write controls.

The Step 3.1 doc grep shows result, restart evidence, HTTP 200 evidence, authority denials, and next increment title.

Focused status shows the Plan 1 docs and /map files in this lane, plus unrelated docs/plan-index.md drift if it remains dirty.
```

## Stop Conditions

Stop if any next increment requires:

- Backend/API edits.
- Source Proxy edits.
- Tests.
- Dashboard edits.
- `/coding` edits.
- Package, config, env, generated, or Scout edits.
- Durable storage.
- Approval-token runtime.
- Write authority.
- Command execution authority.
- Queue execution authority.
- Approval authority.
- Self-approval.
- Limited unattended operation.
- Full auto.

## Next Recommended Increment Title

Plan 1 Step 4: Read-Only /map Phase Closeout Decision And Next-Plan Gate
