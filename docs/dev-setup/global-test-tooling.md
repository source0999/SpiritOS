# Global Test Tooling

Install the same Playwright and Vitest versions globally that this repo uses locally:

```bash
npm install -g playwright@1.60.0 vitest@4.1.5
```

This repo's Vitest config runs in `jsdom`, so install the matching environment peer globally too:

```bash
npm install -g jsdom@24.1.3
```

Canonical versions:

```bash
playwright --version  # Version 1.60.0
vitest --version      # vitest/4.1.5
```

Peer environment check:

```bash
npm ls -g jsdom --depth=0
```

Keep the project-local installs in `node_modules` intact. `npx playwright` and `npx vitest` remain valid fallbacks, but Dell-hosted coding loop checks should be runnable directly from a fresh shell:

```bash
playwright test tests/ui-agent-trials/coding-agent-a-plus.spec.ts
vitest run src/lib/coding/__tests__/dummy-coder-10-grader.test.ts
```

Chromium browser bundles are expected under the Playwright cache. Verify without forcing a download:

```bash
playwright install --dry-run chromium
```

If the expected Chromium cache is missing on a fresh box, run:

```bash
playwright install chromium
```
