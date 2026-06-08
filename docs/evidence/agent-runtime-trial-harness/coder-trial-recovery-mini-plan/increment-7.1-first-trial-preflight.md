# Increment 7.1 - First Trial Preflight

Date: 2026-06-08

## Baseline

`git status --short` before the Coder 001 run showed an already-dirty Gate 5/6 tree, including:

- Modified runner/backend files such as `src/components/coding/CodingCockpitShell.tsx`, `src/lib/coding/reversible-trial-runner.ts`, `src/lib/coding/durable-run-store.ts`, and Source Proxy files.
- Untracked Gate 5/6 prompt/grader files:
  - `src/lib/coding/dummy-coder-10-prompts.ts`
  - `src/lib/coding/dummy-project-summary.ts`
  - `src/lib/coding/dummy-coder-10-grader.ts`
  - related focused tests
  - `tests/ui-agent-trials/fixtures/coder-10-dummy-product-site-definition.json`
- Existing evidence folder under `docs/evidence/agent-runtime-trial-harness/coder-trial-recovery-mini-plan/`.

`git diff --stat` showed 18 modified tracked files before Gate 7 evidence, with the main active surface in `CodingCockpitShell.tsx`, Source Proxy decision/task files, durable run types/store, and focused coding tests.

## Fixture Absence

Confirmed before running Coder 001:

- `tests/ui-agent-trials/fixtures/dummy-product-site/` did not exist.
- Existing fixture siblings included `dummy-coding-targets/` and `coder-10-dummy-product-site-definition.json`.

## Prompt Bank

Confirmed `src/lib/coding/dummy-coder-10-prompts.ts` defines exactly Coder 001 through Coder 010.

Coder 001 is present as `coder-001-init-dummy-product-site` and its submitted prompt contains:

`tests/ui-agent-trials/fixtures/dummy-product-site/`

The runner exposes a selected-prompt dropdown and a single action labelled `Run selected LumaCart prompt`. The full Coder 10 path is not triggered by default from this panel.

## Preflight Decision

Coder 001 was selectable and LumaCart was absent before the run.

During preflight, I found the single-prompt runner was not setting the live-apply fields needed for the backend implementation path, and the backend live-create allowlist did not include the dummy-product fixture root. I made a narrow Gate 7 runner/backend correction:

- `src/components/coding/CodingCockpitShell.tsx`: single prompt request now includes `selected_target`, `trial_mode: "live_apply"`, and `wants_implementation: true`.
- `src/lib/coding/dummy-coder-10-prompts.ts`: Coder 001 primary targets now enumerate the expected starter files, with `README.md` first for the single-target backend.
- `source_proxy/api/decision.py`: live-create allowlist now includes `tests/ui-agent-trials/fixtures/dummy-product-site/`.

No Coder 002-010, Coder 10, Coder 25, Coder 50, or Coder 100 run was started.
