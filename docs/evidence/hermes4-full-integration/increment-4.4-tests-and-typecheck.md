# Increment 4.4 - Tests and typecheck

Date: 2026-05-29T20:01:26-04:00

## Available scripts
```text
Lifecycle scripts included in spirit-os@0.1.0:
  start
    next start
  test
    vitest
available via `npm run-script`:
  dev
    next dev -H 0.0.0.0 --webpack
  dev:https
    next dev -H 0.0.0.0 --webpack --experimental-https -p 3000
  dev:https:lan
    next dev -H 0.0.0.0 --webpack -p 3000 --experimental-https --experimental-https-key ./certificates/spirit-dev-key.pem --experimental-https-cert ./certificates/spirit-dev.pem
  dev:turbo
    next dev -H 0.0.0.0
  dev:backend
    cd backend && docker compose up -d
  dev:all
    npm run dev:backend && npm run dev
  dev:all:https
    npm run dev:backend && npm run dev:https
  dev:all:https:lan
    npm run dev:backend && npm run dev:https:lan
  proxy:bootstrap
    node ./scripts/source-proxy-bootstrap.mjs
  proxy:bootstrap:linux
    bash ./scripts/source-proxy-bootstrap.sh
  proxy:bootstrap:windows
    powershell -ExecutionPolicy Bypass -File ./scripts/source-proxy-bootstrap.ps1
  proxy:dev
    node ./scripts/source-proxy-dev.mjs
  proxy:https
    node ./scripts/source-proxy-dev.mjs --https
  proxy:https:lan
    node ./scripts/source-proxy-dev.mjs --https --lan
  context:pack
    repomix --config repomix.config.json .
  context:compress
    node ./scripts/source-context-compress.mjs
  validate:blueprints
    node ./scripts/validate-blueprints.mjs
  next:mcp:ws
    node ./scripts/next-mcp-ws-bridge.mjs
  next:mcp:ws:probe
    node ./scripts/next-mcp-ws-probe.mjs
  next:mcp:ws:smoke
    node ./scripts/next-mcp-ws-smoke.mjs
  build
    next build --webpack
  lint
    eslint .
  typecheck
    tsc --noEmit
  check
    npm run lint && npm run typecheck && npm run build
  test:coding-regression
    python -m pytest -q source_proxy/tests/test_coding_regression_pack.py
  test:coding-frontend-regression
    vitest run src/lib/coding/__tests__/unified-diff-paths.test.ts src/components/coding/__tests__/approval-gate-binding.test.ts src/lib/coding/__tests__/proxy-route-payload.test.ts src/components/coding/__tests__/coding-workflow-step.test.ts src/components/coding/__tests__/client-fallback.test.ts src/components/coding/__tests__/proxy-safety-smoke.test.ts src/app/v1/coding/self-tests/run/__tests__/route.test.ts
  test:ui
    vitest --ui
```

## Checks
```text

> spirit-os@0.1.0 test
> vitest --runInBand model-provider-status

file:///home/source/SpiritOS/node_modules/vitest/dist/chunks/cac.DJJmV0dT.js:406
          throw new CACError(`Unknown option \`${name.length > 1 ? `--${name}` : `-${name}`}\``);
                ^

