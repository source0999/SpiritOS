# Increment 2.1.1 Current Baseline

Date: 2026-05-28

## Scope

Allowed work for this increment was limited to reading Plan 1 evidence, capturing current Linux git status, capturing current Mac worker API status, capturing current Mac git status, and listing Plan 1 evidence files.

No implementation files were modified.

## Plan 1 evidence read

Read:

- `docs/evidence/mac-worker-hardening/plan-1/plan-1-closeout.md`
- `docs/evidence/mac-worker-hardening/plan-1/increment-1.5.1-job-acceptance-matrix.md`

Plan 1 closeout says:

- Mac path is `/Users/spiritmac/spiritos-worker/SpiritOS`.
- Mac path is a real git checkout on `main`.
- Mac HEAD was `ac1c6ddf7cf2d71739801a13c46a3f1f3426ea26`.
- Mac status had untracked `scripts/mac-worker/`.
- Proven jobs were `system_status`, `run_safe_check`, `trial_context_assist`, `repo_context_search`, and `source_proxy_context_discovery`.
- Not tested jobs were `scout_research_packet` and `browser_design_check`.
- Recommended follow-up was to formalize `scripts/mac-worker/` as tracked repo content or an approved overlay.

## Required command results

### Linux git status

Command:

```bash
cd /home/source/SpiritOS
git status --branch --short --untracked-files=normal
```

Result:

```text
## main...origin/main
 M _reference/dashboardDemo/index.html
 M _reference/dashboardDemo/src/App.tsx
 M _reference/dashboardDemo/src/index.css
 M _reference/dashboardDemo/vite.config.ts
 M docs/plan-index.md
 M package-lock.json
 M package.json
 M playwright.config.mjs
 M src/app/__tests__/static-shell-routes.test.tsx
 M src/app/coding/__tests__/page.test.tsx
 M src/app/coding/page.tsx
 M src/app/proxy-backend/page.tsx
 M src/components/coding/CodingCockpitShell.tsx
 M src/components/coding/CodingCommandCenterShell.tsx
 M src/components/coding/__tests__/coding-cockpit-shell.test.tsx
 M src/components/coding/__tests__/coding-command-center-shell.test.tsx
 M src/lib/coding/plain-english-scope.ts
?? .codex-smoke/coding-plan1-runner-desktop.png
?? .codex-smoke/coding-plan1-runner-tablet.png
?? .codex-smoke/plan1-coding-desktop.png
?? .codex-smoke/plan1-coding-tablet.png
?? .codex-smoke/plan1-proxy-backend-desktop.png
?? .codex-smoke/plan2-2.3.1-coding-desktop.png
?? .codex-smoke/plan2-2.3.2-coding-tablet.png
?? .codex-smoke/plan2-2.3.3-coding-mobile.png
?? .codex-smoke/plan3-3.1.4-runner-desktop.png
?? .codex-smoke/plan3-3.1.4-runner-tablet.png
?? basic.js
?? docs/agent-runtime-trial-harness-mac-subagent-port-master-plan-v0.1.md
?? docs/agent-runtime-trial-harness-mac-subagent-port-new-chat-handoff-v0.1.md
?? docs/evidence/agent-runtime-trial-harness/
?? docs/evidence/mac-worker-hardening/
?? docs/spiritos-coding-readiness-roadmap-to-codex-like-features.md
?? scripts/agent-trials/
?? scripts/mac-worker/
?? src/app/api/coding/
?? src/app/v1/coding/mac-advisory/
?? src/lib/coding/__tests__/agent-trials-ui.test.ts
?? src/lib/coding/__tests__/plain-english-scope.test.ts
?? src/lib/coding/agent-trials-ui.ts
?? src/lib/mac-advisory/
?? src/lib/mac-worker/
?? tests/ui-agent-trials/
```

### Linux HEAD

Command:

```bash
cd /home/source/SpiritOS
git rev-parse HEAD
```

Result:

```text
ac1c6ddf7cf2d71739801a13c46a3f1f3426ea26
```

### Mac worker API status

Command:

```bash
cd /home/source/SpiritOS
curl -sk https://127.0.0.1:3000/api/coding/mac-worker
```

Result:

```text
curl exited with code 7 and no response body.
```

Interpretation: the local HTTPS app endpoint on `127.0.0.1:3000` was not reachable during this baseline increment. No server was started because this increment is baseline capture only.

### Mac git status and HEAD

Command:

```bash
ssh -o BatchMode=yes spirit-mac-mini 'cd /Users/spiritmac/spiritos-worker/SpiritOS && git status --branch --short --untracked-files=normal && git rev-parse HEAD'
```

Result:

```text
## main...origin/main
?? scripts/mac-worker/
ac1c6ddf7cf2d71739801a13c46a3f1f3426ea26
```

### Plan 1 evidence files

Command:

```bash
cd /home/source/SpiritOS
find docs/evidence/mac-worker-hardening/plan-1 -maxdepth 1 -type f | sort
```

Result:

```text
docs/evidence/mac-worker-hardening/plan-1/increment-1.1.1-linux-baseline.md
docs/evidence/mac-worker-hardening/plan-1/increment-1.1.2-mac-baseline.md
docs/evidence/mac-worker-hardening/plan-1/increment-1.2.1-checkout-strategy.md
docs/evidence/mac-worker-hardening/plan-1/increment-1.2.2-real-git-checkout.md
docs/evidence/mac-worker-hardening/plan-1/increment-1.3.1-direct-worker-system-status.md
docs/evidence/mac-worker-hardening/plan-1/increment-1.3.2-api-system-status.md
docs/evidence/mac-worker-hardening/plan-1/increment-1.4.1-run-safe-check-git-status.md
docs/evidence/mac-worker-hardening/plan-1/increment-1.4.2-run-safe-check-diff-check.md
docs/evidence/mac-worker-hardening/plan-1/increment-1.4.3-safe-command-allowlist.md
docs/evidence/mac-worker-hardening/plan-1/increment-1.5.1-job-acceptance-matrix.md
docs/evidence/mac-worker-hardening/plan-1/increment-1.5.2-context-jobs-post-checkout.md
docs/evidence/mac-worker-hardening/plan-1/increment-1.6.1-api-status-truth.md
docs/evidence/mac-worker-hardening/plan-1/increment-1.6.2-coding-ui-truth.md
docs/evidence/mac-worker-hardening/plan-1/increment-1.7.1-repo-checks.md
docs/evidence/mac-worker-hardening/plan-1/increment-1.7.2-final-mac-smoke.md
docs/evidence/mac-worker-hardening/plan-1/phase-1.1-closeout.md
docs/evidence/mac-worker-hardening/plan-1/phase-1.2-closeout.md
docs/evidence/mac-worker-hardening/plan-1/phase-1.3-closeout.md
docs/evidence/mac-worker-hardening/plan-1/phase-1.4-closeout.md
docs/evidence/mac-worker-hardening/plan-1/phase-1.5-closeout.md
docs/evidence/mac-worker-hardening/plan-1/phase-1.6-closeout.md
docs/evidence/mac-worker-hardening/plan-1/phase-1.7-closeout.md
docs/evidence/mac-worker-hardening/plan-1/plan-1-closeout.md
```

## Safety confirmation

- No Mac write authority was changed.
- No hidden worker, daemon, launch agent, or persistent process was started.
- No protected production data was mutated.
- No implementation files were changed.

## GO / NO-GO

GO for Increment 2.1.1 complete.

Next authorized increment: Increment 2.1.2, confirm A+ gap list.
