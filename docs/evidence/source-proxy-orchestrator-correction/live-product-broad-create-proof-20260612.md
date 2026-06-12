# Live Product broad create proof - 2026-06-12

## Scope

User request: prove the Product proxy can classify broad messy create/artifact intent, choose disposable scope, avoid exact-target cheating, and enforce model-authored output for these prompts:

- `init repo and make homepage for agent lab`
- `make a calculator app`
- `make a portfolio homepage with placeholder nav and footer`

This pass used the real local Product route on `source-server` with `qwen2.5-coder:7b`. It did not use mocked `model_call` callbacks, backend-created files, deterministic fallback scaffolds, benchmark prompts, or real app mutation.

## Generic repair made during proof

The first calculator live run exposed a generic parser gap: the local model authored a valid multi-file `WriteFile` action array inside a fenced JSON block. The parser rejected the fenced JSON and retried, which produced a weaker one-file artifact.

Repair:

- `source_proxy/decision/tool_actions.py` now accepts fenced JSON action objects/action arrays through the same action schema validation used by strict JSON.
- `source_proxy/tests/test_coding_regression_pack.py` adds a parser regression proving a fenced, model-authored three-file action array is accepted.

This is not a prompt fallback or scaffold. It preserves the no-cheat boundary because the model still authors every target and every byte of file content, and the executor still enforces workspace, protected-path, allowed-extension, and file-count gates.

## Commands run

```bash
cd /home/source/SpiritOS
.venv/bin/python -m pytest source_proxy/tests/test_coding_regression_pack.py -k 'tool_action_parser or tool_action_contract or tool_action_executor or human_messy_homepage or messy_homepage or artifact'
.venv/bin/python scripts/agent-trials/run-source-proxy-human-messy-homepage-smoke.py --run --mode product --prompt 'init repo and make homepage for agent lab' --model-id qwen2.5-coder:7b
.venv/bin/python scripts/agent-trials/run-source-proxy-human-messy-homepage-smoke.py --run --mode product --prompt 'make a calculator app' --model-id qwen2.5-coder:7b
.venv/bin/python scripts/agent-trials/run-source-proxy-human-messy-homepage-smoke.py --run --mode product --prompt 'make a portfolio homepage with placeholder nav and footer' --model-id qwen2.5-coder:7b
.venv/bin/python -m pytest source_proxy/tests/test_coding_regression_pack.py -k 'task_spec_intake or tool_action or human_messy_homepage or messy_homepage or pure or artifact or protected or fake'
git diff --check
git status --branch --short --untracked-files=normal
```

## Check results

- Focused parser/proxy pytest after repair: `26 passed, 83 deselected in 6.12s`
- Requested broad pytest selector: `39 passed, 70 deselected in 18.38s`
- `git diff --check`: clean, no output
- `git status --branch --short --untracked-files=normal`:

```text
## master
 M docs/evidence/source-proxy-tool-action-runtime-v1/human-messy-homepage-debug/latest-run.json
 M docs/evidence/source-proxy-tool-action-runtime-v1/human-messy-homepage-debug/preview-url.txt
 M scripts/agent-trials/run-source-proxy-human-messy-homepage-smoke.py
 M source_proxy/decision/human_messy_homepage.py
 M source_proxy/decision/task_spec_intake.py
 M source_proxy/decision/tool_action_executor.py
 M source_proxy/decision/tool_action_loop.py
 M source_proxy/decision/tool_actions.py
 M source_proxy/tests/test_coding_regression_pack.py
?? docs/evidence/source-proxy-orchestrator-correction/
?? docs/evidence/source-proxy-tool-action-runtime-v1/human-messy-homepage-debug/pure-mode-phase-1/
?? docs/evidence/source-proxy-tool-action-runtime-v1/human-messy-homepage-debug/runs/20260611-223358/
```

## Live run results

### Homepage

