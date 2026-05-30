# Increment 1.7.1 Repository Checks

Date: 2026-05-28

## Required checks run

```bash
cd /home/source/SpiritOS
npx --no-install vitest run src/lib/mac-worker/__tests__/contract.test.ts src/app/api/coding/mac-worker/__tests__/route.test.ts src/lib/coding/__tests__/agent-trials-ui.test.ts --reporter=dot
npx --no-install vitest run src/components/coding/__tests__/coding-command-center-shell.test.tsx --reporter=dot
npx --no-install tsc --noEmit --pretty false
git diff --check
python3 -m py_compile scripts/mac-worker/spirit_mac_worker.py
node --check scripts/mac-worker/spirit-mac-worker.mjs
node --check scripts/agent-trials/run-ui-agent-trials.mjs
```

## Evidence

Checks were rerun after the final `src/lib/mac-worker/client.ts` stdout normalization fix.

### Mac worker, route, and agent trial tests

```text
Test Files  3 passed (3)
Tests  19 passed (19)
```

### Coding command center component test

```text
Test Files  1 passed (1)
Tests  74 passed (74)
```

The component suite emitted existing React `act(...)` warnings during async shell updates, but all tests passed.

### TypeScript

```text
passed with no output
```

### Git diff check

```text
passed with no output
```

### Python compile

```text
passed with no output
```

### Node syntax checks

```text
scripts/mac-worker/spirit-mac-worker.mjs passed with no output
scripts/agent-trials/run-ui-agent-trials.mjs passed with no output
```

## Result

Increment 1.7.1 is complete.

Required checks were run directly.

Evidence was written to this file.

GO to the next authorized increment: Increment 1.7.2, run final Mac smoke checks.