CACError: Unknown option `--runInBand`
    at Command.checkUnknownOptions (file:///home/source/SpiritOS/node_modules/vitest/dist/chunks/cac.DJJmV0dT.js:406:17)
    at CAC.runMatchedCommand (file:///home/source/SpiritOS/node_modules/vitest/dist/chunks/cac.DJJmV0dT.js:606:13)
    at CAC.parse (file:///home/source/SpiritOS/node_modules/vitest/dist/chunks/cac.DJJmV0dT.js:547:12)
    at file:///home/source/SpiritOS/node_modules/vitest/dist/cli.js:11:13
    at ModuleJob.run (node:internal/modules/esm/module_job:325:25)
    at async ModuleLoader.import (node:internal/modules/esm/loader:606:24)
    at async asyncRunEntryPointWithESMLoader (node:internal/modules/run_main:117:5)

Node.js v20.20.2

> spirit-os@0.1.0 test
> vitest --runInBand agent-trials-ui

file:///home/source/SpiritOS/node_modules/vitest/dist/chunks/cac.DJJmV0dT.js:406
          throw new CACError(`Unknown option \`${name.length > 1 ? `--${name}` : `-${name}`}\``);
                ^

CACError: Unknown option `--runInBand`
    at Command.checkUnknownOptions (file:///home/source/SpiritOS/node_modules/vitest/dist/chunks/cac.DJJmV0dT.js:406:17)
    at CAC.runMatchedCommand (file:///home/source/SpiritOS/node_modules/vitest/dist/chunks/cac.DJJmV0dT.js:606:13)
    at CAC.parse (file:///home/source/SpiritOS/node_modules/vitest/dist/chunks/cac.DJJmV0dT.js:547:12)
    at file:///home/source/SpiritOS/node_modules/vitest/dist/cli.js:11:13
    at ModuleJob.run (node:internal/modules/esm/module_job:325:25)
    at async ModuleLoader.import (node:internal/modules/esm/loader:606:24)
    at async asyncRunEntryPointWithESMLoader (node:internal/modules/run_main:117:5)

Node.js v20.20.2

> spirit-os@0.1.0 lint
> eslint .

[BABEL] Note: The code generator has deoptimised the styling of /home/source/SpiritOS/src/components/coding/CodingAgentInterface.tsx as it exceeds the max of 500KB.

/home/source/SpiritOS/src/app/v1/cartographer/audit-trail/route.ts
  110:9  warning  'result' is assigned a value but never used  @typescript-eslint/no-unused-vars

/home/source/SpiritOS/src/components/coding/CodingAgentInterface.tsx
  1479:6  warning  React Hook useEffect has a missing dependency: 'previewDiffVerification'. Either include it or remove the dependency array                                                        react-hooks/exhaustive-deps
  1551:6  warning  React Hook useEffect has missing dependencies: 'approvalGate', 'diffVerification', 'longRunningTask', and 'proxySafetySmoke'. Either include them or remove the dependency array  react-hooks/exhaustive-deps

/home/source/SpiritOS/src/components/coding/CodingCockpitShell.tsx
  858:9   warning  'allowedFileList' is assigned a value but never used                                                         @typescript-eslint/no-unused-vars
  862:11  warning  'trimmedTarget' is assigned a value but never used                                                           @typescript-eslint/no-unused-vars
  867:6   warning  React Hook useMemo has a missing dependency: 'targetFile'. Either include it or remove the dependency array  react-hooks/exhaustive-deps

/home/source/SpiritOS/src/components/coding/CodingCommandCenterShell.tsx
   492:7   warning  'defaultWorkspace' is assigned a value but never used                                                                       @typescript-eslint/no-unused-vars
   507:7   warning  'trialInstructions' is assigned a value but never used                                                                      @typescript-eslint/no-unused-vars
  4538:18  warning  'copyBrowserWidgetAcceptanceEvidenceCloseoutPacket' is defined but never used                                               @typescript-eslint/no-unused-vars
  4546:18  warning  'copyWidgetManualAcceptanceEvidenceReviewGatePacket' is defined but never used                                              @typescript-eslint/no-unused-vars
  4856:6   warning  React Hook useEffect has a missing dependency: 'runSelectedTrialPreview'. Either include it or remove the dependency array  react-hooks/exhaustive-deps

/home/source/SpiritOS/src/components/coding/__tests__/coding-command-center-shell.test.tsx
  205:10  warning  'openEnvironmentDetails' is defined but never used  @typescript-eslint/no-unused-vars

/home/source/SpiritOS/src/components/dashboard/HomelabBlueprintReviewWidget.tsx
  108:10  warning  'pendingProposalCount' is defined but never used  @typescript-eslint/no-unused-vars

/home/source/SpiritOS/src/lib/coding/progress-surface.ts
  50:9  warning  'nextStep' is assigned a value but never used  @typescript-eslint/no-unused-vars

/home/source/SpiritOS/src/lib/coding/proxy-trial-prompts.ts
  1005:22  warning  '_count' is assigned a value but never used  @typescript-eslint/no-unused-vars

/home/source/SpiritOS/src/lib/mac-worker/client.ts
  68:9  warning  'localWorkerPath' is assigned a value but never used  @typescript-eslint/no-unused-vars

✖ 16 problems (0 errors, 16 warnings)


> spirit-os@0.1.0 typecheck
> tsc --noEmit

```

## Result

GO with recorded test-command caveats.

- Suggested `npm test -- --runInBand ...` commands failed because this repo uses Vitest and does not support Jest's `--runInBand` flag.
- `npm run lint` completed with warnings only, no errors.
- `npm run typecheck` completed with no TypeScript errors.
- Focused Vitest replacement passed: `src/lib/coding/__tests__/model-provider-status.test.ts` (3 tests).
- Focused Vitest replacement passed: `src/lib/coding/__tests__/agent-trials-ui.test.ts` (15 tests).
- Source Proxy focused pytest could not run in this shell: `python` is unavailable and `python3 -m pytest` reported `No module named pytest`.
- `git diff --check` passed.

## Follow-up focused checks without Jest-only flag
```text

> spirit-os@0.1.0 test
> vitest run src/lib/coding/__tests__/model-provider-status.test.ts


 RUN  v4.1.5 /home/source/SpiritOS


 Test Files  1 passed (1)
      Tests  3 passed (3)
   Start at  20:03:36
   Duration  10.55s (transform 427ms, setup 636ms, import 105ms, tests 6ms, environment 9.03s)


> spirit-os@0.1.0 test
> vitest run src/lib/coding/__tests__/agent-trials-ui.test.ts


 RUN  v4.1.5 /home/source/SpiritOS


 Test Files  1 passed (1)
      Tests  15 passed (15)
   Start at  20:03:48
   Duration  916ms (transform 124ms, setup 86ms, import 128ms, tests 28ms, environment 406ms)

/bin/bash: line 7: python: command not found
```

## Python Source Proxy focused checks with python3
```text
/usr/bin/python3: No module named pytest
```
