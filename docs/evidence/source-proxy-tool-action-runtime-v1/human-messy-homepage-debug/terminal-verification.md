# Terminal Verification

Before reproduction:

```text
python scripts/agent-trials/run-source-proxy-qwen-init-smoke.py --run
status: NO-GO
actions_seen: 0
files_changed: []
openable_homepage: false
preview_url: ""
real_app_touched: false
```

After smoke on Dell/backend terminal:

```text
cd /home/source/SpiritOS
.venv-source-proxy/bin/python scripts/agent-trials/run-source-proxy-human-messy-homepage-smoke.py --run --prompt 'init a repo and make homepage for agent lab expermients'
status: GO
workspace path: /home/source/SpiritOS/docs/evidence/source-proxy-tool-action-runtime-v1/human-messy-homepage-debug/runs/20260611-215502/workspace
generated files: index.html
preview URL: http://10.0.0.186:8765/
backend_created_content: false
fallback_used: false
real_app_touched: false
file_equals_model_action_content: true
actions_seen: 1
openable_homepage: true
```

Serve verification:

```text
.venv-source-proxy/bin/python scripts/agent-trials/run-source-proxy-human-messy-homepage-smoke.py --serve --host 0.0.0.0 --port 8765
Serving workspace: /home/source/SpiritOS/docs/evidence/source-proxy-tool-action-runtime-v1/human-messy-homepage-debug/runs/20260611-215502/workspace
Requested port 8765 was busy; using 8766.
URL: http://10.0.0.186:8766/
```

HTTP check:

```text
8766 200 <!DOCTYPE html> <html lang="en"> <head>     <meta charset="UTF-8">
```

Focused regression:

```text
python -m pytest source_proxy/tests/test_coding_regression_pack.py -k "task_spec_intake or tool_action or bounded_agent_loop or advisory or plan7 or messy or homepage"
34 passed, 1 skipped, 63 deselected
```

Frontend regression on Dell:

```text
npm exec vitest -- run --pool=threads --no-file-parallelism --maxWorkers=1 src/lib/coding/__tests__/tool-runtime-surface.test.ts src/components/coding/__tests__/coding-command-center-shell.test.tsx
2 passed test files, 78 passed tests
stderr: existing React act(...) warnings
```

Final file checks:

```text
git diff --check
passed with no output

git status --branch --short --untracked-files=normal
dirty tree with pre-existing Source Proxy plan/evidence files plus this run's new files; no commit/stash/reset/checkout/clean performed
```
