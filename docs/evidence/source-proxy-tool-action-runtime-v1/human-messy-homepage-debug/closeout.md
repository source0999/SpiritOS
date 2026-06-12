# Human Messy Homepage Closeout

GO/NO-GO: GO.

Exact root cause: the old messy prompt smoke bypassed Tool Action Runtime v1 and called Qwen through raw `/api/generate`; Qwen authored advisory HTML in prose, but no runtime parser/executor converted it into a disposable `WriteFile`, so the workspace stayed unchanged.

Files changed:

- `source_proxy/decision/task_spec_intake.py`
- `source_proxy/decision/tool_actions.py`
- `source_proxy/decision/human_messy_homepage.py`
- `source_proxy/tests/test_coding_regression_pack.py`
- `scripts/agent-trials/run-source-proxy-human-messy-homepage-smoke.py`
- `docs/evidence/source-proxy-tool-action-runtime-v1/human-messy-homepage-debug/*`

Tests run:

- `python -m pytest source_proxy/tests/test_coding_regression_pack.py -k "task_spec_intake or tool_action or bounded_agent_loop or advisory or plan7 or messy or homepage"` -> 34 passed, 1 skipped.
- `npm exec vitest -- run --pool=threads --no-file-parallelism --maxWorkers=1 src/lib/coding/__tests__/tool-runtime-surface.test.ts src/components/coding/__tests__/coding-command-center-shell.test.tsx` on Dell -> 2 files passed, 78 tests passed, with existing React `act(...)` warnings.
- `.venv-source-proxy/bin/python scripts/agent-trials/run-source-proxy-human-messy-homepage-smoke.py --run --prompt 'init a repo and make homepage for agent lab expermients'` on Dell -> GO.
- `.venv-source-proxy/bin/python scripts/agent-trials/run-source-proxy-human-messy-homepage-smoke.py --serve --host 0.0.0.0 --port 8765` -> port 8765 was occupied, script fell forward to 8766 and served the generated workspace.
- `git diff --check` -> passed with no output.
- `git status --branch --short --untracked-files=normal` -> dirty pre-existing Source Proxy plan/evidence tree; no commit, push, branch, stash, reset, checkout, or clean performed.

Final smoke command:

```text
.venv-source-proxy/bin/python scripts/agent-trials/run-source-proxy-human-messy-homepage-smoke.py --run --prompt 'init a repo and make homepage for agent lab expermients'
```

Workspace path:

```text
/home/source/SpiritOS/docs/evidence/source-proxy-tool-action-runtime-v1/human-messy-homepage-debug/runs/20260611-215502/workspace
```

Preview URL:

```text
http://10.0.0.186:8766/
```

Anti-cheat verdict:

- `fallback_used`: false
- `deterministic_scaffold_used`: false
- `dummy_fixture_used`: false
- `backend_created_content`: false
- `file_equals_model_action_content`: true
- `real_app_touched`: false