- Run id: `20260612-003540`
- Status: `GO`
- Prompt: `init repo and make homepage for agent lab`
- Route type: `product`
- Task shape: `disposable_single_file_artifact`
- Task shape source: `generic_artifact_resolver`
- Artifact class: `html_static_page`
- Allowed extensions: `.html`
- Exact allowed files: none
- Allowed scope source: `artifact_class_extensions`
- Workspace decision source: `generic_artifact_resolver`
- Target path source: `model_action`
- Path selection mode: `model_chosen`
- Proxy exact target suggested: empty
- Model-authored targets: `index.html`
- Workspace before file count: `0`
- Workspace after files: `index.html`
- Backend-created content: `false`
- Fallback/deterministic scaffold/dummy fixture: `false`
- Real app touched: `false`
- File equals model action content: `true`
- Manual expectation check: mentions Agent Lab and has no missing local refs.
- Score: `docs/evidence/source-proxy-tool-action-runtime-v1/human-messy-homepage-debug/pure-mode-phase-1/product/runs/20260612-003540/score.json`
- Receipt: `docs/evidence/source-proxy-tool-action-runtime-v1/human-messy-homepage-debug/pure-mode-phase-1/product/runs/20260612-003540/receipt.json`

### Calculator

- Run id: `20260612-003549`
- Status: `GO`
- Prompt: `make a calculator app`
- Route type: `product`
- Task shape: `disposable_small_file_bundle`
- Task shape source: `generic_artifact_resolver`
- Artifact class: `static_ui_artifact`
- Allowed extensions: `.html`, `.css`, `.js`
- Exact allowed files: none
- Allowed scope source: `artifact_class_extensions`
- Workspace decision source: `generic_artifact_resolver`
- Target path source: `model_action`
- Path selection mode: `model_chosen`
- Proxy exact target suggested: empty
- Model-authored targets: `index.html`, `script.js`, `styles.css`
- Workspace before file count: `0`
- Workspace after files: `index.html`, `script.js`, `styles.css`
- Backend-created content: `false`
- Fallback/deterministic scaffold/dummy fixture: `false`
- Real app touched: `false`
- File equals model action content: `true`
- Raw model transcript count: `1`
- Parser evidence: `strict_json` rejected because the JSON was fenced; `fenced_json` accepted three `WriteFile` actions.
- Manual expectation check: display exists, digits/operators exist, CSS/JS refs exist, no missing local refs.
- Score: `docs/evidence/source-proxy-tool-action-runtime-v1/human-messy-homepage-debug/pure-mode-phase-1/product/runs/20260612-003549/score.json`
- Receipt: `docs/evidence/source-proxy-tool-action-runtime-v1/human-messy-homepage-debug/pure-mode-phase-1/product/runs/20260612-003549/receipt.json`

### Portfolio

- Run id: `20260612-003614`
- Status: `GO`
- Prompt: `make a portfolio homepage with placeholder nav and footer`
- Route type: `product`
- Task shape: `disposable_single_file_artifact`
- Task shape source: `generic_artifact_resolver`
- Artifact class: `html_static_page`
- Allowed extensions: `.html`
- Exact allowed files: none
- Allowed scope source: `artifact_class_extensions`
- Workspace decision source: `generic_artifact_resolver`
- Target path source: `model_action`
- Path selection mode: `model_chosen`
- Proxy exact target suggested: empty
- Model-authored targets: `index.html`
- Workspace before file count: `0`
- Workspace after files: `index.html`
- Backend-created content: `false`
- Fallback/deterministic scaffold/dummy fixture: `false`
- Real app touched: `false`
- File equals model action content: `true`
- Manual expectation check: nav-like placeholder, footer-like placeholder, placeholder hash links, no missing local refs.
- Score: `docs/evidence/source-proxy-tool-action-runtime-v1/human-messy-homepage-debug/pure-mode-phase-1/product/runs/20260612-003614/score.json`
- Receipt: `docs/evidence/source-proxy-tool-action-runtime-v1/human-messy-homepage-debug/pure-mode-phase-1/product/runs/20260612-003614/receipt.json`

## Hardcode scan

Command:

```bash
~/.local/bin/rg -n 'init repo and make homepage for agent lab|make a calculator app|make a portfolio homepage with placeholder nav and footer' source_proxy scripts/agent-trials docs/evidence/source-proxy-orchestrator-correction -g '!docs/evidence/source-proxy-tool-action-runtime-v1/**' || true
```

Result: no matches.

## GO / NO-GO

GO for this proof target.

The proxy classified the broad create/artifact prompts, chose disposable workspaces, supplied artifact class/extension boundaries without exact file targets, and executed only validated model-authored actions. The key generic repair was parser acceptance for fenced JSON model actions; the calculator rerun proved that the original model-authored multi-file bundle can now execute without callback scaffolding or backend-authored content.
